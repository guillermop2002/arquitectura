#!/bin/bash

# Script para reparar dependencias corruptas en Oracle Cloud ARM64

echo "🔧 Reparando dependencias corruptas..."

# Parar todos los contenedores
echo "Parando contenedores..."
docker-compose -f docker-compose.oracle_arm64.yml down

# Limpiar imágenes Docker existentes
echo "Limpiando imágenes Docker..."
docker rmi arquitectura-app arquitectura-rasa 2>/dev/null || true
docker system prune -f

# Limpiar cache de pip
echo "Limpiando cache de pip..."
pip cache purge 2>/dev/null || true

# Reconstruir desde cero
echo "Reconstruyendo imágenes desde cero..."
docker-compose -f docker-compose.oracle_arm64.yml build --no-cache --pull

echo "✅ Reparación completada"
