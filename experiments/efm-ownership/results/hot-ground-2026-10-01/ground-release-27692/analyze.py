import csv,json,math,collections
from pathlib import Path
p=Path(__file__).resolve().parent
tape=[list(map(float,l.split())) for l in (p.parent/'ground-tape/recorded-flight.txt').read_text().splitlines()[7:]]
channels=[0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29]
indices=[12,13,14,15,16,17,18,19,20,21,22,23,24,11,42,35,36,37,38,39,40,41,43,44,45,46,47,48,49,27,28,25,26]
samples=collections.defaultdict(list);contacts=collections.defaultdict(list);events=[]
for line in (p/'raw/dcs.log').open(errors='replace'):
 if 'DCSR_RELEASE ' not in line or 'DCSR_RELEASE_BRIDGE' in line:continue
 a=line.split('DCSR_RELEASE ',1)[1].strip().split(',')
 if a[0]=='SAMPLE' and a[2]=='StagedPlayback':samples[a[1]].append(list(map(float,a[3:])))
 elif a[0]=='CONTACT' and a[2]=='StagedPlayback':contacts[a[1]].append(list(map(float,a[3:])))
 elif a[0] not in ['SAMPLE','CONTACT']:events.append(a)
def metric(rows):
 result={'samples':len(rows),'model_time':[rows[0][0],rows[-1][0]],'replay_time':[rows[0][13],rows[-1][13]],'position_error_max_m':0,'state_error_max':0,'velocity_error_max_mps':0,'max_adjacent_displacement_m':0}
 for r in rows:
  t=r[13];s=tape[min(len(tape)-1,max(0,round(t/.02)))]
  result['position_error_max_m']=max(result['position_error_max_m'],math.dist(r[1:4],s[1:4]))
  result['velocity_error_max_mps']=max(result['velocity_error_max_mps'],math.dist(r[10:13],s[8:11] if t>0 else [0,0,0]))
  result['state_error_max']=max(result['state_error_max'],max(abs(r[15+i]-s[j]) for i,j in enumerate(indices)))
 result['max_adjacent_displacement_m']=max([math.dist(a[1:4],b[1:4]) for a,b in zip(rows,rows[1:])] or [0])
 return result
out={'events':events,'phases':{k:metric(v) for k,v in samples.items() if k in ['countdown','requested','starting','playing']},'contact':{}}
for phase,rows in contacts.items():
 if phase not in ['countdown','requested','starting','playing']:continue
 out['contact'][phase]={'rows':len(rows),'in_air':sorted(set(r[3] for r in rows)),'life':sorted(set(r[6] for r in rows)),'life0':sorted(set(r[7] for r in rows)),'surface':sorted(set(r[8] for r in rows)),'agl_range_m':[min(r[5] for r in rows),max(r[5] for r in rows)]}
countdown=next(float(a[1]) for a in events if a[0]=='COUNTDOWN')
request=next(float(a[3]) for a in events if a[0]=='REQUEST')
release=next(float(a[3]) for a in events if a[0]=='PLAYER_RELEASED')
running=next(a for a in events if a[0]=='NATIVE_RUNNING')
out['countdown_duration_s']=request-countdown
out['release_ack_delay_s']=release-request
out['first_native_running_after_player_s']=float(running[1])-release
out['first_running_replay_time_s']=float(running[2])
out['last_held_to_first_playing_displacement_m']=math.dist(samples['countdown'][-1][1:4],samples['playing'][0][1:4])
out['first_playing_sample']=samples['playing'][0]
out['final_playing_sample']=samples['playing'][-1]
trace={}
for r in csv.DictReader((p/'raw/ground-pose-27692.csv').open()):
 if None in r or any(v is None for v in r.values()) or r['phase'] not in ['before_step_restored','after_step','after_animation'] or float(r['model_time'])<countdown:continue
 key=('countdown' if float(r['replay_time'])==0 else 'playing')+'/'+r['phase']
 s=trace.setdefault(key,{'rows':0,'error_max_m':0.,'vertical_error_max_m':0.})
 s['rows']+=1
 s['error_max_m']=max(s['error_max_m'],math.dist([float(r['precise_'+a]) for a in 'xyz'],[float(r['target_'+a]) for a in 'xyz']))
 s['vertical_error_max_m']=max(s['vertical_error_max_m'],abs(float(r['precise_y'])-float(r['target_y'])))
out['trace']=trace
(p/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
