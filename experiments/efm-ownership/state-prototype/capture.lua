-- THROWAWAY: observe stock Hornet exterior arguments; never commands aircraft state.
-- A separate log namespace deliberately bypasses the production flight-library sink.
if DCS_STATE_PROTOTYPE then return end
DCS_STATE_PROTOTYPE={active=false,take=0,rows=0,segment='baseline'}
local r=DCS_STATE_PROTOTYPE
local channels={}
for i=0,30 do channels[#channels+1]=i end
local function emit(message) env.info('DCSSTATE_LOG,1,'..message) end
local function tell(message) trigger.action.outText('State diagnostic: '..message,15) end
local function stop(reason)
    if not r.active then return end
    r.active=false
    emit('END,'..r.take..','..reason..','..r.rows)
    tell('stopped ('..reason..'), '..r.rows..' samples in DCS.log. Preserve the log before another DCS session.')
end
local function tick()
    if not r.active then return nil end
    local u=Unit.getByName('Observer')
    if not u or not u:isExist() or not u:getPlayerName() then stop('aircraft_lost');return nil end
    local now=timer.getTime()
    if now-r.started>=240 then stop('time_limit');return nil end
    local values={}
    for _,index in ipairs(channels) do
        local ok,value=pcall(function() return u:getDrawArgumentValue(index) end)
        if not ok or type(value)~='number' or value~=value or value==math.huge or value==-math.huge then
            stop('invalid_argument_'..index);return nil
        end
        values[#values+1]=string.format('%.9g',value)
    end
    r.rows=r.rows+1
    emit('DATA,'..r.take..','..r.rows..','..string.format('%.9f',now)..','..r.segment..','..table.concat(values,','))
    return now+0.05
end
local menu=missionCommands.addSubMenu('Exterior state diagnostic')
missionCommands.addCommand('Start capture (4 minute maximum)',menu,function()
    if r.active then return end
    local u=Unit.getByName('Observer')
    if not u or not u:isExist() or not u:getPlayerName() or u:getTypeName()~='FA-18C_hornet' then
        tell('enter the stock Hornet cockpit first');return
    end
    r.take=r.take+1;r.rows=0;r.segment='baseline';r.started=timer.getTime();r.active=true
    emit('BEGIN,'..r.take..','..u:getTypeName())
    emit('CHANNELS,'..r.take..','..table.concat(channels,','))
    local take=r.take
    timer.scheduleFunction(function() if take==r.take then return tick() end end,nil,r.started+0.05)
    tell('capturing. Select a segment marker before each control change. Markers do not move any controls.')
end)
local markers=missionCommands.addSubMenu('Mark next control change',menu)
for _,label in ipairs({'baseline','gear','flaps','pitch','roll','rudder','speedbrake'}) do
    local segment=label
    missionCommands.addCommand(segment,markers,function()
        if not r.active then tell('start capture first');return end
        r.segment=segment
        emit('MARK,'..r.take..','..string.format('%.9f',timer.getTime())..','..segment)
        tell('segment '..segment)
    end)
end
missionCommands.addCommand('Stop capture',menu,function() stop('user_stop') end)
tell('ready. This mission only observes exterior arguments; use F10 > Exterior state diagnostic.')
