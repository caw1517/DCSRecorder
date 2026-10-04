[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PackageDirectory,
    [string]$SavedGames='C:\Users\w_can\Saved Games\DCS',
    [string]$Repo='E:\Projects\DCS_Recorder',
    [string]$DcsRoot='D:\DCS World',
    [switch]$ValidateOnly
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before installing.' }
$packageRoot=(Resolve-Path -LiteralPath $PackageDirectory).Path
$manifest=Get-Content -LiteralPath (Join-Path $packageRoot 'manifest.json') -Raw | ConvertFrom-Json
$name='047-Hornet-Hot-Ground-Capture.miz'
if ($manifest.profile -ne 'hot-ground-source-capture-v1' -or $manifest.mission -ne $name -or $manifest.dcs_build -ne '2.9.30.28536') { throw 'Unexpected capture package.' }
$build=(Get-Content -LiteralPath (Join-Path $DcsRoot 'autoupdate.cfg') -Raw | ConvertFrom-Json).version
if ($build -ne $manifest.dcs_build) { throw 'DCS build differs from this capture profile.' }
$source=Join-Path $packageRoot $name
$target=Join-Path $SavedGames "Missions\$name"
if (Test-Path -LiteralPath $target) { throw 'Capture mission already exists; refusing overwrite.' }
if ((Get-FileHash -LiteralPath $source).Hash -ne $manifest.sha256) { throw 'Package mission hash mismatch.' }
$dependencies=@{
    'Scripts\Hooks\dcs-recorder-autosave.lua'='companion\recording_sink.lua'
    'Scripts\DCSRecorderEngineCapture\engine_capture.lua'='companion\engine_capture.lua'
    'Scripts\DCSRecorderSmokeCapture\smoke_capture.lua'='companion\smoke_capture.lua'
    'Scripts\DCSRecorderEngineCapture\NativeEngineCapture2930.dll'='experiments\efm-ownership\build\Release\NativeEngineCapture2930.dll'
    'Scripts\DCSRecorderSmokeCapture\NativeSmokeCapture2930.dll'='experiments\efm-ownership\build\Release\NativeSmokeCapture2930.dll'
}
$hashes=@{}
foreach ($relative in $dependencies.Keys) {
    $installed=Join-Path $SavedGames $relative
    $hashes[$relative]=(Get-FileHash -LiteralPath $installed).Hash
    if ($hashes[$relative] -ne (Get-FileHash -LiteralPath (Join-Path $Repo $dependencies[$relative])).Hash) { throw "Installed capture dependency differs: $relative" }
}
if ($ValidateOnly) { [pscustomobject]@{Status='Validated'; Mission=$target; CaptureDependencies=$hashes.Count}; return }
$receipt=Join-Path $packageRoot 'installation.json'
if (Test-Path -LiteralPath $receipt) { throw 'Installation receipt already exists.' }
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during preflight.' }
[IO.File]::Copy($source,$target,$false)
if ((Get-FileHash -LiteralPath $target).Hash -ne $manifest.sha256) { throw 'Installed mission hash mismatch.' }
foreach ($relative in $hashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $SavedGames $relative)).Hash -ne $hashes[$relative]) { throw 'Capture dependency changed during installation.' }
}
[ordered]@{Status='Installed and verified'; InstalledUtc=[DateTime]::UtcNow.ToString('o'); Mission=$target; Sha256=$manifest.sha256; Dependencies=$hashes} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receipt -Encoding utf8
Write-Output "Installed and verified $target"
