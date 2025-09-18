"""
Endpoints para el sistema de checklist final de Madrid.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json

from ..core.madrid_final_checklist_system import MadridFinalChecklistSystem, FinalChecklist
from ..core.madrid_final_report_generator import MadridFinalReportGenerator
from ..core.madrid_normative_applicator import MadridNormativeApplicator
from ..core.madrid_compliance_checker import MadridComplianceChecker
from ..core.ai_client import AIClient

logger = logging.getLogger(__name__)

# Router para endpoints de checklist final
final_checklist_router = APIRouter(prefix="/madrid/final-checklist", tags=["Madrid Final Checklist"])

# Inicializar sistemas
checklist_system = MadridFinalChecklistSystem()
report_generator = MadridFinalReportGenerator()
normative_applicator = MadridNormativeApplicator()
ai_client = AIClient()
compliance_checker = MadridComplianceChecker(ai_client)

@final_checklist_router.post("/generate-checklist")
async def generate_final_checklist(checklist_data: Dict[str, Any]):
    """
    Generar checklist final basado en los datos del proyecto y normativa aplicada.
    
    Args:
        checklist_data: Datos del proyecto, normativa aplicada y resultados de cumplimiento
        
    Returns:
        Checklist final generado
    """
    try:
        logger.info(f"Generando checklist final para proyecto {checklist_data.get('project_id', 'unknown')}")
        
        # Extraer datos
        project_data = checklist_data.get('project_data', {})
        normative_application = checklist_data.get('normative_application', {})
        compliance_results = checklist_data.get('compliance_results', {})
        
        if not project_data:
            raise HTTPException(status_code=400, detail="Datos del proyecto son requeridos")
        
        # Generar checklist final
        checklist = checklist_system.generate_final_checklist(
            project_data=project_data,
            normative_application=normative_application,
            compliance_results=compliance_results
        )
        
        # Convertir a diccionario para respuesta
        checklist_dict = {
            "project_id": checklist.project_id,
            "project_name": checklist.project_name,
            "building_type": checklist.building_type,
            "is_existing_building": checklist.is_existing_building,
            "overall_completion": checklist.overall_completion,
            "total_items": checklist.total_items,
            "completed_items": checklist.completed_items,
            "critical_items": checklist.critical_items,
            "high_priority_items": checklist.high_priority_items,
            "status": checklist.status,
            "created_at": checklist.created_at.isoformat(),
            "updated_at": checklist.updated_at.isoformat(),
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "icon": category.icon,
                    "color": category.color,
                    "completion_percentage": category.completion_percentage,
                    "total_items": category.total_items,
                    "completed_items": category.completed_items,
                    "items": [
                        {
                            "id": item.id,
                            "title": item.title,
                            "description": item.description,
                            "category": item.category,
                            "priority": item.priority.value,
                            "status": item.status.value,
                            "normative_reference": item.normative_reference,
                            "document_requirement": item.document_requirement,
                            "verification_method": item.verification_method,
                            "evidence_required": item.evidence_required,
                            "current_evidence": item.current_evidence,
                            "notes": item.notes,
                            "assigned_to": item.assigned_to,
                            "due_date": item.due_date.isoformat() if item.due_date else None,
                            "created_at": item.created_at.isoformat(),
                            "updated_at": item.updated_at.isoformat()
                        }
                        for item in category.items
                    ]
                }
                for category in checklist.categories
            ],
            "metadata": checklist.metadata
        }
        
        logger.info(f"Checklist generado: {checklist.total_items} elementos, {checklist.overall_completion:.1f}% completado")
        
        return JSONResponse(content=checklist_dict)
        
    except Exception as e:
        logger.error(f"Error generando checklist final: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando checklist: {str(e)}")

@final_checklist_router.post("/update-item")
async def update_checklist_item(update_data: Dict[str, Any]):
    """
    Actualizar elemento del checklist.
    
    Args:
        update_data: Datos de actualización del elemento
        
    Returns:
        Resultado de la actualización
    """
    try:
        project_id = update_data.get('project_id')
        item_id = update_data.get('item_id')
        updates = update_data.get('updates', {})
        
        if not project_id or not item_id:
            raise HTTPException(status_code=400, detail="project_id e item_id son requeridos")
        
        # En una implementación real, esto cargaría el checklist desde la base de datos
        # Por ahora, simular actualización exitosa
        logger.info(f"Actualizando elemento {item_id} del proyecto {project_id}")
        
        # Simular actualización
        success = True  # En implementación real, esto actualizaría la base de datos
        
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": f"Elemento {item_id} actualizado correctamente",
                "item_id": item_id,
                "updates": updates
            })
        else:
            raise HTTPException(status_code=400, detail="Error actualizando elemento")
        
    except Exception as e:
        logger.error(f"Error actualizando elemento del checklist: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando elemento: {str(e)}")

@final_checklist_router.get("/{project_id}/status")
async def get_checklist_status(project_id: str):
    """
    Obtener estado del checklist de un proyecto.
    
    Args:
        project_id: ID del proyecto
        
    Returns:
        Estado del checklist
    """
    try:
        logger.info(f"Obteniendo estado del checklist para proyecto {project_id}")
        
        # En una implementación real, esto cargaría el estado desde la base de datos
        # Por ahora, devolver estado simulado
        status = {
            "project_id": project_id,
            "status": "in_progress",
            "overall_completion": 0.0,
            "total_items": 0,
            "completed_items": 0,
            "critical_items": 0,
            "high_priority_items": 0,
            "last_updated": None,
            "categories": []
        }
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del checklist: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@final_checklist_router.post("/generate-report")
async def generate_final_report(report_data: Dict[str, Any]):
    """
    Generar reporte final completo.
    
    Args:
        report_data: Datos para generar el reporte
        
    Returns:
        Reporte final generado
    """
    try:
        logger.info(f"Generando reporte final para proyecto {report_data.get('project_id', 'unknown')}")
        
        # Extraer datos
        project_data = report_data.get('project_data', {})
        normative_application = report_data.get('normative_application', {})
        compliance_results = report_data.get('compliance_results', {})
        checklist_data = report_data.get('checklist_data', {})
        
        if not project_data:
            raise HTTPException(status_code=400, detail="Datos del proyecto son requeridos")
        
        # Generar checklist si no se proporciona
        if not checklist_data:
            checklist = checklist_system.generate_final_checklist(
                project_data=project_data,
                normative_application=normative_application,
                compliance_results=compliance_results
            )
        else:
            # Reconstruir checklist desde datos proporcionados
            checklist = FinalChecklist(
                project_id=checklist_data.get('project_id', 'unknown'),
                project_name=checklist_data.get('project_name', 'Proyecto Sin Nombre'),
                building_type=checklist_data.get('building_type', 'residencial'),
                is_existing_building=checklist_data.get('is_existing_building', False)
            )
        
        # Generar reporte final
        report = report_generator.generate_final_report(
            checklist=checklist,
            compliance_results=compliance_results,
            normative_application=normative_application,
            project_data=project_data
        )
        
        # Convertir a diccionario para respuesta
        report_dict = {
            "project_id": report.project_id,
            "project_name": report.project_name,
            "building_type": report.building_type,
            "is_existing_building": report.is_existing_building,
            "report_date": report.report_date.isoformat(),
            "executive_summary": report.executive_summary,
            "checklist_summary": report.checklist_summary,
            "compliance_analysis": report.compliance_analysis,
            "normative_analysis": report.normative_analysis,
            "recommendations": report.recommendations,
            "next_steps": report.next_steps,
            "technical_details": report.technical_details,
            "appendices": report.appendices,
            "metadata": report.metadata
        }
        
        logger.info(f"Reporte final generado para proyecto {report.project_id}")
        
        return JSONResponse(content=report_dict)
        
    except Exception as e:
        logger.error(f"Error generando reporte final: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")

@final_checklist_router.get("/{project_id}/export-json")
async def export_checklist_to_json(project_id: str):
    """
    Exportar checklist a JSON.
    
    Args:
        project_id: ID del proyecto
        
    Returns:
        Checklist en formato JSON
    """
    try:
        logger.info(f"Exportando checklist a JSON para proyecto {project_id}")
        
        # En una implementación real, esto cargaría el checklist desde la base de datos
        # Por ahora, devolver JSON simulado
        checklist_json = {
            "project_id": project_id,
            "export_date": "2024-01-01T00:00:00Z",
            "format": "json",
            "version": "1.0",
            "checklist": {
                "status": "draft",
                "total_items": 0,
                "completed_items": 0,
                "categories": []
            }
        }
        
        return JSONResponse(content=checklist_json)
        
    except Exception as e:
        logger.error(f"Error exportando checklist a JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Error exportando: {str(e)}")

@final_checklist_router.get("/templates")
async def get_checklist_templates():
    """
    Obtener plantillas de checklist disponibles.
    
    Returns:
        Plantillas de checklist
    """
    try:
        logger.info("Obteniendo plantillas de checklist")
        
        templates = {
            "residencial": {
                "name": "Edificio Residencial",
                "description": "Checklist para edificios residenciales",
                "categories": [
                    "documentacion_basica",
                    "seguridad_estructural",
                    "seguridad_incendios",
                    "accesibilidad",
                    "eficiencia_energetica"
                ]
            },
            "industrial": {
                "name": "Edificio Industrial",
                "description": "Checklist para edificios industriales",
                "categories": [
                    "documentacion_basica",
                    "seguridad_estructural",
                    "seguridad_incendios",
                    "accesibilidad",
                    "eficiencia_energetica"
                ]
            }
        }
        
        return JSONResponse(content=templates)
        
    except Exception as e:
        logger.error(f"Error obteniendo plantillas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo plantillas: {str(e)}")

@final_checklist_router.post("/simulate-checklist")
async def simulate_checklist_generation(simulation_data: Dict[str, Any]):
    """
    Simular generación de checklist para testing.
    
    Args:
        simulation_data: Datos para simulación
        
    Returns:
        Checklist simulado
    """
    try:
        logger.info("Simulando generación de checklist")
        
        # Datos de simulación
        project_data = {
            "project_id": simulation_data.get('project_id', 'sim_project_001'),
            "project_name": simulation_data.get('project_name', 'Proyecto de Simulación'),
            "primary_use": simulation_data.get('primary_use', 'residencial'),
            "is_existing_building": simulation_data.get('is_existing_building', False)
        }
        
        # Simular aplicación de normativa
        normative_application = {
            "primary_use": project_data['primary_use'],
            "secondary_uses": [],
            "is_existing_building": project_data['is_existing_building'],
            "applicable_documents": [
                {"name": "DB-HE", "type": "basic"},
                {"name": "DB-SI", "type": "basic"},
                {"name": "pgoum_residencial", "type": "pgoum"}
            ]
        }
        
        # Simular resultados de cumplimiento
        compliance_results = {
            "compliance_score": 75.0,
            "total_checks": 20,
            "passed_checks": 15,
            "failed_checks": 5,
            "critical_issues": 1,
            "high_issues": 2,
            "medium_issues": 2,
            "low_issues": 0
        }
        
        # Generar checklist simulado
        checklist = checklist_system.generate_final_checklist(
            project_data=project_data,
            normative_application=normative_application,
            compliance_results=compliance_results
        )
        
        # Convertir a diccionario
        checklist_dict = {
            "project_id": checklist.project_id,
            "project_name": checklist.project_name,
            "building_type": checklist.building_type,
            "is_existing_building": checklist.is_existing_building,
            "overall_completion": checklist.overall_completion,
            "total_items": checklist.total_items,
            "completed_items": checklist.completed_items,
            "critical_items": checklist.critical_items,
            "high_priority_items": checklist.high_priority_items,
            "status": checklist.status,
            "simulation": True
        }
        
        return JSONResponse(content=checklist_dict)
        
    except Exception as e:
        logger.error(f"Error simulando checklist: {e}")
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")
