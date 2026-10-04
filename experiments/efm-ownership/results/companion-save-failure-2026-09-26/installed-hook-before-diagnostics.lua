-- Durable sink for the mission recorder's versioned log protocol.
-- Runs in the GUI hook environment; never evaluates mission text or uses a bridge.
local root = lfs.writedir() .. 'DCSRecorder/'
assert(lfs.mkdir(root) or lfs.attributes(root, 'mode') == 'directory')
local directory = root .. 'recordings/'
assert(lfs.mkdir(directory) or lfs.attributes(directory, 'mode') == 'directory')
local columns = 't,x,y,z,fx,fy,fz,ux,uy,uz,rx,ry,rz,vx,vy,vz,speedbrake,rpm_left,rpm_right\n'
local position, pending, active, serial, frame = 0, '', nil, 0, 0
local function announce(text) log.write('DCS_RECORDER_SAVE', log.INFO, text) end
local function abandon(reason)
    if active then pcall(function() active.file:flush(); active.file:close() end); active = nil; announce('Incomplete recording retained: ' .. reason) end
end
local function open_take(id, hex)
    abandon('new take')
    assert(#hex <= 8192 and #hex % 2 == 0 and not hex:find('[^%x]'), 'Invalid recorder metadata')
    local metadata = hex:gsub('..', function(pair) return string.char(tonumber(pair,16)) end)
    assert(metadata:sub(1,9) == 'DCSREC,1\n', 'Invalid recorder version')
    local filename
    repeat
        serial = serial + 1
        filename = directory .. os.date('!%Y%m%dT%H%M%SZ') .. '-' .. string.format('%04d',serial)
    until not lfs.attributes(filename .. '.partial') and not lfs.attributes(filename .. '.csv')
    local file = assert(io.open(filename .. '.partial', 'wb'))
    active = {id=id, rows=0, file=file, name=filename}
    assert(file:write(metadata,columns)); assert(file:flush())
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
        assert(commas == 18 and #data < 4096 and active.rows < 20000, 'Malformed or oversized recording')
        assert(active.file:write(data,'\n')); active.rows = active.rows + 1
        if active.rows % 50 == 0 then assert(active.file:flush()) end
        return
    end
    local reason
    id,reason,count = event:match('^END,(%d+),([%w_]+),(%d+)$')
    if id and active and id == active.id then
        assert(tonumber(count) == active.rows, 'Recording footer count mismatch')
        if reason ~= 'user_stop' or active.rows < 2 then abandon(reason); return end
        assert(active.file:write('END,user_stop,',active.rows,'\n')); assert(active.file:flush()); assert(active.file:close())
        local completed = active.name; active = nil
        assert(os.rename(completed .. '.partial',completed .. '.csv'))
        announce('Saved recording: ' .. completed .. '.csv')
    elseif event:match('^BEGIN,') or (active and not id) then
        error('Malformed recording protocol')
    end
end
local function pump()
    local input = io.open(lfs.writedir() .. 'Logs/dcs.log','rb')
    if not input then return end
    local size = input:seek('end')
    if size < position then position=0; pending=''; abandon('log truncated') end
    assert(input:seek('set',position))
    local chunk = input:read(262144) or ''
    position = position + #chunk; input:close()
    pending = pending .. chunk
    while true do
        local ending = pending:find('\n',1,true)
        if not ending then break end
        local line = pending:sub(1,ending-1); pending=pending:sub(ending+1)
        local ok,err = pcall(consume,line)
        if not ok then abandon(tostring(err)); announce('Save failed: ' .. tostring(err)) end
    end
    if #pending > 1048576 then pending=''; abandon('oversized log line') end
end
local function safe_pump()
    local ok,err = pcall(pump)
    if not ok then abandon(tostring(err)); announce('Save failed: ' .. tostring(err)) end
end
local hooks = {}
function hooks.onSimulationFrame()
    frame=frame+1
    if frame % 15 == 0 then safe_pump() end
end
function hooks.onSimulationStop() safe_pump() end
DCS.setUserCallbacks(hooks)
announce('Automatic recording save installed. Completed F10 Stop takes appear in DCSRecorder/recordings; .partial files are never playback-ready.')
