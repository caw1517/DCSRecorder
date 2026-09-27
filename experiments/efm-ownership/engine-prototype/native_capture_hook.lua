-- THROWAWAY read-only companion to the existing engine diagnostic.
-- Native reads occur only during a matching stock-Hornet diagnostic capture.
local index,active,reader=0,nil,nil
local function emit(s)log.write('DCS_NATIVE_ENGINE',log.INFO,'DCSENGINE_NATIVE,1,'..s)end
local function number(v)
    assert(type(v)=='number' and v==v and math.abs(v)<math.huge,'invalid_number')
    return string.format('%.12g',v)
end
local function sample(take,seq)
    local t=Export.LoGetModelTime()
    local own=Export.LoGetSelfData()
    assert(own and own.Name=='FA-18C_hornet','stock_hornet_unavailable')
    local id=Export.LoGetPlayerPlaneId()
    if active.id then assert(id==active.id,'player_changed')else active.id=id end
    if not reader then
        local path=lfs.writedir()..'Scripts/DCSRecorderEngineCapture/NativeEngineCapture.dll'
        local err;reader,err=package.loadlib(path,'dcs_native_engine_sample')
        assert(reader,err or 'native_helper_unavailable')
    end
    local info=Export.LoGetEngineInfo()
    local native=reader()
    assert(type(native)=='string','native_result_unavailable')
    local finish=Export.LoGetModelTime()
    assert(finish>=t and finish-t<=0.1,'sample_clock_changed')
    assert(Export.LoGetPlayerPlaneId()==id,'player_changed')
    local p=assert(own.Position)
    local row={take,seq,number(t),number(finish),number(id),number(p.x),number(p.y),number(p.z),
        number(info.RPM.left),number(info.RPM.right),native}
    emit('DATA,'..table.concat(row,','))
    if native:sub(1,3)~='OK,' then error(native)end
end
local function consume(message)
    local event=message:match('^DCSENGINE_MISSION,1,(.*)')
    if not event then return end
    event=event:gsub('\r$','')
    local take,started,id=event:match('^BEGIN,(%d+),([^,]+),(%d+),FA%-18C_hornet,Observer$')
    if take then active={take=take,rows=0,started=tonumber(started)};emit('BEGIN,'..take..','..started..','..id);return end
    local seq
    take,seq=event:match('^DATA,(%d+),(%d+),')
    if take and active and take==active.take then
        if tonumber(seq)~=active.rows+1 then emit('ERROR,'..take..',sequence_gap');active=nil;return end
        if Export.LoGetModelTime()-active.started>241 then emit('ERROR,'..take..',time_limit');active=nil;return end
        active.rows=tonumber(seq)
        local ok,err=pcall(sample,take,seq)
        if not ok then emit('ERROR,'..take..','..seq..','..tostring(err):gsub('[\r\n]',' '));active=nil end
        return
    end
    local reason,count
    take,reason,count=event:match('^END,(%d+),([%w_]+),(%d+)$')
    if take and active and take==active.take then emit('END,'..take..','..reason..','..count);active=nil end
end
local function pump()
    local entries,next_index=DCS.getLogHistory(index)
    assert(type(entries)=='table' and type(next_index)=='number','invalid_history')
    if next_index<index then active=nil;emit('ERROR,0,history_reset')end
    index=next_index
    for _,entry in ipairs(entries)do
        local message=entry.message or entry[4]
        if type(message)=='string'then consume(message)end
    end
end
local function safe_pump()
    local ok,err=pcall(pump)
    if not ok then active=nil;emit('ERROR,0,'..tostring(err):gsub('[\r\n]',' '))end
end
DCS.setUserCallbacks({onSimulationFrame=safe_pump,onSimulationStop=function()
    safe_pump()
    if active then emit('END,'..active.take..',simulation_stop,'..active.rows);active=nil end
end})
emit('READY,hook_loaded')
