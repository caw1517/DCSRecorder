$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'companion-launch.json') -Raw | ConvertFrom-Json
$arguments='"'+$config.app+'" --settings "'+$config.settings+'"'
Start-Process -FilePath $config.python -ArgumentList $arguments -WorkingDirectory $config.working_directory -WindowStyle Hidden
