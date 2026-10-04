"""Bind this fixed diagnostic to a reviewed DCS-serialized mission reference.

The source mission/DLL/tape are unchanged. Only bounded, measured serialization
changes can enter the reference; runtime comparison remains exact.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('fixture_data',ROOT/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
FIELDS=('theatre','weather','coalition','trigrules','date','start_time','forcedOptions')
REFERENCE='Scripts/DCSRecorderReleaseControl/expected.lua'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        result=[]
        for k in sorted(a.keys()|b.keys(),key=str):result.extend(differences(a.get(k),b.get(k),path+'['+str(k)+']'))
        return result
    return [] if type(a)==type(b) and a==b or isinstance(a,(int,float)) and isinstance(b,(int,float)) and a==b else [path]

def validate_roundtrip(original,loaded):
    reviewed=copy.deepcopy(original)
    allowed=[]
    groups=reviewed['coalition']['blue']['country'][1]['plane']['group']
    actual_groups=loaded['coalition']['blue']['country'][1]['plane']['group']
    for group_id,group in groups.items():
        for unit_index,unit in group['units'].items():
            actual=actual_groups[group_id]['units'][unit_index]
            prefix=f'coalition[blue][country][1][plane][group][{group_id}][units][{unit_index}]'
            for key in ('heading','psi'):
                if unit[key]!=actual.get(key):
                    delta=abs(unit[key]-actual[key])
                    if not math.isfinite(delta) or delta>1e-12:raise ValueError('Non-serialization attitude change: '+prefix+'['+key+']')
                    # Precision bound for this reference preparation only,
                    # never a playback acceptance tolerance or live comparator.
                    unit[key]=actual[key];allowed.append(dict(path=prefix+'['+key+']',kind='angle_serialization',delta=delta))
            cartridge=unit.get('dataCartridge')
            if cartridge is not None and 'dataCartridge' not in actual:
                if set(cartridge)!={'GroupsPoints','Points'} or cartridge['Points']!={} or any(v!={} for v in cartridge['GroupsPoints'].values()):
                    raise ValueError('Nonempty cartridge data would be lost')
                del unit['dataCartridge'];allowed.append(dict(path=prefix+'[dataCartridge]',kind='empty_cartridge_omitted'))
            if unit['skill'] not in ('Player','Client') and 'Radio' in unit and 'Radio' not in actual:
                del unit['Radio'];allowed.append(dict(path=prefix+'[Radio]',kind='non_player_radio_omitted'))
            elif isinstance(unit.get('Radio'),dict) and isinstance(actual.get('Radio'),dict):
                for radio_id,radio in unit['Radio'].items():
                    loaded_radio=actual['Radio'][radio_id]
                    if 'channelsNames' not in radio and loaded_radio.get('channelsNames')=={}:
                        radio['channelsNames']={};allowed.append(dict(path=prefix+f'[Radio][{radio_id}][channelsNames]',kind='empty_radio_labels_added'))
    unexpected=[]
    for field in FIELDS:unexpected.extend(differences(reviewed[field],loaded.get(field),field))
    if unexpected:raise ValueError('Unreviewed loaded changes: '+', '.join(unexpected))
    return allowed

def read_mission(path):
    with zipfile.ZipFile(path) as z:
        mission=data.LuaData(z.read('mission').decode('utf-8-sig')).mission()
        p=data.LuaData(z.read('l10n/DEFAULT/dictionary').decode('utf-8-sig'));p.take('dictionary');p.take('=');dictionary=p.value()
    return mission,dictionary.get(mission['descriptionText'],mission['descriptionText'])

def prepare(package,captured,output,dcs):
    package,output=package.resolve(),output.resolve()
    if output.exists():raise ValueError('Use a fresh package directory')
    manifest=json.loads((package/'manifest.json').read_text(encoding='utf-8-sig'))
    if manifest['profile']!='release-airborne-v1' or manifest['module']!='DCSRecorder-Hornet-Release-Test':raise ValueError('Unsupported package')
    for name,sha in manifest['files'].items():
        source=(package/'payload'/name).resolve()
        if not source.is_relative_to(package/'payload') or digest(source)!=sha:raise ValueError('Package hash mismatch: '+name)
    original=data.LuaData((package/'mission.lua').read_text(encoding='utf-8')).mission()
    loaded,description=read_mission(captured)
    allowed=validate_roundtrip(original,loaded)
    parser=data.LuaData((package/'payload'/REFERENCE).read_text(encoding='utf-8'));parser.take('return');expected=parser.value()
    if description!=expected['description']:raise ValueError('Loaded briefing changed')
    shutil.copytree(package,output)
    expected['mission']={field:loaded[field] for field in FIELDS}
    (output/'payload'/REFERENCE).write_text('return '+data.serialize(expected)+'\n',encoding='utf-8')
    (output/'loaded-reference.lua').write_text('mission = '+data.serialize(loaded),encoding='utf-8')
    report=dict(source_package=str(package),source_manifest_sha256=digest(package/'manifest.json'),
        captured_archive=str(captured.resolve()),captured_archive_sha256=digest(captured),reviewed_changes=allowed,
        runtime_comparison='Exact; no ignored keys or numerical tolerance',changed_payload_files=[REFERENCE])
    (output/'normalization-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    manifest['files'][REFERENCE]=digest(output/'payload'/REFERENCE)
    manifest['serialized_reference']=report
    manifest['status']='Prepared from reviewed DCS serialization; live readiness/release still pending'
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    subprocess.run([str(dcs/'bin/luae.exe'),str(HERE/'check_loaded_defaults.lua'),str(ROOT),str(output),str(dcs),str(output/'loaded-reference.lua')],check=True)
    print(json.dumps(dict(status=manifest['status'],reviewed_changes=len(allowed),changed_payload_files=[REFERENCE]),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('captured',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--dcs',type=Path,default=Path('D:/DCS World'));a=p.parse_args();prepare(a.package,a.captured,a.output,a.dcs)
