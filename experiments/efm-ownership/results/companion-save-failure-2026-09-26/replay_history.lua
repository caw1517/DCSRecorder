local hook_path,root,log_path=assert(arg[1]),assert(arg[2]),assert(arg[3])
root=root:gsub('\\','/')..'/'
local source=assert(io.open(log_path,'rb'));local entries={}
for line in source:lines() do entries[#entries+1]={0,1,'SCRIPTING',line} end
source:close()
local callbacks
local wrapped_io=setmetatable({}, {__index=io})
function wrapped_io.open(path,mode)
 if path==root..'Logs/dcs.log' then return nil,'active log unavailable' end
 return io.open(path,mode)
end
local env=setmetatable({io=wrapped_io,lfs={writedir=function()return root end,mkdir=function()return true end,
 attributes=function(path)local f=io.open(path,'rb');if f then f:close();return {} end end},
 log={INFO=1,write=function(_,_,text)print(text)end},
 DCS={setUserCallbacks=function(value)callbacks=value end,getLogHistory=function(index)
  local output={};local ending=math.min(index+100,#entries)
  for i=index+1,ending do output[#output+1]=entries[i] end
  return output,ending
 end}},{__index=_G})
local hook=assert(loadfile(hook_path));setfenv(hook,env);hook()
for i=1,math.ceil(#entries/100)+1 do callbacks.onSimulationFrame() end
