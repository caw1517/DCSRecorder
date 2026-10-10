-- Read measured emitter state after the existing engine/identity association.
local reader,reader_build
local function finite(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
return function(data,active)
    local motion_time=tonumber(data:match('^([^,]+),'))
    local t=Export.LoGetModelTime()
    local limit=active.smoke_time and active.hitch_limit or .15
    local max_delay=active.capture_timing=='frame-batch-v1' and active.smoke_time and limit or .05
    assert(finite(t) and motion_time and t>=motion_time and t-motion_time<=max_delay,
        'Smoke sample delayed over '..math.floor(max_delay*1000+.5)..' ms')
    assert(not active.smoke_time or t>=active.smoke_time,'Reversed smoke sample time')
    assert(not active.smoke_time or t-active.smoke_time<=limit,'Smoke sample clock gap over '..math.floor(limit*1000+.5)..' ms')
    local id=Export.LoGetPlayerPlaneId()
    assert(id==active.engine_player_id,'Smoke/engine player mismatch')
    if not reader or reader_build~=active.capture_build then
        local binary=active.capture_build=='2.9.30.28536' and 'NativeSmokeCapture2930.dll' or 'NativeSmokeCapture.dll'
        local err;reader,err=package.loadlib(lfs.writedir()..'Scripts/DCSRecorderSmokeCapture/'..binary,'dcs_native_smoke_sample')
        assert(reader,err or 'Native smoke capture helper unavailable')
        reader_build=active.capture_build
    end
    local result=reader()
    local on,aggregate,classification
    if type(result)=='string' then on,aggregate,classification=result:match('^OK,10,([01]),([01]),(%d+)$')end
    assert(on and aggregate==on and classification=='0','Native white-smoke state unavailable or inconsistent')
    local finish=Export.LoGetModelTime()
    assert(finite(finish) and finish>=t and finish-t<=.02 and Export.LoGetPlayerPlaneId()==id,'Player/clock changed during smoke read')
    assert(active.smoke_time~=t or active.smoke_on==on,'Smoke changed at one timestamp')
    active.smoke_time=t;active.smoke_on=on
    active.max_smoke_delay=math.max(active.max_smoke_delay or 0,t-motion_time)
    return data..','..string.format('%.12g',t)..','..on
end
