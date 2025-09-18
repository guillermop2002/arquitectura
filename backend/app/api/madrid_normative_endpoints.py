"""
Endpoints para aplicación de normativa específica de Madrid.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json

from ..core.madrid_normative_applicator import MadridNormativeApplicator, NormativeApplication
from ..core.madrid_compliance_checker import MadridComplianceChecker
from ..core.ai_client import AIClient

logger = logging.getLogger(__name__)

# Router para endpoints de normativa
normative_router = APIRouter(prefix="/madrid/normative", tags=["Madrid Normative"])

# Inicializar aplicadores
normative_applicator = MadridNormativeApplicator()
ai_client = AIClient()
compliance_checker = MadridComplianceChecker(ai_client)

@normative_router.post("/apply-normative")
async def apply_normative(normative_data: Dict[str, Any]):
    """
    Aplicar normativa específica según el tipo de edificio y usos.
    
    Args:
        normative_data: Datos del proyecto para aplicación de normativa
        
    Returns:
        Aplicación de normativa específica
    """
    try:
        logger.info(f"Aplicando normativa para proyecto {normative_data.get('project_id', 'unknown')}")
        
        # Extraer datos del proyecto
        project_id = normative_data.get('project_id', 'unknown')
        primary_use = normative_data.get('primary_use')
        secondary_uses = normative_data.get('secondary_uses', [])
        is_existing_building = normative_data.get('is_existing_building', False)
        
        if not primary_use:
            raise HTTPException(status_code=400, detail="Uso principal del edificio es requerido")
        
        # Aplicar normativa
        application = normative_applicator.apply_normative(
            project_data=normative_data,
            primary_use=primary_use,
            secondary_uses=secondary_uses,
            is_existing_building=is_existing_building
        )
        
        # Crear respuesta
        response = {
            "project_id": application.project_id,
            "primary_use": application.primary_use,
            "secondary_uses": application.secondary_uses,
            "is_existing_building": application.is_existing_building,
            "applicable_documents": [
                {
                    "name": doc.name,
                    "type": doc.type,
                    "description": doc.description,
                    "priority": doc.priority,
                    "building_types": doc.building_types,
                    "floors": doc.floors
                }
                for doc in application.applicable_documents
            ],
            "floor_assignments": application.floor_assignments,
            "compliance_requirements": application.compliance_requirements,
            "summary": normative_applicator.get_normative_summary(application)
        }
        
        logger.info(f"Normativa aplicada: {len(application.applicable_documents)} documentos, "
                   f"{len(application.floor_assignments)} plantas")
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error aplicando normativa: {e}")
        raise HTTPException(status_code=500, detail=f"Error aplicando normativa: {str(e)}")

@normative_router.post("/check-compliance")
async def check_compliance(compliance_data: Dict[str, Any]):
    """
    Verificar cumplimiento de la normativa aplicada.
    
    Args:
        compliance_data: Datos para verificación de cumplimiento
        
    Returns:
        Resultado de verificación de cumplimiento
    """
    try:
        logger.info(f"Verificando cumplimiento para proyecto {compliance_data.get('project_id', 'unknown')}")
        
        # Extraer datos
        project_id = compliance_data.get('project_id', 'unknown')
        project_data = compliance_data.get('project_data', {})
        project_text = compliance_data.get('project_text', '')
        normative_application_data = compliance_data.get('normative_application', {})
        
        # Reconstruir aplicación de normativa
        application = NormativeApplication(
            project_id=normative_application_data.get('project_id', project_id),
            primary_use=normative_application_data.get('primary_use', ''),
            secondary_uses=normative_application_data.get('secondary_uses', []),
            is_existing_building=normative_application_data.get('is_existing_building', False),
            applicable_documents=[],  # Se reconstruiría desde los datos
            floor_assignments=normative_application_data.get('floor_assignments', {}),
            compliance_requirements=normative_application_data.get('compliance_requirements', {})
        )
        
        # Verificar cumplimiento
        result = await compliance_checker.check_compliance(
            normative_application=application,
            project_data=project_data,
            project_text=project_text
        )
        
        # Generar reporte
        report = compliance_checker.generate_compliance_report(result)
        
        logger.info(f"Verificación completada: {result.compliance_score:.1f}% cumplimiento")
        
        return JSONResponse(content=report)
        
    except Exception as e:
        logger.error(f"Error verificando cumplimiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error verificando cumplimiento: {str(e)}")

@normative_router.get("/normative-documents")
async def get_normative_documents():
    """
    Obtener lista de documentos normativos disponibles.
    
    Returns:
        Lista de documentos normativos
    """
    try:
        documents = []
        
        for doc_name, doc in normative_applicator.documents.items():
            documents.append({
                "name": doc.name,
                "type": doc.type,
                "description": doc.description,
                "priority": doc.priority,
                "building_types": doc.building_types,
                "floors": doc.floors,
                "path": doc.path
            })
        
        return JSONResponse(content={
            "total_documents": len(documents),
            "documents": documents,
            "by_type": {
                "basic": len([d for d in documents if d["type"] == "basic"]),
                "pgoum": len([d for d in documents if d["type"] == "pgoum"]),
                "support": len([d for d in documents if d["type"] == "support"])
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo documentos normativos: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo documentos: {str(e)}")

@normative_router.get("/building-types")
async def get_building_types():
    """
    Obtener tipos de edificio disponibles.
    
    Returns:
        Lista de tipos de edificio
    """
    try:
        building_types = list(normative_applicator.building_type_mapping.keys())
        
        return JSONResponse(content={
            "building_types": building_types,
            "total_types": len(building_types),
            "mapping": normative_applicator.building_type_mapping
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo tipos de edificio: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tipos: {str(e)}")

@normative_router.post("/simulate-normative-application")
async def simulate_normative_application(simulation_data: Dict[str, Any]):
    """
    Simular aplicación de normativa sin procesar documentos reales.
    
    Args:
        simulation_data: Datos para simulación
        
    Returns:
        Simulación de aplicación de normativa
    """
    try:
        logger.info("Simulando aplicación de normativa")
        
        # Datos de simulación
        primary_use = simulation_data.get('primary_use', 'residencial')
        secondary_uses = simulation_data.get('secondary_uses', [])
        is_existing_building = simulation_data.get('is_existing_building', False)
        
        # Simular aplicación
        simulated_application = normative_applicator.apply_normative(
            project_data=simulation_data,
            primary_use=primary_use,
            secondary_uses=secondary_uses,
            is_existing_building=is_existing_building
        )
        
        # Crear respuesta simulada
        response = {
            "simulation": True,
            "project_id": simulated_application.project_id,
            "primary_use": simulated_application.primary_use,
            "secondary_uses": simulated_application.secondary_uses,
            "is_existing_building": simulated_application.is_existing_building,
            "applicable_documents": [
                {
                    "name": doc.name,
                    "type": doc.type,
                    "description": doc.description,
                    "priority": doc.priority
                }
                for doc in simulated_application.applicable_documents
            ],
            "floor_assignments": simulated_application.floor_assignments,
            "compliance_requirements": simulated_application.compliance_requirements,
            "summary": normative_applicator.get_normative_summary(simulated_application)
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error simulando aplicación de normativa: {e}")
        raise HTTPException(status_code=500, detail=f"Error en simulación: {str(e)}")

@normative_router.get("/compliance-status/{project_id}")
async def get_compliance_status(project_id: str):
    """
    Obtener estado de cumplimiento de un proyecto.
    
    Args:
        project_id: ID del proyecto
        
    Returns:
        Estado de cumplimiento
    """
    try:
        # En producción, esto obtendría el estado desde la base de datos
        # Por ahora, devolver un estado simulado
        status = {
            "project_id": project_id,
            "status": "pending",
            "compliance_score": 0.0,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "critical_issues": 0,
            "last_updated": None
        }
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de cumplimiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")
