-- Staged recorded playback. This script does not own or stop any recorder.
local c=assert(DCS_STAGED_CONFIG)
local s={phase='waiting'}
DCS_STAGED_PLAYBACK=s
local function event(text) env.info(string.format('DCS_PLAYBACK_EVENT,%.6f,%s',timer.getTime(),text)) end
local function notice(text,seconds) trigger.action.outText('DCS Recorder: '..text,seconds or 12) end
local function dispose(phase,text)
    local unit=Unit.getByName('StagedPlayback')
    if unit and unit:isExist() then unit:destroy() end
    s.phase=phase;event(phase:upper());notice(text,20)
end
local function sample(name)
    local u=Unit.getByName(name)
    if not u or not u:isExist() then return end
    local p,v=u:getPosition(),u:getVelocity()
    env.info(string.format('DCS_PLAYBACK_SAMPLE,%s,%s,%.6f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.6f',
        s.phase,name,timer.getTime(),p.p.x,p.p.y,p.p.z,p.x.x,p.x.y,p.x.z,p.y.x,p.y.y,p.y.z,v.x,v.y,v.z,u:getDrawArgumentValue(21)))
end
local function tick()
    if s.phase=='starting' or s.phase=='playing' then
        local unit=Unit.getByName('StagedPlayback')
        if not unit or not unit:isExist() then
            dispose('failed','Playback aircraft unavailable. Mission continues; restart the mission to retry.')
        else
            local status=unit:getDrawArgumentValue(999)
            local matched=math.abs(unit:getDrawArgumentValue(997)-c.token_high)<1e-8 and
                math.abs(unit:getDrawArgumentValue(998)-c.token_low)<1e-8
            if status~=0 and not matched then
                dispose('failed','Playback package mismatch. Mission continues; select the matching recording package before retrying.')
            elseif matched and math.abs(status-0.75)<1e-6 then
                dispose('failed','Playback controller rejected its state. Mission continues; retain the logs for diagnosis.')
            elseif matched and math.abs(status-0.25)<1e-6 then
                if s.phase=='starting' then s.phase='playing';event('NATIVE_STARTED');notice('Playback running.',5) end
            elseif matched and math.abs(status-0.5)<1e-6 then
                if s.phase=='playing' then
                    sample('StagedPlayback')
                    dispose('complete','Playback complete. Your mission continues. Restart the mission to replay.')
                else dispose('failed','Unexpected playback completion before start. Mission continues.') end
            end
            if s.phase=='starting' and timer.getTime()-s.release_time>1 then
                dispose('failed','Playback controller did not confirm start. Mission continues; retain the logs.')
            elseif s.phase=='playing' and timer.getTime()-s.release_time>c.duration+2 then
                dispose('failed','Playback completion was not confirmed. Mission continues; retain the logs.')
            end
        end
    end
    sample('Observer');sample('StagedPlayback')
    return timer.getTime()+0.02
end
function s.released()
    s.phase='starting';s.release_time=timer.getTime();event('RELEASE')
    notice('Starting recorded playback; awaiting controller confirmation.',5)
end
local menu=missionCommands.addSubMenu('DCS Recorder')
missionCommands.addCommand('Start playback (3-second countdown)',menu,function()
    if s.phase~='waiting' then notice('Start already requested. Restart the mission to replay.');return end
    s.phase='countdown';event('F10_START');local remaining=3
    notice('Starting in 3. Do not toggle Active Pause manually.',4)
    timer.scheduleFunction(function()
        remaining=remaining-1
        if remaining>0 then notice('Starting in '..remaining..'.',2);return timer.getTime()+1 end
        s.phase='release_requested';event('RELEASE_REQUESTED')
        trigger.action.setUserFlag('DCS_RECORDED_RELEASE',1)
    end,nil,timer.getTime()+1)
end)
missionCommands.addCommand('Show playback status',menu,function() notice('Playback state: '..s.phase..'.',10) end)
event('INITIALIZED');sample('Observer')
timer.scheduleFunction(tick,nil,timer.getTime()+0.02)
notice('Staged airborne playback. Wait until ready, then communications menu F10 > DCS Recorder > Start playback. Do not toggle Active Pause manually. This integration test replays the complete recorded flight.',45)
