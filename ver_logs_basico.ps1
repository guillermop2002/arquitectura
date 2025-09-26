# Script para ver logs del sistema básico
param(
    [string]$Mode = "remote"
)

Write-Host "🔍 LOGS DEL SISTEMA BÁSICO" -ForegroundColor Cyan

if ($Mode -eq "remote") {
    Write-Host "📡 Conectando a Oracle Cloud..." -ForegroundColor Yellow
    ssh ubuntu@158.179.210.136 'cd ~/arquitectura; docker-compose -f docker-compose.basico.yml logs --tail 50'
}
elseif ($Mode -eq "local") {
    Write-Host "💻 Logs locales..." -ForegroundColor Green
    if (Test-Path "logs/basico_detailed.log") {
        Get-Content "logs/basico_detailed.log" -Tail 50
    } else {
        Write-Host "❌ Sin logs locales"
    }
}
else {
    Write-Host "❌ Usar: -Mode remote o -Mode local" -ForegroundColor Red
}