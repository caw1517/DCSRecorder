-- Durable sink for the mission recorder's versioned log protocol via DCS log history.
-- Runs in the GUI hook environment; never evaluates mission text or uses a bridge.
local root = lfs.writedir() .. 'DCSRecorder/'
assert(lfs.mkdir(root) or lfs.attributes(root, 'mode') == 'directory')
local directory = root .. 'recordings/'
assert(lfs.mkdir(directory) or lfs.attributes(directory, 'mode') == 'directory')
local columns = 't,x,y,z,fx,fy,fz,ux,uy,uz,rx,ry,rz,vx,vy,vz,speedbrake,rpm_left,rpm_right'
local exterior = ',arg_0,arg_3,arg_5,arg_9,arg_10,arg_11,arg_12,arg_13,arg_14,arg_15,arg_16,arg_17,arg_18'
local engine = ',arg_28,arg_29,arg_89,arg_90,engine_time,engine_core_left,engine_fan_left,engine_thrust_left,engine_power_left,engine_core_right,engine_fan_right,engine_thrust_right,engine_power_right'
local lights = ',arg_88,arg_190,arg_191,arg_192,arg_193,arg_210,arg_212'
local wheels = ',arg_1,arg_6,arg_4,arg_101,arg_103,arg_102,arg_2'
local capture_engine,capture_smoke
local history_index, active, serial = 0, nil, 0
local function announce(text) log.write('DCS_RECORDER_SAVE', log.INFO, text) end
-- DCS file methods may succeed with no return values, unlike stock Lua.
-- Exceptions and explicit nil/error pairs still fail; persisted bytes are checked.
local function checked(fn,...)
    local result,err=fn(...)
    if result==false or (result==nil and err~=nil) then error(tostring(err or 'File operation failed')) end
    return result
end
local function read_bytes(path)
    local file=assert(io.open(path,'rb'))
    local ok,data=pcall(function() return file:read('*a') end)
    checked(file.close,file)
    assert(ok and type(data)=='string','Cannot verify saved recording bytes')
    return data
end
local function write_status(text)
    pcall(function()
        local file=assert(io.open(root..'save-status.txt','wb'))
        checked(file.write,file,text);checked(file.flush,file);checked(file.close,file)
    end)
end
local function storage_check()
    local stem=root..'.autosave-check-'..os.date('!%Y%m%dT%H%M%SZ')
    local count=0
    while lfs.attributes(stem..'.tmp') or lfs.attributes(stem..'.done') do count=count+1;stem=stem..'-'..count end
    local expected='DCS Recorder storage check'
    local file=assert(io.open(stem..'.tmp','wb'))
    checked(file.write,file,expected);checked(file.flush,file);checked(file.close,file)
    assert(read_bytes(stem..'.tmp')==expected,'Storage write/read verification failed')
    checked(os.rename,stem..'.tmp',stem..'.done')
    assert(not lfs.attributes(stem..'.tmp') and read_bytes(stem..'.done')==expected,'Storage rename verification failed')
    checked(os.remove,stem..'.done')
end

local function abandon(reason)
    if active then pcall(function() active.file:flush(); active.file:close() end); active = nil; announce('Incomplete recording retained: ' .. reason) end
end
local function open_take(id, hex)
    abandon('new take')
    assert(#hex <= 8192 and #hex % 2 == 0 and not hex:find('[^%x]'), 'Invalid recorder metadata')
    local metadata = hex:gsub('..', function(pair) return string.char(tonumber(pair,16)) end)
    local version=metadata:match('^DCSREC,([1234567])\n')
    assert(version, 'Invalid recorder version')
    if version~='1' then assert(metadata:find('\nstate_profile,hornet-exterior-v1\n',1,true),'Invalid exterior state profile') end
    local source_id
    if tonumber(version)>=3 then
        assert(metadata:find('\nengine_profile,hornet-native-engine-v1\n',1,true),'Invalid engine profile')
        assert(metadata:find('\ncapture_build,2.9.29.27468\n',1,true),'Unsupported engine capture build')
        source_id=tonumber(metadata:match('\nsource_unit_id,(%d+)\n'));assert(source_id,'Missing source identity')
        if not capture_engine then capture_engine=assert(loadfile(lfs.writedir()..'Scripts/DCSRecorderEngineCapture/engine_capture.lua'))() end
    end
    local has_smoke=version=='4' or (tonumber(version)>=5 and metadata:find('\nsmoke_profile,',1,true)~=nil)
    if has_smoke then
        assert(metadata:find('\nsmoke_profile,hornet-native-smoke-v1\n',1,true) and
            metadata:find('\nsmoke_station,10\n',1,true) and
            metadata:find('\nsmoke_clsid,{INV-SMOKE-WHITE}\n',1,true),'Unsupported smoke metadata')
        if not capture_smoke then capture_smoke=assert(loadfile(lfs.writedir()..'Scripts/DCSRecorderSmokeCapture/smoke_capture.lua'))() end
    end
    local has_engine=tonumber(version)>=3
    if tonumber(version)>=5 then assert(metadata:find('\nlight_profile,hornet-lights-v1\n',1,true),'Invalid light profile')end
    if tonumber(version)>=6 then assert(metadata:find('\ncanopy_profile,hornet-canopy-v1\n',1,true),'Invalid canopy profile')end
    if version=='7' then assert(metadata:find('\nwheel_profile,hornet-wheels-v1\n',1,true),'Invalid wheel profile')end
    local header=columns..(version~='1' and exterior or '')..(has_engine and engine or '')..(has_smoke and ',smoke_time,smoke_on' or '')..(tonumber(version)>=5 and lights or '')..(tonumber(version)>=6 and ',arg_38' or '')..(version=='7' and wheels or '')..'\n'
    local filename
    repeat
        serial = serial + 1
        filename = directory .. os.date('!%Y%m%dT%H%M%SZ') .. '-' .. string.format('%04d',serial)
    until not lfs.attributes(filename .. '.partial') and not lfs.attributes(filename .. '.csv')
    local file = assert(io.open(filename .. '.partial', 'wb'))
    active = {id=id, rows=0, file=file, name=filename, parts={metadata,header}, version=version,source_id=source_id,
        has_engine=has_engine,has_smoke=has_smoke,commas=version=='7' and 50 or tonumber(version)>=6 and 43 or version=='5' and 42 or has_engine and 35 or (version=='2' and 31 or 18)}
    checked(file.write,file,metadata,header); checked(file.flush,file)
    write_status('RECORDING\nRecording in progress; use F10 Stop to save.')
end
local function consume(line)
    local event = line:match('DCSREC_LOG,1,(.*)')
    if not event then return end
    event = event:gsub('\r$','')
    local id,hex = event:match('^BEGIN,(%d+),(%x+)$')
    if id then open_take(id,hex); return end
    local count,data
    id,count,data = event:match('^DATA,(%d+),(%d+),(.+)$')
    if id and active and id == active.id then
        assert(tonumber(count) == active.rows + 1, 'Missing or duplicate sample')
        local _,commas = data:gsub(',','')
        assert(commas == active.commas and #data < 4096 and active.rows < 20000, 'Malformed or oversized recording')
        local light_data=''
        if tonumber(active.version)>=5 then
            local fields={};for value in (data..','):gmatch('(.-),')do fields[#fields+1]=value end
            local last=active.version=='7' and 51 or active.version=='6' and 44 or 43
            assert(#fields==last,'Invalid appearance mission row')
            for i=37,last do local v=tonumber(fields[i]);assert(v and v==v and v>=(i==51 and -1 or 0) and v<=1,'Invalid light/canopy/wheel value')end
            light_data=','..table.concat(fields,',',37,last);data=table.concat(fields,',',1,36)
        end
        if active.has_engine then data=capture_engine(data,active) end
        if active.has_smoke then data=capture_smoke(data,active) end
        data=data..light_data
        checked(active.file.write,active.file,data,'\n');active.parts[#active.parts+1]=data..'\n';active.rows = active.rows + 1
        if active.rows % 50 == 0 then checked(active.file.flush,active.file) end
        return
    end
    local reason
    id,reason,count = event:match('^END,(%d+),([%w_]+),(%d+)$')
    if id and active and id == active.id then
        assert(tonumber(count) == active.rows, 'Recording footer count mismatch')
        if reason ~= 'user_stop' or active.rows < 2 then abandon(reason); return end
        local footer='END,user_stop,'..active.rows..'\n'
        checked(active.file.write,active.file,footer);checked(active.file.flush,active.file);checked(active.file.close,active.file)
        active.parts[#active.parts+1]=footer
        local expected=table.concat(active.parts)
        assert(read_bytes(active.name..'.partial')==expected,'Saved recording verification failed; partial retained')
        local completed=active.name
        checked(os.rename,completed..'.partial',completed..'.csv')
        assert(not lfs.attributes(completed..'.partial') and read_bytes(completed..'.csv')==expected,'Completed recording verification failed')
        active=nil
        write_status('READY\nLast saved: '..completed..'.csv')
        announce('Saved recording: ' .. completed .. '.csv')
    elseif event:match('^BEGIN,') or (active and not id) then
        error('Malformed recording protocol')
    end
end
-- The GUI environment cannot open the simulator's active log file. Read the
-- documented in-process API on every frame to avoid waiting for file flushes.
local ready,last_error=false,nil
local storage_ready=false
local function pump()
    if not storage_ready then storage_check();storage_ready=true end
    assert(type(DCS.getLogHistory)=='function', 'DCS log-history API unavailable')
    local entries,next_index=DCS.getLogHistory(history_index)
    assert(type(entries)=='table' and type(next_index)=='number', 'Invalid DCS log-history response')
    if next_index < history_index then abandon('log history reset') end
    history_index=next_index
    if not ready then ready=true;write_status('READY\nStorage and DCS log history verified.');announce('Automatic save ready: storage write/rename and DCS log-history callback verified.') end
    for _,entry in ipairs(entries) do
        local message=entry.message or entry[4]
        if type(message)=='string' then
            local ok,err=pcall(consume,message)
            if not ok then abandon(tostring(err));write_status('FAILED\n'..tostring(err));announce('Save failed: '..tostring(err)) end
        end
    end
end
local function safe_pump()
    local ok,err=pcall(pump)
    if not ok then
        abandon(tostring(err));write_status('FAILED\n'..tostring(err))
        if tostring(err)~=last_error then announce('Save failed: '..tostring(err));last_error=tostring(err) end
    else last_error=nil end
end
local hooks={onSimulationFrame=safe_pump,onSimulationStop=safe_pump}
write_status('STARTING\nWaiting for the DCS storage check.')
DCS.setUserCallbacks(hooks)
announce('Automatic recording save installed. Completed F10 Stop takes appear in DCSRecorder/recordings; .partial files are never playback-ready.')
