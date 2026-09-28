-- Diagnostic only: observe stock Hornet arguments; markers never command smoke.
if DCS_SMOKE_PROBE then return end
local r={active=false,take=0,rows=0,previous={}}
DCS_SMOKE_PROBE=r
local function emit(s) env.info('DCSSMOKE,1,'..s) end
local function tell(s) trigger.action.outText('Smoke diagnostic: '..s,15) end
local function stop(reason)
    if not r.active then return end
    r.active=false;emit('END,'..r.take..','..reason..','..r.rows)
    tell('capture stopped. Keep this DCS session open for log collection.')
end
local function tick()
    if not r.active then return end
    local u=Unit.getByName('Observer')
    if not u or not u:isExist() or not u:getPlayerName() then stop('aircraft_lost');return end
    local now=timer.getTime()
    if now-r.started>=120 then stop('time_limit');return end
    local changed={}
    for i=0,999 do
        local ok,v=pcall(u.getDrawArgumentValue,u,i)
        if not ok or type(v)~='number' or v~=v or math.abs(v)==math.huge then
            stop('invalid_argument_'..i);return
        end
        if r.previous[i]==nil or math.abs(v-r.previous[i])>0.000001 then
            changed[#changed+1]=i..'='..string.format('%.9g',v);r.previous[i]=v
        end
    end
    r.rows=r.rows+1
    emit('FRAME,'..r.take..','..r.rows..','..string.format('%.9f',now)..','..#changed)
    for start=1,#changed,25 do
        local chunk={};for i=start,math.min(start+24,#changed) do chunk[#chunk+1]=changed[i] end
        emit('ARGS,'..r.take..','..r.rows..','..table.concat(chunk,','))
    end
    return now+.2
end
local menu=missionCommands.addSubMenu('Smoke diagnostic')
missionCommands.addCommand('Start capture',menu,function()
    if r.active then return end
    local u=Unit.getByName('Observer')
    if not u or not u:isExist() or not u:getPlayerName() or u:getTypeName()~='FA-18C_hornet' then
        tell('enter the stock Hornet cockpit first');return
    end
    local clsid
    for _,country in pairs(env.mission.coalition.blue.country) do
        for _,group in pairs((country.plane or {}).group or {}) do
            for _,unit in pairs(group.units) do
                if unit.name=='Observer' then clsid=((unit.payload.pylons or {})[10] or {}).CLSID end
            end
        end
    end
    if clsid~='{INV-SMOKE-WHITE}' then tell('expected white smoke generator on station 10');return end
    r.take=r.take+1;r.rows=0;r.previous={};r.started=timer.getTime();r.active=true
    emit('BEGIN,'..r.take..','..r.started..','..u:getID()..','..clsid..',0,999')
    local take=r.take
    timer.scheduleFunction(function() if r.take==take then return tick() end end,nil,r.started+.2)
    tell('capturing. Toggle Smoke Device ON/OFF with your aircraft control. Mark the state you see, then hold 5 seconds. Repeat twice.')
end)
for _,state in ipairs({'ON','OFF'}) do
    local label=state
    missionCommands.addCommand('Mark smoke visibly '..label,menu,function()
        if not r.active then tell('start capture first');return end
        emit('MARK,'..r.take..','..string.format('%.9f',timer.getTime())..','..label)
        tell('marked '..label..'; this marker does not switch smoke.')
    end)
end
missionCommands.addCommand('Stop capture',menu,function() stop('user_stop') end)
tell('white smoke fitted. Start via F10 > Smoke diagnostic. Use your Smoke Device - ON/OFF binding to switch it.')
