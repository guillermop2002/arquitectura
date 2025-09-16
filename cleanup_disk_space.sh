#!/bin/bash

# Script para limpiar espacio en disco en Oracle Cloud ARM64

echo "🧹 Limpiando espacio en disco..."

# Mostrar espacio antes de la limpieza
echo "📊 Espacio disponible ANTES de la limpieza:"
df -h

# Limpiar cache de Docker (más agresivo)
echo "Limpiando cache de Docker..."
docker system prune -af --volumes
docker volume prune -f
docker image prune -af
docker container prune -f
docker network prune -f

# Limpiar cache de pip
echo "Limpiando cache de pip..."
pip cache purge 2>/dev/null || true
rm -rf ~/.cache/pip 2>/dev/null || true

# Limpiar logs del sistema
echo "Limpiando logs del sistema..."
sudo journalctl --vacuum-time=1d 2>/dev/null || true
sudo find /var/log -type f -name "*.log" -exec truncate -s 0 {} \; 2>/dev/null || true

# Limpiar archivos temporales
echo "Limpiando archivos temporales..."
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*
sudo rm -rf /var/cache/apt/archives/*

# Limpiar cache de apt
echo "Limpiando cache de apt..."
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y
sudo apt-get autopurge -y

# Limpiar archivos de swap
echo "Limpiando archivos de swap..."
sudo swapoff -a 2>/dev/null || true
sudo swapon -a 2>/dev/null || true

# Limpiar archivos core dumps
echo "Limpiando core dumps..."
sudo find / -name "core.*" -type f -delete 2>/dev/null || true

# Mostrar espacio disponible después de la limpieza
echo "📊 Espacio disponible DESPUÉS de la limpieza:"
df -h

echo "✅ Limpieza completada"
