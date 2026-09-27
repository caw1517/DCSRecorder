"""Validate native RPM consumption separately from the user's audible verdict."""
import argparse
import bisect
import collections
import csv
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('calls',type=Path)
parser.add_argument('events',type=Path)
parser.add_argument('tape',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
with args.calls.open()as f: rows=list(csv.DictReader(f))
with args.events.open()as f: events=list(csv.DictReader(f))
names=[r['event']for r in events]
assert names==['tape_loaded','create','rpm_hook_installed','baseline_begin',
    'recorded_rpm_begin','rpm_hook_restored','original_getter_restored','destroy'],names
phase=float(next(r['time']for r in events if r['event']=='recorded_rpm_begin'))
assert len({r['id']for r in rows})==1
text=args.tape.read_text().splitlines()
assert text[0]=='DCS_CORE_RPM_PROBE_V1'
tape=[list(map(float,l.split()))for l in text[2:]]
assert len(tape)==int(text[1])
times=[r[0]for r in tape]
def at(t,c):
    t=min(max(t,0),times[-1])
    i=max(0,min(bisect.bisect_right(times,t)-1,len(tape)-2))
    a,b=tape[i:i+2]
    return a[c]+(b[c]-a[c])*(t-a[0])/(b[0]-a[0])
for r in rows:
    if r['overridden']=='1':assert r['engine']in ('1','2') and r['core']=='1'
    else:assert r['original']==r['returned']
sound=[r for r in rows if r['caller_module']=='Sound.dll']
overridden=[r for r in sound if r['overridden']=='1']
assert {r['engine']for r in overridden}=={'1','2'}
assert any(r['overridden']=='0' and r['core']=='1' and r['engine']=='1'for r in sound)
# This run drains calls one 20 ms SDK step after the value was published.
# Verify the observed relationship, rather than relabeling drain_time as call time.
clock_steps=[b-a for a,b in zip(sorted({float(r['drain_time'])for r in rows}),
    sorted({float(r['drain_time'])for r in rows})[1:])]
assert clock_steps and max(abs(v-.02)for v in clock_steps)<1e-7
error=max(abs(float(r['returned'])-at(float(r['drain_time'])-phase-.02,int(r['engine'])))for r in overridden)
assert error<1e-6,error
groups=collections.defaultdict(list)
for r in sound:groups[(r['caller_rva'],r['engine'],r['core'],r['overridden'])].append(r)
result={'native_consumption':'passed','audio_fidelity':'requires separate human verdict',
    'total_calls':len(rows),'sound_calls':len(sound),'sound_overridden_calls':len(overridden),
    'maximum_recorded_rpm_error':error,'observed_publish_to_drain_delay':.02,
    'events':events,'sound_groups':[]}
for (rva,engine,core,override),rs in groups.items():
    result['sound_groups'].append({'caller_rva':hex(int(rva)),'engine':int(engine),'core':core=='1',
        'overridden':override=='1','calls':len(rs),
        'returned_range':[min(float(r['returned'])for r in rs),max(float(r['returned'])for r in rs)]})
args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(f'PASS: {len(overridden)} Sound.dll core-RPM overrides match the tape (maximum error {error:.3g}); other values forwarded; clean restoration')
