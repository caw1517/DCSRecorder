"""Offline full-flight duration check: recording, storage, conversion, preparation and
controller playback of 30- and 60-minute takes, before any long live flight.

Two long takes are made, since none has been flown yet:
- sink: the real recording sink (via companion/test_engine_sink.lua) saves a
  continuously moving contact take of the requested length;
- circuit: the accepted 248.7 s parking-to-parking circuit with its hot parked
  start held longer, prepared against its own authored scene.
Each is read, validated by the companion library, converted, prepared (circuit) and
replayed end to end by the surface controller's reader (surface_long_tape_check).
Usage: python check_long_take.py [seconds ...]   (default 1800 3600)
"""
import csv, json, shutil, subprocess, sys, tempfile, time, tracemalloc
from pathlib import Path
HERE = Path(__file__).resolve().parent
EFM = HERE.parents[1]
REPO = EFM.parents[1]
sys.path.insert(0, str(REPO/'companion')); sys.path.insert(0, str(EFM)); sys.path.insert(0, str(EFM/'authored-preparation'))
from library import Library, TRIAL_BUILD
from recorded_flight import read, convert
from prepare_staged_playback import fingerprint

DCS = Path('D:/DCS World')
CIRCUIT = EFM/'results/takeoff-landing-2026-10-04/source/20261004T200936Z-0001.csv'
SAVED_GAMES = Path.home()/'Saved Games/DCS'
# The circuit's own authored scene, as the companion's lineage kept it.
SCENE = SAVED_GAMES/'DCSRecorder/lineages/9217256bd24e4ccda5a5921c531d239d/revisions/7da72749866d21e24c339165cc7580f093bc196f32b3a02460cfd390a864f75a/source.miz'
LEAD, PLAYER = 1, 2
CHECK = EFM/'build/Release/surface_long_tape_check.exe'
TIME_COLUMNS = ('t', 'engine_time', 'smoke_time')


def timed(fn, *args, **kwargs):
    tracemalloc.start(); start = time.perf_counter()
    try: result = fn(*args, **kwargs)
    finally: elapsed = time.perf_counter()-start; peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    return result, round(elapsed, 2), round(peak/2**20)


def plain(fn, *args, **kwargs):
    start = time.perf_counter(); result = fn(*args, **kwargs)
    return result, round(time.perf_counter()-start, 2)


def extend_parked_start(source, destination, seconds):
    """Hold the first (hot, parked) sample until the take lasts `seconds`."""
    rows = list(csv.reader(source.open(encoding='utf-8-sig', newline='')))
    header = next(i for i, r in enumerate(rows) if r and r[0] == 't'); names = rows[header]
    body, footer = rows[header+1:-1], rows[-1]
    duration = float(body[-1][0])-float(body[0][0])
    extra = round((seconds-duration)/0.02)
    columns = [names.index(c) for c in TIME_COLUMNS if c in names]
    def shifted(row, by):
        row = list(row)
        for c in columns: row[c] = repr(float(row[c])+by)
        return row
    hold = [shifted(body[0], i*0.02) for i in range(extra)]
    body = hold+[shifted(r, extra*0.02) for r in body]
    with destination.open('w', encoding='utf-8', newline='') as f:
        csv.writer(f, lineterminator='\n').writerows(rows[:header+1]+body+[[footer[0], footer[1], str(len(body))]])
    return destination


def sink_take(root, seconds):
    (root/'DCSRecorder/recordings').mkdir(parents=True)
    here = REPO/'companion'
    start = time.perf_counter()
    result = subprocess.run([str(DCS/'bin/luae.exe'), str(here/'test_engine_sink.lua'), str(here/'recording_sink.lua'),
                             str(here/'engine_capture.lua'), str(root), 'batch', str(here/'smoke_capture.lua'), 'contact',
                             TRIAL_BUILD, str(round(seconds/0.02))], capture_output=True, text=True)
    elapsed = round(time.perf_counter()-start, 2)
    status = (root/'DCSRecorder/save-status.txt').read_text()
    if result.returncode or not status.startswith('READY'): raise RuntimeError(result.stdout+result.stderr+status)
    return next((root/'DCSRecorder/recordings').glob('*.csv')), elapsed


def replay(tape, seconds):
    result = subprocess.run([str(CHECK), str(tape), '%x' % fingerprint(tape.read_bytes()), str(seconds-0.1)], capture_output=True, text=True)
    if result.returncode: raise RuntimeError(result.stdout+result.stderr)
    return result.stdout.strip()


def check(seconds, root):
    report = dict(target_seconds=seconds)
    # Sink: a continuously moving contact take saved by the real recording sink.
    take, report['sink_save_s'] = sink_take(root/'sink', seconds)
    library = Library(dict(saved_games=str(root/'sink'), dcs=str(DCS), build_trial=TRIAL_BUILD), running=lambda: False)
    (metadata, samples, _), report['sink_read_s'], report['sink_read_peak_mb'] = timed(read, take)
    del samples
    entries, report['sink_library_first_s'] = plain(library.entries)
    _, report['sink_library_again_s'] = plain(library.entries)
    # The fixture records no authored scene, so the normal setup lists it as a
    # validated legacy take; its full length must still pass validation.
    assert abs(entries[0]['duration']-metadata['duration']) < 1e-9 and entries[0].get('legacy'), entries[0]
    report.update(sink_bytes=take.stat().st_size, sink_duration=metadata['duration'], sink_samples=metadata['samples'])
    tape = root/'sink-tape/recorded-flight.txt'
    _, report['sink_convert_s'] = plain(convert, take, tape)
    report['sink_tape_bytes'] = tape.stat().st_size
    report['sink_replay'] = replay(tape, seconds)
    # Circuit: the accepted parking-to-parking take, prepared against its own scene.
    take = extend_parked_start(CIRCUIT, root/CIRCUIT.name, seconds)
    from prepare_playback import build
    result, report['circuit_prepare_s'] = plain(build, take, SCENE, LEAD, PLAYER, root/'circuit', f'DCSRecorder-Duration-{seconds}.miz',
                                                dcs=DCS, saved_games=SAVED_GAMES)
    recording = result['recording']
    assert recording['parked_endpoint']['eligible'] and recording['surface_available'], 'circuit lost its parked ending'
    tape = next((root/'circuit/payload/Mods/aircraft').glob('*/bin/recorded-flight.txt'))
    config = (root/'circuit/mission.lua').read_text(encoding='utf-8')
    assert 'replay_scale' in config, 'prepared mission lacks the long replay clock'
    report.update(circuit_duration=recording['duration'], circuit_samples=recording['samples'], circuit_tape_bytes=tape.stat().st_size,
                  circuit_replay=replay(tape, seconds))
    return report


if __name__ == '__main__':
    targets = [int(s) for s in sys.argv[1:]] or [1800, 3600]
    reports = []
    for seconds in targets:
        with tempfile.TemporaryDirectory() as tmp:
            reports.append(check(seconds, Path(tmp)))
        print(json.dumps(reports[-1], indent=2), flush=True)
    (HERE/'offline-check.json').write_text(json.dumps(reports, indent=2)+'\n', encoding='utf-8')
