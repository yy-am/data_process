$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

# Fill API keys here before running.
# If you only test one model, only A is required.
$env:POC_MODEL_API_KEY_A = "sk-ooOP32Dy6I5kAl9YzIt6BuKyNCJKxytVCapPniwcRm8POqBT"
$env:POC_MODEL_API_KEY_B = "sk-TPfRsi8dQggoAGGTR9tlMUDwFxJd5S680zHzEneWWueUGH66"

if ([string]::IsNullOrWhiteSpace($env:POC_MODEL_API_KEY_A)) {
    Write-Host "Please fill POC_MODEL_API_KEY_A in scripts\run_model_comparison.ps1 before running." -ForegroundColor Yellow
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputPath = Join-Path $projectRoot "reports\model_comparison_report_$timestamp.xlsx"
$healthUrl = "http://127.0.0.1:8000/health"

try {
    $health = Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 5
    if (-not $health.Content.Contains('"status":"ok"')) {
        Write-Host "Local service is not healthy: $healthUrl" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "Local service is not running. Please start .\start-server.ps1 first." -ForegroundColor Red
    exit 1
}

& "$projectRoot\python.cmd" -B scripts\generate_model_comparison_report.py `
  --config-file scripts\model_eval_config.json `
  --output $outputPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "Model comparison report generation failed. Please check the console output." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Model comparison report generated:" -ForegroundColor Green
Write-Host $outputPath -ForegroundColor Cyan
