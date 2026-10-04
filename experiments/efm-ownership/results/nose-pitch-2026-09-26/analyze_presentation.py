"""Compare temporary cached-pose diagnostics with the controller's native trace."""
import argparse
import csv
import json
import math
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('diagnostic',type=Path)
parser.add_argument('native',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()

def axis(row,prefix,k):return [float(row[f'{prefix}{i}']) for i in range(k,k+3)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def angle(a,b):return math.degrees(math.acos(max(-1,min(1,dot(a,b)/math.sqrt(dot(a,a)*dot(b,b))))))
def split_runs(rows,phase):
    runs=[]
    previous=None
    for row in rows:
        if phase and row.get('phase')!=phase:continue
        if 'status' in row and row['status']!='called':continue
        t=float(row['object_time'])
        if previous is None or t<=previous:runs.append([])
        runs[-1].append(row);previous=t
    return runs

native=split_runs(csv.DictReader(args.native.open()),None)
diagnostic=split_runs(csv.DictReader(args.diagnostic.open()),'before')
assert len(native)==len(diagnostic), 'Run counts differ; correlate runs before analysis'
reports=[]
for run,(commands,reads) in enumerate(zip(native,diagnostic),1):
    lookup={round(float(row['object_time']),2):row for row in commands}
    points=[];seen=set();start=float(commands[0]['object_time'])
    for read in reads:
        if read['read_ok']!='1':continue
        cache_time=float(read['cache_time'])
        if cache_time in seen or cache_time-start<.2:continue
        seen.add(cache_time)
        command=lookup.get(round(cache_time,2))
        if not command:continue
        f,u,r=[axis(command,'command',k) for k in (0,4,8)]
        cf,cu=[axis(read,'cached',k) for k in (0,4)]
        measured_pitch=math.degrees(math.atan2(dot(cf,u),dot(cf,f)))
        measured_yaw=math.degrees(math.atan2(-dot(cf,r),dot(cf,f)))
        # Units/operations observed in the inspected Position(double) path.
        predicted_pitch=float(read['field_4db4'])+(cache_time-float(read['rotation_time']))*float(read['field_22b4'])
        predicted_yaw=math.degrees(float(read['field_56cc'])+(cache_time-float(read['pose_time']))*float(read['field_56d4']))
        points.append({'elapsed':cache_time-start,'cache_time':cache_time,
                       'nose_error_deg':angle(cf,f),'up_error_deg':angle(cu,u),
                       'measured_local_pitch_deg':measured_pitch,'field_pitch_prediction_deg':predicted_pitch,
                       'measured_local_yaw_deg':measured_yaw,'field_yaw_prediction_deg':predicted_yaw,
                       'pitch_residual_deg':measured_pitch-predicted_pitch,
                       'yaw_residual_deg':measured_yaw-predicted_yaw,
                       'other_rotation_flag':int(read['field_21f4'])})
    assert points,'No aligned cached poses; inspect diagnostics'
    report={'run':run,'matched_cache_samples':len(points),
            'peak':max(points,key=lambda p:p['nose_error_deg']),
            'max_abs_pitch_residual_deg':max(abs(p['pitch_residual_deg']) for p in points),
            'max_abs_yaw_residual_deg':max(abs(p['yaw_residual_deg']) for p in points)}
    reports.append(report)
    with args.output.with_name(args.output.stem+f'-run{run}.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(points[0]));writer.writeheader();writer.writerows(points)
args.output.write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
