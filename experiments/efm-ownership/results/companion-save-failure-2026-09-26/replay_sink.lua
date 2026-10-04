local hook_path,root=assert(arg[1]),assert(arg[2])
root=root:gsub('\\','/')..'/'
local callbacks
local env=setmetatable({lfs={writedir=function()return root end,mkdir=function()return true end,
    attributes=function(path)local f=io.open(path,'rb');if f then f:close();return {} end end},
    log={INFO=1,write=function(_,_,text)print(text)end},DCS={setUserCallbacks=function(value)callbacks=value end}},{__index=_G})
local hook=assert(loadfile(hook_path));setfenv(hook,env);hook()
for i=1,1500 do callbacks.onSimulationFrame() end
print('Replay finished')
