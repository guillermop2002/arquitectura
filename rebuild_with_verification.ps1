# Script de rebuild con verificación de errores para Windows PowerShell

Write-Host "🔧 REBUILD CON VERIFICACIÓN DE ERRORES" -ForegroundColor Blue
Write-Host "======================================" -ForegroundColor Blue

# 1. Verificar errores antes del rebuild
Write-Host "1. Verificando errores en el código local..." -ForegroundColor Yellow

if (Test-Path "check_specific_errors.py") {
    python check_specific_errors.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Verificación local completada - Sin errores detectados" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Se detectaron errores en el código local" -ForegroundColor Yellow
        $response = Read-Host "¿Continuar con el rebuild? (y/N)"
        if ($response -notmatch "^[Yy]$") {
            Write-Host "❌ Rebuild cancelado por el usuario" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "⚠️ Script de verificación no encontrado, continuando..." -ForegroundColor Yellow
}

# 2. Parar contenedores
Write-Host "2. Parando contenedores existentes..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml down --remove-orphans

# 3. Limpiar Docker
Write-Host "3. Limpiando Docker..." -ForegroundColor Yellow
if (Test-Path "docker_cleanup.sh") {
    bash docker_cleanup.sh
} else {
    docker system prune -a -f --volumes
}

# 4. Rebuild del contenedor app
Write-Host "4. Reconstruyendo contenedor app..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml build --no-cache app

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Contenedor app reconstruido exitosamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error al reconstruir el contenedor app" -ForegroundColor Red
    exit 1
}

# 5. Levantar servicios
Write-Host "5. Levantando servicios..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml up -d

# 6. Esperar a que los servicios estén listos
Write-Host "6. Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 7. Verificar estado de los servicios
Write-Host "7. Verificando estado de los servicios..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml ps

# 8. Verificar logs de errores
Write-Host "8. Verificando logs de errores..." -ForegroundColor Yellow
Write-Host "Esperando 10 segundos para que se inicialicen los servicios..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Buscar errores específicos en los logs
Write-Host "Buscando errores específicos en los logs..." -ForegroundColor Yellow

# Error de OCR
$ocr_errors = (docker-compose -f docker-compose.oracle_arm64.yml logs app | Select-String "Error in OCR processing: invalid literal for int\(\)").Count
if ($ocr_errors -gt 0) {
    Write-Host "❌ Se encontraron $ocr_errors errores de OCR" -ForegroundColor Red
} else {
    Write-Host "✅ No se encontraron errores de OCR" -ForegroundColor Green
}

# Error de AI Client
$ai_errors = (docker-compose -f docker-compose.oracle_arm64.yml logs app | Select-String "AIClient.*generate_response").Count
if ($ai_errors -gt 0) {
    Write-Host "❌ Se encontraron $ai_errors errores de AI Client" -ForegroundColor Red
} else {
    Write-Host "✅ No se encontraron errores de AI Client" -ForegroundColor Green
}

# Error de Document Analyzer
$doc_errors = (docker-compose -f docker-compose.oracle_arm64.yml logs app | Select-String "unexpected keyword argument 'content'").Count
if ($doc_errors -gt 0) {
    Write-Host "❌ Se encontraron $doc_errors errores de Document Analyzer" -ForegroundColor Red
} else {
    Write-Host "✅ No se encontraron errores de Document Analyzer" -ForegroundColor Green
}

# 9. Probar la aplicación
Write-Host "9. Probando la aplicación..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Aplicación principal funcionando" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Aplicación principal no responde correctamente" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Aplicación principal no responde aún" -ForegroundColor Yellow
}

# 10. Mostrar logs recientes
Write-Host "10. Mostrando logs recientes (últimas 20 líneas)..." -ForegroundColor Yellow
docker-compose -f docker-compose.oracle_arm64.yml logs --tail=20 app

# 11. Resumen final
Write-Host ""
Write-Host "======================================" -ForegroundColor Blue
Write-Host "📊 RESUMEN DEL REBUILD:" -ForegroundColor Blue
Write-Host "======================================" -ForegroundColor Blue

if ($ocr_errors -eq 0 -and $ai_errors -eq 0 -and $doc_errors -eq 0) {
    Write-Host "🎉 ¡REBUILD EXITOSO! No se detectaron errores críticos." -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 PRÓXIMOS PASOS:" -ForegroundColor Yellow
    Write-Host "1. Probar la funcionalidad desde el frontend"
    Write-Host "2. Verificar que el análisis de documentos funciona"
    Write-Host "3. Monitorear los logs para asegurar estabilidad"
} else {
    Write-Host "⚠️ REBUILD COMPLETADO CON ADVERTENCIAS" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "❌ ERRORES DETECTADOS:" -ForegroundColor Red
    Write-Host "   • Errores de OCR: $ocr_errors"
    Write-Host "   • Errores de AI Client: $ai_errors"
    Write-Host "   • Errores de Document Analyzer: $doc_errors"
    Write-Host ""
    Write-Host "🔧 ACCIONES RECOMENDADAS:" -ForegroundColor Yellow
    Write-Host "1. Revisar los logs detallados"
    Write-Host "2. Verificar que las correcciones se aplicaron correctamente"
    Write-Host "3. Considerar un rebuild adicional si es necesario"
}

Write-Host ""
Write-Host "📋 COMANDOS ÚTILES:" -ForegroundColor Cyan
Write-Host "   Ver logs en tiempo real: docker-compose -f docker-compose.oracle_arm64.yml logs -f app"
Write-Host "   Ver estado de servicios: docker-compose -f docker-compose.oracle_arm64.yml ps"
Write-Host "   Reiniciar servicios: docker-compose -f docker-compose.oracle_arm64.yml restart"
Write-Host "   Parar servicios: docker-compose -f docker-compose.oracle_arm64.yml down"
