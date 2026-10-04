import sys
from pathlib import Path
sys.path.insert(0,r'C:\Users\w_can\.codex\worktrees\airborne-staging\DCS_Recorder\experiments\efm-ownership')
from extract_recording_log import extract
root=Path(r'E:\Projects\DCS_Recorder\experiments\efm-ownership\results\companion-save-failure-2026-09-26')
expected=extract(root/'dcs.log',root/'recovered')
actual=Path(r'C:\Users\w_can\Saved Games\DCS\DCSRecorder\recordings')
assert len(expected)==1, 'Expected exactly one explicitly stopped take in the captured log'
found=any(p.read_bytes()==expected[0].read_bytes() for p in actual.glob('*.csv'))
print('Stopped capture: 2301 samples; matching durable library entry:',found)
assert found, 'F10 Stop completed but the recording is absent from the durable library'
