-- Throwaway capability probe: stock player + late-activated stock lead.
-- Native recorded-playback DLLs are not exercised by this mission.
local state = {phase='waiting', samples=0}
DCS_STAGING_PROTOTYPE = state
local function event(text)
    env.info('DCS_STAGE_EVENT,' .. string.format('%.6f', timer.getTime()) .. ',' .. text)
end
local function notice(text, seconds)
    trigger.action.outText('STAGING PROTOTYPE: ' .. text, seconds or 12)
end
local function snapshot(name)
    local unit = Unit.getByName(name)
    if not unit or not unit:isExist() then return end
    local pose, velocity = unit:getPosition(), unit:getVelocity()
    local p = pose.p
    env.info(string.format('DCS_STAGE_SAMPLE,%s,%s,%.6f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f',
        state.phase, name, timer.getTime(), p.x,p.y,p.z,velocity.x,velocity.y,velocity.z,pose.x.x,pose.x.y,pose.x.z))
    if name=='Observer' and not state.initial then state.initial={x=p.x,y=p.y,z=p.z} end
    return p
end
local function sample()
    snapshot('Observer'); snapshot('StageLead')
    state.samples=state.samples+1
    return timer.getTime()+0.02
end
function state.released()
    state.phase='flying'; state.released_at=timer.getTime()
    event('RELEASE'); snapshot('Observer'); snapshot('StageLead')
    notice('Released. Check that the lead appears about 150 feet ahead and your controls work normally. The lead will disappear after 10 seconds.',15)
    timer.scheduleFunction(function()
        local lead=Unit.getByName('StageLead')
        if lead and lead:isExist() then lead:destroy() end
        state.phase='complete'; event('LEAD_REMOVED')
        notice('Staging test complete. Your aircraft and mission continue. Fly a gentle turn, then exit normally.',25)
    end,nil,timer.getTime()+10)
end
local menu=missionCommands.addSubMenu('DCS Recorder staging test')
missionCommands.addCommand('Start staged flight (3-second countdown)',menu,function()
    if state.phase~='waiting' then notice('Start already requested. Restart the mission for another run.');return end
    state.phase='countdown'; state.requested_at=timer.getTime();event('F10_START')
    local remaining=3
    notice('Starting in 3. Do not toggle Active Pause manually.',4)
    timer.scheduleFunction(function()
        remaining=remaining-1
        if remaining>0 then
            notice('Starting in '..remaining..'.',2)
            return timer.getTime()+1
        end
        -- Use a native mission trigger for the command, as ED training missions do.
        state.phase='release_requested';event('RELEASE_REQUESTED')
        trigger.action.setUserFlag('DCS_STAGE_RELEASE',1)
    end,nil,timer.getTime()+1)
end)
missionCommands.addCommand('Show staging status',menu,function()
    event('F10_STATUS')
    local p=snapshot('Observer')
    local drift='unavailable'
    if p and state.initial then
        local q=state.initial
        drift=string.format('%.3f m',math.sqrt((p.x-q.x)^2+(p.y-q.y)^2+(p.z-q.z)^2))
    end
    notice('State: '..state.phase..'; mission time: '..string.format('%.3f',timer.getTime())..'; measured player drift: '..drift..'.',20)
end)
event('INITIALIZED')
snapshot('Observer')
timer.scheduleFunction(sample,nil,timer.getTime()+0.02)
notice('Active Pause requested. Wait 10 seconds, then use the communications menu: F10 > DCS Recorder staging test > Start staged flight. This is NOT recorded playback. If controls or countdown do not work, exit and report what happened.',45)