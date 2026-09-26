-- Local prototype: change aircraft/profile, retaining the prior formation geometry.
local baseline, donor, output = assert(arg[1]), assert(arg[2]), assert(arg[3])
local function clone(x)
    if type(x) ~= 'table' then return x end
    local result={}; for k,v in pairs(x) do result[k]=clone(v) end; return result
end
local function serialize(x)
    if type(x)=='string' then return string.format('%q',x) end
    if type(x)=='number' or type(x)=='boolean' then return tostring(x) end
    assert(type(x)=='table')
    local keys={}; for k in pairs(x) do keys[#keys+1]=k end
    table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
    local parts={'{'}
    for _,k in ipairs(keys) do parts[#parts+1]='['..serialize(k)..']='..serialize(x[k])..',\n' end
    parts[#parts+1]='}'; return table.concat(parts)
end
dofile(donor)
local player
for _,side in pairs(mission.coalition) do
    if type(side)=='table' then for _,country in pairs(side.country or {}) do
        for _,group in pairs((country.plane or {}).group or {}) do
            for _,unit in pairs(group.units) do
                if unit.skill=='Player' and unit.type=='FA-18C_hornet' then
                    assert(not player,'Multiple donor players'); player=clone(unit)
                end
            end
        end
    end end
end
assert(player,'No stock Hornet donor player')
dofile(baseline)
local count=0
local speed=225.0215739890135
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        for i,old in pairs(group.units) do
            assert(old.name=='Observer' or old.name=='Probe')
            local unit=clone(player)
            for _,key in ipairs({'x','y','alt','alt_type','heading','psi','unitId','name','skill'}) do unit[key]=old[key] end
            unit.type=old.name=='Probe' and 'DCSRecorder-Hornet-Probe' or 'FA-18C_hornet'
            unit.speed=speed
            unit.livery_id='Blue Angels Jet Team'
            unit.onboard_num=old.name=='Probe' and '001' or '002'
            unit.payload.pylons={}
            -- Empty stations retain the removable Hornet pylons. Explicitly
            -- choose the stock <CLEAN> option for every removable pylon.
            for _,station in ipairs({2,3,5,7,8}) do
                unit.payload.pylons[station]={CLSID='<CLEAN>'}
            end
            unit.payload.fuel=3500
            group.units[i]=unit; count=count+1
        end
        local eta=0
        for i,point in ipairs(group.route.points) do
            if i>1 then
                local previous=group.route.points[i-1]
                eta=eta+math.sqrt((point.x-previous.x)^2+(point.y-previous.y)^2)/speed
            end
            point.speed=speed; point.speed_locked=true
            -- DCS requires a time anchor; downstream times follow locked speeds.
            point.ETA_locked=(i==1); point.ETA=eta
        end
    end
end
assert(count==2,'Expected one player and one playback aircraft')
mission.weather.atmosphere_type=0; mission.weather.cyclones={}
mission.weather.groundTurbulence=0; mission.weather.qnh=760
mission.weather.season.temperature=15
for _,layer in ipairs({'atGround','at2000','at8000'}) do mission.weather.wind[layer].speed=0 end
-- requiredModules values are declare_plugin IDs, not aircraft or folder names.
mission.requiredModules={['F/A-18C']='F/A-18C'}
local turn_duration=math.pi/(9.80665*math.sqrt(2.5^2-1)/speed)+(6+3)/2
local first_end=7+turn_duration
local second_start=first_end+10
local second_end=second_start+turn_duration
local briefing=string.format('Hornet right-level-left test: run 110 seconds. Nominal 400 KIAS, clean jets, lights off. Control 5s; 180-degree right turn 7-%.1fs; straight and level to %.1fs; 180-degree left turn to %.1fs; release %.1fs. Each turn: 6s roll-in, 3s roll-out, 66.4-degree bank, 2.5g geometric path. Confirm HUD speed.',first_end,second_start,second_end,second_end+6)
if arg[4] then briefing=assert(dofile(arg[4])) end
mission.descriptionText=briefing
-- Keep the previous independent pose observer, updating its briefing.
local observer=assert(mission.trigrules[1].actions[1].text)
observer=observer:gsub('Climbing%-turn probe: run 55 seconds%. Control starts at 5s; release at 43s%.',
    briefing)
-- Atmosphere measurement checks the nominal KIAS estimate without claiming HUD access.
local airlog=[[
local function air_sample()
  for _,name in ipairs({'Probe','Observer'}) do
    local u=Unit.getByName(name)
    if u and u:isExist() then
      local p=u:getPoint(); local v=u:getVelocity(); local wind=atmosphere.getWind(p)
      local appearance={}
      for _,index in ipairs({21,88,190,191,192,193,210,212,309,310,312,314,315}) do
        appearance[#appearance+1]=string.format('%d=%.3f',index,u:getDrawArgumentValue(index))
      end
      env.info(string.format('HORNET_APPEARANCE,%s,%.3f,%s',name,timer.getTime(),table.concat(appearance,',')))
      local ok,T,P=pcall(atmosphere.getTemperatureAndPressure,p)
      if ok and type(T)=='number' and type(P)=='number' and T>0 and P>0 then
        local speed=math.sqrt((v.x-wind.x)^2+(v.y-wind.y)^2+(v.z-wind.z)^2)
        local m2=speed^2/(1.4*287.05287*T)
        local qc=P*((1+0.2*m2)^3.5-1)
        local cas=math.sqrt(1.4*287.05287*288.15)*math.sqrt(5*((1+qc/101325)^(2/7)-1))*3600/1852
        env.info(string.format('HORNET_AIR,%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f',name,timer.getTime(),T,P,speed,cas,wind.x,wind.y,wind.z))
      end
    end
  end
  return timer.getTime()+0.5
end
timer.scheduleFunction(air_sample,nil,timer.getTime()+0.1)
]]
observer=observer..'\n'..airlog
mission.trig.actions[1]='a_do_script('..string.format('%q',observer)..');'
mission.trigrules[1].actions[1].text=observer
assert(loadstring(observer),'Observer script syntax')
-- Initialize the stock player's exterior-light switches after cockpit startup.
-- Device/command IDs and off values come from the installed Hornet scripts.
assert(not mission.trigrules[2],'Expected only the existing observer trigger')
mission.trigrules[2]={comment='Hornet exterior lights off',eventlist='',predicate='triggerOnce',
    rules={{predicate='c_time_after',seconds=1}},actions={}}
local commands={}
for _,command in ipairs({3001,3002,3003,3004}) do
    table.insert(mission.trigrules[2].actions,{predicate='a_cockpit_perform_clickable_action',
        cockpit_device=8,command=command,value=0,COCKPIT_ADDITIONAL_PLUGIN=''})
    commands[#commands+1]=string.format('a_cockpit_perform_clickable_action(8,%d,0,"");',command)
end
mission.trig.conditions[2]='return(c_time_after(1))'
mission.trig.actions[2]=table.concat(commands)..' mission.trig.func[2]=nil;'
mission.trig.func[2]='if mission.trig.conditions[2]() then mission.trig.actions[2]() end'
mission.trig.flag[2]=true
local f=assert(io.open(output,'wb')); f:write('mission = ',serialize(mission)); f:close()
print('PASS: two clean Hornets, matched livery, lights-off trigger, calm ISA weather; '..briefing)
