#!/bin/bash
# Script para configurar monitoreo automático de espacio en disco

echo "⏰ Configurando monitoreo automático de espacio en disco..."

# Hacer ejecutable el script de monitoreo
chmod +x monitor_disk_space.sh

# Crear entrada de cron para monitoreo cada 5 minutos
echo "*/5 * * * * /app/monitor_disk_space.sh >> /var/log/disk_monitor.log 2>&1" | crontab -

# Crear entrada de cron para limpieza diaria a las 2 AM
echo "0 2 * * * /usr/local/bin/cleanup_on_startup.sh >> /var/log/daily_cleanup.log 2>&1" | crontab -

# Crear entrada de cron para limpieza de Docker semanal (domingos a las 3 AM)
echo "0 3 * * 0 /app/docker_cleanup.sh >> /var/log/docker_cleanup.log 2>&1" | crontab -

# Verificar que cron esté funcionando
systemctl enable cron
systemctl start cron

echo "✅ Monitoreo automático configurado:"
echo "  • Verificación de disco cada 5 minutos"
echo "  • Limpieza diaria a las 2:00 AM"
echo "  • Limpieza de Docker semanal (domingos 3:00 AM)"
echo "  • Logs en /var/log/disk_monitor.log"
echo "  • Logs en /var/log/daily_cleanup.log"
echo "  • Logs en /var/log/docker_cleanup.log"
