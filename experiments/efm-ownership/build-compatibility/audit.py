"""Read-only audit of captured sections against existing native byte guards.

Candidate matches are search results, never permission to update addresses or
invoke native methods. Reports contain metadata only, not vendor code bytes.
"""
import argparse
import bisect
import hashlib
import json
import re
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULES = ('dcs', 'worldgeneral', 'sound', 'aifm', 'cockpit')


class Snapshot:
    def __init__(self, directory):
        manifests = list(directory.glob('*/sections.txt'))
        if len(manifests) != 1:
            raise ValueError(f'Expected one section manifest: {directory}')
        self.parts = {}
        self.metadata = []
        for line in manifests[0].read_text().splitlines():
            fields = line.split()
            if fields[0] == 'image_base':
                self.base = int(fields[1], 16)
            elif fields[0] == 'section':
                _, name, rva, size = fields
                blob = (manifests[0].parent / (name[1:] + '.bin')).read_bytes()
                if name in self.parts or len(blob) != int(size, 16):
                    raise ValueError(f'Duplicate or incomplete section: {name}')
                self.parts[name] = (int(rva, 16), blob)
                self.metadata.append(dict(name=name, rva='0x'+rva, size=len(blob),
                                          sha256=hashlib.sha256(blob).hexdigest()))
            else:
                raise ValueError(f'Incomplete capture: {line}')
        if set(self.parts) != {'.text', '.rdata', '.pdata'}:
            raise ValueError('Expected exactly three read-only sections')
        self.functions = list(struct.iter_unpack('<III', self.parts['.pdata'][1]))
        self.starts = [f[0] for f in self.functions]
        text_rva, text = self.parts['.text']
        self.function_table_valid = self.starts == sorted(self.starts) and all(
            text_rva <= a < b <= text_rva+len(text) for a,b,_ in self.functions)
        # Protected images can retain packed/stale exception sections. They are
        # complete capture bytes, but cannot establish executable function bounds.
        if not self.function_table_valid:
            self.functions = []
            self.starts = []

    def read(self, rva, size):
        for start, blob in self.parts.values():
            if start <= rva and rva+size <= start+len(blob):
                return blob[rva-start:rva-start+size]
        return b''

    def function(self, rva):
        index = bisect.bisect_right(self.starts, rva)-1
        if index >= 0 and rva < self.functions[index][1]:
            a,b,_ = self.functions[index]
            return dict(start=hex(a), end=hex(b), offset=hex(rva-a))
        return None

    def matches(self, needle):
        start, blob = self.parts['.text']
        result = []
        offset = blob.find(needle)
        while offset >= 0:
            result.append(start+offset)
            offset = blob.find(needle, offset+1)
        return result


def guards():
    # Explicit source inventory for guards whose arrays are local variables.
    rows = [
        ('native_body.h','dcs',0x7105f7,'49 8b 8e 98 2f 00 00'),
        ('native_body.h','aifm',0xa2070,'48 8b 41 20 c3'),
        ('native_body.h','dcs',0x711152,'f3 41 0f 58 86 ac 01 00 00'),
        ('native_motion.h','worldgeneral',0x68d50,'48 89 5c 24 08 57 48 83 ec 20'),
        ('native_velocity.h','worldgeneral',0x69310,'48 89 5c 24 08 57 48 83 ec 20'),
        ('native_velocity.h','worldgeneral',0x69390,'48 8d 81 54 02 00 00 c3'),
        ('native_velocity.h','dcs',0x712408,'f3 45 0f 10 a6 f0 01 00 00'),
        ('native_velocity.h','dcs',0x712411,'f3 41 0f 10 ae ec 01 00 00'),
        ('native_velocity.h','dcs',0x712435,'f3 45 0f 10 9e e8 01 00 00'),
        ('native_presentation_pitch.h','dcs',0x6d41eb,'f3 0f 10 8e b4 4d 00 00'),
        ('native_presentation_pitch.h','dcs',0x6d41f6,'f3 0f 10 86 b4 22 00 00'),
        ('object_probe.cpp','dcs',0x70fef0,'48 8b c4 48 89 58 10 48 89 70 18 48 89 78 20'),
        ('object_probe.cpp','dcs',0x675279,'ff 90 70 0c 00 00 48 8b 4b 58'),
        ('object_probe.cpp','dcs',0x6b6070,'48 8b c4 48 89 58 10 55 56 57 41 54 41 55 41 56 41 57'),
        ('object_probe.cpp','dcs',0x67529c,'41 b0 01 0f 28 ce 48 8b 01 ff 90 10 0c 00 00'),
        ('object_probe.cpp','dcs',0x6b73a7,'e8 44 1f fb ff'),
    ]
    module_names = dict(image='dcs',world='worldgeneral',sound='sound')
    for source in ('engine-prototype/sound_boundary.h', 'engine_native_layout.h'):
        content = (HERE.parent/source).read_text()
        found = re.findall(r'matches\((image|world|sound)\+(?:native_build::(?:dcs|world)\()?(0x[0-9a-f]+)\)?,std::array<unsigned char,(\d+)>\{([^}]+)\}', content)
        assert len(found) == (12 if 'sound_boundary' in source else 5)
        for module,rva,count,values in found:
            needle = bytes(int(v.strip(),0) for v in values.split(','))
            assert len(needle) == int(count)
            rows.append((source,module_names[module],int(rva,16),needle.hex()))
    return rows


def audit(root):
    snapshots = {name:Snapshot(root/name) for name in MODULES}
    rows = []
    for source,module,rva,signature in guards():
        snapshot = snapshots[module]
        needle = bytes.fromhex(signature)
        candidates = snapshot.matches(needle)
        rows.append(dict(source=source,module=module,old_rva=hex(rva),
                         matches_at_old_rva=snapshot.read(rva,len(needle))==needle,
                         candidate_count=len(candidates),
                         candidates=[dict(rva=hex(c),function=snapshot.function(c))
                                     for c in candidates] if len(candidates)<=12 else [],
                         candidates_omitted=len(candidates)>12))
    pointers = []
    dcs = snapshots['dcs']
    for rva,target in ((0x11461f8,0x133b650),(0x1146ff0,0x133b770)):
        blob = dcs.read(rva,8)
        value = struct.unpack('<Q',blob)[0] if len(blob)==8 else None
        pointers.append(dict(old_rva=hex(rva),expected_target_rva=hex(target),
                             matches=value==dcs.base+target))
    return dict(status='read-only audit; candidate matches do not validate compatibility',
                captured_sections=sum(len(s.metadata) for s in snapshots.values()),
                sections={name:s.metadata for name,s in snapshots.items()},
                function_table_valid={name:s.function_table_valid for name,s in snapshots.items()},
                guard_count=len(rows),old_guard_matches=sum(r['matches_at_old_rva'] for r in rows),
                guards=rows,table_boundaries=pointers)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('capture',type=Path)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    report=audit(args.capture)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','captured_sections','guard_count','old_guard_matches')}))
