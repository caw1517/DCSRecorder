assert(loadfile(arg[1]))()
local count=0
for _,rule in pairs(mission.trigrules)do
    for _,action in pairs(rule.actions)do
        if action.predicate=='a_do_script' then assert(loadstring(action.text));count=count+1 end
    end
end
for _,section in ipairs({'actions','conditions','func','funcStartup'})do
    for _,code in pairs(mission.trig[section])do assert(loadstring(code))end
end
local script=mission.trigrules[1].actions[2].text
local config_code=assert(script:match('^(DCSR_RELEASE_CONFIG=.-)\n%-%- Bounded airborne integration'))
local e={};local fn=assert(loadstring(config_code));setfenv(fn,e);fn()
local c=assert(e.DCSR_RELEASE_CONFIG)
assert(type(c.smoke_events)=='table' and #c.smoke_events>0 and c.smoke_events[1].time==0)
assert(type(c.smoke_events[1].on)=='boolean' and c.duration>0 and type(c.expected)=='table')
local channels=0;for _,value in pairs(c.expected)do assert(type(value)=='number');channels=channels+1 end
assert(channels==33 and count==2,'incomplete generated control')
print('PASS: generated nested mission/trigger Lua; 33 initial channels and typed smoke schedule')
