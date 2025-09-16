# Script de PowerShell para iniciar el sistema
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Sistema de Verificacion Arquitectonica" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Activando entorno virtual y ejecutando..." -ForegroundColor Green
Write-Host ""

# Activar entorno virtual
& .venv_clean\Scripts\Activate.ps1

# Ejecutar script completo
python start_complete.py

Read-Host "Presiona Enter para continuar"
