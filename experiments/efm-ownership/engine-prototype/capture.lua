-- THROWAWAY, read-only stock-Hornet engine observation. No production recording.
if DCS_ENGINE_PROTOTYPE then return end
DCS_ENGINE_PROTOTYPE={active=false,take=0,rows=0,segment='baseline'}
local r=DCS_ENGINE_PROTOTYPE
-- Only 89 is labelled nozzle by the installed descriptor; others are candidates.
local channels={28,29,38,39,40,41,89,90,395,396,397,398,420}
local function emit(s) env.info('DCSENGINE_MISSION,1,'..s) end
local function tell(s) trigger.action.outText('Engine diagnostic: '..s,15) end
local function number(v)
    assert(type(v)=='number' and v==v and math.abs(v)<math.huge,'unavailable_numeric_channel')
    return string.format('%.12g',v)
end
local function stop(reason)
    if not r.active then return end
    r.active=false;emit('END,'..r.take..','..reason..','..r.rows)
    tell('stopped ('..reason..'), '..r.rows..' samples. Preserve this DCS session for collection.')
end
local function tick()
    if not r.active then return end
    local u=Unit.getByName('Observer')
    if not u or not u:isExist() or not u:getPlayerName() or u:getID()~=r.unit then stop('aircraft_changed');return end
    local now=timer.getTime()
    if now-r.started>=240 then stop('time_limit');return end
    local ok,values=pcall(function()
        local p=u:getPosition().p
        local row={number(now),r.segment,number(p.x),number(p.y),number(p.z)}
        for _,index in ipairs(channels) do row[#row+1]=number(u:getDrawArgumentValue(index)) end
        return row
    end)
    if not ok then stop('unavailable_channel');return end
    r.rows=r.rows+1;emit('DATA,'..r.take..','..r.rows..','..table.concat(values,','))
    return now+0.05
end
local menu=missionCommands.addSubMenu('Engine state diagnostic')
missionCommands.addCommand('Start capture (4 minute maximum)',menu,function()
    if r.active then return end
    local u=Unit.getByName('Observer')
    if not u or not u:isExist() or not u:getPlayerName() or u:getTypeName()~='FA-18C_hornet' then tell('enter the stock Hornet cockpit first');return end
    r.take=r.take+1;r.rows=0;r.segment='baseline';r.started=timer.getTime();r.unit=u:getID();r.active=true
    emit('BEGIN,'..r.take..','..number(r.started)..','..r.unit..',FA-18C_hornet,Observer')
    emit('CHANNELS,'..r.take..','..table.concat(channels,','));tick()
    local take=r.take
    timer.scheduleFunction(function() if take==r.take then return tick() end end,nil,r.started+0.05)
    tell('capturing. Mark each phase, then move throttles yourself. Markers never move controls.')
end)
local markers=missionCommands.addSubMenu('Mark next throttle change',menu)
for _,label in ipairs({'baseline','both_idle','both_military','left_afterburner','right_afterburner','both_afterburner','both_dry'}) do
    local segment=label
    missionCommands.addCommand(segment,markers,function()
        if not r.active then tell('start capture first');return end
        r.segment=segment;emit('MARK,'..r.take..','..number(timer.getTime())..','..segment)
        tell('phase '..segment..'. Move throttles, hold briefly, and observe nozzle/flame/sound separately.')
    end)
end
missionCommands.addCommand('Stop capture',menu,function() stop('user_stop') end)
tell('ready. F10 > Engine state diagnostic. This captures observations, not a flight-library take.')
