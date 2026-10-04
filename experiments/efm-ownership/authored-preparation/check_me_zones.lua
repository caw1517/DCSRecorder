-- Load a mission's trigger zones through the installed, unmodified Mission
-- Editor TriggerZoneData module, then save them back and compare fields.
-- Usage: luae.exe check_me_zones.lua <mission.lua> [<DCS root>]
local missionPath, dcs = arg[1], arg[2] or 'D:/DCS World'
assert(missionPath, 'usage: check_me_zones.lua <mission.lua> [<DCS root>]')
package.path = dcs..'/MissionEditor/modules/?.lua;'..dcs..'/Scripts/?.lua;'..package.path
-- Only the Mission Editor's mission registry is stubbed; unlinked zones use
-- nothing from it beyond its unit lookup table.
package.loaded['me_mission'] = {unit_by_id = {}}
package.loaded['me_utilities'] = {}
Factory = require('Factory') -- a global in the Mission Editor runtime

local env = {}
setfenv(assert(loadfile(missionPath)), env)()
local zones = assert(env.mission and env.mission.triggers, 'mission.triggers missing').zones or {}

local Data = require('Mission.TriggerZoneData')
Data.setMissionData({registerTriggerZone = function() end, unregisterTriggerZone = function() end})
Data.onNewMission()
local ok, err = pcall(Data.loadTriggerZones, zones)
if not ok then print('FAIL Mission Editor zone load: '..tostring(err)); os.exit(1) end

local saved, failures = Data.saveTriggerZones(), 0
local function fail(msg) failures = failures + 1; print('FAIL '..msg) end
if #saved ~= #zones then fail(('zone count %d -> %d'):format(#zones, #saved)) end
for i, z in ipairs(zones) do
	local s = saved[i] or {}
	for _, k in ipairs({'name', 'x', 'y', 'radius', 'type', 'hidden', 'heading'}) do
		if s[k] ~= z[k] then fail(('zone %d %s: %s -> %s'):format(i, k, tostring(z[k]), tostring(s[k]))) end
	end
	for c = 1, 4 do
		if (s.color or {})[c] ~= z.color[c] then fail(('zone %d color[%d] changed'):format(i, c)) end
	end
end
if failures > 0 then os.exit(1) end
print(('PASS %d trigger zone(s) load and save through the Mission Editor unchanged'):format(#zones))
