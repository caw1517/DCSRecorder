-- Exercise saved mission light triggers, using installed cockpit command IDs.
local mission_path,dcs=assert(arg[1]),assert(arg[2])
dofile(mission_path)
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/devices.lua')
dofile(dcs..'/Mods/aircraft/FA-18C/Cockpit/Scripts/command_defs.lua')
local expected={}
for _,name in ipairs({'Position','Formation','Strobe','LdgTaxi'}) do expected[extlights_commands[name]]=true end
local count=0
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        for _,unit in pairs(group.units) do
            count=count+1
            for _,station in ipairs({2,3,5,7,8}) do
                assert(unit.payload.pylons[station] and unit.payload.pylons[station].CLSID=='<CLEAN>',unit.name..': removable pylon still fitted')
            end
            for _,loadout in pairs(unit.payload.pylons) do assert(loadout.CLSID=='<CLEAN>','External store remains') end
        end
    end
end
assert(count==tonumber(arg[3] or 2))
local time=0
function c_time_after(t) return time>t end
local calls={}
function a_cockpit_perform_clickable_action(device,command,value,plugin)
    assert(device==devices.EXT_LIGHTS and expected[command] and value==0 and plugin=='','Incorrect light command')
    calls[command]=(calls[command] or 0)+1
end
assert(mission.trig.func[2],'Missing lights-off trigger')
local run=assert(loadstring(mission.trig.func[2]))
mission.trig.conditions[2]=assert(loadstring(mission.trig.conditions[2]))
mission.trig.actions[2]=assert(loadstring(mission.trig.actions[2]))
run(); assert(not next(calls),'Lights trigger ran before initialization')
time=2; run()
for command in pairs(expected) do assert(calls[command]==1,'Light switch was not turned off') end
assert(mission.trig.func[2]==nil,'Lights initialization did not remove its trigger')
print('PASS: '..count..' jets have all removable pylons removed; timed trigger turns all four installed Hornet exterior-light controls off once')
