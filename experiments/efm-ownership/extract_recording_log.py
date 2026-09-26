"""Extract completed mission-owned captures from DCS.log. Does not control DCS."""
import argparse,csv,hashlib,io
from pathlib import Path

MARKER='DCSREC_LOG,1,'
COLUMNS='t,x,y,z,fx,fy,fz,ux,uy,uz,rx,ry,rz,vx,vy,vz,speedbrake,rpm_left,rpm_right\n'

def extract(logfile,output):
    active=None;completed=[]
    with Path(logfile).open(encoding='utf-8',errors='replace') as stream:
        for line in stream:
            if not line.endswith('\n'):break # live logger may still be writing this event
            if MARKER not in line:continue
            event=line.partition(MARKER)[2].rstrip('\r\n')
            parts=event.split(',',3)
            if parts[0]=='BEGIN':
                if len(parts)!=3:raise ValueError('Malformed recording start')
                metadata=bytes.fromhex(parts[2]).decode('utf-8')
                if not metadata.startswith('DCSREC,1\n'):raise ValueError('Invalid recording metadata')
                active={'id':parts[1],'metadata':metadata,'rows':[]}
            elif parts[0]=='DATA':
                if not active or parts[1]!=active['id']:continue
                if len(parts)!=4 or int(parts[2])!=len(active['rows'])+1:
                    raise ValueError('Missing or duplicate recording sample in log')
                row=next(csv.reader(io.StringIO(parts[3])))
                if len(row)!=19:raise ValueError('Truncated recording sample in log')
                active['rows'].append(parts[3]+'\n')
            elif parts[0]=='END':
                if not active or parts[1]!=active['id']:continue
                if len(parts)!=4 or int(parts[3])!=len(active['rows']):raise ValueError('Recording end/count mismatch')
                data=active['metadata']+COLUMNS+''.join(active['rows'])+f'END,{parts[2]},{parts[3]}\n'
                encoded=data.encode('utf-8');digest=hashlib.sha256(encoded).hexdigest()[:16]
                destination=Path(output)/f"take-{active['id']}-{digest}.csv"
                destination.parent.mkdir(parents=True,exist_ok=True)
                if destination.exists() and destination.read_bytes()!=encoded:raise ValueError('Recording filename collision')
                destination.write_bytes(encoded);completed.append(destination);active=None
    return completed

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('logfile');p.add_argument('output');a=p.parse_args()
    paths=extract(a.logfile,a.output)
    if not paths:raise SystemExit('No completed recording found. Stop the take through F10 before extracting.')
    for path in paths:print(path)
