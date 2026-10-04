local path=assert(arg[1])
local f,err=io.open(path,'rb')
print('open',not not f,err)
if f then
 print('seek_end',f:seek('end'))
 print('seek_start',f:seek('set',0))
 local text=f:read(262144)
 print('bytes_read',text and #text or 0)
 f:close()
end
