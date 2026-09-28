-- Generate a staged recorded-playback mission from the local donor package.
local source,script_path,config_path,output=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4])
dofile(source)
local c=assert(dofile(config_path))
local function serialize(a)
    if type(a)=='string' then return string.format('%q',a) end
    if type(a)=='number' or type(a)=='boolean' then return tostring(a) end
    assert(type(a)=='table');local keys={};for k in pairs(a) do keys[#keys+1]=k end
    table.sort(keys,function(b,c)return tostring(b)<tostring(c)end)
    local out={'{'};for _,k in ipairs(keys) do out[#out+1]='['..serialize(k)..']='..serialize(a[k])..',\n' end
    out[#out+1]='}';return table.concat(out)
end
local x,y,z,heading,speed=c.x,c.y,c.z,c.heading,c.speed
local f
local count,lead_id=0,nil
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        assert(#group.units==1)
        local u=group.units[1];local player=u.name=='Observer'
        assert(player or u.name=='Probe')
        u.type=player and 'FA-18C_hornet' or (c.aircraft or 'DCSRecorder-Hornet-Staged');u.name=player and 'Observer' or 'StagedPlayback'
        u.skill=player and 'Player' or 'High'
        if c.smoke_events and not player then
            assert(c.smoke_clsid=='{INV-SMOKE-WHITE}','Unsupported recorded smoke loadout')
            assert(not u.payload.pylons[10],'Existing smoke station must not be replaced')
            u.payload.pylons[10]={CLSID=c.smoke_clsid}
        end
        u.x=x-(player and 45.72*math.cos(heading) or 0)
        u.y=z-(player and 45.72*math.sin(heading) or 0)
        u.alt=y;u.alt_type='BARO';u.heading=heading;u.psi=-heading;u.speed=speed
        group.x=u.x;group.y=u.y;group.start_time=0
        group.lateActivation=not player
        group.uncontrolled=false
        if not player then group.name='StagedPlaybackGroup';lead_id=group.groupId end
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
f=assert(io.open(script_path,'rb'));local script=f:read('*a');f:close()
script='DCS_STAGED_CONFIG='..serialize({duration=c.duration,token_high=c.token_high,token_low=c.token_low,
    smoke_events=c.smoke_events,exterior=c.exterior,lights=c.lights,canopy=c.canopy})..'\n'..script
assert(loadstring(script))
-- Preserve the donor's separate lights-off trigger at index 2.
mission.trigrules[1].comment='Staging prototype: hold player and initialize diagnostics'
mission.trigrules[1].actions={{predicate='a_set_command',command=816},{predicate='a_do_script',text=script}}
mission.trig.actions[1]='a_set_command(816);a_do_script('..string.format('%q',script)..');'
mission.trigrules[3]={comment='Release player and spawn reference lead once',predicate='triggerOnce',eventlist='',
    rules={{predicate='c_flag_is_true',flag='DCS_RECORDED_RELEASE'}},
    actions={{predicate='a_activate_group',group=lead_id},{predicate='a_set_command',command=816},
        {predicate='a_do_script',text='DCS_STAGED_PLAYBACK.released()'}}}
mission.trig.conditions[3]='return(c_flag_is_true("DCS_RECORDED_RELEASE"))'
mission.trig.actions[3]='a_activate_group('..lead_id..');a_set_command(816);a_do_script("DCS_STAGED_PLAYBACK.released()"); mission.trig.func[3]=nil;'
mission.trig.func[3]='if mission.trig.conditions[3]() then mission.trig.actions[3]() end'
mission.trig.flag[3]=true
mission.descriptionText='RECORDED PLAYBACK INTEGRATION TEST. Active Pause holds your stock Hornet until F10 > DCS Recorder > Start playback. A three-second countdown activates the custom recorded-playback aircraft and releases your aircraft. Original recorded pose, motion and speed brake are commanded from the first callback without translation or attitude blending. Full aircraft-state fidelity is not yet supported. The lead disappears after confirmed completion; your mission continues. On a controller or package error, the lead is removed and a failure message appears. Restart the mission to replay. Wait about 10 seconds before the first start; do not manually toggle pause.'
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
assert(loadfile(output))
for _,section in ipairs({'actions','conditions','func','funcStartup'}) do
    for _,code in pairs(mission.trig[section]) do assert(loadstring(code)) end
end
print(string.format('Prepared staging mission: original x=%.6f y=%.6f z=%.6f; separation=45.72m; stock player + dedicated recorded aircraft; late activation; runtime NOT verified',x,y,z))
