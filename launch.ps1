$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = Join-Path $here "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Start-Transcript -Path (Join-Path $logDir "run_$stamp.log") | Out-Null

$venv = Join-Path $here "venv\Scripts\Activate.ps1"
. $venv

function Fail-Friendly($msg) {
  Write-Host "`n=== DEMO-SAFE ERROR ===" -ForegroundColor Red
  Write-Host $msg -ForegroundColor Yellow
  Write-Host "A support bundle was created in the logs/ folder." -ForegroundColor Yellow
  Stop-Transcript | Out-Null
  exit 1
}

try {
  python tools/doctor.py
} catch {
  Compress-Archive -Path $logDir\* -DestinationPath (Join-Path $logDir "support_$stamp.zip") -Force
  Fail-Friendly "Preflight failed. Fix the issues and re-run."
}

try {
  python app.py
} catch {
  Compress-Archive -Path $logDir\* -DestinationPath (Join-Path $logDir "support_$stamp.zip") -Force
  Fail-Friendly "App execution failed. Check logs for details."
}

Stop-Transcript | Out-Null
Write-Host "`n✅ Run completed successfully." -ForegroundColor Green
exit 0
