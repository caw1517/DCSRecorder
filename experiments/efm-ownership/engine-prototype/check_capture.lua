-- Offline smoke harness for the packaged mission and GUI hook. No live-state claim.
local here,mission_path,output,mode=assert(arg[1]),assert(arg[2]),assert(arg[3]),arg[4] or 'normal'
local file=assert(io.open(output,'wb'))
local now=10;local history={};local commands={};local scheduled={};local hooks
local phase='baseline';local left,right=0.5,0.5;local engine_calls=0
local function emit(message)
    history[#history+1]={message=message};file:write(message,'\n')
end
local gui={assert=assert,type=type,tostring=tostring,tonumber=tonumber,pcall=pcall,ipairs=ipairs,
    string=string,table=table,math=math,
    log={INFO=1,write=function(_,_,message)emit(message)end},
    DCS={getLogHistory=function(index)
        local entries={};for i=index+1,#history do entries[#entries+1]=history[i] end
        return entries,#history
    end,setUserCallbacks=function(value)hooks=value end},
    Export={
        LoGetModelTime=function()return now+(mode=='stale' and 1 or 0.004) end,
        LoGetPlayerPlaneId=function()return 42 end,
        LoGetSelfData=function()
            if mode=='missing_self' then return nil end
            local result={Name='FA-18C_hornet',UnitName=mode=='identity' and 'Other' or 'Observer',Position={x=now*200,y=2000,z=0}}
            if mode=='identity' then result.Position.x=result.Position.x+100 end
            if mode=='missing_name' then result.UnitName=nil end
            return result
        end,
        LoGetEngineInfo=function()
            engine_calls=engine_calls+1
            if mode=='unavailable' then return nil end
            return {RPM={left=60+left*40,right=60+right*40},Temperature={left=400+left*400,right=400+right*400},FuelConsumption={left=left,right=right}}
        end}}
local f=assert(loadfile(here..'/engine-hook.lua'));setfenv(f,gui);f()
local unit={}
function unit:isExist()return true end
function unit:getPlayerName()return 'Pilot' end
function unit:getTypeName()return 'FA-18C_hornet' end
function unit:getID()return 42 end
function unit:getPosition()return {p={x=now*200,y=2000,z=0}} end
function unit:getDrawArgumentValue(index)if index==89 then return left elseif index==90 then return right else return 0 end end
local env={assert=assert,type=type,tostring=tostring,tonumber=tonumber,pcall=pcall,pairs=pairs,ipairs=ipairs,
    string=string,table=table,math=math,
    Unit={getByName=function()return unit end},env={info=emit},
    timer={getTime=function()return now end,scheduleFunction=function(fn,arg,time)scheduled[#scheduled+1]={fn=fn,arg=arg,time=time}end},
    missionCommands={addSubMenu=function()return {}end,addCommand=function(name,menu,fn)commands[name]=fn end},
    trigger={action={outText=function()end}}}
local function execute(code)local fn=assert(loadstring(code));setfenv(fn,env);return fn()end
env.a_do_script=execute
f=assert(loadfile(mission_path));setfenv(f,env);f()
for i,code in pairs(env.mission.trig.conditions)do env.mission.trig.conditions[i]=assert(loadstring(code));setfenv(env.mission.trig.conditions[i],env)end
for i,code in pairs(env.mission.trig.actions)do env.mission.trig.actions[i]=assert(loadstring(code));setfenv(env.mission.trig.actions[i],env)end
for _,code in pairs(env.mission.trig.funcStartup)do execute(code)end
hooks.onSimulationFrame();assert(engine_calls==0,'Must be idle outside diagnostic capture')
commands['Start capture (4 minute maximum)']();hooks.onSimulationFrame()
local phases={{'both_idle',0,0},{'both_military',0.7,0.7},{'left_afterburner',1,0.7},{'right_afterburner',0.7,1},{'both_afterburner',1,1},{'both_dry',0.7,0.7}}
for _,p in ipairs(phases)do
    commands[p[1]]();left=p[2];right=p[3]
    for i=1,20 do
        now=now+0.05
        for _,job in ipairs(scheduled)do if job.time and now+1e-9>=job.time then job.time=job.fn(job.arg,now)end end
        hooks.onSimulationFrame()
    end
end
local before=engine_calls
for i=1,100 do hooks.onSimulationFrame()end
assert(engine_calls==before,'Pause must not duplicate samples')
commands['Stop capture']();hooks.onSimulationFrame();hooks.onSimulationStop()
assert(engine_calls==before,'Stop must not sample again')
file:close()
print('PASS: packaged mission and hook; independent engines, pause, stop, mode='..mode)
