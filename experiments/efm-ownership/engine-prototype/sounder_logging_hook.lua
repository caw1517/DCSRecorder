-- THROWAWAY: make the sounder's normally filtered diagnostics observable.
-- Separate outputs only; does not change the normal dcs.log output settings.
local ok,err=pcall(function()
    assert(log and log.set_output and log.ALL and log.MESSAGE,'logging API unavailable')
    log.set_output('dcs-recorder-sounder','SOUNDER',log.ALL,log.MESSAGE)
    log.set_output('dcs-recorder-sound','SOUND',log.ALL,log.MESSAGE)
    log.set_output('dcs-recorder-ed-sound','ED_SOUND',log.ALL,log.MESSAGE)
end)
if log and log.write then
    log.write('DCSRECORDER_SOUND_TRACE',ok and log.INFO or log.ERROR,
        ok and 'Dedicated SOUNDER/SOUND/ED_SOUND logs enabled' or tostring(err))
end
