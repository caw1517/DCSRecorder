-- Smoke the new F10 flow independently of live rendering.
local script=assert(arg[1])
local function run(mode)
    local now,status,elapsed=0,0,0
    local exists,activated,released=true,false,false
    local commands={};local callback;local messages={}
    local unit={isExist=function()return exists end,destroy=function()exists=false end,
        getDrawArgumentValue=function(_,i)if i==999 then return status elseif i==998 then return elapsed/1000 else return 0.3 end end}
    local env={ipairs=ipairs,string=string,table=table,
        DCS_STATE_CONFIG={duration=48.9,markers={{time=1,segment='Hold closed'}}},
        Unit={getByName=function()return unit end},Group={getByName=function()return {} end},
        env={info=function(s)messages[#messages+1]=s end},
        timer={getTime=function()return now end,scheduleFunction=function(fn)callback=fn end},
        trigger={action={outText=function()end,activateGroup=function()activated=true end,setUserFlag=function()released=true end}},
        missionCommands={addSubMenu=function()return {}end,addCommand=function(name,_,fn)commands[name]=fn end}}
    local f=assert(loadfile(script));setfenv(f,env);f()
    commands['Start captured canopy sequence']();assert(activated and released and callback)
    now=0.1;status=0.25;elapsed=0.1;assert(callback())
    if mode=='complete' then
        now=49;elapsed=48.9;status=0.5;assert(callback() and exists)
        now=56.9;assert(callback() and exists)
        now=57;assert(not callback() and not exists)
    elseif mode=='failed' then status=0.75;assert(not callback() and not exists)
    elseif mode=='timeout' then status=0;now=11;assert(not callback() and not exists)
    elseif mode=='stop' then commands['Stop and remove test aircraft']();assert(not exists) end
    assert(messages[#messages]:find('DCSCANOPY_PLAYBACK,END,'))
    print('PASS: canopy playback F10/release/telemetry/removal '..mode)
end
for _,mode in ipairs({'complete','failed','timeout','stop'})do run(mode)end
