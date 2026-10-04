-- The normal configuration checker requires lights OFF. Check this control's
-- deliberate lights-ON trigger against installed cockpit command definitions.
dofile(assert(arg[1]))
local dcs=assert(arg[2])
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')
local expected={
    [devices.EXT_LIGHTS..':'..extlights_commands.Position]=true,
    [devices.EXT_LIGHTS..':'..extlights_commands.Formation]=true,
    [devices.EXT_LIGHTS..':'..extlights_commands.Strobe]=true,
    [devices.EXT_LIGHTS..':'..extlights_commands.LdgTaxi]=true,
    [devices.HOTAS..':'..hotas_commands.THROTTLE_EXTERIOR_LIGHTS]=true,
}
local seen={}
function a_cockpit_perform_clickable_action(device,command,value,plugin)
    local key=device..':'..command
    assert(expected[key] and not seen[key] and value==1 and plugin=='','unexpected light command')
    seen[key]=true
end
assert(loadstring(mission.trig.actions[2]))()
for key in pairs(expected)do assert(seen[key],'missing light command')end
local count=0
for _,action in pairs(mission.trigrules[2].actions)do
    assert(expected[action.cockpit_device..':'..action.command] and action.value==1)
    count=count+1
end
assert(count==5)
print('PASS: five initial light commands match installed Hornet definitions in editor and executable triggers')
