$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
& "$projectRoot\python.cmd" -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000
