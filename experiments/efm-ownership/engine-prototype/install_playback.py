"""Install the new isolated engine module/mission; never replace an existing variant."""
import argparse
import json
import subprocess
from pathlib import Path
from install import digest
from prepare_playback import VARIANTS


def install(package,saved):
    package=package.resolve();saved=saved.resolve()
    result=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq DCS.exe','/FO','CSV','/NH'],
        capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if '"dcs.exe"' in result.stdout.lower():raise ValueError('Close DCS before installing the engine module')
    manifest=json.loads((package/'manifest.json').read_text())
    module=manifest['module']
    assert module in VARIANTS
    binary,mission_name=VARIANTS[module]
    assert manifest['binary']==binary
    protected=[saved/'Scripts/Export.lua',saved/'Scripts/Hooks/dcs-recorder-autosave.lua',
               saved/'Scripts/Hooks/dcs-recorder-engine-diagnostic.lua']
    protected+=list((saved/'DCSRecorder/recordings').glob('*.csv'))
    for module in ('DCSRecorder-Hornet-Staged','DCSRecorder-Hornet-State-Staged'):
        binary=saved/'Mods/aircraft'/module/'bin'
        protected+=list(binary.glob('*.dll'))+list(binary.glob('recorded-flight.*'))
    protected+=list((saved/'Mods/aircraft/DCSRecorder-Hornet-Engine-Appearance').rglob('*'))
    protected+=list((saved/'Scripts/Hooks').glob('*.lua'))
    for name in ('DCSRecorder-Hornet-Engine-Sound-Probe','DCSRecorder-Hornet-Sounder-Test','DCSRecorder-Hornet-Audibility-Test','DCSRecorder-Hornet-Native-RPM','DCSRecorder-Hornet-Native-Engine'):
        protected += [p for p in (saved/'Mods/aircraft'/name).rglob('*')
                      if p.is_file() and p.suffix in ('.lua','.dll','.txt')]
    protected+=list((saved/'Missions').glob('DCSRecorder-*Sound*.miz'))
    protected+=list((saved/'Missions').glob('DCSRecorder-Native-RPM*.miz'))
    protected+=list((saved/'Missions').glob('DCSRecorder-Native-Engine*.miz'))
    protected+=list((saved/'Scripts/DCSRecorderEngineCapture').glob('*.dll'))
    protected=[p for p in protected if not p.is_dir()]
    module=manifest['module']
    before={str(p):digest(p) if p.exists() else None for p in protected}
    plans=[]
    for relative,expected in manifest['files'].items():
        rel=Path(relative);source=(package/rel).resolve()
        assert source.is_relative_to(package) and digest(source)==expected
        if rel.parts[0]==module: target=saved/'Mods/aircraft'/rel
        else:
            assert relative==mission_name
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
