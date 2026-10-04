-- Hold-only native control. No playback release is offered.
local c=assert(DCSR_HELD_CONFIG)
local started=timer.getTime()
local first_held,failed,finished,initial_smoke=nil,false,false,false
local function emit(text)env.info('DCSR_HELD '..text)end
local function notice(text)trigger.action.outText('Held-start test: '..text,20)end
local function remove_lead(reason)
    local u=Unit.getByName('StagedPlayback')
    if u and u:isExist() then u:destroy()end
    emit('REMOVED reason='..reason)
end
local function sample(name)
    local u=Unit.getByName(name)
    if not u or not u:isExist() then return false end
    local p,v=u:getPosition(),u:getVelocity()
    local values={}
    for _,a in ipairs({0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29})do
        values[#values+1]=string.format('%.9g',u:getDrawArgumentValue(a))
    end
    emit(string.format('SAMPLE,%s,%.6f,%d,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9g,%.9g,%s',
        name,timer.getTime(),u:getID(),p.p.x,p.p.y,p.p.z,p.x.x,p.x.y,p.x.z,p.y.x,p.y.y,p.y.z,
        v.x,v.y,v.z,u:getDrawArgumentValue(996)*1000,u:getDrawArgumentValue(999),table.concat(values,',')))
    return true
end
local function tick()
    if failed or finished then return end
    local now=timer.getTime()
    local lead=Unit.getByName('StagedPlayback')
    if not lead or not lead:isExist() then
        failed=true;notice('FAILED: playback aircraft missing. Exit normally.');emit('FAILED missing_aircraft');return
    end
    local status=lead:getDrawArgumentValue(999)
    local match=math.abs(lead:getDrawArgumentValue(997)-c.token_high)<1e-8 and
        math.abs(lead:getDrawArgumentValue(998)-c.token_low)<1e-8
    if (status~=0 and not match) or status==0.75 or (now-started>2 and status~=0.125) then
        failed=true;emit('FAILED controller_status='..status..' matched='..tostring(match))
        remove_lead('failure');notice('FAILED: hold controller did not confirm. Exit normally.');return
    end
    if match and status==0.125 then
        if not initial_smoke then
            if c.smoke~=nil then lead:getController():setCommand({id='SMOKE_ON_OFF',params={value=c.smoke}})end
            emit(string.format('INITIAL_SMOKE,%.6f,%s',now,tostring(c.smoke)))
            initial_smoke=true
        end
        if c.expected then
            for index,value in pairs(c.expected)do
                local actual=lead:getDrawArgumentValue(index)
                -- Float/log comparison precision, not a product fidelity tolerance.
                if actual~=actual or math.abs(actual-value)>0.000001 then
                    failed=true;emit(string.format('FAILED snapshot_arg=%d expected=%.12g actual=%.12g',index,value,actual))
                    remove_lead('snapshot_mismatch');notice('FAILED: initial state was not retained. Exit normally.');return
                end
            end
        end
        if not first_held then first_held=now;emit('HELD');notice('Inspect the held lead for 30 seconds. Do not toggle pause.') end
    end
    sample('Observer');sample('StagedPlayback');sample('SceneWitness')
    if first_held and now-first_held>=30 then
        finished=true;emit('OBSERVATION_COMPLETE');notice('30-second observation complete. Exit normally; report drift, flicker, or sound changes.')
        -- Keep the measured hold visible until exit. A bounded 90-second guard
        -- cleans up the diagnostic object if the user leaves this test running.
        timer.scheduleFunction(function()remove_lead('diagnostic_time_limit')end,nil,now+60)
        return
    end
    return now+0.1
end
local function checked_tick()
    local ok,next_time=pcall(tick)
    if not ok then failed=true;emit('FAILED script='..tostring(next_time));remove_lead('script_failure');notice('FAILED: retain the log and exit.');return end
    return next_time
end
emit('INITIALIZED')
notice('Player Active Pause requested. Watch the lead ahead; the scene witness should continue flying. No release is offered.')
-- Try the complete snapshot immediately at mission startup. If the native
-- object is not ready yet, the first scheduled tick retries without claiming
-- that a command or a frame has already been initialized.
checked_tick()
if not failed and not finished then timer.scheduleFunction(checked_tick,nil,started+0.02)end
