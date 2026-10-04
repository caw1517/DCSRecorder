local path=assert(arg[1])
local function check(mode)
    local now,queue,logs,removed,smoke=0,{}, {},false,0
    DCSR_HELD_CONFIG={token_high=.2,token_low=.3,smoke=true,expected={[21]=.7,[38]=.9}}
    env={info=function(s)logs[#logs+1]=s end}
    trigger={action={outText=function()end}}
    timer={getTime=function()return now end,scheduleFunction=function(fn,param,t)queue[#queue+1]={fn,param,t}end}
    local lead={}
    function lead:isExist()return not removed end
    function lead:destroy()removed=true end
    function lead:getID()return 17 end
    function lead:getPosition()return {p={x=0,y=2000,z=0},x={x=1,y=0,z=0},y={x=0,y=1,z=0}}end
    function lead:getVelocity()return {x=0,y=0,z=0}end
    function lead:getDrawArgumentValue(i)
        if i==997 then return mode=='mismatch' and .7 or .2 end
        if i==998 then return .3 end
        if i==999 then return mode=='failed' and .75 or (mode=='timeout' or mode=='delayed' and now<.02) and 0 or .125 end
        if i==21 then return mode=='wrong_snapshot' and 0 or .7 end
        if i==38 then return .9 end
        return 0
    end
    function lead:getController()return {setCommand=function(_,c)assert(c.id=='SMOKE_ON_OFF');smoke=smoke+1 end}end
    Unit={getByName=function(name)if mode=='missing' and name=='StagedPlayback' then return nil end;return lead end}
    assert(loadfile(path))()
    if mode=='success' then assert(smoke==1,'ready snapshot smoke deferred past startup')end
    if mode=='delayed' then assert(smoke==0,'smoke initialized before native readiness')end
    local calls=0
    while #queue>0 do
        table.sort(queue,function(a,b)return a[3]<b[3]end)
        local item=table.remove(queue,1);now=item[3]
        local next_time=item[1](item[2],now)
        if next_time then queue[#queue+1]={item[1],item[2],next_time}end
        calls=calls+1;assert(calls<1000,'unbounded test scheduler')
    end
    local joined=table.concat(logs,'\n')
    if mode=='success' or mode=='delayed' then
        assert(joined:find('OBSERVATION_COMPLETE',1,true) and not joined:find('FAILED',1,true),joined)
        assert(removed and smoke==1 and now>=90 and now<91,'cleanup or smoke initialization failed')
        assert(joined:find('SAMPLE,SceneWitness',1,true),'scene witness not observed')
    else
        assert(joined:find('FAILED',1,true) and not joined:find('OBSERVATION_COMPLETE',1,true),joined)
        assert(mode=='missing' or removed,'failed lead not removed')
    end
end
for _,mode in ipairs({'success','delayed','mismatch','failed','timeout','missing','wrong_snapshot'})do check(mode)end
print('PASS: held observation, witness telemetry, smoke once, bounded cleanup, mismatch/failure/timeout/missing refusal')
