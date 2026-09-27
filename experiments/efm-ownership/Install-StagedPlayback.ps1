[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PackageDirectory,
    [string]$SavedGames = (Join-Path $env:USERPROFILE 'Saved Games\DCS'),
    [string]$DcsRoot = 'D:\DCS World',
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before installing this test.' }
$packageRoot = (Resolve-Path -LiteralPath $PackageDirectory).Path
$manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.profile -ne 'staged-v1' -or $manifest.dcs_build -ne '2.9.29.27468') {
    throw 'Unsupported staged-playback package profile or DCS build.'
}
$installedVersion = (Get-Content -LiteralPath (Join-Path $DcsRoot 'autoupdate.cfg') -Raw | ConvertFrom-Json).version
if ($installedVersion -ne $manifest.dcs_build) { throw "DCS build mismatch: $installedVersion" }
$modName = 'DCSRecorder-Hornet-Staged'
$missionName = 'DCSRecorder-Staged-Playback.miz'
$modTarget = [IO.Path]::GetFullPath((Join-Path $SavedGames "Mods\aircraft\$modName"))
$missionTarget = [IO.Path]::GetFullPath((Join-Path $SavedGames "Missions\$missionName"))
if ((Test-Path -LiteralPath $modTarget) -or (Test-Path -LiteralPath $missionTarget)) {
    throw 'Test destination already exists. Installation will not overwrite it.'
}
$copyPlan = @()
$packagePrefix = $packageRoot.TrimEnd('\') + '\'
foreach ($entry in $manifest.files.PSObject.Properties) {
    $relative = $entry.Name.Replace('/', '\')
    if ([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or ($relative.Split('\') -contains '..')) {
        throw "Invalid package path: $relative"
    }
    $source = [IO.Path]::GetFullPath((Join-Path $packageRoot $relative))
    if (-not $source.StartsWith($packagePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Package path escapes root: $relative"
    }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $entry.Value) {
        throw "Package hash mismatch: $relative"
    }
    $destination = $null
    if ($relative.StartsWith("$modName\", [StringComparison]::Ordinal)) {
        $destination = Join-Path $modTarget $relative.Substring($modName.Length + 1)
    } elseif ($relative -eq $missionName) {
        $destination = $missionTarget
    }
    if ($destination) {
        $copyPlan += [pscustomobject]@{ Source = $source; Destination = $destination; Sha256 = $entry.Value }
    }
}
foreach ($required in @('entry.lua', 'aircraft.lua', 'bin\HornetStagedProbe.dll', 'bin\recorded-flight.txt')) {
    if ((Join-Path $modTarget $required) -notin $copyPlan.Destination) { throw "Package missing $required" }
}
if ($missionTarget -notin $copyPlan.Destination) { throw 'Package missing mission.' }
if ($ValidateOnly) {
    [pscustomobject]@{ Status = 'Validated'; Files = $copyPlan.Count; Mod = $modTarget; Mission = $missionTarget }
    return
}
# No existing files are replaced. A partial install is preserved for inspection if copying fails.
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during validation; close it and retry.' }
foreach ($item in $copyPlan) {
    $parent = Split-Path -Parent $item.Destination
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    [IO.File]::Copy($item.Source, $item.Destination, $false)
    if ((Get-FileHash -LiteralPath $item.Destination -Algorithm SHA256).Hash -ne $item.Sha256) {
        throw "Installed hash mismatch: $($item.Destination)"
    }
}
$receipt = [pscustomobject]@{
    Status = 'Installed; live DCS validation pending'
    InstalledUtc = [DateTime]::UtcNow.ToString('o')
    DcsBuild = $installedVersion
    Mod = $modTarget
    Mission = $missionTarget
    Files = $copyPlan
}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $packageRoot 'installation.json') -Encoding UTF8
[pscustomobject]@{ Status = $receipt.Status; VerifiedFiles = $copyPlan.Count; Mod = $modTarget; Mission = $missionTarget }
