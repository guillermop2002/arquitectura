#!/bin/bash
# Script de Despliegue Principal
# Sistema de Verificación Arquitectónica - Oracle Cloud ARM64

set -e

# Configuración
APP_DIR="/opt/verification-app"
COMPOSE_FILE="docker-compose.oracle_arm64.yml"
ENV_FILE="env.oracle_arm64.txt"
LOG_FILE="/opt/verification-app/logs/deployment.log"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# Funciones
info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; exit 1; }

# Iniciar log
mkdir -p "$(dirname "$LOG_FILE")"
echo "" > "$LOG_FILE"
info "🚀 Iniciando despliegue automatizado..."

# 1. Validar entorno
info "🔍 Validando entorno de despliegue..."
if ! python validate_production_config.py; then
    error "❌ Validación de entorno falló"
fi

# 2. Detener servicios existentes
info "🛑 Deteniendo servicios existentes..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans || warning "No hay servicios para detener"

# 3. Limpiar recursos
info "🧹 Limpiando recursos Docker..."
docker system prune -f --volumes || warning "Error en limpieza"

# 4. Construir imágenes
info "🏗️ Construyendo imágenes Docker..."
if ! ./build_oracle_arm64.sh; then
    error "❌ Error construyendo imágenes"
fi

# 5. Configurar volúmenes
info "💾 Configurando volúmenes..."
if ! ./setup_volumes_arm64.sh; then
    error "❌ Error configurando volúmenes"
fi

# 6. Aplicar optimizaciones
info "⚡ Aplicando optimizaciones..."
if ! ./optimize_arm64_performance.sh; then
    warning "⚠️ Error aplicando optimizaciones"
fi

# 7. Desplegar servicios
info "🚀 Desplegando servicios..."
if ! docker-compose -f "$COMPOSE_FILE" up -d; then
    error "❌ Error desplegando servicios"
fi

# 8. Esperar inicio
info "⏳ Esperando inicio de servicios..."
sleep 60

# 9. Verificar salud
info "🏥 Verificando salud de servicios..."
if ! python check_external_services.py; then
    error "❌ Verificación de salud falló"
fi

# 10. Ejecutar pruebas de integración
info "🧪 Ejecutando pruebas de integración..."
if ! python integration_tests.py; then
    error "❌ Pruebas de integración fallaron"
fi

info "🎉 Despliegue completado exitosamente!"
