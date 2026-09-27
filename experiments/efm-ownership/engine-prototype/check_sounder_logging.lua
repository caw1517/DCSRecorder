-- Check the hook against log constants from the installed native DCS library.
local core,hook=assert(arg[1]),assert(arg[2])
assert(package.loadlib(core,'ED_luaopen_log'))()
local native_log=log
local calls={}
local trace_markers={}
local function has(mask,flag)return math.floor(mask/flag)%2==1 end
log={ALL=native_log.ALL,TRACE=native_log.TRACE,MESSAGE=native_log.MESSAGE,
    INFO=native_log.INFO,ERROR=native_log.ERROR,
    set_output=function(name,facility,levels,format)
        calls[#calls+1]={name=name,facility=facility,levels=levels}
    end,
    write=function(facility,level,message)
        if level==native_log.TRACE and message:find('DCSRECORDER%-TRACE%-CHECK')then
            trace_markers[facility]=true
        end
    end}
assert(loadfile(hook))()
assert(#calls==3,'expected three scoped outputs')
for _,call in ipairs(calls)do
    assert(has(call.levels,native_log.INFO),'INFO must remain visible')
    assert(has(call.levels,native_log.TRACE),call.facility..': TRACE excluded by output mask '..call.levels)
    assert(trace_markers[call.facility],call.facility..': missing TRACE self-check marker')
end
print('PASS: hook includes native INFO and TRACE; ALL='..native_log.ALL..', TRACE='..native_log.TRACE)
print('This checks filter configuration against native constants, not live sound dispatch.')
