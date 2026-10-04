"""Exercise real diagnostic exports outside DCS: refuse before any SDK access."""
import ctypes as c
import json
import os
from pathlib import Path
import sys

dll=Path(sys.argv[1]).resolve()
module=c.CDLL(str(dll))
calls=[]
ID=c.CFUNCTYPE(c.c_uint64,c.c_void_p)
COPY=c.CFUNCTYPE(None,c.c_void_p,c.c_void_p,c.c_int,c.c_int)
SET=c.CFUNCTYPE(None,c.c_void_p,c.c_int,c.c_float)
get_id=ID(lambda obj: calls.append('get_id') or 123)
copy=COPY(lambda *args:calls.append('copy'))
set_arg=SET(lambda *args:calls.append('set'))
class API(c.Structure):
    _fields_=[('id',ID),('args',c.c_void_p),('copy',COPY),('set',SET)]
api=API(get_id,None,copy,set_arg)
module.ed_setup_object_api.argtypes=[c.POINTER(API)]
for name in ('ed_on_object_create','ed_on_object_destroy'):
    getattr(module,name).argtypes=[c.c_void_p,c.POINTER(c.c_uint64)]
module.ed_on_object_simulate.argtypes=[c.c_void_p,c.POINTER(c.c_uint64),c.c_double]
for name in ('ed_setup_object_api','ed_on_object_create','ed_on_object_destroy','ed_on_object_simulate'):
    getattr(module,name).restype=None
folder=dll.parent/'layout-logs'
before=set(folder.glob('*.jsonl')) if folder.exists() else set()
cookie=c.c_uint64(42)
module.ed_setup_object_api(c.byref(api))
module.ed_on_object_create(1,c.byref(cookie))
module.ed_on_object_simulate(1,c.byref(cookie),1.0)
module.ed_on_object_simulate(1,c.byref(cookie),1.01)  # rate limited
module.ed_on_object_destroy(1,c.byref(cookie))
module.ed_on_object_simulate(1,c.byref(cookie),2.0)  # no stale object access
files=set(folder.glob('*.jsonl'))-before
assert len(files)==1
rows=[json.loads(line) for line in files.pop().read_text().splitlines()]
assert [r['status'] for r in rows]==['build_guard_refused','destroyed'],rows
assert not calls and cookie.value==42
print('PASS: non-DCS host refusal, zero SDK reads/writes, sample throttling, destroyed-object isolation')
