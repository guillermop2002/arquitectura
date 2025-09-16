#!/bin/bash
# Script de inicio rápido para Oracle Cloud ARM64
# Sistema de Verificación Arquitectónica

set -e

echo "🚀 INICIO RÁPIDO - ORACLE CLOUD ARM64"
echo "====================================="

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar sistema
echo "🔍 Verificando sistema..."
if ! grep -q "Ubuntu 22.04" /etc/os-release; then
    echo -e "${YELLOW}⚠️  Advertencia: Sistema no es Ubuntu 22.04${NC}"
fi

# Verificar arquitectura
if ! uname -m | grep -q "aarch64\|arm64"; then
    echo -e "${RED}❌ Error: No es arquitectura ARM64${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Sistema ARM64 detectado${NC}"

# Verificar Python
if ! command_exists python3.10; then
    echo -e "${RED}❌ Error: Python 3.10 no encontrado${NC}"
    echo "Instalando Python 3.10..."
    sudo apt update
    sudo apt install -y python3.10 python3.10-venv python3-pip
fi

# Verificar Redis
if ! command_exists redis-server; then
    echo -e "${YELLOW}⚠️  Redis no encontrado, instalando...${NC}"
    sudo apt update
    sudo apt install -y redis-server
fi

# Verificar Docker
if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker no encontrado, instalando...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Verificar Docker Compose
if ! command_exists docker-compose; then
    echo -e "${YELLOW}⚠️  Docker Compose no encontrado, instalando...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "🐍 Creando entorno virtual..."
    python3.10 -m venv .venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source .venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.oracle_arm64.txt

# Instalar PyTorch para ARM64
echo "🔥 Instalando PyTorch para ARM64..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Verificar configuración
echo "⚙️  Verificando configuración..."
if [ ! -f "env.oracle_arm64.txt" ]; then
    echo -e "${RED}❌ Error: Archivo env.oracle_arm64.txt no encontrado${NC}"
    echo "Creando archivo de configuración..."
    cp env.groq_only.txt env.oracle_arm64.txt
    echo -e "${YELLOW}⚠️  Edita env.oracle_arm64.txt con tus claves API${NC}"
fi

# Cargar variables de entorno
export $(cat env.oracle_arm64.txt | grep -v '^#' | xargs)

# Verificar claves API
if [ -z "$GROQ_API_KEY" ] || [ "$GROQ_API_KEY" = "gsk_bAHQ8OKiwJ2pgvKPwKq6WGdyb3FYQp3p5AjuufYBorWN4Z2PTFm" ]; then
    echo -e "${YELLOW}⚠️  Advertencia: GROQ_API_KEY no configurada o usando valor por defecto${NC}"
    echo "Edita env.oracle_arm64.txt con tu clave real de Groq"
fi

# Iniciar Redis
echo "🔄 Iniciando Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes
    echo -e "${GREEN}✅ Redis iniciado${NC}"
else
    echo -e "${GREEN}✅ Redis ya está corriendo${NC}"
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p uploads logs analysis_results context_storage temp ssl monitoring

# Verificar archivos necesarios
echo "🔍 Verificando archivos necesarios..."
required_files=(
    "main.py"
    "backend/app/core/ai_client.py"
    "backend/app/core/groq_optimized_prompts.py"
    "backend/app/core/opencv_optimizer.py"
    "backend/app/core/neo4j_optimizer.py"
    "backend/app/core/advanced_plan_analyzer.py"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo -e "${RED}❌ Archivos faltantes:${NC}"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    echo "Asegúrate de subir todos los archivos del proyecto"
    exit 1
fi

echo -e "${GREEN}✅ Todos los archivos necesarios están presentes${NC}"

# Opción de inicio
echo ""
echo "🚀 ¿Cómo quieres iniciar el sistema?"
echo "1) Inicio directo con Python"
echo "2) Inicio con Docker Compose"
echo "3) Solo verificar configuración"
read -p "Selecciona una opción (1-3): " choice

case $choice in
    1)
        echo "🐍 Iniciando con Python..."
        python main.py
        ;;
    2)
        echo "🐳 Iniciando con Docker Compose..."
        docker-compose -f docker-compose.oracle_arm64.yml up -d
        echo "Sistema iniciado con Docker Compose"
        echo "Verifica el estado con: docker-compose -f docker-compose.oracle_arm64.yml ps"
        ;;
    3)
        echo "✅ Verificación completada"
        echo "Para iniciar el sistema:"
        echo "  - Python: python main.py"
        echo "  - Docker: docker-compose -f docker-compose.oracle_arm64.yml up -d"
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "🎉 ¡Sistema listo!"
echo "📊 URLs de acceso:"
echo "  - Aplicación: http://$(curl -s ifconfig.me):5000"
echo "  - Health Check: http://$(curl -s ifconfig.me):5000/health"
echo ""
echo "📋 Comandos útiles:"
echo "  - Monitoreo: ./monitor_oracle.sh"
echo "  - Logs: tail -f logs/app.log"
echo "  - Estado: ps aux | grep python"
