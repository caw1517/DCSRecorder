-- THROWAWAY: DCS's original sound renderer, recorded core/fan RPM and power substituted.
local used,active=false,false
local start,phase,segment
local function tell(s)trigger.action.outText('Combined engine test: '..s,8)end
local function remove(reason)
    active=false
    local unit=Unit.getByName('StatePlayback')
    if unit and unit:isExist()then unit:destroy()end
    env.info('DCS_COMBINED_MISSION,END,'..reason..','..timer.getTime())
    tell(reason..'. Report whether sound, nozzles and flames matched through the recorded sequence.')
end
local function tick()
    if not active then return end
    local unit=Unit.getByName('StatePlayback')
    if not unit or not unit:isExist()then remove('aircraft_missing');return end
    local status=unit:getDrawArgumentValue(999)
    local elapsed=unit:getDrawArgumentValue(998)*1000
    if status>0.6 then remove('native_guard_failed');return end
    if status<0.1 and timer.getTime()-start>5 then remove('no_handshake');return end
    if status>=0.1 then
        local current=elapsed<3 and 'original engine parameters baseline' or (status<0.4 and 'recorded sound, nozzles and flames' or 'original getter restored')
        if current~=phase then phase=current;tell(current)end
        if elapsed>=3 and status<0.4 then
            local current_segment='baseline'
            for _,mark in ipairs(DCS_STATE_CONFIG.markers)do if elapsed-3>=mark.time then current_segment=mark.segment end end
            if segment~=current_segment then segment=current_segment;tell('recorded engine: '..segment..'. Phase labels mark the original throttle inputs.')end
        end
        if elapsed>=DCS_STATE_CONFIG.duration+6 then remove('complete');return end
    end
    if timer.getTime()-start>DCS_STATE_CONFIG.duration+12 then remove('timeout');return end
    return timer.getTime()+0.05
end
local menu=missionCommands.addSubMenu('Combined engine playback')
missionCommands.addCommand('Start combined engine test',menu,function()
    if used then tell('restart the mission to repeat');return end
    local group=Group.getByName('StatePlaybackGroup')
    if not group then tell('test lead unavailable');return end
    used=true;active=true;start=timer.getTime()
    trigger.action.activateGroup(group);trigger.action.setUserFlag('DCS_STATE_RELEASE',1)
    env.info('DCS_COMBINED_MISSION,BEGIN,'..start)
    tell('F2 to the lead. Original engine parameters for 3 seconds, recorded engine sequence, then original engine parameters for 3 seconds.')
    timer.scheduleFunction(tick,nil,start+0.05)
end)
missionCommands.addCommand('Stop combined engine test',menu,function()if active then remove('user_stop')end end)
tell('F10 > Combined engine playback > Start combined engine test. Watch both flames/nozzles and listen. Same recorded clock; stock DCS sound.')
