local input,scriptpath,output=assert(arg[1]),assert(arg[2]),assert(arg[3])
dofile(input)
local lead,observer=0,0
for _,country in pairs(mission.coalition.blue.country) do
    for _,group in pairs((country.plane or {}).group or {}) do
        for _,unit in pairs(group.units) do
            if unit.name=='StagedPlayback' then
                assert(unit.type=='DCSRecorder-Hornet-Engine-Staged' and group.lateActivation)
                unit.payload.pylons[10]={CLSID='{INV-SMOKE-WHITE}'};lead=lead+1
            else
                assert(unit.name=='Observer' and unit.type=='FA-18C_hornet')
                assert(not unit.payload.pylons[10]);observer=observer+1
            end
        end
    end
end
assert(lead==1 and observer==1)
local f=assert(io.open(scriptpath,'rb'));local script=f:read('*a');f:close()
assert(loadstring(script))
local actions=mission.trigrules[1].actions
actions[#actions+1]={predicate='a_do_script',text=script}
mission.trig.actions[1]=mission.trig.actions[1]..'a_do_script('..string.format('%q',script)..');'
mission.descriptionText='SMOKE CONTROL TEST. Uses the accepted Test flight for movement, surfaces and engine sound. ONLY the lead carries a white smoke generator on SMK station 10. Start normally: F10 > DCS Recorder > Start playback. Observe the lead. Smoke is requested ON at playback seconds 3, 13, 23 and OFF at 8, 18, 28; notices label each request. These are SYNTHETIC test commands, not captured smoke. Report whether the lead emits and stops smoke at each notice. Completion removes the lead normally. Keep DCS open for log collection.'
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v) end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v) end
    assert(type(v)=='table');local keys={};for k in pairs(v) do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b) end)
    local out={'{'};for _,k in ipairs(keys) do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..',\n' end
    out[#out+1]='}';return table.concat(out)
end
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
for _,section in ipairs({'actions','conditions','func','funcStartup'}) do
    for _,code in pairs(mission.trig[section]) do assert(loadstring(code)) end
end
print('PASS: white smoke fitted only to staged lead; existing staging triggers retained')
