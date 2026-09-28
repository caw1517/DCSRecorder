"""Add an isolated smoke diagnostic reader; leave the working recorder untouched."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('saved_games', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--dcs', type=Path, default=Path('D:/DCS World'))
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    saved = args.saved_games.resolve()
    assert json.loads((args.dcs / 'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version'] == '2.9.29.27468'
    assert (saved / 'Missions/DCSRecorder-Smoke-Diagnostic.miz').is_file()
    plans = [
        (ROOT / 'build/Release/NativeSmokeCapture.dll', saved / 'Scripts/DCSRecorderSmokeCapture/NativeSmokeCapture.dll'),
        (ROOT / 'smoke-prototype/native_capture_hook.lua', saved / 'Scripts/Hooks/dcs-recorder-native-smoke-capture.lua'),
    ]
    for source, target in plans:
        assert source.is_file() and target.resolve().is_relative_to(saved)
        if target.exists() and digest(target) != digest(source):
            raise RuntimeError('Different existing helper: ' + str(target))
    subprocess.run([str(args.dcs / 'bin/luae.exe'), str(ROOT / 'smoke-prototype/check_native_capture.lua'),
                    str(plans[0][0]), str(plans[1][0])], check=True)
    protected = list((saved / 'Scripts').rglob('*.lua')) + list((saved / 'Missions').glob('*.miz'))
    protected += list((saved / 'DCSRecorder/recordings').glob('*.csv'))
    protected += [p for p in (saved / 'Mods/aircraft').rglob('*') if p.is_file() and
                  (p.suffix in ('.dll', '.lua') or p.name.startswith('recorded-flight.'))]
    before = {str(p): digest(p) for p in protected}
    if args.check_only:
        print(f'PASS: installer preflight; 2 additive files ready; {len(before)} existing files identified for preservation')
        return
    processes = subprocess.run(['tasklist.exe', '/FI', 'IMAGENAME eq DCS.exe', '/FO', 'CSV', '/NH'],
                               text=True, capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if '"dcs.exe"' in processes.stdout.lower():
        raise RuntimeError('Close DCS before installing the capture helper; hooks load at startup')
    for source, target in plans:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(source.read_bytes())
        assert digest(target) == digest(source)
    assert before == {str(p): digest(p) for p in protected}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({'installed': {str(t): digest(t) for _, t in plans},
                                      'protected_unchanged': before}, indent=2) + '\n')
    print(f'PASS: 2 diagnostic files installed; {len(before)} protected hashes unchanged')


if __name__ == '__main__':
    main()
