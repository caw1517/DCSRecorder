-- Engine/motion position association at a declared capture hitch, with stubbed
-- Export and native reader. Usage: luae.exe test_engine_association.lua <engine_capture.lua>
local path=assert(arg[1])
local function run(dt,offset,accel)
    -- Motion row at t=100 s: 200 m/s along x. Export sees the player dt later,
    -- turning with `accel` m/s^2 laterally, plus an unexplained `offset` metres.
    local now=100+dt
    local env=setmetatable({},{__index=_G})
    env.Export={LoGetModelTime=function()return now end,LoGetPlayerPlaneId=function()return 7 end,
        LoGetSelfData=function()return {Name='FA-18C_hornet',Position={x=200*dt,y=2000,z=.5*accel*dt*dt+offset}}end,
        LoGetEngineInfo=function()return {RPM={left=99,right=98}}end}
    env.lfs={writedir=function()return ''end}
    env.package={loadlib=function()return function()return 'OK,.?AVwHumanAircraft@@,8,123,0.99,1.06,2.3,2.3,0.98,0.95,1.15,1.15,8101824,8101872,8101920' end end}
    local capture=assert(loadfile(path));setfenv(capture,env);capture=capture()
    local row={100,0,2000,0};for i=5,36 do row[i]=0 end;row[14]=200
    local active={capture_timing='frame-batch-v1',capture_build='2.9.30.28536',hitch_limit=1,engine_time=100-.02,
        note_hitch=function()end}
    return pcall(capture,table.concat(row,','),active)
end
assert(run(.6,0,88),'a 9 g turn over a 0.6 s hitch was refused')
assert(run(.01,0,0),'a normal frame was refused')
assert(not run(.01,2,0),'a 2 m error within a frame was accepted')
local ok,err=run(.6,100,0)
assert(not ok and tostring(err):find('association failed'),'another aircraft 100 m away was accepted: '..tostring(err))
print('PASS: hitch-delayed samples allow 9 g over the delay; frames stay at 0.5 m; another aircraft is refused')
