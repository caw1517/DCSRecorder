"""Audit retained normal playback against its immutable native tape.

Engine trace timestamps are drain times: getter calls consume the previous
published sample until the next SDK callback. This is not audio-onset telemetry.
No product-wide tolerance or rendered-effect verdict is inferred here.
"""
import argparse
import bisect
import collections
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

EXTERIOR = [0, 3, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
LIGHTS = [88, 190, 191, 192, 193, 210, 212]
WHEELS = [1, 6, 4, 101, 103, 102, 2]


def f32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


class Tape:
    def __init__(self, path):
        lines = path.read_text().splitlines()
        self.version = int(lines[0].removeprefix('DCSREC_PLAYBACK_V'))
        assert 3 <= self.version <= 6
        self.samples = [list(map(float, line.split())) for line in lines[1+self.version:]]
        assert len(self.samples) == int(lines[1])
        self.times = [row[0] for row in self.samples]
        self.columns = {21: 11, **dict(zip(EXTERIOR, range(12, 25))),
                        **dict(zip([28, 29, 89, 90], range(25, 29)))}
        if self.version >= 4:
            self.columns.update(zip(LIGHTS, range(35, 42)))
        if self.version >= 5:
            self.columns[38] = 42
        if self.version >= 6:
            self.columns.update(zip(WHEELS, range(43, 50)))

    def at(self, t):
        t = max(0, min(t, self.times[-1]))
        i = max(0, min(bisect.bisect_right(self.times, t)-1, len(self.times)-2))
        a, b = self.samples[i:i+2]
        dt = b[0]-a[0]
        u = (t-a[0])/dt
        values = [x+(y-x)*u for x, y in zip(a, b)]
        if self.version >= 4:
            values[39] = b[39] if t >= b[0] else a[39]
        if self.version >= 6:
            for k in (46, 47, 48):
                delta = b[k]-a[k]
                if delta > .5: delta -= 1
                if delta < -.5: delta += 1
                values[k] = (a[k]+delta*u) % 1 if 0 < u < 1 and a[k] != b[k] else a[k] if u < 1 else b[k]
        for k in range(3):
            values[1+k] = ((2*u**3-3*u*u+1)*a[1+k]+(u**3-2*u*u+u)*dt*a[8+k]
                           +(-2*u**3+3*u*u)*b[1+k]+(u**3-u*u)*dt*b[8+k])
        qa, qb = a[4:8], b[4:8]
        dot = sum(x*y for x, y in zip(qa, qb))
        if dot < 0: qb = [-v for v in qb]; dot = -dot
        x, y = 1-u, u
        if dot < .9999995:
            angle = math.acos(max(-1, min(1, dot)))
            x, y = math.sin((1-u)*angle)/math.sin(angle), math.sin(u*angle)/math.sin(angle)
        q = [x*v+y*w for v, w in zip(qa, qb)]
        norm = math.sqrt(sum(v*v for v in q))
        values[4:8] = [v/norm for v in q]
        return values


def audit(tape_path, trace_dir, pid, log_path):
    tape = Tape(tape_path)
    motion = rows(trace_dir/f'native-motion-{pid}.csv')
    # A process can contain mission restarts. Audit its last captured run only.
    begin = max(i for i, r in enumerate(motion) if r['status'] == 'captured')
    start = float(motion[begin]['object_time'])
    motion = [r for r in motion[begin+1:] if r['status'] == 'called']
    assert motion and float(motion[-1]['object_time'])-start >= tape.times[-1]
    identity = motion[0]['object_id']
    appearance = rows(trace_dir/f'exterior-{pid}.csv')
    begin = max(i for i, r in enumerate(appearance) if float(r['elapsed']) == 0 and (i == 0 or float(appearance[i-1]['elapsed']) != 0))
    appearance = appearance[begin:]
    assert all(r['id'] == identity for r in appearance)
    groups = collections.defaultdict(lambda: dict(rows=0, requested_error=0, readback_error=0, native_overwrites=0))
    times = sorted({float(r['elapsed']) for r in appearance})
    assert times[0] == 0 and times[-1] >= tape.times[-1]
    strobe_edges = 0
    delivered_strobes = {}
    for r in appearance:
        assert all(math.isfinite(float(r[k])) for k in ('elapsed','requested','before','after'))
        arg = int(r['arg']); elapsed = float(r['elapsed'])
        expected = tape.at(elapsed)[tape.columns[arg]]
        if arg == 193:
            delivered_strobes[elapsed] = float(r['after'])
            # The native elapsed log has 12 significant digits, not the original
            # double. At an exact tape boundary its unrounded value may have
            # been just before the edge. Only this sample-hold channel is
            # discontinuous; permit the immediately preceding sample solely
            # within the timestamp's rounding precision, and report it.
            if abs(float(r['requested'])-expected) > 1e-7:
                i = bisect.bisect_left(tape.times, elapsed)
                k = min(range(max(0,i-1),min(i+1,len(tape.times))),key=lambda k:abs(tape.times[k]-elapsed))
                assert k > 0 and abs(tape.times[k]-elapsed) <= 1e-10
                expected = tape.samples[k-1][39]
                strobe_edges += 1
        g = groups[str(arg)]; g['rows'] += 1
        g['requested_error'] = max(g['requested_error'], abs(float(r['requested'])-expected))
        g['readback_error'] = max(g['readback_error'], abs(float(r['after'])-f32(expected)))
        g['native_overwrites'] += abs(float(r['before'])-float(r['requested'])) > 1e-6
    assert set(map(int, groups)) == set(tape.columns)-{21}
    assert all(g['requested_error'] < 1e-7 and g['readback_error'] < 1e-7 for g in groups.values())
    assert all(g['rows'] == len(times) for g in groups.values())
    engine = rows(trace_dir/f'engine-{pid}.csv')
    begin = max([0]+[i for i in range(1,len(engine)) if float(engine[i]['elapsed']) < float(engine[i-1]['elapsed'])])
    engine = [r for r in engine[begin:] if r['id'] == identity and float(r['time']) > start]
    engines = collections.defaultdict(lambda: dict(rows=0, max_error=0, min_returned=math.inf, max_returned=-math.inf))
    passthrough = 0
    callers = collections.Counter()
    for r in engine:
        assert all(math.isfinite(float(r[k])) for k in ('time','elapsed','original','returned'))
        if int(r['engine']) not in (1, 2):
            assert r['overridden'] == '0' and r['original'] == r['returned']
            passthrough += 1
            continue
        assert r['overridden'] == '1'
        callers[r['caller_module']] += 1
        elapsed = float(r['elapsed'])
        # Drain occurs before publication at this timestamp; destruction drains
        # remaining calls at the last published time and can contain endpoint calls.
        index = max(0, bisect.bisect_left(times, elapsed-1e-8)-1)
        candidates = [times[index]]
        if elapsed >= times[-1]-1e-8: candidates.append(times[-1])
        column = 29+(int(r['engine'])-1)*3+int(r['channel'])
        returned = float(r['returned'])
        error = min(abs(returned-f32(tape.at(t)[column])) for t in candidates)
        g = engines[f"{r['engine']}:{r['channel']}"]; g['rows'] += 1
        g['max_error'] = max(g['max_error'], error)
        g['min_returned'] = min(g['min_returned'], returned); g['max_returned'] = max(g['max_returned'], returned)
    assert set(engines) == {f'{side}:{channel}' for side in (1,2) for channel in (0,1,2)}
    assert all(g['max_error'] < 1e-7 for g in engines.values()), engines
    position = quantized = basis_error = velocity_error = 0
    for r in motion:
        assert all(math.isfinite(float(r[f'{prefix}{i}'])) for prefix in ('actual','command') for i in range(16))
        expected = tape.at(float(r['object_time'])-start)
        command = [float(r[f'command{i}']) for i in range(16)]
        actual = [float(r[f'actual{i}']) for i in range(16)]
        position = max(position, math.dist(command[12:15], expected[1:4]))
        quantized = max(quantized, math.dist(actual[12:15], command[12:15]))
        w,x,y,z = expected[4:8]
        basis = [1-2*(y*y+z*z),2*(x*y+w*z),2*(x*z-w*y),0,
                 2*(x*y-w*z),1-2*(x*x+z*z),2*(y*z+w*x),0,
                 2*(x*z+w*y),2*(y*z-w*x),1-2*(x*x+y*y)]
        basis_error = max(basis_error, max(abs(command[i]-basis[i]) for i in (0,1,2,4,5,6,8,9,10)))
        assert max(abs(actual[i]-f32(command[i])) for i in range(16)) < 1e-5
        velocity_error = max(velocity_error, max(abs(float(r[f'velocity_after{i}'])-float(r[f'velocity_command{i}'])) for i in range(3)))
        assert r['motion_matched'] == '1'
    assert position < 1e-5 and basis_error < 1e-8 and velocity_error == 0
    log = log_path.read_text(errors='replace').split('DCS_PLAYBACK_EVENT,0.000000,INITIALIZED')[-1]
    later = {}
    brake = dict(rows=0, max_error=0, differing_rows=0,
                 interpretation='Measured separately: legacy SDK brake writes precede native animation; visual acceptance does not establish exact later readback.')
    for name, channels in [('EXTERIOR', EXTERIOR+[21]), ('LIGHTS',LIGHTS), ('CANOPY',[38]), ('WHEELS',WHEELS)]:
        if any(c not in tape.columns for c in channels): continue
        count = 0; maximum = 0
        for line in log.splitlines():
            marker = f'DCS_PLAYBACK_{name},'
            if marker not in line: continue
            parts = line.split(marker,1)[1].split(',')
            if parts[0] not in ('playing','complete'): continue
            elapsed = float(parts[2]); values = list(map(float,parts[3:]))
            assert all(map(math.isfinite,[elapsed,*values]))
            assert len(values) == len(channels)
            # Argument 996 carries elapsed as float32 / 1000. Match its
            # nearest native callback, not a re-interpolated noisy timestamp.
            ix = bisect.bisect_left(times, elapsed)
            t = min(times[max(0,ix-1):ix+1], key=lambda t: abs(t-elapsed))
            assert abs(t-elapsed) < 1e-5
            expected = tape.at(t)
            for c,v in zip(channels,values):
                error = abs(v-(delivered_strobes[t] if c == 193 else f32(expected[tape.columns[c]])))
                if c == 21:
                    assert 0 <= v <= 1
                    brake['rows'] += 1
                    brake['max_error'] = max(brake['max_error'],error)
                    brake['differing_rows'] += error > 1e-7
                else:
                    maximum = max(maximum,error)
            count += 1
        later[name.lower()] = dict(rows=count, max_error=maximum)
        # Older missions did not forward light telemetry configuration.
        if count: assert maximum < 1e-7
    assert ',COMPLETE' in log and ',FAILED' not in log
    return dict(tape_sha256=hashlib.sha256(tape_path.read_bytes()).hexdigest(),
                duration=tape.times[-1], native_samples=len(times), object_id=identity,
                appearance=dict(groups), engine=dict(engines), engine_callers=dict(callers), engine_passthrough_calls=passthrough, later_mission=later,
                strobe_sample_boundaries_with_rounded_clock=strobe_edges,
                speedbrake_later_readback=brake,
                motion=dict(rows=len(motion), tape_position_error_m=position,
                            tape_basis_component_error=basis_error, sdk_float_position_rounding_m=quantized,
                            velocity_readback_error_mps=velocity_error),
                interpretation='Numerical delivery and mission completion only; rendering/audio and unexercised channels require human evidence.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('tape','traces','pid','log','output'): p.add_argument(name, type=Path if name != 'pid' else str)
    a = p.parse_args()
    result = audit(a.tape,a.traces,a.pid,a.log)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
