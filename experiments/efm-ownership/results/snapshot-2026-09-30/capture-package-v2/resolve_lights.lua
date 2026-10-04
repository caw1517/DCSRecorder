dofile(arg[1]..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')
dofile(arg[1]..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')
print(devices.HOTAS,hotas_commands.THROTTLE_EXTERIOR_LIGHTS)
