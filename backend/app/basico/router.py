from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import logging
from pathlib import Path
from .session_manager import BasicoSessionManager
from .analyzer import BasicoAnalyzer
from .audit_checker import BasicoAuditChecker

# Configurar logger específico
logger = logging.getLogger("basico.router")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/basico", tags=["basico"])

# Pydantic models
class AnalysisConfig(BaseModel):
    """Configuración para análisis completo"""
    uso_principal: str = Field(..., description="Uso principal del edificio")
    norma_zonal: str = Field(..., description="Norma zonal aplicable")
    grado: str = Field(..., description="Grado de análisis")
    superficie_construida: Optional[int] = Field(150, description="Superficie construida en m²")
    plantas: Optional[int] = Field(2, description="Número de plantas")

# Inicializar componentes
session_manager = BasicoSessionManager()
analyzer = BasicoAnalyzer()
audit_checker = BasicoAuditChecker()

@router.post("/session/create")
async def create_session(project_name: str = Form(...)):
    """Crear nueva sesión de análisis"""
    logger.info(f"🔧 CREANDO SESIÓN: project_name='{project_name}'")
    try:
        session_id = session_manager.create_session(project_name)
        logger.info(f"✅ SESIÓN CREADA: {session_id}")
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        logger.error(f"❌ ERROR CREANDO SESIÓN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@router.post("/session/{session_id}/upload")
async def upload_files(session_id: str, files: List[UploadFile] = File(...)):
    """Subir archivos a una sesión"""
    logger.info(f"📁 SUBIENDO ARCHIVOS: session_id='{session_id}', files={len(files)}")
    try:
        result = await session_manager.upload_files(session_id, files)
        logger.info(f"✅ ARCHIVOS SUBIDOS: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ ERROR SUBIENDO ARCHIVOS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

@router.post("/analyze/fase1/{session_id}")
async def analyze_fase1(session_id: str):
    """Ejecutar Fase 1: Verificación de documentación"""
    logger.info(f"🔍 EJECUTANDO FASE 1: session_id='{session_id}'")
    try:
        session_data = session_manager.get_session(session_id)
        result = await analyzer.fase1_verificar_documentacion(session_data)
        session_manager.save_phase_result(session_id, 1, result)
        logger.info(f"✅ FASE 1 COMPLETADA: {result.get('next_phase_ready', False)}")
        return result
    except Exception as e:
        logger.error(f"❌ ERROR EN FASE 1: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in Phase 1: {str(e)}")

@router.post("/analyze/fase2/{session_id}")
async def analyze_fase2(session_id: str, config: Dict[str, Any] = None):
    """Ejecutar Fase 2: Análisis de memoria"""
    logger.info(f"🔍 EJECUTANDO FASE 2: session_id='{session_id}', config={config}")
    try:
        session_data = session_manager.get_session(session_id)
        result = await analyzer.fase2_analizar_memoria(session_data, config or {})
        session_manager.save_phase_result(session_id, 2, result)
        logger.info(f"✅ FASE 2 COMPLETADA: coherence_score={result.get('coherence_score', 0)}")
        return result
    except Exception as e:
        logger.error(f"❌ ERROR EN FASE 2: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in Phase 2: {str(e)}")

@router.post("/analyze/fase3/{session_id}")
async def analyze_fase3(session_id: str):
    """Ejecutar Fase 3: Verificación normativa"""
    logger.info(f"🔍 EJECUTANDO FASE 3: session_id='{session_id}'")
    try:
        session_data = session_manager.get_session(session_id)
        context = session_manager.get_phase_results(session_id)
        result = await analyzer.fase3_verificar_normativa(session_data, context)
        session_manager.save_phase_result(session_id, 3, result)
        logger.info(f"✅ FASE 3 COMPLETADA: final_score={result.get('final_compliance_score', 0)}")
        return result
    except Exception as e:
        logger.error(f"❌ ERROR EN FASE 3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in Phase 3: {str(e)}")

@router.get("/session/{session_id}/results")
async def get_session_results(session_id: str):
    """Obtener todos los resultados de una sesión"""
    return session_manager.get_complete_results(session_id)

@router.get("/audit/complete")
async def run_complete_audit():
    """Ejecutar auditoría completa del sistema"""
    return audit_checker.run_complete_audit()

@router.get("/production-status")
async def get_production_status():
    """Verificar si el sistema está listo para producción"""
    audit_result = audit_checker.run_complete_audit()
    return {
        "production_ready": audit_result["production_ready"],
        "overall_score": audit_result["overall_score"],
        "readiness_level": audit_result["readiness_level"]
    }

@router.post("/normatives/preview")
async def preview_applicable_normatives(project_context: Dict[str, Any]):
    """Obtener vista previa de normativas aplicables según contexto del proyecto"""
    return analyzer.normative_loader.get_normative_summary(project_context)

@router.get("/")
async def serve_frontend():
    """Servir el frontend de la aplicación básica"""
    frontend_path = Path("frontend/basico/index.html")
    if frontend_path.exists():
        return FileResponse(frontend_path, media_type="text/html")
    else:
        return {"message": "Frontend no encontrado", "available_endpoints": [
            "GET /basico/audit/complete",
            "POST /basico/normatives/preview", 
            "POST /basico/session/create",
            "GET /basico/session/{id}/results"
        ]}

@router.get("/basico-app.js")
async def serve_js():
    """Servir archivo JavaScript"""
    js_path = Path("frontend/basico/basico-app.js")
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    else:
        raise HTTPException(status_code=404, detail="Archivo JavaScript no encontrado")

@router.post("/analyze/complete/{session_id}")
async def analyze_complete(session_id: str, config: AnalysisConfig):
    """Análisis completo: Ejecuta las 3 fases de una vez"""
    logger.info(f"🚀 ANÁLISIS COMPLETO INICIADO: session_id='{session_id}'")
    logger.info(f"⚙️ Configuración recibida: {config.model_dump()}")

    try:
        # Obtener datos de la sesión
        session_data = session_manager.get_session_data(session_id)
        if not session_data:
            logger.error(f"❌ Sesión no encontrada: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"📁 Archivos en sesión: {len(session_data.get('files', []))}")

        # FASE 1: Verificación de documentación
        logger.info("🔍 Ejecutando Fase 1: Verificación de documentación")
        fase1_result = await analyzer.fase1_verificar_documentacion(session_data)
        logger.info(f"✅ Fase 1 completada: {fase1_result.get('combined_results', {}).get('completion_percentage', 0)}%")

        # FASE 2: Análisis de memoria
        logger.info("📖 Ejecutando Fase 2: Análisis de memoria")
        fase2_result = await analyzer.fase2_analizar_memoria(session_data, config.model_dump())
        logger.info(f"✅ Fase 2 completada: {fase2_result.get('coherence_score', 0)}% coherencia")

        # FASE 3: Verificación normativa
        logger.info("📋 Ejecutando Fase 3: Verificación normativa")
        context = {"fase1": fase1_result, "fase2": fase2_result}
        fase3_result = await analyzer.fase3_verificar_normativa(session_data, context)
        logger.info(f"✅ Fase 3 completada: {fase3_result.get('final_score', 0)}% puntuación final")

        # Combinar resultados
        complete_result = {
            "session_id": session_id,
            "config": config.model_dump(),
            "fase1": fase1_result,
            "fase2": fase2_result,
            "fase3": fase3_result,
            "final_score": fase3_result.get("final_score", 0),
            "normative_verification": fase3_result.get("normative_verification", {}),
            "cte_verification": fase3_result.get("cte_verification", {}),
            "pgoum_verification": fase3_result.get("pgoum_verification", {}),
            "timestamp": fase3_result.get("timestamp")
        }

        logger.info(f"🎉 ANÁLISIS COMPLETO FINALIZADO: {complete_result['final_score']}% puntuación final")
        return complete_result

    except Exception as e:
        logger.error(f"❌ ERROR EN ANÁLISIS COMPLETO: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error in complete analysis: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("🏥 HEALTH CHECK solicitado")
    return {
        "status": "ok",
        "service": "basico-verification",
        "version": "1.0.0"
    }
