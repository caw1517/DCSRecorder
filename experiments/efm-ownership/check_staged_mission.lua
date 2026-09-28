-- Mission lifecycle checks with an explicit fake controller, not a DCS runtime test.
local script=assert(arg[1])
local function session(exterior,smoke_events)
    local test={now=0,status=0,exists=false,removed=0,jobs={},commands={},events={},high=0.123,low=0.456}
    test.smoke_calls={};test.elapsed=0
    local unit={}
    function unit:isExist()return test.exists end
    function unit:destroy()test.exists=false;test.removed=test.removed+1 end
    function unit:getDrawArgumentValue(index)
        if index==999 then return test.status end
        if index==997 then return test.high end
        if index==998 then return test.low end
        if index==996 then return test.elapsed/1000 end
        return 0
    end
    function unit:getPosition()return {p={x=0,y=2000,z=0},x={x=1,y=0,z=0},y={x=0,y=1,z=0}} end
    function unit:getVelocity()return {x=220,y=0,z=0} end
    function unit:getController()return {setCommand=function(_,command)
        if test.smoke_error then error('fixture smoke command failed')end
        assert(command.id=='SMOKE_ON_OFF' and type(command.params.value)=='boolean')
        test.smoke_calls[#test.smoke_calls+1]=command.params.value
    end}end
    local player={isExist=function()return true end,getDrawArgumentValue=function()return 0 end,
        getPosition=unit.getPosition,getVelocity=unit.getVelocity,
        destroy=function()error('Playback destroyed player')end}
    local e=setmetatable({DCS_STAGED_CONFIG={duration=6,token_high=0.123,token_low=0.456,exterior=exterior,smoke_events=smoke_events},
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
local surfaces=session(1);surfaces.start();surfaces.status=0.25;surfaces.until_time(13.49)
assert(table.concat(surfaces.events,'\n'):find('DCS_PLAYBACK_EXTERIOR,playing',1,true),'missing later exterior observation')
surfaces.until_time(19.45);surfaces.status=0.5;surfaces.until_time(19.49)
assert(surfaces.removed==1 and surfaces.e.DCS_STAGED_PLAYBACK.phase=='complete','exterior completion failed')
local events={{time=0,on=false},{time=2.01,on=true},{time=4.01,on=false}}
local smoke=session(1,events);smoke.start()
assert(#smoke.smoke_calls==0,'smoke commanded before native handshake')
smoke.status=.25;smoke.until_time(13.49)
assert(#smoke.smoke_calls==1 and smoke.smoke_calls[1]==false,'initial smoke state missing')
smoke.elapsed=2;smoke.until_time(13.51);assert(#smoke.smoke_calls==1,'future smoke state applied early')
smoke.elapsed=2.02;smoke.until_time(13.53);assert(smoke.smoke_calls[2]==true,'recorded ON missing')
smoke.until_time(13.63);assert(#smoke.smoke_calls==2,'duplicate smoke commands at paused native clock')
smoke.elapsed=4.02;smoke.until_time(13.65);assert(smoke.smoke_calls[3]==false,'recorded OFF missing')
smoke.status=.5;smoke.until_time(13.67)
assert(smoke.e.DCS_STAGED_PLAYBACK.phase=='complete' and smoke.removed==1,'smoke broke completion')
local skip=session(1,events);skip.start();skip.status=.25;skip.elapsed=4.1;skip.until_time(13.49)
assert(#skip.smoke_calls==1 and skip.smoke_calls[1]==false,'delayed frame replayed stale burst')
local wrong=session(1,events);wrong.start();wrong.status=.25;wrong.high=.9;wrong.until_time(13.49)
assert(#wrong.smoke_calls==0 and wrong.removed==1,'smoke commanded for mismatched native tape')
local command_fail=session(1,events);command_fail.start();command_fail.status=.25;command_fail.smoke_error=true;command_fail.until_time(13.49)
assert(command_fail.e.DCS_STAGED_PLAYBACK.phase=='failed' and command_fail.removed==1,'smoke error not contained')
local reverse=session(1,events);reverse.start();reverse.status=.25;reverse.elapsed=1;reverse.until_time(13.49)
reverse.elapsed=.9;reverse.until_time(13.51)
assert(reverse.e.DCS_STAGED_PLAYBACK.phase=='failed','reversed smoke clock accepted')
print('PASS: measured smoke initialization, native-clock transitions, duplicate suppression, skipped bursts, mismatch, command/clock failure, normal completion')
print('PASS: delayed release, duplicate F10, controller handshake, pause clock, completion without ending recording, mismatch/native-error/timeouts, mission state reset. Mock lifecycle only.')
