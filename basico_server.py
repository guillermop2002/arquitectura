#!/usr/bin/env python3
"""
Servidor minimalista para el módulo /basico
Optimizado para Oracle Cloud ARM64
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app.basico.router import router as basico_router
import uvicorn
import os
import logging
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
    ]
)

# Set specific logger levels for detailed debugging
logging.getLogger("basico.normative_loader").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

# Configurar variables de entorno por defecto
os.environ.setdefault('HOST', '0.0.0.0')
os.environ.setdefault('PORT', '8000')

# Crear app minimalista solo para /basico
app = FastAPI(
    title="Sistema Básico de Verificación Arquitectónica",
    description="API para verificación de proyectos según Anexo I del CTE",
    version="1.0.0"
)

# Agregar router de basico
app.include_router(basico_router)

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
    print("🚀 Iniciando Sistema Básico de Verificación")
    print("📍 Endpoints disponibles:")
    print("  GET /health")
    print("  GET /basico/audit/complete")
    print("  GET /basico/production-status")
    print("  POST /basico/session/create")
    print("  POST /basico/session/{session_id}/upload")
    print("  GET /basico/ (Frontend)")
    print()
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    uvicorn.run(app, host=host, port=port)
