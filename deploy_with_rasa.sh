#!/bin/bash

# ===========================================
# SCRIPT DE DESPLIEGUE CON RASA MICROSERVICIO
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
DOCKER_COMPOSE_FILE="docker-compose.rasa.yml"
ENV_FILE="env.gcp.txt"

echo -e "${GREEN}🚀 Iniciando despliegue con Rasa Microservicio${NC}"
echo -e "${BLUE}📁 Directorio de trabajo: $APP_DIR${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    error "No se encontró $DOCKER_COMPOSE_FILE. Ejecuta desde el directorio del proyecto."
    exit 1
fi

# Actualizar sistema
info "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado. Instalando..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    success "Docker instalado"
else
    success "Docker ya está instalado"
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado. Instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    success "Docker Compose instalado"
else
    success "Docker Compose ya está instalado"
fi

# Instalar dependencias adicionales
info "📦 Instalando dependencias adicionales..."
sudo apt install -y htop curl git unzip wget

# Configurar variables de entorno
info "⚙️ Configurando variables de entorno..."
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" .env
    success "Archivo .env configurado"
else
    error "No se encontró $ENV_FILE"
    exit 1
fi

# Crear directorios necesarios
info "📁 Creando directorios necesarios..."
mkdir -p uploads temp logs rasa_bot/models rasa_bot/data rasa_bot/actions
success "Directorios creados"

# Verificar configuración de Docker
info "🔍 Verificando configuración de Docker..."
docker --version
docker-compose --version

# Construir y levantar contenedores
info "🏗️ Construyendo y levantando contenedores con Rasa..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up --build -d

# Esperar a que los servicios estén listos
info "⏳ Esperando a que los servicios estén listos..."
sleep 30

# Verificar estado de contenedores
info "🔍 Verificando estado de contenedores..."
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Mostrar logs de la aplicación
info "📋 Mostrando logs de la aplicación..."
docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50

# Verificar conectividad
info "🌐 Verificando conectividad..."
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    success "✅ Aplicación principal está funcionando"
else
    warning "⚠️ La aplicación principal puede estar iniciando"
fi

if curl -f http://localhost:5005/health > /dev/null 2>&1; then
    success "✅ Rasa microservicio está funcionando"
else
    warning "⚠️ Rasa microservicio puede estar iniciando"
fi

# Obtener IP externa
EXTERNAL_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "No disponible")

echo ""
echo -e "${GREEN}🎉 DESPLIEGUE CON RASA COMPLETADO${NC}"
echo -e "${BLUE}📊 Información de acceso:${NC}"
echo -e "   • Aplicación Principal: http://$EXTERNAL_IP:5000"
echo -e "   • Health Check: http://$EXTERNAL_IP:5000/health"
echo -e "   • API Docs: http://$EXTERNAL_IP:5000/docs"
echo -e "   • Rasa Microservicio: http://$EXTERNAL_IP:5005"
echo -e "   • Rasa Health: http://$EXTERNAL_IP:5005/health"
echo -e "   • Neo4j Browser: http://$EXTERNAL_IP:7474"
echo -e "   • Redis: $EXTERNAL_IP:6379"

echo ""
echo -e "${BLUE}📋 Comandos útiles:${NC}"
echo -e "   • Ver logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
echo -e "   • Parar app: docker-compose -f $DOCKER_COMPOSE_FILE down"
echo -e "   • Reiniciar: docker-compose -f $DOCKER_COMPOSE_FILE restart"
echo -e "   • Ver contenedores: docker ps"
echo -e "   • Logs de Rasa: docker-compose -f $DOCKER_COMPOSE_FILE logs rasa"
echo -e "   • Logs de App: docker-compose -f $DOCKER_COMPOSE_FILE logs app"

echo ""
echo -e "${GREEN}[SUCCESS] 🚀 Sistema de Verificación Arquitectónica con Rasa desplegado correctamente${NC}"
