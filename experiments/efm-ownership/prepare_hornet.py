"""Local-only Hornet prototype packaging; references the user's installed DCS assets."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

root=Path(__file__).resolve().parent
dcs=Path('D:/DCS World')
package=root/'package/hornet-prototype'
mod=package/'DCSRecorder-Hornet-Probe'
for folder in ('bin','Cockpit/Scripts','Liveries/DCSRecorder-Hornet-Probe'):
    (mod/folder).mkdir(parents=True,exist_ok=True)
stock=dcs/'CoreMods/aircraft/FA-18C'

# Use the actual Hornet descriptor and its base builder. Register only our new
# type; never re-register stock types or their weapon/loadout declarations.
base=(stock/'FA-18A.lua').read_text(encoding='utf-8-sig')
assert base.count('\nmake_FA_18()')==1
base=base.replace('\nmake_FA_18()','\n-- Stock registration omitted.')
base=base.replace('function aim9_station(', 'local function aim9_station(')
base=base.replace('function make_FA_18(', 'local function make_FA_18(')
assert base.count('add_aircraft(FA_18_Base)')==1
base=base.replace('add_aircraft(FA_18_Base)', '''
    assert(FA_18_Base.Name == 'FA-18C_hornet', 'Unexpected Hornet descriptor')
    FA_18_Base.Name = 'DCSRecorder-Hornet-Probe'
    FA_18_Base.DisplayName = 'DCS Recorder Hornet Prototype'
    FA_18_Base.WorldID = WSTYPE_PLACEHOLDER
    FA_18_Base.attribute[4] = WSTYPE_PLACEHOLDER
    FA_18_Base.shape_table_data[1].name = 'DCSRecorder-Hornet-Probe'
    FA_18_Base.shape_table_data[1].username = 'DCSRecorder-Hornet-Probe'
    FA_18_Base.shape_table_data[1].index = WSTYPE_PLACEHOLDER
    add_aircraft(FA_18_Base)
''')
hornet=(stock/'FA-18C_hornet.lua').read_text(encoding='utf-8-sig')
assert hornet.count('local function fpu_8a_fuel_tank')==1
hornet=hornet.split('local function fpu_8a_fuel_tank')[0]
hornet=hornet.replace('function make_FA_18C_hornet()', 'local function make_FA_18C_hornet()')
# The plugin environment lacks setmetatable; use a generated local descriptor
# instead of a runtime proxy environment, following the validated TF-51D setup.
descriptor=(base+'\n'+hornet).replace('current_mod_path','"./CoreMods/aircraft/FA-18C"')
(mod/'aircraft.lua').write_text(descriptor,encoding='utf-8')
# The editor resolves datalink scripts relative to the registered descriptor's
# _file, now this custom mod. Keep the stock relative dependency tree intact.
shutil.copytree(stock/'Datalinks',mod/'Datalinks',dirs_exist_ok=True)
(mod/'entry.lua').write_text('''local id = 'DCSRecorder-Hornet-Probe'
local root = current_mod_path
declare_plugin(id, {
    installed=true, dirName=root, displayName='DCS Recorder Hornet Prototype',
    fileMenuName=id, version='0.1', state='installed',
    binaries={'HornetProbe'}, load_immediately=true,
})
mount_vfs_model_path('./CoreMods/aircraft/FA-18C/Shapes')
mount_vfs_texture_path('./CoreMods/aircraft/FA-18C/Textures/FA-18C')
mount_vfs_liveries_path(root..'/Liveries')
dofile(root..'/aircraft.lua')
make_flyable(id, root..'/Cockpit/Scripts/', {id, 'HornetProbe'}, nil)
plugin_done()
''',encoding='utf-8')
shutil.copy2(root/'mod/Cockpit/Scripts/device_init.lua',mod/'Cockpit/Scripts/device_init.lua')
shutil.copy2(root/'build/Release/HornetProbe.dll',mod/'bin/HornetProbe.dll')
# Installed ED livery, copied only into this user's local prototype package.
# The new type needs its own livery lookup directory. Do not distribute assets.
shutil.copy2(stock/'Liveries/FA-18C_hornet/Blue Angels Jet Team.zip',mod/'Liveries/DCSRecorder-Hornet-Probe/Blue Angels Jet Team.zip')
baseline=Path('C:/Users/w_can/Saved Games/DCS/Missions/EFM-Probe-climbing-turn-formation-zero-wind.miz')
donor=dcs/'Mods/aircraft/FA-18C/Missions/QuickStart/Caucasus FA-18C Free Flight.miz'
with zipfile.ZipFile(baseline) as z: (package/'baseline.lua').write_bytes(z.read('mission'))
with zipfile.ZipFile(donor) as z: (package/'donor.lua').write_bytes(z.read('mission'))
data=(root/'hornet_roll_data.h').read_text()
pull=float(re.search(r'pull_duration=([0-9.e+-]+)',data)[1])
maneuver=float(re.search(r'maneuver_duration=([0-9.e+-]+)',data)[1])
briefing=(f'Hornet equal-altitude left-roll test: run 75 seconds. Clean jets, lights off, calm air, initial 400 KIAS. '
          f'Control 5s; gradual pull begins 7s; left roll begins {7+pull:.1f}s at 14 degrees nose-up; '
          f'peak pitch about 30 degrees; wings/nose level {7+maneuver:.1f}s; release {13+maneuver:.1f}s. '
          'Main roll 1.8g geometric normal load, easing to 1g over final 6s. '
          'Returns to pre-pull altitude and original heading, offset left. Speed bleeds and recovers under constant modeled thrust and drag; no speed hold. '
          'Approximate engine model; not calibrated Hornet performance or verified demonstration procedure.')
(package/'roll-briefing.lua').write_text('return '+json.dumps(briefing)+'\n')
subprocess.run([str(dcs/'bin/luae.exe'),str(root/'generate_hornet_mission.lua'),str(package/'baseline.lua'),str(package/'donor.lua'),str(package/'mission'),str(package/'roll-briefing.lua')],check=True)
subprocess.run([str(dcs/'bin/luae.exe'),str(root/'verify_hornet_requirements.lua'),str(package/'mission'),str(dcs/'Mods/aircraft/FA-18C/entry.lua'),str(dcs/'MissionEditor/modules/me_mission.lua')],check=True)
subprocess.run([str(dcs/'bin/luae.exe'),str(root/'verify_hornet_routes.lua'),str(package/'mission'),str(dcs/'MissionEditor/modules/me_route.lua')],check=True)
subprocess.run([str(dcs/'bin/luae.exe'),str(root/'verify_hornet_configuration.lua'),str(package/'mission'),str(dcs)],check=True)
mission=package/'EFM-Probe-Hornet-left-roll-400KIAS.miz'
with zipfile.ZipFile(baseline) as src, zipfile.ZipFile(mission,'w',zipfile.ZIP_DEFLATED) as dest:
    for entry in src.infolist():
        dest.writestr(entry, (package/'mission').read_bytes() if entry.filename=='mission' else src.read(entry.filename))
# Syntax checks do not establish registration success; DCS startup is that test.
checks=package/'syntax-check.lua'
paths=[mod/'entry.lua',mod/'aircraft.lua',package/'mission']
checks.write_text('\n'.join('assert(loadfile('+json.dumps(p.as_posix())+'))' for p in paths)+"\nprint('PASS: Hornet plugin, descriptor and mission Lua syntax')\n")
subprocess.run([str(dcs/'bin/luae.exe'),str(checks)],check=True)
subprocess.run([str(dcs/'bin/luae.exe'),str(root/'verify_hornet_datalink.lua'),str(mod/'aircraft.lua'),str(dcs/'MissionEditor/modules/me_datalinks.lua')],check=True)
manifest={'prototype':'Hornet equal-altitude positive-g left roll, constant modeled thrust; live validation pending',
          'mission_filename':mission.name,
          'dll_sha256':hashlib.sha256((mod/'bin/HornetProbe.dll').read_bytes()).hexdigest(),
          'mission_sha256':hashlib.sha256(mission.read_bytes()).hexdigest(),
          'initial_mission_speed_m_s':225.0215739890135,'nominal_kias':400,
          'speed_schedule':'Initial 400 KCAS at 2000m; integrate constant thrust, parabolic drag and gravity. Not calibrated Hornet performance.',
          'altitude_target':'pre-pull altitude','heading_target':'original heading with left displacement',
          'pull_start_mission_seconds':7,'roll_start_mission_seconds':7+pull,
          'roll_end_mission_seconds':7+maneuver,'release_mission_seconds':13+maneuver,
          'roll_degrees':-360,'geometric_normal_load_factor':1.8,'recovery_seconds':6,
          'geometry_data_sha256':hashlib.sha256((root/'hornet_roll_data.h').read_bytes()).hexdigest(),
          'livery':'Blue Angels Jet Team','player_type':'FA-18C_hornet','playback_type':'DCSRecorder-Hornet-Probe'}
(package/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
