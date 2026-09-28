-- THROWAWAY: observe captured canopy position on a separate lead.
local channels={38}
local active,used=false,false
local started,finished,last_segment
local function tell(s) trigger.action.outText('Canopy playback: '..s,15) end
local function remove(reason)
    active=false
    local u=Unit.getByName('StatePlayback')
    if u and u:isExist() then u:destroy() end
    env.info('DCSCANOPY_PLAYBACK,END,'..reason)
    tell(reason..'. Mission continues; restart the mission to repeat.')
end
local function tick()
    if not active then return end
    local now=timer.getTime()
    local u=Unit.getByName('StatePlayback')
    if not u or not u:isExist() then remove('aircraft_missing');return end
    local status=u:getDrawArgumentValue(999)
    local elapsed=u:getDrawArgumentValue(998)*1000
    if status>0.6 then remove('writer_failed');return end
    if status<0.1 and now-started>10 then remove('no_writer_handshake');return end
    if status>0.1 then
        local segment='baseline'
        for _,mark in ipairs(DCS_STATE_CONFIG.markers) do if elapsed>=mark.time then segment=mark.segment end end
        if segment~=last_segment then last_segment=segment;tell('watch '..segment..' at '..string.format('%.1f',elapsed)..' s') end
        local values={}
        for _,index in ipairs(channels) do values[#values+1]=string.format('%.9g',u:getDrawArgumentValue(index)) end
        env.info(string.format('DCSCANOPY_PLAYBACK,DATA,%.9f,%.9f,%s,%s',now,elapsed,segment,table.concat(values,',')))
    end
    if status>0.4 and not finished then finished=now;tell('sequence complete; holding final state for 8 seconds') end
    if finished and now-finished>=8 then remove('complete');return end
    if now-started>DCS_STATE_CONFIG.duration+30 then remove('timeout');return end
    return now+0.02
end
local menu=missionCommands.addSubMenu('Canopy playback')
missionCommands.addCommand('Start captured canopy sequence',menu,function()
    if used then tell('restart this mission to repeat');return end
    local group=Group.getByName('StatePlaybackGroup')
    if not group then tell('test lead unavailable');return end
    used=true;active=true;started=timer.getTime()
    trigger.action.activateGroup(group);trigger.action.setUserFlag('DCS_STATE_RELEASE',1)
    env.info('DCSCANOPY_PLAYBACK,BEGIN,'..started)
    tell('started. F2 to watch the lead: compare canopy opening, partial holds, full opening and closure.')
    timer.scheduleFunction(tick,nil,started+0.1)
end)
missionCommands.addCommand('Stop and remove test aircraft',menu,function() if active then remove('user_stop') end end)
tell('ready. F10 > Canopy playback > Start captured canopy sequence. Do not manually toggle Active Pause.')
