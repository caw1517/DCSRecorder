-- THROWAWAY read-only diagnostic. Does not authorize or block recorder/playback.
-- Install temporarily as a separate Saved Games hook, restart DCS, then remove.
local hooks = {}
local dir = lfs.writedir() .. 'Scripts/DCSRecorderIdentityProbe/'
local function read(path)
    local f = io.open(path, 'rb')
    if not f then return nil end
    local bytes = f:read('*a')
    f:close()
    return bytes
end
-- External immutable reference, read at hook startup, not from the tested archive.
local expected = read(dir .. 'expected.miz')
local active = false
local nextSample = 0
local lastResult = nil
local function observe(event)
    local filename = DCS.getMissionFilename() or ''
    local ok, current = pcall(DCS.getCurrentMission)
    local m = ok and type(current) == 'table' and (current.mission or current) or {}
    local description = tostring(m.descriptionText or '')
    local target = filename:find('Identity%-LoadProbe') or description:find('IDENTITY_LOAD_PROBE')
    if not target and not active then return end
    active = not not target
    local actual = filename ~= '' and read(filename) or nil
    local result = not expected and 'NO_EXPECTED' or not actual and 'UNREADABLE' or actual == expected and 'MATCH' or 'MISMATCH'
    local marker = description:find('EDITED') and 'EDITED' or description:find('ORIGINAL') and 'ORIGINAL' or 'UNKNOWN'
    local state = filename .. '|' .. result .. '|' .. marker
    if event ~= 'frame' or state ~= lastResult then
        log.write('IDENTITY_PROBE', log.INFO, 'event='..event..' result='..result..' marker='..marker..' expected_bytes='..tostring(expected and #expected or 0)..' actual_bytes='..tostring(actual and #actual or 0)..' filename='..filename)
        lastResult = state
    end
end
local function safe(event)
    local ok, err = pcall(observe, event)
    if not ok then log.write('IDENTITY_PROBE', log.ERROR, tostring(err)) end
end
function hooks.onMissionLoadBegin() nextSample=0; lastResult=nil; safe('load_begin') end
function hooks.onMissionLoadEnd() safe('load_end') end
function hooks.onSimulationStart() safe('simulation_start') end
function hooks.onSimulationStop() safe('simulation_stop'); active=false end
function hooks.onSimulationFrame()
    local now = DCS.getRealTime()
    if now >= nextSample then nextSample=now+1; safe('frame') end
end
DCS.setUserCallbacks(hooks)
log.write('IDENTITY_PROBE', log.INFO, 'hook_installed expected_bytes='..tostring(expected and #expected or 0))
