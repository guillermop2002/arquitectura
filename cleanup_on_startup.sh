#!/bin/bash
# Script de limpieza automática al iniciar Docker
# Se ejecuta cada vez que se inicia el contenedor

echo "🧹 Iniciando limpieza automática del sistema..."

# Limpiar archivos temporales del sistema
echo "📁 Limpiando archivos temporales..."
find /tmp -type f -mtime +0 -delete 2>/dev/null || true
find /var/tmp -type f -mtime +0 -delete 2>/dev/null || true

# Limpiar logs antiguos del sistema
echo "📝 Limpiando logs del sistema..."
find /var/log -name "*.log" -type f -mtime +1 -delete 2>/dev/null || true
find /var/log -name "*.log.*" -type f -mtime +1 -delete 2>/dev/null || true

# Limpiar directorios de la aplicación
echo "🗂️ Limpiando directorios de la aplicación..."
rm -rf /app/uploads/session_* 2>/dev/null || true
rm -rf /app/temp/* 2>/dev/null || true
rm -rf /app/analysis_results/* 2>/dev/null || true
find /app/logs -name "*.log" -type f -mtime +0 -delete 2>/dev/null || true
find /app/logs -name "session_*.json" -type f -mtime +0 -delete 2>/dev/null || true

# Limpiar cache de Python
echo "🐍 Limpiando cache de Python..."
find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /app -name "*.pyc" -type f -delete 2>/dev/null || true
find /app -name "*.pyo" -type f -delete 2>/dev/null || true

# Limpiar cache de pip
echo "📦 Limpiando cache de pip..."
pip cache purge 2>/dev/null || true

# Limpiar espacio en disco si es crítico
echo "💾 Verificando espacio en disco..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "⚠️ Uso de disco crítico: ${DISK_USAGE}%"
    echo "🧹 Ejecutando limpieza forzada..."
    
    # Limpiar más agresivamente
    find /app -name "*.tmp" -type f -delete 2>/dev/null || true
    find /app -name "*.temp" -type f -delete 2>/dev/null || true
    find /app -name "*.bak" -type f -delete 2>/dev/null || true
    
    # Limpiar directorios vacíos
    find /app -type d -empty -delete 2>/dev/null || true
    
    echo "✅ Limpieza forzada completada"
else
    echo "✅ Uso de disco normal: ${DISK_USAGE}%"
fi

# Mostrar espacio liberado
echo "📊 Estado final del disco:"
df -h / | head -2

echo "🎉 Limpieza automática completada"
