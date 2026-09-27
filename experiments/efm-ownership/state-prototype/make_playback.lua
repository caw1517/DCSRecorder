local source,script_path,config_path,output=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4])
dofile(source)
local config=assert(dofile(config_path))
local count=0
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        assert(#group.units==1)
        local u=group.units[1]
        assert(u.name=='Probe' or u.name=='Observer')
        local lead=u.name=='Probe'
        if lead then
            u.name='StatePlayback';u.type=config.aircraft or 'DCSRecorder-Hornet-State';u.skill='High'
            group.name='StatePlaybackGroup';group.lateActivation=true
        end
        group.uncontrolled=false
        -- A simple native AI route isolates presentation from the motion controller.
        u.speed=145
        for i,point in ipairs(group.route.points) do
            point.x=u.x+(i-1)*60000*math.cos(u.heading)
            point.y=u.y+(i-1)*60000*math.sin(u.heading)
            point.alt=u.alt;point.speed=145;point.speed_locked=true
            point.ETA=(i-1)*60000/145;point.ETA_locked=(i==1)
            point.task={id='ComboTask',params={tasks={}}}
        end
        count=count+1
    end
end
assert(count==2)
assert(mission.weather.wind.atGround.speed==0 and mission.weather.wind.at2000.speed==0 and mission.weather.wind.at8000.speed==0)
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v) end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v) end
    assert(type(v)=='table');local keys={};for k in pairs(v) do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
    local parts={'{'}
    for _,k in ipairs(keys) do parts[#parts+1]='['..serialize(k)..']='..serialize(v[k])..',\n' end
    parts[#parts+1]='}';return table.concat(parts)
end
local f=assert(io.open(script_path,'rb'));local script=f:read('*a');f:close()
script='DCS_STATE_CONFIG='..serialize(config)..'\n'..script
assert(loadstring(script))
mission.trigrules[1].comment='Exterior-only actuator: hold player and register F10 start'
mission.trigrules[1].actions={{predicate='a_set_command',command=816},{predicate='a_do_script',text=script}}
mission.trig.actions[1]='a_set_command(816);a_do_script('..string.format('%q',script)..');'
mission.trigrules[3]={comment='Release active pause after F10 start',predicate='triggerOnce',eventlist='',
    rules={{predicate='c_flag_is_true',flag='DCS_STATE_RELEASE'}},actions={{predicate='a_set_command',command=816}}}
mission.trig.conditions[3]='return(c_flag_is_true("DCS_STATE_RELEASE"))'
mission.trig.actions[3]='a_set_command(816);mission.trig.func[3]=nil;'
mission.trig.func[3]='if mission.trig.conditions[3]() then mission.trig.actions[3]() end'
mission.trig.flag[3]=true
mission.descriptionText='EXTERIOR STATE PLAYBACK TEST. Active Pause holds your Hornet until F10 > Exterior state playback > Start captured surface sequence. Start releases your Hornet and spawns the separate test lead. Press F2 to inspect the lead. Watch baseline, roll, pitch, rudder, gear, flaps, speed brake in order; phase messages appear automatically. Captured surfaces play for 130.55 seconds, then hold for 8 seconds before the lead is removed. The lead follows a normal AI route: this is an exterior actuator test, not replay of the diagnostic flight path. Keep DCS running when finished so logs can be collected. Restart this mission to repeat. Do not manually toggle Active Pause before starting.'
if config.post_step then mission.descriptionText='STABILATOR TIMING COMPARISON. Same captured sequence, with only arguments 15/16 reapplied after the guarded native physics step. Watch the pitch phase at about 36 seconds after start. Live success is not yet established.\n\n'..mission.descriptionText end
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: isolated exterior module, two aircraft, simple AI route, active-pause/F10 release')
