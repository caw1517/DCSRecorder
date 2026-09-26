-- Packaging regression: run the installed mission-load predicate against the
-- official Hornet plugin ID, assuming the user's confirmed enabled installation.
-- This checks metadata, not entitlement or live module activation.
local missionFile, pluginFile, editorFile = assert(arg[1]), assert(arg[2]), assert(arg[3])
local function read(path)
    local f=assert(io.open(path,'rb')); local text=f:read('*a'); f:close(); return text
end
local pluginId=assert(read(pluginFile):match('local self_ID%s*=%s*"([^"]+)"'))
local condition=assert(read(editorFile):match('(if %(base%.enableModules%[v%].-then)%s+txtMsg'),
    'Installed mission-load predicate changed')
local rejects=assert(loadstring('return function(base,v) '..condition..
    ' return true end return false end'))()
local registered={enableModules={[pluginId]=true},
    pluginsById={[pluginId]={applied=true,state='installed'}}}
dofile(missionFile)
local count=0
for _,required in pairs(mission.requiredModules) do
    count=count+1
    assert(not rejects(registered,required),
        'Need Modules for mission load: '..required..' (installed plugin ID is '..pluginId..')')
end
assert(count==1,'Expected one explicit Hornet dependency')
print('PASS: mission dependency accepted by installed loader predicate for '..pluginId)
