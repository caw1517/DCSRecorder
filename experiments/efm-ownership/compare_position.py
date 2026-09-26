"""Compare read-only object samples with independent mission telemetry.

Positive sample delay means native time t corresponds to mission time t-delay.
Interpolation and fitted delay are diagnostic, not proof of callback ordering.
"""
import argparse,bisect,csv,json,math,statistics
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('result_directory')
a=p.parse_args(); root=Path(a.result_directory)
rows=list(csv.DictReader((root/'native-body.csv').open()))
native=[(float(r['object_time']),tuple(float(r[c]) for c in ('x','y','z'))) for r in rows if r['status']=='object_position_candidate']
tracks={}
for line in (root/'dcs-excerpt.txt').read_text().splitlines():
    if 'OWNERSHIP_OBSERVER,' not in line: continue
    fields=line.split('OWNERSHIP_OBSERVER,',1)[1].split(',')
    tracks.setdefault(fields[0],[]).append((float(fields[1]),tuple(map(float,fields[2:5]))))
def compare(track,delay):
    times=[r[0] for r in track]; errors=[]
    for t,xyz in native:
        target=t-delay
        i=bisect.bisect_right(times,target)-1
        if i<0 or i+1>=len(track): continue
        fraction=(target-times[i])/(times[i+1]-times[i])
        expected=[lo+fraction*(hi-lo) for lo,hi in zip(track[i][1],track[i+1][1])]
        errors.append(math.dist(xyz,expected))
    return {'pairs':len(errors),'rms_m':math.sqrt(statistics.mean(e*e for e in errors)),
            'max_m':max(errors),'median_m':statistics.median(errors)}
probe=tracks['Probe']
delays=[i/1000 for i in range(-100,101)]
best=min(delays,key=lambda d:compare(probe,d)['rms_m'])
result={'native_samples':len(native),'statuses':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
        'native_time_range':[native[0][0],native[-1][0]],'same_timestamp':compare(probe,0),
        'fixed_20ms_delay':compare(probe,0.02),'best_delay_s':best,'best_fit':compare(probe,best),
        'other_aircraft_at_best_delay':compare(tracks['Observer'],best)}
print(json.dumps(result,indent=2))
