-- Execute packaged startup/phase triggers and sampler, without claiming rendering.
local path,dcs=assert(arg[1]),assert(arg[2])
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')
local allowed={}
for _,k in ipairs({'CanopySwitchOpen','CanopySwitchClose'})do allowed[cpt_commands[k]]=true end
local function run(mode)
    local now=0
    local flags,jobs,commands,logs,calls,state={},{},{},{},{},{}
    local held=0
    local unit={isExist=function()return true end,getPlayerName=function()return 'fixture'end,
        getTypeName=function()return 'FA-18C_hornet'end,getID=function()return 2 end,
        getVelocity=function()return {x=mode=='moving' and 2 or 0,y=0,z=0}end,inAir=function()return false end,
        getDrawArgumentValue=function(_,i)assert(i==38);return .038 end}
    local e=setmetatable({env={info=function(s)logs[#logs+1]=s end},Unit={getByName=function(n)assert(n=='Observer');return unit end},
        trigger={action={outText=function()end,setUserFlag=function(k,v)flags[k]=v end}},
        timer={getTime=function()return now end,scheduleFunction=function(fn,_,time)jobs[#jobs+1]={fn=fn,time=time}end},
        missionCommands={addSubMenu=function()return {}end,addCommand=function(s,_,fn)commands[s]=fn end},
        a_set_command=function(cmd)error('Unexpected command or pause') end,
        c_flag_is_true=function(k)return flags[k]==1 end,
        a_cockpit_perform_clickable_action=function(device,cmd,value,plugin)
            assert(plugin=='')
            assert((device==devices.CPT_MECHANICS and allowed[cmd]) or
                false)
            assert(value>=-1 and value<=1)
            calls[#calls+1]={device,cmd,value};state[device..':'..cmd]=value
        end}, {__index=_G})
    local function execute(text)local fn=assert(loadstring(text));setfenv(fn,e);return fn()end
    e.a_do_script=execute
    local fn=assert(loadfile(path));setfenv(fn,e);fn()
    local mission=e.mission;assert(mission.start_time==12*3600)
    local count=0
    for _,c in pairs(mission.coalition.blue.country)do for _,g in pairs((c.plane or {}).group or {})do
        for _,u in pairs(g.units)do
            assert(u.name=='Observer' and u.type=='FA-18C_hornet' and u.skill=='Player' and u.speed==0)
            for _,p in pairs(u.payload.pylons)do assert(p.CLSID=='<CLEAN>')end
            count=count+1
        end
    end end
    assert(count==1)
    for _,kind in ipairs({'actions','conditions'})do for i,code in pairs(mission.trig[kind])do
        local f=assert(loadstring(code));setfenv(f,e);mission.trig[kind][i]=f
    end end
    for _,code in pairs(mission.trig.funcStartup)do execute(code)end
    assert(held==0 and #calls==0,'startup commanded canopy before F10')
    commands['Start automatic canopy sequence']();assert(not e.DCS_CANOPY_PROBE.active,'startup guard')
    now=10;commands['Start automatic canopy sequence']();commands['Start automatic canopy sequence']()
    assert(#jobs==1 and e.DCS_CANOPY_PROBE.active,'duplicate start')
    for frame=1,6000 do
        now=10+frame*.02
        if mode~='missing_phase' then
            for i=2,#mission.trigrules do if mission.trig.func[i]then execute(mission.trig.func[i])end end
        end
        for _,job in ipairs(jobs)do if job.time and now+1e-8>=job.time then job.time=job.fn()end end
        if mode=='abort' and frame==50 then commands['Stop and release canopy control']()end
    end
    assert(not e.DCS_CANOPY_PROBE.active and flags.DCS_CANOPY_CLEANUP==1)
    local before=#calls;commands['Start automatic canopy sequence']();assert(#jobs==1 and #calls==before,'restart not bounded')
    local applied=0;local rows=0;local reason
    for _,s in ipairs(logs)do
        local phase=s:match('^DCSCANOPY,1,APPLIED,(%d+),')
        if phase then applied=applied+1;assert(tonumber(phase)==applied)end
        local seq=s:match('^DCSCANOPY,1,DATA,(%d+),')
        if seq then rows=rows+1;assert(tonumber(seq)==rows)end
        local why,n=s:match('^DCSCANOPY,1,END,([^,]+),(%d+),')
        if why then assert(not reason and tonumber(n)==rows);reason=why end
    end
    assert(reason==(mode=='normal'and 'complete'or mode=='abort'and 'user_stop'or mode=='moving'and 'aircraft_moving'or 'phase_not_applied'))
    if mode=='normal'then assert(applied==10 and rows>2000)end
    if mode~='missing_phase'then for cmd in pairs(allowed)do assert(state[devices.CPT_MECHANICS..':'..cmd]==0,'cleanup left canopy switch commanded')end end
    if mode=='normal' and arg[3]then
        local output=assert(io.open(arg[3],'wb'));output:write(table.concat(logs,'\n'),'\n');output:close()
    end
end
for _,mode in ipairs({'normal','abort','missing_phase','moving'})do run(mode)end
print('PASS: packaged startup, installed command IDs, 10-phase sequence, 50-Hz records, duplicate start, completion, abort/cleanup missing-phase and moving-aircraft guards')
