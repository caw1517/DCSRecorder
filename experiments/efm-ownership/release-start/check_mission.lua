local path=assert(arg[1])
local function run(mode)
    local now,queue,logs,commands,flags=0,{},{},{},{}
    local status,elapsed,removed,smoke=.125,0,false,0
    DCSR_RELEASE_CONFIG={token_high=.2,token_low=.3,duration=8,expected={[21]=.7},smoke_events={{time=0,on=true},{time=2,on=false}}}
    env={info=function(s)logs[#logs+1]=s end}
    trigger={action={outText=function()end,setUserFlag=function(k,v)flags[k]=v end}}
    timer={getTime=function()return now end,scheduleFunction=function(fn,param,t)queue[#queue+1]={fn,param,t}end}
    missionCommands={addSubMenu=function()return 1 end,addCommand=function(name,menu,fn)commands[name]=fn end}
    local unit={}
    function unit:isExist()return not removed end
    function unit:destroy()removed=true end
    function unit:getPosition()return {p={x=10,y=2000,z=30},x={x=1,y=0,z=0},y={x=0,y=1,z=0}}end
    function unit:getVelocity()return {x=status==.25 and 140 or 0,y=0,z=0}end
    function unit:getDrawArgumentValue(i)
        if i==997 then return mode=='mismatch' and .7 or .2 end
        if i==998 then return .3 end
        if i==999 then return status end
        if i==996 then return elapsed/1000 end
        if i==21 then return mode=='bad_snapshot' and 0 or .7 end
        return 0
    end
    function unit:getController()return {setCommand=function(_,c)assert(c.id=='SMOKE_ON_OFF');smoke=smoke+1 end}end
    Unit={getByName=function(name)if mode=='missing' and name=='StagedPlayback' then return nil end;return unit end}
    assert(loadfile(path))()
    local s=DCSR_RELEASE
    local function advance(to)
        local loops=0
        while #queue>0 do
            table.sort(queue,function(a,b)return a[3]<b[3]end)
            if queue[1][3]>to then break end
            local item=table.remove(queue,1);now=item[3]
            local next_time=item[1](item[2],now)
            if next_time then queue[#queue+1]={item[1],item[2],next_time}end
            loops=loops+1;assert(loops<10000)
        end
        now=to
    end
    if mode=='mismatch' or mode=='bad_snapshot' or mode=='missing' then
        assert(s.phase=='failed' and flags.DCSR_RELEASE_CLEANUP==1,'unsafe initial readiness');return
    end
    if mode=='no_bridge' then advance(11);assert(s.phase=='failed' and removed);return end
    assert(s.arm('session',1) and s.phase=='waiting')
    advance(20);assert(elapsed==0 and smoke==1)
    commands['Start playback (3-second countdown)']()
    commands['Start playback (3-second countdown)']()
    assert(s.phase=='countdown')
    advance(22.9);assert(s.phase=='countdown' and not flags.DCSR_RELEASE_PENDING or flags.DCSR_RELEASE_PENDING==0)
    -- A real pause supplies no model-time advance to the mission scheduler.
    for i=1,100 do advance(22.9)end
    assert(s.phase=='countdown')
    if mode=='readiness_lost' then status=.75;advance(23.1);assert(s.phase=='failed' and removed);return end
    advance(23.01);assert(s.phase=='requested' and flags.DCSR_RELEASE_PENDING==1)
    local requests=0;for _,line in ipairs(logs)do if line:find('DCSR_RELEASE REQUEST,',1,true)then requests=requests+1 end end
    assert(requests==1,'duplicate start request')
    if mode=='no_ack' then advance(24.1);assert(s.phase=='failed' and removed and flags.DCSR_RELEASE_CLEANUP==1);return end
    assert(s.released('session',1) and s.phase=='starting' and not s.held)
    status=.25;advance(23.04);assert(s.phase=='playing')
    assert(flags.DCSR_RELEASE_PENDING==0 and smoke==1,'release toggled recorded smoke')
    commands['Start playback (3-second countdown)']();assert(s.phase=='playing')
    for i=1,100 do advance(23.04)end
    elapsed=2;advance(23.08);assert(smoke==2,'smoke did not use native replay time')
    if mode=='playing_failure' then status=.75;advance(23.12);assert(s.phase=='failed' and flags.DCSR_RELEASE_CLEANUP==0);return end
    status=.5;elapsed=8;advance(23.12)
    assert(s.phase=='complete' and removed and flags.DCSR_RELEASE_CLEANUP==0)
end
for _,mode in ipairs({'success','mismatch','bad_snapshot','missing','no_bridge','readiness_lost','no_ack','playing_failure'})do run(mode)end
print('PASS: mission countdown, native-clock smoke, repeated requests, pause, initial/readiness/ack failure, held cleanup and completion')
