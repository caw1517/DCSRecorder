"""Install only the two separate diagnostic files, while DCS is closed."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(package, saved):
    processes=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq DCS.exe','/FO','CSV','/NH'],
        capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if '"dcs.exe"' in processes.stdout.lower():
        raise ValueError('Close DCS before installing the engine diagnostic.')
    manifest=json.loads((package/'manifest.json').read_text())
    destinations={
        'DCSRecorder-Engine-State-Diagnostic.miz':saved/'Missions/DCSRecorder-Engine-State-Diagnostic.miz',
        'dcs-recorder-engine-diagnostic.lua':saved/'Scripts/Hooks/dcs-recorder-engine-diagnostic.lua'}
    protected=[saved/'Scripts/Export.lua',saved/'Scripts/Hooks/dcs-recorder-autosave.lua']
    for module in ('DCSRecorder-Hornet-Staged','DCSRecorder-Hornet-State-Staged'):
        binary=saved/'Mods/aircraft'/module/'bin'
        protected+=list(binary.glob('*.dll'))+list(binary.glob('recorded-flight.*'))
    before={str(path):digest(path) if path.exists() else None for path in protected}
    for name,target in destinations.items():
        if digest(package/name)!=manifest['files'][name]: raise ValueError('Package hash mismatch: '+name)
        if target.exists() and digest(target)!=manifest['files'][name]:
            raise ValueError('Refusing to overwrite a different diagnostic: '+str(target))
    for name,target in destinations.items():
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream: stream.write((package/name).read_bytes())
        assert digest(target)==manifest['files'][name]
    assert before=={str(path):digest(path) if path.exists() else None for path in protected}
    result={'installed':{str(target):digest(target) for target in destinations.values()},'protected_unchanged':before}
    (package/'installation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'installed':list(result['installed']),'protected_files_unchanged':len(before)},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('package',type=Path)
    parser.add_argument('saved_games',type=Path)
    args=parser.parse_args()
    install(args.package,args.saved_games)
