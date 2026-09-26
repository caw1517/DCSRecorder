local id = "DCSRecorder-EFM-Probe"
local root = current_mod_path
declare_plugin(id, {
    installed = true, dirName = root, displayName = "DCS Recorder EFM Probe",
    fileMenuName = id, version = "0.1", state = "installed",
    binaries = { "OwnershipProbe" },
    load_immediately = true,
})
dofile(root .. "/aircraft.lua")
make_flyable(id, root .. "/Cockpit/Scripts/", { id, "OwnershipProbe" }, nil)
plugin_done()
