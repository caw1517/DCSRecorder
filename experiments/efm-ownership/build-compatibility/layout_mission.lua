-- Observes normal AI motion for comparison with read-only native field reads.
local started=timer.getTime()
env.info('DCSR_LAYOUT,STARTED')
trigger.action.outText('Read-only aircraft layout check. Let the mission run for 20 seconds, then exit DCS. The lead flies normally; no hold or playback runs.',20)
timer.scheduleFunction(function(_,now)
    local u=Unit.getByName('Probe')
    if not u or not u:isExist() then env.info('DCSR_LAYOUT,MISSING');return end
    local p=u:getPoint();local v=u:getVelocity()
    env.info(string.format('DCSR_LAYOUT,SAMPLE,%.6f,%s,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f',
        now,tostring(u:getID()),p.x,p.y,p.z,v.x,v.y,v.z))
    if now-started>=20 then
        env.info('DCSR_LAYOUT,COMPLETE')
        trigger.action.outText('Layout observation complete. Exit DCS normally.',30)
        return
    end
    return now+0.1
end,nil,started+0.1)
