"""Add a read-only diagnostic helper/hook; preserve all existing game artifacts."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser()
parser.add_argument('saved_games',type=Path)
parser.add_argument('report',type=Path)
parser.add_argument('--dcs',type=Path,default=Path('D:/DCS World'))
args=parser.parse_args()
saved=args.saved_games.resolve()
assert json.loads((args.dcs/'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version']=='2.9.29.27468'
processes=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq DCS.exe','/FO','CSV','/NH'],
    text=True,capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
if '"dcs.exe"'in processes.stdout.lower():raise RuntimeError('Close DCS before installing the capture helper')
assert (saved/'Missions/DCSRecorder-Engine-State-Diagnostic.miz').is_file()
assert (saved/'Scripts/Hooks/dcs-recorder-engine-diagnostic.lua').is_file()
plans=[(ROOT/'build/Release/NativeEngineCapture.dll',saved/'Scripts/DCSRecorderEngineCapture/NativeEngineCapture.dll'),
       (ROOT/'engine-prototype/native_capture_hook.lua',saved/'Scripts/Hooks/dcs-recorder-native-engine-capture.lua')]
for source,target in plans:
    assert source.is_file() and target.resolve().is_relative_to(saved)
    if target.exists() and digest(target)!=digest(source):raise RuntimeError('Different existing helper: '+str(target))
protected=list((saved/'Scripts').rglob('*.lua'))+list((saved/'Missions').glob('*.miz'))
protected+=list((saved/'DCSRecorder/recordings').glob('*.csv'))
protected+=[p for p in (saved/'Mods/aircraft').rglob('*')if p.is_file()and (p.suffix in ('.dll','.lua')or p.name.startswith('recorded-flight.'))]
before={str(p):digest(p)for p in protected}
for source,target in plans:
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        with target.open('xb')as f:f.write(source.read_bytes())
    assert digest(target)==digest(source)
assert before=={str(p):digest(p)for p in protected}
args.report.parent.mkdir(parents=True,exist_ok=True)
args.report.write_text(json.dumps({'installed':{str(t):digest(t)for _,t in plans},'protected_unchanged':before},indent=2))
print(f'PASS: 2 new diagnostic files installed; {len(before)} protected hashes unchanged')
