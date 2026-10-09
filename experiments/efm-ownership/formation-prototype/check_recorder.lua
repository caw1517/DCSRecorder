-- The injected recorder in formation mode, with stubbed mission APIs: no F10
-- Start; begin_formation takes the first sample in the release callback itself,
-- events reach the log with the take number, and Stop saves as usual.
-- Usage: luae.exe check_recorder.lua <recorder script> <namespace> <player name> [solo]
local path,namespace,player=assert(arg[1]),assert(arg[2]),assert(arg[3])
local now,logs,commands,queue=33,{},{},{}
local unit={}
function unit:isExist()return true end
function unit:getPlayerName()return 'Pilot' end
function unit:getTypeName()return 'FA-18C_hornet' end
function unit:getID()return 12 end
function unit:getPosition()return {p={x=100+now,y=10,z=200},x={x=1,y=0,z=0},y={x=0,y=1,z=0},z={x=0,y=0,z=1}}end
function unit:getVelocity()return {x=0,y=0,z=0}end
function unit:getDrawArgumentValue(i)return i==2 and -.5 or 0 end
function unit:inAir()return false end
function unit:getLife()return 1 end
function unit:getLife0()return 1 end
env={info=function(text)logs[#logs+1]=text end,
    mission={theatre='Caucasus',coalition={blue={country={{plane={group={{units={{name=player,livery_id='Blue Angels Jet Team'}}}}}}}}}}}
land={getHeight=function()return 10 end,getSurfaceType=function()return 5 end}
Unit={getByName=function(name)assert(name==player,'recorded the wrong aircraft '..tostring(name));return unit end}
trigger={action={outText=function()end}}
timer={getTime=function()return now end,scheduleFunction=function(fn,arg,t)queue[#queue+1]={fn,arg,t}end}
missionCommands={addSubMenu=function()return 1 end,addCommand=function(name,_,fn)commands[name]=fn end}
assert(loadfile(path))()
local r=assert(_G[namespace],'recorder global missing')
local function decoded(line)
    local hex=assert(line:match('BEGIN,1,(%x+)$'));return (hex:gsub('..',function(h)return string.char(tonumber(h,16))end))
end
local function run_queue(count)
    for _=1,count do
        table.sort(queue,function(x,y)return x[3]<y[3]end)
        local item=table.remove(queue,1);now=item[3];local t=item[1](item[2],now);if t then queue[#queue+1]={item[1],item[2],t}end
    end
end
if arg[4]=='solo' then
    -- The unchanged solo path: F10 Start samples from the next frame, with sync counts.
    assert(commands['Start recording'] and commands['Stop recording'] and not r.begin_formation,'solo recorder menu changed')
    commands['Start recording']()
    assert(decoded(logs[1]):find('\nsource,"'..player..'"\n',1,true) and #logs==1,'solo BEGIN')
    run_queue(20)
    assert(logs[2]:match('^DCSREC_LOG,1,DATA,1,1,33.02,'),'solo first sample: '..tostring(logs[2]))
    commands['Stop recording']()
    assert(logs[#logs]:match('^DCSREC_LOG,1,END,1,user_stop,%d+$'),'solo stop')
    print('PASS: solo recorder keeps F10 Start, its first sample on the next frame, and Stop')
    return
end
assert(not commands['Start recording'] and commands['Stop recording'],'formation recorder offers F10 Start')
assert(r.begin_formation('formation_id,'..string.rep('f',32)..'\nformation_version,2\nformation_epoch,33.000000000\n'))
assert(not r.begin_formation(''),'second begin accepted')
local metadata=decoded(logs[1])
assert(metadata:find('\nsource,"'..player..'"\n',1,true) and metadata:find('\nformation_epoch,33.000000000\n$'),'metadata: '..metadata)
assert(logs[2]:match('^DCSREC_LOG,1,DATA,1,1,33,'),'first sample not taken at the release: '..tostring(logs[2]))
r.event('not_ready',string.rep('c',32))
run_queue(10)
r.event('failed',string.rep('a',32),now-33)
commands['Stop recording']()
local function has(pattern)for _,l in ipairs(logs)do if l:find(pattern,1,true)then return true end end;return false end
assert(has('DCSREC_LOG,1,EVENT,1,not_ready,'..string.rep('c',32)..','),'not-ready event')
assert(has('DCSREC_LOG,1,EVENT,1,failed,'..string.rep('a',32)..',0.200'),'failure event with replay time')
assert(has('DCSREC_LOG,1,DATA,1,11,') and has('DCSREC_LOG,1,END,1,user_stop,11'),'samples or stop missing')
r.event('ended',string.rep('b',32),1)
assert(not has('EVENT,1,ended'),'event logged after the take stopped')
print('PASS: formation recorder has no F10 Start, samples at the release, logs events and stops as usual')
