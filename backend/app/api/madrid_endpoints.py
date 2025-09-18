"""
Endpoints API específicos para el sistema Madrid.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio

from ..core.madrid_floor_processor import MadridFloorProcessor
from ..core.madrid_normative_processor import MadridNormativeProcessor
from ..core.madrid_database_manager import MadridDatabaseManager, DatabaseConfig
from ..models.madrid_schemas import MadridProjectData, BuildingType, SecondaryUse

logger = logging.getLogger(__name__)

# Router para endpoints de Madrid
madrid_router = APIRouter(prefix="/madrid", tags=["Madrid"])

# Instancias globales (se inicializarán en startup)
floor_processor = MadridFloorProcessor()
normative_processor = MadridNormativeProcessor()
db_manager = None

# Modelos Pydantic para requests
class FloorProcessingRequest(BaseModel):
    floor_descriptions: List[str] = Field(..., description="Lista de descripciones de plantas en texto")

class FloorProcessingResponse(BaseModel):
    processed_floors: List[float] = Field(..., description="Plantas procesadas en formato numérico")
    floor_labels: List[str] = Field(..., description="Etiquetas legibles de las plantas")
    unprocessed: List[str] = Field(default=[], description="Plantas que no se pudieron procesar")

class ProjectVerificationRequest(BaseModel):
    is_existing_building: bool = Field(..., description="Si es edificio existente")
    primary_use: str = Field(..., description="Uso principal del edificio")
    has_secondary_uses: bool = Field(..., description="Si tiene usos secundarios")
    secondary_uses: List[Dict[str, Any]] = Field(default=[], description="Usos secundarios con plantas")
    files: List[str] = Field(..., description="Archivos de memoria y planos")

class ProjectVerificationResponse(BaseModel):
    project_id: str = Field(..., description="ID del proyecto")
    status: str = Field(..., description="Estado del procesamiento")
    applicable_normative: List[Dict[str, Any]] = Field(..., description="Normativa aplicable")
    processing_notes: List[str] = Field(default=[], description="Notas del procesamiento")

# Dependencias
async def get_db_manager():
    """Obtener instancia del gestor de base de datos."""
    global db_manager
    if db_manager is None:
        db_manager = MadridDatabaseManager()
        await db_manager.initialize()
    return db_manager

# Endpoints

@madrid_router.post("/process-floors", response_model=FloorProcessingResponse)
async def process_floor_descriptions(request: FloorProcessingRequest):
    """
    Procesar descripciones de plantas en formato texto a números.
    
    Convierte descripciones como "Planta Segunda", "Sótano 1", "Entreplanta" 
    a números: 2, -1, 0.5
    """
    try:
        logger.info(f"Procesando plantas: {request.floor_descriptions}")
        
        # Procesar plantas
        processed_floors = floor_processor.process_floor_list(request.floor_descriptions)
        
        # Generar etiquetas
        floor_labels = [floor_processor.get_floor_label(floor) for floor in processed_floors]
        
        # Identificar plantas no procesadas
        unprocessed = []
        for desc in request.floor_descriptions:
            if floor_processor.extract_floor_number(desc) is None:
                unprocessed.append(desc)
        
        response = FloorProcessingResponse(
            processed_floors=processed_floors,
            floor_labels=floor_labels,
            unprocessed=unprocessed
        )
        
        logger.info(f"Plantas procesadas: {len(processed_floors)} exitosas, {len(unprocessed)} fallidas")
        return response
        
    except Exception as e:
        logger.error(f"Error procesando plantas: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando plantas: {str(e)}")

@madrid_router.post("/verify-project", response_model=ProjectVerificationResponse)
async def verify_madrid_project(
    request: ProjectVerificationRequest,
    background_tasks: BackgroundTasks,
    db: MadridDatabaseManager = Depends(get_db_manager)
):
    """
    Verificar proyecto Madrid con normativa específica.
    
    Procesa un proyecto con datos específicos de Madrid y determina
    la normativa aplicable según el tipo de edificio y plantas.
    """
    try:
        logger.info(f"Iniciando verificación de proyecto Madrid: {request.primary_use}")
        
        # Generar ID de proyecto
        import uuid
        project_id = str(uuid.uuid4())
        
        # Procesar usos secundarios con plantas
        processed_secondary_uses = floor_processor.process_secondary_uses(request.secondary_uses)
        
        # Crear datos del proyecto
        project_data = {
            'project_id': project_id,
            'is_existing_building': request.is_existing_building,
            'primary_use': request.primary_use,
            'has_secondary_uses': request.has_secondary_uses,
            'secondary_uses': processed_secondary_uses,
            'files': request.files
        }
        
        # Obtener normativa aplicable
        applicable_normative = await db.get_applicable_normative(project_data)
        
        # Crear nodos en Neo4j (en background)
        background_tasks.add_task(
            db.create_project_normative_nodes,
            project_id,
            project_data
        )
        
        # Generar notas de procesamiento
        processing_notes = []
        processing_notes.append(f"Proyecto {project_id} creado")
        processing_notes.append(f"Uso principal: {request.primary_use}")
        processing_notes.append(f"Usos secundarios: {len(processed_secondary_uses)}")
        processing_notes.append(f"Normativa aplicable: {len(applicable_normative)} secciones")
        
        if request.is_existing_building:
            processing_notes.append("Incluye Documentos de Apoyo (edificio existente)")
        
        response = ProjectVerificationResponse(
            project_id=project_id,
            status="processing",
            applicable_normative=applicable_normative,
            processing_notes=processing_notes
        )
        
        logger.info(f"Verificación iniciada: {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error verificando proyecto Madrid: {e}")
        raise HTTPException(status_code=500, detail=f"Error verificando proyecto: {str(e)}")

@madrid_router.get("/normative-documents")
async def get_normative_documents(
    category: Optional[str] = None,
    building_type: Optional[str] = None
):
    """
    Obtener lista de documentos normativos disponibles.
    
    Args:
        category: Filtrar por categoría (cte, pgoum_general, pgoum_specific, support)
        building_type: Filtrar por tipo de edificio
    """
    try:
        # Escanear documentos si no están cargados
        if not normative_processor.processed_documents:
            normative_processor.scan_normative_documents()
        
        documents = list(normative_processor.processed_documents.values())
        
        # Aplicar filtros
        if category:
            documents = [doc for doc in documents if doc.category == category]
        
        if building_type:
            documents = [doc for doc in documents if doc.building_type == building_type]
        
        # Convertir a formato de respuesta
        response_data = []
        for doc in documents:
            response_data.append({
                'id': doc.id,
                'name': doc.name,
                'category': doc.category,
                'building_type': doc.building_type,
                'pages': doc.pages,
                'file_size': doc.file_size,
                'processed_at': doc.processed_at
            })
        
        return {
            'total_documents': len(response_data),
            'documents': response_data
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo documentos normativos: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo documentos: {str(e)}")

@madrid_router.get("/normative-index")
async def get_normative_index():
    """Obtener índice de normativa para consultas."""
    try:
        # Escanear documentos si no están cargados
        if not normative_processor.processed_documents:
            normative_processor.scan_normative_documents()
        
        index = normative_processor.create_normative_index()
        return index
        
    except Exception as e:
        logger.error(f"Error obteniendo índice normativo: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo índice: {str(e)}")

@madrid_router.post("/search-normative")
async def search_normative_content(
    query: str,
    building_types: List[str] = None,
    floors: List[float] = None,
    categories: List[str] = None,
    db: MadridDatabaseManager = Depends(get_db_manager)
):
    """
    Buscar contenido en la normativa.
    
    Args:
        query: Texto a buscar
        building_types: Tipos de edificio a filtrar
        floors: Plantas a filtrar
        categories: Categorías a filtrar
    """
    try:
        results = await db.search_normative_content(
            query=query,
            building_types=building_types,
            floors=floors,
            categories=categories
        )
        
        return {
            'query': query,
            'total_results': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error buscando normativa: {e}")
        raise HTTPException(status_code=500, detail=f"Error buscando normativa: {str(e)}")

@madrid_router.get("/project/{project_id}/normative")
async def get_project_normative(
    project_id: str,
    db: MadridDatabaseManager = Depends(get_db_manager)
):
    """Obtener normativa aplicable a un proyecto específico."""
    try:
        # Obtener datos del proyecto desde Neo4j
        # (Implementar según necesidad)
        
        # Por ahora, retornar estructura básica
        return {
            'project_id': project_id,
            'normative_sections': [],
            'status': 'not_implemented'
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo normativa del proyecto {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo normativa: {str(e)}")

@madrid_router.post("/initialize-normative")
async def initialize_normative_system(
    background_tasks: BackgroundTasks,
    db: MadridDatabaseManager = Depends(get_db_manager)
):
    """Inicializar sistema de normativa (procesar documentos)."""
    try:
        logger.info("Inicializando sistema de normativa Madrid...")
        
        # Escanear documentos
        documents = normative_processor.scan_normative_documents()
        
        # Almacenar en base de datos (en background)
        background_tasks.add_task(_store_documents_in_db, documents, db)
        
        return {
            'status': 'initializing',
            'total_documents': len(documents),
            'message': 'Sistema de normativa inicializándose en background'
        }
        
    except Exception as e:
        logger.error(f"Error inicializando sistema normativo: {e}")
        raise HTTPException(status_code=500, detail=f"Error inicializando: {str(e)}")

async def _store_documents_in_db(documents: Dict[str, Any], db: MadridDatabaseManager):
    """Almacenar documentos en base de datos (función de background)."""
    try:
        stored_count = 0
        for doc in documents.values():
            if await db.store_normative_document(doc):
                stored_count += 1
        
        logger.info(f"Documentos almacenados en BD: {stored_count}/{len(documents)}")
        
    except Exception as e:
        logger.error(f"Error almacenando documentos en BD: {e}")
