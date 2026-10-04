"""Check a retained live smoke observation against the actual source and commands.

Rendering verdicts come from the user, never from command success. A new verdict
requires a new live run. This is a retained-evidence check, not a DCS renderer.
"""
import argparse
import json
from pathlib import Path


def check(folder):
    metadata=json.loads((folder/'raw/recorded-flight.json').read_text())
    review=json.loads((folder/'review.json').read_text())
    text=(folder/'raw/dcs.log').read_text(errors='replace')
    commands=[line.split('DCSR_HELD INITIAL_SMOKE,',1)[1] for line in text.splitlines()
              if 'DCSR_HELD INITIAL_SMOKE,' in line]
    assert metadata['smoke_events'][0]=={'time':0.0,'on':True}, 'Source does not establish initial smoke ON'
    assert len(commands)==1 and commands[0].endswith(',true'), 'Initial smoke ON command missing or duplicated'
    assert 'DCSR_HELD OBSERVATION_COMPLETE' in text, 'Observation did not complete'
    assert 'DCSR_HELD FAILED' not in text, 'Hold controller failed'
    print('Source smoke ON; initial ON command at mission time '+commands[0].split(',')[0]+'; observation complete.')
    if review.get('held_smoke_required') is False:
        assert review.get('requirement_change_quote'), 'Missing user authorization for changed held-smoke criterion'
        print('DEFERRED: user permits no visible smoke while held; visible onset on release is still unverified.')
        return
    if review['visible_smoke'] is not True:
        raise SystemExit('FAIL: user observed no visible smoke during the held snapshot; command delivery is not rendering acceptance.')
    print('PASS: user confirmed visible smoke in this retained run.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path)
    check(parser.parse_args().folder)
