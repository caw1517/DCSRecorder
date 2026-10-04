[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PreviousPackage,
    [string]$PreviousHookReceipt,
    [Parameter(Mandatory=$true)][string]$PackageDirectory,
    [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
    [string]$SavedGames=(Join-Path $env:USERPROFILE 'Saved Games\DCS'),
    [switch]$ValidateOnly
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before updating this diagnostic.' }
$savedRoot=(Resolve-Path -LiteralPath $SavedGames).Path
$oldRoot=(Resolve-Path -LiteralPath $PreviousPackage).Path
$newRoot=(Resolve-Path -LiteralPath $PackageDirectory).Path
$old=Get-Content -LiteralPath (Join-Path $oldRoot 'manifest.json') -Raw | ConvertFrom-Json
$new=Get-Content -LiteralPath (Join-Path $newRoot 'manifest.json') -Raw | ConvertFrom-Json
foreach ($m in @($old,$new)) {
    if ($m.profile -ne 'release-airborne-v1' -or $m.module -ne 'DCSRecorder-Hornet-Release-Test' -or
        $m.dcs_build -ne '2.9.30.28536' -or $m.mission -ne '043-Hornet-Countdown-Release.miz') { throw 'Unexpected package.' }
}
if ((Get-Content 'D:/DCS World/autoupdate.cfg' -Raw | ConvertFrom-Json).version -ne $new.dcs_build) { throw 'DCS build changed.' }
$hookName='Scripts/Hooks/DCSRecorderReleaseControl.lua'
$hook=$null
if ($PreviousHookReceipt) {
    $hook=Get-Content -LiteralPath $PreviousHookReceipt -Raw | ConvertFrom-Json
    if ($hook.Target -ne [IO.Path]::GetFullPath((Join-Path $savedRoot $hookName)) -or
        $hook.PreviousSha256 -ne $old.files.$hookName) { throw 'Hook receipt does not match original installation.' }
}
$allowed=@('Missions/043-Hornet-Countdown-Release.miz','Scripts/DCSRecorderReleaseControl/expected.lua',$hookName)
$oldNames=@($old.files.PSObject.Properties.Name | Sort-Object)
$newNames=@($new.files.PSObject.Properties.Name | Sort-Object)
if (($oldNames -join '|') -ne ($newNames -join '|') -or $oldNames.Count -ne 14) { throw 'Package file set changed.' }
$checks=@();$changes=@()
foreach ($name in $newNames) {
    if ([IO.Path]::IsPathRooted($name) -or $name.Contains(':') -or ($name.Split('/') -contains '..')) { throw 'Invalid path.' }
    $target=[IO.Path]::GetFullPath((Join-Path $savedRoot $name))
    $source=[IO.Path]::GetFullPath((Join-Path (Join-Path $newRoot 'payload') $name))
    if (-not $target.StartsWith($savedRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or
        -not $source.StartsWith($newRoot+'\payload\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped root.' }
    $before=if ($name -eq $hookName -and $null -ne $hook) { $hook.Sha256 } else { $old.files.$name }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $before) { throw "Installed bytes changed: $name" }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $new.files.$name) { throw "New package hash mismatch: $name" }
    $item=[pscustomobject]@{Name=$name;Target=$target;Source=$source;Before=$before;After=$new.files.$name}
    $checks+=$item
    if ($before -ne $item.After) {
        if ($name -notin $allowed) { throw "Unexpected changed file: $name" }
        $changes+=$item
    }
}
if ($ValidateOnly) { $changes | Select-Object Name,Before,After; return }
$evidenceRoot=[IO.Path]::GetFullPath($EvidenceDirectory)
if (Test-Path -LiteralPath $evidenceRoot) { throw 'Use a fresh update receipt directory.' }
New-Item -ItemType Directory -Path $evidenceRoot | Out-Null
foreach ($item in $changes) {
    $backup=Join-Path $evidenceRoot $item.Name
    New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
    [IO.File]::Copy($item.Target,$backup,$false)
}
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during preflight.' }
foreach ($item in $changes) { [IO.File]::Copy($item.Source,$item.Target,$true) }
foreach ($item in $checks) {
    if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.After) { throw "Updated hash mismatch: $($item.Name)" }
}
[ordered]@{Status='Installed checked diagnostic update; live readiness/release pending';UpdatedUtc=[DateTime]::UtcNow.ToString('o');
    ChangedFiles=$changes;VerifiedFiles=$checks.Count;UnchangedFiles=$checks.Count-$changes.Count;Manifest=(Join-Path $newRoot 'manifest.json')} |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'receipt.json') -Encoding UTF8
Write-Output "Updated $($changes.Count) diagnostic files; verified all $($checks.Count) files; native DLL and tape unchanged."
