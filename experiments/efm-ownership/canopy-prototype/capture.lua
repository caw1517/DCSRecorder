-- Separate parked-canopy observation experiment; no flight-library or playback writes.
if DCS_CANOPY_PROBE then return end
local phases=assert(DCS_CANOPY_PHASES)
local channels={38}
local r={active=false,used=false,rows=0,phase=0,requested=0}
DCS_CANOPY_PROBE=r
local function emit(text)env.info('DCSCANOPY,1,'..text)end
local function tell(text)trigger.action.outText('Canopy diagnostic: '..text,10)end
local function stop(reason)
    if not r.active then return end
    r.active=false;trigger.action.setUserFlag('DCS_CANOPY_CLEANUP',1)
    emit('END,'..reason..','..r.rows..','..string.format('%.9f',timer.getTime()))
    tell('finished ('..reason..'). Leave DCS open for log collection. Canopy switch returns to HOLD.')
end
local function request(i)
    r.requested=i;r.request_time=timer.getTime()
    emit('REQUEST,'..i..','..string.format('%.9f',r.request_time)..','..phases[i].name)
    trigger.action.setUserFlag('DCS_CANOPY_PHASE_'..i,1)
end
function r.applied(i)
    if not r.active then return end
    if i~=r.requested or i~=r.phase+1 then stop('phase_order');return end
    r.phase=i;r.phase_time=timer.getTime()
    emit('APPLIED,'..i..','..string.format('%.9f',r.phase_time)..','..phases[i].name)
    tell(phases[i].name..'. Observe externally; controls change automatically.')
end
local function tick()
    if not r.active then return end
    local now=timer.getTime()
    if now-r.started>120 then stop('time_limit');return end
    if r.requested~=r.phase and now-r.request_time>3 then stop('phase_not_applied');return end
    local unit=Unit.getByName('Observer')
    if not unit or not unit:isExist() or not unit:getPlayerName() then stop('aircraft_lost');return end
    local velocity=unit:getVelocity()
    if unit:inAir() or not velocity or velocity.x*velocity.x+velocity.y*velocity.y+velocity.z*velocity.z>1 then stop('aircraft_moving');return end
    local values={}
    for _,channel in ipairs(channels)do
        local ok,v=pcall(unit.getDrawArgumentValue,unit,channel)
        if not ok or type(v)~='number' or v~=v or math.abs(v)==math.huge then stop('invalid_argument');return end
        values[#values+1]=string.format('%.9g',v)
    end
    r.rows=r.rows+1
    emit('DATA,'..r.rows..','..string.format('%.9f',now)..','..r.phase..','..table.concat(values,','))
    if r.phase>0 and r.requested==r.phase and now-r.phase_time>=phases[r.phase].hold then
        if r.phase==#phases then stop('complete');return end
        request(r.phase+1)
    end
    return now+.02
end
local menu=missionCommands.addSubMenu('Canopy diagnostic')
missionCommands.addCommand('Start automatic canopy sequence',menu,function()
    if r.used then tell('restart the mission for another run');return end
    if timer.getTime()<3 then tell('wait three seconds for startup');return end
    local unit=Unit.getByName('Observer')
    if not unit or not unit:isExist() or not unit:getPlayerName() or unit:getTypeName()~='FA-18C_hornet' then
        tell('enter the stock Hornet cockpit first');return
    end
    r.used=true;r.active=true;r.started=timer.getTime()
    emit('BEGIN,'..string.format('%.9f',r.started)..','..unit:getID()..',FA-18C_hornet')
    emit('CHANNELS,'..table.concat(channels,','));request(1)
    timer.scheduleFunction(tick,nil,r.started+.02)
end)
missionCommands.addCommand('Stop and release canopy control',menu,function()stop('user_stop')end)
tell('Stay parked with the parking brake set, then F10 > Canopy diagnostic > Start automatic canopy sequence. Use F2 to watch.')
