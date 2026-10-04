"""Prepare an additive real hot-ground take; never widen playback eligibility."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
REPO = Path('E:/Projects/DCS_Recorder')
EFM = REPO / 'experiments/efm-ownership'
spec = importlib.util.spec_from_file_location('mission_data', REPO / 'companion/mission-identity-probe.prototype.py')
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)
BUILD = '2.9.30.28536'
NAME = '047-Hornet-Hot-Ground-Capture.miz'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_mission(path):
    with zipfile.ZipFile(path) as z:
        return data.LuaData(z.read('mission').decode('utf-8-sig')).mission()


def prepare(source, output, dcs):
    assert json.loads((dcs / 'autoupdate.cfg').read_text(encoding='utf-8-sig'))['version'] == BUILD
    m = read_mission(source)
    ground_source = dcs / 'Mods/aircraft/FA-18C/Missions/QuickStart/Caucasus FA-18C Cold and Dark.miz'
    ground = read_mission(ground_source)
    assert m['theatre'] == ground['theatre'] == 'Caucasus'
    assert all(v['speed'] == 0 for v in m['weather']['wind'].values())
    old = m['coalition']['blue']['country'][1]['plane']['group'][1]['units'][1]
    assert old['type'] == 'FA-18C_hornet' and old['skill'] == 'Player'
    assert old['livery_id'] == 'Blue Angels Jet Team'
    assert len(m['trigrules']) == 2
    startup = m['trigrules'][1]['actions'][1]['text']
    for required in ('DCSRECORDER_WHEELS=true', 'DCSRECORDER_SMOKE=true', 'capture_build,' + BUILD, 'frame-batch-v1'):
        assert required in startup, required
    selected = []
    for country in ground['coalition']['blue']['country'].values():
        for group in country.get('plane', {}).get('group', {}).values():
            if any(u['skill'] == 'Player' for u in group['units'].values()):
                selected.append((country, group))
    assert len(selected) == 1
    country, group = selected[0]
    group = copy.deepcopy(group)
    assert len(group['units']) == 1
    unit = group['units'][1]
    first = group['route']['points'][1]
    assert unit['type'] == 'FA-18C_hornet'
    assert first['type'] == 'TakeOffParking' and first['airdromeId'] == 25
    assert unit['parking_id'] == '15' and unit['parking'] == '1'
    original_placement = {k: unit[k] for k in ('x', 'y', 'heading', 'parking', 'parking_id')}
    unit.update(name='Observer', livery_id=old['livery_id'], payload=copy.deepcopy(old['payload']), speed=0)
    group.update(name='GroundCapture', lateActivation=False, uncontrolled=False)
    first.update(type='TakeOffParkingHot', action='From Parking Area Hot')
    for point in group['route']['points'].values():
        point['task'] = dict(id='ComboTask', params=dict(tasks={}))
    m['coalition']['blue']['country'] = {1: dict(id=country['id'], name=country['name'], plane=dict(group={1: group}))}
    m['coalition']['red']['country'] = {}
    m['coalition']['neutrals']['country'] = {}
    m['start_time'] = 12 * 3600
    description = ('HOT-GROUND SOURCE CAPTURE. Stock Hornet, engines running, Blue Angels livery, Kobuleti parking 15. '
        'Lights come on automatically. Hold the wheel brakes and let the aircraft settle. '
        'F10 > DCS Recorder > Start recording. Remain stationary for a few seconds, then taxi straight '
        'at walking speed for about 10 seconds, brake to a full stop and remain stopped for a few seconds. '
        'F10 > DCS Recorder > Stop recording. Leave DCS open for log collection. No Active Pause. '
        'This records the real source; held playback is a later separate check.')
    # Replace only the old user-facing prompts; retain full recorder behavior.
    prompt = "trigger.action.outText('Fly your own Hornet. F10 > DCS Recorder > Start recording. Start with 5 seconds straight and level, then fly a gentle turn or roll. Stop recording through the same menu.',25)"
    assert startup.count(prompt) == 1
    startup = startup.replace(prompt, '')
    snapshot_prompt = "trigger.action.outText(\"SNAPSHOT CAPTURE."
    idx = startup.find(snapshot_prompt)
    if idx < 0:
        idx = startup.find("trigger.action.outText('SNAPSHOT CAPTURE.")
    assert idx >= 0, 'Expected prepared snapshot instructions'
    startup = startup[:idx]
    binding = hashlib.sha256((digest(source) + digest(ground_source) + json.dumps(original_placement, sort_keys=True)).encode()).hexdigest()
    startup += '\nDCSGROUND_SOURCE_ID=' + data.serialize(binding) + '\n'
    startup += (HERE / 'contact.lua').read_text(encoding='utf-8')
    startup += '\ntrigger.action.outText(' + data.serialize(description) + ',45)\n'
    m['descriptionText'] = description
    m['trigrules'][1]['comment'] = 'Full-state hot-ground recording and paired contact evidence'
    m['trigrules'][1]['actions'][1]['text'] = startup
    m['trig']['actions'][1] = 'a_do_script(' + data.serialize(startup) + ');'
    output.mkdir(parents=True, exist_ok=False)
    script = output / 'mission.lua'
    script.write_text('mission = ' + data.serialize(m), encoding='utf-8')
    lua = dcs / 'bin/luae.exe'
    for validator, args in (
        (EFM / 'verify_hornet_requirements.lua', [script, dcs / 'Mods/aircraft/FA-18C/entry.lua', dcs / 'MissionEditor/modules/me_mission.lua']),
        (EFM / 'verify_hornet_routes.lua', [script, dcs / 'MissionEditor/modules/me_route.lua', 1]),
        (EFM / 'held-start/check_capture.lua', [script, dcs]),
        (HERE / 'check_capture.lua', [script]),
    ):
        subprocess.run([str(lua), str(validator), *map(str, args)], check=True)
    mission = output / NAME
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(mission, 'x', zipfile.ZIP_DEFLATED) as dst:
        for entry in src.infolist():
            dst.writestr(entry, script.read_bytes() if entry.filename == 'mission' else src.read(entry.filename))
    manifest = dict(profile='hot-ground-source-capture-v1', dcs_build=BUILD, mission=NAME, sha256=digest(mission),
                    source=str(source), source_sha256=digest(source), ground_source=str(ground_source),
                    ground_source_sha256=digest(ground_source), contact_binding=binding, placement=original_placement,
                    preparation_sources={p.name: digest(p) for p in (HERE / 'prepare_capture.py', HERE / 'contact.lua', HERE / 'check_capture.lua')},
                    status='Offline checks passed; real capture and hot-ground playback acceptance pending')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--dcs', type=Path, default=Path('D:/DCS World'))
    a = p.parse_args()
    prepare(a.source, a.output, a.dcs)
