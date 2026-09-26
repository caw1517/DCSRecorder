param(
    [Parameter(Mandatory=$true)][string]$Baseline,
    [Parameter(Mandatory=$true)][string]$Tape,
    [string]$DcsRoot='D:\DCS World',
    [string]$OutputDirectory
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$experimentRoot=Split-Path $PSScriptRoot -Parent
if (-not $OutputDirectory) { $OutputDirectory=Join-Path $experimentRoot 'package\staging-prototype' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory=(Resolve-Path -LiteralPath $OutputDirectory).Path
$baselineLua=Join-Path $OutputDirectory 'baseline.lua'
$missionLua=Join-Path $OutputDirectory 'mission'
$missionPackage=Join-Path $OutputDirectory 'DCSRecorder-Staging-Prototype.miz'
if (Test-Path -LiteralPath $missionPackage) { throw 'Output mission exists. Choose a fresh output directory to preserve prior experiments.' }
$zip=[IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $Baseline).Path)
try {
    $entry=$zip.GetEntry('mission')
    if (-not $entry) { throw 'Baseline has no mission entry.' }
    $inputStream=$entry.Open();$outputStream=[IO.File]::Create($baselineLua)
    try { $inputStream.CopyTo($outputStream) } finally { $outputStream.Dispose();$inputStream.Dispose() }
} finally { $zip.Dispose() }
$lua=Join-Path $DcsRoot 'bin\luae.exe'
& $lua (Join-Path $PSScriptRoot 'generate.lua') $baselineLua (Join-Path $PSScriptRoot 'staging.lua') $Tape $missionLua
if ($LASTEXITCODE -ne 0) { throw 'Mission generation failed.' }
& $lua (Join-Path $experimentRoot 'verify_hornet_requirements.lua') $missionLua (Join-Path $DcsRoot 'Mods\aircraft\FA-18C\entry.lua') (Join-Path $DcsRoot 'MissionEditor\modules\me_mission.lua')
if ($LASTEXITCODE -ne 0) { throw 'Mission requirements failed.' }
& $lua (Join-Path $experimentRoot 'verify_hornet_routes.lua') $missionLua (Join-Path $DcsRoot 'MissionEditor\modules\me_route.lua') 2
if ($LASTEXITCODE -ne 0) { throw 'Route checks failed.' }
& $lua (Join-Path $experimentRoot 'verify_hornet_configuration.lua') $missionLua $DcsRoot 2
if ($LASTEXITCODE -ne 0) { throw 'Aircraft configuration checks failed.' }
$zip=[IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $Baseline).Path)
$dest=[IO.Compression.ZipFile]::Open($missionPackage,[IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($entry in $zip.Entries) {
        $target=$dest.CreateEntry($entry.FullName,[IO.Compression.CompressionLevel]::Optimal)
        $stream=$target.Open()
        try {
            if ($entry.FullName -eq 'mission') { $bytes=[IO.File]::ReadAllBytes($missionLua);$stream.Write($bytes,0,$bytes.Length) }
            else { $source=$entry.Open();try { $source.CopyTo($stream) } finally { $source.Dispose() } }
        } finally { $stream.Dispose() }
    }
} finally { $dest.Dispose();$zip.Dispose() }
$manifest=[ordered]@{
    status='Prepared. Live DCS staging behavior unverified.'
    purpose='Active Pause, F10 countdown, simultaneous release, and 150-foot initial separation; stock aircraft only.'
    dcs_version=(Get-Item -LiteralPath (Join-Path $DcsRoot 'bin\DCS.exe')).VersionInfo.FileVersion
    baseline_sha256=(Get-FileHash -LiteralPath $Baseline -Algorithm SHA256).Hash
    tape_sha256=(Get-FileHash -LiteralPath $Tape -Algorithm SHA256).Hash
    mission_sha256=(Get-FileHash -LiteralPath $missionPackage -Algorithm SHA256).Hash
    native_playback_exercised=$false
}
[IO.File]::WriteAllText((Join-Path $OutputDirectory 'manifest.json'),($manifest | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
Write-Output $missionPackage