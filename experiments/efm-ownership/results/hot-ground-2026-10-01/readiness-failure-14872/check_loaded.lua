local repo,package,captured=assert(arg[1]),assert(arg[2]),assert(arg[3])
local expected=dofile(package..'/payload/Scripts/DCSRecorderGroundControl/expected.lua')
assert(loadfile(captured))()
local guard=dofile(repo..'/companion/session_guard.lua')
local function copy(v)if type(v)~='table' then return v end;local r={};for k,x in pairs(v)do r[k]=copy(x)end;return r end
local function run(mode)
    local actual=copy(mission)
    local groups=actual.coalition.blue.country[1].plane.group
    if mode=='player_position' then groups[1].units[1].x=groups[1].units[1].x+1
    elseif mode=='witness_route' then groups[3].route.points[2].y=groups[3].route.points[2].y+1
    elseif mode=='witness_eta' then groups[3].route.points[2].ETA=groups[3].route.points[2].ETA+.01
    elseif mode=='extra_aircraft' then groups[4]=copy(groups[1])
    elseif mode=='trigger' then actual.trigrules[1].actions[2].text=actual.trigrules[1].actions[2].text..' -- changed'
    elseif mode=='weather' then actual.weather.wind.atGround.speed=1 end
    local callbacks,armed=nil,false;local logs={}
    local e=setmetatable({},{__index=_G})
    e.lfs={writedir=function()return 'fixture/'end}
    e.dofile=function(p)return p:find('expected.lua',1,true) and expected or guard end
    e.log={INFO=1,write=function(_,_,s)logs[#logs+1]=s end}
    e.DCS={getModelTime=function()return 0 end,getMissionFilename=function()return '049-Hornet-Ground-Hold-Release.miz'end,
        getCurrentMission=function()return actual end,getMissionDescription=function()return expected.description end,
        getLogHistory=function()return {},0 end,setUserCallbacks=function(v)callbacks=v end}
    e.package={loadlib=function()return function()return 'READY,1,0,0'end end}
    e.net={dostring_in=function(_,s)if s:find('DCSR_RELEASE.arm(',1,true)then armed=true end end}
    local fn=assert(loadfile(package..'/payload/Scripts/Hooks/DCSRecorderGroundControl.lua'));setfenv(fn,e);fn()
    callbacks.onSimulationStart();callbacks.onSimulationFrame()
    assert(armed==(mode==nil),'unexpected readiness for '..tostring(mode)..'\n'..table.concat(logs,'\n'))
end
run(nil)
for _,mode in ipairs({'player_position','witness_route','witness_eta','extra_aircraft','trigger','weather'})do run(mode)end
print('PASS: actual captured mission passes real hook; edited positions/routes/ETA/aircraft/triggers/weather refused')
