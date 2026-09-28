-- Synthetic emitter control test, NOT playback of captured smoke state.
local last,finished=nil,false
local function emit(s)env.info('DCSSMOKE_CONTROL,1,'..s)end
local function tell(s)trigger.action.outText('Smoke control test: '..s,5)end
local function tick()
    local state=DCS_STAGED_PLAYBACK
    if not state then return timer.getTime()+.1 end
    if state.phase=='complete' or state.phase=='failed' then
        if not finished then emit('END,'..state.phase);finished=true end
        return
    end
    if state.phase~='playing' then return timer.getTime()+.1 end
    local unit=Unit.getByName('StagedPlayback')
    if not unit or not unit:isExist() then emit('ERROR,aircraft_lost');return end
    local elapsed=1000*unit:getDrawArgumentValue(996)
    local on=(elapsed>=3 and elapsed<8) or (elapsed>=13 and elapsed<18) or (elapsed>=23 and elapsed<28)
    if last~=on then
        local ok,err=pcall(function()
            unit:getController():setCommand({id='SMOKE_ON_OFF',params={value=on}})
        end)
        if not ok then emit('ERROR,'..tostring(err):gsub('[\r\n,]',' '));tell('command failed; retain log');return end
        last=on
        emit(string.format('COMMAND,%.9f,%.9f,%s',timer.getTime(),elapsed,on and 'ON' or 'OFF'))
        tell('lead smoke requested '..(on and 'ON' or 'OFF')..'. Compare the visible trail.')
    end
    return timer.getTime()+.1
end
timer.scheduleFunction(tick,nil,timer.getTime()+.1)
emit('READY,synthetic_sequence_3_8_13_18_23_28')
