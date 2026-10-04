import csv,json,math
from pathlib import Path
p=Path(__file__).resolve().parent
initial=json.loads((p.parent/'ground-tape/initial.json').read_text())['raw']
expected=json.loads((p.parent/'ground-hold-26844/package-v3/manifest.json').read_text())['initial']['expected']
channels=[0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29]
samples=[];contacts=[];witness=[];events=[]
for line in (p/'raw/dcs.log').open(errors='replace'):
 if 'DCSR_RELEASE ' not in line:continue
 a=line.split('DCSR_RELEASE ',1)[1].strip().split(',')
 if a[0]=='SAMPLE' and a[1]=='waiting':
  if a[2]=='StagedPlayback':samples.append(a)
  elif a[2]=='SceneWitness':witness.append(a)
 elif a[0]=='CONTACT' and a[1]=='waiting' and a[2]=='StagedPlayback':contacts.append(a)
 elif a[0] in ['READY','INSPECTION_COMPLETE','FAILED']:events.append(line.strip())
def maxerr(indices,targets):return max(abs(float(r[i])-target) for r in samples for i,target in zip(indices,targets))
pose={}
for r in csv.DictReader((p/'raw/ground-pose-27692.csv').open()):
 if None in r or any(v is None for v in r.values()) or r['phase'] not in ['after_step','after_animation']:continue
 s=pose.setdefault(r['phase'],{'rows':0,'position_error_max':0.,'replay_max':0.})
 s['rows']+=1;s['position_error_max']=max(s['position_error_max'],max(abs(float(r['precise_'+a])-float(r['target_'+a])) for a in 'xyz'));s['replay_max']=max(s['replay_max'],float(r['replay_time']))
out={'events':events,'samples':len(samples),'hold_span_s':float(samples[-1][3])-float(samples[0][3]),
 'mission_position_error_max_m':maxerr(range(4,7),[float(initial[k]) for k in ['x','y','z']]),
 'mission_basis_component_error_max':maxerr(range(7,13),[float(initial[k]) for k in ['fx','fy','fz','ux','uy','uz']]),
 'mission_velocity_max_mps':max(math.sqrt(sum(float(r[i])**2 for i in range(13,16))) for r in samples),
 'snapshot_channels':len(channels),'snapshot_error_max':maxerr(range(18,51),[float(expected[str(c)]) for c in channels]),
 'contacts':len(contacts),'in_air':sorted(set(r[6] for r in contacts)),'life':sorted(set(r[9] for r in contacts)),
 'life0':sorted(set(r[10] for r in contacts)),'surface':sorted(set(r[11] for r in contacts)),
 'origin_agl_m':sorted(set(r[8] for r in contacts)),
 'witness_displacement_m':math.dist([float(v) for v in witness[0][4:7]],[float(v) for v in witness[-1][4:7]]),
 'boundaries':pose}
engine=list(csv.DictReader((p/'raw/engine-27692.csv').open()))
engine=[r for r in engine if None not in r and r['returned'] is not None]
out['engine_rows']=len(engine)
out['engine_override_values']={f'{e}/{c}':sorted(set(r['returned'] for r in engine if r['engine']==e and r['channel']==c)) for e in ['1','2'] for c in ['0','1','2']}
out['engine_unoverridden']=sum(r['overridden']!='1' for r in engine)
out['engine_unoverridden_by_engine']={e:sum(r['overridden']!='1' and r['engine']==e for r in engine) for e in sorted(set(r['engine'] for r in engine))}
out['startup_note']='Full-run extrema above include initial 0.00-0.10 s startup substeps; stable interval is reported separately, not discarded.'
samples=[r for r in samples if float(r[3])>=.12]
out['stable_interval']={'start_s':float(samples[0][3]),'end_s':float(samples[-1][3]),'samples':len(samples),
 'position_error_max_m':maxerr(range(4,7),[float(initial[k]) for k in ['x','y','z']]),
 'basis_component_error_max':maxerr(range(7,13),[float(initial[k]) for k in ['fx','fy','fz','ux','uy','uz']])}
(p/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
