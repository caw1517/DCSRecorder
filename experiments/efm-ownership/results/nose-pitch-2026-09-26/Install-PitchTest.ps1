$ErrorActionPreference = 'Stop'
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'Close DCS before installing the pitch test.' }
$testDll = 'C:\Users\w_can\.codex\worktrees\airborne-staging\DCS_Recorder\experiments\efm-ownership\build\Release\HornetStagedProbe.dll'
$installedDll = 'C:\Users\w_can\Saved Games\DCS\Mods\aircraft\DCSRecorder-Hornet-Staged\bin\HornetStagedProbe.dll'
$tape = 'C:\Users\w_can\Saved Games\DCS\Mods\aircraft\DCSRecorder-Hornet-Staged\bin\recorded-flight.txt'
$expectedDiagnostic = '84F1EE567B8BF24CA254F03306A609E6C7F853AE5D09DD329ED7072F5193FA5A'
$expectedTape = '7A08359BA48BBD9087BEA9DA89B43074B0AAB7B2889F036E5677EA8669ED4B49'
if ((Get-FileHash -LiteralPath $installedDll).Hash -ne $expectedDiagnostic) { throw 'Installed DLL changed; inspect before replacement.' }
if ((Get-FileHash -LiteralPath $tape).Hash -ne $expectedTape) { throw 'Active recording changed; retain the matched comparison case.' }
$backup = Join-Path $PSScriptRoot 'rollback\HornetStagedProbe-diagnostic-only.dll'
[IO.File]::Copy($installedDll,$backup,$false)
if ((Get-FileHash -LiteralPath $backup).Hash -ne $expectedDiagnostic) { throw 'Rollback copy verification failed.' }
$testHash = (Get-FileHash -LiteralPath $testDll).Hash
if (Get-Process DCS -ErrorAction SilentlyContinue) { throw 'DCS started during validation; installation stopped.' }
[IO.File]::Copy($testDll,$installedDll,$true)
if ((Get-FileHash -LiteralPath $installedDll).Hash -ne $testHash) { throw 'Installed pitch-test hash mismatch.' }
$receipt = [pscustomobject]@{
    InstalledUtc=[DateTime]::UtcNow.ToString('o'); InstalledDll=$installedDll;
    PreviousSha256=$expectedDiagnostic; TestSha256=$testHash; Backup=$backup;
    TapeSha256=(Get-FileHash -LiteralPath $tape).Hash;
    Mission='DCSRecorder-Playback-d7a5d25a.miz'; Tests='12/12 CTests passed';
    Status='Installed pitch suppression experiment; live validation pending'
}
$receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'pitch-test-installation.json') -Encoding utf8
$receipt | ConvertTo-Json
