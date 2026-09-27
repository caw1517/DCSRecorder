local hook_path,root=assert(arg[1]),assert(arg[2])
root=root:gsub('\\','/')..'/'
local callbacks
local history,buffer={},''
local wrapped_io=setmetatable({}, {__index=io})
if arg[3]=='deny_log_read' then
 function wrapped_io.open(path,mode)
  if path==root..'Logs/dcs.log' and mode=='rb' then return nil, 'cannot open active DCS log' end
  return io.open(path,mode)
 end
end
if arg[3]=='dcs_void_io' then
 function wrapped_io.open(path,mode)
  local file,err=io.open(path,mode)
  if not file then return nil,err end
  local proxy={}
  function proxy:write(...) local result,err=file:write(...);if not result then error(err) end end
  function proxy:flush() local result,err=file:flush();if not result then error(err) end end
  function proxy:close() local result,err=file:close();if not result then error(err) end end
  function proxy:read(...)return file:read(...)end
  function proxy:seek(...)return file:seek(...)end
  return proxy
 end
end
local wrapped_os=setmetatable({}, {__index=os})
if arg[3]=='dcs_void_io' then
 function wrapped_os.rename(a,b)local result,err=os.rename(a,b);if not result then error(err) end end
 function wrapped_os.remove(a)local result,err=os.remove(a);if not result then error(err) end end
end
local env=setmetatable({io=wrapped_io,os=wrapped_os,lfs={writedir=function()return root end,mkdir=function()return true end,
    attributes=function(path)local f=io.open(path,'rb');if f then f:close();return {} end end},
    log={INFO=1,write=function()end},DCS={setUserCallbacks=function(value)callbacks=value end, getLogHistory=function(index)
 local result={}
 for i=index+1,#history do result[#result+1]=history[i] end
 return result,#history
 end}},{__index=_G})
local hook=assert(loadfile(hook_path));setfenv(hook,env);hook()
local function pump()for i=1,15 do callbacks.onSimulationFrame() end end
local function write(text,mode)
 local f=assert(io.open(root..'Logs/dcs.log',mode or 'ab'));f:write(text);f:close()
 if mode=='wb' then history={};buffer='' end
 buffer=buffer..text
 while true do
  local ending=buffer:find('\n',1,true);if not ending then break end
  history[#history+1]={0,1,'SCRIPTING',buffer:sub(1,ending-1)};buffer=buffer:sub(ending+1)
 end
 pump()
end
local meta='DCSREC,1\naircraft,FA-18C_hornet\nlivery,Blue Angels Jet Team\ntheatre,Caucasus\nsource,Observer\n'
if arg[4]=='v2' then meta=meta:gsub('DCSREC,1','DCSREC,2')..'state_profile,hornet-exterior-v1\n' end
local hex=meta:gsub('.',function(c)return string.format('%02x',string.byte(c))end)
local function emit(text)write('INFO SCRIPTING: DCSREC_LOG,1,'..text..'\n')end
local row='10,0,2000,0,1,0,0,0,1,0,0,0,1,220,0,0,0,,'
if arg[4]=='v2' then row=row..',0.1,0.2,0.3,-0.4,-0.5,0.6,-0.7,0.8,-0.9,0.4,-0.3,0.2,-0.1' end
write('', 'wb')
emit('BEGIN,1,'..hex);emit('DATA,1,1,'..row)
-- Partial final line must not be consumed until completed.
write('INFO SCRIPTING: DCSREC_LOG,1,DATA,1,2,'..row)
write('\n');emit('END,1,user_stop,2')
-- Duplicate END cannot create another recording.
emit('END,1,user_stop,2')
-- A new mission may reuse the same take number; identities remain distinct.
emit('BEGIN,1,'..hex);emit('DATA,1,1,'..row);emit('DATA,1,2,'..row);emit('END,1,user_stop,2')
-- Lost sample, aircraft loss, and abandoned take stay incomplete.
emit('BEGIN,2,'..hex);emit('DATA,2,2,'..row);emit('END,2,user_stop,2')
emit('BEGIN,3,'..hex);emit('DATA,3,1,'..row);emit('END,3,aircraft_lost,1')
emit('BEGIN,4,'..hex);emit('DATA,4,1,'..row)
callbacks.onSimulationStop()
-- Log truncation invalidates the pending take without publishing it.
write('', 'wb');pump()
print('PASS: split lines, explicit stop, repeated take IDs, duplicate END, missing rows, aircraft loss, abandonment, truncation')
