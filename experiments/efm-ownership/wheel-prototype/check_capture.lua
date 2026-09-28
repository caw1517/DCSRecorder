-- Exercise the packaged read-only mission, including paused frames and aborts.
local path=assert(arg[1])
local function run(mode)
    local now=0;local logs,jobs,commands={},{},{}
    local channels={[0]=true,[5]=true,[3]=true,[1]=true,[6]=true,[4]=true,[101]=true,[103]=true,[102]=true}
    local unit={isExist=function()return not(mode=='lost'and now>11)end,
        getPlayerName=function()return 'fixture'end,getTypeName=function()return 'FA-18C_hornet'end,getID=function()return 2 end,
        inAir=function()return mode=='airborne' and now>11 end,
        getPosition=function()return {p={x=now*2,y=45,z=0}}end,
        getVelocity=function()return {x=mode=='fast'and 16 or (now<15 or now>35)and 0 or 2,y=0,z=0}end}
    -- Keep all arguments numeric; fixture motion is not live mapping evidence.
    unit.getDrawArgumentValue=function(_,c)
        assert(channels[c])
        if mode=='invalid'and now>11 then return 0/0 end
        if c>=100 then return (now*.2)%1 end
        return (c==0 or c==5 or c==3)and 1 or .3
    end
    local e={assert=assert,type=type,ipairs=ipairs,pcall=pcall,string=string,math=math,table=table,
        env={info=function(s)logs[#logs+1]=s end},Unit={getByName=function(n)assert(n=='Observer');return unit end},
        trigger={action={outText=function()end}},
        timer={getTime=function()return now end,scheduleFunction=function(fn,_,time)jobs[#jobs+1]={fn=fn,time=time}end},
        missionCommands={addSubMenu=function()return {}end,addCommand=function(s,_,fn)commands[s]=fn end}}
    local function execute(s)local fn=assert(loadstring(s));setfenv(fn,e);return fn()end
    e.a_do_script=execute
    local fn=assert(loadfile(path));setfenv(fn,e);fn()
    local mission=e.mission;assert(#mission.trigrules==1 and #mission.trigrules[1].actions==1)
    assert(mission.trigrules[1].actions[1].predicate=='a_do_script')
    local count=0
    for _,country in pairs(mission.coalition.blue.country)do for _,g in pairs(country.plane.group)do
        assert(g.route.points[1].type=='TakeOffParkingHot')
        for _,u in pairs(g.units)do
            count=count+1;assert(u.name=='Observer'and u.type=='FA-18C_hornet'and u.skill=='Player'and u.speed==0)
            for _,p in pairs(u.payload.pylons)do assert(p.CLSID=='<CLEAN>')end
        end
    end end
    assert(count==1)
    mission.trig.conditions[1]=assert(loadstring(mission.trig.conditions[1]));setfenv(mission.trig.conditions[1],e)
    mission.trig.actions[1]=assert(loadstring(mission.trig.actions[1]));setfenv(mission.trig.actions[1],e)
    for _,code in pairs(mission.trig.funcStartup)do execute(code)end
    assert(#logs==0 and #jobs==0,'capture ran before start')
    commands['Start taxi capture']();assert(not e.DCS_WHEEL_PROBE.active)
    now=10;commands['Start taxi capture']();commands['Start taxi capture']();assert(#jobs==1)
    local function frame()
        for _,job in ipairs(jobs)do if job.time and now+1e-8>=job.time then job.time=job.fn()end end
    end
    for i=1,10000 do
        now=10+i*.02;frame()
        if i==25 then commands['Mark braking']()end
        if i==100 then
            local before=e.DCS_WHEEL_PROBE.rows
            for j=1,1000 do frame()end
            assert(e.DCS_WHEEL_PROBE.rows==before,'pause duplicated samples')
        end
        if mode=='normal' and i==2000 then commands['Stop taxi capture']()end
    end
    assert(not e.DCS_WHEEL_PROBE.active)
    local before=#logs;commands['Start taxi capture']();assert(#jobs==1 and #logs==before)
    local reason,counted;local samples=0
    for _,line in ipairs(logs)do
        local n=line:match('^DCSWHEEL,1,DATA,(%d+),')
        if n then samples=samples+1;assert(tonumber(n)==samples)end
        local why,n=line:match('^DCSWHEEL,1,END,([^,]+),(%d+),')
        if why then assert(not reason);reason=why;counted=tonumber(n)end
    end
    local expected={normal='user_stop',fast='taxi_speed_limit',airborne='airborne',lost='aircraft_lost',invalid='invalid_argument',timeout='time_limit'}
    assert(reason==expected[mode] and counted==samples)
    if mode=='normal'then
        assert(samples==2000)
        if arg[3]then local f=assert(io.open(arg[3],'wb'));f:write(table.concat(logs,'\n'),'\n');f:close()end
    end
    print('PASS: read-only packaged wheel capture '..mode)
end
for _,mode in ipairs({'normal','fast','airborne','lost','invalid','timeout'})do run(mode)end
