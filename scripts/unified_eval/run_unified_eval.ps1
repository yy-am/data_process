$bundleDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $bundleDir "..\..")
Set-Location $projectRoot

$configPath = "$bundleDir\unified_model_eval_config.json"
$localConfigPath = "$bundleDir\unified_model_eval_config.local.json"
if (Test-Path $localConfigPath) {
  $configPath = $localConfigPath
}

& "$projectRoot\python.cmd" -B `
  "$projectRoot\scripts\run_unified_model_eval.py" `
  --config-file "$configPath" `
  --report-dir "$bundleDir\reports"
