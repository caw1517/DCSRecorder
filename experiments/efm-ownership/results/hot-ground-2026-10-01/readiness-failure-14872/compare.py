from pathlib import Path
import importlib.util,json,zipfile
root=Path(__file__).resolve().parent
repo=Path('E:/Projects/DCS_Recorder')
spec=importlib.util.spec_from_file_location('data',repo/'companion/mission-identity-probe.prototype.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
package=repo/'experiments/efm-ownership/results/hot-ground-2026-10-01/ground-release-package'
p=data.LuaData((package/'payload/Scripts/DCSRecorderGroundControl/expected.lua').read_text(encoding='utf-8'));p.take('return');expected=p.value()
with zipfile.ZipFile(root/'raw/loaded-tempMission.miz') as z:loaded=data.LuaData(z.read('mission').decode('utf-8-sig')).mission()
diff=[]
def compare(a,b,path):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(a.keys()|b.keys(),key=str):compare(a.get(k),b.get(k),path+[k])
    elif a!=b or type(a)!=type(b) and not (isinstance(a,(float,int)) and isinstance(b,(float,int))):
        diff.append(dict(path=path,expected=a,loaded=b,delta=b-a if type(a) in (int,float) and type(b) in (int,float) else None))
for field in expected['fields'].values():compare(expected['mission'][field],loaded.get(field),[field])
(root/'differences.json').write_text(json.dumps(diff,indent=2)+'\n')
(root/'loaded-reference.lua').write_text('mission = '+data.serialize(loaded),encoding='utf-8')
print(json.dumps(diff,indent=2))
