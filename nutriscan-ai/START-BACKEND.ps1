# Smart AI Food Scanner - Start backend (run this so Login/Register and Scan work)
Set-Location $PSScriptRoot\backend
$venvPy = Join-Path $PSScriptRoot backend ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    Write-Host "Starting backend on http://127.0.0.1:8000 (using .venv)..."
    & $venvPy -m uvicorn main:app --host 127.0.0.1 --port 8000
} else {
    $py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { $null }
    if (-not $py) { Write-Host "Python not found. Run: cd backend; py -m venv .venv; .venv\Scripts\pip install -r requirements.txt"; exit 1 }
    Write-Host "Starting backend on http://127.0.0.1:8000 ..."
    & $py -m uvicorn main:app --host 127.0.0.1 --port 8000
}
