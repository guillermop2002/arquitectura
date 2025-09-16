#!/bin/bash

# Script de despliegue con entrenamiento de Rasa

echo "🚀 Desplegando con modelo de Rasa entrenado..."

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

# 1. Verificar que existe el directorio rasa_bot
if [ ! -d "rasa_bot" ]; then
    error "Directorio rasa_bot no encontrado"
    exit 1
fi

# 2. Entrenar modelo de Rasa localmente
info "🤖 Entrenando modelo de Rasa..."
cd rasa_bot
rasa train
if [ $? -eq 0 ]; then
    success "Modelo de Rasa entrenado exitosamente"
else
    error "Error al entrenar modelo de Rasa"
    exit 1
fi
cd ..

# 3. Verificar que el modelo se creó
if [ -f "rasa_bot/models/*.tar.gz" ]; then
    success "Modelo encontrado: $(ls rasa_bot/models/*.tar.gz)"
else
    warning "No se encontró modelo entrenado, se entrenará durante el build"
fi

# 4. Parar servicios existentes
info "🛑 Parando servicios existentes..."
docker-compose -f docker-compose.oracle_arm64.yml down --remove-orphans

# 5. Limpiar imágenes existentes
info "🧹 Limpiando imágenes existentes..."
docker rmi arquitectura-app arquitectura-rasa 2>/dev/null || true
docker system prune -f

# 6. Construir y levantar servicios
info "🏗️ Construyendo y levantando servicios..."
docker-compose -f docker-compose.oracle_arm64.yml build --no-cache
docker-compose -f docker-compose.oracle_arm64.yml up -d

# 7. Esperar a que los servicios estén listos
info "⏳ Esperando a que los servicios estén listos..."
sleep 30

# 8. Verificar estado
info "📊 Estado de los servicios:"
docker-compose -f docker-compose.oracle_arm64.yml ps

# 9. Verificar logs de Rasa
info "📋 Logs de Rasa:"
docker-compose -f docker-compose.oracle_arm64.yml logs rasa --tail=20

# 10. Probar Rasa
info "🧪 Probando Rasa..."
sleep 10
if curl -f http://localhost:5005/webhooks/rest/webhook -X POST -H "Content-Type: application/json" -d '{"sender": "test", "message": "hola"}' > /dev/null 2>&1; then
    success "Rasa respondiendo correctamente"
else
    warning "Rasa no responde aún, revisa los logs"
fi

success "🎉 Despliegue completado con modelo de Rasa entrenado"
