-- THROWAWAY: same spatial host, contrasting a generated tone and stock samples.
local function report(s) print('[DCS-AUDIBILITY] '..s) end
local host=ED_AudioAPI.createHost(ED_AudioAPI.ContextWorld,'DCSRecorderAudibility')
local names={'Aircrafts/FA-18/F404GE_RPM1','DCSRecorderAudibility/Tone',
    'Aircrafts/FA-18/Afterburner','DCSRecorderAudibility/Afterburner'}
local labels={'stock_engine','control_tone','stock_afterburner','defined_afterburner','silent'}
local sources={}
for i,name in ipairs(names)do
    sources[i]=ED_AudioAPI.createSource(host,name)
    report('source '..labels[i]..' handle='..tostring(sources[i]))
end
local origin,last_time,last_phase,next_report
local failed=false
local function stop()for i=1,#names do if sources[i]then ED_AudioAPI.stopSource(sources[i])end end end
local function finite(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
function onUpdate(params)
    if failed then return end
    for _,key in ipairs({'timestamp','posx','posy','posz','orienta','orientb','orientc','orientd','velx','vely','velz'})do
        if not finite(params[key])then stop();failed=true;report('invalid_host_parameter '..key);return end
    end
    local now=params.timestamp
    if last_time and now<last_time then stop();failed=true;report('backward_clock');return end
    origin=origin or now;last_time=now
    ED_AudioAPI.setHostPosition(host,params.posx,params.posy,params.posz)
    ED_AudioAPI.setHostOrientation(host,params.orienta,params.orientb,params.orientc,params.orientd)
    ED_AudioAPI.setHostVelocity(host,params.velx,params.vely,params.velz)
    ED_AudioAPI.setHostTimestamp(host,now)
    local elapsed=now-origin
    local phase=elapsed>=12 and 5 or math.floor(elapsed/3)+1
    if phase~=last_phase then
        stop();last_phase=phase
        local selected=sources[phase]
        if selected then
            ED_AudioAPI.setSourcePitch(selected,1)
            ED_AudioAPI.setSourceGain(selected,0.4)
            ED_AudioAPI.playSourceLooped(selected)
        end
        report(string.format('phase=%s elapsed=%.6f selected=%s',labels[phase],elapsed,tostring(selected)))
    end
    if not next_report or now>=next_report then
        next_report=now+1
        local line=string.format('state elapsed=%.6f position=%.3f/%.3f/%.3f',elapsed,params.posx,params.posy,params.posz)
        for i=1,#names do
            local source=sources[i]
            local playing=source and 'query_unavailable' or 'source_unavailable'
            if source and type(ED_AudioAPI.isSourcePlaying)=='function'then playing=tostring(ED_AudioAPI.isSourcePlaying(source))end
            line=line..' '..labels[i]..'='..playing
        end
        for _,key in ipairs({'coreRPM_1','coreRPM_2','fanRPM_1','fanRPM_2','thrust_1','thrust_2','flame_1','flame_2'})do
            line=line..' '..key..'='..tostring(params[key])
        end
        report(line)
    end
end
