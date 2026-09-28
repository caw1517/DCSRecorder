local input,output,dcs=assert(arg[1]),assert(arg[2]),assert(arg[3])
dofile(input)
local f=assert(io.open(dcs..'/CoreMods/aircraft/FA-18C/FA-18C_hornet.lua','rb'))
local descriptor=f:read('*a');f:close()
assert(descriptor:find('{INV-SMOKE-WHITE}',1,true),'Installed white smoke loadout missing')
local count=0
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        for _,unit in pairs(group.units) do
            assert(unit.name=='Observer' and unit.type=='FA-18C_hornet' and unit.skill=='Player')
            for _,station in ipairs({2,3,5,7,8}) do assert(unit.payload.pylons[station].CLSID=='<CLEAN>') end
            unit.payload.pylons[10]={CLSID='{INV-SMOKE-WHITE}'};count=count+1
        end
    end
end
assert(count==1)
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v) end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v) end
    assert(type(v)=='table');local keys={};for k in pairs(v) do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b) end)
    local out={'{'};for _,k in ipairs(keys) do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..',\n' end
    out[#out+1]='}';return table.concat(out)
end
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: one stock Hornet with white smoke on SMK station 10 and clean removable stations')
