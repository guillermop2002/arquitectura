# Script simple de rebuild para Windows PowerShell

Write-Host "🔧 REBUILD SIMPLE CON VERIFICACIÓN" -ForegroundColor Blue
Write-Host "=================================" -ForegroundColor Blue

# 1. Verificar errores
Write-Host "1. Verificando errores..." -ForegroundColor Yellow
python check_specific_errors.py

# 2. Parar contenedores
Write-Host "2. Parando contenedores..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml down --remove-orphans

# 3. Limpiar Docker
Write-Host "3. Limpiando Docker..." -ForegroundColor Yellow
docker system prune -a -f --volumes

# 4. Rebuild
Write-Host "4. Reconstruyendo..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml build --no-cache app

# 5. Levantar servicios
Write-Host "5. Levantando servicios..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml up -d

# 6. Esperar
Write-Host "6. Esperando inicialización..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# 7. Verificar logs
Write-Host "7. Verificando logs..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml logs --tail=30 app

Write-Host "✅ Rebuild completado" -ForegroundColor Green
