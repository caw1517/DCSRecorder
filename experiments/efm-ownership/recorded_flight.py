"""Validate a recorded-flight CSV and emit the native playback tape. No DCS control."""
import argparse,csv,json,math
from pathlib import Path
from exterior_state import PROFILE, CHANNELS, STATE_COLUMNS, columns
import engine_state
import smoke_state
import light_state
import canopy_state
import wheel_state
import contact_state

def quaternion(f,u,r):
    m=[[f[i],u[i],r[i]] for i in range(3)];trace=sum(m[i][i] for i in range(3))
    if trace>0:
        s=2*math.sqrt(1+trace);q=[s/4,(m[2][1]-m[1][2])/s,(m[0][2]-m[2][0])/s,(m[1][0]-m[0][1])/s]
    else:
        i=max(range(3),key=lambda i:m[i][i]);j=(i+1)%3;k=(i+2)%3
        s=2*math.sqrt(1+m[i][i]-m[j][j]-m[k][k]);q=[0.0]*4
        q[0]=(m[k][j]-m[j][k])/s;q[i+1]=s/4;q[j+1]=(m[i][j]+m[j][i])/s;q[k+1]=(m[i][k]+m[k][i])/s
    length=math.sqrt(sum(v*v for v in q));return [v/length for v in q]

def read(path, *, ground_trial_log=None):
    with Path(path).open(newline='',encoding='utf-8-sig') as f: rows=list(csv.reader(f))
    if not rows or rows[0] not in (['DCSREC',str(v)] for v in range(1,9)): raise ValueError('Unsupported recording version')
    version=int(rows[0][1])
    metadata={};i=1
    while i<len(rows) and rows[i] and rows[i][0]!='t':
        if len(rows[i])!=2: raise ValueError('Invalid metadata')
        metadata[rows[i][0]]=rows[i][1];i+=1
    if metadata.get('aircraft')!='FA-18C_hornet' or metadata.get('theatre')!='Caucasus' or not metadata.get('livery'):
        raise ValueError('First playback prototype supports a named-livery Hornet on Caucasus only')
    if version>=2 and metadata.get('state_profile')!=PROFILE: raise ValueError('Unsupported exterior state profile')
    if version>=3 and (metadata.get('engine_profile')!=engine_state.PROFILE or metadata.get('capture_build') not in ('2.9.29.27468','2.9.30.28536')):
        raise ValueError('Unsupported native engine profile/build')
    timing=metadata.get('capture_timing')
    if timing is not None and (timing!='frame-batch-v1' or version<3 or metadata.get('capture_build')!='2.9.30.28536'):
        raise ValueError('Unsupported capture timing profile/build')
    if version==1 and 'state_profile' in metadata: raise ValueError('Legacy recording cannot declare exterior state')
    if version<3 and 'engine_profile' in metadata: raise ValueError('Legacy recording cannot declare native engine state')
    if version<4 and any(k.startswith('smoke_') for k in metadata): raise ValueError('Legacy recording cannot declare measured smoke')
    if version>=5 and metadata.get('light_profile')!=light_state.PROFILE: raise ValueError('Unsupported light profile')
    if version<5 and 'light_profile' in metadata: raise ValueError('Legacy recording cannot declare lights')
    if version>=6 and metadata.get('canopy_profile')!=canopy_state.PROFILE: raise ValueError('Unsupported canopy profile')
    if version<6 and 'canopy_profile' in metadata: raise ValueError('Legacy recording cannot declare canopy')
    if version>=7 and metadata.get('wheel_profile')!=wheel_state.PROFILE: raise ValueError('Unsupported wheel profile')
    if version<7 and 'wheel_profile' in metadata: raise ValueError('Legacy recording cannot declare wheels')
    if version>=8 and metadata.get('contact_profile')!=contact_state.PROFILE: raise ValueError('Unsupported contact profile')
    if version<8 and 'contact_profile' in metadata: raise ValueError('Legacy recording cannot declare ground contact')
    has_smoke=version==4 or (version>=5 and 'smoke_profile' in metadata)
    if version>=5 and not has_smoke and any(k.startswith('smoke_') for k in metadata): raise ValueError('Incomplete smoke metadata')
    expected=columns(version,has_smoke)
    if i>=len(rows) or rows[i]!=expected: raise ValueError('Invalid recording columns')
    names=rows[i];body=rows[i+1:]
    if not body or not body[-1] or body[-1][0]!='END': raise ValueError('Recording is incomplete; stop the take before importing')
    footer=body.pop()
    if len(footer)!=3 or int(footer[2])!=len(body): raise ValueError('Recording footer/sample count mismatch')
    if footer[1] not in ('user_stop','mission_stop','mission_restart','new_take'): raise ValueError('Recording ended with aircraft loss/error')
    ground_report=None
    if ground_trial_log is not None:
        import importlib.util
        spec=importlib.util.spec_from_file_location('ground_source_evidence',Path(__file__).parent/'ground-start/source_evidence.py')
        evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
        ground_report=evidence.validate(path,metadata,[dict(zip(names,row)) for row in body],ground_trial_log)
    samples=[];raw=[];flags=[]
    for row in body:
        if len(row)!=len(names): raise ValueError('Truncated sample row')
        d=dict(zip(names,row));raw.append(d)
        exterior=[float(d[k]) for k in STATE_COLUMNS] if version>=2 else []
        if any(not math.isfinite(v) or not (0 if c in (0,3,5) else -1)<=v<=1 for c,v in zip(CHANNELS,exterior)):
            raise ValueError('Invalid exterior state sample')
        vals=[float(d[k]) for k in ['t','x','y','z','fx','fy','fz','ux','uy','uz','rx','ry','rz','vx','vy','vz','speedbrake']]
        if not all(math.isfinite(v) for v in vals): raise ValueError('Non-finite sample')
        t=vals[0];p=vals[1:4];f=vals[4:7];u=vals[7:10];r=vals[10:13];v=vals[13:16];brake=vals[16]
        for a,axis in enumerate([f,u,r]):
            for b,other in enumerate([f,u,r]):
                if abs(sum(x*y for x,y in zip(axis,other))-(1 if a==b else 0))>0.001: raise ValueError('Invalid orientation basis')
        cross=[f[1]*u[2]-f[2]*u[1],f[2]*u[0]-f[0]*u[2],f[0]*u[1]-f[1]*u[0]]
        if sum(x*y for x,y in zip(cross,r))<0.999: raise ValueError('Reflected orientation basis')
        speed=math.sqrt(sum(x*x for x in v))
        elapsed=t-samples[0][0] if samples else 0
        # Version 8 carries source contact per row: grounded rows may be slow or
        # stationary; airborne rows keep the airborne speed envelope.
        grounded=version>=8 and contact_state.parse(d)[0]==0
        flags.append(grounded)
        if ground_report is not None and speed>5:raise ValueError('Ground trial exceeds bounded taxi speed')
        if speed>260:
            raise ValueError(f'Recorded speed {speed:.2f} m/s exceeds the current playback maximum of 260 m/s at {elapsed:.2f} s. '
                             'This limit uses ground speed (about 505 knots), not cockpit indicated airspeed. The recording is saved.')
        if ground_report is None and not grounded and speed<70:
            raise ValueError(f'Recorded speed {speed:.2f} m/s is below the current airborne playback minimum of 70 m/s at {elapsed:.2f} s. '
                             'Ground starts and transitions are not yet supported. The recording is saved.')
        if not 0<=brake<=1:
            raise ValueError(f'Invalid speed-brake value {brake:g} at {elapsed:.2f} s; expected 0 to 1.')
        q=quaternion(f,u,r)
        if samples:
            prev=samples[-1];dt=t-prev[0]
            if not 0<dt<=0.15: raise ValueError('Non-monotonic time or recording gap over 150 ms')
            dot=sum(a*b for a,b in zip(q,prev[4:8]))
            if dot<0:q=[-x for x in q];dot=-dot
            if math.dist(p,[prev[k]+dt*(prev[k+7]+v[k-1])/2 for k in range(1,4)])>max(0.5,dt*8):
                raise ValueError('Position/velocity discontinuity in recorded flight')
        samples.append([t,*p,*q,*v,brake,*exterior])
    if len(samples)<2 or not 5<=samples[-1][0]-samples[0][0]<=300: raise ValueError('Record between 5 and 300 seconds')
    start=samples[0][0]
    if version>=3:
        for sample,engine in zip(samples,engine_state.align(raw,.15 if timing=='frame-batch-v1' else .05)):sample.extend(engine)
    if version>=5:
        for sample,row in zip(samples,raw):
            lights=[float(row[k]) for k in light_state.COLUMNS]
            if any(not math.isfinite(v) or not 0<=v<=1 for v in lights): raise ValueError('Invalid light sample')
            sample.extend(lights)
    if version>=6:
        for sample,row in zip(samples,raw):
            canopy=float(row['arg_38'])
            if not math.isfinite(canopy) or not 0<=canopy<=1: raise ValueError('Invalid canopy sample')
            sample.append(canopy)
    if version>=7:
        for sample,row in zip(samples,raw):
            wheels=[float(row[k]) for k in wheel_state.COLUMNS]
            if any(not math.isfinite(v) or not (-1 if c==2 else 0)<=v<=1 for c,v in zip(wheel_state.CHANNELS,wheels)):
                raise ValueError('Invalid wheel sample')
            sample.extend(wheels)
    # Contact evidence is validated and summarized; endpoint eligibility is separate.
    if version>=8: metadata['contact']=contact_state.summary(raw)
    # Only takes with grounded samples need the native surface tape and controller.
    surface=any(flags)
    if surface:
        for sample,grounded in zip(samples,flags):sample.append(1 if grounded else 0)
    if has_smoke: metadata['smoke_events']=smoke_state.transitions(metadata,raw)
    for sample in samples:sample[0]-=start
    metadata.update(duration=samples[-1][0],samples=len(samples),source_time=start,recording_version=version,
                    exterior_available=version>=2,engine_available=version>=3,smoke_available=has_smoke,lights_available=version>=5,canopy_available=version>=6,wheels_available=version>=7,contact_available=version>=8,surface_available=surface)
    if ground_report is not None:metadata['ground_trial']=ground_report
    return metadata,samples,raw

def convert(source,destination, *, ground_trial_log=None):
    metadata,samples,_=read(source,ground_trial_log=ground_trial_log)
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    # Smoke commands are embedded in the mission. Lights and canopy extend the
    # native tape explicitly; older recordings keep their existing tape version.
    metadata['native_tape_version']=7 if metadata['surface_available'] else 6 if metadata['wheels_available'] else 5 if metadata['canopy_available'] else 4 if metadata['lights_available'] else min(metadata['recording_version'],3)
    text=f'DCSREC_PLAYBACK_V{metadata["native_tape_version"]}\n'+str(len(samples))+'\n'
    if metadata['exterior_available']:text+=PROFILE+'\n'
    if metadata['engine_available']:text+=engine_state.PROFILE+'\n'
    if metadata['lights_available']:text+=light_state.PROFILE+'\n'
    if metadata['canopy_available']:text+=canopy_state.PROFILE+'\n'
    if metadata['wheels_available']:text+=wheel_state.PROFILE+'\n'
    if metadata['surface_available']:text+=contact_state.PROFILE+'\n'
    text+=''.join(' '.join(f'{v:.15g}' for v in row)+'\n' for row in samples)
    destination.write_text(text,encoding='ascii')
    destination.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('recording');parser.add_argument('output')
    args=parser.parse_args();print(json.dumps(convert(args.recording,args.output),indent=2))
