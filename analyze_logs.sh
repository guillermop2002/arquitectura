#!/bin/bash
# Script para analizar logs y detectar errores específicos

echo "🔍 ANÁLISIS DE LOGS - SISTEMA DE VERIFICACIÓN"
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

# 1. Obtener logs del contenedor app
show_status "1. Obteniendo logs del contenedor app..."
logs=$(docker-compose -f docker-compose.oracle_arm64.yml logs app)

# 2. Analizar errores específicos
show_status "2. Analizando errores específicos..."

# Error de OCR
ocr_errors=$(echo "$logs" | grep -c "Error in OCR processing: invalid literal for int()" || echo "0")
if [ "$ocr_errors" -gt 0 ]; then
    show_error "Se encontraron $ocr_errors errores de OCR"
    echo "   📍 Ejemplos de errores OCR:"
    echo "$logs" | grep "Error in OCR processing: invalid literal for int()" | head -3 | sed 's/^/      /'
else
    show_success "No se encontraron errores de OCR"
fi

# Error de AI Client
ai_errors=$(echo "$logs" | grep -c "AIClient.*generate_response" || echo "0")
if [ "$ai_errors" -gt 0 ]; then
    show_error "Se encontraron $ai_errors errores de AI Client"
    echo "   📍 Ejemplos de errores AI Client:"
    echo "$logs" | grep "AIClient.*generate_response" | head -3 | sed 's/^/      /'
else
    show_success "No se encontraron errores de AI Client"
fi

# Error de Document Analyzer
doc_errors=$(echo "$logs" | grep -c "unexpected keyword argument 'content'" || echo "0")
if [ "$doc_errors" -gt 0 ]; then
    show_error "Se encontraron $doc_errors errores de Document Analyzer"
    echo "   📍 Ejemplos de errores Document Analyzer:"
    echo "$logs" | grep "unexpected keyword argument 'content'" | head -3 | sed 's/^/      /'
else
    show_success "No se encontraron errores de Document Analyzer"
fi

# Error de sesión
session_errors=$(echo "$logs" | grep -c "Sesión no encontrada" || echo "0")
if [ "$session_errors" -gt 0 ]; then
    show_error "Se encontraron $session_errors errores de sesión"
    echo "   📍 Ejemplos de errores de sesión:"
    echo "$logs" | grep "Sesión no encontrada" | head -3 | sed 's/^/      /'
else
    show_success "No se encontraron errores de sesión"
fi

# Error de Unknown
unknown_errors=$(echo "$logs" | grep -c "Error en Unknown:" || echo "0")
if [ "$unknown_errors" -gt 0 ]; then
    show_error "Se encontraron $unknown_errors errores desconocidos"
    echo "   📍 Ejemplos de errores desconocidos:"
    echo "$logs" | grep "Error en Unknown:" | head -3 | sed 's/^/      /'
else
    show_success "No se encontraron errores desconocidos"
fi

# 3. Resumen de errores
echo ""
echo "=============================================="
echo "📊 RESUMEN DE ERRORES:"
echo "=============================================="

total_errors=$((ocr_errors + ai_errors + doc_errors + session_errors + unknown_errors))

echo "   • Errores de OCR: $ocr_errors"
echo "   • Errores de AI Client: $ai_errors"
echo "   • Errores de Document Analyzer: $doc_errors"
echo "   • Errores de sesión: $session_errors"
echo "   • Errores desconocidos: $unknown_errors"
echo "   • TOTAL: $total_errors errores"

# 4. Recomendaciones
echo ""
echo "=============================================="
echo "💡 RECOMENDACIONES:"
echo "=============================================="

if [ "$total_errors" -eq 0 ]; then
    show_success "¡No se detectaron errores! El sistema está funcionando correctamente."
else
    if [ "$ocr_errors" -gt 0 ]; then
        echo "🔧 OCR: Verificar que enhanced_ocr_processor.py usa float() en lugar de int()"
    fi
    
    if [ "$ai_errors" -gt 0 ]; then
        echo "🔧 AI Client: Verificar que todos los archivos usan generate_completion() en lugar de generate_response()"
    fi
    
    if [ "$doc_errors" -gt 0 ]; then
        echo "🔧 Document Analyzer: Verificar que las llamadas usan pdf_doc y classification en lugar de content"
    fi
    
    if [ "$session_errors" -gt 0 ]; then
        echo "🔧 Sesión: Verificar que session_file_manager está funcionando correctamente"
    fi
    
    if [ "$unknown_errors" -gt 0 ]; then
        echo "🔧 Desconocidos: Revisar la inicialización de componentes"
    fi
    
    echo ""
    echo "🚀 ACCIÓN RECOMENDADA:"
    echo "   Ejecutar: ./rebuild_server.sh"
fi

# 5. Mostrar logs recientes
echo ""
echo "=============================================="
echo "📋 LOGS RECIENTES (últimas 20 líneas):"
echo "=============================================="
docker-compose -f docker-compose.oracle_arm64.yml logs --tail=20 app

echo ""
echo "🔍 Para ver logs en tiempo real:"
echo "   docker-compose -f docker-compose.oracle_arm64.yml logs -f app"
