[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PackageDirectory,
    [string]$SavedGames = (Join-Path $env:USERPROFILE 'Saved Games\DCS'),
    [string]$DcsRoot = 'D:\DCS World',
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before installing this control.' }
$packageRoot = (Resolve-Path -LiteralPath $PackageDirectory).Path
$savedRoot = (Resolve-Path -LiteralPath $SavedGames).Path
$manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'manifest.json') -Raw | ConvertFrom-Json
$modName = 'DCSRecorder-Hornet-Held-Test'
$binaryName = 'HornetHeldProbe'
$missionName = '040-Hornet-Held-Start.miz'
if ($manifest.profile -eq 'snapshot-airborne-v1') {
    $modName = 'DCSRecorder-Hornet-Snapshot-Test'
    $binaryName = 'HornetSnapshotProbe'
    $missionName = '042-Hornet-Snapshot-Hold.miz'
}
if ($manifest.profile -notin @('held-start-airborne-v1', 'snapshot-airborne-v1') -or
    $manifest.dcs_build -ne '2.9.30.28536' -or
    $manifest.module -ne $modName -or $manifest.binary -ne $binaryName -or
    $manifest.mission -ne $missionName) { throw 'Unsupported held-start package.' }
$installedVersion = (Get-Content -LiteralPath (Join-Path $DcsRoot 'autoupdate.cfg') -Raw | ConvertFrom-Json).version
if ($installedVersion -ne $manifest.dcs_build) { throw "DCS build mismatch: $installedVersion" }
$modTarget = [IO.Path]::GetFullPath((Join-Path $savedRoot "Mods\aircraft\$modName"))
$missionTarget = [IO.Path]::GetFullPath((Join-Path $savedRoot "Missions\$missionName"))
if ((Test-Path -LiteralPath $modTarget) -or (Test-Path -LiteralPath $missionTarget)) {
    throw 'Control destination already exists; installation will not overwrite it.'
}
$copyPlan = @()
$packagePrefix = $packageRoot.TrimEnd('\') + '\'
foreach ($entry in $manifest.files.PSObject.Properties) {
    $relative = $entry.Name.Replace('/', '\')
    if ([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or
        ($relative.Split('\') -contains '..') -or ($relative.Split('\') -contains '.')) {
        throw "Invalid package path: $relative"
    }
    $source = [IO.Path]::GetFullPath((Join-Path $packageRoot $relative))
    if (-not $source.StartsWith($packagePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Package path escapes root: $relative"
    }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $entry.Value) {
        throw "Package hash mismatch: $relative"
    }
    if ($relative.StartsWith("$modName\", [StringComparison]::Ordinal)) {
        $destination = [IO.Path]::GetFullPath((Join-Path $modTarget $relative.Substring($modName.Length + 1)))
        if (-not $destination.StartsWith($modTarget + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Destination escapes test module: $relative"
        }
    } elseif ($relative -eq $missionName) {
        $destination = $missionTarget
    } else { throw "Unexpected package entry: $relative" }
    if ($copyPlan.Count -gt 0 -and $destination -in $copyPlan.Destination) { throw "Duplicate destination: $relative" }
    $copyPlan += [pscustomobject]@{ Source = $source; Destination = $destination; Sha256 = $entry.Value }
}
foreach ($required in @('entry.lua', 'aircraft.lua', "bin\$binaryName.dll", 'bin\recorded-flight.txt', 'bin\recorded-flight.json')) {
    if ((Join-Path $modTarget $required) -notin $copyPlan.Destination) { throw "Package missing $required" }
}
if ($missionTarget -notin $copyPlan.Destination) { throw 'Package missing mission.' }
if ($ValidateOnly) {
    [pscustomobject]@{ Status = 'Validated'; Files = $copyPlan.Count; Mod = $modTarget; Mission = $missionTarget }
    return
}
# Hash existing user/runtime files before this additive installation.
$protected = @{}
foreach ($folder in @('Mods\aircraft', 'Scripts', 'Missions', 'DCSRecorder')) {
    $path = Join-Path $savedRoot $folder
    if (-not (Test-Path -LiteralPath $path)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $path -File -Recurse) {
        if ($file.Extension -notin @('.lua', '.dll', '.txt', '.csv', '.miz', '.json', '.zip')) { continue }
        if ($file.FullName -match '\\(probe-logs|state-logs|layout-logs)\\') { continue }
        $protected[$file.FullName] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    }
}
$receiptPath = Join-Path $packageRoot 'held-installation.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Installation receipt already exists; inspect it before proceeding.' }
$receipt = [ordered]@{
    Status = 'Preflight complete; installation not yet verified'
    InstalledUtc = [DateTime]::UtcNow.ToString('o')
    DcsBuild = $installedVersion
    Mod = $modTarget
    Mission = $missionTarget
    Files = $copyPlan
    Protected = $protected
}
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during validation; close it before installing.' }
# Preserve partial installations for inspection; never replace or delete user files.
foreach ($item in $copyPlan) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $item.Destination) -Force | Out-Null
    [IO.File]::Copy($item.Source, $item.Destination, $false)
    if ((Get-FileHash -LiteralPath $item.Destination -Algorithm SHA256).Hash -ne $item.Sha256) {
        throw "Installed hash mismatch: $($item.Destination)"
    }
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) {
        throw "Existing file changed: $path"
    }
}
$receipt.Status = 'Installed; live held-staging validation pending'
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
[pscustomobject]@{ Status = $receipt.Status; VerifiedFiles = $copyPlan.Count; UnchangedFiles = $protected.Count; Mod = $modTarget; Mission = $missionTarget }
