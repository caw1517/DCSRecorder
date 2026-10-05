-- Exercise a generated authored playback control script with stubbed mission APIs.
-- Usage: luae.exe check_authored_mission.lua <control.lua> <namespace> <lead name>
local path,namespace,lead_name=assert(arg[1]),assert(arg[2]),assert(arg[3])
local function run(mode)
    local now,queue,logs,notices,flags,commands=0,{},{},{},{},{}
    local status,removed=.125,false
    if mode=='native_never_ready' then status=0 end
    env={info=function(s)logs[#logs+1]=s end}
    trigger={action={outText=function(text)notices[#notices+1]=text end,setUserFlag=function(k,v)flags[k]=v end}}
    timer={getTime=function()return now end,scheduleFunction=function(fn,param,t)queue[#queue+1]={fn,param,t}end}
    local menus={}
    -- Only the owned top-level menu, and submenus nested inside it (diagnostic faults).
    missionCommands={addSubMenu=function(name,parent)assert(parent==nil or parent==1,'nested under an authored menu');menus[#menus+1]=name;return #menus end,
        addCommand=function(name,menu,fn)assert(menu and menu>=1 and menu<=#menus,'command outside the owned menu');commands[name]=fn end}
    local chunk=assert(loadfile(path))
    local function config()return _G[namespace..'_CONFIG']end
    local unit={}
    function unit:isExist()return not removed end
    function unit:destroy()removed=true end
    function unit:getPosition()return {p={x=0,y=0,z=0},x={x=1,y=0,z=0},y={x=0,y=1,z=0}}end
    function unit:getVelocity()return {x=0,y=0,z=0}end
    function unit:getDrawArgumentValue(i)
        if i==997 then return config().token_high end
        if i==998 then return config().token_low end
        if i==999 then return status end
        if i==996 then return 0 end
        return config().expected[i] or 0
    end
    function unit:getController()return {setCommand=function()end}end
    -- Ground takes also log playback-side contact and health.
    function unit:inAir()return false end
    function unit:getLife()return 20 end
    function unit:getLife0()return 20 end
    land={getHeight=function()return 0 end,getSurfaceType=function()return 5 end}
    Unit={getByName=function(name)return unit end}
    local before={};for k in pairs(_G)do before[k]=true end
    chunk()
    local s=_G[namespace]
    assert(s and config(),'generated control did not initialize its namespace')
    -- Ownership: only the allocated namespace's globals, flags and one top-level F10 menu.
    for k in pairs(_G)do
        assert(before[k] or k==namespace or k==namespace..'_CONFIG','generated control created unowned global '..tostring(k))
    end
    assert(menus[1]=='DCS Recorder playback' and (#menus==1 or (#menus==2 and config().faults and menus[2]=='Fault injection (developer)')),'unexpected F10 menus')
    local function advance(to)
        while #queue>0 do
            table.sort(queue,function(a,b)return a[3]<b[3]end)
            if queue[1][3]>to then break end
            local item=table.remove(queue,1);now=item[3]
            local next_time=item[1](item[2],now)
            if next_time then queue[#queue+1]={item[1],item[2],next_time}end
        end
        now=to
    end
    local function last()return notices[#notices] or ''end
    if mode=='no_checker' or mode=='native_never_ready' then
        advance(11)
        assert(s.phase=='failed' and removed and flags[namespace..'_CLEANUP']==1,'unverified release was not refused')
        local identity=last():find('Open the authored mission in Mission Editor',1,true)~=nil
        assert(identity==(mode=='no_checker'),'wrong refusal text for '..mode..': '..last())
        assert(last():find('DCS Recorder: ',1,true)==1)
        return flags
    end
    assert(s.arm('session_1',1) and s.phase=='waiting')
    commands['Start playback (3-second countdown)']()
    advance(4)
    assert(s.phase=='requested','countdown did not request release')
    if mode=='hook_refusal' then
        s.fail('stale_or_mismatched_request')
        assert(s.phase=='failed' and removed and last():find('scene saved with this take',1,true),'hook refusal lacked recovery text')
        return flags
    end
    assert(s.released('session_1',1) and s.phase=='starting')
    assert(not s.released('session_1',1),'second release accepted')
    return flags
end
local owned_flags={}
for _,mode in ipairs({'no_checker','native_never_ready','hook_refusal','success'})do
    for k in pairs(run(mode))do owned_flags[k]=true end
end
for k in pairs(owned_flags)do assert(tostring(k):find(namespace..'_',1,true)==1,'unowned flag '..tostring(k))end
print('PASS: authored control owns only its namespace globals, flags and F10 menu; refuses unverified release with recovery text and releases once when approved')
