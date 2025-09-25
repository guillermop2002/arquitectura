#!/bin/bash

echo "🚀 Desplegando Sistema Básico de Verificación"

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p uploads sessions logs Normativa

# Verificar archivo anexo1.json
if [ ! -f "Normativa/anexo1.json" ]; then
    echo "⚠️ Creando anexo1.json por defecto..."
    # El archivo ya está creado arriba
fi

# Verificar variables de entorno
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️ GROQ_API_KEY no está configurada"
    echo "Configúrala con: export GROQ_API_KEY=tu_api_key"
fi

# Detener servicios existentes
echo "🛑 Deteniendo servicios existentes..."
docker-compose down

# Construir y desplegar
echo "🏗️ Construyendo y desplegando..."
docker-compose up --build -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando servicios..."
sleep 30

# Verificar salud del sistema
echo "🏥 Verificando salud del sistema..."
curl -f http://localhost:8000/health || echo "❌ Servicio no responde"

# Ejecutar auditoría
echo "🔍 Ejecutando auditoría del sistema..."
curl -f http://localhost:8000/basico/audit/complete || echo "❌ Auditoría falló"

echo "✅ Despliegue completado!"
echo "🌐 Accede a: http://localhost:8000"
echo "📊 Auditoría: http://localhost:8000/basico/audit/complete"
echo "💚 Estado: http://localhost:8000/basico/production-status"