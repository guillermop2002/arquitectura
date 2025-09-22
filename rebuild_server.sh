#!/bin/bash
# Script de rebuild optimizado para Oracle Cloud ARM64

echo "🚀 REBUILD OPTIMIZADO PARA ORACLE CLOUD ARM64"
echo "=============================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función para mostrar estado
show_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

show_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

show_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

show_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Verificar errores antes del rebuild
show_status "1. Verificando errores en el código..."
if [ -f "check_specific_errors.py" ]; then
    python3 check_specific_errors.py
    if [ $? -eq 0 ]; then
        show_success "Verificación local completada - Sin errores detectados"
    else
        show_warning "Se detectaron errores en el código local"
        echo "¿Continuar con el rebuild? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            show_error "Rebuild cancelado por el usuario"
            exit 1
        fi
    fi
else
    show_warning "Script de verificación no encontrado, continuando..."
fi

# 2. Parar contenedores existentes
show_status "2. Parando contenedores existentes..."
docker-compose -f docker-compose.oracle_arm64.yml down --remove-orphans

# 3. Limpiar Docker completamente
show_status "3. Limpiando Docker completamente..."
docker container prune -f
docker image prune -a -f
docker volume prune -f
docker network prune -f
docker builder prune -a -f
docker system prune -a -f --volumes

# 4. Rebuild del contenedor app con cache limpio
show_status "4. Reconstruyendo contenedor app (esto puede tomar varios minutos)..."
docker-compose -f docker-compose.oracle_arm64.yml build --no-cache --pull app

if [ $? -eq 0 ]; then
    show_success "Contenedor app reconstruido exitosamente"
else
    show_error "Error al reconstruir el contenedor app"
    exit 1
fi

# 5. Levantar servicios
show_status "5. Levantando servicios..."
docker-compose -f docker-compose.oracle_arm64.yml up -d

# 6. Esperar a que los servicios estén listos
show_status "6. Esperando a que los servicios estén listos (60 segundos)..."
sleep 60

# 7. Verificar estado de los servicios
show_status "7. Verificando estado de los servicios..."
docker-compose -f docker-compose.oracle_arm64.yml ps

# 8. Verificar logs de errores específicos
show_status "8. Verificando logs de errores específicos..."
echo "Esperando 30 segundos adicionales para inicialización completa..."
sleep 30

# Buscar errores específicos en los logs
show_status "Buscando errores específicos en los logs..."

# Error de OCR
ocr_errors=$(docker-compose -f docker-compose.oracle_arm64.yml logs app | grep -c "Error in OCR processing: invalid literal for int()" || echo "0")
if [ "$ocr_errors" -gt 0 ]; then
    show_error "Se encontraron $ocr_errors errores de OCR"
else
    show_success "No se encontraron errores de OCR"
fi

# Error de AI Client
ai_errors=$(docker-compose -f docker-compose.oracle_arm64.yml logs app | grep -c "AIClient.*generate_response" || echo "0")
if [ "$ai_errors" -gt 0 ]; then
    show_error "Se encontraron $ai_errors errores de AI Client"
else
    show_success "No se encontraron errores de AI Client"
fi

# Error de Document Analyzer
doc_errors=$(docker-compose -f docker-compose.oracle_arm64.yml logs app | grep -c "unexpected keyword argument 'content'" || echo "0")
if [ "$doc_errors" -gt 0 ]; then
    show_error "Se encontraron $doc_errors errores de Document Analyzer"
else
    show_success "No se encontraron errores de Document Analyzer"
fi

# Error de sesión
session_errors=$(docker-compose -f docker-compose.oracle_arm64.yml logs app | grep -c "Sesión no encontrada" || echo "0")
if [ "$session_errors" -gt 0 ]; then
    show_error "Se encontraron $session_errors errores de sesión"
else
    show_success "No se encontraron errores de sesión"
fi

# 9. Probar la aplicación
show_status "9. Probando la aplicación..."
sleep 15

if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    show_success "Aplicación principal funcionando correctamente"
else
    show_warning "Aplicación principal no responde aún"
fi

# 10. Mostrar logs recientes
show_status "10. Mostrando logs recientes (últimas 30 líneas)..."
docker-compose -f docker-compose.oracle_arm64.yml logs --tail=30 app

# 11. Resumen final
echo ""
echo "=============================================="
echo "📊 RESUMEN DEL REBUILD:"
echo "=============================================="

total_errors=$((ocr_errors + ai_errors + doc_errors + session_errors))

if [ "$total_errors" -eq 0 ]; then
    show_success "🎉 ¡REBUILD EXITOSO! No se detectaron errores críticos."
    echo ""
    echo "🎯 PRÓXIMOS PASOS:"
    echo "1. Probar la funcionalidad desde el frontend"
    echo "2. Verificar que el análisis de documentos funciona"
    echo "3. Monitorear los logs para asegurar estabilidad"
    echo ""
    echo "🌐 ACCESO A LA APLICACIÓN:"
    echo "   • Frontend: http://$(curl -s ifconfig.me)"
    echo "   • Health Check: http://$(curl -s ifconfig.me)/health"
    echo "   • Neo4j Browser: http://$(curl -s ifconfig.me):7474"
else
    show_warning "⚠️ REBUILD COMPLETADO CON ADVERTENCIAS"
    echo ""
    echo "❌ ERRORES DETECTADOS:"
    echo "   • Errores de OCR: $ocr_errors"
    echo "   • Errores de AI Client: $ai_errors"
    echo "   • Errores de Document Analyzer: $doc_errors"
    echo "   • Errores de sesión: $session_errors"
    echo "   • TOTAL: $total_errors errores"
    echo ""
    echo "🔧 ACCIONES RECOMENDADAS:"
    echo "1. Revisar los logs detallados"
    echo "2. Verificar que las correcciones se aplicaron correctamente"
    echo "3. Considerar un rebuild adicional si es necesario"
fi

echo ""
echo "📋 COMANDOS ÚTILES:"
echo "   Ver logs en tiempo real: docker-compose -f docker-compose.oracle_arm64.yml logs -f app"
echo "   Ver estado de servicios: docker-compose -f docker-compose.oracle_arm64.yml ps"
echo "   Reiniciar servicios: docker-compose -f docker-compose.oracle_arm64.yml restart"
echo "   Parar servicios: docker-compose -f docker-compose.oracle_arm64.yml down"
echo "   Ver logs específicos: docker-compose -f docker-compose.oracle_arm64.yml logs app | grep ERROR"
echo ""
echo "🔍 DIAGNÓSTICO ADICIONAL:"
echo "   Verificar espacio en disco: df -h"
echo "   Verificar memoria: free -h"
echo "   Verificar procesos Docker: docker ps -a"
