#!/bin/bash

# Script de despliegue optimizado para Sistema Madrid
# Preserva toda la configuración existente y añade funcionalidades Madrid

set -e

echo "🏛️ DESPLIEGUE SISTEMA MADRID - ORACLE CLOUD ARM64"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    log_error "No se encontró main.py. Ejecutar desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar archivos críticos existentes
log_info "Verificando configuración existente..."

critical_files=(
    "requirements.oracle_arm64.txt"
    "Dockerfile.oracle_arm64"
    "docker-compose.oracle_arm64.yml"
    "nginx/nginx.conf"
    "nginx/conf.d/default.conf"
    ".env"
)

for file in "${critical_files[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Archivo crítico no encontrado: $file"
        exit 1
    fi
done

log_success "Configuración existente verificada"

# Verificar que Docker esté funcionando
log_info "Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    log_error "Docker no está funcionando. Iniciar Docker primero."
    exit 1
fi

log_success "Docker funcionando correctamente"

# Verificar que docker-compose esté disponible
if ! command -v docker-compose > /dev/null 2>&1; then
    log_error "docker-compose no está instalado"
    exit 1
fi

log_success "docker-compose disponible"

# Crear directorios necesarios para Madrid (si no existen)
log_info "Creando directorios necesarios para sistema Madrid..."

madrid_dirs=(
    "uploads/madrid"
    "temp/madrid"
    "logs/madrid"
    "reports/madrid"
    "analysis_results/madrid"
    "context_storage/madrid"
    "Normativa/PGOUM"
    "Normativa/DOCUMENTOS_BASICOS"
    "Normativa/DOCUMENTOS_DE_APOYO"
)

for dir in "${madrid_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_info "Directorio creado: $dir"
    fi
done

log_success "Directorios Madrid creados"

# Verificar permisos de directorios
log_info "Verificando permisos de directorios..."
chmod -R 755 uploads temp logs reports analysis_results context_storage
log_success "Permisos configurados"

# Limpiar contenedores existentes (solo si están corriendo)
log_info "Limpiando contenedores existentes..."
if docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "Up"; then
    log_warning "Deteniendo contenedores existentes..."
    docker-compose -f docker-compose.oracle_arm64.yml down
    sleep 5
fi

log_success "Contenedores limpiados"

# Limpiar imágenes huérfanas (opcional)
log_info "Limpiando imágenes huérfanas..."
docker image prune -f > /dev/null 2>&1 || true
log_success "Imágenes limpiadas"

# Construir imágenes con cache optimizado
log_info "Construyendo imágenes Docker (con cache optimizado)..."

# Construir imagen principal
log_info "Construyendo imagen principal (app)..."
if docker-compose -f docker-compose.oracle_arm64.yml build --no-cache app; then
    log_success "Imagen principal construida"
else
    log_error "Error construyendo imagen principal"
    exit 1
fi

# Construir imagen Rasa
log_info "Construyendo imagen Rasa..."
if docker-compose -f docker-compose.oracle_arm64.yml build --no-cache rasa; then
    log_success "Imagen Rasa construida"
else
    log_error "Error construyendo imagen Rasa"
    exit 1
fi

# Iniciar servicios en orden
log_info "Iniciando servicios..."

# 1. Iniciar bases de datos primero
log_info "Iniciando bases de datos..."
docker-compose -f docker-compose.oracle_arm64.yml up -d postgres redis db
sleep 10

# Verificar que las bases de datos estén funcionando
log_info "Verificando bases de datos..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "verificacion-postgres.*Up" && \
       docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "verificacion-redis.*Up" && \
       docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "verificacion-db.*Up"; then
        log_success "Bases de datos funcionando"
        break
    fi
    
    attempt=$((attempt + 1))
    log_info "Esperando bases de datos... ($attempt/$max_attempts)"
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    log_error "Bases de datos no iniciaron correctamente"
    docker-compose -f docker-compose.oracle_arm64.yml logs postgres redis db
    exit 1
fi

# 2. Iniciar aplicación principal
log_info "Iniciando aplicación principal..."
docker-compose -f docker-compose.oracle_arm64.yml up -d app
sleep 15

# Verificar que la aplicación esté funcionando
log_info "Verificando aplicación principal..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "verificacion-app.*Up"; then
        log_success "Aplicación principal funcionando"
        break
    fi
    
    attempt=$((attempt + 1))
    log_info "Esperando aplicación principal... ($attempt/$max_attempts)"
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    log_error "Aplicación principal no inició correctamente"
    docker-compose -f docker-compose.oracle_arm64.yml logs app
    exit 1
fi

# 3. Iniciar Rasa
log_info "Iniciando Rasa..."
docker-compose -f docker-compose.oracle_arm64.yml up -d rasa
sleep 10

# Verificar que Rasa esté funcionando
log_info "Verificando Rasa..."
max_attempts=20
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "verificacion-rasa.*Up"; then
        log_success "Rasa funcionando"
        break
    fi
    
    attempt=$((attempt + 1))
    log_info "Esperando Rasa... ($attempt/$max_attempts)"
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    log_warning "Rasa no inició correctamente, continuando sin Rasa"
fi

# 4. Iniciar Nginx
log_info "Iniciando Nginx..."
docker-compose -f docker-compose.oracle_arm64.yml up -d nginx
sleep 5

# Verificar que Nginx esté funcionando
log_info "Verificando Nginx..."
max_attempts=15
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "verificacion-nginx.*Up"; then
        log_success "Nginx funcionando"
        break
    fi
    
    attempt=$((attempt + 1))
    log_info "Esperando Nginx... ($attempt/$max_attempts)"
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    log_error "Nginx no inició correctamente"
    docker-compose -f docker-compose.oracle_arm64.yml logs nginx
    exit 1
fi

# Verificación final del sistema
log_info "Realizando verificación final del sistema..."

# Verificar que todos los servicios estén funcionando
services=("verificacion-app" "verificacion-postgres" "verificacion-redis" "verificacion-db" "verificacion-nginx")
all_services_up=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "$service.*Up"; then
        log_success "$service: UP"
    else
        log_error "$service: DOWN"
        all_services_up=false
    fi
done

# Verificar Rasa por separado (opcional)
if docker-compose -f docker-compose.oracle_arm64.yml ps | grep -q "verificacion-rasa.*Up"; then
    log_success "verificacion-rasa: UP"
else
    log_warning "verificacion-rasa: DOWN (opcional)"
fi

# Test de conectividad
log_info "Probando conectividad..."

# Test local
if curl -s -f http://localhost/health > /dev/null 2>&1; then
    log_success "Health check local: OK"
else
    log_warning "Health check local: FALLÓ"
fi

# Test de endpoints Madrid
if curl -s -f http://localhost/madrid/integration/health > /dev/null 2>&1; then
    log_success "Sistema Madrid: OK"
else
    log_warning "Sistema Madrid: No disponible aún"
fi

# Mostrar estado final
log_info "Estado final del sistema:"
docker-compose -f docker-compose.oracle_arm64.yml ps

# Mostrar URLs de acceso
echo ""
echo "🌐 URLs DE ACCESO:"
echo "=================="
echo "Aplicación principal: http://localhost"
echo "API Documentation: http://localhost/docs"
echo "Sistema Madrid: http://localhost/madrid/integration/health"
echo "Neo4j Browser: http://localhost:7474"
echo "Rasa (si funciona): http://localhost:5005"

# Mostrar comandos útiles
echo ""
echo "🔧 COMANDOS ÚTILES:"
echo "==================="
echo "Ver logs: docker-compose -f docker-compose.oracle_arm64.yml logs -f"
echo "Reiniciar: docker-compose -f docker-compose.oracle_arm64.yml restart"
echo "Detener: docker-compose -f docker-compose.oracle_arm64.yml down"
echo "Estado: docker-compose -f docker-compose.oracle_arm64.yml ps"

if [ "$all_services_up" = true ]; then
    echo ""
    log_success "🎉 SISTEMA MADRID DESPLEGADO EXITOSAMENTE"
    echo "El sistema está funcionando correctamente en Oracle Cloud ARM64"
    echo "Todas las funcionalidades Madrid están disponibles"
else
    echo ""
    log_warning "⚠️ SISTEMA DESPLEGADO CON ADVERTENCIAS"
    echo "Algunos servicios pueden no estar funcionando correctamente"
    echo "Revisar logs para más detalles"
fi

echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "=================="
echo "1. Subir documentos normativos a la carpeta Normativa/"
echo "2. Configurar variables de entorno específicas de Madrid"
echo "3. Probar endpoints del sistema Madrid"
echo "4. Configurar firewall de Oracle Cloud si es necesario"
echo "5. Realizar pruebas de verificación completas"

echo ""
log_info "Despliegue completado. Revisar logs si hay problemas."
