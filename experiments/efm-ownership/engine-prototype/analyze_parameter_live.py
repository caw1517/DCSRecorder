"""Check measured parameter delivery independently of the human sound verdict."""
import argparse
import bisect
import collections
import csv
import json
from pathlib import Path


def inspect(calls, events, tape_path):
    with calls.open() as stream:
        rows = list(csv.DictReader(stream))
    with events.open() as stream:
        lifecycle = list(csv.DictReader(stream))
    assert [r['event'] for r in lifecycle] == [
        'tape_loaded', 'create', 'parameter_hook_installed', 'baseline_begin',
        'recorded_parameters_begin', 'parameter_hook_restored',
        'original_getter_restored', 'destroy'], lifecycle
    assert len({r['id'] for r in rows}) == 1
    phase = float(next(r['time'] for r in lifecycle
                       if r['event'] == 'recorded_parameters_begin'))
    lines = tape_path.read_text().splitlines()
    assert lines[0] == 'DCS_NATIVE_ENGINE_PROBE_V1'
    tape = [list(map(float, line.split())) for line in lines[2:]]
    assert len(tape) == int(lines[1]) and all(len(r) == 7 for r in tape)
    times = [r[0] for r in tape]

    def at(t, channel):
        t = min(max(t, 0), times[-1])
        i = max(0, min(bisect.bisect_right(times, t) - 1, len(tape) - 2))
        a, b = tape[i:i + 2]
        return a[channel] + (b[channel] - a[channel]) * (t - a[0]) / (b[0] - a[0])

    clocks = sorted({float(r['drain_time']) for r in rows})
    assert len(clocks) > 1
    assert max(abs(b - a - .02) for a, b in zip(clocks, clocks[1:])) < 1e-7
    overrides = []
    for row in rows:
        if row['overridden'] == '1':
            assert row['engine'] in ('1', '2') and row['channel'] in ('0', '1', '2')
            overrides.append(row)
        else:
            assert row['original'] == row['returned']
    # Logged drain time is not call time. Verify the same one-step delay observed
    # in the original RPM run against every overridden channel and caller.
    error = max(abs(float(r['returned']) - at(
        float(r['drain_time']) - phase - .02,
        (int(r['engine']) - 1) * 3 + int(r['channel']) + 1)) for r in overrides)
    assert error < 1e-6, error
    sound = [r for r in rows if r['caller_module'] == 'Sound.dll']
    changed = [r for r in sound if r['overridden'] == '1']
    expected = {(str(e), str(c)) for e in (1, 2) for c in (0, 1, 2)}
    assert {(r['engine'], r['channel']) for r in changed} == expected
    assert {(r['engine'], r['channel']) for r in sound
            if r['overridden'] == '0'} >= expected
    # Confirm both native power consumers, including the unchanged F0 forwarder.
    for rva in (0x134cab, 0x134cc1):
        assert {r['engine'] for r in changed
                if int(r['caller_rva']) == rva and r['channel'] == '2'} == {'1', '2'}
    assert max(float(r['returned']) for r in changed if r['channel'] == '1') > 1
    assert max(float(r['returned']) for r in changed if r['channel'] == '2') > 2
    groups = collections.defaultdict(list)
    for row in sound:
        groups[(row['caller_rva'], row['engine'], row['channel'], row['overridden'])].append(row)
    return {
        'native_consumption': 'passed',
        'audio_fidelity': 'separate human verdict required',
        'total_calls': len(rows), 'overridden_calls': len(overrides),
        'sound_calls': len(sound), 'sound_overridden_calls': len(changed),
        'maximum_recorded_parameter_error': error,
        'observed_publish_to_drain_delay': .02, 'events': lifecycle,
        'sound_groups': [dict(caller_rva=hex(int(rva)), engine=int(engine),
                              channel=int(channel), overridden=override == '1',
                              calls=len(rs), returned_range=[
                                  min(float(r['returned']) for r in rs),
                                  max(float(r['returned']) for r in rs)])
                         for (rva, engine, channel, override), rs in groups.items()]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('calls', 'events', 'tape', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = inspect(args.calls, args.events, args.tape)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"PASS: {result['sound_overridden_calls']} Sound.dll overrides; "
          f"all six channels and both power callsites; maximum tape error "
          f"{result['maximum_recorded_parameter_error']:.3g}; clean restoration")
