-- Packaged mission sandbox: no I/O, Export, GUI bridge or capture hook.
local root,out,mission_path=assert(arg[1]),assert(arg[2]),assert(arg[3])
-- Startup regression: the replacement hook loads without any simulator,
-- mission bridge or lifecycle callbacks having been initialized.
local announced=false
local hook=assert(loadfile(root..'/hooks/dcs-recorder.lua'))
setfenv(hook,{log={INFO=1,write=function()announced=true end}});hook();assert(announced)
local now=10;local commands={};local scheduled={};local messages={}
local file=assert(io.open(out..'/dcs.log','wb'))
local unit={}
function unit:isExist() return true end
function unit:getPlayerName() return 'Pilot' end
function unit:getTypeName() return 'FA-18C_hornet' end
function unit:getPosition() return {p={x=220*now,y=2000,z=0},x={x=1,y=0,z=0},y={x=0,y=1,z=0},z={x=0,y=0,z=1}} end
function unit:getVelocity() return {x=220,y=0,z=0} end
function unit:getDrawArgumentValue(i)
 if i==21 then return now>12 and 0.5 or 0 end
 if i==0 or i==3 or i==5 then return (now-10)/20 end
 assert(i>=9 and i<=18);return -0.8+(now-10)/30+i/100
end
local env={assert=assert,pairs=pairs,ipairs=ipairs,type=type,tostring=tostring,tonumber=tonumber,string=string,math=math,table=table,
    Unit={getByName=function(n)assert(n=='Observer');return unit end},
    timer={getTime=function()return now end,scheduleFunction=function(fn,arg,time)scheduled[#scheduled+1]={fn=fn,arg=arg,time=time} end},
    env={info=function(message)file:write('2026-09-26 20:00:00.000 INFO SCRIPTING (Main): ',message,'\n') end},
    trigger={action={outText=function(message)messages[#messages+1]=message end}},
    missionCommands={addSubMenu=function()return {} end,addCommand=function(name,menu,fn)commands[name]=fn end}}
local function execute(code)local f=assert(loadstring(code));setfenv(f,env);return f() end
env.a_do_script=execute -- serialized mission trigger API, not a GUI bridge
local loader=assert(loadfile(mission_path));setfenv(loader,env);loader();env.env.mission=env.mission
local trig=env.mission.trig
for i,code in pairs(trig.conditions)do trig.conditions[i]=assert(loadstring(code));setfenv(trig.conditions[i],env) end
for i,code in pairs(trig.actions)do trig.actions[i]=assert(loadstring(code));setfenv(trig.actions[i],env) end
for _,code in pairs(trig.funcStartup)do execute(code) end
local function frame()
    for _,job in ipairs(scheduled)do
        if job.time and now+1e-9>=job.time then job.time=job.fn(job.arg,now) end
    end
end
commands['Start recording']()
for i=1,301 do
    now=10+i*0.02;frame()
    if i==150 then for j=1,6000 do frame() end end
end
commands['Stop recording']();frame()
assert(messages[#messages]:find('301 samples'),'Pause added samples or stop confirmation missing')
commands['Start recording']()
for i=1,301 do now=17+i*0.02;frame() end
commands['Stop recording']()
commands['Start recording']();now=24;frame();file:close()
print('PASS: packaged mission records without a GUI bridge; actual sample clocks, 6000 paused frames, two complete takes, abandoned take, speed brake, stop confirmation')
print(out..'/dcs.log')
