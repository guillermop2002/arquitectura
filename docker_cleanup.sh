#!/bin/bash
# Script de limpieza automática de Docker
# Se ejecuta antes de cada rebuild para liberar espacio

echo "🐳 Iniciando limpieza de Docker..."

# Detener contenedores si están corriendo
echo "⏹️ Deteniendo contenedores..."
docker-compose -f docker-compose.oracle_arm64.yml down 2>/dev/null || true

# Limpiar contenedores parados
echo "🗑️ Limpiando contenedores parados..."
docker container prune -f 2>/dev/null || true

# Limpiar imágenes no utilizadas
echo "🖼️ Limpiando imágenes no utilizadas..."
docker image prune -a -f 2>/dev/null || true

# Limpiar volúmenes no utilizados
echo "💾 Limpiando volúmenes no utilizados..."
docker volume prune -f 2>/dev/null || true

# Limpiar redes no utilizadas
echo "🌐 Limpiando redes no utilizadas..."
docker network prune -f 2>/dev/null || true

# Limpiar cache de build
echo "🔨 Limpiando cache de build..."
docker builder prune -a -f 2>/dev/null || true

# Limpiar sistema completo
echo "🧹 Limpieza completa del sistema Docker..."
docker system prune -a -f --volumes 2>/dev/null || true

# Mostrar espacio liberado
echo "📊 Estado del sistema Docker:"
docker system df

echo "✅ Limpieza de Docker completada"
