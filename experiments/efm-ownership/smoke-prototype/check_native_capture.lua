-- Check the actual Lua ABI, and capture failure/lifecycle boundaries offline.
local dll,hook=assert(arg[1]),assert(arg[2])
local reader=assert(package.loadlib(dll,'dcs_native_smoke_sample'))
assert(reader()=='UNAVAILABLE,no_cockpit','unexpected result outside DCS')
local function scenario(mode)
    local messages,history,callbacks={},{},nil
    local calls,loads,now,id=0,0,10.2,42
    local state=0
    local environment={type=type,tostring=tostring,tonumber=tonumber,assert=assert,
        pcall=pcall,ipairs=ipairs,string=string,table=table,math=math,
        log={INFO=1,write=function(_,_,s)messages[#messages+1]=s end},
        lfs={writedir=function()return 'fixture/'end},
        package={loadlib=function(path,symbol)
            assert(path=='fixture/Scripts/DCSRecorderSmokeCapture/NativeSmokeCapture.dll')
            assert(symbol=='dcs_native_smoke_sample');loads=loads+1
            if mode=='load_failure'then return nil,'fixture_load_failure'end
            return function()
                calls=calls+1
                if mode=='native_failure'then return 'UNAVAILABLE,fixture'end
                if mode=='invalid_state'then return 'OK,10,2,0,0'end
                if mode=='identity_change'then id=id+1 end
                if mode=='clock_change'then now=now+1 end
                return 'OK,10,'..state..','..state..',0'
            end
        end},
        Export={LoGetModelTime=function()return now end,LoGetPlayerPlaneId=function()return id end,
            LoGetSelfData=function()return {Name=mode=='wrong_type'and 'F-16C_50'or 'FA-18C_hornet'}end},
        DCS={getLogHistory=function(index)
            if mode=='history_reset'and #history>1 then return {},0 end
            local rows={};for i=index+1,#history do rows[#rows+1]={message=history[i]}end;return rows,#history
        end,setUserCallbacks=function(cb)callbacks=cb end}}
    -- A stale capture must not cause native reads at hook startup.
    history[1]='DCSSMOKE,1,BEGIN,9,1,2,{INV-SMOKE-WHITE},0,999'
    local f=assert(loadfile(hook));setfenv(f,environment);f()
    callbacks.onSimulationFrame();assert(loads==0 and calls==0)
    local function post(s)history[#history+1]='DCSSMOKE,1,'..s;callbacks.onSimulationFrame()end
    post('BEGIN,1,10,2,{INV-SMOKE-WHITE},0,999')
    if mode=='delayed'then now=11 end
    post('FRAME,1,'..(mode=='sequence_gap'and '2'or '1')..',10.2,1000')
    if mode=='normal'or mode=='end_count'or mode=='simulation_stop'then
        assert(messages[#messages]:find(',OK,10,0,0,0',1,true))
        state=1;now=10.4;post('FRAME,1,2,10.4,0')
        assert(messages[#messages]:find(',OK,10,1,1,0',1,true))
        state=0;now=10.6;post('FRAME,1,3,10.6,0')
        assert(messages[#messages]:find(',OK,10,0,0,0',1,true))
        assert(calls==3 and loads==1)
        if mode=='simulation_stop'then callbacks.onSimulationStop()
        else post('END,1,user_stop,'..(mode=='end_count'and '4'or '3'))end
        if mode~='end_count'then assert(messages[#messages]:find('DCSSMOKE_NATIVE,1,END,1,',1,true))end
    end
    if mode~='normal'and mode~='simulation_stop'then
        assert(messages[#messages]:find('DCSSMOKE_NATIVE,1,ERROR,',1,true),'failure not explicit: '..mode)
    end
    local before=calls
    post('FRAME,1,4,10.8,0');assert(calls==before,'reads continued after stop/error')
    callbacks.onSimulationStop();assert(calls==before)
end
for _,mode in ipairs({'normal','native_failure','invalid_state','load_failure','wrong_type',
    'identity_change','clock_change','delayed','sequence_gap','end_count','simulation_stop','history_reset'})do scenario(mode)end
print('PASS: actual DLL Lua ABI; OFF/ON/OFF, dormant startup, stop and capture error boundaries (12 scenarios)')
