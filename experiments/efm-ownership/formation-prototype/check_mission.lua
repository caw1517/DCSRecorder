-- Exercise a generated formation control script with stubbed mission APIs.
-- Usage: luae.exe check_mission.lua <control.lua> <namespace>
local path,namespace=assert(arg[1]),assert(arg[2])
local function run(mode,record)
    local now,queue,logs,notices,flags,commands=0,{},{},{},{},{}
    env={info=function(text)logs[#logs+1]=text end}
    trigger={action={outText=function(text)notices[#notices+1]=text end,setUserFlag=function(k,v)flags[k]=v end}}
    timer={getTime=function()return now end,scheduleFunction=function(fn,param,t)queue[#queue+1]={fn,param,t}end}
    local menus={}
    missionCommands={addSubMenu=function(name,parent)menus[#menus+1]=name;return #menus end,
        addCommand=function(name,menu,fn)assert(menu>=1 and menu<=#menus,'command outside the owned menu');commands[name]=fn end}
    local chunk=assert(loadfile(path))
    -- Units are created by name once the config is known (it is the chunk's first line).
    local units,state={}, {}
    local function config()return _G[namespace..'_CONFIG']end
    local function make(name,index)
        local u={name=name,index=index,removed=false}
        function u:isExist()return not self.removed end
        function u:destroy()self.removed=true end
        function u:getPosition()return {p={x=index,y=0,z=0},x={x=1,y=0,z=0},y={x=0,y=1,z=0}}end
        function u:getVelocity()return {x=0,y=0,z=0}end
        function u:getController()return {setCommand=function()end}end
        function u:getDrawArgumentValue(i)
            local cfg=config().positions[self.index]
            local status=state[self.index] or (mode=='none_ready' and 0 or .125)  -- every position, however many
            if status==0 then return 0 end
            if i==997 then return cfg.token_high end
            if i==998 then return cfg.token_low end
            if i==999 then return status end
            if i==996 then return 0 end
            return cfg.expected[i] or 0
        end
        return u
    end
    Unit={getByName=function(name)
        if units[name]==nil then
            for i,p in ipairs(config().positions)do if p.name==name then units[name]=make(name,i)end end
            if units[name]==nil then units[name]=make(name,0);units[name].player=true end
        end
        return units[name]
    end}
    local before={};for k in pairs(_G)do before[k]=true end
    if mode=='one_never_ready' then state[2]=0 end

    -- Recording against the formation: a stub recorder stands in for the injected
    -- one (its own global guard then skips it) and keeps what it is told.
    local recorder={began={},events={}}
    if record then
        _G[namespace..'_REC']={begin_formation=function(extra)recorder.began[#recorder.began+1]={extra,now};return true end,
            event=function(kind,association,t)recorder.events[#recorder.events+1]={kind,association,t}end}
    end
    chunk()
    local s=_G[namespace]
    local c=config()
    assert(s and c and #c.positions>=1,'formation config missing')
    for k in pairs(_G)do
        assert(before[k] or k:sub(1,#namespace)==namespace,'created unowned global '..tostring(k))
    end
    -- The injected recorder itself is exercised by check_recorder.lua.
    if not record then c.record=nil end
    if record then
        c.record={formation=string.rep('f',32),version=3}
        for i,p in ipairs(c.positions)do p.association=string.rep(tostring(i),32)end
    end
    local a,b=c.positions[1].name,c.positions[2] and c.positions[2].name
    local function advance(to)
        while #queue>0 do
            table.sort(queue,function(x,y)return x[3]<y[3]end)
            if queue[1][3]>to then break end
            local item=table.remove(queue,1);now=item[3]
            local next_time=item[1](item[2],now)
            if next_time then queue[#queue+1]={item[1],item[2],next_time}end
        end
        now=to
    end
    local function logged(pattern)for _,l in ipairs(logs)do if l:find(pattern,1,true)then return true end end;return false end
    local function release()
        assert(s.arm('sess_1',1),'arm refused with every live aircraft ready')
        commands['Start playback (3-second countdown)']()
        advance(now+3.05)
        assert(s.phase=='requested' and flags[namespace..'_PENDING']==1,'countdown did not request release')
        assert(s.released('sess_1',1,now) and s.phase=='running','release acknowledgment')
        if record then
            assert(#recorder.began==1 and recorder.began[1][2]==now,'recording did not begin once at the release')
            assert(recorder.began[1][1]==string.format('formation_id,%s\nformation_version,3\nformation_epoch,%.9f\n',string.rep('f',32),now),
                'recording metadata: '..recorder.began[1][1])
            recorder.epoch=now
        end
        for i in ipairs(c.positions)do state[i]=.25 end
        advance(now+.1)
    end
    if mode=='none_ready' then
        advance(16)
        assert(s.phase=='failed' and flags[namespace..'_CLEANUP']==1,'no ready aircraft did not fail and clean up the hold')
        return
    end
    advance(.5)
    if mode=='one_never_ready' then
        assert(not s.arm('sess_1',1),'armed before the slow aircraft resolved')
        advance(16)
        assert(s.positions[2].phase=='failed' and units[b].removed and not units[a].removed,'slow aircraft not removed alone')
        assert(s.positions[1].phase=='ready' and s.phase=='preparing','other aircraft disturbed')
        release()
        assert(s.positions[1].phase=='playing','remaining aircraft did not play')
        if record then
            assert(#recorder.events==1 and recorder.events[1][1]=='not_ready' and recorder.events[1][2]==c.positions[2].association and
                recorder.events[1][3]==nil,'not-ready aircraft not recorded')
        end
        return
    end
    for _,p in ipairs(s.positions)do assert(p.phase=='ready','aircraft not ready: '..p.name)end
    release()
    for _,p in ipairs(s.positions)do assert(p.phase=='playing','aircraft not playing: '..p.name)end
    if mode=='single' then
        state[1]=c.positions[1].parked and .375 or .5
        advance(now+.1)
        assert(s.positions[1].phase==(c.positions[1].parked and 'parked' or 'complete'),'aircraft did not reach its own ending')
        if record then
            assert(#recorder.events==1 and recorder.events[1][1]=='ended' and recorder.events[1][2]==c.positions[1].association,'ending not recorded')
        end
        _G[namespace..'_REC']=nil
        return
    end
    if mode=='destroy' then
        commands['Destroy: '..a]()
        advance(now+.1)
        assert(logged('FAULT,destroy,'..a),'destroy fault not logged')
    elseif mode=='abort' then
        commands['Native abort: '..a]()
        assert(logged('ABORT_REQUEST,'..a),'abort request not logged for the hook')
        state[1]=.75 -- the native controller's failed status after the hook's abort
        advance(now+.1)
    end
    assert(s.positions[1].phase=='failed' and units[a].removed,'removed aircraft still flying')
    assert(logged('POSITION_FAILED,'..a),'per-aircraft failure not logged')
    assert(s.positions[2].phase=='playing' and not units[b].removed and s.phase=='running','other aircraft stopped')
    advance(now+1)
    assert(s.positions[2].phase=='playing','other aircraft stopped later')
    state[2]=c.positions[2].parked and .375 or .5
    advance(now+.1)
    assert(s.positions[2].phase==(c.positions[2].parked and 'parked' or 'complete'),'remaining aircraft did not reach its own ending')
    assert(flags[namespace..'_CLEANUP']~=1,'a released formation requested hold cleanup')
    if record then
        local failed,ended=recorder.events[1],recorder.events[2]
        assert(#recorder.events==2 and failed[1]=='failed' and failed[2]==c.positions[1].association and
            failed[3]>.09 and failed[3]<.25,'failure not recorded with its replay time')
        assert(ended[1]=='ended' and ended[2]==c.positions[2].association and ended[3]>failed[3],'ending not recorded')
    end
    _G[namespace..'_REC']=nil
end
-- A formation of one playing aircraft (recording #2 against version 1): `single`.
local modes,recording={'destroy','abort','one_never_ready','none_ready'},{'destroy','one_never_ready'}
if arg[3]=='single' then modes,recording={'single'},{'single'} end
for _,mode in ipairs(modes)do run(mode) end
for _,mode in ipairs(recording)do run(mode,true) end
print('PASS: formation control releases every ready aircraft on the shared epoch; destroy, native abort and readiness timeouts remove one aircraft alone; a recording begins at the release and records not-ready, failed and ended aircraft')
