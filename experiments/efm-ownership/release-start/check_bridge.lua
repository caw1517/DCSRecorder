local control=assert(package.loadlib(arg[1],'dcs_release_control'))
for _,cmd in ipairs({'inspect','commit','abort'})do
    assert(control(cmd,0,0,1)=='REFUSED,object_or_package','unowned object accepted')
    assert(control(cmd,'0',0,1)=='REFUSED,arguments','mistyped token accepted')
end
assert(control()=='REFUSED,arguments')
print('PASS: actual DLL Lua ABI; missing object and malformed request refusal')
