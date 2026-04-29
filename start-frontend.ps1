# start-frontend.ps1 — Arranca el servidor del frontend
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Arrancando frontend en http://localhost:3000" -ForegroundColor Cyan

Set-Location frontend
python -m http.server 3000
Set-Location ..