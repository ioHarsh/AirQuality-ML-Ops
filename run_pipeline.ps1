# run_pipeline.ps1
$now = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$repo = "C:\Users\conhkum\Desktop\ML_OPS"
$venvPython = Join-Path $repo "venv\Scripts\python.exe"
$logDir = Join-Path $repo "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir "pipeline_$now.log"

Write-Output "Starting pipeline at $(Get-Date)" | Out-File -FilePath $logFile -Encoding utf8
Set-Location $repo

# Run pipeline using the venv's Python interpreter
& $venvPython -m src.pipeline_runner  *>> $logFile 2>&1

Write-Output "Finished at $(Get-Date)" >> $logFile
