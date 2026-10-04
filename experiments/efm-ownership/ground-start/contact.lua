-- Read-only contact evidence paired with the unchanged full-state recorder.
-- The CSV format stays v7; this diagnostic sidecar lives in DCS.log.
local r=assert(DCSRECORDER,'Full-state recorder must load first')
assert(not r.ground_capture,'Ground capture already installed')
r.ground_capture=true
local original=r.sample
local active_take,last_time,last_row
local function finite(v) return type(v)=='number' and v==v and math.abs(v)<math.huge end
local function emit(text) env.info('DCSGROUND,1,'..text) end
local function finish(reason)
    if active_take then
        emit('END,'..active_take..','..tostring(last_row or 0)..','..reason)
        active_take=nil
    end
end
function r.sample()
    local data=original()
    if not data:match('^DATA,') then return data end
    local take,time=data:match('^DATA,(%d+),([^,]+),')
    local t=tonumber(time)
    if active_take~=take then
        finish('next_take')
        active_take=take;last_time=nil;last_row=0
        emit('BEGIN,'..take..','..assert(DCSGROUND_SOURCE_ID)..','..r.source)
        emit('COLUMNS,take,row,t,unit_id,in_air,terrain_height,origin_agl,life,life0,surface_type')
    end
    if not last_time or t>last_time then
        local u=Unit.getByName(r.source)
        local ok,values=pcall(function()
            local p=u:getPosition().p
            local h=land.getHeight({x=p.x,y=p.z})
            local air=u:inAir()
            assert(type(air)=='boolean','Missing ground signal')
            -- DCS returns a numeric string here; normalize it before numeric validation.
            local id=tonumber(u:getID())
            assert(finite(id) and id>0 and id==math.floor(id),'Invalid unit identity')
            local v={id,air and 1 or 0,h,p.y-h,u:getLife(),u:getLife0(),land.getSurfaceType({x=p.x,y=p.z})}
            for i=1,7 do assert(finite(v[i]),'Invalid ground evidence') end
            return v
        end)
        if not ok then emit('ERROR,'..take..','..time..',ground_evidence_unavailable');return 'INVALID' end
        last_time=t;last_row=r.rows+1
        for i,n in ipairs(values) do values[i]=string.format('%.12g',n) end
        emit('DATA,'..take..','..last_row..','..time..','..table.concat(values,','))
    end
    return data
end
timer.scheduleFunction(function()
    if r.state~='recording' then finish(r.state) end
    return timer.getTime()+.1
end,nil,timer.getTime()+.1)
world.addEventHandler({onEvent=function(_,event)
    local unit=Unit.getByName(r.source)
    if unit and (event.initiator==unit or event.target==unit) then
        emit('EVENT,'..tostring(r.take)..','..string.format('%.12g',event.time or timer.getTime())..','..tostring(event.id))
    end
end})
