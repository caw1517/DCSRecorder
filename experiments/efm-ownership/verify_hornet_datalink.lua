-- Replay the installed editor's real descriptor loader and setDefault call.
-- Stub only unrelated editor/GUI services; never edit DCS installation files.
local descriptorPath, editorPath = assert(arg[1]), assert(arg[2])
local f=assert(io.open(descriptorPath,'rb')); local descriptor=f:read('*a'); f:close()
local datalinks=assert(loadstring('return '..assert(descriptor:match('\n%s*datalinks%s*=%s*(%b{})'))))()
local unit={type='DCSRecorder-Hornet-Probe',name='Probe',unitId=9001,index=1,AddPropAircraft={}}
unit.boss={units={unit}}
local function copy(to,from)
    for k,v in pairs(from) do
        if type(v)=='table' then to[k]={}; copy(to[k],v) else to[k]=v end
    end
end
U={recursiveCopyTable=copy,traverseTable=function() end}
local modules={
    me_db_api={unit_by_type={[unit.type]={_file=descriptorPath,datalinks=datalinks}}},
    me_mission={unit_by_id={[9001]=unit}},
    i18n={setup=function(env) env._=function(s) return s end end},
    lfs={
        writedir=function() return './missing-saved-games/' end,
        currentdir=function() return './missing-dcs-root/' end,
        normpath=function(path) return (path:gsub('\\','/')) end,
        attributes=function(path)
            local file=io.open(path,'rb')
            if file then file:close(); return {mode='file'} end
        end,
    },
}
local originalRequire=require
require=function(name) return modules[name] or {} end
local originalLoadfile=loadfile
loadfile=function(path)
    -- Avoid waiting on stdin if DCS's path resolver returns nil. Its loader
    -- produces an empty descriptor here, matching the logged missing method.
    if not path then return function() end end
    return originalLoadfile(path)
end
dofile(editorPath)
me_datalinks.setDefault(unit)
assert(unit.datalinks.Link16.network.teamMembers[1].missionUnitId==9001)
assert(unit.datalinks.Link16.settings.AIC_Channel==1)
local dlg=assert(me_datalinks.getCorrectPath('Datalinks/Link16.dlg'),'Missing Link16 dialog')
require=originalRequire; loadfile=originalLoadfile
print('PASS: installed editor loads the packaged Link16 descriptor, generates defaults and resolves its dialog')
