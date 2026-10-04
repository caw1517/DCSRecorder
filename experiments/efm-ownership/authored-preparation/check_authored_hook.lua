-- Exercise a generated authored playback hook with stubbed DCS callbacks.
-- Usage: luae.exe check_authored_hook.lua <payload dir> <control> <mission file> <namespace>
local payload,control,mission_file,namespace=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4])
local dir=payload..'/Scripts/'..control..'/'
local expected=dofile(dir..'expected.lua')
local guard=dofile(dir..'session_guard.lua')
local function copy(v)
    if type(v)~='table' then return v end
    local out={};for k,x in pairs(v)do out[k]=copy(x)end;return out
end
local function first_plane(m)
    for _,c in pairs(m.coalition)do for _,country in pairs(c.country or {})do
        for _,g in pairs((country.plane or {}).group or {})do return g end
    end end
end
local function run(edit,filename,native_reply)
    local armed,logs,callbacks=false,{},nil
    local loaded={mission=copy(expected.mission)}
    local m=loaded.mission
    if edit=='position' then local u=first_plane(m).units[1];u.x=u.x+1
    elseif edit=='trigger' then local _,r=next(m.trigrules);r.comment=(r.comment or '')..' edited'
    elseif edit=='extra_aircraft' then
        local _,c=next(m.coalition.blue.country);local g=c.plane.group;g[#g+1]=copy(g[1])
    elseif edit=='weather' then m.weather.wind.atGround.speed=1 end
    local e=setmetatable({},{__index=_G})
    e.lfs={writedir=function()return 'unused/'end}
    e.dofile=function(path)return path:find('expected.lua',1,true) and expected or guard end
    e.log={INFO=1,write=function(_,_,message)logs[#logs+1]=message end}
    e.DCS={getModelTime=function()return 0 end,getMissionFilename=function()return filename or mission_file end,
        getCurrentMission=function()return loaded end,getMissionDescription=function()return expected.description end,
        getLogHistory=function()return {},0 end,setUserCallbacks=function(c)callbacks=c end}
    e.package={loadlib=function(path,export)
        assert(path:find('/'..control,1,true)==nil and path:find('HornetAuthoredProbe.dll',1,true),'unexpected DLL '..path)
        return function()return native_reply or 'READY,1,0,0' end end}
    e.net={dostring_in=function(_,code)if code:find(namespace..'.arm(',1,true)then armed=true end end}
    local chunk=assert(loadfile(payload..'/Scripts/Hooks/'..control..'.lua'));setfenv(chunk,e);chunk()
    callbacks.onSimulationStart();callbacks.onSimulationFrame()
    return armed,table.concat(logs,'\n')
end
local armed,logs=run(nil)
assert(armed,'Hook did not arm against its own predicted loaded mission:\n'..logs)
for _,edit in ipairs({'position','trigger','extra_aircraft','weather'})do
    assert(not run(edit),'Hook armed despite loaded edit: '..edit)
end
assert(not run(nil,'some-other-mission.miz'),'Hook armed for another mission')
assert(not run(nil,nil,'NOT_READY,0,0,0'),'Hook armed without native readiness')
print('PASS: authored hook arms only for its exact loaded mission and native readiness')
