[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Package,
    [string]$SavedGames = (Join-Path $env:USERPROFILE 'Saved Games\DCS'),
    [string]$DcsRoot = 'D:\DCS World'
)
$ErrorActionPreference = 'Stop'
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Exit DCS before installing this separate session-control hook.' }
$version = (Get-Content -LiteralPath (Join-Path $DcsRoot 'autoupdate.cfg') -Raw | ConvertFrom-Json).version
if ($version -ne '2.9.29.27468') { throw "Unsupported DCS build: $version" }
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$control = Join-Path $SavedGames 'Scripts/DCSRecorderSessionControl'
$pairs = @(
    @{ Source = (Join-Path $repo 'companion/session_guard.lua'); Target = (Join-Path $control 'session_guard.lua') },
    @{ Source = (Join-Path $Package 'expected.lua'); Target = (Join-Path $control 'expected.lua') },
    @{ Source = (Join-Path $PSScriptRoot 'hook.lua'); Target = (Join-Path $SavedGames 'Scripts/Hooks/dcs-recorder-session-control.lua') }
)
foreach ($name in @('030-Session-Guard-valid.miz','031-Session-Guard-edited.miz','032-Session-Guard-repacked.miz')) {
    $pairs += @{ Source = (Join-Path $Package $name); Target = (Join-Path $SavedGames "Missions/$name") }
}
# Preflight every destination before writing. Existing files are never replaced.
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Source -PathType Leaf)) { throw "Missing source: $($pair.Source)" }
    $pair.Hash = (Get-FileHash -LiteralPath $pair.Source -Algorithm SHA256).Hash
    if ((Test-Path -LiteralPath $pair.Target) -and
        ((Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash -ne $pair.Hash)) {
        throw "Different destination already exists: $($pair.Target)"
    }
}
foreach ($pair in $pairs) {
    if (-not (Test-Path -LiteralPath $pair.Target)) {
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($pair.Target)) | Out-Null
        [IO.File]::Copy($pair.Source, $pair.Target, $false)
    }
    if ((Get-FileHash -LiteralPath $pair.Target -Algorithm SHA256).Hash -ne $pair.Hash) { throw 'Installed hash mismatch' }
}
$pairs | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Package 'installation.json') -Encoding UTF8
[pscustomobject]@{ Status='Installed; live checks pending'; Files=$pairs.Count; Build=$version; FirstMission='030-Session-Guard-valid.miz' }
