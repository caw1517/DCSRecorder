-- Read-only companion to the white-smoke diagnostic. Never commands smoke.
local index,active,reader=0,nil,nil
local function emit(s)log.write('DCS_NATIVE_SMOKE',log.INFO,'DCSSMOKE_NATIVE,1,'..s)end
local function number(v)
    assert(type(v)=='number' and v==v and math.abs(v)<math.huge,'invalid_number')
    return string.format('%.12g',v)
end
local function sample(take,seq,mission_time)
    local t=Export.LoGetModelTime()
    assert(t>=mission_time and t-mission_time<=.25,'mission_sample_delayed')
    local own=Export.LoGetSelfData()
    assert(own and own.Name=='FA-18C_hornet','stock_hornet_unavailable')
    -- Export and mission unit IDs occupy different namespaces; retain both.
    local id=Export.LoGetPlayerPlaneId()
    number(id)
    if active.id then assert(id==active.id,'player_changed')else active.id=id end
    if not reader then
        local path=lfs.writedir()..'Scripts/DCSRecorderSmokeCapture/NativeSmokeCapture.dll'
        local err;reader,err=package.loadlib(path,'dcs_native_smoke_sample')
        assert(reader,err or 'native_helper_unavailable')
    end
    local native=reader()
    assert(type(native)=='string','native_result_unavailable')
    assert(native:match('^OK,10,[01],[01],%d+$'),native)
    local finish=Export.LoGetModelTime()
    assert(finish>=t and finish-t<=.1,'sample_clock_changed')
    assert(Export.LoGetPlayerPlaneId()==id,'player_changed')
    emit('DATA,'..table.concat({take,seq,number(mission_time),number(t),number(finish),number(id),native},','))
end
local function consume(message)
    local event=message:match('^DCSSMOKE,1,(.*)')
    if not event then return end
    event=event:gsub('\r$','')
    local take,started,id=event:match('^BEGIN,(%d+),([^,]+),(%d+),{INV%-SMOKE%-WHITE},0,999$')
    if take then
        assert(not active,'capture_overlap')
        started=tonumber(started);number(started)
        active={take=take,rows=0,started=started,previous=started}
        emit('BEGIN,'..take..','..number(started)..','..id..',10,{INV-SMOKE-WHITE}')
        return
    end
    local seq,clock
    take,seq,clock=event:match('^FRAME,(%d+),(%d+),([^,]+),%d+$')
    if take and active and take==active.take then
        assert(tonumber(seq)==active.rows+1,'sequence_gap')
        clock=tonumber(clock);number(clock)
        assert(clock>active.previous and clock-active.started<=121,'capture_clock_invalid')
        active.rows=tonumber(seq);active.previous=clock
        sample(take,seq,clock)
        return
    end
    local reason,count
    take,reason,count=event:match('^END,(%d+),([%w_]+),(%d+)$')
    if take and active and take==active.take then
        assert(tonumber(count)==active.rows,'end_count_mismatch')
        emit('END,'..take..','..reason..','..count);active=nil
    end
end
local function pump()
    local entries,next_index=DCS.getLogHistory(index)
    assert(type(entries)=='table' and type(next_index)=='number','invalid_history')
    assert(next_index>=index,'history_reset')
    index=next_index
    for _,entry in ipairs(entries)do
        local message=entry.message or entry[4]
        if type(message)=='string'then consume(message)end
    end
end
local function safe_pump()
    local ok,err=pcall(pump)
    if not ok then
        emit('ERROR,'..(active and active.take or '0')..','..tostring(err):gsub('[\r\n]',' '))
        active=nil
    end
end
-- Ignore old log entries when loaded; only a new diagnostic BEGIN enables reads.
local _,initial=DCS.getLogHistory(0)
assert(type(initial)=='number','invalid_initial_history');index=initial
DCS.setUserCallbacks({onSimulationFrame=safe_pump,onSimulationStop=function()
    safe_pump()
    if active then emit('END,'..active.take..',simulation_stop,'..active.rows);active=nil end
end})
emit('READY,hook_loaded')
