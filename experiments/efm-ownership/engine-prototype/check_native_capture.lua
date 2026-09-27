-- Real Lua ABI check outside DCS, plus capture lifecycle/error fixtures.
local dll,hook=assert(arg[1]),assert(arg[2])
local reader=assert(package.loadlib(dll,'dcs_native_engine_sample'))
assert(reader()=='UNAVAILABLE,modules_not_loaded','unexpected native result outside DCS')
local function scenario(mode)
    local messages,history,callbacks={},{},nil
    local calls,loads,now=0,0,10
    local id=42
    local environment={type=type,tostring=tostring,tonumber=tonumber,assert=assert,error=error,
        pcall=pcall,ipairs=ipairs,string=string,table=table,math=math,
        log={INFO=1,write=function(_,_,s)messages[#messages+1]=s end},
        lfs={writedir=function()return 'fixture/'end},
        package={loadlib=function(path,symbol)
            assert(path=='fixture/Scripts/DCSRecorderEngineCapture/NativeEngineCapture.dll')
            assert(symbol=='dcs_native_engine_sample');loads=loads+1
            if mode=='load_failure'then return nil,'fixture_load_failure'end
            return function()
                calls=calls+1
                if mode=='native_failure'then return 'UNAVAILABLE,fixture'end
                if mode=='identity_change'then id=id+1 end
                if mode=='clock_change'then now=now+1 end
                return 'OK,.?AVFixture@@,0,1,0.7,0.4,0.3,0.3,0.8,0.5,0.4,0.4,1,2,3'
            end
        end},
        Export={LoGetModelTime=function()return now end,LoGetPlayerPlaneId=function()return id end,
            LoGetSelfData=function()return {Name=mode=='wrong_type'and 'F-16C_50'or 'FA-18C_hornet',Position={x=1,y=2,z=3}}end,
            LoGetEngineInfo=function()return {RPM={left=70,right=80}}end},
        DCS={getLogHistory=function(index)
            local rows={};for i=index+1,#history do rows[#rows+1]={message=history[i]}end;return rows,#history
        end,setUserCallbacks=function(cb)callbacks=cb end}}
    local f=assert(loadfile(hook));setfenv(f,environment);f()
    callbacks.onSimulationFrame();assert(loads==0 and calls==0,'native code loaded outside capture')
    local function post(s)history[#history+1]='DCSENGINE_MISSION,1,'..s;callbacks.onSimulationFrame()end
    post('BEGIN,1,10,42,FA-18C_hornet,Observer')
    post('DATA,1,1,10,baseline')
    if mode=='normal'then
        assert(messages[#messages]:find(',OK,.?AVFixture@@,',1,true),'native values missing')
        post('DATA,1,2,10.05,baseline');assert(calls==2 and loads==1)
        post('END,1,user_stop,2');assert(messages[#messages]=='DCSENGINE_NATIVE,1,END,1,user_stop,2')
    else
        assert(messages[#messages]:find('DCSENGINE_NATIVE,1,ERROR,1,1,',1,true),'failure not explicit: '..mode)
    end
    local before=calls
    post('DATA,1,3,10.1,baseline');assert(calls==before,'reads continued after stop/error')
    callbacks.onSimulationStop();assert(calls==before)
end
for _,mode in ipairs({'normal','native_failure','load_failure','wrong_type','identity_change','clock_change'})do scenario(mode)end
print('PASS: actual DLL Lua ABI/unavailable result; dormant outside capture; values, caching, stop, load/native/type/identity/clock failures')
