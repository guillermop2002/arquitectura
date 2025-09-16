# ☁️ GUÍA DE DESPLIEGUE A GOOGLE CLOUD PLATFORM

## **📋 INFORMACIÓN GENERAL**
- **Plataforma**: Google Cloud Platform (GCP)
- **Créditos**: $300 USD por 90 días
- **Arquitectura**: x86_64 (compatible con tu proyecto actual)
- **Servicios**: Compute Engine, Cloud SQL, Cloud Storage

---

## **🎯 PASOS DE DESPLIEGUE**

### **PASO 1: CONFIGURAR CUENTA DE GOOGLE CLOUD**

#### **1.1 Crear Cuenta y Proyecto**
1. **Ir a**: https://console.cloud.google.com/
2. **Crear cuenta** con tu email de Google
3. **Activar créditos** de $300 USD
4. **Crear proyecto nuevo**:
   - Nombre: `verificacion-arquitectonica`
   - ID: `verificacion-arquitectonica`
   - Región: `us-central1` (Iowa)

#### **1.2 Habilitar APIs Necesarias**
```bash
# APIs requeridas
- Compute Engine API
- Cloud SQL API
- Cloud Storage API
- Cloud Build API
- Container Registry API
```

### **PASO 2: CONFIGURAR COMPUTE ENGINE**

#### **2.1 Crear Instancia de VM**
```bash
# Especificaciones recomendadas
- Tipo de máquina: e2-standard-4
- vCPUs: 4
- RAM: 16 GB
- Disco: 100 GB SSD
- SO: Ubuntu 22.04 LTS
- Región: us-central1-a
```

#### **2.2 Configurar Firewall**
```bash
# Reglas de firewall necesarias
- Puerto 22 (SSH): 0.0.0.0/0
- Puerto 80 (HTTP): 0.0.0.0/0
- Puerto 443 (HTTPS): 0.0.0.0/0
- Puerto 5000 (FastAPI): 0.0.0.0/0
- Puerto 6379 (Redis): 0.0.0.0/0
- Puerto 7474 (Neo4j): 0.0.0.0/0
```

### **PASO 3: CONFIGURAR BASE DE DATOS**

#### **3.1 Cloud SQL (PostgreSQL)**
```bash
# Configuración de Cloud SQL
- Tipo: PostgreSQL 15
- Región: us-central1
- Zona: us-central1-a
- Tipo de máquina: db-f1-micro (gratis)
- Almacenamiento: 10 GB SSD
- Red: default
```

#### **3.2 Neo4j Aura (Mantener actual)**
```bash
# Usar la instancia actual de Neo4j
- URI: neo4j+s://a8c7ced7.databases.neo4j.io
- Usuario: a8c7ced7
- Contraseña: pEl2sdgHeG2amSo_bijeJDm9L7tdZMSuzom-4nHmx40
- Base de datos: a8c7ced7
```

### **PASO 4: CONFIGURAR ALMACENAMIENTO**

#### **4.1 Cloud Storage**
```bash
# Crear bucket para archivos
- Nombre: verificacion-arquitectonica-files
- Región: us-central1
- Clase de almacenamiento: Standard
- Acceso: Uniform
```

---

## **🚀 DESPLIEGUE AUTOMATIZADO**

### **PASO 5: CREAR SCRIPT DE DESPLIEGUE**

#### **5.1 Script de Configuración Inicial**
```bash
#!/bin/bash
# setup_gcp.sh

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv git curl wget unzip

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Instalar Google Cloud SDK
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt update && sudo apt install -y google-cloud-cli

# Configurar zona horaria
sudo timedatectl set-timezone Europe/Madrid

echo "✅ Configuración inicial completada"
```

#### **5.2 Script de Despliegue de la Aplicación**
```bash
#!/bin/bash
# deploy_app.sh

# Crear directorio del proyecto
mkdir -p /opt/verificacion-app
cd /opt/verificacion-app

# Clonar o copiar código del proyecto
# (Aquí copiarías todos los archivos del proyecto)

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cat > .env << EOF
# Google Cloud Configuration
GCP_PROJECT_ID=verificacion-arquitectonica
GCP_REGION=us-central1
GCP_ZONE=us-central1-a

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/verificacion_db

# Neo4j Configuration
NEO4J_URI=neo4j+s://a8c7ced7.databases.neo4j.io
NEO4J_USERNAME=a8c7ced7
NEO4J_PASSWORD=pEl2sdgHeG2amSo_bijeJDm9L7tdZMSuzom-4nHmx40
NEO4J_DATABASE=a8c7ced7

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
GROQ_API_KEY=gsk_bAHQ8OKiwJ2pgvKPwKq6WGdyb3FYQp3p5AjuufYBorWN4Z2PTFm

# Application Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=False
ENVIRONMENT=production

# File Configuration
MAX_FILE_SIZE=104857600
MAX_FILES=20
UPLOAD_FOLDER=uploads
TEMP_FOLDER=temp

# Security
SECRET_KEY=gcp_production_secret_key_very_long_and_secure_change_in_production
SESSION_TIMEOUT=3600
EOF

# Crear directorios necesarios
mkdir -p uploads temp logs cache

# Configurar permisos
chmod +x *.sh
chown -R $USER:$USER /opt/verificacion-app

echo "✅ Aplicación desplegada"
```

#### **5.3 Script de Inicio del Servicio**
```bash
#!/bin/bash
# start_service.sh

cd /opt/verificacion-app

# Activar entorno virtual
source venv/bin/activate

# Iniciar Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Iniciar aplicación
python main.py

echo "✅ Servicio iniciado"
```

---

## **🐳 DESPLIEGUE CON DOCKER**

### **PASO 6: CREAR DOCKERFILE PARA GCP**

#### **6.1 Dockerfile.gcp**
```dockerfile
# Dockerfile.gcp
FROM python:3.10-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p uploads temp logs cache

# Configurar permisos
RUN chmod +x *.sh

# Exponer puerto
EXPOSE 5000

# Comando de inicio
CMD ["python", "main.py"]
```

#### **6.2 docker-compose.gcp.yml**
```yaml
# docker-compose.gcp.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.gcp
    ports:
      - "5000:5000"
    environment:
      - HOST=0.0.0.0
      - PORT=5000
      - DATABASE_URL=postgresql://postgres:password@db:5432/verificacion_db
      - REDIS_URL=redis://redis:6379
      - NEO4J_URI=neo4j+s://a8c7ced7.databases.neo4j.io
      - NEO4J_USERNAME=a8c7ced7
      - NEO4J_PASSWORD=pEl2sdgHeG2amSo_bijeJDm9L7tdZMSuzom-4nHmx40
      - GROQ_API_KEY=gsk_bAHQ8OKiwJ2pgvKPwKq6WGdyb3FYQp3p5AjuufYBorWN4Z2PTFm
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./temp:/app/temp
      - ./cache:/app/cache
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=verificacion_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## **🔧 CONFIGURACIÓN DE NGINX**

### **PASO 7: CONFIGURAR NGINX PARA GCP**

#### **7.1 nginx.gcp.conf**
```nginx
# nginx.gcp.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # Upstream
    upstream app {
        server app:5000;
    }

    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # File upload size
        client_max_body_size 100M;

        # API endpoints
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Static files
        location /static/ {
            alias /app/frontend/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            proxy_pass http://app;
            access_log off;
        }
    }
}
```

---

## **📋 CHECKLIST DE DESPLIEGUE**

### **PASO 8: VERIFICACIÓN COMPLETA**

#### **8.1 Checklist Pre-Despliegue**
- [ ] Cuenta de Google Cloud creada
- [ ] Créditos de $300 activados
- [ ] Proyecto GCP creado
- [ ] APIs habilitadas
- [ ] Instancia VM creada
- [ ] Firewall configurado
- [ ] Cloud SQL configurado
- [ ] Cloud Storage configurado

#### **8.2 Checklist Post-Despliegue**
- [ ] Aplicación accesible en http://IP_EXTERNA
- [ ] Base de datos conectada
- [ ] Redis funcionando
- [ ] Neo4j conectado
- [ ] Archivos subiendo correctamente
- [ ] Logs generándose
- [ ] Monitoreo funcionando

---

## **💰 ESTIMACIÓN DE COSTOS**

### **Costos Mensuales Estimados**
```
Compute Engine (e2-standard-4):
- vCPU: 4 × $0.067 = $0.268/hora
- RAM: 16GB × $0.009 = $0.144/hora
- Total: $0.412/hora × 24 × 30 = $296.64/mes

Cloud SQL (db-f1-micro):
- vCPU: 1 × $0.017 = $0.017/hora
- RAM: 0.6GB × $0.002 = $0.001/hora
- Almacenamiento: 10GB × $0.17 = $1.70/mes
- Total: ~$13/mes

Cloud Storage:
- 100GB × $0.020 = $2/mes

Total estimado: ~$312/mes
```

### **Con Créditos de $300**
- **Duración estimada**: ~28 días
- **Costo real**: $0 (cubierto por créditos)

---

## **🚀 COMANDOS DE DESPLIEGUE RÁPIDO**

### **PASO 9: DESPLIEGUE AUTOMATIZADO**

#### **9.1 Comandos en GCP Console**
```bash
# 1. Crear instancia VM
gcloud compute instances create verificacion-app \
    --zone=us-central1-a \
    --machine-type=e2-standard-4 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=100GB \
    --boot-disk-type=pd-ssd \
    --tags=http-server,https-server

# 2. Configurar firewall
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags https-server

gcloud compute firewall-rules create allow-app \
    --allow tcp:5000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server

# 3. Conectar a la instancia
gcloud compute ssh verificacion-app --zone=us-central1-a
```

#### **9.2 Comandos en la VM**
```bash
# 1. Ejecutar configuración inicial
curl -sSL https://raw.githubusercontent.com/tu-repo/setup_gcp.sh | bash

# 2. Clonar proyecto
git clone https://github.com/tu-usuario/verificacion-app.git
cd verificacion-app

# 3. Ejecutar despliegue
chmod +x deploy_app.sh
./deploy_app.sh

# 4. Iniciar servicio
chmod +x start_service.sh
./start_service.sh
```

---

## **📊 MONITOREO Y MANTENIMIENTO**

### **PASO 10: CONFIGURAR MONITOREO**

#### **10.1 Cloud Monitoring**
```bash
# Habilitar Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Configurar alertas
- CPU > 80% por 5 minutos
- Memoria > 90% por 5 minutos
- Disco > 85% por 5 minutos
- Aplicación no responde por 2 minutos
```

#### **10.2 Logs de Aplicación**
```bash
# Ver logs en tiempo real
tail -f /opt/verificacion-app/logs/app.log

# Ver logs de Docker
docker-compose -f docker-compose.gcp.yml logs -f
```

---

## **🔒 SEGURIDAD**

### **PASO 11: CONFIGURAR SEGURIDAD**

#### **11.1 Configuración de Seguridad**
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Configurar UFW
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 5000

# Configurar fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

#### **11.2 Certificados SSL**
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com
```

---

## **📞 SOPORTE Y TROUBLESHOOTING**

### **Problemas Comunes**

#### **1. Aplicación no inicia**
```bash
# Verificar logs
journalctl -u verificacion-app -f

# Verificar puertos
netstat -tlnp | grep :5000
```

#### **2. Base de datos no conecta**
```bash
# Verificar Cloud SQL
gcloud sql instances list
gcloud sql connect verificacion-db --user=postgres
```

#### **3. Archivos no se suben**
```bash
# Verificar permisos
ls -la /opt/verificacion-app/uploads/
sudo chown -R $USER:$USER /opt/verificacion-app/uploads/
```

---

## **🎉 CONCLUSIÓN**

### **✅ VENTAJAS DE GOOGLE CLOUD**
- **Créditos gratuitos**: $300 por 90 días
- **Compatibilidad**: x86_64 (sin cambios en código)
- **Servicios integrados**: Cloud SQL, Storage, Monitoring
- **Escalabilidad**: Fácil escalado vertical y horizontal
- **Soporte**: Documentación y comunidad extensa

### **📊 ESTADO DEL DESPLIEGUE**
- **Código**: Sin modificaciones necesarias
- **Configuración**: Adaptada para GCP
- **Servicios**: Cloud SQL + Neo4j Aura + Redis
- **Monitoreo**: Cloud Monitoring integrado
- **Seguridad**: Firewall y SSL configurados

**El proyecto está listo para desplegarse en Google Cloud Platform manteniendo toda la funcionalidad actual.**
