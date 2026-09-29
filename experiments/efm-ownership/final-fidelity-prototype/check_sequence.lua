-- Execute the packaged sequencer and real generated trigger actions.
for _,abort_at in ipairs({-1,35})do
    local now,job,callback=0,nil,nil
    local flags,calls,logs={},{},{}
    local e=setmetatable({DCSRECORDER={state='idle'},
        timer={getTime=function()return now end,scheduleFunction=function(fn,_,t)callback=fn;job=t end},
        trigger={action={setUserFlag=function(k,v)flags[k]=v end,outText=function()end}},
        env={info=function(s)logs[#logs+1]=s end},
        c_flag_is_true=function(k)return flags[k]==1 end,
        a_cockpit_perform_clickable_action=function(device,command,value,plugin)
            assert(plugin=='' and value>=-1 and value<=1)
            calls[#calls+1]={device,command,value}
        end}, {__index=_G})
    local function execute(code)local fn=assert(loadstring(code));setfenv(fn,e);return fn()end
    e.a_do_script=execute
    local fn=assert(loadfile(arg[1]));setfenv(fn,e);fn()
    local mission=e.mission
    assert(mission.start_time==19*3600 and #mission.trigrules==11)
    local units=0
    for _,c in pairs(mission.coalition.blue.country)do for _,g in pairs((c.plane or {}).group or {})do for _,u in pairs(g.units)do
        assert(u.name=='Observer' and u.type=='FA-18C_hornet' and u.skill=='Player' and u.speed==120)
        assert(u.livery_id=='Blue Angels Jet Team')
        for station,p in pairs(u.payload.pylons)do assert(p.CLSID=='<CLEAN>' or (station==10 and p.CLSID=='{INV-SMOKE-WHITE}'))end
        assert(u.payload.pylons[10].CLSID=='{INV-SMOKE-WHITE}')
        units=units+1
    end end end
    assert(units==1)
    local startup=mission.trigrules[1].actions[1].text
    assert(loadstring(startup))
    assert(startup:find('DCSRECORDER_WHEELS=true',1,true))
    local begin=assert(startup:find('FINAL_FIDELITY_PHASES=',1,true))
    execute(startup:sub(begin))
    local function frame()
        if job and now>=job then job=callback()end
        for i=2,#mission.trigrules do if mission.trig.func[i]then
            local condition=assert(loadstring(mission.trig.conditions[i]));setfenv(condition,e)
            if condition()then execute(mission.trig.actions[i])end
        end end
    end
    for i=1,50 do now=i*.02;frame()end
    assert(#calls==0,'controls changed before recording')
    e.DCSRECORDER.state='recording'
    for i=51,4800 do
        now=i*.02
        if abort_at>0 and now>=abort_at then e.DCSRECORDER.state='stopped'end
        frame()
    end
    if abort_at<0 then assert(#logs==9);e.DCSRECORDER.state='stopped';now=97;frame();assert(#logs==10)
    else assert(#logs==5)end
    assert(flags.FINAL_FIDELITY_CLEANUP==1)
    local states={};for _,c in ipairs(calls)do states[c[1]..':'..c[2]]=c[3]end
    for _,v in pairs(states)do assert(v==0,'cleanup left a controlled switch on')end
    local n=#calls;e.DCSRECORDER.state='recording';now=100;frame();assert(#calls==n)
end
print('PASS: packaged phases, no pre-record actions, stop cleanup, early abort and one-shot guard')
