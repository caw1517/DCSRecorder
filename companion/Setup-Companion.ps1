[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$BaselineMission,
    [Parameter(Mandatory=$true)][string]$DonorMod,
    [Parameter(Mandatory=$true)][string]$AcceptedRecording,
    [string]$SavedGames = (Join-Path $env:USERPROFILE 'Saved Games\DCS'),
    [string]$DcsRoot = 'D:\DCS World'
)
$ErrorActionPreference='Stop'
if(Get-Process DCS -ErrorAction SilentlyContinue){throw 'Close DCS before installing the automatic save hook.'}
$version=(Get-Content -LiteralPath (Join-Path $DcsRoot 'autoupdate.cfg') -Raw | ConvertFrom-Json).version
if($version -ne '2.9.29.27468'){throw "Unsupported DCS build: $version"}
foreach($inputPath in @($Python,$BaselineMission,$AcceptedRecording,(Join-Path $DonorMod 'entry.lua'))){if(-not(Test-Path -LiteralPath $inputPath -PathType Leaf)){throw "Missing dependency: $inputPath"}}
$recorderHome=Join-Path $SavedGames 'DCSRecorder'
$recordings=Join-Path $recorderHome 'recordings'
$hooks=Join-Path $SavedGames 'Scripts\Hooks'
New-Item -ItemType Directory -Path $recordings,$hooks -Force | Out-Null
$hookSource=Join-Path $PSScriptRoot 'recording_sink.lua'
$hookTarget=Join-Path $hooks 'dcs-recorder-autosave.lua'
if(Test-Path -LiteralPath $hookTarget){
 if((Get-FileHash -LiteralPath $hookTarget).Hash -ne (Get-FileHash -LiteralPath $hookSource).Hash){throw 'A different automatic save hook is already installed. Preserve and review it before updating.'}
}else{[IO.File]::Copy($hookSource,$hookTarget,$false)}
$baselineTarget=Join-Path $recordings 'accepted-baseline.csv'
$baselineHash=(Get-FileHash -LiteralPath $AcceptedRecording -Algorithm SHA256).Hash.ToLowerInvariant()
if(Test-Path -LiteralPath $baselineTarget){
 if((Get-FileHash -LiteralPath $baselineTarget).Hash.ToLowerInvariant() -ne $baselineHash){throw 'Existing baseline differs; refusing to replace it.'}
}else{[IO.File]::Copy($AcceptedRecording,$baselineTarget,$false)}
$settingsPath=Join-Path $recorderHome 'companion-settings.json'
$settings=@{saved_games=$SavedGames;dcs=$DcsRoot;baseline_mission=$BaselineMission;donor_mod=$DonorMod;accepted_baseline_sha256=$baselineHash}
if(Test-Path -LiteralPath $settingsPath){[IO.File]::Copy($settingsPath,$settingsPath+'.'+[guid]::NewGuid().ToString('N')+'.bak',$false)}
$settings|ConvertTo-Json|Set-Content -LiteralPath $settingsPath -Encoding UTF8
@{python=$Python;app=(Join-Path $PSScriptRoot 'app.py');settings=$settingsPath;working_directory=$PSScriptRoot}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $recorderHome 'companion-launch.json') -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Start-DCSRecorder.ps1') -Destination (Join-Path $recorderHome 'Start-DCSRecorder.ps1')
if((Get-FileHash -LiteralPath $hookTarget).Hash -ne (Get-FileHash -LiteralPath $hookSource).Hash){throw 'Installed hook hash mismatch.'}
[pscustomobject]@{Settings=$settingsPath;Launcher=(Join-Path $recorderHome 'Start-DCSRecorder.ps1');AutomaticSaveHook=$hookTarget;DcsRestartRequired=$true}
