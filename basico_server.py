#!/usr/bin/env python3
"""
Servidor minimalista para el módulo /basico
Optimizado para Oracle Cloud ARM64
"""

import logging
import sys
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.app.basico.router import router as basico_router
import uvicorn
import os
import time
from pathlib import Path

# Configurar logging detallado para Docker logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Para docker-compose logs
        logging.FileHandler('logs/basico_detailed.log', encoding='utf-8')
    ]
)

# Logger principal
logger = logging.getLogger("basico.server")
logger.setLevel(logging.DEBUG)

# Configurar variables de entorno por defecto
os.environ.setdefault('HOST', '0.0.0.0')
os.environ.setdefault('PORT', '8000')

# Crear app minimalista solo para /basico
app = FastAPI(
    title="Sistema Básico de Verificación Arquitectónica",
    description="API para verificación de proyectos según Anexo I del CTE",
    version="1.0.0"
)

# Añadir CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging detallado de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"🌐 REQUEST: {request.method} {request.url}")
    logger.debug(f"   📋 Headers: {dict(request.headers)}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"✅ RESPONSE: {response.status_code} - {process_time:.4f}s")
    
    return response

# Agregar router de basico
app.include_router(basico_router, prefix="/basico")

# Endpoint de health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "basico-verification",
        "version": "1.0.0"
    }

# Endpoint de auditoría
@app.get("/basico/audit/complete")
async def audit_complete():
    try:
        from backend.app.basico.audit_checker import BasicoAuditChecker
        auditor = BasicoAuditChecker()
        results = auditor.run_complete_audit()
        return {"audit_results": results}
    except Exception as e:
        return {"error": str(e), "status": "audit_failed"}

# Endpoint de estado de producción
@app.get("/basico/production-status")
async def production_status():
    try:
        from backend.app.basico.audit_checker import BasicoAuditChecker
        auditor = BasicoAuditChecker()
        results = auditor.run_complete_audit()
        
        return {
            "production_ready": results["production_ready"],
            "overall_score": results["overall_score"],
            "readiness_level": results["readiness_level"],
            "system_status": results["system_status"]
        }
    except Exception as e:
        return {
            "production_ready": False,
            "overall_score": 0.0,
            "error": str(e)
        }

# Servir frontend estático
frontend_path = Path("backend/app/basico/frontend")
if frontend_path.exists():
    app.mount("/basico", StaticFiles(directory=str(frontend_path), html=True), name="basico_frontend")

if __name__ == "__main__":
    logger.info("🚀 Iniciando Sistema Básico de Verificación")
    logger.info("📍 Endpoints disponibles:")
    logger.info("  GET /health")
    logger.info("  GET /basico/audit/complete")
    logger.info("  GET /basico/production-status")
    logger.info("  POST /basico/session/create")
    logger.info("  POST /basico/session/{session_id}/upload")
    logger.info("  GET /basico/ (Frontend)")
    logger.info("")
    
    # Crear directorio de logs si no existe
    Path("logs").mkdir(exist_ok=True)
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    logger.info(f"🌐 Servidor iniciando en {host}:{port}")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="debug",
        access_log=True
    )
