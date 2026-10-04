"""Predict the mission DCS 2.9.30 holds after loading an authored playback copy.

The release hook compares DCS.getCurrentMission() exactly against expected.lua,
so the reference must equal DCS's loaded form, not the archive we wrote. Each
rule below was observed in real loaded archives (source-v4-live,
recording-v4-live, playback-v1-live-1); `check` re-proves the model against them. Anything the model
does not predict still fails readiness at runtime: nothing is ignored there.
"""
from pathlib import Path
import copy, math, subprocess, sys, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'companion'))
import authored_missions as a

HERE = Path(__file__).resolve().parent
FIELDS = ('theatre', 'weather', 'coalition', 'trigrules', 'date', 'start_time', 'forcedOptions')


def number(value):
    # DCS serializes the loaded mission with 14 significant digits (route ETA and
    # derived heading observed); the live comparison sees that loaded form.
    if isinstance(value, float):
        return float(format(value, '.14g'))
    if isinstance(value, dict):
        return {k: number(v) for k, v in value.items()}
    return value


def start_parameters(mission):
    """me_mission.lua fixUnitsPos/setUnitStartParameters (DCS 2.9.30): units of a
    group not starting from the ground take speed/altitude from route point 1 and
    heading/psi from the bearing to point 2, unless the group sets manualHeading."""
    for coalition in mission.get('coalition', {}).values():
        for country in (coalition.get('country') or {}).values():
            for kind in ('plane', 'helicopter'):
                for group in ((country.get(kind) or {}).get('group') or {}).values():
                    points = (group.get('route') or {}).get('points') or {}
                    p1, p2 = points.get(1), points.get(2)
                    if not p1 or p1.get('action') in ('From Ground Area', 'From Ground Area Hot', 'On Road'):
                        continue
                    for unit in group['units'].values():
                        unit.update(speed=p1['speed'], alt=p1['alt'], alt_type=p1['alt_type'])
                        if p2 and group.get('manualHeading') is not True:
                            unit['heading'] = math.atan2(p2['y']-p1['y'], p2['x']-p1['x'])
                        if p2:
                            unit['psi'] = math.atan2(-(p2['y']-p1['y']), p2['x']-p1['x'])


def defaults(mission, dcs, custom_aircraft, custom_type):
    with tempfile.TemporaryDirectory() as tmp:
        source, target = Path(tmp)/'in.lua', Path(tmp)/'out.lua'
        source.write_text('mission = '+a.serialize(mission), encoding='utf-8')
        subprocess.run([str(Path(dcs)/'bin/luae.exe'), str(HERE/'prepare_defaults.lua'), str(source), str(target),
                        str(dcs), str(custom_aircraft), str(HERE/'loaded_defaults.lua'), custom_type],
                       check=True, capture_output=True)
        parser = a.LuaData(target.read_text(encoding='utf-8')); parser.take('return')
        return parser.value()


def loaded(mission, dcs='D:/DCS World', custom_aircraft=None, custom_type='-'):
    m = copy.deepcopy(mission)
    start_parameters(m)
    resolved = defaults(m, dcs, custom_aircraft or Path(dcs)/'CoreMods/aircraft/FA-18C/FA-18C_hornet.lua', custom_type)
    for row in a.aircraft(m):
        # me_mission.lua fixRadio (DCS 2.9.30) on load: a newly placed group saved
        # without radioSet loads with radioSet=false (observed live, 061-Enforcement-Auto).
        group = row['group']
        if group.get('frequency') is None or group.get('modulation') is None:
            raise ValueError(f"{row['unit']['name']}: group radio frequency is unset; its loaded default is unobserved.")
        group.setdefault('communication', True)
        group['radioSet'] = group.get('radioSet') or False
        unit = row['unit']
        unit.update(copy.deepcopy(resolved[unit['unitId']]))
        cartridge = unit.get('dataCartridge')
        if cartridge is not None:
            if set(cartridge) != {'GroupsPoints', 'Points'} or cartridge['Points'] or any(cartridge['GroupsPoints'].values()):
                raise ValueError(f"{unit['name']}: nonempty data cartridge; its loaded form is unobserved.")
            del unit['dataCartridge']
        if unit.get('skill') not in ('Player', 'Client'):
            unit.pop('Radio', None)
        for radio in (unit.get('Radio') or {}).values():
            radio.setdefault('channelsNames', {})
    for rule in m.get('trigrules', {}).values():
        for action in rule.get('actions', {}).values():
            if action.get('predicate') == 'a_out_text_delay':
                action.setdefault('KeyDict_text', action['text'])
    return {f: number(m[f]) for f in FIELDS if f in m}


def differences(x, y, path=''):
    if isinstance(x, dict) and isinstance(y, dict):
        out = []
        for k in sorted(x.keys() | y.keys(), key=str):
            out += differences(x.get(k, '<absent>'), y.get(k, '<absent>'), f'{path}[{k}]')
        return out
    return [] if type(x) == type(y) and x == y or isinstance(x, (int, float)) and isinstance(y, (int, float)) and x == y else [path]


def check(prepared_miz, loaded_miz, custom_aircraft=None, custom_type='-'):
    """Prove the model on one real pair: archive written vs archive DCS loaded."""
    mission = lambda p: a.LuaData(a.zip_entries(Path(p).read_bytes())['mission'].decode('utf-8-sig')).mission()
    predicted, actual = loaded(mission(prepared_miz), custom_aircraft=custom_aircraft, custom_type=custom_type), mission(loaded_miz)
    return [d for f in predicted for d in differences(predicted[f], actual.get(f), f)]


if __name__ == '__main__':
    # Optional: <module aircraft.lua> <module type> for a playback package.
    found = check(*sys.argv[1:5])
    for line in found:
        print('FAIL unpredicted loaded difference: '+line)
    sys.exit(1 if found else print('PASS loaded mission fields match the predicted DCS load exactly'))
