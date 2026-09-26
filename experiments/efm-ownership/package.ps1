param([string]$DcsRoot = 'D:\DCS World')
$ErrorActionPreference = 'Stop'
$probeRoot = $PSScriptRoot
$package = Join-Path $probeRoot 'package'
New-Item -ItemType Directory -Force -Path "$package\DCSRecorder-EFM-Probe\bin", "$package\Missions" | Out-Null
Copy-Item -Path "$probeRoot\mod\*" -Destination "$package\DCSRecorder-EFM-Probe" -Recurse -Force
Copy-Item -LiteralPath "$probeRoot\build\Release\OwnershipProbe.dll" -Destination "$package\DCSRecorder-EFM-Probe\bin\OwnershipProbe.dll" -Force
$descriptor = [IO.File]::ReadAllText((Join-Path $DcsRoot 'CoreMods\aircraft\TF-51D\TF-51D.lua'))
if ([regex]::Matches($descriptor, 'add_aircraft\(\{').Count -ne 1 -or $descriptor.TrimEnd() -notmatch '\}\)$') { throw 'Unexpected stock descriptor format' }
$descriptor = $descriptor.Replace('current_mod_path', '"./CoreMods/aircraft/TF-51D"').Replace('add_aircraft({', 'local aircraft = {')
$descriptor = [regex]::Replace($descriptor, '\}\)\s*$', '}')
$descriptor += @'

aircraft.Name = "DCSRecorder-EFM-Probe"
aircraft.DisplayName = "DCS Recorder EFM Probe"
aircraft.WorldID = WSTYPE_PLACEHOLDER
aircraft.attribute[4] = WSTYPE_PLACEHOLDER
aircraft.shape_table_data[1].name = "DCSRecorder-EFM-Probe"
aircraft.shape_table_data[1].index = WSTYPE_PLACEHOLDER
aircraft.shape_table_data[1].username = "DCSRecorder-EFM-Probe"
add_aircraft(aircraft)
'@
[IO.File]::WriteAllText("$package\DCSRecorder-EFM-Probe\aircraft.lua", $descriptor)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$template = Join-Path $DcsRoot 'Mods\aircraft\TF-51D\Missions\QuickStart\Caucasus TF-51_flight over town.miz'
$archive = [IO.Compression.ZipFile]::OpenRead($template)
try {
    $reader = [IO.StreamReader]::new($archive.GetEntry('mission').Open())
    try { [IO.File]::WriteAllText("$package\base-mission.lua", $reader.ReadToEnd()) } finally { $reader.Dispose() }
} finally { $archive.Dispose() }
& "$DcsRoot\bin\luae.exe" "$probeRoot\generate_missions.lua" "$package\base-mission.lua" $package
if ($LASTEXITCODE -ne 0) { throw 'Mission generation failed' }
foreach ($mode in @('player','ai','clients','formation')) {
    $target = "$package\Missions\EFM-Probe-$mode.miz"
    Copy-Item -LiteralPath $template -Destination $target -Force
    $archive = [IO.Compression.ZipFile]::Open($target, 'Update')
    try {
        $archive.GetEntry('mission').Delete()
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,"$package\$mode-mission",'mission') | Out-Null
    } finally { $archive.Dispose() }
}
Write-Output "Prepared $package"
