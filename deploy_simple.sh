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

# Configurar normativa Madrid
setup_normativa() {
    info "Configurando normativa Madrid..."
    
    # Verificar que existe la carpeta Normativa
    if [ ! -d "Normativa" ]; then
        error "Carpeta Normativa no encontrada. Creando estructura básica..."
        mkdir -p Normativa/{DOCUMENTOS_BASICOS/{DBHE,DBHR,DBHS,DBSE,DBSI,DBSUA},DOCUMENTOS_DE_APOYO/{DBHE,DBHR,DBSI,DBSUA},PGOUM}
        warning "Estructura de normativa creada. Debe subir los archivos PDF correspondientes."
    else
        success "Carpeta Normativa encontrada"
        
        # Verificar estructura básica
        if [ ! -d "Normativa/PGOUM" ] || [ ! -d "Normativa/DOCUMENTOS_BASICOS" ]; then
            warning "Estructura de normativa incompleta. Verificando..."
        fi
        
        # Contar archivos PDF
        pdf_count=$(find Normativa -name "*.pdf" | wc -l)
        info "Encontrados $pdf_count archivos PDF de normativa"
        
        if [ $pdf_count -eq 0 ]; then
            warning "No se encontraron archivos PDF de normativa. El sistema funcionará con datos simulados."
        else
            success "Normativa configurada correctamente"
        fi
    fi
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

# Configurar Rasa simple
configure_rasa_simple() {
    info "Configurando Rasa simple (puente a LLM)..."
    
    # Verificar que existe el directorio rasa_bot
    if [ ! -d "rasa_bot" ]; then
        error "Directorio rasa_bot no encontrado"
        exit 1
    fi
    
    # Usar configuración simple de Rasa
    if [ -f "rasa_bot/config.simple.yml" ]; then
        info "Aplicando configuración simple de Rasa..."
        cp rasa_bot/config.simple.yml rasa_bot/config.yml
        cp rasa_bot/domain.simple.yml rasa_bot/domain.yml
        cp rasa_bot/data/nlu.simple.yml rasa_bot/data/nlu.yml
        cp rasa_bot/data/stories.simple.yml rasa_bot/data/stories.yml
        cp rasa_bot/actions.simple.py rasa_bot/actions.py
        success "Rasa configurado como puente simple a LLM"
    else
        warning "Archivos de configuración simple no encontrados, usando configuración por defecto"
    fi
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
    echo "🤖 Rasa Chatbot: http://$(curl -s ifconfig.me):5005"
    echo "🗄️ Neo4j Browser: http://$(curl -s ifconfig.me):7474"
    echo "📊 PostgreSQL: puerto 5432"
    echo "🔄 Redis: puerto 6379"
    echo ""
    echo "🎯 NUEVAS FUNCIONALIDADES MADRID:"
    echo "  • Análisis inteligente de documentos con Neo4j"
    echo "  • Resolución de ambigüedades con chatbot"
    echo "  • Checklist final con trazabilidad completa"
    echo "  • Limpieza automática de Neo4j cada 24h"
    echo "  • Sistema de subida de normativa Madrid"
    echo ""
    echo "📋 Comandos útiles:"
    echo "  Ver logs: docker-compose -f docker-compose.oracle_arm64.yml logs -f"
    echo "  Parar servicios: docker-compose -f docker-compose.oracle_arm64.yml down"
    echo "  Reiniciar: docker-compose -f docker-compose.oracle_arm64.yml restart"
    echo "  Limpieza Neo4j: curl -X POST http://localhost:5000/neo4j/cleanup/manual"
    echo "  Estado Neo4j: curl http://localhost:5000/neo4j/cleanup/status"
    echo "  Estado Normativa: curl http://localhost:5000/api/madrid/normativa/status"
    echo "  Subir Normativa: curl -X POST -F 'zip_file=@normativa.zip' http://localhost:5000/api/madrid/normativa/upload-zip"
}

# Función principal
main() {
    echo "🚀 Iniciando despliegue simplificado en Oracle Cloud ARM64..."
    echo "================================================================"
    
    check_dependencies
    create_directories
    setup_normativa
    check_env_file
    configure_rasa_simple
    clean_dependencies
    deploy_services
    wait_for_services
    check_logs
    test_application
    show_access_info
    
    echo "================================================================"
    success "¡Despliegue completado con sistema Madrid + Neo4j integrado!"
}

# Ejecutar función principal
main "$@"
