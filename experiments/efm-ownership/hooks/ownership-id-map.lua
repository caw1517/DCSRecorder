-- Read-only diagnostic: map mission IDs to engine runtime IDs using Sim Control API.
local hooks = {}
local next_sample = 0
local seen = {}
local function write(message)
    log.write('OWNERSHIP_ID', log.INFO, message)
end
function hooks.onSimulationStart()
    next_sample = 0
    seen = {}
end
function hooks.onSimulationFrame()
    local filename = DCS.getMissionFilename() or ''
    if not filename:find('EFM%-Probe%-') then return end
    local now = DCS.getModelTime()
    if now < next_sample then return end
    next_sample = now + 1
    for _,mission_id in ipairs({9001, 2}) do
        local ok, runtime_id = pcall(DCS.getUnitProperty, mission_id, DCS.UNIT_RUNTIME_ID)
        local key = tostring(ok)..':'..tostring(runtime_id)
        if seen[mission_id] ~= key then
            seen[mission_id] = key
            write(string.format('mission_id=%s runtime_id=%s success=%s model_time=%.3f',
                tostring(mission_id), tostring(runtime_id), tostring(ok), now))
        end
    end
end
DCS.setUserCallbacks(hooks)
