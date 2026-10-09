-- Exercise a generated formation hook with stubbed DCS callbacks and a stub
-- controller bridge. Usage: luae.exe check_hook.lua <payload dir> <control> <namespace>
local payload,control,namespace=assert(arg[1]),assert(arg[2]),assert(arg[3])
local dir=payload..'/Scripts/'..control..'/'
local expected=dofile(dir..'expected.lua')
local guard=dofile(dir..'session_guard.lua')
assert(#expected.positions>=1,'expected.lua lists no positions')
local function copy(v)
    if type(v)~='table' then return v end
    local out={};for k,x in pairs(v)do out[k]=copy(x)end;return out
end
local function run(mode)
    local logs,callbacks,history,now,calls,missions={},nil,{},0,{},{}
    local loaded={mission=copy(expected.mission)}
    if mode=='mismatch' then loaded.mission.weather=loaded.mission.weather or {};loaded.mission.weather.edited=true end
    local runtime={}
    for i,p in ipairs(expected.positions)do runtime[p.unit_id]=16777216+i*256 end
    if mode=='late_runtime' then runtime[expected.positions[2].unit_id]=0 end
    -- Stub controller: one object per runtime ID, addressed by bridge key.
    local objects={}
    local function key(high,low)
        for i,p in ipairs(expected.positions)do if p.high==high and p.low==low then return i end end
    end
    local e=setmetatable({},{__index=_G})
    e.lfs={writedir=function()return 'unused/'end}
    e.dofile=function(path)return path:find('expected.lua',1,true) and expected or guard end
    e.log={INFO=1,write=function(_,_,message)logs[#logs+1]=message end}
    e.DCS={UNIT_RUNTIME_ID=7,getModelTime=function()return now end,getMissionFilename=function()return expected.mission_name end,
        getCurrentMission=function()return loaded end,getMissionDescription=function()return expected.description end,
        getUnitProperty=function(id,property)assert(property==7);return runtime[id] end,
        getLogHistory=function(index)local r={};for i=index+1,#history do r[#r+1]=history[i]end;return r,#history end,
        setUserCallbacks=function(c)callbacks=c end}
    e.package={loadlib=function(path,export)
        assert(export=='dcs_release_control' and path:find('/'..expected.binary..'.dll',1,true),'unexpected DLL '..path)
        return function(command,high,low,third,epoch)
            local i=key(high,low);calls[#calls+1]={command,i,third,epoch}
            if not i then return 'REFUSED,object_or_package' end
            if command=='assign' then
                assert(third==16777216+i*256,'take assigned to the wrong runtime ID')
                objects[i]={generation=10+i};return 'ASSIGNED,'..(10+i)..','..third
            end
            local o=objects[i]
            if not o or o.aborted then return 'REFUSED,object_or_package' end
            if command=='inspect' then return 'READY,'..o.generation..','..now..',0' end
            if third~=o.generation then return 'REFUSED,object_or_package' end
            if command=='commit' then
                assert(epoch==now,'commit epoch is not the model time of the commit callback')
                if mode=='commit_refused' and i==1 then return 'REFUSED,not_ready_or_consumed' end
                o.committed=true;return 'COMMITTED,'..o.generation..','..now
            end
            if command=='abort' then o.aborted=true;return 'ABORTED,'..o.generation end
        end end}
    e.net={dostring_in=function(target,code)
        assert(target=='mission' and code:find(namespace,1,true),'bridge call outside the owned namespace')
        missions[#missions+1]=code
        if code:find('a_set_command(816)',1,true)then
            local session,epoch=code:match('released%(\\?"([%w_]+)\\?",1,([%d.]+)%)')
            assert(math.abs(tonumber(epoch)-now)<1e-9,'player release not on the formation epoch')
            history[#history+1]={message=namespace..' PLAYER_RELEASED,'..session..',1,'..now}
        end
    end}
    local chunk=assert(loadfile(payload..'/Scripts/Hooks/'..control..'.lua'));setfenv(chunk,e);chunk()
    for k in pairs(e)do assert(({lfs=1,dofile=1,log=1,DCS=1,package=1,net=1})[k],'hook created global '..tostring(k))end
    local function frame(t)now=t;callbacks.onSimulationFrame()end
    local function sent(pattern)for _,m in ipairs(missions)do if m:find(pattern,1,true)then return true end end;return false end
    local function count(command,i)local n=0;for _,c in ipairs(calls)do if c[1]==command and c[2]==i then n=n+1 end end;return n end
    callbacks.onSimulationStart()
    local session=logs[#logs]:match('^START,([%w_]+),')
    assert(session,'session start not logged')
    frame(0);frame(.2)
    if mode=='late_runtime' then
        assert(objects[1] and not objects[2],'unresolved runtime ID was assigned')
        assert(not sent('.arm('),'armed before every aircraft was assigned')
        runtime[expected.positions[2].unit_id]=16777216+2*256
        frame(.4);frame(.6)
    end
    for i in ipairs(expected.positions)do assert(objects[i],'position '..i..' not assigned')end
    if mode=='mismatch' then
        assert(not sent('.arm('),'armed against a mismatched loaded mission');return
    end
    assert(sent('.arm(') and sent(session),'not armed once every aircraft was ready')
    if mode=='abort' then
        local name=expected.positions[1].name
        history[#history+1]={message=namespace..' ABORT_REQUEST,'..name..',0.700000000'}
        frame(.8)
        assert(objects[1].aborted and not objects[2].aborted,'abort reached the wrong aircraft')
        assert(sent('fail_position(') and sent(name),'mission not told to remove the aborted aircraft')
    end
    history[#history+1]={message=namespace..' REQUEST,'..session..',1,'..string.format('%.9f',now)}
    frame(now+.01);frame(now+.02)
    local released=mode=='abort' and {2} or mode=='commit_refused' and {2} or {}
    if #released==0 then for i in ipairs(expected.positions)do released[i]=i end end
    for _,i in ipairs(released)do assert(objects[i].committed,'aircraft '..i..' not committed')end
    if mode~='normal' and mode~='late_runtime' then assert(not objects[1].committed,'dropped aircraft committed')end
    if mode=='commit_refused' then assert(objects[1].aborted and sent('fail_position('),'refused commit not dropped alone')end
    assert(sent('a_set_command(816)'),'player release not dispatched')
    local epochs={}
    for _,c in ipairs(calls)do if c[1]=='commit' then epochs[c[4]]=true end end
    local shared=0;for _ in pairs(epochs)do shared=shared+1 end
    assert(shared==1,'aircraft committed on more than one epoch')
    local commits=0;for _,m in ipairs(logs)do if m:match('^COMMIT,')then commits=commits+1 end end
    assert(commits==1,'formation epoch not logged exactly once')
    for i in ipairs(expected.positions)do assert(count('assign',i)==1,'repeated assignment')end
    frame(now+2)
    for _,m in ipairs(missions)do if m:find('.fail(',1,true)then error(mode..': released formation failed: '..m..' | '..table.concat(logs,' ; '))end end
end
-- A formation of one playing aircraft (recording #2 against version 1) has no pair to isolate.
local modes=#expected.positions>1 and {'normal','late_runtime','abort','commit_refused','mismatch'} or {'normal','mismatch'}
for _,mode in ipairs(modes)do run(mode)end
print('PASS: formation hook assigns each take to its runtime ID, arms only when all are ready, commits every aircraft on one shared epoch, and releases or drops aircraft individually')
