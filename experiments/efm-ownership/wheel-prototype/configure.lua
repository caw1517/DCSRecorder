local baseline,ground,script_path,output,dcs=assert(arg[1]),assert(arg[2]),assert(arg[3]),assert(arg[4]),assert(arg[5])
dofile(baseline);local clean=mission;local clean_unit
for _,country in pairs(clean.coalition.blue.country)do for _,g in pairs((country.plane or {}).group or {})do
    for _,u in pairs(g.units)do if u.name=='Observer' then clean_unit=u end end
end end
assert(clean_unit and clean_unit.type=='FA-18C_hornet')
dofile(ground);assert(mission.theatre=='Caucasus');local selected,country_id,country_name
for _,country in pairs(mission.coalition.blue.country)do for _,g in pairs((country.plane or {}).group or {})do
    for _,u in pairs(g.units)do if u.skill=='Player' then
        assert(not selected and #g.units==1 and u.type=='FA-18C_hornet')
        selected=g;country_id=country.id;country_name=country.name
    end end
end end
assert(selected)
local unit=selected.units[1];local first=selected.route.points[1]
assert(first.type=='TakeOffParking' and first.action=='From Parking Area' and first.airdromeId==25)
assert(unit.parking_id=='15' and unit.parking=='1')
unit.name='Observer';unit.livery_id=clean_unit.livery_id;unit.payload=clean_unit.payload;unit.speed=0
selected.name='WheelDiagnostic';selected.lateActivation=false;selected.uncontrolled=false
first.type='TakeOffParkingHot';first.action='From Parking Area Hot'
for _,point in pairs(selected.route.points)do point.task={id='ComboTask',params={tasks={}}}end
mission=clean;mission.coalition.blue.country={{id=country_id,name=country_name,plane={group={selected}}}}
mission.coalition.red.country={};mission.coalition.neutrals.country={};mission.start_time=12*3600
local function serialize(v)
    if type(v)=='string' then return string.format('%q',v)end
    if type(v)=='number' or type(v)=='boolean' then return tostring(v)end
    assert(type(v)=='table');local keys={};for k in pairs(v)do keys[#keys+1]=k end
    table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
    local out={'{'};for _,k in ipairs(keys)do out[#out+1]='['..serialize(k)..']='..serialize(v[k])..','end
    out[#out+1]='}';return table.concat(out)
end
dofile(dcs..'/Mods/aircraft/FA-18C/FM/config.lua')
local expected={{0,1,101},{5,6,103},{3,4,102}}
for i,gear in ipairs(FA18C.suspension)do
    assert(gear.arg_post==expected[i][1] and gear.arg_amortizer==expected[i][2] and gear.arg_wheel_rotation==expected[i][3])
end
local f=assert(io.open(script_path,'rb'));local script=f:read('*a');f:close();assert(loadstring(script))
if arg[6]=='steering' then
    script='DCS_WHEEL_PROTOCOL=2;DCS_WHEEL_CHANNELS={0,5,3,1,6,4,101,103,102,2,17,18}\n'..script
end
mission.trigrules={{comment='Read-only wheel and suspension capture',predicate='triggerStart',eventlist='',rules={},actions={{predicate='a_do_script',text=script}}}}
mission.trig={actions={'a_do_script('..string.format('%q',script)..');'},conditions={'return(true)'},func={},flag={true},funcStartup={'if mission.trig.conditions[1]() then mission.trig.actions[1]() end'}}
mission.descriptionText='WHEEL AND SUSPENSION DIAGNOSTIC. Parked stock Hornet, engines running. No Active Pause. F10 > Wheel diagnostic > Start taxi capture. Remain stopped for 5 seconds, release parking brake and taxi slowly (about 5-10 knots), then brake to a full stop and hold for 5 seconds. Repeat once. Optional F10 Mark braking. Stop taxi capture through F10 and leave DCS open. Observe wheel rotation/strut movement in F2 when practical. Stay on the ground; this first test is taxi only. Capture ends after 3 minutes or above 15 m/s. It does not command controls or write to the flight library.'
if arg[6]=='steering'then
    mission.descriptionText='NOSE-WHEEL STEERING CAPTURE. Parked stock Hornet. F10 > Wheel diagnostic > Start taxi capture. No Active Pause. Center steering for 5 seconds, taxi slowly with a left turn for about 5 seconds, center for 5 seconds, then turn right for about 5 seconds, center and stop. About 5-10 knots. If practical observe the nose wheel in F2. Optional F10 marks record visible left/center/right states. Stop taxi capture and leave DCS open. This adds unverified argument 2 plus rudder arguments 17/18 to the earlier wheel/compression channels. No control commands, native hooks or normal flight-library changes. Do not take off.'
end
f=assert(io.open(output,'wb'));f:write('mission = ',serialize(mission));f:close()
print('PASS: installed wheel mappings verified; one clean parked hot-start Hornet; read-only script; no control commands')
