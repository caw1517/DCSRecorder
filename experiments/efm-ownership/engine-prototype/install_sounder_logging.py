"""Install one temporary logging hook; preserve the actual audio experiment."""
import argparse
import json
import os
import subprocess
from pathlib import Path
from install import digest

def install(saved,report,previous_report=None):
    saved=saved.resolve()
    result=subprocess.run(['tasklist.exe','/FI','IMAGENAME eq DCS.exe','/FO','CSV','/NH'],
        capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if '"dcs.exe"' in result.stdout.lower():raise ValueError('Close DCS before installing the logging hook')
    source=Path(__file__).with_name('sounder_logging_hook.lua')
    target=saved/'Scripts/Hooks/dcs-recorder-sounder-logging.lua'
    replacing=target.exists() and digest(source)!=digest(target)
    previous=None
    if replacing:
        if previous_report is None:raise ValueError('Different existing hook; previous installation report required')
        previous=json.loads(previous_report.read_text())
        assert Path(previous['hook']).resolve()==target.resolve()
        assert digest(target)==previous['sha256'],'Previous installed hook hash mismatch'
        assert not report.exists(),'Use a new report path'
    protected=list((saved/'Scripts').glob('*.lua'))+list((saved/'Scripts/Hooks').glob('*.lua'))
    protected+=list((saved/'DCSRecorder/recordings').glob('*.csv'))
    for name in ('DCSRecorder-Hornet-Staged','DCSRecorder-Hornet-State-Staged',
                 'DCSRecorder-Hornet-Engine-Appearance','DCSRecorder-Hornet-Sounder-Test'):
        protected += [p for p in (saved/'Mods/aircraft'/name).rglob('*') if p.is_file() and p.suffix in ('.lua','.dll','.txt')]
    mission=saved/'Missions/DCSRecorder-Sound-Routing-Test.miz'
    protected.append(mission)
    before={str(p):digest(p) for p in protected if p!=target}
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        with target.open('xb') as stream:stream.write(source.read_bytes())
    elif replacing:
        backup=report.with_suffix('.previous.lua')
        with backup.open('xb') as stream:stream.write(target.read_bytes())
        assert digest(backup)==previous['sha256']
        temporary=target.with_suffix('.lua.pending')
        with temporary.open('xb') as stream:stream.write(source.read_bytes())
        assert digest(temporary)==digest(source)
        assert digest(target)==previous['sha256']
        os.replace(temporary,target)
    assert digest(target)==digest(source)
    assert before=={p:digest(Path(p)) for p in before}
    report.write_text(json.dumps({'hook':str(target),'sha256':digest(target),
        'previous_report':str(previous_report) if replacing else None,
        'backup':str(backup) if replacing else None,'protected_unchanged':before},indent=2))
    print(f'PASS: logging hook installed; {len(before)} protected files unchanged')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('saved_games',type=Path);parser.add_argument('report',type=Path)
    parser.add_argument('--previous-report',type=Path)
    args=parser.parse_args();install(args.saved_games,args.report,args.previous_report)
