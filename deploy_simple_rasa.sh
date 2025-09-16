#!/bin/bash

# Script de despliegue SIMPLE con Rasa básico

echo "🚀 Desplegando con Rasa SIMPLE (solo puente a LLM)..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. Parar servicios existentes
info "🛑 Parando servicios existentes..."
docker-compose -f docker-compose.oracle_arm64.yml down --remove-orphans

# 2. Limpiar imágenes existentes
info "🧹 Limpiando imágenes existentes..."
docker rmi arquitectura-app arquitectura-rasa 2>/dev/null || true
docker system prune -f

# 3. Construir y levantar servicios
info "🏗️ Construyendo y levantando servicios..."
docker-compose -f docker-compose.oracle_arm64.yml build --no-cache
docker-compose -f docker-compose.oracle_arm64.yml up -d

# 4. Esperar a que los servicios estén listos
info "⏳ Esperando a que los servicios estén listos..."
sleep 30

# 5. Verificar estado
info "📊 Estado de los servicios:"
docker-compose -f docker-compose.oracle_arm64.yml ps

# 6. Verificar logs de Rasa
info "📋 Logs de Rasa:"
docker-compose -f docker-compose.oracle_arm64.yml logs rasa --tail=10

success "🎉 Despliegue completado con Rasa SIMPLE"
echo "💡 Rasa ahora solo hace de puente entre el frontend y la LLM"
