local source,script_path,output=assert(arg[1]),assert(arg[2]),assert(arg[3])
dofile(source)
local player_count=0
for _,country in pairs(mission.coalition.blue.country) do
    local groups=(country.plane or {}).group or {}
    for i=#groups,1,-1 do
        local group=groups[i]
        if group.units[1].name=='Probe' then table.remove(groups,i)
        else
            assert(#group.units==1 and group.units[1].name=='Observer')
            assert(group.units[1].type=='FA-18C_hornet' and group.units[1].skill=='Player')
            player_count=player_count+1
        end
    end
end
assert(player_count==1)
local f=assert(io.open(script_path,'rb'));local script=f:read('*a');f:close()
assert(loadstring(script))
mission.trigrules[1].actions={{predicate='a_do_script',text=script}}
mission.trig.actions[1]='a_do_script('..string.format('%q',script)..');'
mission.descriptionText='Actual-flight recording test. Fly the stock clean Hornet in calm air. F10 > DCS Recorder > Start recording. Begin with 5 seconds straight and level, then fly a gentle turn. Stay between 5000 and 9500 feet MSL and 300-400 KIAS. Keep roll rates gentle. F10 > DCS Recorder > Stop recording before leaving the mission; wait for the sample-count confirmation. This prototype writes the take into DCS.log for extraction afterward. Leave DCS open until the take is collected.'
if arg[4] then local description=assert(io.open(arg[4],'rb'));mission.descriptionText=description:read('*a');description:close() end
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v) end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v) end
    assert(type(v)=='table');local keys={};for k in pairs(v) do keys[#keys+1]=k end
    table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
    local out={'{'};for _,k in ipairs(keys) do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..',\n' end
    out[#out+1]='}';return table.concat(out)
end
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: recording mission has one stock player Hornet, F10 controls and no synthetic playback aircraft')
