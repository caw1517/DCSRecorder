import csv,json,math
from pathlib import Path
root=Path(r'E:\Projects\DCS_Recorder\experiments\efm-ownership\results\nose-pitch-2026-09-26')
def angle(a,b):
    value=sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
    return math.degrees(math.acos(max(-1,min(1,value))))
def axis(row,prefix,start):return [float(row[f'{prefix}{i}']) for i in range(start,start+3)]
def basis_angle(row,a,b):
    return max(angle(axis(row,a,k),axis(row,b,k)) for k in (0,4,8))
runs=[]
for row in csv.DictReader((root/'native-motion-15596.csv').open()):
    if row['status']=='captured':runs.append([])
    elif runs:runs[-1].append(row)
report=[]
for n,rows in enumerate(runs,1):
    if not rows:continue
    begin=float(rows[0]['object_time']);points=[]
    for row in rows:
        if row['status']!='called':continue
        elapsed=float(row['object_time'])-begin
        points.append({'elapsed':round(elapsed,4),'forward_correction_deg':angle(axis(row,'command',0),axis(row,'before',0)),
                      'basis_correction_deg':basis_angle(row,'command','before'),
                      'after_command_error_deg':basis_angle(row,'command','actual'),
                      'position_correction_m':math.dist(axis(row,'command',12),axis(row,'before',12)),
                      'bank_deg':math.degrees(math.atan2(float(row['command9']),float(row['command5'])))})
    peaks=sorted((p for p in points if p['elapsed']>0.2),key=lambda p:p['basis_correction_deg'],reverse=True)[:8]
    summary={'run':n,'duration':round(float(rows[-1]['object_time'])-begin,4),'rows':len(rows),'peaks':peaks}
    report.append(summary)
(root/'trace-analysis.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
