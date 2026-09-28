"""Reconstruct sparse smoke observations; report candidates, never assert emission."""
import argparse
import json
from pathlib import Path


def analyze(path):
    takes = {}
    for line in path.read_text(errors='replace').splitlines():
        if 'DCSSMOKE,1,' not in line:
            continue
        row = line.split('DCSSMOKE,1,', 1)[1].split(',')
        event, take = row[:2]
        if event == 'BEGIN':
            assert take not in takes, 'Repeated take ID; separate mission sessions first'
            takes[take] = dict(start=float(row[2]), mission_id=int(row[3]), store=row[4], frames=[], marks=[])
        data = takes[take]
        if event == 'FRAME':
            assert int(row[2]) == len(data['frames'])+1, 'Frame gap'
            data['frames'].append(dict(time=float(row[3]), count=int(row[4]), changes={}))
        elif event == 'ARGS':
            assert int(row[2]) == len(data['frames']), 'Arguments outside current frame'
            changes = data['frames'][-1]['changes']
            for pair in row[3:]:
                key, value = pair.split('='); key = int(key)
                assert key not in changes, 'Duplicate argument in frame'
                changes[key] = float(value)
        elif event == 'MARK':
            data['marks'].append(dict(time=float(row[2]), state=row[3]))
        elif event == 'END':
            assert int(row[3]) == len(data['frames']), 'End count mismatch'
            data['end'] = row[2]
    output = {}
    for take, data in takes.items():
        assert data.get('end') == 'user_stop', 'Incomplete capture'
        frames = data.pop('frames'); state = {}; samples = []
        assert set(frames[0]['changes']) == set(range(1000)), 'Incomplete initial snapshot'
        for frame in frames:
            assert frame['count'] == len(frame['changes']), 'Lost argument chunk'
            state.update(frame['changes']); samples.append((frame['time'], state.copy()))
        gaps = [b[0]-a[0] for a,b in zip(samples,samples[1:])]
        assert gaps and min(gaps)>0 and max(gaps)<.401, 'Invalid sample clock'
        windows = {}
        for mark in data['marks']:
            windows.setdefault(mark['state'], []).extend(s for t,s in samples if mark['time']+1<=t<=mark['time']+5)
        assert windows.get('ON') and windows.get('OFF'), 'Both visible-state markers required'
        candidates=[]; binary=[]
        for channel in range(1000):
            values = [s[channel] for _,s in samples]
            distinct = set(values)
            if len(distinct) == 1: continue
            transitions=[dict(time=t,value=s[channel]) for i,(t,s) in enumerate(samples)
                         if i==0 or s[channel]!=samples[i-1][1][channel]]
            if len(distinct)<=3:
                binary.append(dict(arg=channel,values=sorted(distinct),transitions=transitions))
            on=[s[channel] for s in windows['ON']]; off=[s[channel] for s in windows['OFF']]
            if max(on)<min(off)-1e-5 or max(off)<min(on)-1e-5:
                candidates.append(dict(arg=channel,on=[min(on),max(on)],off=[min(off),max(off)],
                                       distinct=len(distinct),transitions=transitions if len(transitions)<=12 else len(transitions)))
        data.update(samples=len(samples),duration=samples[-1][0]-samples[0][0],max_gap=max(gaps),
                    changing_arguments=sum(len({s[c] for _,s in samples})>1 for c in range(1000)),
                    separated_window_candidates=candidates,small_discrete_channels=binary)
        output[take]=data
    assert output, 'No smoke capture found'
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('log',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=analyze(args.log)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
