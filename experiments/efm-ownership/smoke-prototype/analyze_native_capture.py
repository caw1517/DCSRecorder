"""Validate paired diagnostic rows; retain native timestamps independently of markers."""
import argparse
import json
import math
from pathlib import Path


def analyze(path):
    mission, native = {}, {}
    for line in path.read_text(errors='replace').splitlines():
        if 'DCSSMOKE,1,' in line:
            row = line.split('DCSSMOKE,1,', 1)[1].split(',')
            event, take = row[:2]
            if event == 'BEGIN':
                assert take not in mission, 'Repeated mission ID; separate sessions first'
                assert row[4:] == ['{INV-SMOKE-WHITE}', '0', '999'], 'Unexpected loadout/range'
                mission[take] = dict(start=float(row[2]), id=int(row[3]), frames={}, marks=[])
            data = mission[take]
            if event == 'FRAME':
                assert int(row[2]) == len(data['frames']) + 1, 'Mission frame gap'
                data['frames'][int(row[2])] = float(row[3])
            elif event == 'MARK':
                data['marks'].append(dict(time=float(row[2]), state=row[3]))
            elif event == 'END':
                assert 'end' not in data and int(row[3]) == len(data['frames']), 'Mission END mismatch'
                data['end'] = row[2]
        if 'DCSSMOKE_NATIVE,1,' not in line:
            continue
        row = line.split('DCSSMOKE_NATIVE,1,', 1)[1].split(',')
        event, take = row[:2]
        assert event != 'ERROR', 'Native capture error: ' + ','.join(row[1:])
        if event == 'READY':
            continue
        if event == 'BEGIN':
            assert len(row) == 6 and row[4:] == ['10', '{INV-SMOKE-WHITE}'], 'Unexpected native metadata'
            assert take not in native, 'Repeated native ID; separate sessions first'
            native[take] = dict(start=float(row[2]), id=int(row[3]), rows=[])
        data = native[take]
        if event == 'DATA':
            assert 'end' not in data, 'Native DATA after END'
            assert len(row) == 12 and row[7:9] == ['OK', '10'], 'Invalid native row'
            assert int(row[2]) == len(data['rows']) + 1, 'Native sequence gap'
            mission_time, start, finish = map(float, row[3:6])
            assert all(map(math.isfinite, (mission_time, start, finish))), 'Nonfinite clock'
            assert 0 <= start - mission_time <= .250001 and 0 <= finish - start <= .100001, 'Delayed native read'
            on, aggregate, classification = map(int, row[9:12])
            assert on in (0, 1) and aggregate == on and 0 <= classification <= 255, 'Invalid smoke state'
            data['rows'].append(dict(mission_time=mission_time, time=start, finish=finish,
                                     export_id=int(row[6]), on=on, classification=classification))
        elif event == 'END':
            assert 'end' not in data and int(row[3]) == len(data['rows']), 'Native END mismatch'
            data['end'] = row[2]
    assert mission and mission.keys() == native.keys(), 'Missing native/mission capture'
    output = {}
    for take, data in native.items():
        source = mission[take]
        assert source.get('end') == data.get('end') == 'user_stop', 'Incomplete capture'
        assert source['id'] == data['id'] and source['start'] == data['start'], 'Capture association mismatch'
        rows = data['rows']
        assert len(rows) >= 2 and len(rows) == len(source['frames']), 'Missing paired rows'
        assert len({r['export_id'] for r in rows}) == 1, 'Export identity changed'
        assert len({r['classification'] for r in rows}) == 1, 'Store classification changed'
        for seq, r in enumerate(rows, 1):
            assert abs(r['mission_time'] - source['frames'][seq]) <= 1e-6, 'Frame clock mismatch'
        gaps = [b['time'] - a['time'] for a, b in zip(rows, rows[1:])]
        assert min(gaps) > 0 and max(gaps) < .451, 'Native clock gap'
        transitions = [dict(time=r['time'], on=r['on']) for i, r in enumerate(rows)
                       if i == 0 or r['on'] != rows[i-1]['on']]
        output[take] = dict(samples=len(rows), duration=rows[-1]['time']-rows[0]['time'],
                            max_gap=max(gaps), max_delay=max(r['time']-r['mission_time'] for r in rows),
                            max_read_span=max(r['finish']-r['time'] for r in rows),
                            export_id=rows[0]['export_id'], mission_id=source['id'],
                            classification=rows[0]['classification'], transitions=transitions,
                            markers=source['marks'], end=data['end'])
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = analyze(args.log)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
