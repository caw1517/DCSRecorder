-- Read-only taxi diagnostic. No controls, argument writes or flight-library output.
if DCS_WHEEL_PROBE then return end
local channels={0,5,3,1,6,4,101,103,102}
local r={active=false,used=false,rows=0}
DCS_WHEEL_PROBE=r
local function finite(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
local function emit(s)env.info('DCSWHEEL,1,'..s)end
local function tell(s)trigger.action.outText('Wheel diagnostic: '..s,15)end
local function stop(reason)
    if not r.active then return end
    r.active=false
    emit('END,'..reason..','..r.rows..','..string.format('%.9f',timer.getTime()))
    tell('capture finished ('..reason..'). Leave DCS open for log collection.')
end
local function tick()
    if not r.active then return end
    local now=timer.getTime()
    if now-r.started>=180 then stop('time_limit');return end
    local unit=Unit.getByName('Observer')
    if not unit or not unit:isExist() or not unit:getPlayerName() then stop('aircraft_lost');return end
    if unit:inAir() then stop('airborne');return end
    local p=unit:getPosition().p;local v=unit:getVelocity()
    local values={now,p.x,p.y,p.z,v.x,v.y,v.z}
    for _,c in ipairs(channels)do
        local ok,value=pcall(unit.getDrawArgumentValue,unit,c)
        if not ok or not finite(value)then stop('invalid_argument');return end
        values[#values+1]=value
    end
    for _,value in ipairs(values)do if not finite(value)then stop('invalid_sample');return end end
    if v.x*v.x+v.y*v.y+v.z*v.z>225 then stop('taxi_speed_limit');return end
    if not r.last or now>r.last then
        r.rows=r.rows+1;r.last=now
        for i,value in ipairs(values)do values[i]=string.format('%.12g',value)end
        emit('DATA,'..r.rows..','..table.concat(values,','))
    end
    return now+.02
end
local menu=missionCommands.addSubMenu('Wheel diagnostic')
missionCommands.addCommand('Start taxi capture',menu,function()
    if r.used then tell('restart the mission for another capture');return end
    if timer.getTime()<3 then tell('wait three seconds for startup');return end
    local unit=Unit.getByName('Observer')
    if not unit or not unit:isExist() or not unit:getPlayerName() or unit:getTypeName()~='FA-18C_hornet' then
        tell('enter the stock Hornet cockpit first');return
    end
    if unit:inAir()then tell('this diagnostic starts parked');return end
    r.active=true;r.used=true;r.started=timer.getTime()
    emit('BEGIN,'..string.format('%.9f',r.started)..','..unit:getID()..',FA-18C_hornet')
    emit('CHANNELS,'..table.concat(channels,','))
    timer.scheduleFunction(tick,nil,r.started+.02)
    tell('recording. Stay stopped 5 seconds, taxi slowly, brake to a stop, then repeat. F10 Stop taxi capture when done.')
end)
missionCommands.addCommand('Mark braking',menu,function()
    if r.active then emit('MARK,'..string.format('%.9f',timer.getTime())..',braking')end
end)
missionCommands.addCommand('Stop taxi capture',menu,function()stop('user_stop')end)
tell('ready. Stay parked and use F10 > Wheel diagnostic > Start taxi capture. No Active Pause. This mission measures only; you control the jet.')
