# setup.ps1 — Configuracion inicial (ejecutar solo una vez)
Write-Host "Configurando permisos de ejecucion de scripts..." -ForegroundColor Yellow
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Write-Host "Listo. Ya puedes usar start.ps1 y start-frontend.ps1" -ForegroundColor Green