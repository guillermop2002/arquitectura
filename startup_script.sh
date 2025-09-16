#!/bin/bash
# startup_script.sh
# Script de inicio automático para la VM de Google Cloud

# Logging
exec > >(tee -a /var/log/startup-script.log)
exec 2>&1

echo "🚀 Iniciando script de configuración de la VM"
echo "Fecha: $(date)"

# Actualizar sistema
echo "📦 Actualizando sistema..."
apt-get update
apt-get upgrade -y

# Instalar dependencias básicas
echo "🔧 Instalando dependencias básicas..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    htop \
    vim \
    nano \
    tree \
    jq

# Instalar Docker
echo "🐳 Instalando Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Agregar usuario al grupo docker
usermod -aG docker $USER

# Instalar Docker Compose
echo "🐙 Instalando Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Instalar Google Cloud SDK
echo "☁️ Instalando Google Cloud SDK..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
apt-get update
apt-get install -y google-cloud-cli

# Configurar zona horaria
echo "🕐 Configurando zona horaria..."
timedatectl set-timezone Europe/Madrid

# Instalar dependencias para OCR y procesamiento de imágenes
echo "👁️ Instalando dependencias para OCR..."
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    libpoppler-cpp-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p /opt/verificacion-app
mkdir -p /var/log/verificacion-app
mkdir -p /opt/backups

# Configurar permisos
chown -R $USER:$USER /opt/verificacion-app
chown -R $USER:$USER /var/log/verificacion-app

# Crear script de monitoreo
echo "📊 Creando script de monitoreo..."
cat > /opt/verificacion-app/monitor.sh << 'EOF'
#!/bin/bash
# Script de monitoreo básico

LOG_FILE="/var/log/verificacion-app/monitor.log"
APP_DIR="/opt/verificacion-app"

echo "$(date): Iniciando monitoreo" >> $LOG_FILE

# Verificar Docker
if ! docker info > /dev/null 2>&1; then
    echo "$(date): ERROR - Docker no está funcionando" >> $LOG_FILE
    systemctl restart docker
fi

# Verificar aplicación
if [ -f "$APP_DIR/docker-compose.gcp.yml" ]; then
    cd $APP_DIR
    if ! docker-compose -f docker-compose.gcp.yml ps | grep -q "Up"; then
        echo "$(date): ERROR - Aplicación no está funcionando, reiniciando..." >> $LOG_FILE
        docker-compose -f docker-compose.gcp.yml up -d
    fi
fi

# Verificar espacio en disco
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): WARNING - Uso de disco alto: ${DISK_USAGE}%" >> $LOG_FILE
fi

# Verificar memoria
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "$(date): WARNING - Uso de memoria alto: ${MEMORY_USAGE}%" >> $LOG_FILE
fi

echo "$(date): Monitoreo completado" >> $LOG_FILE
EOF

chmod +x /opt/verificacion-app/monitor.sh

# Configurar cron para monitoreo
echo "⏰ Configurando cron para monitoreo..."
echo "*/5 * * * * /opt/verificacion-app/monitor.sh" | crontab -u $USER -

# Crear script de limpieza automática
echo "🧹 Creando script de limpieza automática..."
cat > /opt/verificacion-app/cleanup.sh << 'EOF'
#!/bin/bash
# Script de limpieza automática

LOG_FILE="/var/log/verificacion-app/cleanup.log"
APP_DIR="/opt/verificacion-app"

echo "$(date): Iniciando limpieza automática" >> $LOG_FILE

# Limpiar logs antiguos (más de 7 días)
find /var/log -name "*.log" -mtime +7 -delete 2>/dev/null

# Limpiar archivos temporales
find /tmp -type f -mtime +1 -delete 2>/dev/null

# Limpiar cache de Docker
docker system prune -f 2>/dev/null

# Limpiar archivos de la aplicación (si existen)
if [ -d "$APP_DIR/temp" ]; then
    find $APP_DIR/temp -type f -mtime +1 -delete 2>/dev/null
fi

if [ -d "$APP_DIR/cache" ]; then
    find $APP_DIR/cache -type f -mtime +3 -delete 2>/dev/null
fi

echo "$(date): Limpieza automática completada" >> $LOG_FILE
EOF

chmod +x /opt/verificacion-app/cleanup.sh

# Configurar cron para limpieza
echo "⏰ Configurando cron para limpieza..."
echo "0 2 * * * /opt/verificacion-app/cleanup.sh" | crontab -u $USER -

# Crear script de backup
echo "💾 Creando script de backup..."
cat > /opt/verificacion-app/backup.sh << 'EOF'
#!/bin/bash
# Script de backup

BACKUP_DIR="/opt/backups"
APP_DIR="/opt/verificacion-app"
DATE=$(date +%Y%m%d_%H%M%S)

echo "$(date): Iniciando backup" >> /var/log/verificacion-app/backup.log

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de la aplicación
if [ -d "$APP_DIR" ]; then
    tar -czf $BACKUP_DIR/verificacion-app_$DATE.tar.gz -C /opt verificacion-app
    echo "$(date): Backup de aplicación creado: verificacion-app_$DATE.tar.gz" >> /var/log/verificacion-app/backup.log
fi

# Backup de la base de datos (si existe)
if docker ps | grep -q postgres; then
    docker exec $(docker ps | grep postgres | awk '{print $1}') pg_dump -U postgres verificacion_db > $BACKUP_DIR/database_$DATE.sql
    echo "$(date): Backup de base de datos creado: database_$DATE.sql" >> /var/log/verificacion-app/backup.log
fi

# Limpiar backups antiguos (más de 7 días)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete 2>/dev/null
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete 2>/dev/null

echo "$(date): Backup completado" >> /var/log/verificacion-app/backup.log
EOF

chmod +x /opt/verificacion-app/backup.sh

# Configurar cron para backup
echo "⏰ Configurando cron para backup..."
echo "0 3 * * * /opt/verificacion-app/backup.sh" | crontab -u $USER -

# Configurar UFW (firewall básico)
echo "🔥 Configurando firewall básico..."
ufw --force enable
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 5000

# Instalar fail2ban
echo "🛡️ Instalando fail2ban..."
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Crear usuario para la aplicación
echo "👤 Configurando usuario de aplicación..."
useradd -m -s /bin/bash verificacion 2>/dev/null || true
usermod -aG docker verificacion

# Configurar logrotate
echo "📝 Configurando logrotate..."
cat > /etc/logrotate.d/verificacion-app << 'EOF'
/var/log/verificacion-app/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 verificacion verificacion
}
EOF

# Crear script de inicio de la aplicación
echo "🚀 Creando script de inicio de la aplicación..."
cat > /opt/verificacion-app/start.sh << 'EOF'
#!/bin/bash
# Script de inicio de la aplicación

APP_DIR="/opt/verificacion-app"
LOG_FILE="/var/log/verificacion-app/app.log"

cd $APP_DIR

echo "$(date): Iniciando aplicación" >> $LOG_FILE

# Verificar que Docker esté funcionando
if ! docker info > /dev/null 2>&1; then
    echo "$(date): ERROR - Docker no está funcionando" >> $LOG_FILE
    systemctl restart docker
    sleep 10
fi

# Iniciar aplicación con Docker Compose
if [ -f "docker-compose.gcp.yml" ]; then
    echo "$(date): Iniciando con Docker Compose" >> $LOG_FILE
    docker-compose -f docker-compose.gcp.yml up -d
else
    echo "$(date): Iniciando directamente con Python" >> $LOG_FILE
    # Activar entorno virtual si existe
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Instalar dependencias si es necesario
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    # Iniciar aplicación
    nohup python main.py >> $LOG_FILE 2>&1 &
fi

echo "$(date): Aplicación iniciada" >> $LOG_FILE
EOF

chmod +x /opt/verificacion-app/start.sh

# Configurar servicio systemd
echo "⚙️ Configurando servicio systemd..."
cat > /etc/systemd/system/verificacion-app.service << 'EOF'
[Unit]
Description=Verificacion Arquitectonica App
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/verificacion-app/start.sh
ExecStop=/bin/bash -c "cd /opt/verificacion-app && docker-compose -f docker-compose.gcp.yml down"
User=verificacion
Group=verificacion
WorkingDirectory=/opt/verificacion-app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable verificacion-app.service

# Limpiar paquetes innecesarios
echo "🧹 Limpiando paquetes innecesarios..."
apt-get autoremove -y
apt-get autoclean

# Mostrar información del sistema
echo "📊 Información del sistema:"
echo "Memoria: $(free -h | awk 'NR==2{print $2}')"
echo "Disco: $(df -h / | awk 'NR==2{print $2}')"
echo "CPU: $(nproc) cores"

echo "✅ Script de configuración completado"
echo "Fecha de finalización: $(date)"

# Iniciar la aplicación
echo "🚀 Iniciando aplicación..."
systemctl start verificacion-app.service

echo "🎉 Configuración de la VM completada!"
echo "La aplicación debería estar disponible en unos minutos."
