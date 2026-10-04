[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PreviousPackage,
    [Parameter(Mandatory=$true)][string]$NextPackage,
    [string]$SavedGames=(Join-Path $env:USERPROFILE 'Saved Games\DCS')
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before switching the snapshot.' }
$oldRoot=(Resolve-Path -LiteralPath $PreviousPackage).Path
$newRoot=(Resolve-Path -LiteralPath $NextPackage).Path
$savedRoot=(Resolve-Path -LiteralPath $SavedGames).Path
$old=Get-Content -LiteralPath (Join-Path $oldRoot 'manifest.json') -Raw | ConvertFrom-Json
$new=Get-Content -LiteralPath (Join-Path $newRoot 'manifest.json') -Raw | ConvertFrom-Json
$module='DCSRecorder-Hornet-Snapshot-Test'
$mission='042-Hornet-Snapshot-Hold.miz'
foreach ($m in @($old,$new)) {
    if ($m.profile -ne 'snapshot-airborne-v1' -or $m.module -ne $module -or
        $m.binary -ne 'HornetSnapshotProbe' -or $m.mission -ne $mission -or
        $m.dcs_build -ne '2.9.30.28536') { throw 'Unexpected snapshot profile' }
}
$allowed=@("$module/bin/recorded-flight.txt","$module/bin/recorded-flight.json",$mission)
if (Compare-Object @($old.files.PSObject.Properties.Name) @($new.files.PSObject.Properties.Name)) { throw 'Package file set changed' }
$plan=@()
foreach ($entry in $new.files.PSObject.Properties) {
    $relative=$entry.Name
    if ($relative.Contains('..') -or $relative.Contains(':') -or $relative.Contains('\')) { throw 'Invalid package path' }
    if ($relative -eq $mission) { $target=Join-Path $savedRoot "Missions\$mission" }
    elseif ($relative.StartsWith("$module/",[StringComparison]::Ordinal)) { $target=Join-Path $savedRoot "Mods/aircraft/$relative" }
    else { throw 'Unexpected package entry' }
    $source=Join-Path $newRoot $relative
    $before=$old.files.PSObject.Properties[$relative].Value
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $before) { throw "Installed file changed: $relative" }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $entry.Value) { throw "New package hash mismatch: $relative" }
    if ($before -ne $entry.Value) {
        if ($relative -notin $allowed) { throw "Unexpected changed file: $relative" }
        $plan += [pscustomobject]@{Relative=$relative;Source=$source;Target=$target;Before=$before;After=$entry.Value}
    }
}
if ($plan.Count -ne 3) { throw 'Expected only tape, metadata and mission to change' }
$backup=Join-Path $newRoot 'previous-installed'
if (Test-Path -LiteralPath $backup) { throw 'Switch already attempted; inspect retained receipt/backups' }
foreach ($item in $plan) {
    $path=Join-Path $backup $item.Relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
    [IO.File]::Copy($item.Target,$path,$false)
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $item.Before) { throw 'Backup hash mismatch' }
}
$receipt=Join-Path $newRoot 'switch-receipt.json'
$plan | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receipt -Encoding UTF8
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during preflight' }
foreach ($item in $plan) {
    [IO.File]::Copy($item.Source,$item.Target,$true)
    if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.After) { throw 'Installed hash mismatch; backups retained' }
}
[pscustomobject]@{Status='Snapshot switched; live validation pending';ChangedFiles=$plan.Count;Backup=$backup;Mission=$mission}
