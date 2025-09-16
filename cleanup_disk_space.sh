#!/bin/bash

# Script para limpiar espacio en disco en Oracle Cloud ARM64

echo "🧹 Limpiando espacio en disco..."

# Limpiar cache de Docker
echo "Limpiando cache de Docker..."
docker system prune -af
docker volume prune -f

# Limpiar cache de pip
echo "Limpiando cache de pip..."
pip cache purge 2>/dev/null || true

# Limpiar logs del sistema
echo "Limpiando logs del sistema..."
sudo journalctl --vacuum-time=1d 2>/dev/null || true

# Limpiar archivos temporales
echo "Limpiando archivos temporales..."
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# Limpiar cache de apt
echo "Limpiando cache de apt..."
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y

# Mostrar espacio disponible
echo "📊 Espacio disponible después de la limpieza:"
df -h

echo "✅ Limpieza completada"
