import json,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent
repo='caw1517/DCSRecorder'
def gh(*args):return subprocess.check_output(['gh',*args,'--repo',repo],text=True)
task=json.loads(gh('issue','view','23','--json','body,title'))
parent=json.loads(gh('issue','view','11','--json','body,title'))
for number,current,name in [(23,task,'task'),(11,parent,'parent')]:
 # The first PowerShell snapshot replaced a Unicode dash. Use the reviewed
 # direct-Python snapshot for the parent so existing text is preserved exactly.
 filename='parent-current.json' if name=='parent' else 'task-before.json'
 before=json.loads((p/filename).read_text(encoding='utf-8-sig'))
 assert current['body']==before['body'],f'Issue {number} changed; review concurrent edits'
assert task['body'].count('- [ ]')==3
task_body=task['body'].replace('- [ ]','- [x]')
old='- [ ] 4. [Prove hot-ground staging and first taxi movement](https://github.com/caw1517/DCSRecorder/issues/23)'
assert parent['body'].count(old)==1
parent_body=parent['body'].replace(old,old.replace('[ ]','[x]',1))
marker='## Wayfinder decisions'
assert parent_body.count(marker)==1
pointer='## Ground staging execution evidence\n\n- [Prove hot-ground staging and first taxi movement](https://github.com/caw1517/DCSRecorder/issues/23#issuecomment-5943183433): real short hot-ground hold, three-second countdown and first taxi release accepted by the user; source/contact evidence and measured startup, integration and strobe-timing residuals retained. Broader taxi, numerical-tolerance and parked-completion gates remain open.\n\n'
parent_body=parent_body.replace(marker,pointer+marker)
(p/'task-completed.md').write_text(task_body,encoding='utf-8')
(p/'parent-updated.md').write_text(parent_body,encoding='utf-8')
print(gh('issue','edit','23','--body-file',str(p/'task-completed.md')).strip())
print(gh('issue','close','23','--reason','completed').strip())
print(gh('issue','edit','11','--body-file',str(p/'parent-updated.md')).strip())
checked=json.loads(gh('issue','view','23','--json','state,body'))
assert checked['state']=='CLOSED' and checked['body']==task_body
checked_parent=json.loads(gh('issue','view','11','--json','state,body'))
assert checked_parent['state']=='OPEN' and checked_parent['body']==parent_body
print('Verified: ground task closed with three checks complete; parent remains open with step 4 checked and evidence linked.')
