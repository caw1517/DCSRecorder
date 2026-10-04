[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PackageDirectory,[string]$UpdateFrom,[switch]$ValidateOnly)
# Additive install of an authored playback package built by prepare_playback.py.
# Refuses to run with DCS open, to overwrite anything, or on any hash mismatch.
# -UpdateFrom <previous package>: installed files must equal that package exactly;
# only changed files are replaced, after a backup, with rollback on failure.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before installing playback.' }
if ((Get-Content 'D:/DCS World/autoupdate.cfg' -Raw | ConvertFrom-Json).version -ne '2.9.30.28536') { throw 'DCS build changed.' }
$root=(Resolve-Path -LiteralPath $PackageDirectory).Path
$payload=(Resolve-Path -LiteralPath (Join-Path $root 'payload')).Path
$saved=(Resolve-Path -LiteralPath (Join-Path $env:USERPROFILE 'Saved Games/DCS')).Path
$manifest=Get-Content -LiteralPath (Join-Path $root 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.profile -notin @('authored-playback-airborne-v1','authored-playback-ground-v1')) { throw 'Unsupported package profile.' }
$previous=$null
if ($UpdateFrom) { $previous=Get-Content -LiteralPath (Join-Path (Resolve-Path -LiteralPath $UpdateFrom).Path 'manifest.json') -Raw | ConvertFrom-Json }
$items=@()
foreach ($property in $manifest.files.PSObject.Properties) {
    $source=[IO.Path]::GetFullPath((Join-Path $payload $property.Name))
    $target=[IO.Path]::GetFullPath((Join-Path $saved $property.Name))
    if (-not $source.StartsWith($payload+'\',[StringComparison]::OrdinalIgnoreCase) -or
        -not $target.StartsWith($saved+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped named directories.' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $property.Value) { throw ('Package hash changed: '+$property.Name) }
    if ($previous -and $property.Name -eq ('Missions/'+$manifest.mission) -and $manifest.mission -ne $previous.mission) {
        # A new playback mission for the same module/control: added, never overwriting.
        if (Test-Path -LiteralPath $target) { throw ('Existing mission will not be overwritten: '+$target) }
    } elseif ($previous) {
        $old=$previous.files.PSObject.Properties[$property.Name]
        if (-not $old) { throw ('Update adds a file; use a fresh install: '+$property.Name) }
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $old.Value) { throw ('Installed file differs from the previous package: '+$property.Name) }
        if ($old.Value -eq $property.Value) { continue }
    } elseif (Test-Path -LiteralPath $target) { throw ('Existing file will not be overwritten: '+$target) }
    $items+=@{Name=$property.Name;Source=$source;Target=$target;Hash=$property.Value}
}
if ($previous) {
    foreach ($old in $previous.files.PSObject.Properties) {
        # The previous playback mission stays installed; its hook reference is
        # replaced, so loading it refuses readiness and cleans up (fails closed).
        if ($old.Name -eq ('Missions/'+$previous.mission)) { continue }
        if (-not $manifest.files.PSObject.Properties[$old.Name]) { throw ('Update removes a file: '+$old.Name) }
    }
    if ($previous.module -ne $manifest.module -or $previous.control -ne $manifest.control) { throw 'Update changes package identity.' }
} else {
    foreach ($dir in @(('Mods/aircraft/'+$manifest.module),('Scripts/'+$manifest.control))) {
        if (Test-Path -LiteralPath (Join-Path $saved $dir)) { throw ('Existing directory will not be merged: '+$dir) }
    }
}
$repo=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ((Get-FileHash -LiteralPath (Join-Path $repo 'companion/session_guard.lua')).Hash -ne
    (Get-FileHash -LiteralPath (Join-Path $payload ('Scripts/'+$manifest.control+'/session_guard.lua'))).Hash) { throw 'Packaged session guard differs from the companion source.' }
if ($ValidateOnly) { Write-Output ("Validated {0} new files; no changes." -f $items.Count); return }
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during validation.' }
$written=@();$backups=@()
$backupRoot=Join-Path $root ('backup-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
try {
    foreach ($item in $items) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $item.Target) | Out-Null
        if ($previous -and (Test-Path -LiteralPath $item.Target)) {
            $backup=Join-Path $backupRoot $item.Name
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
            [IO.File]::Copy($item.Target,$backup,$false); $backups+=@{Backup=$backup;Target=$item.Target}
            [IO.File]::Copy($item.Source,$item.Target,$true)
        } else { [IO.File]::Copy($item.Source,$item.Target,$false); $written+=$item.Target }
        if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash -ne $item.Hash) { throw ('Installed hash mismatch: '+$item.Name) }
    }
} catch {
    foreach ($path in $written) { Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue }
    foreach ($b in $backups) { [IO.File]::Copy($b.Backup,$b.Target,$true) }
    throw
}
@{Status='Authored playback installed; live readiness/release pending';UpdateFrom=$UpdateFrom;Files=$items;Utc=[DateTime]::UtcNow.ToString('o')} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root 'installation.json') -Encoding utf8
Write-Output ("Installed {0} changed/new files for {1}; hashes verified." -f $items.Count,$manifest.mission)
