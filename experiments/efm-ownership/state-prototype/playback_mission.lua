-- THROWAWAY: observe the separate SDK-only appearance actuator from mission context.
local channels={0,3,5,9,10,11,12,13,14,15,16,17,18,21}
local active=false
local started,finished,last_segment=nil,nil,nil
local function tell(s) trigger.action.outText('Exterior playback: '..s,15) end
local function remove(reason)
    active=false
    local u=Unit.getByName('StatePlayback')
    if u and u:isExist() then u:destroy() end
    env.info('DCSSTATE_PLAYBACK,END,'..reason)
    tell(reason..'. The mission can continue; restart the mission to repeat.')
end
local function tick()
    if not active then return nil end
    local now=timer.getTime()
    local u=Unit.getByName('StatePlayback')
    if not u or not u:isExist() then remove('aircraft missing');return nil end
    local status=u:getDrawArgumentValue(999)
    local elapsed=u:getDrawArgumentValue(998)*1000
    if status>0.6 then remove('writer failed; retain logs');return nil end
    if status<0.1 and now-started>10 then remove('no writer handshake; restart DCS to load the new module');return nil end
    if status>0.1 then
        local segment='baseline'
        for _,mark in ipairs(DCS_STATE_CONFIG.markers) do if elapsed>=mark.time then segment=mark.segment end end
        if segment~=last_segment then last_segment=segment;tell('watch '..segment..' ('..string.format('%.1f',elapsed)..' seconds)') end
        local values={}
        for _,index in ipairs(channels) do values[#values+1]=string.format('%.9g',u:getDrawArgumentValue(index)) end
        env.info(string.format('DCSSTATE_PLAYBACK,DATA,%.9f,%.9f,%s,%s',now,elapsed,segment,table.concat(values,',')))
    end
    if status>0.4 and not finished then finished=now;tell('sequence complete; holding final state for 8 seconds') end
    if finished and now-finished>=8 then remove('complete');return nil end
    if now-started>DCS_STATE_CONFIG.duration+30 then remove('timeout');return nil end
    return now+0.05
end
local menu=missionCommands.addSubMenu('Exterior state playback')
local used=false
missionCommands.addCommand('Start captured surface sequence',menu,function()
    if used then tell('restart this mission to repeat');return end
    local group=Group.getByName('StatePlaybackGroup')
    if not group then tell('test aircraft group unavailable');return end
    used=true;active=true;started=timer.getTime()
    trigger.action.activateGroup(group)
    trigger.action.setUserFlag('DCS_STATE_RELEASE',1)
    env.info('DCSSTATE_PLAYBACK,BEGIN,'..started)
    tell('started. Press F2 to select the lead and watch its surfaces. This test uses a normal AI flight route.')
    timer.scheduleFunction(tick,nil,started+0.1)
end)
missionCommands.addCommand('Stop and remove test aircraft',menu,function() if active then remove('user_stop') end end)
tell('ready. F10 > Exterior state playback > Start captured surface sequence. Use F2 to inspect the lead.')
