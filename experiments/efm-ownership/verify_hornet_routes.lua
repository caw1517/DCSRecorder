-- Run the installed editor's full route-timing validator on the saved mission.
local missionFile, routeModule = assert(arg[1]), assert(arg[2])
local f=assert(io.open(routeModule,'rb')); local source=f:read('*a'); f:close()
local code=assert(source:match('(local function getWptWithFlags.-)\nfunction verifyWptTasks'),
    'Installed route-validator layout changed')
local loader=assert(loadstring(code..'\nreturn verifyRoute'))
setfenv(loader,{table=table,tostring=tostring,_=function(s) return s end})
local verify=loader()
dofile(missionFile)
local errors={}; local checked=0
for _,side in pairs(mission.coalition) do
    if type(side)=='table' then for _,country in pairs(side.country or {}) do
        for _,group in pairs((country.plane or {}).group or {}) do
            -- DCS adds waypoint indices when importing a serialized mission.
            for i,point in ipairs(group.route.points) do point.index=i end
            local err=verify(group.route,group.lateActivation)
            if err then errors[#errors+1]=group.name..': '..err end
            checked=checked+1
        end
    end end
end
assert(checked==tonumber(arg[3] or 2),'Unexpected number of aircraft routes')
assert(#errors==0,table.concat(errors,'\n'))
print('PASS: '..checked..' saved aircraft routes pass the installed DCS route-timing validator')
