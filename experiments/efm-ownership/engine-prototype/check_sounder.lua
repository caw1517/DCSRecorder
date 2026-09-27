-- Verify actual probe dispatch/lifecycle; cannot establish audible DCS output.
local path=assert(arg[1])
local function run(mode)
    local calls={};local env={math=math,ipairs=ipairs,type=type,tostring=tostring,string=string}
    local function record(name,...)
        calls[#calls+1]={name,...}
    end
    env.ED_AudioAPI={ContextWorld=1,createHost=function()return 7 end,
        createSource=function(_,name)return name end}
    for _,name in ipairs({'setHostPosition','setHostOrientation','setHostVelocity','setHostTimestamp',
        'stopSource','setSourcePitch','setSourceGain','playSourceLooped'}) do
        env.ED_AudioAPI[name]=function(...)record(name,...)end
    end
    local script=assert(loadfile(path));setfenv(script,env);script()
    local params={timestamp=100,posx=1,posy=2,posz=3,orienta=0,orientb=0,orientc=0,orientd=1,velx=10,vely=20,velz=30}
    for _,t in ipairs({100,101,103,106,109,112,115}) do params.timestamp=t;env.onUpdate(params) end
    local played={}
    for _,call in ipairs(calls) do if call[1]=='playSourceLooped' then played[#played+1]=call[2] end end
    assert(#played==4 and played[1]:find('RPM1') and played[2]:find('Afterburner') and played[3]==played[1] and played[4]==played[2])
    local before=#calls
    if mode=='backward' then params.timestamp=90 elseif mode=='missing' then params.velx=nil else params.timestamp=0/0 end
    env.onUpdate(params)
    assert(#calls==before+2 and calls[#calls][1]=='stopSource')
    params.timestamp=120;params.velx=10;env.onUpdate(params);assert(#calls==before+2)
    print('PASS: four audio phases, terminal silence and fail-closed '..mode)
end
for _,mode in ipairs({'backward','missing','nan'}) do run(mode) end
