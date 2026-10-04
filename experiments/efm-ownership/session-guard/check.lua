-- Actual module and hook, with simulated DCS bridge/log history.
local root = assert(arg[1])
local guard = dofile(root .. '/companion/session_guard.lua')
local count = 0
local function scenario(kind)
    local now, releases, requests, history, callbacks = 0, 0, {}, {}, nil
    local expected = {package='package', fields={'coalition'}, mission={coalition={unit={x=10}}}, description='ORIGINAL'}
    local current = {mission={coalition={unit={x=10}}}}
    local description = 'ORIGINAL'
    local gate
    local function fresh()
        gate = guard.gate('package', function() return now end, function() releases=releases+1 end,
            function(package, token, sequence)
                requests[#requests+1]={package,token,sequence}
                history[#history+1]={message='DCSR_SESSION_REQUEST,'..package..','..token..','..sequence}
            end)
    end
    fresh()
    local logs={}
    local e=setmetatable({
        lfs={writedir=function() return '' end},
        dofile=function(path) if path:find('expected.lua',1,true) then return expected else return guard end end,
        log={INFO=1,write=function(_,_,text) logs[#logs+1]=text end},
        DCS={getCurrentMission=function() return current end,
            getMissionDescription=function() return description end,
            getMissionFilename=function() return '030-Session-Guard-valid.miz' end,
            getRealTime=function() return now end,
            getLogHistory=function(index)
                local out={};for i=index+1,#history do out[#out+1]=history[i] end
                return out,#history
            end,
            setUserCallbacks=function(value) callbacks=value end},
        a_do_script=function(code)
            local fn=assert(loadstring(code));setfenv(fn,{DCSR_SESSION_CONTROL=gate,
                tostring=tostring,env={info=function(message)
                    if kind=='missing_ack' and message:find('DCSR_SESSION_ARMED,',1,true)==1 then return end
                    history[#history+1]={message=message}
                end}})
            local result=fn()
            if kind=='inner_dropped_return' then return nil end
            return result
        end,
    },{__index=_G})
    if kind~='missing_bridge' then
        -- Reproduce the observed hook context: a_do_script exists only in the
        -- target mission context, never in this user-hook environment.
        local mission_context={a_do_script=e.a_do_script,tostring=tostring}
        e.a_do_script=false
        e.net={dostring_in=function(target,code)
            assert(target=='mission')
            if kind=='transport_only' then return '',true end
            if kind=='bridge_denied' then return nil,'access denied' end
            local fn=assert(loadstring(code));setfenv(fn,mission_context)
            local result=fn()
            if kind=='dropped_return' then return '',true end
            return result
        end}
    end
    e.a_do_script=false
    local hook=assert(loadfile(root..'/experiments/efm-ownership/session-guard/hook.lua'))
    setfenv(hook,e);hook()
    callbacks.onSimulationStart();callbacks.onSimulationFrame()
    if kind=='missing_bridge' or kind=='transport_only' or kind=='bridge_denied' then
        assert(not gate.request() and releases==0 and gate.status()=='unverified')
    else
        assert(gate.status()=='ready','Release blocked: '..gate.status())
        if kind=='edited_loaded_matching_path' then description='EDITED' end
        if kind=='placement_changed' then current.mission.coalition.unit.x=11 end
        assert(gate.request());assert(not gate.request(),'duplicate request')
        if kind=='stale' then now=2 end
        if kind=='restart' then
            local old=requests[#requests]
            callbacks.onSimulationStop();fresh();callbacks.onSimulationStart();callbacks.onSimulationFrame()
            assert(gate.request())
            assert(not gate.answer(old[1],old[2],old[3],true),'old session approved new request')
        end
        callbacks.onSimulationFrame()
        if kind=='dropped_return' or kind=='inner_dropped_return' or kind=='missing_ack' then now=2;gate.expire() end
        local allowed=kind=='valid' or kind=='restart' or kind=='mission_bridge' or
            kind=='dropped_return' or kind=='inner_dropped_return'
        assert(releases==(allowed and 1 or 0),kind..': '..gate.status())
        if kind=='missing_ack' then assert(gate.status()=='refused','missing acknowledgment did not time out') end
        if allowed then
            local request=requests[#requests]
            assert(not gate.answer(request[1],request[2],request[3],true),'duplicate approval')
            assert(releases==1)
        end
    end
    count=count+1
end
for _,kind in ipairs({'dropped_return','inner_dropped_return','missing_ack','mission_bridge','valid','missing_bridge','transport_only','bridge_denied','edited_loaded_matching_path','placement_changed','stale','restart'}) do scenario(kind) end
local now, released=0,0
local gate=guard.gate('p',function()return now end,function()released=released+1 end,function()end)
assert(not gate.request(),'missing hook permitted release')
assert(gate.arm('p','session'));assert(gate.request())
assert(not gate.answer('wrong','session',1,true))
assert(not gate.answer('p','session',2,true))
now=2;gate.expire();assert(gate.status()=='refused')
assert(not gate.answer('p','session',1,true) and released==0)
gate=guard.gate('p',function()return now end,function()released=released+1 end,function()end)
assert(gate.arm('p','session'));assert(gate.request());now=0/0
assert(not gate.answer('p','session',1,true) and released==0,'nonfinite clock released')
assert(guard.difference({[1]='a'},{['1']='a'},'root'),'key types conflated')
assert(guard.difference({a=1},{a=1,b=2},'root'),'unknown field ignored')
print('PASS: '..count..' hook/mission integration cases; missing hook, wrong package/sequence, timeout, NaN, key types, unknown fields. Mocked DCS only.')
