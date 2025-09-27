#!/bin/bash

# Script de limpieza automática para Oracle Cloud
# Se ejecuta cada 12 horas para mantener espacio en disco

LOG_FILE="/var/log/cleanup_script.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 🧹 Iniciando limpieza automática..." >> $LOG_FILE

# Función para registrar con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# 1. Limpiar Docker
log "🐳 Limpiando Docker..."
docker system prune -af --volumes >> $LOG_FILE 2>&1

# 2. Limpiar paquetes
log "📦 Limpiando paquetes..."
apt-get autoremove -y >> $LOG_FILE 2>&1
apt-get autoclean >> $LOG_FILE 2>&1

# 3. Limpiar logs del sistema
log "📋 Limpiando logs del sistema..."
journalctl --vacuum-time=7d >> $LOG_FILE 2>&1

# 4. Limpiar archivos temporales
log "🗂️ Limpiando archivos temporales..."
find /tmp -type f -atime +7 -delete 2>/dev/null || true

# 5. Truncar logs grandes
log "📄 Truncando logs grandes..."
find /var/log -name "*.log" -type f -size +100M -exec truncate -s 50M {} \; 2>/dev/null || true

# 6. Limpiar archivos de sesión antiguos (si existen)
log "🗃️ Limpiando sesiones antiguas..."
find /tmp -name "session_*" -type d -mtime +1 -exec rm -rf {} \; 2>/dev/null || true
find /tmp -name "basico_*" -type f -mtime +1 -delete 2>/dev/null || true

# 7. Verificar espacio disponible
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
log "💾 Uso de disco después de limpieza: ${DISK_USAGE}%"

# 8. Reiniciar servicios si el uso es alto
if [ $DISK_USAGE -gt 85 ]; then
    log "⚠️ Uso de disco alto (${DISK_USAGE}%), reiniciando servicios..."
    cd /home/ubuntu/arquitectura
    docker-compose -f docker-compose.basico.yml restart >> $LOG_FILE 2>&1
    log "🔄 Servicios reiniciados"
fi

log "✅ Limpieza completada. Uso de disco: ${DISK_USAGE}%"

# Mantener solo las últimas 100 líneas del log
tail -n 100 $LOG_FILE > ${LOG_FILE}.tmp && mv ${LOG_FILE}.tmp $LOG_FILE

echo "[$DATE] ✅ Limpieza automática completada. Uso de disco: ${DISK_USAGE}%" >> $LOG_FILE
