-- Additive, isolated diagnostic; mission scripting remains sanitized.
local dir=lfs.writedir()..'Scripts/DCSRecorderReleaseControl/'
local expected=dofile(dir..'expected.lua')
local guard=dofile(dir..'session_guard.lua')
local hooks,serial={},0
local active,reader,index,session,generation,consumed,ack,requested_at,next_arm
local last_readiness
local function emit(text)log.write('DCSR_RELEASE_BRIDGE',log.INFO,text)end
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
local function native(command,gen)
    return reader(command,expected.high,expected.low,gen or generation or 0)
end
local function fail(reason)
    if reader and generation then native('abort')end
    active=false
    emit('FAILED,'..reason)
    bridge(script('if DCSR_RELEASE then DCSR_RELEASE.fail('..q(reason)..') end'))
end
local function pump()
    if not active then return end
    local now=DCS.getModelTime()
    local entries,tail=DCS.getLogHistory(index)
    assert(type(entries)=='table' and type(tail)=='number' and tail>=index,'history_unavailable')
    index=tail
    if not consumed and now>=next_arm then
        next_arm=now+.1
        local reply=native('inspect',0)
        local gen,stamp=reply:match('^READY,(%d+),([^,]+),0$')
        local matches,reason=matching()
        local readiness=not gen and 'native_not_ready' or
            math.abs(now-tonumber(stamp))>.1 and 'clock_difference' or
            not matches and ('loaded_mismatch:'..reason) or 'arming'
        if readiness~=last_readiness then
            last_readiness=readiness
            emit(string.format('READINESS state=%s model=%.9f native=%s',readiness,now,tostring(reply)))
        end
        if readiness=='arming' then
            generation=tonumber(gen)
            bridge(script('if DCSR_RELEASE then DCSR_RELEASE.arm('..q(session)..','..gen..') end'))
        end
    end
    for _,entry in ipairs(entries)do
        local message=entry.message or entry[4] or ''
        local token,gen,stamp=message:match('^DCSR_RELEASE REQUEST,([%w_]+),(%d+),([%d.]+)%s*$')
        if token==session and tonumber(gen)==generation and not consumed then
            consumed=true;requested_at=now
            if now-tonumber(stamp)<0 or now-tonumber(stamp)>1 or not matching() then fail('stale_or_mismatched_request');return end
            local inspect=native('inspect')
            local ready_gen,native_time=inspect:match('^READY,(%d+),([^,]+),0$')
            if tonumber(ready_gen)~=generation or math.abs(now-tonumber(native_time or '-99'))>.1 then fail('native_not_ready');return end
            local result=native('commit')
            if not result:match('^COMMITTED,'..generation..',') then fail('native_commit_refused');return end
            emit(string.format('COMMIT,%s,%.9f,%s',session,now,result))
            -- The flag is set only by the validated mission countdown. No
            -- delayed trigger scan: issue the command in this same callback.
            bridge('if c_flag_is_true("DCSR_RELEASE_PENDING") then a_set_command(816); '..
                script('DCSR_RELEASE.released('..q(session)..','..generation..')')..'; end')
        end
        local released,released_gen=message:match('^DCSR_RELEASE PLAYER_RELEASED,([%w_]+),(%d+),')
        if released==session and tonumber(released_gen)==generation and consumed then ack=true;emit('ACK,'..message)end
        -- Diagnostic packages only: forward the mission's injected native faults.
        local fault=message:match('^DCSR_RELEASE FAULT,(%a+)%s*$')
        if expected.faults and generation and (fault=='clock' or fault=='state') then
            emit('FAULT,'..fault..','..native('fault_'..fault))
        end
        if message:match('^DCSR_RELEASE FAILED,') then
            if generation then native('abort')end
            active=false;return
        end
    end
    if consumed and not ack and now-requested_at>1 then fail('player_release_ack_missing')end
end
local function reset()
    active,reader,generation,consumed,ack=false,nil,nil,false,false
    last_readiness=nil
    next_arm=0
end
function hooks.onMissionLoadBegin()reset()end
function hooks.onSimulationStart()
    reset()
    -- An in-mission restart may reload DCS's temporary copy, so the file name alone
    -- cannot select it there; the exact loaded-mission comparison still can. Other
    -- names stay unselected, even with identical content.
    local filename=DCS.getMissionFilename() or ''
    if not filename:find('043-Hornet-Countdown-Release.miz',1,true) then
        local ok,matches=pcall(matching)
        if not (ok and matches) then return end
        if not filename:lower():find('tempmission%.miz$') then emit('NOT_SELECTED,'..filename);return end
        emit('SELECTED_BY_CONTENT,'..filename)
    end
    serial=serial+1;session=string.format('%d_%d',os.time(),serial)
    local _,tail=DCS.getLogHistory(0);index=assert(tail)
    reader=assert(package.loadlib(lfs.writedir()..'Mods/aircraft/DCSRecorder-Hornet-Release-Test/bin/HornetReleaseProbe.dll','dcs_release_control'))
    active=true;emit('START,'..session)
end
function hooks.onSimulationFrame()
    local ok,err=pcall(pump)
    if not ok then
        pcall(fail,'hook_error_'..tostring(err));active=false
    end
end
function hooks.onSimulationStop()reset()end
DCS.setUserCallbacks(hooks)
