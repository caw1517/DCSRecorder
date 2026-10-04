"""Negative controls at the captured serialization/reference boundary."""
import copy
from pathlib import Path
import sys
from prepare_reference import data,read_mission,validate_roundtrip

original=data.LuaData((Path(sys.argv[1])/'mission.lua').read_text(encoding='utf-8')).mission()
loaded,_=read_mission(Path(sys.argv[2]))
assert validate_roundtrip(original,loaded)
def unit(m):return m['coalition']['blue']['country'][1]['plane']['group'][1]['units'][1]
for mode in ('position','heading','radio','nonempty_cartridge','trigger','extra_field','callsign'):
    a,b=copy.deepcopy(original),copy.deepcopy(loaded)
    if mode=='position':unit(b)['x']+=1
    elif mode=='heading':unit(b)['heading']+=1e-6
    elif mode=='radio':unit(b)['Radio'][1]['channels'][1]=999
    elif mode=='nonempty_cartridge':unit(a)['dataCartridge']['Points'][1]={'x':1,'y':2}
    elif mode=='trigger':b['trigrules'][1]['actions'][2]['text']+=' -- change'
    elif mode=='extra_field':unit(b)['unexpected']=True
    elif mode=='callsign':unit(b)['AddPropAircraft']['VoiceCallsignLabel']='ZZ'
    try:validate_roundtrip(a,b)
    except ValueError:pass
    else:raise AssertionError('Accepted unreviewed '+mode)
print('PASS: captured serialization accepted; seven meaningful/unreviewed changes refused')
