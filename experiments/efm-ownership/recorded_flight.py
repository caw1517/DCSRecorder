"""Validate a recorded-flight CSV and emit the native playback tape. No DCS control."""
import argparse,csv,json,math
from pathlib import Path
from exterior_state import PROFILE, CHANNELS, STATE_COLUMNS, columns

def quaternion(f,u,r):
    m=[[f[i],u[i],r[i]] for i in range(3)];trace=sum(m[i][i] for i in range(3))
    if trace>0:
        s=2*math.sqrt(1+trace);q=[s/4,(m[2][1]-m[1][2])/s,(m[0][2]-m[2][0])/s,(m[1][0]-m[0][1])/s]
    else:
        i=max(range(3),key=lambda i:m[i][i]);j=(i+1)%3;k=(i+2)%3
        s=2*math.sqrt(1+m[i][i]-m[j][j]-m[k][k]);q=[0.0]*4
        q[0]=(m[k][j]-m[j][k])/s;q[i+1]=s/4;q[j+1]=(m[i][j]+m[j][i])/s;q[k+1]=(m[i][k]+m[k][i])/s
    length=math.sqrt(sum(v*v for v in q));return [v/length for v in q]

def read(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f: rows=list(csv.reader(f))
    if not rows or rows[0] not in (['DCSREC','1'],['DCSREC','2']): raise ValueError('Unsupported recording version')
    version=int(rows[0][1])
    metadata={};i=1
    while i<len(rows) and rows[i] and rows[i][0]!='t':
        if len(rows[i])!=2: raise ValueError('Invalid metadata')
        metadata[rows[i][0]]=rows[i][1];i+=1
    if metadata.get('aircraft')!='FA-18C_hornet' or metadata.get('theatre')!='Caucasus' or not metadata.get('livery'):
        raise ValueError('First playback prototype supports a named-livery Hornet on Caucasus only')
    if version==2 and metadata.get('state_profile')!=PROFILE: raise ValueError('Unsupported exterior state profile')
    if version==1 and 'state_profile' in metadata: raise ValueError('Legacy recording cannot declare exterior state')
    expected=columns(version)
    if i>=len(rows) or rows[i]!=expected: raise ValueError('Invalid recording columns')
    names=rows[i];body=rows[i+1:]
    if not body or not body[-1] or body[-1][0]!='END': raise ValueError('Recording is incomplete; stop the take before importing')
    footer=body.pop()
    if len(footer)!=3 or int(footer[2])!=len(body): raise ValueError('Recording footer/sample count mismatch')
    if footer[1] not in ('user_stop','mission_stop','mission_restart','new_take'): raise ValueError('Recording ended with aircraft loss/error')
    samples=[];raw=[]
    for row in body:
        if len(row)!=len(names): raise ValueError('Truncated sample row')
        d=dict(zip(names,row));raw.append(d)
        exterior=[float(d[k]) for k in STATE_COLUMNS] if version==2 else []
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
        if not 70<=math.sqrt(sum(x*x for x in v))<=260 or not 0<=brake<=1:
            raise ValueError('Take exceeds current airborne speed/animation support; ground transitions require ground playback support')
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
    for sample in samples:sample[0]-=start
    metadata.update(duration=samples[-1][0],samples=len(samples),source_time=start,recording_version=version,
                    exterior_available=version==2)
    return metadata,samples,raw

def convert(source,destination):
    metadata,samples,_=read(source)
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    text=f'DCSREC_PLAYBACK_V{metadata["recording_version"]}\n'+str(len(samples))+'\n'
    if metadata['exterior_available']:text+=PROFILE+'\n'
    text+=''.join(' '.join(f'{v:.15g}' for v in row)+'\n' for row in samples)
    destination.write_text(text,encoding='ascii')
    destination.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('recording');parser.add_argument('output')
    args=parser.parse_args();print(json.dumps(convert(args.recording,args.output),indent=2))
