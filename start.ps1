# start.ps1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = $PSScriptRoot

$venvActivate = Join-Path $root "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Host "ERROR: No se encontro el entorno virtual" -ForegroundColor Red
    exit 1
}

Write-Host "Entorno virtual activado" -ForegroundColor Green

Push-Location (Join-Path $root "backend")
try {
    uvicorn main:app --reload
} finally {
    Pop-Location
}