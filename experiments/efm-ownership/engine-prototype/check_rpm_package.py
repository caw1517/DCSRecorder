"""Read-only check of RPM extraction, stock descriptor, hashes and caller guard."""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parent/'native-interface-inspection'))
from inspect_pe import PE

parser=argparse.ArgumentParser()
parser.add_argument('package',type=Path)
parser.add_argument('capture',type=Path)
parser.add_argument('--dcs',type=Path,default=Path('D:/DCS World'))
args=parser.parse_args()
pkg=args.package
m=json.loads((pkg/'manifest.json').read_text())
mod=pkg/m['module']
assert m['rpm_probe'] and not (mod/'Sounds').exists()
donor=(ROOT/'package/hornet-prototype/DCSRecorder-Hornet-Probe/aircraft.lua').read_text(encoding='utf-8-sig')
assert (mod/'aircraft.lua').read_text(encoding='utf-8')==donor.replace('DCSRecorder-Hornet-Probe',m['module'])
assert m['channels']==['rpm_left','rpm_right']
for name,digest in m['files'].items():
    assert hashlib.sha256((pkg/name).read_bytes()).hexdigest()==digest
text=(mod/'bin/recorded-rpm.txt').read_text().splitlines()
assert text[0]=='DCS_CORE_RPM_PROBE_V1'
rows=[list(map(float,line.split()))for line in text[2:]]
source=[]
for line in args.capture.read_text(encoding='utf-8-sig').splitlines():
    if 'DCSENGINE_MISSION,1,BEGIN,' in line: source=[]
    if 'DCSENGINE_EXPORT,1,DATA,' in line:
        f=next(csv.reader([line.split('DCSENGINE_EXPORT,1,DATA,',1)[1]]))
        source.append([float(f[2]),float(f[9])/100,float(f[10])/100])
assert len(rows)==len(source)==int(text[1])==m['samples'] and len(rows)>1
origin=source[0][0]
for row,raw in zip(rows,source):
    raw[0]-=origin
    assert all(abs(a-b)<1e-8 for a,b in zip(row,raw))
pe=PE(args.dcs/'bin/Sound.dll')
source_cpp=(ROOT/'engine-prototype/rpm_playback.cpp').read_text()
rva,count,values=re.search(r'matches\(sound\+(0x[0-9a-f]+),std::array<unsigned char,(\d+)>\{([^}]+)\}',source_cpp).groups()
expected=bytes(int(v.strip(),0)for v in values.split(','))
offset=pe.offset(int(rva,16))
assert len(expected)==int(count) and pe.data[offset:offset+len(expected)]==expected
print(f'PASS: all {len(rows)} RPM samples match capture timestamps and RPM/100; original aircraft descriptor; no custom sounds; package hashes; installed Sound.dll getter-call guard')
print(json.dumps(m['rpm_metadata'],indent=2))
