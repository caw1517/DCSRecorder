-- Mission lifecycle checks with an explicit fake controller, not a DCS runtime test.
local script=assert(arg[1])
local function session()
    local test={now=0,status=0,exists=false,removed=0,jobs={},commands={},events={},high=0.123,low=0.456}
    local unit={}
    function unit:isExist()return test.exists end
    function unit:destroy()test.exists=false;test.removed=test.removed+1 end
    function unit:getDrawArgumentValue(index)
        if index==999 then return test.status end
        if index==997 then return test.high end
        if index==998 then return test.low end
        return 0
    end
    function unit:getPosition()return {p={x=0,y=2000,z=0},x={x=1,y=0,z=0},y={x=0,y=1,z=0}} end
    function unit:getVelocity()return {x=220,y=0,z=0} end
    local player={isExist=function()return true end,getDrawArgumentValue=function()return 0 end,
        getPosition=unit.getPosition,getVelocity=unit.getVelocity,
        destroy=function()error('Playback destroyed player')end}
    local e=setmetatable({DCS_STAGED_CONFIG={duration=6,token_high=0.123,token_low=0.456},
        DCSRECORDER={state='recording'},
        Unit={getByName=function(n)if n=='Observer' then return player else return unit end end},
        env={info=function(text)test.events[#test.events+1]=text end},
        timer={getTime=function()return test.now end,scheduleFunction=function(fn,a,t)test.jobs[#test.jobs+1]={fn=fn,a=a,t=t} end},
        trigger={action={outText=function()end,setUserFlag=function(name,value)test.flag=name;test.flag_value=value end}},
        missionCommands={addSubMenu=function()return {} end,addCommand=function(name,menu,fn)test.commands[name]=fn end}}, {__index=_G})
    local load=assert(loadfile(script));setfenv(load,e);load()
    function test.frame()
        for _,job in ipairs(test.jobs)do if job.t and test.now+1e-8>=job.t then job.t=job.fn(job.a,test.now) end end
    end
    function test.until_time(t)
        while test.now+0.00001<t do test.now=math.min(test.now+0.02,t);test.frame() end
    end
    function test.start()
        test.until_time(10)
        test.commands['Start playback (3-second countdown)']()
        local jobs=#test.jobs;test.commands['Start playback (3-second countdown)']();assert(#test.jobs==jobs,'duplicate start scheduled another countdown')
        test.until_time(13)
        assert(e.DCS_STAGED_PLAYBACK.phase=='release_requested' and test.flag=='DCS_RECORDED_RELEASE','countdown')
        test.until_time(13.45);test.exists=true;e.DCS_STAGED_PLAYBACK.released()
        assert(e.DCS_STAGED_PLAYBACK.release_time==test.now,'must use actual release clock')
    end
    test.e=e;return test
end
local good=session();good.start();good.status=0.25;good.until_time(13.49)
assert(good.e.DCS_STAGED_PLAYBACK.phase=='playing','controller handshake')
local paused_time=good.now;for i=1,1000 do good.frame()end
assert(good.now==paused_time and good.e.DCS_STAGED_PLAYBACK.phase=='playing','paused frames advanced state')
good.until_time(19.45);good.status=0.5;good.until_time(19.49)
assert(good.e.DCS_STAGED_PLAYBACK.phase=='complete' and good.removed==1,'native completion must remove only playback')
assert(good.e.DCSRECORDER.state=='recording','completion stopped independent recording')
good.until_time(20);assert(good.removed==1,'duplicate completion')
local bad=session();bad.start();bad.high=0.999;bad.status=0.25;bad.until_time(13.49)
assert(bad.e.DCS_STAGED_PLAYBACK.phase=='failed' and bad.removed==1,'mismatched tape accepted')
local fail=session();fail.start();fail.status=0.75;fail.until_time(13.49)
assert(fail.e.DCS_STAGED_PLAYBACK.phase=='failed','native failure accepted')
local missing=session();missing.start();missing.until_time(14.6)
assert(missing.e.DCS_STAGED_PLAYBACK.phase=='failed' and missing.removed==1,'no controller confirmation timeout')
local stale=session();stale.start();stale.status=0.25;stale.until_time(22)
assert(stale.e.DCS_STAGED_PLAYBACK.phase=='failed' and stale.removed==1,'lost completion watchdog')
local reset=session();assert(reset.e.DCS_STAGED_PLAYBACK.phase=='waiting','new mission state not reset')
print('PASS: delayed release, duplicate F10, controller handshake, pause clock, completion without ending recording, mismatch/native-error/timeouts, mission state reset. Mock lifecycle only.')
