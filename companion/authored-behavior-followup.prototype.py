"""Throwaway editor comparison and same-name/new-ID object lifetime fixture."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('fixture', Path(__file__).with_name('authored-behavior-fixtures.prototype.py'))
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
p = f.p
root = Path(sys.argv[1])
before, bm = p.read(root/'031-Behavior-Prepared.miz')
saved_name = sys.argv[2] if len(sys.argv)>2 else '032-Behavior-Editor-Roundtrip.miz'
after, am = p.read(root/saved_name)

def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [d for k in sorted(set(a)|set(b),key=str) for d in (differences(a[k],b[k],path+'/'+str(k)) if k in a and k in b else [path+'/'+str(k)])]
    return [] if a==b else [path]

report = {'before_sha256':p.sha((root/'031-Behavior-Prepared.miz').read_bytes()),
    'after_sha256':p.sha((root/saved_name).read_bytes()),
    'mission_changed_paths':differences(bm,am),
    'source_trigrules_equal':bm['trigrules']==am['trigrules'],
    'aircraft_inventory_equal':p.aircraft(bm)==p.aircraft(am),
    'removed_members':sorted(set(before)-set(after)),
    'added_members':sorted(set(after)-set(before)),
    'changed_members':[k for k in before if k in after and before[k]!=after[k]],
    'authored_resource_bytes_equal':before['l10n/DEFAULT/behavior-authored.lua']==after.get('l10n/DEFAULT/behavior-authored.lua'),
    'recorder_resource_bytes_equal':before['l10n/DEFAULT/dcsr-probe-2.lua']==after.get('l10n/DEFAULT/dcsr-probe-2.lua'),
    'default_dictionary_equal':f.table(before['l10n/DEFAULT/dictionary'],'dictionary')==f.table(after['l10n/DEFAULT/dictionary'],'dictionary'),
    'default_resource_map_equal':f.table(before['l10n/DEFAULT/mapResource'],'mapResource')==f.table(after['l10n/DEFAULT/mapResource'],'mapResource')}
(root/(Path(saved_name).stem+'.comparison.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

entries = dict(before)
m = copy.deepcopy(bm)
g = copy.deepcopy(m['coalition']['blue']['country'][1]['plane']['group'][2])
g['groupId'],g['units'][1]['unitId'] = 10402,10502
script = '''-- Disposable stock-AI lifetime probe. Does not replace the player.
local oldUnit = Unit.getByName('BehaviorSelected')
local oldGroup = Group.getByName('BehaviorSelectedGroup')
local function value(o, method)
    if not o then return 'absent' end
    local ok,v = pcall(function() return o[method](o) end)
    return ok and tostring(v) or 'invalid'
end
local function report(label)
    local u=Unit.getByName('BehaviorSelected')
    local g=Group.getByName('BehaviorSelectedGroup')
    env.info('REPLACEMENT_BEHAVIOR '..label..' cached_unit_alive='..value(oldUnit,'isExist')..' cached_group_alive='..value(oldGroup,'isExist')..' current_unit='..value(u,'getID')..' current_group='..value(g,'getID'))
end
local events={}
function events:onEvent(e)
    local name=e.initiator and value(e.initiator,'getName') or ''
    if name=='BehaviorSelected' then
        env.info('REPLACEMENT_EVENT id='..tostring(e.id)..' unit='..value(e.initiator,'getID'))
    end
end
world.addEventHandler(events)
timer.scheduleFunction(function()
    report('before')
    oldGroup:destroy()
    report('removed')
    coalition.addGroup(2,Group.Category.AIRPLANE,REPLACEMENT_GROUP)
    report('replaced')
    return nil
end,nil,timer.getTime()+8)
timer.scheduleFunction(function() report('later');return nil end,nil,timer.getTime()+18)
'''.replace('REPLACEMENT_GROUP',p.serialize(g))
resources=f.table(entries['l10n/DEFAULT/mapResource'],'mapResource')
key='ResKey_DCSR_replacement_11002'
assert key not in resources
resources[key]='behavior-replacement.lua'
entries['l10n/DEFAULT/behavior-replacement.lua']=script.encode()
entries['l10n/DEFAULT/mapResource']=f.encoded('mapResource',resources)
m['maxDictId']=11002
f.add_start(m,4,key,'Disposable replacement lifetime diagnostic; not playback')
entries['mission']=f.encoded('mission',m)
destination=root/'033-Behavior-Replacement.miz'
data = f.packed(entries)
if destination.exists():
    if destination.read_bytes()!=data:
        raise ValueError('Existing replacement fixture differs; preserve it and choose a new output directory')
else:
    with destination.open('xb') as stream:
        stream.write(data)
(root/'behavior-replacement.lua').write_text(script)
print('Replacement fixture:',p.sha(destination.read_bytes()))
