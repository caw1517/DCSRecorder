-- Invoked by package.ps1 with the installed Lua 5.1 interpreter.
local base, out = assert(arg[1]), assert(arg[2])
local function clone(x)
    if type(x) ~= "table" then return x end
    local t = {}; for k,v in pairs(x) do t[k] = clone(v) end; return t
end
local function serialize(x)
    if type(x)=="string" then return string.format("%q",x) end
    if type(x)=="number" or type(x)=="boolean" then return tostring(x) end
    assert(type(x)=="table", "Unexpected mission value")
    local keys={}; for k in pairs(x) do keys[#keys+1]=k end
    table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
    local text={"{"}
    for _,k in ipairs(keys) do text[#text+1]="["..serialize(k).."]="..serialize(x[k])..",\n" end
    text[#text+1]="}"; return table.concat(text)
end
dofile(base)
local original=mission
for _,mode in ipairs({"player","ai","clients","formation"}) do
    mission=clone(original)
    -- Playback currently assumes calm air: native integration adds wind
    -- after our velocity command. See docs/research/dcs-zero-wind-control.md.
    mission.weather.atmosphere_type=0
    mission.weather.cyclones={}
    mission.weather.groundTurbulence=0
    for _,layer in ipairs({"atGround","at2000","at8000"}) do
        mission.weather.wind[layer].speed=0
    end
    local groups
    for _,country in pairs(mission.coalition.blue.country) do
        if country.plane then
            for _,group in pairs(country.plane.group) do
                for _,unit in pairs(group.units) do
                    if unit.skill=="Player" and unit.type=="TF-51D" then
                        assert(not groups,"Multiple players"); groups=country.plane.group
                    end
                end
            end
        end
    end
    assert(groups and #groups==1,"Unexpected mission template")
    local player=groups[1]
    player.name="Observer"; player.units[1].name="Observer"
    if mode=="player" then
        player.units[1].type="DCSRecorder-EFM-Probe"
        player.name="Probe"; player.units[1].name="Probe"
    else
        local target=clone(player)
        target.name="Probe"; target.groupId=9001
        target.units[1].name="Probe"; target.units[1].unitId=9001
        target.units[1].type="DCSRecorder-EFM-Probe"; target.units[1].skill="Excellent"
        target.x=target.x+1000; target.units[1].x=target.units[1].x+1000
        for _,point in pairs(target.route.points) do point.x=point.x+1000 end
        groups[#groups+1]=target
        if mode=="formation" then
            local lead=target.units[1]
            lead.speed=105; player.units[1].speed=105
            for _,point in pairs(target.route.points) do point.speed=105 end
            for _,point in pairs(player.route.points) do point.speed=105 end
            local heading=lead.heading
            -- Player starts 100 m aft and 60 m to the lead's left.
            local x=lead.x-100*math.cos(heading)+60*math.sin(heading)
            local y=lead.y-100*math.sin(heading)-60*math.cos(heading)
            local dx,dy=x-player.units[1].x,y-player.units[1].y
            player.x=player.x+dx; player.y=player.y+dy
            player.units[1].x=x; player.units[1].y=y
            for _,point in pairs(player.route.points) do point.x=point.x+dx; point.y=point.y+dy end
        end
        if mode=="clients" then
            player.units[1].skill="Client"
            target.units[1].skill="Client"
        end
    end
    mission.requiredModules={}
    mission.descriptionText="EFM pose-control diagnostic: "..mode..". Run for 55 seconds: starts at 5s, 90-degree climbing turn, pitch/roll check, releases at 43s. No aerodynamic fidelity claim."
    -- Independent observations go to normal dcs.log; no script sandbox changes.
    local observer=[[
env.info('OWNERSHIP_OBSERVER_STARTED')
trigger.action.outText('Climbing-turn probe: run 55 seconds. Control starts at 5s; release at 43s.',15)
local function sample()
  for _,name in ipairs({'Probe','Observer'}) do
    local u=Unit.getByName(name)
    if u and u:isExist() then
      local p=u:getPosition()
      env.info(string.format('OWNERSHIP_OBSERVER,%s,%.3f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%s',
        name,timer.getTime(),p.p.x,p.p.y,p.p.z,p.y.x,p.y.y,p.y.z,tostring(u:getID())))
      local v=u:getVelocity()
      env.info(string.format('TURN_OBSERVER,%s,%.3f,%.6f,%.6f,%.6f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.6f,%.6f,%.6f',
        name,timer.getTime(),p.p.x,p.p.y,p.p.z,p.x.x,p.x.y,p.x.z,p.y.x,p.y.y,p.y.z,p.z.x,p.z.y,p.z.z,v.x,v.y,v.z))
    end
  end
  return timer.getTime()+0.1
end
timer.scheduleFunction(sample,nil,timer.getTime()+0.1)
]]
    mission.trig=mission.trig or {}
    mission.trig.actions={ [1]="a_do_script("..string.format("%q",observer)..");" }
    mission.trig.conditions={ [1]="return(true)" }
    mission.trig.func={}
    mission.trig.funcStartup={ [1]="if mission.trig.conditions[1]() then mission.trig.actions[1]() end" }
    mission.trig.flag={ [1]=true }
    mission.trigrules={ [1]={
        comment="Ownership telemetry", predicate="triggerStart", eventlist="",
        rules={}, actions={ [1]={predicate="a_do_script",text=observer} },
    } }
    local f=assert(io.open(out.."/"..mode.."-mission","wb"))
    f:write("mission = ",serialize(mission)); f:close()
end
