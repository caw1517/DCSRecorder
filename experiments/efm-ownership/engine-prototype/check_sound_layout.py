"""Compare read guards with local analysis images, without executing those images."""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'native-interface-inspection'))
from inspect_pe import PE

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('dcs_analysis',type=Path);parser.add_argument('world_analysis',type=Path)
    args=parser.parse_args()
    images={'image':PE(args.dcs_analysis),'world':PE(args.world_analysis)}
    header=Path(__file__).with_name('sound_boundary.h').read_text()
    guards=re.findall(r'matches\((image|world)\+(0x[0-9a-f]+),std::array<unsigned char,(\d+)>\{([^}]+)\}',header)
    assert len(guards)==12
    for module,rva,count,values in guards:
        expected=bytes(int(v.strip(),0) for v in values.split(','))
        assert len(expected)==int(count)
        image=images[module];offset=image.offset(int(rva,16))
        assert image.data[offset:offset+len(expected)]==expected,(module,rva)
    print('PASS: all 12 read guards match the retained analysis images; live build still checked at runtime')
