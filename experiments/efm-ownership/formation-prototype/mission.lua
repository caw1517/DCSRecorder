-- Formation prototype: N playback aircraft, each owning its own recorded flight,
-- released together. Generalizes release-start/mission.lua; a failed or removed
-- aircraft is removed alone and every other aircraft keeps playing.
local c=assert(DCSR_FORMATION_CONFIG)
local s={phase='preparing',held=true,started=timer.getTime(),positions={},not_ready={}}
DCSR_FORMATION=s
local function emit(text)env.info('DCSR_FORMATION '..text)end
local function notice(text)trigger.action.outText('DCS Recorder formation: '..text,15)end
local function flag(name,value)trigger.action.setUserFlag(name,value)end
for i,cfg in ipairs(c.positions)do
    s.positions[i]={cfg=cfg,name=cfg.name,phase='preparing',smoke_index=0,last_replay=0}
end
local function unit(p)local u=Unit.getByName(p.name);return u and u:isExist() and u or nil end
-- Recording against the formation: the recorder (injected beside this script)
-- begins at the release on the shared epoch; events carry the replay time.
local function event(kind,p)
    if not c.record or not p.cfg.association then return end
    if kind=='not_ready' then s.not_ready[#s.not_ready+1]=p.cfg.association;return end
    if s.recording then DCSR_FORMATION_REC.event(kind,p.cfg.association,timer.getTime()-s.epoch)end
end
local function replay(p)return (p.cfg.replay_scale or 1000)end
local function matched(p,u)
    return math.abs(u:getDrawArgumentValue(997)-p.cfg.token_high)<1e-8 and
        math.abs(u:getDrawArgumentValue(998)-p.cfg.token_low)<1e-8
end
local function initial(p,u)
    if not matched(p,u) or u:getDrawArgumentValue(999)~=.125 or u:getDrawArgumentValue(996)~=0 then return false end
    for index,value in pairs(p.cfg.expected)do
        local actual=u:getDrawArgumentValue(index)
        if actual~=actual or math.abs(actual-value)>0.000001 then return false end
    end
    return true
end
local function ended(p)return p.phase=='failed' or p.phase=='complete' end
local function live()
    local out={};for _,p in ipairs(s.positions)do if not ended(p)then out[#out+1]=p end end;return out
end
-- Owned smoke is switched off before the aircraft is removed.
local function remove(p,u)
    if p.smoke_on then
        pcall(function()u:getController():setCommand({id='SMOKE_ON_OFF',params={value=false}})end)
        p.smoke_on=false;emit(string.format('SMOKE_REMOVED,%s,%.9f',p.name,timer.getTime()))
    end
    u:destroy();emit('AIRCRAFT_REMOVED,'..p.name)
end
function s.cleaned()s.held=false;emit('HOLD_CLEANED')end
function s.fail(reason)
    if s.phase=='failed' then return end
    s.phase='failed';flag('DCSR_FORMATION_PENDING',0)
    for _,p in ipairs(s.positions)do
        if not ended(p)then p.phase='failed';local u=unit(p);if u then remove(p,u)end end
    end
    if s.held then flag('DCSR_FORMATION_CLEANUP',1)end
    emit('FAILED,'..tostring(reason))
    notice('FAILED: '..tostring(reason)..'. Playback aircraft were removed; the mission continues. Logs were retained.')
end
-- One aircraft fails alone: it is removed and the others continue.
function s.fail_position(name,reason)
    for _,p in ipairs(s.positions)do
        if p.name==name and not ended(p)then
            p.phase='failed';local u=unit(p);if u then remove(p,u)end
            event(s.held and 'not_ready' or 'failed',p)
            emit('POSITION_FAILED,'..p.name..','..tostring(reason))
            notice(p.name..' removed: '..tostring(reason)..'. Other aircraft continue.')
        end
    end
    if #live()==0 and s.phase~='done' then
        if s.held then s.fail('no_playback_aircraft')
        else s.phase='done';emit('DONE');notice('No playback aircraft remain; the mission continues.') end
    end
end
local function all_ready()
    local remaining=live()
    if #remaining==0 then return false end
    for _,p in ipairs(remaining)do
        local u=unit(p);if p.phase~='ready' or not u or not initial(p,u)then return false end
    end
    return true
end
function s.arm(session,generation)
    if s.phase~='preparing' and s.phase~='waiting' then return false end
    if not all_ready() or type(session)~='string' or not session:match('^[%w_]+$') or
        type(generation)~='number' or generation<1 then return false end
    s.session,s.generation=session,generation
    if s.phase~='waiting' then
        s.phase='waiting'
        local names={};for _,p in ipairs(live())do names[#names+1]=p.name end
        emit('READY,'..session..','..generation..','..table.concat(names,'|'))
        notice('Ready: '..table.concat(names,', ')..'. F10 > DCS Recorder formation > Start playback. Do not toggle Active Pause.')
    end
    return true
end
function s.released(session,generation,epoch)
    if s.phase~='requested' or s.session~=session or s.generation~=generation or type(epoch)~='number' then
        s.fail('unexpected_release_ack');return false
    end
    s.held=false;flag('DCSR_FORMATION_PENDING',0)
    s.phase='running';s.release_time=timer.getTime();s.epoch=epoch
    emit(string.format('PLAYER_RELEASED,%s,%d,%.9f,%.9f',session,generation,s.release_time,epoch))
    notice('Released. Each aircraft flies its own recorded flight.')
    if c.record then
        s.recording=DCSR_FORMATION_REC.begin_formation(string.format('formation_id,%s\nformation_version,%d\nformation_epoch,%.9f\n',
            c.record.formation,c.record.version,epoch))
        emit(string.format('RECORDING,%s,%.9f',s.recording and 'started' or 'refused',epoch))
        if s.recording then for _,association in ipairs(s.not_ready)do DCSR_FORMATION_REC.event('not_ready',association)end end
    end
    return true
end
local function sample(name,p)
    local u=Unit.getByName(name);if not u or not u:isExist() then return end
    local pos,v=u:getPosition(),u:getVelocity()
    local elapsed,status='',''
    if p then elapsed=string.format('%.9f',replay(p)*u:getDrawArgumentValue(996));status=string.format('%.9g',u:getDrawArgumentValue(999))end
    emit(string.format('SAMPLE,%s,%s,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%s,%s',
        p and p.phase or s.phase,name,timer.getTime(),pos.p.x,pos.p.y,pos.p.z,pos.x.x,pos.x.y,pos.x.z,pos.y.x,pos.y.y,pos.y.z,
        v.x,v.y,v.z,elapsed,status))
end
local function smoke(p,u)
    local elapsed=replay(p)*u:getDrawArgumentValue(996)
    assert(elapsed==elapsed and elapsed>=p.last_replay and elapsed<=p.cfg.duration+.1,'invalid_replay_clock')
    p.last_replay=elapsed
    local events=p.cfg.smoke_events
    while events[p.smoke_index+1] and events[p.smoke_index+1].time<=elapsed do p.smoke_index=p.smoke_index+1 end
    local desired=assert(events[p.smoke_index])
    if desired.on~=p.smoke_on then
        u:getController():setCommand({id='SMOKE_ON_OFF',params={value=desired.on}})
        p.smoke_on=desired.on
        emit(string.format('SMOKE,%s,%.9f,%.9f,%d',p.name,timer.getTime(),elapsed,desired.on and 1 or 0))
    end
end
-- One position's step; returns a failure reason or nil.
local function step(p,now)
    local u=unit(p)
    if not u then return 'missing_aircraft' end
    local status=u:getDrawArgumentValue(999)
    if status~=0 and (not matched(p,u) or status==.75) then return 'native_readiness_lost' end
    if s.phase=='preparing' or s.phase=='waiting' or s.phase=='countdown' or s.phase=='requested' then
        if p.phase=='preparing' then
            if matched(p,u) and status==.125 then
                if not initial(p,u) then return 'snapshot_mismatch' end
                p.phase='ready';emit('POSITION_READY,'..p.name)
            elseif now-s.started>15 then return 'assignment_or_readiness_timeout' end
        elseif p.phase=='ready' then
            if not initial(p,u) then return 'initial_state_not_retained' end
            smoke(p,u)
        end
        return
    end
    -- Released: each aircraft follows its own native status.
    if p.phase=='ready' or p.phase=='playing' then
        if status==.25 then
            if p.phase=='ready' then p.phase='playing';emit(string.format('NATIVE_RUNNING,%s,%.9f,%.9f',p.name,now,replay(p)*u:getDrawArgumentValue(996)))end
            smoke(p,u)
        elseif status==.5 and p.phase=='playing' then
            smoke(p,u);sample(p.name,p);remove(p,u);p.phase='complete';event('ended',p);emit('COMPLETE,'..p.name)
            notice(p.name..': recording ended; aircraft removed.')
        elseif status==.375 and p.phase=='playing' then
            smoke(p,u)
            if p.cfg.parked then
                p.phase='parked';p.parked_time=now;event('ended',p);emit(string.format('PARKED,%s,%.9f',p.name,now))
                notice(p.name..': recording ended; parked with engines running.')
            else
                sample(p.name,p);remove(p,u);p.phase='complete';event('ended',p);emit('COMPLETE,'..p.name..',not_parked')
            end
        elseif p.phase=='playing' or now-s.release_time>1 then return 'native_release_not_confirmed' end
        if p.phase=='playing' and now-s.release_time>p.cfg.duration+2 then return 'completion_timeout' end
    elseif p.phase=='parked' then
        if status~=.375 then return 'parked_hold_lost' end
        smoke(p,u)
    end
end
local function tick()
    if s.phase=='failed' or s.phase=='done' then return end
    local now=timer.getTime()
    if s.phase=='requested' and now-s.request_time>1 then s.fail('release_ack_timeout');return end
    for _,p in ipairs(s.positions)do
        if not ended(p)then
            local ok,reason=pcall(step,p,now)
            if not ok or reason then s.fail_position(p.name,ok and reason or ('error_'..tostring(reason)))end
        end
    end
    if s.phase=='failed' or s.phase=='done' then return end
    if s.phase=='preparing' and now-s.started>20 then s.fail('bridge_or_native_readiness_timeout');return end
    if s.phase=='running' then
        local active=false
        for _,p in ipairs(s.positions)do if p.phase=='playing' or p.phase=='ready' then active=true end end
        if not active then
            local parked=false;for _,p in ipairs(s.positions)do if p.phase=='parked' then parked=true end end
            if not parked then s.phase='done';emit('DONE');return end
        end
    end
    sample(c.player)
    for _,p in ipairs(s.positions)do if not ended(p)then sample(p.name,p)end end
    return now+.02
end
local function checked_tick()
    local ok,next_time=pcall(tick)
    if not ok then s.fail(next_time);return end
    return next_time
end
local function start()
    if s.phase~='waiting' then emit('START_REFUSED,'..s.phase);notice('Start unavailable: '..s.phase..'.');return end
    if not all_ready() then s.fail('not_ready');return end
    s.phase='countdown';s.countdown_time=timer.getTime();emit(string.format('COUNTDOWN,%.9f',s.countdown_time))
    notice('Starting in 3. Do not toggle Active Pause.')
    local remaining=3
    timer.scheduleFunction(function()
        if s.phase~='countdown' then return end
        remaining=remaining-1
        if remaining>0 then notice('Starting in '..remaining..'.');return timer.getTime()+1 end
        if not all_ready() then s.fail('not_ready_at_release');return end
        s.phase='requested';s.request_time=timer.getTime();flag('DCSR_FORMATION_PENDING',1)
        emit(string.format('REQUEST,%s,%d,%.9f',s.session,s.generation,s.request_time))
    end,nil,s.countdown_time+1)
end
local menu=missionCommands.addSubMenu('DCS Recorder formation')
missionCommands.addCommand('Start playback (3-second countdown)',menu,start)
missionCommands.addCommand('Show status',menu,function()
    local parts={s.phase};for _,p in ipairs(s.positions)do parts[#parts+1]=p.name..'='..p.phase end
    notice(table.concat(parts,'; '))
end)
-- Isolation proof (developer prototype): remove one aircraft by native abort or
-- by destroying it; the others must keep flying their own recorded flights.
local faults=missionCommands.addSubMenu('Remove one aircraft (developer)',menu)
for _,p in ipairs(s.positions)do
    missionCommands.addCommand('Native abort: '..p.name,faults,function()
        emit(string.format('ABORT_REQUEST,%s,%.9f',p.name,timer.getTime()))
    end)
    missionCommands.addCommand('Destroy: '..p.name,faults,function()
        local u=unit(p);emit(string.format('FAULT,destroy,%s,%.9f',p.name,timer.getTime()))
        if u then u:destroy()end
    end)
end
flag('DCSR_FORMATION_PENDING',0);flag('DCSR_FORMATION_CLEANUP',0)
emit('INITIALIZED,'..#s.positions);notice('Player held. Waiting for every playback aircraft to receive its recorded flight.')
checked_tick()
if s.phase~='failed' then timer.scheduleFunction(checked_tick,nil,timer.getTime()+.02)end
