-- Exercise a generated authored playback hook with stubbed DCS callbacks.
-- Usage: luae.exe check_authored_hook.lua <payload dir> <control> <mission file> <namespace>
local payload,control,mission_file,namespace=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4])
local dir=payload..'/Scripts/'..control..'/'
local expected=dofile(dir..'expected.lua')
local guard=dofile(dir..'session_guard.lua')
for _,key in ipairs({'take_sha256','prepared_sha256','scene_sha256'})do
    assert(type(expected[key])=='string' and #expected[key]==64,'approval reference is not bound to '..key)
end
local function copy(v)
    if type(v)~='table' then return v end
    local out={};for k,x in pairs(v)do out[k]=copy(x)end;return out
end
local function first_plane(m)
    for _,c in pairs(m.coalition)do for _,country in pairs(c.country or {})do
        for _,g in pairs((country.plane or {}).group or {})do return g end
    end end
end
-- request: nil (none), 'valid', 'stale_session', 'old_timestamp', 'duplicate', 'restart'
local function run(edit,filename,native_reply,request)
    local armed,logs,callbacks,history,now,commits,dispatches,failures=false,{},nil,{},0,0,0,{}
    local session
    local loaded={mission=copy(expected.mission)}
    local m=loaded.mission
    if edit=='position' then local u=first_plane(m).units[1];u.x=u.x+1
    elseif edit=='trigger' then local _,r=next(m.trigrules);r.comment=(r.comment or '')..' edited'
    elseif edit=='extra_aircraft' then
        local _,c=next(m.coalition.blue.country);local g=c.plane.group;g[#g+1]=copy(g[1])
    elseif edit=='weather' then m.weather.wind.atGround.speed=1 end
    local description=edit=='briefing' and expected.description..' edited' or expected.description
    local e=setmetatable({},{__index=_G})
    e.lfs={writedir=function()return 'unused/'end}
    e.dofile=function(path)return path:find('expected.lua',1,true) and expected or guard end
    e.log={INFO=1,write=function(_,_,message)
        logs[#logs+1]=message
        session=message:match('^START,([%w_]+),') or session
    end}
    e.DCS={getModelTime=function()return now end,getMissionFilename=function()return filename or mission_file end,
        getCurrentMission=function()return loaded end,getMissionDescription=function()return description end,
        getLogHistory=function(index)local r={};for i=index+1,#history do r[#r+1]=history[i]end;return r,#history end,
        setUserCallbacks=function(c)callbacks=c end}
    e.package={loadlib=function(path,export)
        assert(path:find('/'..control,1,true)==nil and path:find('HornetAuthoredProbe.dll',1,true),'unexpected DLL '..path)
        return function(command)
            if command=='inspect' then return native_reply or ('READY,1,'..now..',0')end
            if command=='commit' then commits=commits+1;return 'COMMITTED,1,'..now end
            return 'ABORTED,1'
        end end}
    e.net={dostring_in=function(target,code)
        assert(target=='mission' and code:find(namespace,1,true),'bridge call outside the owned namespace')
        if code:find(namespace..'.arm(',1,true)then armed=true end
        if code:find(namespace..'.fail(',1,true)then failures[#failures+1]=code end
        if code:find('a_set_command(816)',1,true)then
            dispatches=dispatches+1
            history[#history+1]={message=namespace..' PLAYER_RELEASED,'..session..',1,'..now}
        end
    end}
    local chunk=assert(loadfile(payload..'/Scripts/Hooks/'..control..'.lua'));setfenv(chunk,e);chunk()
    -- Ownership: user callbacks are additive per hook; this one registers only these.
    for name in pairs(callbacks)do
        assert(({onMissionLoadBegin=1,onSimulationStart=1,onSimulationFrame=1,onSimulationStop=1})[name],'unexpected callback '..name)
    end
    for k in pairs(e)do
        assert(({lfs=1,dofile=1,log=1,DCS=1,package=1,net=1})[k],'hook created global '..tostring(k))
    end
    callbacks.onSimulationStart();callbacks.onSimulationFrame()
    local start=table.concat(logs,'\n')
    assert(filename or start:find('take='..expected.take_sha256..',prepared='..expected.prepared_sha256..',scene='..expected.scene_sha256,1,true),
        'session start did not log its take/revision binding')
    if request then
        now=3
        local token=request=='stale_session' and 'old_session' or session
        local stamp=request=='old_timestamp' and '1.000000000' or '3.000000000'
        history[#history+1]={message=namespace..' REQUEST,'..token..',1,'..stamp}
        if request=='duplicate' then history[#history+1]=history[#history]end
        callbacks.onSimulationFrame();callbacks.onSimulationFrame()
        if request=='restart' then
            -- A fresh session must not honor a request logged for the previous one.
            local old=session;commits,dispatches=0,0
            callbacks.onSimulationStop();callbacks.onMissionLoadBegin();callbacks.onSimulationStart()
            assert(session~=old,'restart reused the session')
            history[#history+1]={message=namespace..' REQUEST,'..old..',1,3.000000000'}
            callbacks.onSimulationFrame()
        end
    end
    return armed,table.concat(logs,'\n'),commits,dispatches,#failures
end
local armed,logs=run(nil)
assert(armed,'Hook did not arm against its own predicted loaded mission:\n'..logs)
for _,edit in ipairs({'position','trigger','extra_aircraft','weather','briefing'})do
    assert(not run(edit),'Hook armed despite loaded edit: '..edit)
end
assert(not run(nil,'some-other-mission.miz'),'Hook armed for another mission')
assert(not run(nil,nil,'NOT_READY,0,0,0'),'Hook armed without native readiness')
local _,_,commits,dispatches=run(nil,nil,nil,'valid')
assert(commits==1 and dispatches==1,'valid approval did not release exactly once')
_,_,commits,dispatches=run(nil,nil,nil,'duplicate')
assert(commits==1 and dispatches==1,'duplicate request released twice')
_,_,commits,dispatches=run(nil,nil,nil,'stale_session')
assert(commits==0 and dispatches==0,'request from another session released')
local failures
_,_,commits,dispatches,failures=run(nil,nil,nil,'old_timestamp')
assert(commits==0 and dispatches==0 and failures==1,'stale request released')
_,_,commits,dispatches=run(nil,nil,nil,'restart')
assert(commits==0 and dispatches==0,'restart honored a previous session request')
print('PASS: authored hook binds take/revision, arms only for its exact loaded mission and native readiness, and refuses stale, duplicate and cross-session approval')
