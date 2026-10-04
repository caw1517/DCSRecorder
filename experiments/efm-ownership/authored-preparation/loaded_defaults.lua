-- Authored-mission variant of release-start/loaded_defaults.lua: stock Hornets
-- plus at most one named playback module type; any number of one-unit groups.
-- This does not ignore differences or mutate a running DCS mission.
local function read(path)
    local f=assert(io.open(path,'rb'));local text=f:read('*a');f:close();return text
end
local function copy(value)
    if type(value)~='table' then return value end
    local out={};for k,v in pairs(value)do out[k]=copy(v)end;return out
end
return function(mission,dcs,custom_aircraft,custom_type)
    local units,groups={},{}
    for _,coalition in pairs(mission.coalition)do
        if type(coalition)=='table' then
            for _,country in pairs(coalition.country or {})do
                for _,group in pairs((country.plane or {}).group or {})do
                    assert(#group.units==1,'This control supports one aircraft per group')
                    groups[#groups+1]=group
                    for _,unit in ipairs(group.units)do
                        assert(unit.type=='FA-18C_hornet' or unit.type==custom_type,'Unsupported aircraft type: '..tostring(unit.type))
                        units[unit.unitId]=unit
                    end
                end
            end
        end
    end
    local e=setmetatable({_ = function(s)return s end},{__index=_G})
    local helpers=assert(loadfile(dcs..'/CoreMods/aircraft/FA-18C/Datalinks/AddProp.lua'));setfenv(helpers,e);helpers()
    local function properties(path)
        local body=assert(read(path):match('AddPropAircraft%s*=%s*(%b{})'),'Installed Hornet property table changed')
        local fn=assert(loadstring('return '..body));setfenv(fn,e);return fn()
    end
    local props={FA_18=properties(dcs..'/CoreMods/aircraft/FA-18C/FA-18C_hornet.lua'),custom=properties(custom_aircraft)}
    local source=read(dcs..'/MissionEditor/modules/me_paramFM.lua'):gsub('\r\n','\n')
    local setup=assert(source:match('(function setupOnLoad%(a_prop, a_unit, a_typePanel%).-\nend)'),'Installed property loader changed')
    e.base={pairs=pairs,table=table,string=string}
    e.MissionModule={unit_by_id=units}
    e.crutches={getPlayerSkill=function()return 'Player'end,getClientSkill=function()return 'Client'end}
    local chunk=assert(loadstring(setup));setfenv(chunk,e);chunk()
    for _,group in ipairs(groups)do
        for i,unit in ipairs(group.units)do
            local old_boss,old_index=unit.boss,unit.index
            unit.boss,unit.index=group,i
            e.setupOnLoad(unit.type=='FA-18C_hornet' and props.FA_18 or props.custom,unit)
            unit.boss,unit.index=old_boss,old_index
        end
    end
    local link=setmetatable({},{__index=_G})
    link.recursiveCopyTable=function(to,from)for k,v in pairs(from)do to[k]=copy(v)end end
    link.getAddPropByUnitId=function(id)return assert(units[id]).AddPropAircraft end
    link.getDatalinksByUnitId=function(id)return assert(units[id]).datalinks end
    local descriptor=assert(loadfile(dcs..'/CoreMods/aircraft/FA-18C/Datalinks/Link16.lua'))
    setfenv(descriptor,link);descriptor()
    for _,group in ipairs(groups)do
        local unit=group.units[1]
        unit.datalinks=unit.datalinks or {}
        if unit.datalinks.Link16==nil then
            unit.datalinks.Link16=link.getDefault({unit={unitId=unit.unitId,index=1,name=unit.name,
                AddPropAircraft=copy(unit.AddPropAircraft)},group={}})
        end
    end
    return mission
end
