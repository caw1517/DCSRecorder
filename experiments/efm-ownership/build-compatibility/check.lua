local dll=assert(arg[1])
local fn=assert(package.loadlib(dll,'dcs_build_capture'))
assert(fn()=='UNAVAILABLE,not_dcs','read-only helper must refuse non-DCS host')
print('PASS: Lua ABI and non-DCS host refusal; no runtime sections captured')
