"""
Endpoints para el sistema de checklist final de Madrid - SIMPLIFICADO.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json

from ..core.madrid_final_checklist_system import MadridFinalChecklistSystem
from ..core.madrid_final_report_generator import MadridFinalReportGenerator
from ..core.madrid_normative_applicator import MadridNormativeApplicator
from ..core.madrid_compliance_checker import MadridComplianceChecker
from ..core.ai_client import AIClient

logger = logging.getLogger(__name__)

# Router para endpoints de checklist final
final_checklist_router = APIRouter(prefix="/api/madrid/final-checklist", tags=["Madrid Final Checklist"])

# Inicializar sistemas
checklist_system = MadridFinalChecklistSystem()
report_generator = MadridFinalReportGenerator()
normative_applicator = MadridNormativeApplicator()
ai_client = AIClient()
compliance_checker = MadridComplianceChecker(ai_client)

@final_checklist_router.post("/generate-checklist")
async def generate_final_checklist(checklist_data: Dict[str, Any]):
    """
    Generar checklist final SIMPLIFICADO - solo incumplimientos.
    
    Args:
        checklist_data: Datos del proyecto, normativa aplicada y resultados de cumplimiento
        
    Returns:
        Lista simple de incumplimientos
    """
    try:
        logger.info(f"Generando checklist final para proyecto {checklist_data.get('project_id', 'unknown')}")
        
        # Extraer datos
        project_data = checklist_data.get('project_data', {})
        normative_application = checklist_data.get('normative_application', {})
        compliance_results = checklist_data.get('compliance_results', {})
        
        if not project_data:
            raise HTTPException(status_code=400, detail="Datos del proyecto son requeridos")
        
        # Generar checklist SIMPLIFICADO - solo incumplimientos
        checklist_dict = checklist_system.generate_simple_checklist(checklist_data)
        
        logger.info(f"Checklist simplificado generado: {checklist_dict.get('total_incumplimientos', 0)} incumplimientos")
        
        return JSONResponse(content=checklist_dict)
        
    except Exception as e:
        logger.error(f"Error generando checklist final: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando checklist: {str(e)}")


@final_checklist_router.get("/status/{project_id}")
async def get_checklist_status(project_id: str):
    """
    Obtener estado del checklist para un proyecto.
    
    Args:
        project_id: ID del proyecto
        
    Returns:
        Estado actual del checklist
    """
    try:
        logger.info(f"Obteniendo estado del checklist para proyecto {project_id}")
        
        # Por ahora retornamos un estado básico
        status = {
            'project_id': project_id,
            'status': 'ready',
            'message': 'Sistema listo para generar checklist simplificado'
        }
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del checklist: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")


@final_checklist_router.post("/generate-report")
async def generate_final_report(report_data: Dict[str, Any]):
    """
    Generar reporte final basado en el checklist.
    
    Args:
        report_data: Datos para generar el reporte
        
    Returns:
        Reporte final generado
    """
    try:
        logger.info(f"Generando reporte final para proyecto {report_data.get('project_id', 'unknown')}")
        
        # Generar reporte usando el sistema existente
        report = report_generator.generate_comprehensive_report(
            analysis_data=report_data.get('analysis_data', {}),
            checklist_data=report_data.get('checklist_data', {}),
            project_metadata=report_data.get('project_metadata', {})
        )
        
        logger.info(f"Reporte generado exitosamente")
        
        return JSONResponse(content={
            'project_id': report_data.get('project_id', 'unknown'),
            'report': report,
            'status': 'completed'
        })
        
    except Exception as e:
        logger.error(f"Error generando reporte final: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")