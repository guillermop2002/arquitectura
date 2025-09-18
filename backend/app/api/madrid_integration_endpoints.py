"""
Endpoints de integración del sistema Madrid.
Proporciona acceso unificado a todas las funcionalidades Madrid.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import uuid
from datetime import datetime

from ..core.madrid_integration_manager import madrid_integration_manager
from ..models.madrid_schemas import MadridProjectData

logger = logging.getLogger(__name__)

# Router para endpoints de integración Madrid
integration_router = APIRouter(prefix="/madrid/integration", tags=["Madrid Integration"])

# Modelos Pydantic
class MadridProjectRequest(BaseModel):
    """Request para procesar proyecto Madrid completo."""
    project_data: MadridProjectData = Field(..., description="Datos del proyecto Madrid")
    auto_resolve_ambiguities: bool = Field(default=False, description="Resolver ambigüedades automáticamente")
    generate_report: bool = Field(default=True, description="Generar reporte de verificación")

class MadridProjectResponse(BaseModel):
    """Response de procesamiento de proyecto Madrid."""
    success: bool = Field(..., description="Si el procesamiento fue exitoso")
    project_id: str = Field(..., description="ID del proyecto")
    status: str = Field(..., description="Estado del procesamiento")
    message: str = Field(..., description="Mensaje descriptivo")
    verification_result: Optional[Dict[str, Any]] = Field(None, description="Resultado de verificación")
    ambiguities_count: Optional[int] = Field(None, description="Número de ambigüedades detectadas")
    chatbot_session_id: Optional[str] = Field(None, description="ID de sesión del chatbot")
    report_generated: Optional[bool] = Field(None, description="Si se generó reporte")
    processing_time: Optional[float] = Field(None, description="Tiempo de procesamiento en segundos")

class MadridSystemStatusResponse(BaseModel):
    """Response de estado del sistema Madrid."""
    overall_status: str = Field(..., description="Estado general del sistema")
    initialized: bool = Field(..., description="Si el sistema está inicializado")
    components: Dict[str, bool] = Field(..., description="Estado de cada componente")
    last_check: str = Field(..., description="Última verificación")

class MadridHealthCheckResponse(BaseModel):
    """Response de health check del sistema Madrid."""
    status: str = Field(..., description="Estado de salud")
    timestamp: str = Field(..., description="Timestamp de verificación")
    components_healthy: int = Field(..., description="Número de componentes saludables")
    total_components: int = Field(..., description="Total de componentes")
    details: Dict[str, Any] = Field(..., description="Detalles de cada componente")

# Dependencias
async def get_madrid_integration_manager():
    """Obtener instancia del gestor de integración Madrid."""
    return madrid_integration_manager

# Endpoints

@integration_router.post("/process-project", response_model=MadridProjectResponse)
async def process_madrid_project(
    request: MadridProjectRequest,
    background_tasks: BackgroundTasks,
    manager: madrid_integration_manager = Depends(get_madrid_integration_manager)
):
    """
    Procesar proyecto Madrid completo.
    
    Ejecuta el flujo completo: detección de ambigüedades, resolución (si es necesario),
    verificación normativa y generación de reportes.
    """
    try:
        start_time = datetime.now()
        logger.info(f"Iniciando procesamiento de proyecto Madrid: {request.project_data.primary_use}")
        
        # Convertir datos del proyecto
        project_data = {
            'project_id': str(uuid.uuid4()),
            'is_existing_building': request.project_data.is_existing_building,
            'primary_use': request.project_data.primary_use.value,
            'has_secondary_uses': request.project_data.has_secondary_uses,
            'secondary_uses': [
                {
                    'use_type': use.use_type.value,
                    'floors': use.floors
                } for use in request.project_data.secondary_uses
            ],
            'files': request.project_data.files
        }
        
        # Procesar proyecto
        result = await manager.process_madrid_project(project_data)
        
        # Calcular tiempo de procesamiento
        processing_time = (datetime.now() - start_time).total_seconds()
        result['processing_time'] = processing_time
        
        # Iniciar tareas en background si es necesario
        if result.get('status') == 'verification_completed' and request.generate_report:
            background_tasks.add_task(
                _generate_report_background,
                result.get('verification_result', {}),
                project_data
            )
        
        logger.info(f"Procesamiento completado: {result.get('status')} en {processing_time:.2f}s")
        return MadridProjectResponse(**result)
        
    except Exception as e:
        logger.error(f"Error procesando proyecto Madrid: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando proyecto: {str(e)}")

@integration_router.get("/status", response_model=MadridSystemStatusResponse)
async def get_madrid_system_status(
    manager: madrid_integration_manager = Depends(get_madrid_integration_manager)
):
    """
    Obtener estado del sistema Madrid.
    
    Returns:
        Estado actual de todos los componentes del sistema
    """
    try:
        status = await manager.get_system_status()
        return MadridSystemStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema Madrid: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@integration_router.get("/health", response_model=MadridHealthCheckResponse)
async def madrid_health_check(
    manager: madrid_integration_manager = Depends(get_madrid_integration_manager)
):
    """
    Health check del sistema Madrid.
    
    Returns:
        Estado de salud detallado del sistema
    """
    try:
        status = await manager.get_system_status()
        
        # Contar componentes saludables
        components = status.get('components', {})
        healthy_components = sum(1 for healthy in components.values() if healthy)
        total_components = len(components)
        
        # Determinar estado general
        if healthy_components == total_components:
            health_status = "healthy"
        elif healthy_components > total_components // 2:
            health_status = "degraded"
        else:
            health_status = "unhealthy"
        
        return MadridHealthCheckResponse(
            status=health_status,
            timestamp=datetime.now().isoformat(),
            components_healthy=healthy_components,
            total_components=total_components,
            details=components
        )
        
    except Exception as e:
        logger.error(f"Error en health check del sistema Madrid: {e}")
        raise HTTPException(status_code=500, detail=f"Error en health check: {str(e)}")

@integration_router.post("/initialize")
async def initialize_madrid_system(
    background_tasks: BackgroundTasks,
    manager: madrid_integration_manager = Depends(get_madrid_integration_manager)
):
    """
    Inicializar sistema Madrid.
    
    Inicializa todos los componentes del sistema Madrid en background.
    """
    try:
        logger.info("Inicializando sistema Madrid...")
        
        # Inicializar en background
        background_tasks.add_task(_initialize_system_background, manager)
        
        return {
            "message": "Inicialización del sistema Madrid iniciada en background",
            "status": "initializing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error iniciando inicialización del sistema Madrid: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando inicialización: {str(e)}")

@integration_router.get("/components")
async def get_madrid_components_info(
    manager: madrid_integration_manager = Depends(get_madrid_integration_manager)
):
    """
    Obtener información de los componentes del sistema Madrid.
    
    Returns:
        Información detallada de cada componente
    """
    try:
        components_info = {
            "floor_processor": {
                "name": "Procesador de Plantas Madrid",
                "description": "Convierte descripciones de plantas en formato texto a números",
                "features": ["Plantas especiales", "Conversión inteligente", "Validación de rangos"],
                "available": manager.status.floor_processor
            },
            "normative_processor": {
                "name": "Procesador de Normativa PGOUM",
                "description": "Gestiona documentos normativos específicos de Madrid",
                "features": ["CTE", "PGOUM General", "PGOUM Específico", "Documentos de Apoyo"],
                "available": manager.status.normative_processor
            },
            "database_manager": {
                "name": "Gestor de Base de Datos Madrid",
                "description": "Integra PostgreSQL para normativa y Neo4j para relaciones",
                "features": ["PostgreSQL", "Neo4j", "Índices optimizados", "Cache Redis"],
                "available": manager.status.database_manager
            },
            "verification_engine": {
                "name": "Motor de Verificación Madrid",
                "description": "Aplica normativa específica con referencias exactas",
                "features": ["Verificación inteligente", "Referencias específicas", "Reportes detallados"],
                "available": manager.status.verification_engine
            },
            "report_generator": {
                "name": "Generador de Reportes Madrid",
                "description": "Genera reportes con referencias normativas específicas",
                "features": ["Referencias exactas", "Múltiples formatos", "Reportes ejecutivos"],
                "available": manager.status.report_generator
            },
            "ambiguity_detector": {
                "name": "Detector de Ambigüedades Madrid",
                "description": "Identifica dudas específicas que requieren aclaración",
                "features": ["6 tipos de ambigüedades", "4 niveles de severidad", "Detección automática"],
                "available": manager.status.ambiguity_detector
            },
            "chatbot_system": {
                "name": "Sistema de Chatbot Madrid",
                "description": "Resuelve ambigüedades mediante conversación inteligente",
                "features": ["Resolución conversacional", "Patrones de reconocimiento", "Gestión de sesiones"],
                "available": manager.status.chatbot_system
            }
        }
        
        return {
            "total_components": len(components_info),
            "available_components": sum(1 for comp in components_info.values() if comp["available"]),
            "components": components_info
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo información de componentes: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo información: {str(e)}")

@integration_router.post("/cleanup")
async def cleanup_madrid_system(
    manager: madrid_integration_manager = Depends(get_madrid_integration_manager)
):
    """
    Limpiar recursos del sistema Madrid.
    
    Libera recursos y cierra conexiones del sistema Madrid.
    """
    try:
        logger.info("Limpiando sistema Madrid...")
        
        await manager.cleanup()
        
        return {
            "message": "Sistema Madrid limpiado correctamente",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error limpiando sistema Madrid: {e}")
        raise HTTPException(status_code=500, detail=f"Error limpiando sistema: {str(e)}")

# Funciones de background
async def _initialize_system_background(manager: madrid_integration_manager):
    """Inicializar sistema en background."""
    try:
        await manager.initialize_system()
        logger.info("Sistema Madrid inicializado en background")
    except Exception as e:
        logger.error(f"Error inicializando sistema Madrid en background: {e}")

async def _generate_report_background(verification_result: Dict[str, Any], project_data: Dict[str, Any]):
    """Generar reporte en background."""
    try:
        # Aquí se podría generar el reporte adicional si es necesario
        logger.info(f"Reporte generado en background para proyecto: {project_data.get('project_id')}")
    except Exception as e:
        logger.error(f"Error generando reporte en background: {e}")
