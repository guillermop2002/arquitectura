#!/bin/bash

# Script de despliegue simplificado para Oracle Cloud ARM64
# Sistema de Verificación Arquitectónica

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funciones de logging
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verificar dependencias
check_dependencies() {
    info "Verificando dependencias..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado. Instalando..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        success "Docker instalado. Reinicia la sesión SSH."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado. Instalando..."
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        success "Docker Compose instalado."
    fi
    
    success "Dependencias verificadas"
}

# Crear directorios necesarios
create_directories() {
    info "Creando directorios necesarios..."
    mkdir -p uploads temp logs reports analysis_results context_storage
    success "Directorios creados"
}

# Verificar archivo .env
check_env_file() {
    info "Verificando archivo .env..."
    if [ ! -f .env ]; then
        error "Archivo .env no encontrado. Creando desde ejemplo..."
        cp env.example.txt .env
        warning "Configura las variables de entorno en .env antes de continuar."
        exit 1
    fi
    success "Archivo .env encontrado"
}

# Limpiar dependencias corruptas
clean_dependencies() {
    info "Limpiando dependencias corruptas..."
    
    # Parar servicios existentes
    docker-compose -f docker-compose.oracle_arm64.yml down --remove-orphans 2>/dev/null || true
    
    # Limpiar imágenes Docker existentes
    docker rmi arquitectura-app arquitectura-rasa 2>/dev/null || true
    docker system prune -f
    
    # Limpiar cache de pip
    pip cache purge 2>/dev/null || true
    
    success "Dependencias limpiadas"
}

# Construir y levantar servicios
deploy_services() {
    info "Construyendo y levantando servicios..."
    
    # Construir imágenes desde cero
    info "Construyendo imágenes Docker..."
    docker-compose -f docker-compose.oracle_arm64.yml build --no-cache --pull
    
    # Levantar servicios
    info "Levantando servicios..."
    docker-compose -f docker-compose.oracle_arm64.yml up -d
    
    success "Servicios desplegados"
}

# Esperar a que los servicios estén listos
wait_for_services() {
    info "Esperando a que los servicios estén listos..."
    sleep 30
    
    # Verificar estado de los servicios
    info "Verificando estado de los servicios..."
    docker-compose -f docker-compose.oracle_arm64.yml ps
}

# Verificar logs
check_logs() {
    info "Verificando logs..."
    docker-compose -f docker-compose.oracle_arm64.yml logs --tail=20
}

# Probar la aplicación
test_application() {
    info "Probando la aplicación..."
    
    # Esperar un poco más para que la aplicación esté completamente lista
    sleep 15
    
    # Probar health check de la aplicación principal
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        success "Aplicación principal funcionando"
    else
        warning "Aplicación principal no responde aún"
        # Mostrar logs de la aplicación para debugging
        info "Logs de la aplicación:"
        docker logs verificacion-app --tail=10
    fi
    
    # Probar Rasa
    if curl -f http://localhost:5005/health > /dev/null 2>&1; then
        success "Rasa funcionando"
    else
        warning "Rasa no responde aún"
        # Mostrar logs de Rasa para debugging
        info "Logs de Rasa:"
        docker logs verificacion-rasa --tail=10
    fi
}

# Mostrar información de acceso
show_access_info() {
    info "Información de acceso:"
    echo "🌐 Aplicación principal: http://$(curl -s ifconfig.me)"
    echo "🔧 Health check: http://$(curl -s ifconfig.me)/health"
    echo "🤖 Rasa: http://$(curl -s ifconfig.me):5005"
    echo "🗄️ Neo4j: http://$(curl -s ifconfig.me):7474"
    echo ""
    echo "📋 Comandos útiles:"
    echo "  Ver logs: docker-compose -f docker-compose.oracle_arm64.yml logs -f"
    echo "  Parar servicios: docker-compose -f docker-compose.oracle_arm64.yml down"
    echo "  Reiniciar: docker-compose -f docker-compose.oracle_arm64.yml restart"
}

# Función principal
main() {
    echo "🚀 Iniciando despliegue simplificado en Oracle Cloud ARM64..."
    echo "================================================================"
    
    check_dependencies
    create_directories
    check_env_file
    clean_dependencies
    deploy_services
    wait_for_services
    check_logs
    test_application
    show_access_info
    
    echo "================================================================"
    success "¡Despliegue completado!"
}

# Ejecutar función principal
main "$@"
