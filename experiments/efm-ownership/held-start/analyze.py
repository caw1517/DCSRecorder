"""Retain and measure one bounded airborne hold, not release acceptance."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path


def analyze(output, manifest_path=None):
    raw = output / 'raw'
    text = (raw / 'dcs.log').read_text(encoding='utf-8', errors='replace')
    lines = [s.split('DCSR_HELD ', 1)[1] for s in text.splitlines() if 'DCSR_HELD ' in s]
    assert lines.count('INITIALIZED') == lines.count('HELD') == lines.count('OBSERVATION_COMPLETE') == 1
    assert not any(s.startswith('FAILED') for s in lines)
    samples = {}
    for line in lines:
        if line.startswith('SAMPLE,'):
            row = next(csv.reader([line]))
            assert len(row) == 51, len(row)
            values = list(map(float, row[2:]))
            assert all(math.isfinite(v) for v in values)
            samples.setdefault(row[1], []).append(values)
    # time, ID, position[3], forward[3], up[3], velocity[3], replay, status, args[33]
    lead, player, witness = (samples[n] for n in ('StagedPlayback', 'Observer', 'SceneWitness'))
    tape = (raw / 'recorded-flight.txt').read_text().splitlines()
    assert tape[0] == 'DCSREC_PLAYBACK_V6'
    first = list(map(float, tape[7].split()))
    assert len(first) == 50
    expected = {21: first[11], 38: first[42]}
    for channels, values in (
        ([0,3,5,9,10,11,12,13,14,15,16,17,18], first[12:25]),
        ([28,29,89,90], first[25:29]), ([88,190,191,192,193,210,212], first[35:42]),
        ([1,6,4,101,103,102,2], first[43:50])):
        expected.update(zip(channels, values))
    args = [0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29]
    assert len(lead[0][16:]) == len(args)

    def drift(rows, start, count):
        return max(math.dist(r[start:start+count], rows[0][start:start+count]) for r in rows)

    report = {'scope': 'One real airborne playback object held at time zero; no release or ground acceptance',
              'configuration': {'build': '2.9.30.28536', 'module': 'DCSRecorder-Hornet-Held-Test',
                                'mission': '040-Hornet-Held-Start.miz', 'native_pid': 26264}}
    if manifest_path:
        manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'))
        engine_paths=list(raw.glob('engine-*.csv'))
        assert len(engine_paths)==1
        report['configuration']={'build':manifest['dcs_build'],'module':manifest['module'],
            'mission':manifest['mission'],'native_pid':int(engine_paths[0].stem.split('-')[1])}
    report['mission'] = {
        'lead_samples': len(lead), 'first_time': lead[0][0], 'last_time': lead[-1][0],
        'observed_seconds': lead[-1][0]-lead[0][0], 'lead_ids': sorted({r[1] for r in lead}),
        'lead_position_drift_m': drift(lead,2,3), 'lead_forward_drift': drift(lead,5,3),
        'lead_up_drift': drift(lead,8,3), 'lead_max_speed_mps': max(math.dist(r[11:14],[0,0,0]) for r in lead),
        'lead_max_source_position_error_m': max(math.dist(r[2:5],first[1:4]) for r in lead),
        'replay_times': sorted({r[14] for r in lead}), 'controller_statuses': sorted({r[15] for r in lead}),
        'appearance_max_source_error': max(abs(r[16+i]-expected[a]) for r in lead for i,a in enumerate(args)),
        'appearance_max_drift': max(abs(r[16+i]-lead[0][16+i]) for r in lead for i in range(len(args))),
        'player_position_drift_m': drift(player,2,3),
        'witness_displacement_m': math.dist(witness[0][2:5],witness[-1][2:5]), 'observation_complete': True}
    m = report['mission']
    assert m['observed_seconds'] >= 30-1e-9 and len(m['lead_ids']) == 1
    assert m['replay_times'] == [0] and m['controller_statuses'] == [0.125]
    assert m['lead_position_drift_m'] == 0 and m['witness_displacement_m'] > 1

    def read(pattern):
        paths = list(raw.glob(pattern))
        assert len(paths) == 1, (pattern, paths)
        with paths[0].open(newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    all_motion = read('native-motion-*.csv')
    motion = [r for r in all_motion if r['status'] == 'called']
    assert motion and {r['status'] for r in all_motion} <= {'captured','called'}
    assert all(r['motion_matched'] == '1' for r in motion)
    report['native_motion'] = {
        'writes': len(motion), 'first_time': float(motion[0]['object_time']), 'last_time': float(motion[-1]['object_time']),
        'ids': sorted({r['object_id'] for r in motion}), 'all_motion_matched': True,
        'max_float_position_readback_error_m': max(math.dist([float(r[f'actual{i}']) for i in range(12,15)],first[1:4]) for r in motion),
        'max_velocity_after_mps': max(math.dist([float(r[f'velocity_after{i}']) for i in range(3)],[0,0,0]) for r in motion),
        'max_commanded_angular_rate': max(abs(float(r[f'angular_command{i}'])) for r in motion for i in range(3)),
        'last_prephysics_calls': int(motion[-1]['step_hook_calls']), 'last_prephysics_applied': int(motion[-1]['step_hook_applied'])}
    exterior = read('exterior-*.csv')
    assert exterior and all(float(r['elapsed']) == 0 for r in exterior)
    report['native_appearance'] = {
        'rows': len(exterior), 'channels': sorted({int(r['arg']) for r in exterior}),
        'max_requested_source_error': max(abs(float(r['requested'])-expected[int(r['arg'])]) for r in exterior),
        'max_postanimation_source_error': max(abs(float(r['after'])-expected[int(r['arg'])]) for r in exterior)}
    engine_all = read('engine-*.csv')
    assert engine_all and all(float(r['elapsed']) == 0 for r in engine_all)
    engine = [r for r in engine_all if int(r['engine']) in (1,2)]
    passthrough = [r for r in engine_all if int(r['engine']) not in (1,2)]
    assert engine and all(r['overridden'] == '1' for r in engine)
    assert all(r['engine'] == '0' and r['overridden'] == '0' and r['returned'] == r['original'] for r in passthrough)
    engine_expected = {(e,c): first[29+(e-1)*3+c] for e in (1,2) for c in range(3)}
    report['native_engine'] = {
        'reads': len(engine_all), 'valid_engine_overrides': len(engine), 'engine_zero_passthrough_reads': len(passthrough),
        'caller_modules': sorted({r['caller_module'] for r in engine}),
        'channels': sorted({(int(r['engine']),int(r['channel'])) for r in engine}), 'all_valid_engines_overridden_at_zero': True,
        'max_returned_source_error': max(abs(float(r['returned'])-engine_expected[int(r['engine']),int(r['channel'])]) for r in engine)}
    events = read('objects-*.csv')
    report['object_event_counts'] = dict(Counter(r['event'] for r in events))
    assert report['object_event_counts']['create']==1
    destroyed=report['object_event_counts'].get('destroy',0)
    assert destroyed in (0,1) and (manifest_path or destroyed==1)
    report['cleanup_limit'] = ('Destroy reported step_hook_already_replaced: object table already replaced at destruction; broader restart/failure cleanup remains unverified.'
        if destroyed and report['object_event_counts'].get('step_hook_already_replaced') else
        'Destruction was not observed in this capture; no teardown or restart acceptance claimed.' if not destroyed else
        'One destruction observed; inspect hook status events separately. Broader restart/failure cleanup remains unverified.')
    report['user_review'] = (json.loads((output/'review.json').read_text()) if manifest_path else
        {'visible_hold': 'Lead perfectly still throughout; scene witness flew away',
         'engine_sound': 'User confirmed steady engine sound'})
    report['hashes'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(raw.iterdir()) if p.is_file()}
    if manifest_path:
        for name in (manifest['binary']+'.dll','recorded-flight.txt','recorded-flight.json'):
            assert report['hashes'][name]==manifest['files'][manifest['module']+'/bin/'+name],name
        assert report['hashes'][manifest['mission']]==manifest['files'][manifest['mission']]
        # Log precision checks, not accepted product-wide fidelity tolerances.
        assert m['appearance_max_source_error']<1e-9 and m['appearance_max_drift']==0
        assert m['lead_forward_drift']==m['lead_up_drift']==m['lead_max_speed_mps']==0
        assert report['native_appearance']['channels']==sorted(expected)
        assert report['native_appearance']['max_postanimation_source_error']<1e-9
        assert report['native_engine']['max_returned_source_error']<1e-9
        report['smoke']={'recorded_initial_on':manifest['recording']['smoke_events'][0]['on'],
            'initial_commands':[s for s in lines if s.startswith('INITIAL_SMOKE,')],
            'rendering':'User permits absence while held; release onset remains unverified'}
    else:
        assert report['hashes']['HornetHeldProbe.dll'] == '23df85f99addea68d379bb646540cc5e04f63ce4fcc966dc18bc1d6b9c653d72'
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'hashes'},indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('output',type=Path)
    p.add_argument('--capture-from',type=Path)
    p.add_argument('--manifest',type=Path)
    a = p.parse_args()
    if a.capture_from:
        assert not a.manifest, 'Capture snapshot-module files explicitly before analyzing with --manifest'
        raw = a.output/'raw'
        raw.mkdir(parents=True,exist_ok=False)
        module = a.capture_from/'Mods/aircraft/DCSRecorder-Hornet-Held-Test/bin'
        sources = [a.capture_from/'Logs/dcs.log',module/'recorded-flight.txt',module/'recorded-flight.json',
                   module/'HornetHeldProbe.dll',a.capture_from/'Missions/040-Hornet-Held-Start.miz',
                   *sorted((module/'probe-logs').iterdir())]
        for source in sources:
            if source.is_file():
                (raw/source.name).write_bytes(source.read_bytes())
    analyze(a.output,a.manifest)
