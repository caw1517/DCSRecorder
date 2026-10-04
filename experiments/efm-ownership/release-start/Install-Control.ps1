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
$payloadRoot = Join-Path $packageRoot 'payload'
$manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.profile -ne 'release-airborne-v1' -or $manifest.dcs_build -ne '2.9.30.28536' -or
    $manifest.module -ne 'DCSRecorder-Hornet-Release-Test' -or $manifest.binary -ne 'HornetReleaseProbe' -or
    $manifest.mission -ne '043-Hornet-Countdown-Release.miz') { throw 'Unsupported release package.' }
$build = (Get-Content -LiteralPath (Join-Path $DcsRoot 'autoupdate.cfg') -Raw | ConvertFrom-Json).version
if ($build -ne $manifest.dcs_build) { throw 'Installed DCS build changed.' }
$modPrefix = 'Mods\aircraft\DCSRecorder-Hornet-Release-Test\'
$allowed = @('Missions\043-Hornet-Countdown-Release.miz', 'Scripts\Hooks\DCSRecorderReleaseControl.lua',
    'Scripts\DCSRecorderReleaseControl\expected.lua', 'Scripts\DCSRecorderReleaseControl\session_guard.lua')
foreach ($relative in @('Mods\aircraft\DCSRecorder-Hornet-Release-Test', 'Scripts\DCSRecorderReleaseControl') + $allowed) {
    if (Test-Path -LiteralPath (Join-Path $savedRoot $relative)) { throw "Destination already exists: $relative" }
}
$plan = @()
foreach ($entry in $manifest.files.PSObject.Properties) {
    $relative = $entry.Name.Replace('/', '\')
    if ([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or
        ($relative.Split('\') -contains '..') -or ($relative.Split('\') -contains '.')) { throw 'Invalid package path.' }
    if (-not $relative.StartsWith($modPrefix, [StringComparison]::Ordinal) -and $relative -notin $allowed) {
        throw "Unexpected file: $relative"
    }
    $source = [IO.Path]::GetFullPath((Join-Path $payloadRoot $relative))
    $target = [IO.Path]::GetFullPath((Join-Path $savedRoot $relative))
    if (-not $source.StartsWith($payloadRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
        -not $target.StartsWith($savedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped root.' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $entry.Value) { throw "Hash mismatch: $relative" }
    if ($plan.Count -gt 0 -and $target -in $plan.Target) { throw 'Duplicate destination.' }
    $plan += [pscustomobject]@{ Source=$source; Target=$target; Sha256=$entry.Value }
}
$required = $allowed + @('entry.lua','aircraft.lua','bin\HornetReleaseProbe.dll','bin\recorded-flight.txt','bin\recorded-flight.json' | ForEach-Object { $modPrefix + $_ })
foreach ($relative in $required) {
    if ((Join-Path $savedRoot $relative) -notin $plan.Target) { throw "Missing required file: $relative" }
}
if ($ValidateOnly) { [pscustomobject]@{ Status='Validated'; Files=$plan.Count }; return }
$protected = @{}
foreach ($folder in @('Mods\aircraft', 'Scripts', 'Missions', 'DCSRecorder')) {
    $path = Join-Path $savedRoot $folder
    if (-not (Test-Path -LiteralPath $path)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $path -File -Recurse) {
        if ($file.Extension -notin @('.lua','.dll','.txt','.csv','.miz','.json','.zip') -or
            $file.FullName -match '\\(probe-logs|state-logs|layout-logs)\\') { continue }
        $protected[$file.FullName] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    }
}
$receiptPath = Join-Path $packageRoot 'installation.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Receipt already exists.' }
$receipt = [ordered]@{ Status='Preflight verified'; InstalledUtc=[DateTime]::UtcNow.ToString('o'); DcsBuild=$build; Files=$plan; Protected=$protected }
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during validation.' }
foreach ($item in $plan) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $item.Target) -Force | Out-Null
    [IO.File]::Copy($item.Source,$item.Target,$false)
    if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.Sha256) { throw 'Installed hash mismatch.' }
}
foreach ($path in $protected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $protected[$path]) { throw "Existing file changed: $path" }
}
$receipt.Status='Installed; live release acceptance pending'
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
[pscustomobject]@{ Status=$receipt.Status; VerifiedFiles=$plan.Count; UnchangedFiles=$protected.Count; Mission=(Join-Path $savedRoot 'Missions\043-Hornet-Countdown-Release.miz') }
