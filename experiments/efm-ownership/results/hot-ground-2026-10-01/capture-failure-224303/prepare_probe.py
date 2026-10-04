import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
REPO=Path('E:/Projects/DCS_Recorder')
spec=importlib.util.spec_from_file_location('mission_data',REPO/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
source=REPO/'experiments/efm-ownership/results/hot-ground-2026-10-01/capture-package/047-Hornet-Hot-Ground-Capture.miz'
with zipfile.ZipFile(source) as z:
    m=data.LuaData(z.read('mission').decode('utf-8-sig')).mission()
contact=(REPO/'experiments/efm-ownership/ground-start/contact.lua').read_text()
block=contact.split('local ok,values=pcall(function()\n',1)[1].split('            return v',1)[0]
script=(HERE/'sensor_probe.lua').read_text().replace('__ORIGINAL_SENSOR_BLOCK__',block)
m['descriptionText']='Read-only ground sensor diagnostic. Click Fly and stay parked. The check runs after five seconds. No recording or taxi required.'
m['trigrules'][1]['comment']='Temporary ground sensor boundary check'
m['trigrules'][1]['actions'][1]['text']=script
m['trig']['actions'][1]='a_do_script('+data.serialize(script)+');'
out=HERE/'sensor-package';out.mkdir(exist_ok=False)
(out/'mission.lua').write_text('mission = '+data.serialize(m))
(out/'probe.lua').write_text(script)
lua='D:/DCS World/bin/luae.exe'
check=out/'check.lua'
check.write_text("assert(loadfile(arg[1]));dofile(arg[2]);local nested;function a_do_script(s) nested=s end;assert(loadstring(mission.trig.actions[1]))();assert(nested==mission.trigrules[1].actions[1].text);assert(loadstring(nested));print('PASS: probe and both packaged trigger representations compile and match')")
subprocess.run([lua,str(check),str(out/'probe.lua'),str(out/'mission.lua')],check=True)
mission=out/'048-Hornet-Ground-Sensor-Check.miz'
with zipfile.ZipFile(source) as src,zipfile.ZipFile(mission,'x',zipfile.ZIP_DEFLATED) as dst:
    for entry in src.infolist():dst.writestr(entry,(out/'mission.lua').read_bytes() if entry.filename=='mission' else src.read(entry.filename))
manifest=dict(mission=mission.name,sha256=hashlib.sha256(mission.read_bytes()).hexdigest(),source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Temporary read-only sensor diagnosis; no recorder, native hooks, or control changes')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
