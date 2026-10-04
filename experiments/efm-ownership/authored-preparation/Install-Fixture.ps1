[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$EvidenceDirectory,[switch]$ValidateOnly)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before installing the test missions.' }
$root=(Resolve-Path -LiteralPath $EvidenceDirectory).Path
$saved=Join-Path $env:USERPROFILE 'Saved Games/DCS'
$missions=(Resolve-Path -LiteralPath (Join-Path $saved 'Missions')).Path
if ((Get-Content 'D:/DCS World/autoupdate.cfg' -Raw | ConvertFrom-Json).version -ne '2.9.30.28536') { throw 'DCS build changed.' }
$manifest=Get-Content -LiteralPath (Join-Path $root 'recording-v4/manifest.json') -Raw | ConvertFrom-Json
$checks=@(
    @{Source='source-v4/054-Authored-Scene.miz';Name='054-Authored-Scene.miz';Hash=$manifest.source_sha256},
    @{Source='recording-v4/prepared.miz';Name='055-Authored-Recording.miz';Hash=$manifest.prepared_sha256}
)
foreach ($item in $checks) {
    $item.SourcePath=[IO.Path]::GetFullPath((Join-Path $root $item.Source))
    $item.Target=[IO.Path]::GetFullPath((Join-Path $missions $item.Name))
    if (-not $item.SourcePath.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase) -or
        -not $item.Target.StartsWith($missions+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped named directories.' }
    if (Test-Path -LiteralPath $item.Target) { throw ('Existing mission will not be overwritten: '+$item.Target) }
    if ((Get-FileHash -LiteralPath $item.SourcePath -Algorithm SHA256).Hash -ne $item.Hash) { throw 'Prepared mission hash changed.' }
}
$repo=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
# Offline Mission Editor load checks: zones through the real loader, every
# resource/dictionary key resolvable. Both missions failed live without these.
foreach ($item in $checks) {
    & python (Join-Path $PSScriptRoot 'check_resources.py') $item.SourcePath
    if ($LASTEXITCODE -ne 0) { throw ('Unresolved resource reference: '+$item.Source) }
}
foreach ($lua in @('source-v4/mission.lua','recording-v4/mission.lua')) {
    & 'D:/DCS World/bin/luae.exe' (Join-Path $PSScriptRoot 'check_me_zones.lua') (Join-Path $root $lua)
    if ($LASTEXITCODE -ne 0) { throw ('Mission Editor zone load failed: '+$lua) }
}
foreach ($pair in @(
    @('companion/recording_sink.lua','Scripts/Hooks/dcs-recorder-autosave.lua'),
    @('companion/engine_capture.lua','Scripts/DCSRecorderEngineCapture/engine_capture.lua')
)) {
    if ((Get-FileHash -LiteralPath (Join-Path $repo $pair[0])).Hash -ne (Get-FileHash -LiteralPath (Join-Path $saved $pair[1])).Hash) { throw ('Recorder dependency differs: '+$pair[1]) }
}
if (-not (Test-Path -LiteralPath (Join-Path $saved 'Scripts/DCSRecorderEngineCapture/NativeEngineCapture2930.dll'))) { throw 'Native capture helper is absent.' }
if ($ValidateOnly) { Write-Output 'Validated two new mission paths and installed capture scripts; no changes.'; return }
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during validation.' }
foreach ($item in $checks) { [IO.File]::Copy($item.SourcePath,$item.Target,$false) }
foreach ($item in $checks) {
    if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.Hash) { throw 'Installed mission hash mismatch.' }
}
@{Status='Two separate mission files installed; live source and prepared comparison pending';Files=$checks;Utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root 'installation-v4.json') -Encoding utf8
Write-Output 'Installed 054-Authored-Scene and 055-Authored-Recording; hashes verified.'
