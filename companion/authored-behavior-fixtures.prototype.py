"""Throwaway known-fixture preservation probe; not a general mission preparer.

Usage: python authored-behavior-fixtures.prototype.py INPUT.miz NEW_OUTPUT_DIR
Reads mission Lua as data. Creates source/prepared stock-aircraft controls only.
"""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('identity', Path(__file__).with_name('mission-identity-probe.prototype.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def table(data, variable):
    parser = p.LuaData(data.decode('utf-8-sig'))
    parser.take(variable)
    parser.take('=')
    result = parser.value()
    parser.skip()
    if parser.pos != len(parser.text):
        raise ValueError('Unsupported trailing data')
    return result

def encoded(variable, data):
    return (variable + ' = ' + p.serialize(data) + '\n').encode('utf-8')

def packed(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 9, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return buf.getvalue()

def add_start(mission, index, key, comment):
    mission['trigrules'][index] = {'comment':comment, 'predicate':'triggerStart', 'eventlist':'', 'rules':{},
        'actions':{1:{'predicate':'a_do_script_file', 'file':key}}}
    mission['trig']['actions'][index] = 'a_do_script_file(getValueResourceByKey(' + p.serialize(key) + '));'
    mission['trig']['conditions'][index] = 'return(true)'
    mission['trig']['flag'][index] = True
    mission['trig']['funcStartup'][index] = f'if mission.trig.conditions[{index}]() then mission.trig.actions[{index}]() end'

AUTHORED = '''-- Known authored fixture: read aircraft references; change only authored flags.
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
'''

def make_source(input_path):
    entries, m = p.read(input_path)
    m = copy.deepcopy(m)
    original = m['coalition']['blue']['country'][1]['plane']['group'][1]
    groups = {}
    for i, (name, skill) in enumerate([('BehaviorObserver','Player'), ('BehaviorSelected','High'), ('BehaviorUnrelated','High')], 1):
        g = copy.deepcopy(original)
        u = g['units'][1]
        g['groupId'], u['unitId'] = 10200+i, 10300+i
        g['name'], u['name'] = name+'Group', name
        u['skill'] = skill
        g['lateActivation'], g['uncontrolled'] = False, False
        dx = (i-1)*1500
        g['x'] += dx
        u['x'] += dx
        for point in g['route']['points'].values():
            point['x'] += dx
            point['task'] = {'id':'ComboTask','params':{'tasks':{}}}
        groups[i] = g
    m['coalition']['blue']['country'][1]['plane']['group'] = groups
    m['trigrules'] = {}
    m['trig'] = {k:{} for k in ('actions','conditions','func','funcStartup','flag')}
    m['descriptionText'] = 'DictKey_behavior_description'
    m['descriptionBlueTask'] = 'DictKey_behavior_task'
    dictionary = table(entries['l10n/DEFAULT/dictionary'], 'dictionary')
    dictionary.update(DictKey_behavior_description='AUTHORED BEHAVIOR CONTROL: three stock Hornets; no recording or playback. Click Fly and wait about 25 seconds for the completion message.', DictKey_behavior_task='Authored briefing preserved in source and prepared control.')
    resources = table(entries.get('l10n/DEFAULT/mapResource',b'mapResource = {}'), 'mapResource')
    key = 'ResKey_behavior_authored_1'
    if key in resources or 'l10n/DEFAULT/behavior-authored.lua' in entries:
        raise ValueError('Fixture resource already exists')
    resources[key] = 'behavior-authored.lua'
    entries['l10n/DEFAULT/behavior-authored.lua'] = AUTHORED.encode()
    add_start(m, 1, key, 'Authored resource script: flag and aircraft references')
    m['trigrules'][2] = {'comment':'Authored timed unit/group references', 'predicate':'triggerOnce', 'eventlist':'',
        'rules':{1:{'predicate':'c_time_after','seconds':5},2:{'predicate':'c_unit_alive','unit':10302},3:{'predicate':'c_group_alive','group':10202}},
        'actions':{1:{'predicate':'a_set_flag_value','flag':'AUTHORED_NATIVE_FLAG','value':17}}}
    m['trig']['conditions'][2] = 'return(c_time_after(5) and c_unit_alive(10302) and c_group_alive(10202))'
    m['trig']['actions'][2] = 'a_set_flag_value("AUTHORED_NATIVE_FLAG",17); mission.trig.func[2]=nil;'
    m['trig']['func'][2] = 'if mission.trig.conditions[2]() then mission.trig.actions[2]() end'
    m['trig']['flag'][2] = True
    m['maxDictId'] = max(int(m.get('maxDictId',0)), 11000)
    entries['mission'] = encoded('mission',m)
    entries['l10n/DEFAULT/dictionary'] = encoded('dictionary',dictionary)
    entries['l10n/DEFAULT/mapResource'] = encoded('mapResource',resources)
    return entries, m

def prepare(source):
    if 'DCSRecorderBehaviorProbe/manifest.json' in source:
        raise ValueError('Use the immutable authored source, not a generated output')
    entries = dict(source)
    m = p.LuaData(entries['mission'].decode()).mission()
    resources = table(entries['l10n/DEFAULT/mapResource'], 'mapResource')
    # This bounded allocator inspects the known fixture; it cannot prove absence
    # of dynamically constructed identifiers in arbitrary authored Lua.
    text = '\n'.join(v.decode('utf-8',errors='replace') for k,v in entries.items() if k.endswith('.lua') or k=='mission')
    n = 1
    while f'DCSR_PROBE_{n}' in text or f'l10n/DEFAULT/dcsr-probe-{n}.lua' in entries:
        n += 1
    flag = f'DCSR_PROBE_{n}_READY'
    m['maxDictId'] += 1
    key = f'ResKey_DCSR_probe_{m["maxDictId"]}'
    while key in resources:
        m['maxDictId'] += 1
        key = f'ResKey_DCSR_probe_{m["maxDictId"]}'
    filename = f'dcsr-probe-{n}.lua'
    resources[key] = filename
    script = "trigger.action.setUserFlag('"+flag+"',1)\nenv.info('PREPARED_BEHAVIOR owned_flag="+flag+" authored_flag='..trigger.misc.getUserFlag('DCSR_PROBE_1_READY'))\n"
    entries['l10n/DEFAULT/'+filename] = script.encode()
    index = max([*m['trigrules'], *(i for t in m['trig'].values() for i in t)])+1
    add_start(m,index,key,'Recorder-owned read-only preparation control; no playback')
    entries['mission'] = encoded('mission',m)
    entries['l10n/DEFAULT/mapResource'] = encoded('mapResource',resources)
    manifest = {'prototype_only':True,'source_sha256':p.sha(packed(source)), 'trigger_index':index,'resource_key':key,'owned_flag':flag,'resource':filename}
    entries['DCSRecorderBehaviorProbe/manifest.json'] = json.dumps(manifest,sort_keys=True).encode()
    return entries,m,manifest

if __name__ == '__main__':
    source_path,out = map(Path,sys.argv[1:3])
    out.mkdir(parents=True,exist_ok=False)
    source,sm = make_source(source_path)
    prepared,pm,manifest = prepare(source)
    again,_,_ = prepare(source)
    # Record observed structure, not a general semantic-preservation claim.
    restored = copy.deepcopy(pm)
    restored['maxDictId'] = sm['maxDictId']
    del restored['trigrules'][manifest['trigger_index']]
    for section in restored['trig'].values():
        section.pop(manifest['trigger_index'],None)
    changed = [k for k in source if source[k] != prepared[k]]
    report = {'status':'structural controls only; live evidence pending','mission_after_removing_owned_additions_equals_source':restored==sm,
        'changed_existing_members':changed,'added_members':sorted(set(prepared)-set(source)),
        'authored_resource_bytes_equal':source['l10n/DEFAULT/behavior-authored.lua']==prepared['l10n/DEFAULT/behavior-authored.lua'],
        'briefing_dictionary_bytes_equal':source['l10n/DEFAULT/dictionary']==prepared['l10n/DEFAULT/dictionary'],
        'reprepare_from_same_source_byte_identical':packed(prepared)==packed(again),'manifest':manifest}
    for name,data in [('030-Behavior-Source',source),('031-Behavior-Prepared',prepared)]:
        archive = packed(data)
        (out/(name+'.miz')).write_bytes(archive)
        report[name+'_sha256'] = p.sha(archive)
    (out/'structural-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
