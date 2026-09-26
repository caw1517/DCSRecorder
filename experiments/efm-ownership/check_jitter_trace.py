"""Replay recorded native telemetry; distinguish input error from intertick drift."""
import argparse,csv,json,math,statistics
from pathlib import Path

def describe(x):
    x=sorted(x);return {'mean':statistics.mean(x),'p95':x[int(.95*(len(x)-1))],'max':max(x)}

def analyze(path):
    rows=list(csv.DictReader(Path(path).open()))
    values={k:[] for k in ['position_correction_m','command_integration_error_m',
        'velocity_overwrite_m_s','nose_velocity_fit_m_s','predicted_drift_residual_m']}
    for a,b in zip(rows,rows[1:]):
        if a['status']!='called' or b['status']!='called':continue
        dt=float(b['object_time'])-float(a['object_time'])
        if not .019<dt<.021 or not 7<float(b['object_time'])<42:continue
        get=lambda r,key,n:[float(r[f'{key}{k}']) for k in range(n)]
        old=get(a,'actual',16);before=get(b,'before',16);target=get(b,'command',16)
        v=get(a,'velocity_command',3);vb=get(b,'velocity_before',3)
        speed=math.sqrt(sum(x*x for x in vb));nose=[before[k]*speed for k in range(3)]
        prediction=[old[12+k]+nose[k]*dt for k in range(3)]
        values['position_correction_m'].append(math.dist(before[12:15],target[12:15]))
        values['command_integration_error_m'].append(math.dist([old[12+k]+v[k]*dt for k in range(3)],target[12:15]))
        values['velocity_overwrite_m_s'].append(math.dist(vb,v))
        values['nose_velocity_fit_m_s'].append(math.dist(vb,nose))
        values['predicted_drift_residual_m'].append(math.dist(prediction,before[12:15]))
    if not values['position_correction_m']:
        raise ValueError('No consecutive controlled samples in the first-take comparison window (7..42 s)')
    report={k:describe(v) for k,v in values.items()}
    controlled=[r for r in rows if r['status']=='called' and 7<float(r['object_time'])<42]
    report['step_hook']={
        'samples':len(controlled),
        'confirmed_samples':sum(r.get('step_hook_status')=='called' and int(r.get('step_hook_applied') or 0)>0 for r in controlled),
        'calls':max(int(r.get('step_hook_calls') or 0) for r in controlled),
        'applied':max(int(r.get('step_hook_applied') or 0) for r in controlled)}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('trace');p.add_argument('--assert-smooth',action='store_true');p.add_argument('--require-step-hook',action='store_true');p.add_argument('--output');a=p.parse_args()
    report=analyze(a.trace);text=json.dumps(report,indent=2);print(text)
    if a.output:Path(a.output).write_text(text+'\n')
    if a.assert_smooth and report['position_correction_m']['p95']>.06:
        raise SystemExit('FAIL: intertick position correction exceeds 6 cm (synthetic roll maximum was 3.63 cm)')
    if a.require_step_hook and report['step_hook']['confirmed_samples']<.95*report['step_hook']['samples']:
        raise SystemExit('FAIL: pre-integration velocity restoration was not confirmed throughout playback')
