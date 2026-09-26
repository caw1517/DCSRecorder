-- Compare the real mission tables; permit only the three wind-speed changes.
dofile(assert(arg[1])); local baseline = mission
dofile(assert(arg[2])); local candidate = mission
assert(baseline.weather.atmosphere_type == 0, 'Expected static weather')
assert(next(baseline.weather.cyclones) == nil, 'Unexpected dynamic weather')
local expected = {atGround=5, at2000=7, at8000=10}
for layer, speed in pairs(expected) do
    assert(baseline.weather.wind[layer].speed == speed, 'Baseline wind changed')
    assert(candidate.weather.wind[layer].speed == 0, 'Candidate wind is nonzero')
    baseline.weather.wind[layer].speed = 0
end
local function compare(a, b, path)
    assert(type(a) == type(b), 'Type mismatch at '..path)
    if type(a) ~= 'table' then
        assert(a == b, 'Value mismatch at '..path)
        return
    end
    for k, v in pairs(a) do compare(v, b[k], path..'.'..tostring(k)) end
    for k in pairs(b) do assert(a[k] ~= nil, 'Added key at '..path..'.'..tostring(k)) end
end
compare(baseline, candidate, 'mission')
print('PASS: mission tables differ only in three wind speeds (5/7/10 -> 0/0/0).')
