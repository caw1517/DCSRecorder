-- Read-only native sampling for version-three recordings. Loaded by the save hook.
local reader
local function split(s)local out={};for v in (s..','):gmatch('(.-),')do out[#out+1]=v end;return out end
local function finite(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
return function(data,active)
    local row=split(data);assert(#row==36,'Invalid engine mission row')
    local t=Export.LoGetModelTime()
    local motion_time=tonumber(row[1])
    assert(finite(t) and motion_time and t>=motion_time and t-motion_time<=.05,'Engine sample delayed over 50 ms')
    assert(not active.engine_time or t>=active.engine_time,'Reversed engine sample time')
    local own=Export.LoGetSelfData()
    assert(own and own.Name=='FA-18C_hornet','Native engine capture requires stock Hornet')
    local id=Export.LoGetPlayerPlaneId()
    assert(id==active.source_id,'Engine/motion aircraft mismatch')
    if not reader then
        local err;reader,err=package.loadlib(lfs.writedir()..'Scripts/DCSRecorderEngineCapture/NativeEngineCapture.dll','dcs_native_engine_sample')
        assert(reader,err or 'Native engine capture helper unavailable')
    end
    local native=split(reader())
    assert(#native==15 and native[1]=='OK' and native[2]=='.?AVwHumanAircraft@@' and native[3]=='8','Native player identity/getters unavailable')
    local identity=table.concat({native[2],native[3],native[4],native[13],native[14],native[15]},',')
    assert(not active.engine_identity or active.engine_identity==identity,'Native engine identity changed')
    local values={}
    for i=5,12 do
        local v=tonumber(native[i]);local c=(i-5)%4
        assert(finite(v) and v>=0 and v<=(c<2 and 1.2 or 4),'Invalid native engine value')
        values[#values+1]=v
    end
    assert(values[3]==values[4] and values[7]==values[8],'Native power getters disagree')
    local info=Export.LoGetEngineInfo()
    assert(info and info.RPM and math.abs(values[1]-info.RPM.left/100)<.001 and
        math.abs(values[5]-info.RPM.right/100)<.001,'Native/Export engine mismatch')
    local finish=Export.LoGetModelTime()
    assert(finite(finish) and finish>=t and finish-t<=.02 and Export.LoGetPlayerPlaneId()==id,'Player/clock changed during engine read')
    -- Check the independently observed position against the recorded velocity.
    local p=own.Position;local dt=t-motion_time;local error2=0
    for i,key in ipairs({'x','y','z'})do
        local expected=assert(tonumber(row[1+i]))+dt*assert(tonumber(row[13+i]))
        assert(p and finite(p[key]),'Invalid Export position')
        error2=error2+(p[key]-expected)^2
    end
    assert(error2<=.25,'Engine/motion position association failed')
    active.engine_time=t;active.engine_identity=identity
    local appended={string.format('%.12g',t)}
    for _,v in ipairs(values)do appended[#appended+1]=string.format('%.12g',v)end
    return data..','..table.concat(appended,',')
end
