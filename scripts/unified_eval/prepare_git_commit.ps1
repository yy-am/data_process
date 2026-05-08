$bundleDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$safeConfig = Join-Path $bundleDir "unified_model_eval_config.example.json"
$targetConfig = Join-Path $bundleDir "unified_model_eval_config.json"

Copy-Item -LiteralPath $safeConfig -Destination $targetConfig -Force
Write-Output "已将 unified_model_eval_config.json 重置为 example 安全配置。"
