-- Execute the actual packaged recorder with a stock-aircraft API fixture.
dofile(assert(arg[1]))
local group=mission.coalition.blue.country[1].plane.group[1]
local source=group.units[1]
assert(source.type=='FA-18C_hornet' and source.skill=='Player' and source.name=='Observer')
assert(source.parking_id=='15' and source.parking=='1' and source.speed==0)
assert(group.route.points[1].type=='TakeOffParkingHot')
assert(group.route.points[1].action=='From Parking Area Hot' and group.route.points[1].airdromeId==25)
assert(source.livery_id=='Blue Angels Jet Team')
assert(source.payload.pylons[10].CLSID=='{INV-SMOKE-WHITE}')
for k,v in pairs(source.payload.pylons) do assert(k==10 or v.CLSID=='<CLEAN>') end
local script=mission.trigrules[1].actions[1].text
assert(loadstring(script))
local nested
function a_do_script(s) nested=s end
assert(loadstring(mission.trig.actions[1]))()
assert(nested==script)
local now=10
local scheduled,commands,logs,events={},{},{},{}
timer={getTime=function()return now end,scheduleFunction=function(fn,a,t)scheduled[#scheduled+1]={fn=fn,a=a,t=t}end}
missionCommands={addSubMenu=function()return {}end,addCommand=function(name,menu,fn)commands[name]=fn end}
trigger={action={outText=function()end}}
env={mission=mission,info=function(text)logs[#logs+1]=text end}
world={addEventHandler=function(handler)events[#events+1]=handler end}
local ground_height,air,life=20,false,100
land={getHeight=function(p)assert(p.x==source.x and p.y==source.y);return ground_height end,
    getSurfaceType=function()return 4 end}
local unit={isExist=function()return true end,getPlayerName=function()return 'pilot'end,
    getTypeName=function()return 'FA-18C_hornet'end,getID=function()return tostring(source.unitId) end,
    getPosition=function()return {p={x=source.x,y=22,z=source.y},x={x=1,y=0,z=0},y={x=0,y=1,z=0},z={x=0,y=0,z=1}}end,
    getVelocity=function()return{x=0,y=0,z=0}end,
    getDrawArgumentValue=function()return 0 end,
    inAir=function()return air end,getLife=function()return life end,getLife0=function()return 100 end}
Unit={getByName=function(name)assert(name=='Observer');return unit end}
assert(loadstring(script))()
assert(#events==1)
commands['Start recording']()
assert(DCSRECORDER.state=='recording')
local sample_tick=scheduled[#scheduled].fn
now=10.02;sample_tick()
assert(DCSRECORDER.rows==1)
now=10.04;sample_tick()
assert(DCSRECORDER.rows==2)
sample_tick() -- same simulation timestamp must not duplicate either stream
assert(DCSRECORDER.rows==2)
local function count(prefix)
    local n=0;for _,line in ipairs(logs)do if line:sub(1,#prefix)==prefix then n=n+1 end end;return n
end
assert(count('DCSGROUND,1,DATA,')==2 and count('DCSREC_LOG,1,DATA,')==2)
assert(count('DCSGROUND,1,DATA,1,1,10.02,'..source.unitId..',0,20,2,100,100,4')==1)
assert(count('DCSGROUND,1,BEGIN,1,'..DCSGROUND_SOURCE_ID..',Observer')==1)
-- A changing contact/damage signal is retained, not silently forced to grounded.
now=10.06;air=true;life=90;sample_tick()
assert(count('DCSGROUND,1,DATA,1,3,10.06,'..source.unitId..',1,20,2,90,100,4')==1)
events[1]:onEvent({initiator=unit,time=now,id=2})
assert(count('DCSGROUND,1,EVENT,1,10.06,2')==1)
commands['Stop recording']()
scheduled[1].fn()
assert(count('DCSGROUND,1,END,1,3,stopped')==1)
assert(count('DCSREC_LOG,1,END,1,user_stop,3')==1)
-- Missing required contact evidence must make the take incomplete.
commands['Start recording']()
sample_tick=scheduled[#scheduled].fn
now=11;ground_height=0/0;sample_tick()
assert(DCSRECORDER.state=='stopped')
assert(count('DCSGROUND,1,ERROR,2,11,ground_evidence_unavailable')==1)
assert(count('DCSREC_LOG,1,END,2,invalid_sample,0')==1)
print('PASS: packaged hot-ground recorder, synchronized contact rows, duplicates, damage/contact transitions, stop, and missing-evidence refusal')
