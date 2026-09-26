"""Read-only PE32+ import/callsite and MSVC RTTI index for local DCS binaries.

Byte-pattern callsites are candidates, not decoded instructions: verify with
dumpbin before drawing conclusions. Nothing here loads or executes the image.
"""
import argparse
import bisect
import hashlib
import json
import struct
from pathlib import Path


class PE:
    def __init__(self, path, snapshot=None):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        pe = self.u32(0x3C)
        assert self.data[pe:pe+4] == b'PE\0\0'
        count = self.u16(pe+6)
        optional_size = self.u16(pe+20)
        optional = pe+24
        assert self.u16(optional) == 0x20B
        self.base = self.u64(optional+24)
        self.import_rva = self.u32(optional+112+8)
        self.exception_rva = self.u32(optional+112+3*8)
        self.exception_size = self.u32(optional+112+3*8+4)
        self.sections = []
        for i in range(count):
            p = optional+optional_size+40*i
            self.sections.append(dict(name=self.data[p:p+8].rstrip(b'\0').decode(),
                size=self.u32(p+16), rva=self.u32(p+12), raw=self.u32(p+20),
                executable=bool(self.u32(p+36) & 0x20000000)))
        if snapshot:
            folder = Path(snapshot)
            for line in (folder/'sections.txt').read_text().splitlines():
                parts = line.split()
                if parts[0] == 'image_base':
                    self.base = int(parts[1],16)
                elif parts[0] == 'section':
                    _,name,rva,size = parts
                    section = next(s for s in self.sections if s['name']==name)
                    blob = (folder/(name[1:]+'.bin')).read_bytes()
                    assert len(blob)==int(size,16) and section['rva']==int(rva,16)
                    section.update(raw=len(self.data),size=len(blob))
                    self.data += blob
                    if name=='.pdata':
                        self.exception_rva=int(rva,16)
                        self.exception_size=len(blob)
        self.functions = []
        if self.exception_rva:
            p = self.offset(self.exception_rva)
            for i in range(self.exception_size//12):
                start,end,unwind = struct.unpack_from('<III',self.data,p+12*i)
                valid_code=any(s['executable'] and s['rva']<=start<end<=s['rva']+s['size'] for s in self.sections)
                if not valid_code:
                    self.functions=[]
                    break # Packed/stale exception tables cannot establish function bounds.
                self.functions.append((start,end,unwind))
        self.functions.sort()
        self.starts = [f[0] for f in self.functions]

    def u16(self,p): return struct.unpack_from('<H',self.data,p)[0]
    def u32(self,p): return struct.unpack_from('<I',self.data,p)[0]
    def u64(self,p): return struct.unpack_from('<Q',self.data,p)[0]
    def offset(self,rva):
        for s in self.sections:
            if s['rva'] <= rva < s['rva']+s['size']:
                return s['raw']+rva-s['rva']
        raise ValueError(f'RVA outside raw data: {rva:x}')
    def rva(self,offset):
        for s in self.sections:
            if s['raw'] <= offset < s['raw']+s['size']:
                return s['rva']+offset-s['raw']
        raise ValueError('Offset outside sections')
    def string(self,rva):
        p=self.offset(rva)
        return self.data[p:self.data.index(0,p)].decode('ascii')
    def function(self,rva):
        i=bisect.bisect_right(self.starts,rva)-1
        if i>=0 and rva<self.functions[i][1]:
            start,end,_=self.functions[i]
            return {'start_rva':hex(start),'end_rva':hex(end)}
        return None
    def imports(self):
        p=self.offset(self.import_rva)
        result={}
        while True:
            names,_,_,name,iat=struct.unpack_from('<IIIII',self.data,p)
            if not name: break
            dll=self.string(name)
            q=self.offset(names or iat)
            for i in range(100000):
                entry=self.u64(q+8*i)
                if not entry: break
                symbol=f'ordinal:{entry & 0xffff}' if entry>>63 else self.string(entry+2)
                result[iat+8*i]={'dll':dll,'symbol':symbol,'iat_rva':hex(iat+8*i)}
            p+=20
        return result
    def calls(self,imports):
        result=[]
        for s in self.sections:
            if not s['executable']: continue
            code=self.data[s['raw']:s['raw']+s['size']]
            for opcode in (b'\xff\x15',b'\xff\x25'):
                p=0
                while True:
                    p=code.find(opcode,p)
                    if p<0: break
                    if p+6<=len(code):
                        site=s['rva']+p
                        target=site+6+struct.unpack_from('<i',code,p+2)[0]
                        if target in imports:
                            result.append(dict(imports[target],site_rva=hex(site),
                                kind='call' if opcode[1]==0x15 else 'jump',function=self.function(site)))
                    p+=1
        return result
    def rtti(self,name):
        needle=name.encode()+b'\0'
        pos=self.data.find(needle)
        if pos<0: return []
        type_rva=self.rva(pos-16)
        result=[]
        for s in self.sections:
            if s['executable']: continue
            for p in range(s['raw'],s['raw']+s['size']-24,4):
                sig,offset,construction,typ,hierarchy,self_rva=struct.unpack_from('<IIIIII',self.data,p)
                if sig!=1 or typ!=type_rva or self_rva!=self.rva(p): continue
                pointer=struct.pack('<Q',self.base+self_rva)
                vtables=[]
                q=0
                while True:
                    q=self.data.find(pointer,q)
                    if q<0: break
                    try: vtables.append(hex(self.rva(q)+8))
                    except ValueError: pass
                    q+=1
                result.append(dict(type_rva=hex(type_rva),locator_rva=hex(self_rva),
                    offset=offset,construction=construction,hierarchy_rva=hex(hierarchy),vtable_rvas=vtables))
        return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('--dll',default='AIFM.dll')
    parser.add_argument('--type',default='.?AVwoAIPlane@@')
    parser.add_argument('--snapshot')
    parser.add_argument('--analysis-image',help='Write a section-overlay file for offline dumpbin; never execute it')
    args=parser.parse_args()
    pe=PE(args.image,args.snapshot)
    if args.analysis_image:
        data=bytearray(pe.data)
        header=pe.u32(0x3c)
        optional=header+24
        struct.pack_into('<Q',data,optional+24,pe.base)
        for i,s in enumerate(pe.sections):
            p=optional+pe.u16(header+20)+40*i
            struct.pack_into('<I',data,p+16,s['size'])
            struct.pack_into('<I',data,p+20,s['raw'])
        Path(args.analysis_image).write_bytes(data)
    imports={r:i for r,i in pe.imports().items() if i['dll'].lower()==args.dll.lower()}
    print(json.dumps(dict(image=pe.path.name,sha256=hashlib.sha256(pe.data).hexdigest(),
        image_base=hex(pe.base),imports=list(imports.values()),calls=pe.calls(imports),rtti=pe.rtti(args.type)),indent=2))
