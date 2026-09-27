-- Drive the actual mission script through completion and failure/stop paths.
local script=assert(arg[1])
local parameters=arg[2]=='--parameters'
local start_command=parameters and 'Start recorded engine test' or 'Start recorded RPM test'
local stop_command=parameters and 'Stop engine test' or 'Stop RPM test'
local prefix=parameters and 'DCS_PARAMETER_MISSION' or 'DCS_RPM_MISSION'
local function scenario(mode,reason)
    local now,elapsed,status=0,0,0
    local exists,removed,scheduled=false,0,nil
    local commands,logs={},{ }
    local unit={isExist=function()return exists end,
        destroy=function()exists=false;removed=removed+1 end,
        getDrawArgumentValue=function(_,n)return n==998 and elapsed/1000 or status end}
    Unit={getByName=function()return exists and unit or nil end}
    Group={getByName=function()return {}end}
    timer={getTime=function()return now end,scheduleFunction=function(fn)scheduled=fn end}
    trigger={action={outText=function()end,activateGroup=function()exists=true end,setUserFlag=function(n,v)assert(n=='DCS_STATE_RELEASE' and v==1)end}}
    env={info=function(s)logs[#logs+1]=s end}
    missionCommands={addSubMenu=function()return {}end,addCommand=function(n,_,fn)commands[n]=fn end}
    DCS_STATE_CONFIG={duration=48.9,markers={{time=0,segment='both_idle'},{time=6,segment='both_military'}}}
    assert(loadfile(script))()
    commands[start_command]();assert(scheduled and exists)
    for i=1,1300 do
        now=i*0.05;elapsed=now
        status=elapsed<51.9 and 0.25 or 0.5
        if mode=='guard' then status=0.75 end
        if mode=='handshake' then status=0 end
        if mode=='stalled' then elapsed=0 end
        if mode=='stop' and now>=1 then commands[stop_command]()end
        if not scheduled()then break end
    end
    assert(removed==1 and not exists,'lead must be removed exactly once: '..mode)
    assert(logs[#logs]:find(prefix..',END,'..reason..',',1,true),'wrong termination: '..mode)
    commands[start_command]();assert(not exists,'second activation allowed')
    assert(scheduled()==nil,'timer remains active')
end
scenario('complete','complete')
scenario('guard','native_guard_failed')
scenario('handshake','no_handshake')
scenario('stalled','timeout')
scenario('stop','user_stop')
print('PASS: RPM mission completion, guard rejection, handshake timeout, stalled clock, manual stop and one-shot activation')
