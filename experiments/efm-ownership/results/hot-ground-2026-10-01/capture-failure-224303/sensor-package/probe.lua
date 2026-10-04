-- Temporary read-only live boundary probe. No recording or control writes.
local function log(s) env.info('[DEBUG-ground23] '..s) end
local function probe(name,fn)
    local ok,v=pcall(fn)
    log(name..' ok='..tostring(ok)..' type='..type(v)..' value='..tostring(v))
    return ok,v
end
local attempts=0
timer.scheduleFunction(function()
    attempts=attempts+1
    local u=Unit.getByName('Observer')
    if not u or not u:isExist() or not u:getPlayerName() then
        if attempts<30 then return timer.getTime()+1 end
        log('no player after 30 attempts');return
    end
    probe('unit_id',function()return u:getID()end)
    probe('in_air',function()return u:inAir()end)
    probe('life',function()return u:getLife()end)
    probe('life0',function()return u:getLife0()end)
    probe('desc_life',function()return u:getDesc().life end)
    probe('position_y',function()return u:getPosition().p.y end)
    probe('terrain_height',function()local p=u:getPosition().p;return land.getHeight({x=p.x,y=p.z})end)
    probe('surface_type',function()local p=u:getPosition().p;return land.getSurfaceType({x=p.x,y=p.z})end)
    -- Execute the exact current sensor block, inserted from contact.lua by the builder.
    local finite=function(v)return type(v)=='number' and v==v and math.abs(v)<math.huge end
    probe('original_sensor_block',function()
            local p=u:getPosition().p
            local h=land.getHeight({x=p.x,y=p.z})
            local air=u:inAir()
            assert(type(air)=='boolean','Missing ground signal')
            local v={u:getID(),air and 1 or 0,h,p.y-h,u:getLife(),u:getLife0(),land.getSurfaceType({x=p.x,y=p.z})}
            for _,n in ipairs(v) do assert(finite(n),'Invalid ground evidence') end

        return 'all required sensor values passed'
    end)
    trigger.action.outText('Ground sensor check finished. Stay parked; no recording needed. Return to Codex.',40)
    log('DONE')
end,nil,timer.getTime()+5)
trigger.action.outText('Ground sensor diagnostic. Stay parked; the check runs automatically after Fly. No recording or taxi needed.',40)
