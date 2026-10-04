local input,output,dcs,custom,adapter=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4]),assert(arg[5])
assert(loadfile(input))()
assert(loadfile(adapter))()(mission,dcs,custom)
local function serialize(v)
    if type(v)=='table' then
        local keys={};for k in pairs(v)do keys[#keys+1]=k end
        table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
        local parts={};for _,k in ipairs(keys)do parts[#parts+1]='['..serialize(k)..']='..serialize(v[k])end
        return '{'..table.concat(parts,',')..'}'
    elseif type(v)=='string' then return string.format('%q',v)
    elseif type(v)=='number' then return string.format('%.17g',v)
    elseif type(v)=='boolean' then return tostring(v)
    end
    error('Unsupported default type: '..type(v))
end
local defaults={}
for _,coalition in pairs(mission.coalition)do
    if type(coalition)=='table' then
        for _,country in pairs(coalition.country or {})do
            for _,group in pairs((country.plane or {}).group or {})do
                for _,unit in ipairs(group.units)do
                    defaults[unit.unitId]={AddPropAircraft=unit.AddPropAircraft,datalinks=unit.datalinks}
                end
            end
        end
    end
end
local file=assert(io.open(output,'wb'));file:write('return '..serialize(defaults)..'\n');file:close()
print('PASS: resolved installed Hornet loading defaults without changing authored values')
