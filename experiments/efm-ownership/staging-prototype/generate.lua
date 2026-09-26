-- Generate one experimental stock-Hornet mission from the local donor package.
local source, script_path, tape_path, output = assert(arg[1]), assert(arg[2]), assert(arg[3]), assert(arg[4])
dofile(source)
local f=assert(io.open(tape_path,'rb'))
assert(f:read('*l'):gsub('\r','')=='DCSREC_PLAYBACK_V1'); assert(tonumber(f:read('*l'))>=2)
local row=f:read('*l');f:close()
local v={};for n in row:gmatch('%S+') do v[#v+1]=assert(tonumber(n)) end
assert(#v==12 and v[1]==0)
local x,y,z=v[2],v[3],v[4]
local w,qx,qy,qz=v[5],v[6],v[7],v[8]
local heading=math.atan2(2*(qx*qz-w*qy),1-2*(qy*qy+qz*qz))
local speed=math.sqrt(v[9]^2+v[10]^2+v[11]^2)
local count,lead_id=0,nil
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        assert(#group.units==1)
        local u=group.units[1];local player=u.name=='Observer'
        assert(player or u.name=='Probe')
        u.type='FA-18C_hornet';u.name=player and 'Observer' or 'StageLead'
        u.skill=player and 'Player' or 'High'
        u.x=x-(player and 45.72*math.cos(heading) or 0)
        u.y=z-(player and 45.72*math.sin(heading) or 0)
        u.alt=y;u.alt_type='BARO';u.heading=heading;u.psi=-heading;u.speed=speed
        group.x=u.x;group.y=u.y;group.start_time=0
        group.lateActivation=not player
        group.uncontrolled=false
        if not player then group.name='StageLeadGroup';lead_id=group.groupId end
        for i,point in ipairs(group.route.points) do
            point.x=u.x+(i-1)*20000*math.cos(heading)
            point.y=u.y+(i-1)*20000*math.sin(heading)
            point.alt=y;point.speed=speed;point.speed_locked=true
            point.ETA=(i-1)*20000/speed;point.ETA_locked=(i==1)
        end
        count=count+1
    end
end
assert(count==2 and lead_id)
assert(mission.weather.wind.atGround.speed==0 and mission.weather.wind.at2000.speed==0 and mission.weather.wind.at8000.speed==0)
f=assert(io.open(script_path,'rb'));local script=f:read('*a');f:close();assert(loadstring(script))
-- Preserve the donor's separate lights-off trigger at index 2.
mission.trigrules[1].comment='Staging prototype: hold player and initialize diagnostics'
mission.trigrules[1].actions={{predicate='a_set_command',command=816},{predicate='a_do_script',text=script}}
mission.trig.actions[1]='a_set_command(816);a_do_script('..string.format('%q',script)..');'
mission.trigrules[3]={comment='Release player and spawn reference lead once',predicate='triggerOnce',eventlist='',
    rules={{predicate='c_flag_is_true',flag='DCS_STAGE_RELEASE'}},
    actions={{predicate='a_activate_group',group=lead_id},{predicate='a_set_command',command=816},
        {predicate='a_do_script',text='DCS_STAGING_PROTOTYPE.released()'}}}
mission.trig.conditions[3]='return(c_flag_is_true("DCS_STAGE_RELEASE"))'
mission.trig.actions[3]='a_activate_group('..lead_id..');a_set_command(816);a_do_script("DCS_STAGING_PROTOTYPE.released()"); mission.trig.func[3]=nil;'
mission.trig.func[3]='if mission.trig.conditions[3]() then mission.trig.actions[3]() end'
mission.trig.flag[3]=true
mission.descriptionText='THROWAWAY STAGING PROTOTYPE. Two stock Hornets; no recorded playback. Startup requests Active Pause. Wait 10 seconds without touching Pause, then use the communications menu F10 > DCS Recorder staging test > Start staged flight. Countdown 3-2-1 should run while your aircraft remains stationary. At release, a stock lead activates at the recording\'s original start, nominally 150 feet ahead; fly normally. Lead disappears 10 seconds later, while your mission continues. If radio menu or countdown is stuck, exit normally and report it; do not manually toggle pause during the measurement. Restart and repeat with a longer wait. Telemetry is written to DCS.log. This tests staging only, not recorded attitude/state or native playback timing.'
local function serialize(a)
    if type(a)=='string' then return string.format('%q',a) end
    if type(a)=='number' or type(a)=='boolean' then return tostring(a) end
    assert(type(a)=='table');local keys={};for k in pairs(a) do keys[#keys+1]=k end
    table.sort(keys,function(b,c)return tostring(b)<tostring(c)end)
    local out={'{'};for _,k in ipairs(keys) do out[#out+1]='['..serialize(k)..']='..serialize(a[k])..',\n' end
    out[#out+1]='}';return table.concat(out)
end
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
assert(loadfile(output))
for _,section in ipairs({'actions','conditions','func','funcStartup'}) do
    for _,code in pairs(mission.trig[section]) do assert(loadstring(code)) end
end
print(string.format('Prepared staging mission: original x=%.6f y=%.6f z=%.6f; separation=45.72m; 2 STOCK Hornets; lead late activation; command 816; runtime NOT verified',x,y,z))