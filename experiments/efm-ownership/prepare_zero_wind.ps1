param(
    [string]$SourceMission = 'C:/Users/w_can/Saved Games/DCS/Missions/EFM-Probe-climbing-turn-formation.miz',
    [string]$Lua = 'D:/DCS World/bin/luae.exe'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$outputDirectory = Join-Path $PSScriptRoot 'package/Missions'
$target = Join-Path $outputDirectory 'EFM-Probe-climbing-turn-formation-zero-wind.miz'
if ([IO.Path]::GetFullPath($SourceMission) -eq [IO.Path]::GetFullPath($target)) { throw 'Source and output must differ' }
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
$sourceHash = (Get-FileHash -LiteralPath $SourceMission).Hash
$sourceZip = [IO.Compression.ZipFile]::OpenRead($SourceMission)
try {
    $reader = [IO.StreamReader]::new($sourceZip.GetEntry('mission').Open())
    try { $baseline = $reader.ReadToEnd() } finally { $reader.Dispose() }
} finally { $sourceZip.Dispose() }
$modified = $baseline
foreach ($layer in @('atGround', 'at2000', 'at8000')) {
    $pattern = '(\["' + $layer + '"\]\s*=\s*\{[^{}]*?\["speed"\]\s*=\s*)[0-9.]+'
    if ([regex]::Matches($modified, $pattern).Count -ne 1) { throw "Unexpected wind layer: $layer" }
    $modified = [regex]::Replace($modified, $pattern, '${1}0')
}
$baselinePath = Join-Path $PSScriptRoot 'package/formation-wind-baseline.lua'
$modifiedPath = Join-Path $PSScriptRoot 'package/formation-zero-wind.lua'
[IO.File]::WriteAllText($baselinePath, $baseline)
[IO.File]::WriteAllText($modifiedPath, $modified)
& $Lua (Join-Path $PSScriptRoot 'verify_zero_wind.lua') $baselinePath $modifiedPath
if ($LASTEXITCODE -ne 0) { throw 'Mission semantic verification failed' }
Copy-Item -LiteralPath $SourceMission -Destination $target -Force
$targetZip = [IO.Compression.ZipFile]::Open($target, 'Update')
try {
    $targetZip.GetEntry('mission').Delete()
    [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($targetZip, $modifiedPath, 'mission') | Out-Null
} finally { $targetZip.Dispose() }
# Compare uncompressed bytes for every archive member, including the changed mission.
$sourceZip = [IO.Compression.ZipFile]::OpenRead($SourceMission)
$targetZip = [IO.Compression.ZipFile]::OpenRead($target)
try {
    if ($sourceZip.Entries.Count -ne $targetZip.Entries.Count) { throw 'Archive member count changed' }
    foreach ($entry in $sourceZip.Entries) {
        $other = $targetZip.GetEntry($entry.FullName)
        if ($null -eq $other) { throw "Missing archive member: $($entry.FullName)" }
        $stream = $other.Open()
        $hasher = [Security.Cryptography.SHA256]::Create()
        try { $actual = [Convert]::ToBase64String($hasher.ComputeHash($stream)) }
        finally { $stream.Dispose(); $hasher.Dispose() }
        if ($entry.FullName -eq 'mission') {
            $expected = [Convert]::ToBase64String([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($modifiedPath)))
        } else {
            $stream = $entry.Open()
            $hasher = [Security.Cryptography.SHA256]::Create()
            try { $expected = [Convert]::ToBase64String($hasher.ComputeHash($stream)) }
            finally { $stream.Dispose(); $hasher.Dispose() }
        }
        if ($actual -ne $expected) { throw "Archive member verification failed: $($entry.FullName)" }
    }
} finally { $sourceZip.Dispose(); $targetZip.Dispose() }
if ((Get-FileHash -LiteralPath $SourceMission).Hash -ne $sourceHash) { throw 'Source mission changed' }
[ordered]@{
    source = $SourceMission
    source_sha256 = $sourceHash
    output = $target
    output_sha256 = (Get-FileHash -LiteralPath $target).Hash
    verification = 'Only the three wind speeds changed; all other mission values and archive members match.'
} | ConvertTo-Json | Tee-Object -FilePath (Join-Path $PSScriptRoot 'package/zero-wind-verification.json')
