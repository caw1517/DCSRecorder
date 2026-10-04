-- Integrated save-hook + native sampler fixture. No real aircraft or native reads.
local sink_path,engine_path,root,mode=assert(arg[1]),assert(arg[2]),assert(arg[3]),arg[4] or 'normal'
local smoke_path=arg[5]
if smoke_path=='-' then smoke_path=nil end
local contact=arg[6]=='contact'
local wheels=arg[6]=='wheels' or contact
local capture_build=arg[7] or '2.9.29.27468'
local canopy=arg[6]=='canopy' or wheels
local lights=arg[6]=='lights' or canopy
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
    LoGetSelfData=function()return {Name='FA-18C_hornet',Position={x=(now-10)*220+(mode=='wrong_position' and 10 or 0),y=2000,z=0}}end,
    LoGetEngineInfo=function()return {RPM={left=99,right=98}}end}
env.package={loadlib=function(path,symbol)
    local suffix=capture_build=='2.9.30.28536' and '2930.dll' or 'Capture.dll'
    assert(path:sub(-#suffix)==suffix,'Wrong build capture helper')
    if symbol=='dcs_native_smoke_sample' then
        assert(smoke_path)
        if mode=='smoke_missing' then return nil,'missing smoke helper'end
        return function()
            if mode=='smoke_unavailable' then return 'UNAVAILABLE,no_smoke_generator'end
            if mode=='smoke_identity' then id=id+1 end
            if mode=='smoke_clock' then now=now+.1 end
            local on=now>=12 and now<14 and '1' or '0'
            return 'OK,10,'..on..','..(mode=='smoke_mismatch' and '2' or on)..',0'
        end
    end
    if mode=='missing' then return nil,'missing helper' end
    return function()
        if mode=='player_during_read' then id=id+1 end
        return 'OK,.?AVwHumanAircraft@@,8,123,0.99,1.06,2.3,'..
        (mode=='unequal' and '2.1' or '2.3')..',0.98,0.95,1.15,1.15,8101824,8101872,8101920'end
end}
env.loadfile=function(path)
    local source
    if path==root..'Scripts/DCSRecorderEngineCapture/engine_capture.lua' then source=engine_path
    elseif path==root..'Scripts/DCSRecorderSmokeCapture/smoke_capture.lua' then source=assert(smoke_path)
    else error('Unexpected capture helper path')end
    local f=assert(loadfile(source));setfenv(f,env);return f
end
local hook=assert(loadfile(sink_path));setfenv(hook,env);hook()
local function emit(text)
    history[#history+1]='DCSREC_LOG,1,'..text
    if not env.defer_pump then callbacks.onSimulationFrame()end
end
local metadata='DCSREC,3\naircraft,FA-18C_hornet\nlivery,Blue Angels Jet Team\ntheatre,Caucasus\nsource,Observer\nsource_unit_id,2\nstate_profile,hornet-exterior-v1\nengine_profile,hornet-native-engine-v1\ncapture_build,'..capture_build..'\nwind_ground,0\nwind_2000,0\nwind_8000,0\n'
if smoke_path then metadata=metadata:gsub('DCSREC,3','DCSREC,4')..'smoke_profile,hornet-native-smoke-v1\nsmoke_station,10\nsmoke_clsid,{INV-SMOKE-WHITE}\n'end
if lights then metadata=metadata:gsub('DCSREC,[34]','DCSREC,5')..'light_profile,hornet-lights-v1\n'end
if canopy then metadata=metadata:gsub('DCSREC,5','DCSREC,6')..'canopy_profile,hornet-canopy-v1\n'end
if wheels then metadata=metadata:gsub('DCSREC,6','DCSREC,7')..'wheel_profile,hornet-wheels-v1\n'end
if contact then metadata=metadata:gsub('DCSREC,7','DCSREC,8')..'contact_profile,hornet-contact-v1'..string.char(10) end
if mode:match('^batch') then metadata=metadata..'capture_timing,frame-batch-v1\n'end
local hex=metadata:gsub('.',function(c)return string.format('%02x',c:byte())end)
emit('BEGIN,1,'..hex)
for i=0,300 do
    local t=10+i*.02;now=t+(mode=='late' and .1 or .01)
    env.defer_pump=(mode=='batch' and i>=100 and i<103) or
        (mode=='batch_initial' and i<3) or (mode=='batch_long' and i>=100 and i<110)
    if mode=='changed_player' and i>0 then id=123 end
    if mode=='invalid_player' then id=0 end
    local values={t,(t-10)*220,2000,0,1,0,0,0,1,0,0,0,1,220,0,0,0,'',''}
    for c=1,13 do values[#values+1]=c<=3 and 0 or -.2 end
    for _,v in ipairs({.8,.7,.5,.4})do values[#values+1]=v end
    if lights then for c=1,7 do values[#values+1]=(mode=='invalid_light' and c==1) and 1.1 or (c==5 and (i%4<2 and 0 or .9) or c/10) end end
    if canopy then values[#values+1]=mode=='invalid_canopy' and 'nan' or (.9*i/300)end
    if wheels then
        for _,v in ipairs({.71+i/3000,.82+i/10000,.83-i/10000,(.97+i*.03)%1,(.98+i*.02)%1,(.99+i*.01)%1,-.7+i/300*1.4})do values[#values+1]=v end
        if mode=='invalid_wheel' then values[#values]='nan' end
    end
    if contact then
        -- Parked, then rolling on the runway; damage and bad flags exercise refusal.
        for _,v in ipairs({i<200 and 0 or 1,12.5,mode=='damaged' and i>=150 and 0.9 or 1,1,mode=='invalid_contact' and 7 or 5})do values[#values+1]=v end
    end
    for j,v in ipairs(values)do values[j]=tostring(v)end
    emit('DATA,1,'..(i+1)..','..table.concat(values,','))
end
emit('END,1,user_stop,301');callbacks.onSimulationStop()
print('PASS: native engine sink fixture finished: '..mode)
