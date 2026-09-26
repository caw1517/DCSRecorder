param([Parameter(Mandatory=$true)][string]$LogFile)
$ErrorActionPreference='Stop'
$invariant=[Globalization.CultureInfo]::InvariantCulture
function Number([string]$text) { [double]::Parse($text,$invariant) }
function Distance($a,$b) { [math]::Sqrt([math]::Pow($a.x-$b.x,2)+[math]::Pow($a.y-$b.y,2)+[math]::Pow($a.z-$b.z,2)) }
$runs=[Collections.Generic.List[object]]::new()
$current=$null
foreach ($line in [IO.File]::ReadLines((Resolve-Path -LiteralPath $LogFile).Path)) {
    if ($line -match 'DCS_STAGE_EVENT,([^,]+),([^,\r\n]+)') {
        $time=Number $Matches[1];$eventName=$Matches[2]
        if ($eventName -eq 'INITIALIZED') {
            $current=@{events=[Collections.Generic.List[object]]::new();samples=[Collections.Generic.List[object]]::new()}
            $runs.Add($current)
        }
        if ($current) { $current.events.Add(@{time=$time;name=$eventName}) }
    } elseif ($current -and $line -match 'DCS_STAGE_SAMPLE,(.*)$') {
        $parts=$Matches[1].Split(',')
        if ($parts.Count -ne 12) { throw 'Incomplete staging telemetry row. Preserve the original log.' }
        $current.samples.Add(@{phase=$parts[0];name=$parts[1];time=(Number $parts[2]);x=(Number $parts[3]);y=(Number $parts[4]);z=(Number $parts[5])})
    }
}
if ($runs.Count -eq 0) { throw 'No staging experiment found in this log. Live validation has not been captured.' }
foreach ($run in $runs) {
    $held=@($run.samples | Where-Object { $_.name -eq 'Observer' -and $_.phase -in @('waiting','countdown','release_requested') })
    $released=@($run.events | Where-Object { $_.name -eq 'RELEASE' })
    $start=@($run.events | Where-Object { $_.name -eq 'F10_START' })
    $removed=@($run.events | Where-Object { $_.name -eq 'LEAD_REMOVED' })
    $player=@($run.samples | Where-Object { $_.name -eq 'Observer' -and $_.phase -eq 'flying' })
    $lead=@($run.samples | Where-Object { $_.name -eq 'StageLead' -and $_.phase -eq 'flying' })
    $continued=@($run.samples | Where-Object { $_.name -eq 'Observer' -and $_.phase -eq 'complete' })
    $drift=$null;$separation=$null;$countdown=$null;$playerTravel=$null
    if ($held.Count) { $drift=($held | ForEach-Object { Distance $_ $held[0] } | Measure-Object -Maximum).Maximum }
    if ($player.Count -and $lead.Count) {
        $paired=@($player | Where-Object { [math]::Abs($_.time-$lead[0].time) -lt 0.000001 })
        if ($paired.Count) { $separation=Distance $paired[0] $lead[0] }
    }
    if ($released.Count -and $start.Count) { $countdown=$released[0].time-$start[0].time }
    if ($player.Count -gt 1) { $playerTravel=Distance $player[0] $player[-1] }
    [ordered]@{
        result='Measurements only; pilot confirmation and native playback integration remain required.'
        events=$run.events
        held_sample_count=$held.Count
        max_player_drift_while_held_m=$drift
        countdown_simulation_seconds=$countdown
        first_simultaneous_separation_m=$separation
        target_separation_m=45.72
        player_travel_after_release_m=$playerTravel
        lead_removal_observed=($removed.Count -gt 0)
        player_samples_after_removal=$continued.Count
        required_pilot_observations='F10 usable while held; countdown visible; no unexpected pause toggle; normal controls after release; mission continues.'
    } | ConvertTo-Json -Depth 6
}