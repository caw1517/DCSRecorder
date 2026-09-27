local path=assert(arg[1])
local audibility=arg[2]=='--audibility'
for _,mode in ipairs({'complete','stop'}) do
    local callbacks,commands={},{}
    local exists,activated,released=true,false,false
    local env={ipairs=ipairs,timer={getTime=function()return 10 end,scheduleFunction=function(fn,value,when)callbacks[#callbacks+1]={fn,when,value}end},
        Unit={getByName=function()return {isExist=function()return exists end,destroy=function()exists=false end}end},
        Group={getByName=function()return {}end},
        env={info=function()end},
        trigger={action={outText=function()end,activateGroup=function()activated=true end,setUserFlag=function()released=true end}},
        missionCommands={addSubMenu=function()return {}end,addCommand=function(name,_,fn)commands[name]=fn end}}
    local script=assert(loadfile(path));setfenv(script,env);script()
    commands['Start sound test']();commands['Start sound test']()
    assert(activated and released and #callbacks==(audibility and 5 or 1) and callbacks[#callbacks][2]==25 and exists)
    if mode=='stop' then commands['Stop sound test']() else
        for _,callback in ipairs(callbacks)do callback[1](callback[3])end
    end
    assert(not exists)
    for _,callback in ipairs(callbacks)do callback[1](callback[3])end;assert(not exists)
    print('PASS: sound routing mission activation, single start and '..mode..' removal')
end
