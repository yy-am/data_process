$bundleDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $bundleDir "..\..")
Set-Location $projectRoot

& "$projectRoot\start-server.ps1"
