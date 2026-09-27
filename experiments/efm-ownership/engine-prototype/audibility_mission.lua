-- THROWAWAY: source/attenuation comparison, with the same 15-second lifecycle.
local used,active=false,false
local function tell(s)trigger.action.outText('Sound audibility test: '..s,4)end
local function remove(reason)
    active=false
    local unit=Unit.getByName('StatePlayback')
    if unit and unit:isExist()then unit:destroy()end
    env.info('DCS_AUDIBILITY_MISSION,END,'..reason..','..timer.getTime())
    tell('finished. Report whether you heard the beeps, stock afterburner, and defined afterburner.')
end
local menu=missionCommands.addSubMenu('Sound audibility test')
missionCommands.addCommand('Start sound test',menu,function()
    if used then tell('restart the mission to repeat');return end
    local group=Group.getByName('StatePlaybackGroup')
    if not group then tell('test lead unavailable');return end
    used=true;active=true
    trigger.action.activateGroup(group)
    trigger.action.setUserFlag('DCS_STATE_RELEASE',1)
    env.info('DCS_AUDIBILITY_MISSION,BEGIN,'..timer.getTime())
    tell('F2 to the lead. Stock engine now; control beeps begin in 3 seconds.')
    for index,label in ipairs({'CONTROL BEEPS','STOCK AFTERBURNER','DEFINED AFTERBURNER','TEST SOURCES SILENT'})do
        timer.scheduleFunction(function(text)if active then tell(text)end end,label,timer.getTime()+3*index)
    end
    timer.scheduleFunction(function()if active then remove('complete')end end,nil,timer.getTime()+15)
end)
missionCommands.addCommand('Stop sound test',menu,function()if active then remove('user_stop')end end)
trigger.action.outText('Sound audibility test: F10 > Sound audibility test > Start sound test. Watch the phase labels and listen separately from the nozzle animations.',20)
