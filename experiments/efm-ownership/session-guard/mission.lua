-- Diagnostic release displays a message only. No playback or player hold.
local package_id = DCSR_SESSION_GUARD_PACKAGE
local gate = DCSR_SESSION_GUARD_MODULE.gate(package_id, timer.getTime, function()
    env.info('DCSR_SESSION_CONTROL RELEASED package=' .. package_id)
    trigger.action.outText('Session check passed. Diagnostic release only; no playback is running.', 30)
end, function(package, session, sequence)
    env.info('DCSR_SESSION_REQUEST,' .. package .. ',' .. session .. ',' .. sequence)
end)
DCSR_SESSION_CONTROL = gate
local menu = missionCommands.addSubMenu('DCS Recorder session check')
missionCommands.addCommand('Request guarded release', menu, function()
    local ok, reason = gate.request()
    if not ok then trigger.action.outText('Release blocked: ' .. reason .. '. Retain the log; restart to retry.', 20) end
end)
missionCommands.addCommand('Show session status', menu, function()
    trigger.action.outText('Session check: ' .. gate.status(), 15)
end)
local last
timer.scheduleFunction(function(_, now)
    gate.expire()
    if last ~= gate.status() then
        last = gate.status()
        env.info('DCSR_SESSION_CONTROL phase=' .. last .. ' package=' .. package_id)
        trigger.action.outText('Session check: ' .. last .. '. F10 > DCS Recorder session check > Request guarded release.', 20)
    end
    return now + 0.1
end, nil, timer.getTime() + 0.1)
env.info('DCSR_SESSION_CONTROL INITIALIZED package=' .. package_id)
