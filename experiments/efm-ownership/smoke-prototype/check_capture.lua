-- Exercise the actual packaged capture, including marker/control separation.
dofile(assert(arg[1]))
local commands,scheduled,logs={},nil,{}
local now,smoke=10,0
env={mission=mission,info=function(s)logs[#logs+1]=s end}
trigger={action={outText=function()end}}
missionCommands={addSubMenu=function(s)return s end,addCommand=function(s,menu,fn)commands[s]=fn end}
timer={getTime=function()return now end,scheduleFunction=function(fn)scheduled=fn end}
local unit={isExist=function()return true end,getPlayerName=function()return 'fixture' end,
    getTypeName=function()return 'FA-18C_hornet' end,getID=function()return 2 end,
    getDrawArgumentValue=function(self,i)return i==700 and smoke or 0 end}
Unit={getByName=function(name)assert(name=='Observer');return unit end}
assert(loadstring(mission.trigrules[1].actions[1].text))()
commands['Start capture']();assert(DCS_SMOKE_PROBE.active)
now=10.2;assert(math.abs(scheduled()-10.4)<1e-9)
assert(logs[2]=='DCSSMOKE,1,FRAME,1,1,10.200000000,1000')
local before=#logs
commands['Mark smoke visibly ON']();assert(smoke==0,'Marker commanded aircraft')
smoke=1;now=10.4;scheduled()
assert(logs[#logs]=='DCSSMOKE,1,ARGS,1,2,700=1')
assert(#logs==before+3)
commands['Stop capture']();assert(not DCS_SMOKE_PROBE.active)
assert(logs[#logs]=='DCSSMOKE,1,END,1,user_stop,2')
assert(scheduled()==nil)
commands['Start capture']();now=131;assert(scheduled()==nil)
assert(logs[#logs]=='DCSSMOKE,1,END,2,time_limit,0')
print('PASS: packaged capture baseline/deltas, markers only label, stop and timeout terminate')
