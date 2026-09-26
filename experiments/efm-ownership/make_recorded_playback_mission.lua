local source,config,output=assert(arg[1]),assert(arg[2]),assert(arg[3])
dofile(source);local c=assert(dofile(config));local count=0
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        assert(#group.units==1);local u=group.units[1]
        assert(u.name=='Probe' or u.name=='Observer')
        local observer=u.name=='Observer'
        -- Five-second native lead-in places capture near the recorded start.
        u.x=c.x-5*c.vx;u.y=c.z-5*c.vz;u.alt=c.y-5*c.vy
        if observer then
            u.x=u.x-120*math.cos(c.heading)+60*math.sin(c.heading)
            u.y=u.y-120*math.sin(c.heading)-60*math.cos(c.heading)
            u.alt=u.alt+30
        end
        u.heading=c.heading;u.psi=-c.heading;u.speed=c.speed;u.livery_id=c.livery
        group.x=u.x;group.y=u.y
        for i,point in ipairs(group.route.points) do
            point.x=u.x+(i-1)*20000*math.cos(c.heading)
            point.y=u.y+(i-1)*20000*math.sin(c.heading)
            point.alt=u.alt;point.speed=c.speed;point.speed_locked=true
            point.ETA=(i-1)*20000/c.speed;point.ETA_locked=(i==1)
        end
        count=count+1
    end
end
assert(count==2)
mission.descriptionText=c.briefing
local script='trigger.action.outText('..string.format('%q',c.briefing)..',30)'
mission.trigrules[1].actions={{predicate='a_do_script',text=script}}
mission.trig.actions[1]='a_do_script('..string.format('%q',script)..');'
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v) end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v) end
    assert(type(v)=='table');local keys={};for k in pairs(v) do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b) end)
    local out={'{'};for _,k in ipairs(keys) do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..',\n' end
    out[#out+1]='}';return table.concat(out)
end
local f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: recorded-flight mission configured from actual first sample and saved livery')
