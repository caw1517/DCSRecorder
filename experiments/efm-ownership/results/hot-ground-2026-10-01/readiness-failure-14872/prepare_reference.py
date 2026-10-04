from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
root=Path(__file__).resolve().parent
repo=Path('E:/Projects/DCS_Recorder')
spec=importlib.util.spec_from_file_location('data',repo/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
seed=repo/'experiments/efm-ownership/results/hot-ground-2026-10-01/ground-release-package'
out=root/'corrected-package'
changes=json.loads((root/'differences.json').read_text())
prefix=['coalition','blue','country',1,'plane','group',3,'route','points',2]
assert {tuple(d['path']) for d in changes}=={tuple(prefix+[k]) for k in ('x','y','ETA')}
for d in changes:
    assert d['loaded']==float(format(d['expected'],'.14g')),'Not the observed 14-significant-digit serialization'
manifest=json.loads((seed/'manifest.json').read_text())
for name,sha in manifest['files'].items():assert hashlib.sha256((seed/'payload'/name).read_bytes()).hexdigest()==sha
shutil.copytree(seed,out)
ref=out/'payload/Scripts/DCSRecorderGroundControl/expected.lua'
p=data.LuaData(ref.read_text(encoding='utf-8'));p.take('return');expected=p.value()
for d in changes:
    parent=expected['mission']
    for key in d['path'][:-1]:parent=parent[key]
    assert parent[d['path'][-1]]==d['expected']
    parent[d['path'][-1]]=d['loaded']
ref.write_text('return '+data.serialize(expected)+'\n',encoding='utf-8')
relative=ref.relative_to(out/'payload').as_posix()
manifest['files'][relative]=hashlib.sha256(ref.read_bytes()).hexdigest()
manifest['reference_repair']=dict(changes=changes,captured_archive_sha256=hashlib.sha256((root/'raw/loaded-tempMission.miz').read_bytes()).hexdigest(),runtime_comparison='Exact and unchanged')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared exact reference repair for the three measured witness-route serialization changes')
