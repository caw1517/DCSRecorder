"""Quantify pose correction before each command, without assuming renderer timing."""
import argparse,csv,json,math,statistics
from pathlib import Path

def axis_error(a,b):
    # atan2 avoids acos precision loss near zero with float basis vectors.
    errors=[]
    for start in (0,4,8):
        x=a[start:start+3];y=b[start:start+3]
        cross=[x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]]
        errors.append(math.degrees(math.atan2(math.sqrt(sum(v*v for v in cross)),sum(u*v for u,v in zip(x,y)))))
    return max(errors)

def describe(values):
    values=sorted(values)
    if not values:return None
    return {'count':len(values),'mean':statistics.mean(values),'p95':values[min(len(values)-1,int(len(values)*.95))],'max':max(values)}

def roll_ab(rows):
    """Attribute each interval to the action at its START, not its end."""
    samples=[r for r in rows if r['status']=='called']
    groups={}
    for previous,current in zip(samples,samples[1:]):
        enabled=previous.get('roll_neutralized')
        if enabled not in ('0','1'):continue
        phase='neutralized' if enabled=='1' else ('baseline_before' if float(previous['object_time'])<15 else 'baseline_after')
        g=groups.setdefault(phase,{k:[] for k in ('intertick_attitude_change_deg','abs_roll_change_deg','roll_rate_after_rad_s','roll_rate_next_rad_s','post_command_error_deg')})
        old=[float(previous[f'actual{i}']) for i in range(16)]
        new=[float(current[f'before{i}']) for i in range(16)]
        dot=lambda a,b:sum(x*y for x,y in zip(a,b))
        roll=math.degrees(math.atan2(dot(new[4:7],old[8:11]),dot(new[4:7],old[4:7])))
        g['intertick_attitude_change_deg'].append(axis_error(old,new))
        g['abs_roll_change_deg'].append(abs(roll))
        g['roll_rate_after_rad_s'].append(float(previous['rates_after0']))
        g['roll_rate_next_rad_s'].append(float(current['rates_before0']))
        g['post_command_error_deg'].append(axis_error([float(current[f'actual{i}']) for i in range(16)],[float(current[f'command{i}']) for i in range(16)]))
    return {phase:{k:describe(v) for k,v in metrics.items()} for phase,metrics in groups.items()}

def gate_ab(rows):
    groups={}
    previous=None
    for current in rows:
        if current['status']!='called':
            previous=None
            continue
        if previous and 'updates_suppressed' in previous:
            phase='suppressed' if previous['updates_suppressed']=='1' else 'normal'
            g=groups.setdefault(phase,{'intertick_attitude_change_deg':[],'intertick_position_change_m':[]})
            old=[float(previous[f'actual{i}']) for i in range(16)]
            new=[float(current[f'before{i}']) for i in range(16)]
            g['intertick_attitude_change_deg'].append(axis_error(old,new))
            g['intertick_position_change_m'].append(math.dist(old[12:15],new[12:15]))
        previous=current
    return {phase:{k:describe(v) for k,v in metrics.items()} for phase,metrics in groups.items()}

def motion_ab(rows):
    groups={};previous=None
    for current in rows:
        if current['status']!='called':
            previous=None
            continue
        if previous and previous.get('motion_matched') in ('0','1'):
            phase='matched' if previous['motion_matched']=='1' else ('baseline_before' if float(previous['object_time'])<15 else 'baseline_after')
            g=groups.setdefault(phase,{k:[] for k in ('pre_position_error_m','pre_attitude_error_deg','velocity_change_m_s','angular_change_rad_s')})
            new=[float(current[f'before{i}']) for i in range(16)]
            target=[float(current[f'command{i}']) for i in range(16)]
            g['pre_position_error_m'].append(math.dist(new[12:15],target[12:15]))
            g['pre_attitude_error_deg'].append(axis_error(new,target))
            for metric,before,after in (('velocity_change_m_s','velocity_before','velocity_after'),('angular_change_rad_s','rates_before','rates_after')):
                g[metric].append(math.dist([float(current[f'{before}{i}']) for i in range(3)],[float(previous[f'{after}{i}']) for i in range(3)]))
        previous=current
    return {phase:{k:describe(v) for k,v in metrics.items()} for phase,metrics in groups.items()}

def analyze(rows):
    samples=[]
    for row in rows:
        if row['status']!='called':continue
        pose={p:[float(row[f'{p}{i}']) for i in range(16)] for p in ('command','actual','before')}
        samples.append((row,pose))
    metrics={k:[] for k in ('pre_command_error_deg','post_command_error_deg','intertick_attitude_change_deg','command_attitude_step_deg','pre_position_error_m','wall_interval_ms','simulation_interval_ms','apply_ms')}
    for i,(r,p) in enumerate(samples):
        metrics['pre_command_error_deg'].append(axis_error(p['before'],p['command']))
        metrics['post_command_error_deg'].append(axis_error(p['actual'],p['command']))
        metrics['pre_position_error_m'].append(math.dist(p['before'][12:15],p['command'][12:15]))
        metrics['apply_ms'].append(float(r['apply_ms']))
        if i:
            previous,q=samples[i-1]
            metrics['intertick_attitude_change_deg'].append(axis_error(p['before'],q['actual']))
            metrics['command_attitude_step_deg'].append(axis_error(p['command'],q['command']))
            metrics['wall_interval_ms'].append(1000*(float(r['wall_seconds'])-float(previous['wall_seconds'])))
            metrics['simulation_interval_ms'].append(1000*(float(r['object_time'])-float(previous['object_time'])))
    return {k:describe(v) for k,v in metrics.items()}

def report_run(rows):
    report=analyze(rows)
    phases=roll_ab(rows)
    if phases:report['roll_ab']=phases
    gates=gate_ab(rows)
    if gates:report['update_gate_ab']=gates
    motion=motion_ab(rows)
    if motion:report['motion_matching_ab']=motion
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('csv_file');args=parser.parse_args()
    rows=list(csv.DictReader(Path(args.csv_file).open()))
    runs=[]
    for row in rows:
        if not runs or row['status']=='captured':runs.append([])
        runs[-1].append(row)
    report=report_run(runs[0]) if len(runs)==1 else {'runs':[report_run(run) for run in runs]}
    print(json.dumps(report,indent=2))
