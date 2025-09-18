# Sistema de Verificación Arquitectónica

Sistema de verificación de proyectos de edificación basado en IA para el cumplimiento del Código Técnico de la Edificación (CTE).

## 🏗️ Características

- **Verificación Automática**: Análisis automático de documentos de proyecto
- **IA Avanzada**: Integración con Groq para análisis inteligente
- **Cumplimiento Normativo**: Verificación específica de normativa Madrid (PGOUM)
- **Sistema Conversacional**: Chatbot Rasa para resolución de ambigüedades
- **Grafo de Conocimiento**: Neo4j para interconexión de memoria, planos y normativa
- **Limpieza Automática**: Sistema de limpieza automática de Neo4j cada 24h
- **Interfaz Web**: Frontend moderno y responsive con 7 pasos de verificación
- **Microservicios**: Arquitectura escalable con Docker

## 🚀 Despliegue Rápido

### Oracle Cloud ARM64

```bash
# Clonar repositorio
git clone https://github.com/guillermop2002/arquitectura.git
cd arquitectura

# Configurar variables de entorno
cp env.oracle_arm64.txt .env
# Editar .env con tus claves de Groq

# Desplegar
./deploy_simple.sh
```

### Acceso a la Aplicación

- **Aplicación Principal**: http://tu-ip
- **Rasa Chatbot**: http://tu-ip:5005
- **Neo4j Browser**: http://tu-ip:7474
- **PostgreSQL**: puerto 5432

## 📋 Requisitos

- Docker y Docker Compose
- 4 claves de API de Groq
- Mínimo 4GB RAM
- ARM64 compatible (Oracle Cloud)

## 🔧 Configuración

### Variables de Entorno

```bash
# Claves de Groq (4 claves para rotación)
GROQ_API_KEY_1=tu_clave_1
GROQ_API_KEY_2=tu_clave_2
GROQ_API_KEY_3=tu_clave_3
GROQ_API_KEY_4=tu_clave_4

# Base de datos
NEO4J_URI=neo4j://db:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=tu_password

# Redis
REDIS_URL=redis://redis:6379
```

## 📁 Estructura del Proyecto

```
├── backend/                 # Backend FastAPI
│   ├── app/
│   │   ├── core/           # Módulos principales
│   │   └── models/         # Modelos de datos
├── frontend/               # Frontend HTML/CSS/JS
├── rasa_bot/              # Bot conversacional
├── monitoring/            # Grafana y Prometheus
├── docker-compose.oracle_arm64.yml
├── Dockerfile.oracle_arm64
└── deploy_simple.sh
```

## 🛠️ Desarrollo

### Instalación Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.oracle_arm64.txt

# Ejecutar aplicación
python main.py
```

### Testing

```bash
# Ejecutar tests
python -m pytest tests/

# Test específico
python test_groq_system_complete.py
```

## 📚 Documentación

- [Guía de Despliegue Oracle Cloud](ORACLE_CLOUD_DEPLOYMENT_GUIDE.md)
- [Sistema de Limpieza](CLEANUP_SYSTEM_IMPLEMENTATION_REPORT.md)
- [Integración Groq](GROQ_SYSTEM_DOCUMENTATION.md)
- [Flujo Completo](FINAL_FLOW_DOCUMENTATION.md)

## 🔍 Flujo de Verificación Madrid (7 Pasos)

El sistema verifica automáticamente proyectos de edificación en Madrid:

1. **Información del Proyecto**: Tipo de edificio, uso principal, usos secundarios
2. **Subida de Documentos**: Memoria descriptiva y planos arquitectónicos
3. **Clasificación Automática**: IA clasifica documentos como memoria o plano
4. **Aplicación de Normativa**: Normativa específica PGOUM según tipo de edificio
5. **Análisis de Documentos**: Detección de ambigüedades con Neo4j
6. **Resolución de Ambigüedades**: Chatbot resuelve problemas específicos
7. **Checklist Final**: Generación de checklist con trazabilidad completa

### Normativas Aplicables:
- **Documentos Básicos**: DB-HE, DB-HR, DB-SI, DB-SU
- **PGOUM General**: Siempre aplicable
- **PGOUM Específico**: Según tipo de edificio (residencial, industrial, etc.)
- **Documentos de Apoyo**: Para edificios existentes

## 🤖 Chatbot Inteligente

- **Rasa Integration**: Chatbot conversacional para resolución de ambigüedades
- **Contexto de Proyecto**: Mantiene contexto entre conversaciones
- **Respuestas Inteligentes**: Basadas en IA y normativas específicas de Madrid
- **Trazabilidad**: Todas las conversaciones se guardan en Neo4j

## 🗄️ Grafo de Conocimiento Neo4j

- **Interconexión**: Relaciones entre memoria, planos y normativa
- **Trazabilidad**: Seguimiento completo de ambigüedades y resoluciones
- **Análisis Avanzado**: Patrones y dependencias entre elementos
- **Limpieza Automática**: Limpieza diaria a las 2:00 AM (30 días de retención)

## 📊 Monitoreo

- **Grafana Dashboards**: Métricas en tiempo real
- **Prometheus**: Recopilación de métricas
- **Logs Centralizados**: Sistema de logging avanzado
- **Neo4j Browser**: Interfaz web para explorar el grafo de conocimiento
- **Endpoints de Gestión**: API para limpieza y estadísticas de Neo4j

### Endpoints Neo4j:
- `GET /neo4j/cleanup/status` - Estado del programador de limpieza
- `POST /neo4j/cleanup/manual` - Limpieza manual de datos antiguos
- `POST /neo4j/cleanup/config` - Configuración de limpieza

## 🚨 Solución de Problemas

### Error: "No se encontraron claves de Groq"
```bash
# Verificar variables de entorno
cat .env | grep GROQ_API_KEY
```

### Error: "ModuleNotFoundError"
```bash
# Reconstruir contenedores
docker-compose -f docker-compose.oracle_arm64.yml build --no-cache
```

### Error: "Neo4j connection failed"
```bash
# Verificar estado de Neo4j
docker logs verificacion-db
```

## 📞 Soporte

Para soporte técnico o reportar problemas:
- Crear issue en GitHub
- Revisar logs: `docker logs verificacion-app`
- Verificar estado: `docker-compose ps`

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- Groq por la API de IA
- Neo4j por la base de datos de grafos
- FastAPI por el framework web
- Rasa por el chatbot conversacional
