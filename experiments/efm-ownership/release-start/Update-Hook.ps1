[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InstalledPackage,
    [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
    [string]$SavedGames=(Join-Path $env:USERPROFILE 'Saved Games\DCS')
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before updating the diagnostic hook.' }
$savedRoot=(Resolve-Path -LiteralPath $SavedGames).Path
$packageRoot=(Resolve-Path -LiteralPath $InstalledPackage).Path
$manifest=Get-Content -LiteralPath (Join-Path $packageRoot 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.profile -ne 'release-airborne-v1') { throw 'Unexpected package.' }
$relative='Scripts/Hooks/DCSRecorderReleaseControl.lua'
$target=[IO.Path]::GetFullPath((Join-Path $savedRoot $relative))
$source=Join-Path $PSScriptRoot 'hook.lua'
$before=@{}
foreach ($entry in $manifest.files.PSObject.Properties) {
    $path=[IO.Path]::GetFullPath((Join-Path $savedRoot $entry.Name))
    if (-not $path.StartsWith($savedRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid manifest path.' }
    $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if ($hash -ne $entry.Value) { throw "Installed file no longer matches package: $($entry.Name)" }
    $before[$path]=$hash
}
$evidenceRoot=[IO.Path]::GetFullPath($EvidenceDirectory)
if (Test-Path -LiteralPath $evidenceRoot) { throw 'Use a fresh evidence directory.' }
New-Item -ItemType Directory -Path $evidenceRoot | Out-Null
[IO.File]::Copy($target,(Join-Path $evidenceRoot 'previous-hook.lua'),$false)
[IO.File]::Copy($source,(Join-Path $evidenceRoot 'installed-hook.lua'),$false)
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during preflight.' }
[IO.File]::Copy($source,$target,$true)
$after=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
if ($after -ne (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash) { throw 'Updated hook hash mismatch.' }
foreach ($path in $before.Keys) {
    if ($path -eq $target) { continue }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $before[$path]) { throw "Other package file changed: $path" }
}
[ordered]@{Status='Installed targeted readiness diagnostics';Target=$target;PreviousSha256=$before[$target];Sha256=$after;UnchangedFiles=$before.Count-1} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidenceRoot 'receipt.json') -Encoding UTF8
Write-Output "Updated only $target; all 13 other package files unchanged."
