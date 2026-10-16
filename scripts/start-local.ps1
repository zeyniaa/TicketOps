param([switch]$Install, [switch]$NoLLM)
$ErrorActionPreference='Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
if ($Install) {
    uv venv --python 3.12 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Gagal menyiapkan Python. Pasang uv dan Python 3.12.' }
    uv pip install --python .venv/Scripts/python.exe -r backend/requirements.lock
    uv pip install --python .venv/Scripts/python.exe --no-deps -e ./backend
    if ($LASTEXITCODE -ne 0) { throw 'Pemasangan dependency Python gagal.' }
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Pemasangan dependency frontend gagal.' }
}
$taskPython=Join-Path $taskRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Jalankan skrip dengan -Install untuk penggunaan pertama.' }
if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'ml/artifacts/baseline.joblib'))) {
    & $taskPython ml/train_baseline.py
    if ($LASTEXITCODE -ne 0) { throw 'Training baseline gagal.' }
}
if ($NoLLM) { $env:TICKETOPS_LLM_ENABLED='false' }
& $taskPython -m alembic -c backend/alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migrasi database gagal.' }
foreach ($taskPort in 8018,5178) {
    if (Get-NetTCPConnection -LocalPort $taskPort -State Listen -ErrorAction SilentlyContinue) { throw "Port $taskPort sedang dipakai. Hentikan sesi TicketOps sebelumnya." }
}
$taskApi=Start-Process -FilePath $taskPython -ArgumentList '-m','uvicorn','ticketops.main:app','--host','127.0.0.1','--port','8018','--no-access-log' -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru
$taskWorker=Start-Process -FilePath $taskPython -ArgumentList '-m','ticketops.worker' -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru
try {
    $env:VITE_MODE='api'
    Write-Host 'TicketOps: http://127.0.0.1:5178 | API docs: http://127.0.0.1:8018/docs'
    node node_modules/vite/bin/vite.js frontend --host 127.0.0.1 --port 5178
} finally {
    $taskApi,$taskWorker | Where-Object { $_ -and -not $_.HasExited } | Stop-Process
}
