"""Compare every packaged native value with the source and verify pinned guards."""
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
parser=argparse.ArgumentParser();parser.add_argument('package',type=Path);parser.add_argument('capture',type=Path)
args=parser.parse_args();pkg=args.package
m=json.loads((pkg/'manifest.json').read_text());mod=pkg/m['module']
assert m['parameter_probe'] and not (mod/'Sounds').exists()
donor=(ROOT/'package/hornet-prototype/DCSRecorder-Hornet-Probe/aircraft.lua').read_text(encoding='utf-8-sig')
assert (mod/'aircraft.lua').read_text(encoding='utf-8')==donor.replace('DCSRecorder-Hornet-Probe',m['module'])
for name,digest in m['files'].items():assert hashlib.sha256((pkg/name).read_bytes()).hexdigest()==digest
source=[]
for line in args.capture.read_text(encoding='utf-8-sig').splitlines():
    if 'DCSENGINE_MISSION,1,BEGIN,'in line:source=[]
    prefix='DCSENGINE_NATIVE,1,DATA,'
    if prefix in line:
        r=next(csv.reader(['DATA,'+line.split(prefix,1)[1]]))
        assert len(r)==26 and r[11]=='OK'
        assert float(r[17])==float(r[18]) and float(r[21])==float(r[22])
        source.append([float(r[i])for i in (3,15,16,17,19,20,21)])
text=(mod/'bin/recorded-engine.txt').read_text().splitlines()
assert text[0]=='DCS_NATIVE_ENGINE_PROBE_V1'
rows=[list(map(float,line.split()))for line in text[2:]]
assert len(rows)==len(source)==int(text[1])==m['samples']
origin=source[0][0]
for row,raw in zip(rows,source):
    raw[0]-=origin
    assert len(row)==7 and all(abs(a-b)<1e-8 for a,b in zip(row,raw))
assert max(r[2]for r in rows)>1 and max(r[3]for r in rows)>2,'above-one inputs must survive'
images={'image':PE(ROOT/'results/sound-routing-2026-09-27/dcs-analysis.exe'),
        'sound':PE(Path('D:/DCS World/bin/Sound.dll'))}
cpp=(ROOT/'engine-prototype/parameter_playback.cpp').read_text()
guards=re.findall(r'matches\((image|sound)\+(0x[0-9a-f]+),std::array<unsigned char,(\d+)>\{([^}]+)\}',cpp)
assert len(guards)==5
for name,rva,count,values in guards:
    expected=bytes(int(v.strip(),0)for v in values.split(','));pe=images[name];offset=pe.offset(int(rva,16))
    assert len(expected)==int(count) and pe.data[offset:offset+len(expected)]==expected,(name,rva)
print(f'PASS: all {len(rows)} native samples, six channels and timestamps match; above-one values retained; E0/F0 equality; stock descriptor; hashes; all five added guards')
