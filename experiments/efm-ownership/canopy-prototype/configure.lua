local baseline,ground,script_path,output,dcs=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4]),assert(arg[5])
dofile(baseline);local clean=mission;local clean_unit
for _,country in pairs(clean.coalition.blue.country)do for _,g in pairs((country.plane or {}).group or {})do
    for _,u in pairs(g.units)do if u.name=='Observer' then clean_unit=u end end
end end
assert(clean_unit and clean_unit.type=='FA-18C_hornet')
dofile(ground);assert(mission.theatre=='Caucasus');local selected,country_id,country_name
for _,country in pairs(mission.coalition.blue.country)do for _,g in pairs((country.plane or {}).group or {})do
    for _,u in pairs(g.units)do if u.skill=='Player' then
        assert(not selected and #g.units==1 and u.type=='FA-18C_hornet')
        selected=g;country_id=country.id;country_name=country.name
    end end
end end
assert(selected)
local unit=selected.units[1];local first=selected.route.points[1]
assert(first.type=='TakeOffParking' and first.action=='From Parking Area' and first.airdromeId==25)
assert(unit.parking_id=='15' and unit.parking=='1')
unit.name='Observer';unit.livery_id=clean_unit.livery_id;unit.payload=clean_unit.payload;unit.speed=0
selected.name='CanopyDiagnostic';selected.lateActivation=false;selected.uncontrolled=false
first.type='TakeOffParkingHot';first.action='From Parking Area Hot'
for _,point in pairs(selected.route.points)do point.task={id='ComboTask',params={tasks={}}}end
mission=clean;mission.coalition.blue.country={{id=country_id,name=country_name,plane={group={selected}}}}
mission.coalition.red.country={};mission.coalition.neutrals.country={};mission.start_time=12*3600
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v)end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v)end
    assert(type(v)=='table');local keys={};for k in pairs(v)do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
    local out={'{'};for _,k in ipairs(keys)do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..','end
    out[#out+1]='}';return table.concat(out)
end
local phases={
    {name='Close fully',hold=8,open=0,close=-1},
    {name='Hold closed',hold=3,open=0,close=0},
    {name='Open briefly',hold=.8,open=1,close=0},
    {name='Hold partial opening',hold=4,open=0,close=0},
    {name='Open fully',hold=8,open=1,close=0},
    {name='Hold open',hold=5,open=0,close=0},
    {name='Close briefly',hold=.8,open=0,close=-1},
    {name='Hold partial closing',hold=4,open=0,close=0},
    {name='Close fully',hold=8,open=0,close=-1},
    {name='Hold closed',hold=3,open=0,close=0},
}
local f=assert(io.open(script_path,'rb'));local script='DCS_CANOPY_PHASES='..serialize(phases)..'\n'..f:read('*a');f:close()
assert(loadstring(script));mission.trigrules={};mission.trig={actions={},conditions={},func={},flag={},funcStartup={}}
mission.trigrules[1]={comment='Load parked canopy diagnostic',predicate='triggerStart',eventlist='',rules={},actions={{predicate='a_do_script',text=script}}}
mission.trig.actions[1]='a_do_script('..string.format('%q',script)..');'
mission.trig.conditions[1]='return(true)';mission.trig.flag[1]=true
mission.trig.funcStartup[1]='if mission.trig.conditions[1]() then mission.trig.actions[1]() end'
local function add_phase(index,flag,phase,callback)
    local actions,code={},{}
    -- Release both spring-loaded directions before commanding either one.
    local calls={{cpt_commands.CanopySwitchOpen,0},{cpt_commands.CanopySwitchClose,0}}
    if phase.open~=0 then calls[#calls+1]={cpt_commands.CanopySwitchOpen,phase.open}end
    if phase.close~=0 then calls[#calls+1]={cpt_commands.CanopySwitchClose,phase.close}end
    for _,call in ipairs(calls)do
        actions[#actions+1]={predicate='a_cockpit_perform_clickable_action',cockpit_device=devices.CPT_MECHANICS,command=call[1],value=call[2],COCKPIT_ADDITIONAL_PLUGIN=''}
        code[#code+1]=string.format('a_cockpit_perform_clickable_action(%d,%d,%.9g,"");',devices.CPT_MECHANICS,call[1],call[2])
    end
    if callback then actions[#actions+1]={predicate='a_do_script',text=callback};code[#code+1]='a_do_script('..string.format('%q',callback)..');'end
    mission.trigrules[index]={comment=phase.name,predicate='triggerOnce',eventlist='',rules={{predicate='c_flag_is_true',flag=flag}},actions=actions}
    mission.trig.conditions[index]='return(c_flag_is_true('..string.format('%q',flag)..'))'
    mission.trig.actions[index]=table.concat(code)..'mission.trig.func['..index..']=nil;'
    mission.trig.func[index]='if mission.trig.conditions['..index..']() then mission.trig.actions['..index..']() end'
    mission.trig.flag[index]=true
end
for i,phase in ipairs(phases)do add_phase(i+1,'DCS_CANOPY_PHASE_'..i,phase,'DCS_CANOPY_PROBE.applied('..i..')')end
add_phase(#phases+2,'DCS_CANOPY_CLEANUP',{name='Release canopy switch',open=0,close=0})
mission.descriptionText='PARKED CANOPY DIAGNOSTIC. Stock Hornet, engines running, installed Caucasus parking start. Stay parked with throttle idle and parking brake set. F10 > Canopy diagnostic > Start automatic canopy sequence. Use F2 to observe closed, partial opening and HOLD, fully open, partial closing and HOLD, then closed. Allow about one minute. Do not use Active Pause or touch canopy controls during the sequence. This is a separate diagnostic, not a flight-library recording or ground-playback test. The switch returns to HOLD on completion or abort. Leave DCS open for log collection.'
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: one stock Hornet; installed parking/airfield retained; hot start; installed canopy switch commands; no jettison or Active Pause')
