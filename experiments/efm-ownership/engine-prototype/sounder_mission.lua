-- THROWAWAY: a 15-second spatial audio routing test on one late-activated lead.
local used,active=false,false
local function tell(s) trigger.action.outText('Sound routing test: '..s,20) end
local function remove(reason)
    active=false
    local unit=Unit.getByName('StatePlayback')
    if unit and unit:isExist() then unit:destroy() end
    env.info('DCS_SOUNDER_MISSION,END,'..reason..','..timer.getTime())
    tell('finished. Report whether the sound switched twice between engine and afterburner, then stopped.')
end
local menu=missionCommands.addSubMenu('Sound routing test')
missionCommands.addCommand('Start sound test',menu,function()
    if used then tell('restart the mission to repeat');return end
    local group=Group.getByName('StatePlaybackGroup')
    if not group then tell('test lead unavailable');return end
    used=true;active=true
    trigger.action.activateGroup(group)
    trigger.action.setUserFlag('DCS_STATE_RELEASE',1)
    env.info('DCS_SOUNDER_MISSION,BEGIN,'..timer.getTime())
    tell('F2 to the lead. Expected: engine 3s, afterburner 3s, engine 3s, afterburner 3s, silence. Lead disappears at 15s.')
    timer.scheduleFunction(function() if active then remove('complete') end end,nil,timer.getTime()+15)
end)
missionCommands.addCommand('Stop sound test',menu,function() if active then remove('user_stop') end end)
tell('F10 > Sound routing test > Start sound test. This tests audio control, not synchronization with nozzle animations.')
