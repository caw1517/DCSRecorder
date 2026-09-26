-- Mission-owned sampling; completed takes are extracted from standard DCS logs.
if DCSRECORDER then return end
DCSRECORDER={state='idle',take=0,source='Observer'}
local r=DCSRECORDER
local function csv(s) return '"'..tostring(s):gsub('"','""')..'"' end
function r.metadata()
    local u=Unit.getByName(r.source)
    if not u or not u:isExist() then return nil end
    local livery
    for _,side in pairs(env.mission.coalition) do
        if type(side)=='table' then for _,country in pairs(side.country or {}) do
            for _,group in pairs((country.plane or {}).group or {}) do
                for _,unit in pairs(group.units) do if unit.name==r.source then livery=unit.livery_id end end
            end
        end end
    end
    if not livery then return nil end
    return 'DCSREC,1\naircraft,'..csv(u:getTypeName())..'\nlivery,'..csv(livery)..
        '\ntheatre,'..csv(env.mission.theatre)..'\nsource,'..csv(r.source)..'\n'
end
function r.sample()
    if r.state~='recording' then return 'IDLE' end
    local u=Unit.getByName(r.source)
    if not u or not u:isExist() or not u:getPlayerName() then r.state='stopped';return 'LOST' end
    local p=u:getPosition();local v=u:getVelocity()
    local values={timer.getTime(),p.p.x,p.p.y,p.p.z,p.x.x,p.x.y,p.x.z,
        p.y.x,p.y.y,p.y.z,p.z.x,p.z.y,p.z.z,v.x,v.y,v.z,u:getDrawArgumentValue(21)}
    for i,value in ipairs(values) do
        if value~=value or value==math.huge or value==-math.huge then return 'INVALID' end
        values[i]=string.format('%.12g',value)
    end
    return 'DATA,'..r.take..','..table.concat(values,',')
end
local function emit(message) env.info('DCSREC_LOG,1,'..message) end
local function stop(reason)
    if r.state~='recording' then return end
    emit('END,'..r.take..','..reason..','..r.rows)
    r.state='stopped'
    trigger.action.outText('Recording stopped: '..r.rows..' samples written to DCS.log. Ready for extraction. Keep this DCS session until the recording is collected.',20)
end
local function tick()
    if r.state~='recording' then return nil end
    local data=r.sample()
    if data=='LOST' then r.state='recording';stop('aircraft_lost');return nil end
    if data=='INVALID' then stop('invalid_sample');return nil end
    local number,values=data:match('^DATA,(%d+),(.+)$')
    if not number then stop('invalid_sample');return nil end
    local now=timer.getTime()
    if not r.last_time or now>r.last_time then
        r.rows=r.rows+1;r.last_time=now
        emit('DATA,'..number..','..r.rows..','..values..',,')
    end
    return now+0.02
end
local menu=missionCommands.addSubMenu('DCS Recorder')
missionCommands.addCommand('Start recording',menu,function()
    if r.state=='recording' then return end
    local metadata=r.metadata()
    if not metadata then trigger.action.outText('Recorder: player aircraft metadata unavailable. Enter the cockpit first.',15);return end
    r.take=r.take+1;r.state='recording';r.rows=0;r.last_time=nil
    emit('BEGIN,'..r.take..','..metadata:gsub('.',function(c)return string.format('%02x',string.byte(c)) end))
    local take=r.take
    timer.scheduleFunction(function()
        if r.take~=take then return nil end
        return tick()
    end,nil,timer.getTime()+0.02)
    trigger.action.outText('Recording take '..r.take..' into DCS.log. Use F10 > DCS Recorder > Stop recording before leaving the mission.',15)
end)
missionCommands.addCommand('Stop recording',menu,function()
    stop('user_stop')
end)
trigger.action.outText('Fly your own Hornet. F10 > DCS Recorder > Start recording. Start with 5 seconds straight and level, then fly a gentle turn or roll. Stop recording through the same menu.',25)
