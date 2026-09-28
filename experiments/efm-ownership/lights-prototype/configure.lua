local source,script_path,output,dcs=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4])
dofile(source)
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v) end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v) end
    assert(type(v)=='table');local keys={};for k in pairs(v)do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
    local out={'{'};for _,k in ipairs(keys)do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..',' end
    out[#out+1]='}';return table.concat(out)
end
local phases={
    {name='All lights OFF',hold=5,position=0,formation=0,strobe=0,landing=0},
    {name='Position lights DIM',hold=6,position=.3},
    {name='Position lights BRIGHT',hold=6,position=1},
    {name='Position lights OFF',hold=3,position=0},
    {name='Formation lights DIM',hold=6,formation=.3},
    {name='Formation lights BRIGHT',hold=6,formation=1},
    {name='Formation lights OFF',hold=3,formation=0},
    {name='Strobes DIM',hold=8,strobe=-1},
    {name='Strobes BRIGHT',hold=8,strobe=1},
    {name='Landing/taxi ON (gear must be down)',hold=8,strobe=0,landing=1},
    {name='All lights OFF',hold=5,position=0,formation=0,strobe=0,landing=0},
}
local f=assert(io.open(script_path,'rb'));local script=f:read('*a');f:close()
script='DCS_LIGHT_PHASES='..serialize(phases)..'\n'..script;assert(loadstring(script))
local count=0
for _,country in pairs(mission.coalition.blue.country)do
    for _,group in pairs((country.plane or {}).group or {})do
        assert(#group.units==1);local unit=group.units[1]
        assert(unit.name=='Observer' and unit.type=='FA-18C_hornet' and unit.skill=='Player')
        unit.speed=120
        for i,point in ipairs(group.route.points)do point.speed=120;point.ETA=(i-1)*20000/120 end
        count=count+1
    end
end
assert(count==1)
mission.start_time=22*3600
mission.trigrules={}
mission.trig={actions={},conditions={},func={},flag={},funcStartup={}}
mission.trigrules[1]={comment='Hold position and load light diagnostic',predicate='triggerStart',eventlist='',rules={},
    actions={{predicate='a_set_command',command=816},{predicate='a_do_script',text=script}}}
mission.trig.actions[1]='a_set_command(816);a_do_script('..string.format('%q',script)..');'
mission.trig.conditions[1]='return(true)';mission.trig.flag[1]=true
mission.trig.funcStartup[1]='if mission.trig.conditions[1]() then mission.trig.actions[1]() end'
local function add_phase(index,flag,phase,callback)
    local actions,code={},{}
    local function command(device,id,value)
        actions[#actions+1]={predicate='a_cockpit_perform_clickable_action',cockpit_device=device,command=id,value=value,COCKPIT_ADDITIONAL_PLUGIN=''}
        code[#code+1]=string.format('a_cockpit_perform_clickable_action(%d,%d,%.9g,"");',device,id,value)
    end
    if index==2 then command(devices.HOTAS,hotas_commands.THROTTLE_EXTERIOR_LIGHTS,1)end
    for _,item in ipairs({{'position','Position'},{'formation','Formation'},{'strobe','Strobe'},{'landing','LdgTaxi'}})do
        if phase[item[1]]~=nil then command(devices.EXT_LIGHTS,extlights_commands[item[2]],phase[item[1]])end
    end
    if callback then actions[#actions+1]={predicate='a_do_script',text=callback};code[#code+1]='a_do_script('..string.format('%q',callback)..');' end
    mission.trigrules[index]={comment=phase.name,predicate='triggerOnce',eventlist='',rules={{predicate='c_flag_is_true',flag=flag}},actions=actions}
    mission.trig.conditions[index]='return(c_flag_is_true('..string.format('%q',flag)..'))'
    mission.trig.actions[index]=table.concat(code)..'mission.trig.func['..index..']=nil;'
    mission.trig.func[index]='if mission.trig.conditions['..index..']() then mission.trig.actions['..index..']() end'
    mission.trig.flag[index]=true
end
for i,phase in ipairs(phases)do add_phase(i+1,'DCS_LIGHT_PHASE_'..i,phase,'DCS_LIGHT_PROBE.applied('..i..')')end
add_phase(#phases+2,'DCS_LIGHT_CLEANUP',phases[#phases])
mission.descriptionText='NIGHTTIME LIGHT OBSERVATION. One stock Hornet held in Active Pause. Do not toggle Active Pause. Lower landing gear, then F10 > Lights diagnostic > Start automatic light sequence. Use F2 to watch position/formation dim and bright, strobes dim and bright, landing/taxi, and off. Allow about 75 seconds; the sequence records actual argument responses at 50 Hz and stops automatically. Leave DCS open when complete. Controls are deliberately commanded in this separate mission; this is not playback and does not create a flight-library recording. Refuel light and ground illumination need separate checks.'
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: stock night mission; installed light device/command IDs; 11 phases; Active Pause; no playback module change')
