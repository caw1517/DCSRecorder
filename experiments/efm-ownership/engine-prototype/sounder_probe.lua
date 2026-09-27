-- THROWAWAY: test spatial audio control, not recorded engine fidelity.
-- Packaging supplies DCS_SOUND_LOG as a path inside this separate module.
local stream
if io and io.open and DCS_SOUND_LOG then stream=io.open(DCS_SOUND_LOG,'w') end
local function report(message)
    local line='[DCS-SOUNDER-PROBE] '..message
    if stream then stream:write(line..'\n');stream:flush() end
    if print then print(line) end
end
report('loaded')
local host=ED_AudioAPI.createHost(ED_AudioAPI.ContextWorld,'DCSRecorderSounderProbe')
local engine=ED_AudioAPI.createSource(host,'Aircrafts/FA-18/F404GE_RPM1')
local afterburner=ED_AudioAPI.createSource(host,'Aircrafts/FA-18/Afterburner')
report('sources engine='..tostring(engine)..' afterburner='..tostring(afterburner))
local origin,last_time,last_phase
local failed=false
local function stop()
    if engine then ED_AudioAPI.stopSource(engine) end
    if afterburner then ED_AudioAPI.stopSource(afterburner) end
end
local function finite(v) return type(v)=='number' and v==v and math.abs(v)<math.huge end
function onUpdate(params)
    if failed then return end
    for _,key in ipairs({'timestamp','posx','posy','posz','orienta','orientb','orientc','orientd','velx','vely','velz'}) do
        if not finite(params[key]) then
            stop();failed=true;report('invalid_host_parameter '..key);return
        end
    end
    local now=params.timestamp
    if last_time and now<last_time then
        stop();failed=true;report('backward_clock');return
    end
    origin=origin or now;last_time=now
    ED_AudioAPI.setHostPosition(host,params.posx,params.posy,params.posz)
    ED_AudioAPI.setHostOrientation(host,params.orienta,params.orientb,params.orientc,params.orientd)
    ED_AudioAPI.setHostVelocity(host,params.velx,params.vely,params.velz)
    ED_AudioAPI.setHostTimestamp(host,now)
    local elapsed=now-origin
    local phase=elapsed>=12 and 4 or math.floor(elapsed/3)
    if phase==last_phase then return end
    stop();last_phase=phase
    local selected=phase<4 and (phase%2==0 and engine or afterburner) or nil
    local name=phase>=4 and 'silent' or (phase%2==0 and 'engine' or 'afterburner')
    report(string.format('phase %d %s elapsed=%.6f timestamp=%.6f',phase,name,elapsed,now))
    if selected then
        ED_AudioAPI.setSourcePitch(selected,1)
        ED_AudioAPI.setSourceGain(selected,0.4)
        ED_AudioAPI.playSourceLooped(selected)
    elseif phase<4 then report('source_unavailable '..name) end
end
