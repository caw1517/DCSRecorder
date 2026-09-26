-- Run the real mission sampler and hook with a local fake simulator.
local root,out=assert(arg[1]),assert(arg[2])
-- The standalone Lua runner lacks lfs; the harness creates output directories.
local real_lfs={mkdir=function() return true end,attributes=function(path)
    local f=io.open(path,'rb');if f then f:close();return {} end
end}
local now=10;local callbacks;local commands={};local exists=true
local unit={}
function unit:isExist() return exists end
function unit:getPlayerName() return 'Pilot' end
function unit:getTypeName() return 'FA-18C_hornet' end
function unit:getPosition() return {p={x=220*now,y=2000,z=0},x={x=1,y=0,z=0},y={x=0,y=1,z=0},z={x=0,y=0,z=1}} end
function unit:getVelocity() return {x=220,y=0,z=0} end
function unit:getDrawArgumentValue(index) assert(index==21);return now>12 and 0.5 or 0 end
local mission_env=setmetatable({Unit={getByName=function(name) assert(name=='Observer');return unit end},
    timer={getTime=function() return now end},
    env={mission={theatre='Caucasus',coalition={blue={country={{plane={group={{units={{name='Observer',livery_id='Blue Angels Jet Team'}}}}}}}}}}},
    trigger={action={outText=function() end}},missionCommands={addSubMenu=function() return {} end,
        addCommand=function(name,menu,fn) commands[name]=fn end}}, {__index=_G})
local function execute(code) local fn=assert(loadstring(code));setfenv(fn,mission_env);return fn() end
mission_env.a_do_script=execute
local loader
if arg[3] then
    -- Exercise the serialized mission startup rather than just its source script.
    loader=assert(loadfile(arg[3]));setfenv(loader,mission_env);loader()
    local trig=mission_env.mission.trig
    for i,code in pairs(trig.conditions) do trig.conditions[i]=assert(loadstring(code));setfenv(trig.conditions[i],mission_env) end
    for i,code in pairs(trig.actions) do trig.actions[i]=assert(loadstring(code));setfenv(trig.actions[i],mission_env) end
    for _,code in pairs(trig.funcStartup) do execute(code) end
else
    loader=assert(loadfile(root..'/record_flight_mission.lua'));setfenv(loader,mission_env);loader()
end
local messages={};local filename='EFM-Probe-Hornet-record.miz'
local hook_env=setmetatable({lfs={writedir=function() return out..'/' end,mkdir=real_lfs.mkdir,attributes=real_lfs.attributes},
    DCS={getMissionFilename=function() return filename end,getModelTime=function() return now end,
        setUserCallbacks=function(h) callbacks=h end},
    Export={LoGetEngineInfo=function() return {RPM={left=82,right=83}} end},
    log={INFO=1,write=function(tag,level,message) messages[#messages+1]=message end},
    a_do_script=execute}, {__index=_G})
loader=assert(loadfile(root..'/hooks/dcs-recorder.lua'));setfenv(loader,hook_env);loader()
-- Reproduce the two callback/environment conditions seen in the live DCS log.
if arg[4]=='before_start' then callbacks.onSimulationFrame() end
if arg[4]=='no_bridge' then hook_env.a_do_script=nil end
callbacks.onSimulationStart();callbacks.onSimulationFrame()
commands['Start recording']()
filename='unrelated.miz';now=10.02;callbacks.onSimulationFrame()
assert(#messages==0,'Recorder must ignore other missions')
filename='EFM-Probe-Hornet-record.miz'
for i=0,300 do now=10.04+i*0.02;callbacks.onSimulationFrame();callbacks.onSimulationFrame() end
commands['Stop recording']();now=16.1;callbacks.onSimulationFrame()
assert(#messages==2 and messages[2]:find('Recording saved:'),'Start/stop did not save exactly one take')
local saved=messages[2]:match('Recording saved: (.+)')
local f=assert(io.open(saved,'rb'));local text=f:read('*a');f:close()
assert(text:find('END,user_stop,301'),'Paused duplicate frames must not add rows')
assert(text:find(',0.5,82,83'),'Speed brake and optional per-engine RPM must be captured')
commands['Start recording']();now=17;callbacks.onSimulationFrame()
now=17.04;callbacks.onSimulationFrame();callbacks.onSimulationStop()
assert(messages[4]:find('Recording saved:') and messages[4]~=messages[2],'Takes must have independent files')
print('PASS: actual mission sampler + GUI hook; mission isolation, metadata, two takes, real sample clocks, pause deduplication, speed brake/RPM, stop and mission-end flush')
print(saved)
