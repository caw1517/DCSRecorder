-- Read measured emitter state after the existing engine/identity association.
local reader
local function finite(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
return function(data,active)
    local motion_time=tonumber(data:match('^([^,]+),'))
    local t=Export.LoGetModelTime()
    assert(finite(t) and motion_time and t>=motion_time and t-motion_time<=.05,'Smoke sample delayed over 50 ms')
    assert(not active.smoke_time or t>=active.smoke_time,'Reversed smoke sample time')
    local id=Export.LoGetPlayerPlaneId()
    assert(id==active.engine_player_id,'Smoke/engine player mismatch')
    if not reader then
        local err;reader,err=package.loadlib(lfs.writedir()..'Scripts/DCSRecorderSmokeCapture/NativeSmokeCapture.dll','dcs_native_smoke_sample')
        assert(reader,err or 'Native smoke capture helper unavailable')
    end
    local result=reader()
    local on,aggregate,classification
    if type(result)=='string' then on,aggregate,classification=result:match('^OK,10,([01]),([01]),(%d+)$')end
    assert(on and aggregate==on and classification=='0','Native white-smoke state unavailable or inconsistent')
    local finish=Export.LoGetModelTime()
    assert(finite(finish) and finish>=t and finish-t<=.02 and Export.LoGetPlayerPlaneId()==id,'Player/clock changed during smoke read')
    assert(active.smoke_time~=t or active.smoke_on==on,'Smoke changed at one timestamp')
    active.smoke_time=t;active.smoke_on=on
    return data..','..string.format('%.12g',t)..','..on
end
