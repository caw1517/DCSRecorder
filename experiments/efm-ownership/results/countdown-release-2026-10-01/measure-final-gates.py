"""Retain repeated-start facts and audit applicability of the live refusal run."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
old = json.loads((root/'gear-package-v4/manifest.json').read_text(encoding='utf-8-sig'))
current = json.loads((root/'gear-package-v5/manifest.json').read_text(encoding='utf-8-sig'))
changed = [p for p in old['files'] if old['files'][p] != current['files'][p]]
assert changed == ['Scripts/DCSRecorderReleaseControl/expected.lua']
for name, expected in current['files'].items():
    assert hashlib.sha256((Path('C:/Users/w_can/Saved Games/DCS')/name).read_bytes()).hexdigest() == expected

def read_run(directory):
    raw = root/directory/'raw'
    events = [line.split('DCSR_RELEASE ',1)[1].split(',')
              for line in (raw/'dcs.log').read_text(encoding='utf-8',errors='replace').splitlines()
              if 'SCRIPTING (Main): DCSR_RELEASE ' in line]
    counts = Counter(e[0] for e in events)
    with next(raw.glob('objects-*.csv')).open(newline='') as f:
        lifecycle = Counter(r['event'] for r in csv.DictReader(f))
    with next(raw.glob('native-motion-*.csv')).open(newline='') as f:
        motion = [r for r in csv.DictReader(f) if r['status']=='called']
    return raw, events, counts, lifecycle, motion

raw, events, counts, native, motion = read_run('repeated-start-41868')
assert [e[1] for e in events if e[0]=='START_REFUSED'] == ['countdown','playing']
assert all(counts[n]==1 for n in ('COUNTDOWN','REQUEST','PLAYER_RELEASED','NATIVE_RUNNING'))
assert native['release_committed']==native['release_epoch']==1
assert not counts['FAILED']
assert all(r['motion_matched']=='1' for r in motion)
repeat = {'pid':41868, 'user_review':'Complete', 'mission_events':dict(counts), 'native_events':dict(native),
          'refused_phases':['countdown','playing'], 'installed_package':'gear-package-v5',
          'all_14_installed_hashes_match':True,
          'scope':'Both duplicate requests refused. Mission exited before recording completion; normal completion is proven in prior runs.'}
(raw.parent/'analysis.json').write_text(json.dumps(repeat,indent=2)+'\n')

raw, events, counts, native, motion = read_run('readiness-failure-36760')
assert counts['FAILED']==counts['HOLD_CLEANED']==1
assert all(counts[n]==0 for n in ('READY','COUNTDOWN','REQUEST','PLAYER_RELEASED','NATIVE_RUNNING','COMPLETE'))
assert native['release_committed']==native['release_epoch']==0
assert native['destroy']==1
assert motion and all(float(r[f'velocity_command{i}'])==0 for r in motion for i in range(3))
samples = [e for e in events if e[0]=='SAMPLE' and e[2]=='StagedPlayback']
assert samples and {float(e[16]) for e in samples}=={0}
positions = {tuple(e[4:7]) for e in samples}
assert len(positions)==1
refusal = {'pid':36760, 'observed_reason':'loaded_mismatch:coalition[blue][country][1][plane][group][1][units][1][heading]:value',
           'mission_events':dict(counts), 'native_events':dict(native),
           'zero_velocity_writes':len(motion), 'playback_samples_at_zero':len(samples),
           'cleanup':'Playback object destroyed; owned player hold cleaned; no release',
           'applicability':'v4 and accepted v5 have identical hook, mission, native DLL, tape and guard code; only expected.lua changed after bounded serialization audit',
           'v4_to_v5_changed_files':changed,
           'scope':'Live loaded-readiness refusal; this was an accidental reference mismatch, not an injected native-unready fault. Other refusal paths have offline fixtures only.'}
(root/'readiness-refusal-analysis.json').write_text(json.dumps(refusal,indent=2)+'\n')
print(json.dumps({'duplicate_request':repeat,'readiness_refusal':refusal},indent=2))
