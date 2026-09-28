local script=assert(arg[1])
local elapsed,commands,callback=0,{},nil
DCS_STAGED_PLAYBACK={phase='waiting'}
env={info=function()end};trigger={action={outText=function()end}}
timer={getTime=function()return elapsed+10 end,scheduleFunction=function(fn)callback=fn end}
local controller={setCommand=function(self,c)
    assert(c.id=='SMOKE_ON_OFF' and type(c.params.value)=='boolean')
    commands[#commands+1]=c.params.value
end}
local unit={isExist=function()return true end,
    getDrawArgumentValue=function(self,i)assert(i==996);return elapsed/1000 end,
    getController=function()return controller end}
Unit={getByName=function(name)assert(name=='StagedPlayback');return unit end}
dofile(script);assert(callback() and #commands==0)
DCS_STAGED_PLAYBACK.phase='playing'
for _,t in ipairs({0,3,8,13,18,23,28}) do elapsed=t+.01;assert(callback()) end
assert(#commands==7)
for i=1,7 do assert(commands[i]==(i%2==0)) end
callback();assert(#commands==7,'Duplicate smoke command')
DCS_STAGED_PLAYBACK.phase='complete';assert(callback()==nil and #commands==7)
print('PASS: control uses native elapsed time, targets only lead, suppresses repeats and stops at completion')
