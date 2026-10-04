[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Source,[Parameter(Mandatory=$true)][string]$Name,
      [Parameter(Mandatory=$true)][string]$Sha256,[switch]$ValidateOnly)
# Additive install of one prepared mission: DCS closed, no overwrite, hash verified.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before installing the mission.' }
if ($Name -notmatch '^[\w.-]+\.miz$') { throw 'Mission name must be a plain .miz file name.' }
$missions=(Resolve-Path -LiteralPath (Join-Path $env:USERPROFILE 'Saved Games/DCS/Missions')).Path
$target=Join-Path $missions $Name
$path=(Resolve-Path -LiteralPath $Source).Path
if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $Sha256.ToUpperInvariant()) { throw 'Prepared mission hash differs.' }
if (Test-Path -LiteralPath $target) { throw ('Existing mission will not be overwritten: '+$target) }
if ($ValidateOnly) { Write-Output "Validated $Name; no changes."; return }
[IO.File]::Copy($path,$target,$false)
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $Sha256.ToUpperInvariant()) { Remove-Item -LiteralPath $target -Force; throw 'Installed hash mismatch.' }
Write-Output "Installed $Name; hash verified."
