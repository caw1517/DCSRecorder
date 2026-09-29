"""Install only the new wheel experiment after DCS is closed."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from prepare_playback import MODULE,BINARY,MISSION,ANIMATION_VARIANT


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def install(package,saved):
    package=package.resolve();saved=saved.resolve()
    tasklist=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq DCS.exe','/FO','CSV','/NH'],
        capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if '"dcs.exe"' in tasklist.stdout.lower():raise ValueError('Close DCS to load the new aircraft module on restart')
    manifest=json.loads((package/'manifest.json').read_text())
    variant=(manifest['module'],manifest['binary'],manifest['mission'])
    assert variant in ((MODULE,BINARY,MISSION),ANIMATION_VARIANT)
    module,binary,mission_name=variant
    protected=[]
    for root in (saved/'Scripts',saved/'DCSRecorder/recordings',saved/'Mods/aircraft'):
        protected += [p for p in root.rglob('*') if p.is_file() and
            p.suffix.lower() in ('.lua','.dll','.txt','.csv','.json') and
            'state-logs' not in p.parts and module not in p.parts]
    protected += list((saved/'Missions').glob('DCSRecorder-*.miz'))
    before={str(p):digest(p) for p in protected}
    plans=[]
    assert module+'/bin/'+binary+'.dll' in manifest['files'] and mission_name in manifest['files']
    for relative,expected in manifest['files'].items():
        rel=Path(relative);source=(package/rel).resolve()
        assert source.is_relative_to(package) and digest(source)==expected
        if rel.parts[0]==module:
            assert 'state-logs' not in rel.parts
            target=saved/'Mods/aircraft'/rel
        else:
            assert relative==mission_name
            target=saved/'Missions'/rel
        assert target.resolve().is_relative_to(saved)
        if target.exists() and digest(target)!=expected:raise ValueError('Existing different file: '+str(target))
        plans.append((source,target,expected))
    for source,target,expected in plans:
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with target.open('xb')as stream:stream.write(source.read_bytes())
        assert digest(target)==expected
    assert before=={str(p):digest(p) for p in protected}
    report=dict(installed={str(t):h for _,t,h in plans},protected_unchanged=before)
    (package/'installation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS: {len(plans)} installed hashes; {len(before)} protected files unchanged')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('package',type=Path);parser.add_argument('saved_games',type=Path)
    args=parser.parse_args();install(args.package,args.saved_games)
