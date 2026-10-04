-- Regression seam: real hook + real comparison + installed DCS load defaults.
local root,package,dcs=assert(arg[1]),assert(arg[2]),assert(arg[3])
local expected=dofile(package..'/payload/Scripts/DCSRecorderReleaseControl/expected.lua')
-- Optional captured DCS serialization exercises the entire observed load/save
-- boundary instead of only the property-default subsystem.
assert(loadfile(arg[4] or package..'/mission.lua'))()
local normalize=dofile(root..'/experiments/efm-ownership/release-start/loaded_defaults.lua')
normalize(mission,dcs,package..'/payload/Mods/aircraft/DCSRecorder-Hornet-Release-Test/aircraft.lua')
local guard=dofile(root..'/companion/session_guard.lua')
local function copy(value)
    if type(value)~='table' then return value end
    local result={};for k,v in pairs(value)do result[k]=copy(v)end;return result
end
local function run(edited)
    local armed,callbacks=false,nil
    local logs={}
    local actual=copy(mission)
    local unit=actual.coalition.blue.country[1].plane.group[1].units[1]
    if edited=='position' then unit.x=unit.x+1
    elseif edited=='callsign' then unit.AddPropAircraft.VoiceCallsignLabel='ZZ'
    elseif edited=='unknown_property' then unit.AddPropAircraft.Unexpected=1
    elseif edited=='extra_aircraft' then actual.coalition.blue.country[1].plane.group[4]=copy(actual.coalition.blue.country[1].plane.group[1])
    elseif edited=='trigger' then actual.trigrules[1].actions[2].text=actual.trigrules[1].actions[2].text..' -- edit' end
    local e=setmetatable({},{__index=_G})
    e.lfs={writedir=function()return 'test/'end}
    e.dofile=function(path)return path:find('expected.lua',1,true) and expected or guard end
    e.log={INFO=1,write=function(_,_,message)logs[#logs+1]=message end}
    e.DCS={getModelTime=function()return 0 end,getMissionFilename=function()return '043-Hornet-Countdown-Release.miz'end,
        getCurrentMission=function()return actual end,getMissionDescription=function()return expected.description end,
        getLogHistory=function()return {},0 end,setUserCallbacks=function(c)callbacks=c end}
    e.package={loadlib=function()return function()return 'READY,1,0,0'end end}
    e.net={dostring_in=function(_,code)if code:find('DCSR_RELEASE.arm(',1,true)then armed=true end end}
    local chunk=assert(loadfile(root..'/experiments/efm-ownership/release-start/hook.lua'));setfenv(chunk,e);chunk()
    callbacks.onSimulationStart();callbacks.onSimulationFrame()
    assert(armed==not edited,'Readiness gate did not handle loaded defaults/edit correctly:\n'..table.concat(logs,'\n'))
end
run(false)
for _,mode in ipairs({'position','callsign','unknown_property','extra_aircraft','trigger'})do run(mode)end
local authored=copy(mission)
local unit=authored.coalition.blue.country[1].plane.group[1].units[1]
unit.AddPropAircraft.VoiceCallsignLabel='ZX';unit.AddPropAircraft.STN_L16='12345'
unit.datalinks.Link16.settings.AIC_Channel=9
normalize(authored,dcs,package..'/payload/Mods/aircraft/DCSRecorder-Hornet-Release-Test/aircraft.lua')
assert(unit.AddPropAircraft.VoiceCallsignLabel=='ZX' and unit.AddPropAircraft.STN_L16=='12345' and
    unit.datalinks.Link16.settings.AIC_Channel==9,'authored datalink configuration overwritten')
print('PASS: installed loading defaults accepted; authored values preserved; position/callsign/extra field/aircraft/trigger changes refused')
