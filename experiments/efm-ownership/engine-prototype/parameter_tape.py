"""Extract measured native channels, never derive thrust from RPM or phase labels."""
import csv
import math
from analyze_native_capture import inspect

CHANNELS=['core1','fan1','thrust1','core2','fan2','thrust2']
def prepare(logfile,target):
    summary=inspect(logfile)[-1]
    assert summary['passes'],summary['issues']
    rows=[]
    for line in logfile.read_text(encoding='utf-8-sig',errors='replace').splitlines():
        if 'DCSENGINE_MISSION,1,BEGIN,'in line:rows=[]
        prefix='DCSENGINE_NATIVE,1,DATA,'
        if prefix not in line:continue
        r=next(csv.reader(['DATA,'+line.split(prefix,1)[1]]))
        assert len(r)==26 and r[11]=='OK' and int(r[2])==len(rows)+1
        # Playback's guarded F0 implementation forwards to E0. Require measured
        # equality on every sample before using that forwarding relationship.
        assert float(r[17])==float(r[18]) and float(r[21])==float(r[22]),'E0/F0 must be captured separately'
        rows.append([float(r[i])for i in (3,15,16,17,19,20,21)])
    assert len(rows)==summary['rows'] and len(rows)>1
    origin=rows[0][0]
    for i,row in enumerate(rows):
        row[0]-=origin
        assert all(math.isfinite(v)for v in row)
        assert all(0<=v<=(4 if c%3==2 else 1.2)for c,v in enumerate(row[1:]))
        if i:assert 0<row[0]-rows[i-1][0]<=.15
    target.write_text('DCS_NATIVE_ENGINE_PROBE_V1\n'+str(len(rows))+'\n'+
        '\n'.join(' '.join(format(v,'.12g')for v in row)for row in rows)+'\n',encoding='ascii')
    return {'samples':len(rows),'duration':rows[-1][0],'origin':origin,'channels':CHANNELS,
        'mapping':'Measured native getters, unscaled; exact E0/F0 equality verified; playback F0 forwards to E0',
        'ranges':{name:[min(r[c]for r in rows),max(r[c]for r in rows)]for c,name in enumerate(CHANNELS,1)}}
