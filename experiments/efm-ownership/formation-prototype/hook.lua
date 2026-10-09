-- Formation prototype control hook. Generalizes release-start/hook.lua: each
-- playback position's mission unit ID is mapped to its native runtime ID
-- (DCS.UNIT_RUNTIME_ID, proven equal to ed_get_object_id) and the controller is
-- told which recorded flight that aircraft owns. Release commits every live
-- aircraft in one callback. Mission scripting remains sanitized.
local dir=lfs.writedir()..'Scripts/DCSRecorderFormationControl/'
local expected=dofile(dir..'expected.lua')
local guard=dofile(dir..'session_guard.lua')
local hooks,serial={},0
local active,reader,index,session,consumed,ack,requested_at,next_arm,next_assign
local positions,last_readiness
local function emit(text)log.write('DCSR_FORMATION_BRIDGE',log.INFO,text)end
local function q(value)return string.format('%q',value)end
local function script(code)return 'a_do_script('..q(code)..')'end
local function bridge(code)return net.dostring_in('mission',code)end
local function matching()
    local current=DCS.getCurrentMission()
    if type(current)~='table' then return false,'loaded_mission_unavailable' end
    local mission=current.mission or current
    for _,field in ipairs(expected.fields)do
        local difference=guard.difference(expected.mission[field],mission[field],field)
        if difference then return false,tostring(difference) end
    end
    if expected.description~=DCS.getMissionDescription() then return false,'localized_description:value' end
    return true,'matched'
end
local function native(command,p,third,epoch)
    return reader(command,p.high,p.low,third or p.generation or 0,epoch)
end
-- One aircraft leaves the formation; the others continue.
local function drop(p,reason)
    if p.gone then return end
    p.gone=true
    if p.generation then emit('ABORT,'..p.name..','..native('abort',p))end
    emit('POSITION_DROPPED,'..p.name..','..reason)
    bridge(script('if DCSR_FORMATION then DCSR_FORMATION.fail_position('..q(p.name)..','..q(reason)..') end'))
end
local function fail(reason)
    if reader then for _,p in ipairs(positions)do if p.generation and not p.gone then native('abort',p)end end end
    active=false
    emit('FAILED,'..reason)
    bridge(script('if DCSR_FORMATION then DCSR_FORMATION.fail('..q(reason)..') end'))
end
local function live()
    local out={};for _,p in ipairs(positions)do if not p.gone then out[#out+1]=p end end;return out
end
local function assign(now)
    if now<next_assign then return end
    next_assign=now+.1
    for _,p in ipairs(positions)do
        if not p.gone and not p.generation then
            local ok,runtime=pcall(DCS.getUnitProperty,p.unit_id,DCS.UNIT_RUNTIME_ID)
            runtime=ok and tonumber(runtime)
            if runtime and runtime>0 then
                local reply=native('assign',p,runtime)
                local generation=reply:match('^ASSIGNED,(%d+),')
                emit(string.format('ASSIGN,%s,mission=%s,runtime=%s,%s',p.name,tostring(p.unit_id),tostring(runtime),reply))
                if generation then p.generation=tonumber(generation);p.runtime=runtime
                elseif reply~='REFUSED,object_unavailable' then drop(p,'assign_'..reply) end
            end
        end
    end
end
local function arm(now)
    if consumed or now<next_arm then return end
    next_arm=now+.1
    local remaining=live()
    local readiness='arming'
    if #remaining==0 then readiness='no_live_aircraft' end
    for _,p in ipairs(remaining)do
        if not p.generation then readiness='awaiting_assignment';break end
        local reply=native('inspect',p,0)
        local generation,stamp=reply:match('^READY,(%d+),([^,]+),0$')
        if reply:match('^REFUSED')then drop(p,'native_'..reply);readiness='dropped';break end
        if tonumber(generation)~=p.generation then readiness='native_not_ready:'..p.name;break end
        if math.abs(now-tonumber(stamp))>.1 then readiness='clock_difference:'..p.name;break end
    end
    if readiness=='arming' then
        local matches,reason=matching()
        if not matches then readiness='loaded_mismatch:'..reason end
    end
    if readiness~=last_readiness then
        last_readiness=readiness
        emit(string.format('READINESS state=%s model=%.9f live=%d',readiness,now,#remaining))
    end
    if readiness=='arming' then
        bridge(script('if DCSR_FORMATION then DCSR_FORMATION.arm('..q(session)..',1) end'))
    end
end
local function release(now,stamp)
    consumed=true;requested_at=now
    if now-tonumber(stamp)<0 or now-tonumber(stamp)>1 or not matching() then fail('stale_or_mismatched_request');return end
    local committed={}
    for _,p in ipairs(live())do
        local inspect=native('inspect',p,0)
        local generation,native_time=inspect:match('^READY,(%d+),([^,]+),0$')
        local result=tonumber(generation)==p.generation and math.abs(now-tonumber(native_time or '-99'))<=.1 and native('commit',p,nil,now) or inspect
        if result:match('^COMMITTED,'..p.generation..',')then committed[#committed+1]=p.name..'='..result
        else drop(p,'commit_refused:'..result) end
    end
    if #committed==0 then fail('native_commit_refused');return end
    -- One formation epoch: every committed aircraft and the player share it.
    emit(string.format('COMMIT,%s,%.9f,%s',session,now,table.concat(committed,'|')))
    -- Same callback as the commits: the player's hold ends with the aircraft's.
    bridge('if c_flag_is_true("DCSR_FORMATION_PENDING") then a_set_command(816); '..
        script('DCSR_FORMATION.released('..q(session)..',1,'..string.format('%.9f',now)..')')..'; end')
end
local function pump()
    if not active then return end
    local now=DCS.getModelTime()
    local entries,tail=DCS.getLogHistory(index)
    assert(type(entries)=='table' and type(tail)=='number' and tail>=index,'history_unavailable')
    index=tail
    assign(now)
    arm(now)
    for _,entry in ipairs(entries)do
        local message=entry.message or entry[4] or ''
        local token,gen,stamp=message:match('^DCSR_FORMATION REQUEST,([%w_]+),(%d+),([%d.]+)%s*$')
        if token==session and tonumber(gen)==1 and not consumed then release(now,stamp);if not active then return end end
        local released=message:match('^DCSR_FORMATION PLAYER_RELEASED,([%w_]+),1,')
        if released==session and consumed then ack=true;emit('ACK,'..message)end
        local abort=message:match('^DCSR_FORMATION ABORT_REQUEST,(.-),[%d.]+%s*$')
        local failed=message:match('^DCSR_FORMATION POSITION_FAILED,(.-),')
        for _,p in ipairs(positions)do
            if p.name==abort then drop(p,'developer_native_abort')end
            if p.name==failed and not p.gone then p.gone=true;if p.generation then emit('ABORT,'..p.name..','..native('abort',p))end end
        end
        if message:match('^DCSR_FORMATION FAILED,') then
            for _,p in ipairs(positions)do if p.generation and not p.gone then native('abort',p)end end
            active=false;return
        end
    end
    if consumed and not ack and now-requested_at>1 then fail('player_release_ack_missing')end
end
local function reset()
    active,reader,consumed,ack=false,nil,false,false
    last_readiness=nil;next_arm=0;next_assign=0
    positions={}
    for i,p in ipairs(expected.positions)do
        positions[i]={name=p.name,unit_id=p.unit_id,high=p.high,low=p.low}
    end
end
function hooks.onMissionLoadBegin()reset()end
function hooks.onSimulationStart()
    reset()
    local filename=DCS.getMissionFilename() or ''
    if not filename:find(expected.mission_name,1,true) then
        local ok,matches=pcall(matching)
        if not (ok and matches) then return end
        if not filename:lower():find('tempmission%.miz$') then emit('NOT_SELECTED,'..filename);return end
        emit('SELECTED_BY_CONTENT,'..filename)
    end
    serial=serial+1;session=string.format('%d_%d',os.time(),serial)
    local _,tail=DCS.getLogHistory(0);index=assert(tail)
    reader=assert(package.loadlib(lfs.writedir()..'Mods/aircraft/'..expected.module..'/bin/'..expected.binary..'.dll','dcs_release_control'))
    active=true;emit('START,'..session..',prepared='..expected.prepared_sha256..',scene='..expected.scene_sha256..',positions='..#positions)
end
function hooks.onSimulationFrame()
    local ok,err=pcall(pump)
    if not ok then
        pcall(fail,'hook_error_'..tostring(err));active=false
    end
end
function hooks.onSimulationStop()reset()end
reset()
DCS.setUserCallbacks(hooks)
