-- Additive diagnostic. Does not enable unsafe scripting APIs.
local dir = lfs.writedir() .. 'Scripts/DCSRecorderSessionControl/'
local guard = dofile(dir .. 'session_guard.lua')
local expected = dofile(dir .. 'expected.lua') -- generated external reference
local hooks, index, generation = {}, 0, 0
local active, session, armed, bridge_reported, last_result, next_arm
local function emit(text) log.write('DCSR_SESSION', log.INFO, text) end
local function check()
    local current = DCS.getCurrentMission()
    if type(current) ~= 'table' then return false, 'loaded_mission_unavailable' end
    local mission = current.mission or current
    -- Bounded fixture contract; no resource-byte or arbitrary-script proof.
    for _, field in ipairs(expected.fields) do
        local mismatch = guard.difference(expected.mission[field], mission[field], field)
        if mismatch then return false, mismatch end
    end
    local mismatch = guard.difference(expected.description, DCS.getMissionDescription(), 'localized_description')
    if mismatch then return false, mismatch end
    return true, 'bounded_loaded_fields_match'
end
local function bridge(code)
    if type(net)=='table' and type(net.dostring_in)=='function' then
        -- User hook -> mission trigger context -> sanitized mission scripting.
        -- Return propagation varies across DCS contexts. Callers require a
        -- session-bound mission log acknowledgment, never transport success.
        return net.dostring_in('mission', 'return tostring(a_do_script(' .. string.format('%q',code) .. '))')
    end
    if not bridge_reported then
        emit('BRIDGE_UNAVAILABLE net.dostring_in=' .. type(net and net.dostring_in))
        bridge_reported=true
    end
    return nil
end
local function q(value) return string.format('%q', value) end
local function observe()
    local ok, reason = check()
    local result = tostring(ok) .. ':' .. reason
    if result ~= last_result then emit('COMPARE session=' .. session .. ' result=' .. result); last_result=result end
    return ok, reason
end
local function pump()
    if not active then return end
    if not armed and DCS.getRealTime() >= next_arm then
        next_arm = DCS.getRealTime() + 0.5
        observe()
        bridge('local ok=DCSR_SESSION_CONTROL and DCSR_SESSION_CONTROL.arm(' ..
            q(expected.package) .. ',' .. q(session) .. '); if ok==true then env.info(' ..
            q('DCSR_SESSION_ARMED,' .. expected.package .. ',' .. session) .. ') end; return ok')
    end
    local entries, next_index = DCS.getLogHistory(index)
    assert(type(entries) == 'table' and type(next_index) == 'number', 'history_unavailable')
    assert(next_index >= index, 'history_reset')
    index = next_index
    for _, entry in ipairs(entries) do
        local message = entry.message or entry[4]
        if type(message) == 'string' then
            local arm_package, arm_token = message:match('^DCSR_SESSION_ARMED,([%w_-]+),([%w_-]+)%s*$')
            if arm_package == expected.package and arm_token == session and not armed then
                armed = true
                emit('ARMED session=' .. session .. ' acknowledgment=mission_log')
            end
            local package, token, sequence = message:match('^DCSR_SESSION_REQUEST,([%w_-]+),([%w_-]+),(%d+)%s*$')
            if armed and package == expected.package and token == session then
                local ok, reason = observe()
                bridge('local accepted=DCSR_SESSION_CONTROL and DCSR_SESSION_CONTROL.answer(' ..
                    q(package) .. ',' .. q(token) .. ',' .. sequence .. ',' .. tostring(ok) .. '); env.info(' ..
                    q('DCSR_SESSION_ANSWER,' .. package .. ',' .. token .. ',' .. sequence .. ',') ..
                    '..tostring(accepted)); return accepted')
                emit('ANSWER_SENT session=' .. session .. ' sequence=' .. sequence .. ' allowed=' .. tostring(ok) ..
                    ' reason=' .. reason)
            end
            local answer_package, answer_token, answer_sequence, accepted = message:match(
                '^DCSR_SESSION_ANSWER,([%w_-]+),([%w_-]+),(%d+),(%w+)%s*$')
            if answer_package == expected.package and answer_token == session then
                emit('ANSWER_ACK session=' .. session .. ' sequence=' .. answer_sequence .. ' accepted=' .. accepted)
            end
        end
    end
end
local function reset()
    active, session, armed, bridge_reported, last_result = false, nil, false, false, nil
    next_arm = 0
end
function hooks.onMissionLoadBegin() reset() end
function hooks.onSimulationStart()
    reset()
    generation = generation + 1
    -- Filename selects this disposable fixture; it is never identity evidence.
    if not (DCS.getMissionFilename() or ''):find('Session%-Guard') then return end
    session = string.format('%d_%d_%d', os.time(), generation, math.floor(DCS.getRealTime()*1000))
    local _, tail = DCS.getLogHistory(0)
    index = assert(tail)
    active = true
    emit('START session=' .. session .. ' bridge=' .. type(net and net.dostring_in))
end
function hooks.onSimulationFrame()
    local ok, err = pcall(pump)
    if not ok then emit('ERROR ' .. tostring(err)); reset() end
end
function hooks.onSimulationStop() reset() end
DCS.setUserCallbacks(hooks)
emit('INSTALLED package=' .. expected.package .. ' bridge=' .. type(net and net.dostring_in))
