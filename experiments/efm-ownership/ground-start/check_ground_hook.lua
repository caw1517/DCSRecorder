local path=assert(arg[1])
local function run(mode)
    local e=setmetatable({},{__index=_G})
    local now,history,calls,commits,dispatches,aborts=0,{}, {},0,0,0
    local callbacks,session
    local expected={high=.2,low=.3,fields={'coalition'},mission={coalition={name='test'}},description='test'}
    e.lfs={writedir=function()return 'test/'end}
    e.dofile=function(file)
        if file:find('expected.lua',1,true) then return expected end
        return {difference=function(a,b)return a.name~=b.name end}
    end
    e.log={INFO=1,write=function(_,_,message)
        calls[#calls+1]=message
        session=session or message:match('^START,([%w_]+)$')
    end}
    e.DCS={getModelTime=function()return now end,getMissionFilename=function()return '049-Hornet-Ground-Hold-Release.miz'end,
        getCurrentMission=function()return {coalition={name=mode=='mismatch' and 'wrong' or 'test'}}end,
        getMissionDescription=function()return 'test'end,
        getLogHistory=function(index)local r={};for i=index+1,#history do r[#r+1]=history[i]end;return r,#history end,
        setUserCallbacks=function(c)callbacks=c end}
    e.package={loadlib=function(_,symbol)
        assert(symbol=='dcs_release_control')
        return function(command,high,low,generation)
            assert(high==.2 and low==.3)
            if command=='inspect' then return 'READY,1,'..now..',0'end
            assert(generation==1)
            if command=='abort' then aborts=aborts+1;return 'ABORTED,1'end
            commits=commits+1
            return mode=='refused' and 'REFUSED,not_ready_or_consumed' or 'COMMITTED,1,'..now
        end
    end}
    e.net={dostring_in=function(target,code)
        assert(target=='mission')
        if code:find('a_set_command(816)',1,true) then
            dispatches=dispatches+1
            if mode~='no_ack' then history[#history+1]={message='DCSR_RELEASE PLAYER_RELEASED,'..session..',1,'..now}end
        end
    end}
    local chunk=assert(loadfile(path));setfenv(chunk,e);chunk()
    callbacks.onSimulationStart();callbacks.onSimulationFrame()
    now=3
    history[#history+1]={message='DCSR_RELEASE REQUEST,'..(mode=='stale_session' and 'old' or session)..',1,3.000000000'}
    history[#history+1]=history[#history]
    callbacks.onSimulationFrame();callbacks.onSimulationFrame()
    if mode=='mismatch' or mode=='stale_session' then assert(commits==0 and dispatches==0);return end
    if mode=='refused' then assert(commits==1 and dispatches==0 and aborts==1);return end
    assert(commits==1 and dispatches==1,'duplicate commit or dispatch')
    -- Wall time is absent; frames at the same model time cannot age the ack.
    for i=1,100 do callbacks.onSimulationFrame()end
    if mode=='no_ack' then assert(aborts==0);now=4.1;callbacks.onSimulationFrame();assert(aborts==1);return end
    assert(aborts==0)
    callbacks.onSimulationStop();history[#history+1]={message='DCSR_RELEASE REQUEST,'..session..',1,3.000000000'}
    callbacks.onSimulationFrame();assert(commits==1)
    callbacks.onSimulationStart();callbacks.onSimulationFrame();assert(commits==1,'restart consumed old log request')
end
for _,mode in ipairs({'success','mismatch','stale_session','refused','no_ack'})do run(mode)end
print('PASS: hook commit/dispatch once, loaded-field mismatch, stale session, native refusal, pause, missing ack and restart')
