"""Replace only the existing isolated sound-test DLL, with an exact-hash backup."""
import argparse
import json
import os
import subprocess
from pathlib import Path
from install import digest

MODULE='DCSRecorder-Hornet-Sounder-Test'
BINARY='HornetEngineSounderProbe.dll'

def closed():
    result=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq DCS.exe','/FO','CSV','/NH'],
        capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if '"dcs.exe"' in result.stdout.lower():raise ValueError('Close DCS before replacing its diagnostic DLL')

def install(source,package,saved,output):
    closed()
    source=source.resolve();saved=saved.resolve();output=output.resolve()
    assert source.name==BINARY
    manifest=json.loads((package/'manifest.json').read_text())
    assert manifest['module']==MODULE
    target=saved/'Mods/aircraft'/MODULE/'bin'/BINARY
    expected=manifest['files'][MODULE+'/bin/'+BINARY]
    assert target.resolve().is_relative_to(saved)
    assert digest(target)==expected,'Installed DLL differs from the original sound-test manifest'
    replacement=source.read_bytes();new_hash=digest(source)
    assert new_hash!=expected
    protected=list((saved/'Scripts').glob('*.lua'))+list((saved/'Scripts/Hooks').glob('*.lua'))
    protected+=list((saved/'DCSRecorder/recordings').glob('*.csv'))
    for module in ('DCSRecorder-Hornet-Staged','DCSRecorder-Hornet-State-Staged',
                   'DCSRecorder-Hornet-Engine-Appearance','DCSRecorder-Hornet-Engine-Sound-Probe',MODULE):
        protected += [p for p in (saved/'Mods/aircraft'/module).rglob('*')
                      if p.is_file() and p.suffix in ('.lua','.dll','.txt') and p!=target]
    protected.append(saved/'Missions/DCSRecorder-Sound-Routing-Test.miz')
    before={str(p):digest(p) for p in protected}
    output.mkdir(parents=True,exist_ok=False)
    backup=output/BINARY
    with backup.open('xb') as stream:stream.write(target.read_bytes())
    assert digest(backup)==expected
    temporary=target.with_suffix('.dll.pending')
    with temporary.open('xb') as stream:stream.write(replacement)
    assert digest(temporary)==new_hash
    closed()
    assert digest(target)==expected
    os.replace(temporary,target)
    assert digest(target)==new_hash
    assert before=={p:digest(Path(p)) for p in before}
    report={'target':str(target),'old_sha256':expected,'new_sha256':new_hash,
            'backup':str(backup),'protected_unchanged':before}
    (output/'installation.json').write_text(json.dumps(report,indent=2))
    print(f'PASS: isolated diagnostic DLL backed up and replaced; {len(before)} protected hashes unchanged')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('source','package','saved_games','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();install(args.source,args.package,args.saved_games,args.output)
