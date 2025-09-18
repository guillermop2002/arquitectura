"""
Endpoints de verificación Madrid con referencias específicas.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import asyncio
import uuid
from datetime import datetime

from ..core.madrid_verification_engine import MadridVerificationEngine, VerificationResult
from ..core.madrid_report_generator import MadridReportGenerator
from ..core.madrid_floor_processor import MadridFloorProcessor
from ..core.madrid_normative_processor import MadridNormativeProcessor
from ..core.madrid_database_manager import MadridDatabaseManager
from ..models.madrid_schemas import MadridProjectData

logger = logging.getLogger(__name__)

# Router para endpoints de verificación Madrid
verification_router = APIRouter(prefix="/madrid/verification", tags=["Madrid Verification"])

# Instancias globales
verification_engine = None
report_generator = None
floor_processor = MadridFloorProcessor()
normative_processor = MadridNormativeProcessor()

# Modelos Pydantic
class VerificationRequest(BaseModel):
    """Request para verificación de proyecto."""
    project_data: MadridProjectData = Field(..., description="Datos del proyecto Madrid")
    include_report: bool = Field(default=True, description="Incluir generación de reporte")
    report_format: str = Field(default="json", description="Formato del reporte (json, html)")

class VerificationResponse(BaseModel):
    """Response de verificación."""
    verification_id: str = Field(..., description="ID de la verificación")
    project_id: str = Field(..., description="ID del proyecto")
    status: str = Field(..., description="Estado de la verificación")
    compliance_percentage: float = Field(..., description="Porcentaje de cumplimiento")
    total_items: int = Field(..., description="Total de items verificados")
    compliant_items: int = Field(..., description="Items cumplidos")
    non_compliant_items: int = Field(..., description="Items no cumplidos")
    critical_issues: int = Field(..., description="Issues críticos")
    report_url: Optional[str] = Field(None, description="URL del reporte generado")
    created_at: str = Field(..., description="Fecha de creación")

class VerificationStatusResponse(BaseModel):
    """Response de estado de verificación."""
    verification_id: str
    status: str
    progress_percentage: float
    current_step: str
    estimated_completion: Optional[str] = None

class VerificationItemResponse(BaseModel):
    """Response de item de verificación."""
    item_id: str
    title: str
    status: str
    severity: str
    normative_references: List[Dict[str, Any]]
    notes: List[str]

# Dependencias
async def get_verification_engine():
    """Obtener instancia del motor de verificación."""
    global verification_engine
    if verification_engine is None:
        verification_engine = MadridVerificationEngine(
            floor_processor=floor_processor,
            normative_processor=normative_processor
        )
    return verification_engine

async def get_report_generator():
    """Obtener instancia del generador de reportes."""
    global report_generator
    if report_generator is None:
        report_generator = MadridReportGenerator()
    return report_generator

# Endpoints

@verification_router.post("/verify", response_model=VerificationResponse)
async def verify_madrid_project(
    request: VerificationRequest,
    background_tasks: BackgroundTasks,
    engine: MadridVerificationEngine = Depends(get_verification_engine),
    report_gen: MadridReportGenerator = Depends(get_report_generator)
):
    """
    Verificar proyecto Madrid con normativa específica.
    
    Ejecuta verificación completa del proyecto aplicando normativa PGOUM y CTE
    con referencias específicas a documentos y páginas.
    """
    try:
        logger.info(f"Iniciando verificación de proyecto: {request.project_data.primary_use}")
        
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
        
        # Ejecutar verificación
        verification_result = await engine.verify_project(project_data)
        
        # Generar reporte si se solicita
        report_url = None
        if request.include_report:
            background_tasks.add_task(
                _generate_report_background,
                verification_result,
                project_data,
                report_gen,
                request.report_format
            )
            report_url = f"/madrid/verification/reports/{verification_result.verification_id}"
        
        # Crear response
        response = VerificationResponse(
            verification_id=verification_result.verification_id,
            project_id=verification_result.project_id,
            status=verification_result.overall_status.value,
            compliance_percentage=verification_result.compliance_percentage,
            total_items=verification_result.total_items,
            compliant_items=verification_result.compliant_items,
            non_compliant_items=verification_result.non_compliant_items,
            critical_issues=verification_result.summary.get('critical_issues', 0),
            report_url=report_url,
            created_at=verification_result.created_at
        )
        
        logger.info(f"Verificación completada: {verification_result.verification_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error en verificación de proyecto: {e}")
        raise HTTPException(status_code=500, detail=f"Error en verificación: {str(e)}")

@verification_router.get("/status/{verification_id}", response_model=VerificationStatusResponse)
async def get_verification_status(verification_id: str):
    """
    Obtener estado de una verificación en progreso.
    
    Args:
        verification_id: ID de la verificación
        
    Returns:
        Estado actual de la verificación
    """
    try:
        # Por ahora, simular estado (en implementación real, consultar base de datos)
        return VerificationStatusResponse(
            verification_id=verification_id,
            status="completed",
            progress_percentage=100.0,
            current_step="Verificación completada",
            estimated_completion=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de verificación {verification_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@verification_router.get("/items/{verification_id}", response_model=List[VerificationItemResponse])
async def get_verification_items(verification_id: str):
    """
    Obtener items de verificación de un proyecto.
    
    Args:
        verification_id: ID de la verificación
        
    Returns:
        Lista de items de verificación
    """
    try:
        # Por ahora, retornar estructura básica
        # En implementación real, consultar base de datos
        return []
        
    except Exception as e:
        logger.error(f"Error obteniendo items de verificación {verification_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo items: {str(e)}")

@verification_router.get("/reports/{verification_id}")
async def get_verification_report(
    verification_id: str,
    format: str = "json",
    report_gen: MadridReportGenerator = Depends(get_report_generator)
):
    """
    Obtener reporte de verificación.
    
    Args:
        verification_id: ID de la verificación
        format: Formato del reporte (json, html)
        
    Returns:
        Reporte de verificación
    """
    try:
        # Buscar archivo de reporte
        if format == "json":
            filename = f"verification_report_{verification_id}.json"
            filepath = report_gen.output_dir / filename
            
            if filepath.exists():
                return FileResponse(
                    path=str(filepath),
                    media_type="application/json",
                    filename=filename
                )
            else:
                raise HTTPException(status_code=404, detail="Reporte no encontrado")
        
        elif format == "html":
            filename = f"verification_report_{verification_id}.html"
            filepath = report_gen.output_dir / filename
            
            if filepath.exists():
                return FileResponse(
                    path=str(filepath),
                    media_type="text/html",
                    filename=filename
                )
            else:
                raise HTTPException(status_code=404, detail="Reporte no encontrado")
        
        else:
            raise HTTPException(status_code=400, detail="Formato no soportado")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo reporte {verification_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo reporte: {str(e)}")

@verification_router.get("/templates/{building_type}")
async def get_verification_templates(building_type: str):
    """
    Obtener plantillas de verificación para un tipo de edificio.
    
    Args:
        building_type: Tipo de edificio
        
    Returns:
        Plantillas de verificación
    """
    try:
        engine = await get_verification_engine()
        templates = engine.verification_templates.get(building_type, [])
        
        return {
            'building_type': building_type,
            'templates': templates,
            'total_templates': len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo plantillas para {building_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo plantillas: {str(e)}")

@verification_router.get("/rules")
async def get_verification_rules():
    """
    Obtener reglas de verificación disponibles.
    
    Returns:
        Reglas de verificación
    """
    try:
        engine = await get_verification_engine()
        return {
            'rules': engine.verification_rules,
            'categories': list(engine.verification_rules.keys())
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo reglas de verificación: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo reglas: {str(e)}")

@verification_router.post("/validate-floor-descriptions")
async def validate_floor_descriptions(
    floor_descriptions: List[str],
    floor_processor: MadridFloorProcessor = Depends(lambda: floor_processor)
):
    """
    Validar descripciones de plantas.
    
    Args:
        floor_descriptions: Lista de descripciones de plantas
        
    Returns:
        Resultado de validación
    """
    try:
        # Procesar plantas
        processed_floors = floor_processor.process_floor_list(floor_descriptions)
        
        # Generar etiquetas
        floor_labels = [floor_processor.get_floor_label(floor) for floor in processed_floors]
        
        # Identificar no procesadas
        unprocessed = []
        for desc in floor_descriptions:
            if floor_processor.extract_floor_number(desc) is None:
                unprocessed.append(desc)
        
        return {
            'input_descriptions': floor_descriptions,
            'processed_floors': processed_floors,
            'floor_labels': floor_labels,
            'unprocessed': unprocessed,
            'validation_success': len(unprocessed) == 0
        }
        
    except Exception as e:
        logger.error(f"Error validando descripciones de plantas: {e}")
        raise HTTPException(status_code=500, detail=f"Error validando plantas: {str(e)}")

# Funciones de background
async def _generate_report_background(
    verification_result: VerificationResult,
    project_data: Dict[str, Any],
    report_generator: MadridReportGenerator,
    format: str
):
    """Generar reporte en background."""
    try:
        await report_generator.generate_verification_report(
            verification_result,
            project_data,
            format
        )
        logger.info(f"Reporte generado en background: {verification_result.verification_id}")
    except Exception as e:
        logger.error(f"Error generando reporte en background: {e}")
