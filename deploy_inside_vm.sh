#!/bin/bash

# ===========================================
# SCRIPT DE DESPLIEGUE DENTRO DE VM GCP
# Sistema de Verificación Arquitectónica
# ===========================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de logging
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuración
APP_DIR="/opt/verification-app"
DOCKER_COMPOSE_FILE="docker-compose.gcp.yml"
ENV_FILE="env.gcp.txt"

echo -e "${GREEN}🚀 Iniciando despliegue dentro de VM GCP${NC}"
echo -e "${BLUE}📁 Directorio de trabajo: $APP_DIR${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    error "No se encontró $DOCKER_COMPOSE_FILE en el directorio actual"
    error "Asegúrate de estar en el directorio correcto: $APP_DIR"
    exit 1
fi

# 1. Actualizar sistema
info "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar Docker si no está instalado
if ! command -v docker &> /dev/null; then
    info "🐳 Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    success "Docker instalado correctamente"
else
    success "Docker ya está instalado"
fi

# 3. Instalar Docker Compose si no está instalado
if ! command -v docker-compose &> /dev/null; then
    info "🐳 Instalando Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    success "Docker Compose instalado correctamente"
else
    success "Docker Compose ya está instalado"
fi

# 4. Instalar dependencias adicionales
info "📦 Instalando dependencias adicionales..."
sudo apt install -y git curl wget unzip htop

# 5. Configurar archivo de entorno
info "⚙️ Configurando variables de entorno..."
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" .env
    success "Archivo .env configurado"
else
    error "No se encontró $ENV_FILE"
    exit 1
fi

# 6. Crear directorios necesarios
info "📁 Creando directorios necesarios..."
mkdir -p uploads temp logs
sudo chown -R $USER:$USER uploads temp logs
success "Directorios creados"

# 7. Verificar configuración de Docker
info "🔍 Verificando configuración de Docker..."
docker --version
docker-compose --version

# 8. Construir y levantar contenedores
info "🏗️ Construyendo y levantando contenedores..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

# 9. Verificar que los contenedores estén corriendo
info "🔍 Verificando estado de contenedores..."
sleep 10
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# 10. Mostrar logs
info "📋 Mostrando logs de la aplicación..."
docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50

# 11. Verificar conectividad
info "🌐 Verificando conectividad..."
sleep 5
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    success "✅ Aplicación funcionando correctamente en http://localhost:5000"
else
    warning "⚠️ La aplicación puede estar iniciando, verifica los logs"
fi

# 12. Mostrar información de acceso
echo ""
echo -e "${GREEN}🎉 DESPLIEGUE COMPLETADO${NC}"
echo -e "${BLUE}📊 Información de acceso:${NC}"
echo -e "   • Aplicación: http://$(curl -s ifconfig.me):5000"
echo -e "   • Health Check: http://$(curl -s ifconfig.me):5000/health"
echo -e "   • API Docs: http://$(curl -s ifconfig.me):5000/docs"
echo ""
echo -e "${YELLOW}📋 Comandos útiles:${NC}"
echo -e "   • Ver logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
echo -e "   • Parar app: docker-compose -f $DOCKER_COMPOSE_FILE down"
echo -e "   • Reiniciar: docker-compose -f $DOCKER_COMPOSE_FILE restart"
echo -e "   • Ver contenedores: docker ps"
echo ""

success "🚀 Sistema de Verificación Arquitectónica desplegado correctamente"
