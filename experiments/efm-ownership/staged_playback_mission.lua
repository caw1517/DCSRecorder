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
    if c.exterior==1 and name=='StagedPlayback' then
        local values={}
        for _,channel in ipairs({0,3,5,9,10,11,12,13,14,15,16,17,18,21}) do
            values[#values+1]=string.format('%.9g',u:getDrawArgumentValue(channel))
        end
        env.info(string.format('DCS_PLAYBACK_EXTERIOR,%s,%.9f,%.9f,%s',s.phase,timer.getTime(),
            1000*u:getDrawArgumentValue(996),table.concat(values,',')))
    end
end
local smoke_index,smoke_on,smoke_elapsed=0,nil,0
if c.smoke_events then
    assert(#c.smoke_events>0 and c.smoke_events[1].time==0,'Missing initial smoke state')
    for i,e in ipairs(c.smoke_events)do
        assert(type(e.time)=='number' and e.time>=0 and e.time<=c.duration and type(e.on)=='boolean','Invalid smoke event')
        if i>1 then assert(e.time>c.smoke_events[i-1].time,'Smoke event clock reversal')end
    end
end
local function update_smoke(unit)
    if not c.smoke_events then return end
    local elapsed=1000*unit:getDrawArgumentValue(996)
    assert(type(elapsed)=='number' and elapsed==elapsed and elapsed>=smoke_elapsed and elapsed<=c.duration+.1,'Invalid smoke playback clock')
    smoke_elapsed=elapsed
    -- Advance to the last measured state due now. Do not replay stale bursts
    -- after a delayed frame, or issue duplicate commands while paused.
    while c.smoke_events[smoke_index+1] and c.smoke_events[smoke_index+1].time<=elapsed do
        smoke_index=smoke_index+1
    end
    local desired=c.smoke_events[smoke_index]
    if desired and desired.on~=smoke_on then
        unit:getController():setCommand({id='SMOKE_ON_OFF',params={value=desired.on}})
        smoke_on=desired.on
        env.info(string.format('DCS_PLAYBACK_SMOKE,%.9f,%.9f,%d,%.9f',timer.getTime(),elapsed,smoke_on and 1 or 0,desired.time))
    end
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
                local ok,err=pcall(update_smoke,unit)
                if not ok then
                    event('SMOKE_ERROR,'..tostring(err))
                    dispose('failed','Recorded smoke control failed. Mission continues; retain the logs.')
                end
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
