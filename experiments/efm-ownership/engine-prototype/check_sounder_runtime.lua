-- Run the locally extracted DCS loader, not a reimplementation of its sandbox.
-- The installed loader bytes remain local and are never committed/distributed.
local loader,script=assert(arg[1]),assert(arg[2])
local console=print
local messages,plays,stops,sources={},{},{},{}
print=function(...)local t={};for i=1,select('#',...)do t[i]=tostring(select(i,...))end;messages[#messages+1]=table.concat(t,' ')end
log={info=print,warning=print,error=print}
ED_AudioAPI={ContextWorld=1,createHost=function()return 1 end,
    createSource=function(_,name)sources[#sources+1]=name;return #sources end,
    playSourceLooped=function(id)plays[#plays+1]=sources[id]end,
    stopSource=function(id)stops[#stops+1]=id end}
for _,name in ipairs({'destroyHost','destroySource','setHostPosition','setHostOrientation','setHostVelocity','setHostTimestamp','setSourcePitch','setSourceGain'}) do
    ED_AudioAPI[name]=function()end
end
assert(loadfile(loader))()
local key='aircraft/planes/dcsrecordersoundertest'
_smix_file[key]=script;_smix_chunk[key]=assert(loadfile(script))
assert(Sounder_exists('Aircraft/Planes/DCSRecorderSounderTest'))
local object=assert(Sounder_create('runtime-check','Aircraft/Planes/DCSRecorderSounderTest'))
local env=getfenv(_smix_chunk[key])
assert(env.io==nil and env.log==nil,'recheck changed sandbox contract')
local bindings={}
for _,name in ipairs({'timestamp','posx','posy','posz','orienta','orientb','orientc','orientd','velx','vely','velz'}) do
    bindings[name]=Sounder_bindParam(name)
    Sounder_setParam(object,bindings[name],name=='orientd' and 1 or 0)
end
for _,time in ipairs({100,101,103,106,109,112,115}) do
    Sounder_setParam(object,bindings.timestamp,time)
    Sounder_process(object)
end
assert(#plays==4 and plays[1]:find('RPM1') and plays[2]:find('Afterburner') and plays[3]==plays[1] and plays[4]==plays[2])
local found_silent=false
for _,line in ipairs(messages) do if line:find('phase 4 silent') then found_silent=true end end
assert(found_silent and #stops>=10)
Sounder_destroy(object)
console('PASS: actual DCS sounder loader creates both sources and dispatches all four phases plus silence')
console('CONFIRMED: sounder environment has no io or log; script diagnostics use its print binding')
