-- Final ordinary flight capture. Only light/probe cockpit controls are automated.
local source,output,dcs=assert(arg[1]),assert(arg[2]),assert(arg[3])
dofile(source)
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v) end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v) end
    local keys={};for k in pairs(v)do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
    local out={'{'};for _,k in ipairs(keys)do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..',' end
    out[#out+1]='}';return table.concat(out)
end
local phases={
    {time=0,name='Lights OFF. Hold level, steady power.',position=0,formation=0,strobe=0,landing=0,probe=0,master=1},
    {time=8,name='Navigation/formation DIM. Gentle turn; extend/retract speed brake.',position=.3,formation=.3},
    {time=20,name='Navigation/formation BRIGHT; strobes DIM. Turn white smoke ON.',position=1,formation=1,strobe=-1},
    {time=32,name='Strobes BRIGHT; landing/taxi ON. Lower gear below 250 KIAS.',strobe=1,landing=1},
    {time=44,name='Refueling probe EXTEND, lights ON. Keep moderate power.',probe=1},
    {time=56,name='Refueling light OFF using master switch.',master=0},
    {time=62,name='Refueling light ON using master switch. Turn white smoke OFF.',master=1},
    {time=70,name='Probe RETRACT; lights OFF. Raise gear; brief full afterburner then reduce power.',probe=0,position=0,formation=0,strobe=0,landing=0},
    {time=90,name='Sequence complete. F10 > DCS Recorder > Stop recording. Leave DCS open.'},
}
local driver=[[
local began,next_phase,used=nil,1,false
timer.scheduleFunction(function()
    local r=DCSRECORDER
    if not r then return timer.getTime()+.1 end
    if not began and not used and r.state=='recording' then began=timer.getTime();used=true end
    if began and r.state~='recording' then trigger.action.setUserFlag('FINAL_FIDELITY_CLEANUP',1);return nil end
    if began and next_phase<=#FINAL_FIDELITY_PHASES and timer.getTime()-began>=FINAL_FIDELITY_PHASES[next_phase].time then
        trigger.action.setUserFlag('FINAL_FIDELITY_PHASE_'..next_phase,1)
        next_phase=next_phase+1
    end
    return timer.getTime()+.02
end,nil,timer.getTime()+.1)
]]
local startup=mission.trigrules[1].actions[1].text
assert(startup:find('DCSRECORDER_WHEELS=true',1,true) and startup:find('DCSRECORDER_SMOKE=true',1,true))
startup=startup..'\nFINAL_FIDELITY_PHASES='..serialize(phases)..'\n'..driver
assert(loadstring(startup))
mission.trigrules[1].actions={{predicate='a_do_script',text=startup}}
mission.trig.actions[1]='a_do_script('..string.format('%q',startup)..');'
local function phase(index,flag,p)
    local actions,code={},{}
    local function command(device,id,value)
        actions[#actions+1]={predicate='a_cockpit_perform_clickable_action',cockpit_device=device,command=id,value=value,COCKPIT_ADDITIONAL_PLUGIN=''}
        code[#code+1]=string.format('a_cockpit_perform_clickable_action(%d,%d,%.9g,"");',device,id,value)
    end
    if p.master~=nil then command(devices.HOTAS,hotas_commands.THROTTLE_EXTERIOR_LIGHTS,p.master)end
    for _,item in ipairs({{'position','Position'},{'formation','Formation'},{'strobe','Strobe'},{'landing','LdgTaxi'}})do
        if p[item[1]]~=nil then command(devices.EXT_LIGHTS,extlights_commands[item[2]],p[item[1]])end
    end
    if p.probe~=nil then command(devices.FUEL_INTERFACE,fuel_commands.ProbeControlSw,p.probe)end
    local note='trigger.action.outText('..string.format('%q',p.name)..',12);env.info('..string.format('%q','DCS_FINAL_FIDELITY,'..p.time..','..p.name)..')'
    actions[#actions+1]={predicate='a_do_script',text=note};code[#code+1]='a_do_script('..string.format('%q',note)..');'
    mission.trigrules[index]={comment=p.name,predicate='triggerOnce',eventlist='',rules={{predicate='c_flag_is_true',flag=flag}},actions=actions}
    mission.trig.conditions[index]='return(c_flag_is_true('..string.format('%q',flag)..'))'
    mission.trig.actions[index]=table.concat(code)..'mission.trig.func['..index..']=nil;'
    mission.trig.func[index]='if mission.trig.conditions['..index..']() then mission.trig.actions['..index..']() end'
    mission.trig.flag[index]=true
end
for i,p in ipairs(phases)do phase(i+1,'FINAL_FIDELITY_PHASE_'..i,p)end
phase(#phases+2,'FINAL_FIDELITY_CLEANUP',{time=-1,name='Recording stopped; light sequence cleaned up.',probe=0,position=0,formation=0,strobe=0,landing=0,master=0})
mission.start_time=19*3600
local count=0
for _,country in pairs(mission.coalition.blue.country)do for _,group in pairs((country.plane or {}).group or {})do
    assert(#group.units==1);local u=group.units[1]
    assert(u.name=='Observer' and u.type=='FA-18C_hornet' and u.skill=='Player')
    u.speed=120
    for i,p in ipairs(group.route.points)do p.speed=120;p.ETA=(i-1)*20000/120 end
    count=count+1
end end
assert(count==1)
mission.descriptionText='FINAL COMBINED CAPTURE. Fly normally; do not use Active Pause while recording. Begin nearly level. F10 > DCS Recorder > Start recording starts a 90-second prompted sequence. Lights and refueling probe change automatically; you control flight, throttle, gear, speed brake and white smoke. Follow on-screen prompts. Stay airborne, within 70-260 m/s world speed; stay below 250 KIAS with gear/probe extended. At the final prompt stop recording with F10 and leave DCS open. Canopy and changing ground wheels were accepted separately; keep canopy closed. Ground illumination will be checked with ground operations. This captures real measured state through the installed normal recorder.'
local f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: final combined capture, nine prompted phases, normal recorder and installed cockpit commands')
