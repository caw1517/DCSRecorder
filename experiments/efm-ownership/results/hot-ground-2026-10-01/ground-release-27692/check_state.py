import csv,json,collections,math
from pathlib import Path
p=Path(__file__).resolve().parent
channels=[0,3,5,9,10,11,12,13,14,15,16,17,18,21,38,88,190,191,192,193,210,212,1,6,4,101,103,102,2,89,90,28,29]
native={};retention=0.;rows=0
for r in csv.DictReader((p/'raw/exterior-27692.csv').open()):
 if None in r or r['after'] is None or float(r['elapsed'])<=0:continue
 elapsed=float(r['elapsed']);arg=int(r['arg']);requested=float(r['requested']);after=float(r['after'])
 native[round(elapsed/.02),arg]=requested
 retention=max(retention,abs(after-requested));rows+=1
mission_error=0.;missing=0;compared=0
for line in (p/'raw/dcs.log').open(errors='replace'):
 if 'DCSR_RELEASE SAMPLE,playing,StagedPlayback,' not in line:continue
 r=list(map(float,line.split('DCSR_RELEASE SAMPLE,playing,StagedPlayback,',1)[1].strip().split(',')))
 if r[13]<=0:continue
 tick=round(r[13]/.02)
 for i,arg in enumerate(channels):
  if (tick,arg) not in native:missing+=1;continue
  mission_error=max(mission_error,abs(r[15+i]-native[tick,arg]));compared+=1
out={'post_animation_rows':rows,'post_animation_requested_vs_retained_max':retention,'mission_channel_comparisons':compared,'mission_vs_native_requested_max':mission_error,'missing':missing,
 'note':'Native requested values implement interpolation and sampled strobe-edge hold. Nearest-source-row comparison is not a valid strobe-edge test; float boundary timing can select the preceding strobe row for one 20 ms sample.'}
(p/'state-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
assert rows and compared and not missing and retention<1e-6 and mission_error<1e-6
