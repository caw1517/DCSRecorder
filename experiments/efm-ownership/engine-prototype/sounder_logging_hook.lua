-- THROWAWAY: make the sounder's normally filtered diagnostics observable.
-- Separate outputs only; does not change the normal dcs.log output settings.
local ok,err=pcall(function()
    assert(log and log.set_output and log.ALL and log.TRACE and log.MESSAGE,'logging API unavailable')
    -- DCS 2.9.29 exposes ALL=255 but TRACE=256. Include that bit explicitly.
    local levels=log.ALL
    if math.floor(levels/log.TRACE)%2==0 then levels=levels+log.TRACE end
    log.set_output('dcs-recorder-sounder','SOUNDER',levels,log.MESSAGE)
    log.set_output('dcs-recorder-sound','SOUND',levels,log.MESSAGE)
    log.set_output('dcs-recorder-ed-sound','ED_SOUND',levels,log.MESSAGE)
    for _,facility in ipairs({'SOUNDER','SOUND','ED_SOUND'})do
        log.write(facility,log.TRACE,'[DCSRECORDER-TRACE-CHECK] TRACE enabled; mask='..levels)
    end
end)
if log and log.write then
    log.write('DCSRECORDER_SOUND_TRACE',ok and log.INFO or log.ERROR,
        ok and 'Dedicated SOUNDER/SOUND/ED_SOUND logs enabled including TRACE' or tostring(err))
end
