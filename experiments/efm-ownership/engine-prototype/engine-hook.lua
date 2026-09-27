-- THROWAWAY GUI hook, read-only. No Export.lua replacement or mission bridge.
local index,active,last_error=0,nil,nil
local function emit(s) log.write('DCS_ENGINE_DIAGNOSTIC',log.INFO,'DCSENGINE_EXPORT,1,'..s) end
local function number(v)
    assert(type(v)=='number' and v==v and math.abs(v)<math.huge,'unavailable_numeric_channel')
    return string.format('%.12g',v)
end
local function field(info,group,side)
    assert(type(info[group])=='table','unavailable_'..group)
    return number(info[group][side])
end
local function sample(take,seq)
    assert(type(Export)=='table','export_api_unavailable')
    local start=Export.LoGetModelTime()
    local self=Export.LoGetSelfData()
    assert(self and self.Name=='FA-18C_hornet' and self.UnitName=='Observer','ownship_identity_mismatch')
    local id=Export.LoGetPlayerPlaneId()
    local info=Export.LoGetEngineInfo()
    assert(type(info)=='table','engine_info_unavailable')
    local p=assert(self.Position,'position_unavailable')
    local row={number(start),number(id),self.Name,self.UnitName,number(p.x),number(p.y),number(p.z)}
    for _,group in ipairs({'RPM','Temperature','FuelConsumption'}) do
        for _,side in ipairs({'left','right'}) do row[#row+1]=field(info,group,side) end
    end
    row[#row+1]=number(Export.LoGetModelTime())
    emit('DATA,'..take..','..seq..','..table.concat(row,','))
end
local function consume(message)
    local event=message:match('^DCSENGINE_MISSION,1,(.*)')
    if not event then return end
    event=event:gsub('\r$','')
    local take,started,id=event:match('^BEGIN,(%d+),([^,]+),(%d+),FA%-18C_hornet,Observer$')
    if take then active={take=take,rows=0};emit('BEGIN,'..take..','..started..','..id);return end
    local seq
    take,seq=event:match('^DATA,(%d+),(%d+),')
    if take and active and take==active.take then
        if tonumber(seq)~=active.rows+1 then emit('ERROR,'..take..',sequence_gap');active=nil;return end
        active.rows=tonumber(seq)
        local ok,err=pcall(sample,take,seq)
        if not ok then emit('UNAVAILABLE,'..take..','..seq..','..tostring(err):gsub('[\r\n,]',' ')) end
        return
    end
    local reason,count
    take,reason,count=event:match('^END,(%d+),([%w_]+),(%d+)$')
    if take and active and take==active.take then emit('END,'..take..','..reason..','..count);active=nil end
end
local function pump()
    local entries,next_index=DCS.getLogHistory(index)
    assert(type(entries)=='table' and type(next_index)=='number','invalid_log_history')
    if next_index<index then emit('ERROR,0,history_reset');active=nil end
    index=next_index
    for _,entry in ipairs(entries) do
        local message=entry.message or entry[4]
        if type(message)=='string' then consume(message) end
    end
end
local function safe_pump()
    local ok,err=pcall(pump)
    if not ok then
        active=nil
        if tostring(err)~=last_error then emit('ERROR,0,'..tostring(err):gsub('[\r\n,]',' '));last_error=tostring(err) end
    else last_error=nil end
end
DCS.setUserCallbacks({onSimulationFrame=safe_pump,onSimulationStop=function()
    safe_pump()
    if active then emit('END,'..active.take..',simulation_stop,'..active.rows);active=nil end
end})
emit('READY,hook_loaded')
