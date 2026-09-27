"""Stage the real Export RPM samples, preserving their own sample timestamps."""
import csv
import math
from analyze import analyze

def prepare(logfile,target):
    summary=analyze(logfile)[-1]
    assert summary['complete'] and summary['alignment_screen_passes']
    rows=[]
    for line in logfile.read_text(encoding='utf-8-sig',errors='replace').splitlines():
        if 'DCSENGINE_MISSION,1,BEGIN,' in line:rows=[]
        prefix='DCSENGINE_EXPORT,1,DATA,'
        if prefix not in line:continue
        fields=next(csv.reader(['DATA,'+line.split(prefix,1)[1]]))
        assert len(fields)==17 and int(fields[2])==len(rows)+1
        rows.append([float(fields[3]),float(fields[10])/100,float(fields[11])/100])
    assert len(rows)==summary['rows'] and len(rows)>1
    origin=rows[0][0]
    for i,row in enumerate(rows):
        row[0]-=origin
        assert all(math.isfinite(v)for v in row) and all(0<=v<=1.1 for v in row[1:])
        if i:assert 0<row[0]-rows[i-1][0]<=0.15
    target.write_text('DCS_CORE_RPM_PROBE_V1\n'+str(len(rows))+'\n'+
        '\n'.join(' '.join(format(v,'.12g')for v in row)for row in rows)+'\n',encoding='ascii')
    return {'samples':len(rows),'duration':rows[-1][0],'origin':origin,
            'mapping':'Export RPM percent / 100 -> native core getter; candidate mapping, live validation required',
            'ranges':[[min(r[i]for r in rows),max(r[i]for r in rows)]for i in (1,2)]}
