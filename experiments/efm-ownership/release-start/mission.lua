-- Bounded airborne integration. The installed user hook commits the native
-- one-shot latch and dispatches Active Pause release in the same hook callback.
local c=assert(DCSR_RELEASE_CONFIG)
local s={phase='preparing',held=true,started=timer.getTime(),smoke_index=0,last_replay=0}
DCSR_RELEASE=s
local function emit(text)env.info('DCSR_RELEASE '..text)end
local function notice(text)trigger.action.outText('Release test: '..text,15)end
local function flag(name,value)trigger.action.setUserFlag(name,value)end
local function lead()local u=Unit.getByName('StagedPlayback');return u and u:isExist() and u or nil end
local function matched(u)
    return math.abs(u:getDrawArgumentValue(997)-c.token_high)<1e-8 and
        math.abs(u:getDrawArgumentValue(998)-c.token_low)<1e-8
end
local function initial(u)
    if not matched(u) or u:getDrawArgumentValue(999)~=.125 or u:getDrawArgumentValue(996)~=0 then return false end
    for index,value in pairs(c.expected)do
        local actual=u:getDrawArgumentValue(index)
        if actual~=actual or math.abs(actual-value)>0.000001 then return false end
    end
    return true
end
function s.fail(reason)
    if s.phase=='failed' or s.phase=='complete' then return end
    s.phase='failed';flag('DCSR_RELEASE_PENDING',0)
    local u=lead();if u then u:destroy()end
    if s.held then flag('DCSR_RELEASE_CLEANUP',1)end
    emit('FAILED,'..tostring(reason));notice('FAILED: '..tostring(reason)..'. Exit normally and retain logs.')
end
function s.cleaned()s.held=false;emit('HOLD_CLEANED')end
function s.arm(session,generation)
    if s.phase~='preparing' and s.phase~='waiting' then return false end
    local u=lead()
    if not u or not initial(u) or type(session)~='string' or not session:match('^[%w_]+$') or
        type(generation)~='number' or generation<1 then return false end
    s.session,s.generation=session,generation
    if s.phase~='waiting' then
        s.phase='waiting';emit('READY,'..session..','..generation)
        notice('Ready. Inspect the held lead, then F10 > DCS Recorder release test > Start playback. Do not toggle Active Pause.')
    end
    return true
end
function s.released(session,generation)
    if s.phase~='requested' or s.session~=session or s.generation~=generation then
        s.fail('unexpected_release_ack');return false
    end
    s.held=false;flag('DCSR_RELEASE_PENDING',0)
    s.phase='starting';s.release_time=timer.getTime()
    emit(string.format('PLAYER_RELEASED,%s,%d,%.9f',session,generation,s.release_time))
    notice('Released. Watch first movement and smoke, then let the short recording finish.')
    return true
end
local function sample(name)
    local u=Unit.getByName(name);if not u or not u:isExist() then return end
    local p,v=u:getPosition(),u:getVelocity();local values={}
    for _,a in ipairs({0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29})do
        values[#values+1]=string.format('%.9g',u:getDrawArgumentValue(a))
    end
    emit(string.format('SAMPLE,%s,%s,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9g,%s',
        s.phase,name,timer.getTime(),p.p.x,p.p.y,p.p.z,p.x.x,p.x.y,p.x.z,p.y.x,p.y.y,p.y.z,
        v.x,v.y,v.z,1000*u:getDrawArgumentValue(996),u:getDrawArgumentValue(999),table.concat(values,',')))
end
local function smoke(u)
    local elapsed=1000*u:getDrawArgumentValue(996)
    assert(elapsed==elapsed and elapsed>=s.last_replay and elapsed<=c.duration+.1,'invalid_replay_clock')
    s.last_replay=elapsed
    while c.smoke_events[s.smoke_index+1] and c.smoke_events[s.smoke_index+1].time<=elapsed do
        s.smoke_index=s.smoke_index+1
    end
    local desired=assert(c.smoke_events[s.smoke_index])
    if desired.on~=s.smoke_on then
        u:getController():setCommand({id='SMOKE_ON_OFF',params={value=desired.on}})
        s.smoke_on=desired.on
        emit(string.format('SMOKE,%.9f,%.9f,%d',timer.getTime(),elapsed,desired.on and 1 or 0))
    end
end
local function tick()
    if s.phase=='failed' or s.phase=='complete' then return end
    local now=timer.getTime();local u=lead()
    if not u then s.fail('missing_aircraft');return end
    local status=u:getDrawArgumentValue(999)
    if status~=0 and (not matched(u) or status==.75) then s.fail('native_readiness_lost');return end
    if s.phase=='preparing' then
        if matched(u) and status==.125 then
            if not initial(u) then s.fail('snapshot_mismatch');return end
            smoke(u)
        end
        if now-s.started>10 then s.fail('bridge_or_native_readiness_timeout');return end
    elseif s.phase=='waiting' or s.phase=='countdown' then
        if not initial(u) then s.fail('initial_state_not_retained');return end
        smoke(u)
    elseif s.phase=='requested' then
        if now-s.request_time>1 then s.fail('release_ack_timeout');return end
    elseif s.phase=='starting' or s.phase=='playing' then
        if status==.25 then
            if s.phase=='starting' then s.phase='playing';emit(string.format('NATIVE_RUNNING,%.9f,%.9f',now,1000*u:getDrawArgumentValue(996)))end
            smoke(u)
        elseif status==.5 and s.phase=='playing' then
            smoke(u);sample('Observer');sample('StagedPlayback');u:destroy();s.phase='complete'
            emit('COMPLETE');notice('Recording ended. Report first movement, smoke onset, and any jump or sound change. Exit normally.');return
        elseif s.phase=='playing' or now-s.release_time>1 then s.fail('native_release_not_confirmed');return end
        if now-s.release_time>c.duration+2 then s.fail('completion_timeout');return end
    end
    sample('Observer');sample('StagedPlayback');sample('SceneWitness')
    return now+.02
end
local function checked_tick()
    local ok,next_time=pcall(tick)
    if not ok then s.fail(next_time);return end
    return next_time
end
local function start()
    if s.phase~='waiting' then emit('START_REFUSED,'..s.phase);notice('Start unavailable: '..s.phase..'.');return end
    local u=lead();if not u or not initial(u) then s.fail('not_ready');return end
    s.phase='countdown';s.countdown_time=timer.getTime();emit(string.format('COUNTDOWN,%.9f',s.countdown_time))
    notice('Starting in 3. Do not toggle Active Pause.')
    local remaining=3
    timer.scheduleFunction(function()
        if s.phase~='countdown' then return end
        remaining=remaining-1
        if remaining>0 then notice('Starting in '..remaining..'.');return timer.getTime()+1 end
        local current=lead()
        if not current or not initial(current) then s.fail('not_ready_at_release');return end
        s.phase='requested';s.request_time=timer.getTime();flag('DCSR_RELEASE_PENDING',1)
        emit(string.format('REQUEST,%s,%d,%.9f',s.session,s.generation,s.request_time))
    end,nil,s.countdown_time+1)
end
local menu=missionCommands.addSubMenu('DCS Recorder release test')
missionCommands.addCommand('Start playback (3-second countdown)',menu,start)
missionCommands.addCommand('Show status',menu,function()notice(s.phase)end)
flag('DCSR_RELEASE_PENDING',0);flag('DCSR_RELEASE_CLEANUP',0)
emit('INITIALIZED');notice('Player held. Waiting for the complete snapshot and release bridge.')
checked_tick()
if s.phase~='failed' then timer.scheduleFunction(checked_tick,nil,timer.getTime()+.02)end
