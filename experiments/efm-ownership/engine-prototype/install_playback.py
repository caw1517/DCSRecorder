"""Install the new isolated engine module/mission; never replace an existing variant."""
import argparse
import json
import subprocess
from pathlib import Path
from install import digest
from prepare_playback import MODULE


def install(package,saved):
    package=package.resolve();saved=saved.resolve()
    result=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq DCS.exe','/FO','CSV','/NH'],
        capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if '"dcs.exe"' in result.stdout.lower():raise ValueError('Close DCS before installing the engine module')
    manifest=json.loads((package/'manifest.json').read_text())
    assert manifest['module']==MODULE
    protected=[saved/'Scripts/Export.lua',saved/'Scripts/Hooks/dcs-recorder-autosave.lua',
               saved/'Scripts/Hooks/dcs-recorder-engine-diagnostic.lua']
    protected+=list((saved/'DCSRecorder/recordings').glob('*.csv'))
    for module in ('DCSRecorder-Hornet-Staged','DCSRecorder-Hornet-State-Staged'):
        binary=saved/'Mods/aircraft'/module/'bin'
        protected+=list(binary.glob('*.dll'))+list(binary.glob('recorded-flight.*'))
    before={str(p):digest(p) if p.exists() else None for p in protected}
    plans=[]
    for relative,expected in manifest['files'].items():
        rel=Path(relative);source=(package/rel).resolve()
        assert source.is_relative_to(package) and digest(source)==expected
        if rel.parts[0]==MODULE: target=saved/'Mods/aircraft'/rel
        else:
            assert relative=='DCSRecorder-Engine-Appearance-Playback.miz'
            target=saved/'Missions'/rel
        assert target.resolve().is_relative_to(saved)
        if target.exists() and digest(target)!=expected:raise ValueError('Existing different file: '+str(target))
        plans.append((source,target,expected))
    for source,target,expected in plans:
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream:stream.write(source.read_bytes())
        assert digest(target)==expected
    assert before=={str(p):digest(p) if p.exists() else None for p in protected}
    report={'installed':{str(t):h for _,t,h in plans},'protected_unchanged':before}
    (package/'installation.json').write_text(json.dumps(report,indent=2))
    print(f'PASS: {len(plans)} installed hashes; {len(before)} protected files unchanged')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('package',type=Path);parser.add_argument('saved_games',type=Path)
    args=parser.parse_args();install(args.package,args.saved_games)
