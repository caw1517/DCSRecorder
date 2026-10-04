-- Known authored fixture: read aircraft references; change only authored flags.
local selectedAtStart = Unit.getByName('BehaviorSelected')
local groupAtStart = Group.getByName('BehaviorSelectedGroup')
trigger.action.setUserFlag('DCSR_PROBE_1_READY', 73) -- deliberately occupied name
trigger.action.setUserFlag('AUTHORED_COUNTER', 0)
local function sample(_, now)
    local selected = Unit.getByName('BehaviorSelected')
    local other = Unit.getByName('BehaviorUnrelated')
    local group = Group.getByName('BehaviorSelectedGroup')
    local count = trigger.misc.getUserFlag('AUTHORED_COUNTER') + 1
    trigger.action.setUserFlag('AUTHORED_COUNTER', count)
    local function id(o) return o and o:isExist() and tostring(o:getID()) or 'absent' end
    local function alive(o) return o and o:isExist() and 'true' or 'false' end
    local pos = other and other:isExist() and other:getPoint() or {x=0,z=0}
    env.info('AUTHORED_BEHAVIOR count='..count..' selected='..id(selected)..' group='..id(group)..' unrelated='..id(other)..' cached_selected_alive='..alive(selectedAtStart)..' cached_group_alive='..alive(groupAtStart)..' occupied_flag='..trigger.misc.getUserFlag('DCSR_PROBE_1_READY')..' native_flag='..trigger.misc.getUserFlag('AUTHORED_NATIVE_FLAG')..' unrelated_x='..pos.x..' unrelated_z='..pos.z)
    if count == 3 then trigger.action.outText('Authored behavior probe complete. You may exit.', 30); return nil end
    return now + 10
end
timer.scheduleFunction(sample, nil, timer.getTime()+2)
