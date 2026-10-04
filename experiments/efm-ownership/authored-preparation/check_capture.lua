-- Run the actual generated recorder under a small mission API fixture.
assert(loadfile(assert(arg[1])))()
local original,owned=mission.trigrules[1],mission.trigrules[2]
assert(original.comment=='Authored message, resource and occupied flag')
assert(owned.comment=='DCS Recorder: record selected authored Hornet')
local script=owned.actions[1].text
assert(loadstring(script))
local menu,logs={},{}
local u={isExist=function()return true end,getTypeName=function()return 'FA-18C_hornet'end,
 getID=function()return 12201 end,getPlayerName=function()return 'Tester'end,
 getPosition=function()return {p={x=1,y=1800,z=3},x={x=1,y=0,z=0},y={x=0,y=1,z=0},z={x=0,y=0,z=1}}end,
 getVelocity=function()return {x=140,y=0,z=0}end,getDrawArgumentValue=function()return 0 end}
local e=setmetatable({},{__index=_G})
e.env={mission=mission,info=function(msg)logs[#logs+1]=msg end}
e.Unit={getByName=function(name)assert(name=='Record Hornet');return u end}
e.trigger={action={outText=function()end}}
local now=1;local tick
e.timer={getTime=function()return now end,scheduleFunction=function(fn)tick=fn end}
e.missionCommands={addSubMenu=function()return 1 end,addCommand=function(name,_,fn)menu[name]=fn end}
local chunk=assert(loadstring(script));setfenv(chunk,e);chunk()
assert(e.DCSRECORDER==nil,'Fixed global leaked')
local recorder=assert(e.DCSR_AUTHORED_2)
local metadata=assert(recorder.metadata())
assert(metadata:find('\nsource,"Record Hornet"\n',1,true))
assert(metadata:find('\ncapture_build,2.9.30.28536\n',1,true))
assert(metadata:find('\nauthored_source_sha256,',1,true))
assert(metadata:find('\nwheel_profile,hornet-wheels-v1',1,true))
menu['Start recording']();now=1.02;tick();menu['Stop recording']()
assert(recorder.rows==1 and recorder.state=='stopped')
assert(logs[1]:find('DCSREC_LOG,1,BEGIN,1,',1,true))
assert(logs[2]:find('DCSREC_LOG,1,DATA,1,1,',1,true))
assert(logs[3]=='DCSREC_LOG,1,END,1,user_stop,1')
print('PASS: selected authored name, complete metadata, isolated globals and autosave protocol')
