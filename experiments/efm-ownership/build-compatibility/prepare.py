"""Package a read-only helper and a disposable one-stock-Hornet mission."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import zipfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('fixture_data',ROOT/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)

def prepare(source,output):
    if output.exists():raise ValueError('Use a fresh output directory')
    entries,m=data.read(source)
    rows=data.aircraft(m)
    if len(rows)!=1 or rows[0]['unit']['type']!='FA-18C_hornet' or rows[0]['unit']['skill']!='Player':
        raise ValueError('Requires the known single stock-Hornet identity fixture')
    script="env.info('DCSR_BUILD_MISSION_READY'); trigger.action.outText('Read-only compatibility capture. Wait ten seconds, then exit normally. No playback runs.',20)"
    m['trigrules']={1:dict(comment='Read-only build compatibility',predicate='triggerStart',eventlist='',rules={},
        actions={1:dict(predicate='a_do_script',text=script)})}
    m['trig']={key:{} for key in ('actions','conditions','func','funcStartup','flag')}
    m['trig']['actions'][1]='a_do_script('+data.serialize(script)+');'
    m['trig']['conditions'][1]='return(true)';m['trig']['flag'][1]=True
    m['trig']['funcStartup'][1]='if mission.trig.conditions[1]() then mission.trig.actions[1]() end'
    m['descriptionText']='READ-ONLY BUILD COMPATIBILITY. One stock Hornet; no custom playback aircraft. Click Fly, wait ten seconds, then exit normally. The separate helper captures only executable/read-only image sections from five DCS modules for compatibility analysis. No native methods, motion writes, memory patches or playback are requested.'
    output.mkdir(parents=True)
    with zipfile.ZipFile(output/'045-Build-Compatibility.miz','x',zipfile.ZIP_DEFLATED) as z:
        for name,raw in entries.items():z.writestr(name,('mission = '+data.serialize(m)).encode() if name=='mission' else raw)
    shutil.copy2(HERE/'hook.lua',output/'dcs-recorder-build-capture.lua')
    shutil.copy2(HERE.parent/'build/Release/BuildCompatibilityCapture.dll',output/'BuildCompatibilityCapture.dll')
    report=dict(status='Read-only capture prepared; live evidence pending',files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()})
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    data.read(output/'045-Build-Compatibility.miz')
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    prepare(a.source,a.output)
