-- Single-player prototype. No Export.lua chaining or core sandbox changes.
local hooks={}
local sim=Sim or DCS
local file,partial,complete,take,next_sample,last_time,last_flush,rows
local failed=false
local root=lfs.writedir()..'DCSRecorder/'
local directory=root..'recordings/'
local function notice(message)
    log.write('DCS_RECORDER',log.INFO,message)
    if type(a_do_script)=='function' then
        pcall(a_do_script,'trigger.action.outText('..string.format('%q',message)..',15)')
    end
end
local function finish(reason)
    if not file then return end
    file:write('END,',reason,',',rows,'\n');file:flush();file:close();file=nil
    local ok,err=os.rename(partial,complete)
    if ok then notice('Recording saved: '..complete)
    else notice('Recording rename failed; partial file retained: '..tostring(err)) end
end
local function abort(message)
    failed=true
    if file then file:flush();file:close();file=nil end
    notice('Recording stopped with error; partial file retained: '..message)
end
local function begin(number)
    local ok,metadata=pcall(a_do_script,'return DCSRECORDER and DCSRECORDER.metadata()')
    if not ok or type(metadata)~='string' then abort('aircraft metadata unavailable');return false end
    lfs.mkdir(root);lfs.mkdir(directory)
    local prefix=directory..os.date('%Y%m%d-%H%M%S')..'-take-'..number
    local suffix=0
    repeat
        complete=prefix..'-'..suffix..'.csv';partial=prefix..'-'..suffix..'.partial.csv';suffix=suffix+1
    until not lfs.attributes(complete) and not lfs.attributes(partial)
    local err;file,err=io.open(partial,'wb')
    if not file then abort(tostring(err));return false end
    file:write(metadata,'t,x,y,z,fx,fy,fz,ux,uy,uz,rx,ry,rz,vx,vy,vz,speedbrake,rpm_left,rpm_right\n')
    take=number;last_time=nil;rows=0;last_flush=0
    notice('Recording take '..number..' to Saved Games/DCS/DCSRecorder/recordings')
    return true
end
function hooks.onSimulationStart()
    finish('mission_restart');take=nil;next_sample=0;failed=false
end
function hooks.onSimulationFrame()
    local name=sim.getMissionFilename() or ''
    if not name:find('EFM%-Probe%-Hornet%-record%.miz$') or failed then return end
    local now=sim.getModelTime()
    if now<next_sample then return end
    next_sample=now+0.019 -- at most one read per frame, approximately 50 Hz
    if type(a_do_script)~='function' then abort('documented mission bridge unavailable');return end
    local ok,payload=pcall(a_do_script,'return DCSRECORDER and DCSRECORDER.sample()')
    if not ok then abort(tostring(payload));return end
    if payload==nil then return end -- mission startup script has not run yet
    if payload=='IDLE' or payload=='LOST' then finish(payload=='LOST' and 'aircraft_lost' or 'user_stop');return end
    if payload=='INVALID' then abort('non-finite flight state');return end
    if type(payload)~='string' then abort('invalid mission response');return end
    local number,data=payload:match('^DATA,(%d+),(.+)$')
    if not number then abort('malformed flight sample');return end
    if take~=number or not file then
        finish('new_take');if not begin(number) then return end
    end
    local timestamp=tonumber(data:match('^([^,]+),'))
    if not timestamp or (last_time and timestamp<last_time) then abort('flight clock reset');return end
    if last_time and timestamp==last_time then return end -- paused/duplicate frame
    local left,right='',''
    if Export and Export.LoGetEngineInfo then
        local good,engine=pcall(Export.LoGetEngineInfo)
        if good and engine and engine.RPM then
            if type(engine.RPM.left)=='number' then left=string.format('%.6g',engine.RPM.left) end
            if type(engine.RPM.right)=='number' then right=string.format('%.6g',engine.RPM.right) end
        end
    end
    local written,err=file:write(data,',',left,',',right,'\n')
    if not written then abort(tostring(err));return end
    rows=rows+1;last_time=timestamp
    if now-last_flush>=1 then file:flush();last_flush=now end
end
function hooks.onSimulationStop() finish('mission_stop') end
sim.setUserCallbacks(hooks)
