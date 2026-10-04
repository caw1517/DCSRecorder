"""Check candidate addresses against static capture; never enable a profile."""
import argparse
import json
import struct
from pathlib import Path
from audit import Snapshot, MODULES, guards, HERE


def check(root, profile):
    images = {name:Snapshot(root/name) for name in MODULES}
    def address(module, old):
        return int(profile.get(module,{}).get(hex(old),hex(old)),16)
    rows = []
    for source,module,old,signature in guards():
        key=f'{module}:{hex(old)}'
        expected=bytes.fromhex(profile['changed_signatures'].get(key,signature))
        current=address(module,old)
        rows.append(dict(source=source,module=module,old_rva=hex(old),
                         candidate_rva=hex(current),matches=images[module].read(current,len(expected))==expected))
    dcs=images['dcs']
    def pointer(rva):
        raw=dcs.read(rva,8)
        return struct.unpack('<Q',raw)[0]-dcs.base if len(raw)==8 else None
    table=address('dcs',0x1146200)
    structures=[]
    locators=[]
    for oldptr,oldtarget,offset in ((0x11461f8,0x133b650,0),(0x1146ff0,0x133b770,8)):
        ptr,target=address('dcs',oldptr),address('dcs',oldtarget)
        fields=struct.unpack('<6I',dcs.read(target,24))
        locators.append(fields)
        structures.append(dict(check=f'locator_offset_{offset}',matches=pointer(ptr)==target
                               and fields[0:3]==(1,offset,0) and fields[5]==target))
    structures.append(dict(check='same_type_and_hierarchy',matches=locators[0][3:5]==locators[1][3:5]))
    structures.append(dict(check='primary_table_boundary',matches=address('dcs',0x1146ff0)-table==0xdf0))
    for slot,oldtarget in ((0xc70,0x70fef0),(0xc10,0x6b6070),(0xd8,0x66d160),(0xe0,0x66d1c0),(0xf0,0x60f110)):
        structures.append(dict(check=f'vtable_slot_{hex(slot)}',matches=pointer(table+slot)==address('dcs',oldtarget)))
    writer=address('dcs',0x6b73a7)
    call=dcs.read(writer,5)
    target=writer+5+struct.unpack('<i',call[1:])[0]
    structures.append(dict(check='animation_writer_call',matches=call[0]==0xe8 and target==0x669580,
                           target_rva=hex(target)))
    return dict(status='Static candidates only; object identity, complete layout and live behavior remain unverified',
                build=profile['build'],guard_count=len(rows),guard_matches=sum(r['matches'] for r in rows),
                guards=rows,structural_checks=structures,
                all_checks_pass=all(r['matches'] for r in rows+structures))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('capture',type=Path)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    profile=json.loads((HERE/'candidate_profile.json').read_text())
    report=check(args.capture,profile)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','guard_count','guard_matches','all_checks_pass')}))
    if not report['all_checks_pass']:raise SystemExit(1)
