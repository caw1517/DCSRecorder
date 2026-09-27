"""Compare every packaged native value with the source and verify pinned guards."""
import argparse
import bisect
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
combined=m.get('combined_probe',False)
assert text[0]==('DCS_ENGINE_COMBINED_V1' if combined else 'DCS_NATIVE_ENGINE_PROBE_V1')
rows=[list(map(float,line.split()))for line in text[2:]]
assert len(rows)==len(source)==int(text[1])==m['samples']
origin=source[0][0]
for row,raw in zip(rows,source):
    raw[0]-=origin
    assert len(row)==(11 if combined else 7) and all(abs(a-b)<1e-8 for a,b in zip(row[:7],raw))
if combined:
    appearance=[];order=None
    for line in args.capture.read_text(encoding='utf-8-sig').splitlines():
        prefix='DCSENGINE_MISSION,1,'
        if prefix not in line:continue
        r=next(csv.reader([line.split(prefix,1)[1]]))
        if r[0]=='BEGIN':appearance=[];order=None
        elif r[0]=='CHANNELS':order=list(map(int,r[2:]))
        elif r[0]=='DATA':
            values=dict(zip(order,map(float,r[8:])))
            appearance.append([float(r[3]),*[values[c]for c in (28,29,89,90)]])
    times=[r[0]for r in appearance]
    for row in rows:
        absolute=origin+row[0]
        assert times[0]-.05<=absolute<=times[-1]+.05
        t=max(times[0],min(times[-1],absolute))
        i=max(0,min(bisect.bisect_right(times,t)-1,len(times)-2))
        a,b=appearance[i:i+2];u=(t-a[0])/(b[0]-a[0])
        assert all(abs(row[6+c]-(a[c]+u*(b[c]-a[c])))<1e-8 for c in range(1,5))
    assert all(max(r[c]for r in rows)-min(r[c]for r in rows)>.1 for c in (7,8,9,10))
assert max(r[2]for r in rows)>1 and max(r[3]for r in rows)>2,'above-one inputs must survive'
images={'image':PE(ROOT/'results/sound-routing-2026-09-27/dcs-analysis.exe'),
        'sound':PE(Path('D:/DCS World/bin/Sound.dll'))}
cpp=(ROOT/'engine-prototype/parameter_playback.cpp').read_text()
guards=re.findall(r'matches\((image|sound)\+(0x[0-9a-f]+),std::array<unsigned char,(\d+)>\{([^}]+)\}',cpp)
assert len(guards)==8
for name,rva,count,values in guards:
    expected=bytes(int(v.strip(),0)for v in values.split(','));pe=images[name];offset=pe.offset(int(rva,16))
    assert len(expected)==int(count) and pe.data[offset:offset+len(expected)]==expected,(name,rva)
print(f'PASS: all {len(rows)} native samples and timestamps match; appearance alignment checked={combined}; above-one values retained; E0/F0 equality; stock descriptor; hashes; all eight guards')
