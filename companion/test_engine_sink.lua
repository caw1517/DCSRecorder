-- Integrated save-hook + native sampler fixture. No real aircraft or native reads.
local sink_path,engine_path,root,mode=assert(arg[1]),assert(arg[2]),assert(arg[3]),arg[4] or 'normal'
root=root:gsub('\\','/')..'/'
local callbacks,now,id,history=nil,10,16777472,{}
local env=setmetatable({}, {__index=_G})
env.lfs={writedir=function()return root end,mkdir=function()return true end,
    attributes=function(path)local f=io.open(path,'rb');if f then f:close();return {}end end}
env.log={INFO=1,write=function()end}
env.DCS={setUserCallbacks=function(h)callbacks=h end,getLogHistory=function(index)
    local out={};for i=index+1,#history do out[#out+1]={message=history[i]}end;return out,#history
end}
env.Export={LoGetModelTime=function()return now end,
    LoGetPlayerPlaneId=function()return id end,
    LoGetSelfData=function()return {Name='FA-18C_hornet',Position={x=(now-10)*220,y=2000,z=0}}end,
    LoGetEngineInfo=function()return {RPM={left=99,right=98}}end}
env.package={loadlib=function()
    if mode=='missing' then return nil,'missing helper' end
    return function()return 'OK,.?AVwHumanAircraft@@,8,123,0.99,1.06,2.3,'..
        (mode=='unequal' and '2.1' or '2.3')..',0.98,0.95,1.15,1.15,8101824,8101872,8101920'end
end}
env.loadfile=function(path)
    assert(path==root..'Scripts/DCSRecorderEngineCapture/engine_capture.lua')
    local f=assert(loadfile(engine_path));setfenv(f,env);return f
end
local hook=assert(loadfile(sink_path));setfenv(hook,env);hook()
local function emit(text)
    history[#history+1]='DCSREC_LOG,1,'..text;callbacks.onSimulationFrame()
end
local metadata='DCSREC,3\naircraft,FA-18C_hornet\nlivery,Blue Angels Jet Team\ntheatre,Caucasus\nsource,Observer\nsource_unit_id,16777472\nstate_profile,hornet-exterior-v1\nengine_profile,hornet-native-engine-v1\ncapture_build,2.9.29.27468\nwind_ground,0\nwind_2000,0\nwind_8000,0\n'
local hex=metadata:gsub('.',function(c)return string.format('%02x',c:byte())end)
emit('BEGIN,1,'..hex)
for i=0,300 do
    local t=10+i*.02;now=t+(mode=='late' and .1 or .01)
    if mode=='wrong_player' then id=123 end
    local values={t,(t-10)*220,2000,0,1,0,0,0,1,0,0,0,1,220,0,0,0,'',''}
    for c=1,13 do values[#values+1]=c<=3 and 0 or -.2 end
    for _,v in ipairs({.8,.7,.5,.4})do values[#values+1]=v end
    for j,v in ipairs(values)do values[j]=tostring(v)end
    emit('DATA,1,'..(i+1)..','..table.concat(values,','))
end
emit('END,1,user_stop,301');callbacks.onSimulationStop()
print('PASS: native engine sink fixture finished: '..mode)
