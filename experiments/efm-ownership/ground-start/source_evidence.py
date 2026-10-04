"""Validate a bounded ground experiment against the retained real contact stream."""
import hashlib
import math
from pathlib import Path


def validate(path, metadata, raw, log_path):
    # This trial is intentionally bound to the reviewed short user take.
    expected='d5bf1359c33276536924e42f28a114bdb4562cce083b8044dfef8e7a40a25791'
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
        raise ValueError('Ground trial requires the reviewed real source take')
    if metadata.get('capture_build')!='2.9.30.28536' or metadata.get('livery')!='Blue Angels Jet Team':
        raise ValueError('Ground trial build/livery mismatch')
    runs=[]
    for line in Path(log_path).read_text(encoding='utf-8',errors='replace').splitlines():
        if 'DCSGROUND,1,' not in line:continue
        event=line.split('DCSGROUND,1,',1)[1].split(',')
        if event[0]=='BEGIN':runs.append(dict(begin=event,rows=[],end=None,errors=[]))
        if not runs:continue
        if event[0]=='DATA':runs[-1]['rows'].append(event)
        elif event[0]=='END':runs[-1]['end']=event
        elif event[0]=='ERROR':runs[-1]['errors'].append(event)
    matches=[r for r in runs if len(r['rows'])==len(raw) and r['rows'] and float(r['rows'][0][3])==float(raw[0]['t'])]
    if len(matches)!=1:raise ValueError('Missing or ambiguous paired ground evidence')
    run=matches[0]
    if run['errors'] or run['end']!=['END',run['begin'][1],str(len(raw)),'stopped']:
        raise ValueError('Incomplete ground evidence')
    for i,(row,evidence) in enumerate(zip(raw,run['rows']),1):
        if len(evidence)!=11 or evidence[1]!=run['begin'][1] or int(evidence[2])!=i or float(evidence[3])!=float(row['t']):
            raise ValueError('Ground sample alignment mismatch')
        values=list(map(float,evidence[4:]))
        if not all(math.isfinite(v) for v in values):raise ValueError('Nonfinite ground evidence')
        unit,air,height,agl,life,life0,surface=values
        if unit!=float(metadata['source_unit_id']) or air!=0 or life!=life0 or life<=0 or surface!=5:
            raise ValueError('Source ground/contact/health mismatch')
        if abs(float(row['y'])-height-agl)>1e-7 or not 1.7<agl<1.95:
            raise ValueError('Source terrain association mismatch')
        if any(float(row['arg_'+str(c)])<.99 for c in (0,3,5)):
            raise ValueError('Ground trial requires deployed gear')
    if len(raw)!=991 or not 5<=float(raw[-1]['t'])-float(raw[0]['t'])<=30:
        raise ValueError('Ground trial duration/sample count mismatch')
    return dict(source_sha256=expected,contact_log_sha256=hashlib.sha256(Path(log_path).read_bytes()).hexdigest(),
                samples=len(raw),scope='One measured ground take; experimental playback, not general ground eligibility')
