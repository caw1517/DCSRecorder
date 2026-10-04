-- Session-bound authorization primitives. Callers must compare loaded data;
-- an archive path/hash is deliberately not an input to this module.
local M = {}

local function difference(expected, actual, path)
    if type(expected) ~= type(actual) then return path .. ':type' end
    if type(expected) ~= 'table' then
        if expected ~= actual then return path .. ':value' end
        return nil
    end
    for key, value in pairs(expected) do
        local mismatch = difference(value, actual[key], path .. '[' .. tostring(key) .. ']')
        if mismatch then return mismatch end
    end
    for key in pairs(actual) do
        if expected[key] == nil then return path .. '[' .. tostring(key) .. ']:unexpected' end
    end
end
M.difference = difference

-- A closed-by-default, single-use mission gate. A missing hook cannot release it.
-- The hook must arm a fresh session before accepting any requests.
function M.gate(package_id, clock, release, emit)
    local state = {phase='unverified', sequence=0, session=nil, pending=nil}
    local gate = {}
    function gate.arm(package, session)
        if package ~= package_id or type(session) ~= 'string' or session == '' then return false end
        if state.session == session then return true end -- repeated bridge poll
        if state.phase == 'released' then return false end
        state.session, state.pending, state.phase = session, nil, 'ready'
        return true
    end
    function gate.request()
        if state.phase ~= 'ready' then return false, state.phase end
        local now = clock()
        if type(now) ~= 'number' or now ~= now or math.abs(now) == math.huge then
            state.phase = 'refused'
            return false, state.phase
        end
        state.sequence = state.sequence + 1
        state.pending = {sequence=state.sequence, time=now}
        state.phase = 'pending'
        emit(package_id, state.session, state.sequence)
        return true
    end
    function gate.answer(package, session, sequence, allowed)
        if package ~= package_id or session ~= state.session or state.phase ~= 'pending' or
            sequence ~= state.pending.sequence then return false end
        local age = clock() - state.pending.time
        state.pending = nil
        if allowed ~= true or age ~= age or age < 0 or age > 1 then
            state.phase = 'refused'
            return false
        end
        state.phase = 'released' -- consume before invoking release, even if it throws
        release()
        return true
    end
    function gate.expire()
        if state.pending and (clock() < state.pending.time or clock() - state.pending.time > 1) then
            state.pending, state.phase = nil, 'refused'
        end
    end
    function gate.status() return state.phase end
    return gate
end

return M
