"""Match read-only snapshot pointers against a known loaded DLL export base."""
import argparse,json,re,struct
from pathlib import Path
from inspect_pe import PE

p=argparse.ArgumentParser()
p.add_argument('image'); p.add_argument('snapshot'); p.add_argument('exports')
p.add_argument('module_base',type=lambda s:int(s,0))
a=p.parse_args()
pe=PE(a.image,a.snapshot)
exports={}
for line in Path(a.exports).read_text().splitlines():
    m=re.match(r'\s+\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)',line)
    if m: exports[a.module_base+int(m[1],16)]=m[2]
imports={}
for s in pe.sections:
    if s['name']!='.rdata': continue
    for offset in range(0,s['size']-7,8):
        pointer=pe.u64(s['raw']+offset)
        if pointer in exports:
            rva=s['rva']+offset
            imports[rva]={'dll':'AIFM.dll','symbol':exports[pointer],'iat_rva':hex(rva)}
print(json.dumps({'module_base':hex(a.module_base),'imports':list(imports.values()),'calls':pe.calls(imports)},indent=2))
