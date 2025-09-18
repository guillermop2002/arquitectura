"""
Endpoints para análisis de documentos en el sistema de verificación Madrid.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime, timedelta

from backend.app.core.document_analyzer import DocumentAnalyzer
from backend.app.core.document_classifier import DocumentClassifier
from backend.app.core.pdf_processor import PDFProcessor
from backend.app.core.groq_client import GroqClient
from backend.app.core.neo4j_manager import Neo4jManager

logger = logging.getLogger(__name__)

# Router para análisis de documentos
analysis_router = APIRouter(prefix="/api/madrid/analysis", tags=["Document Analysis"])

class DocumentAnalysisRequest(BaseModel):
    project_data: Dict[str, Any]
    files: Dict[str, List[Dict[str, Any]]]

class DocumentAnalysisResponse(BaseModel):
    status: str
    documents_analyzed: int
    ambiguities_detected: int
    compliance_issues: int
    analysis_details: List[Dict[str, Any]]
    ambiguities: List[Dict[str, Any]]
    processing_time: float
    timestamp: str

@analysis_router.post("/analyze-documents", response_model=DocumentAnalysisResponse)
async def analyze_documents(request: DocumentAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analiza documentos para detectar ambigüedades y problemas de cumplimiento.
    """
    try:
        start_time = datetime.now()
        
        logger.info(f"Iniciando análisis de documentos para proyecto: {request.project_data.get('project_id', 'unknown')}")
        
        # Inicializar componentes
        pdf_processor = PDFProcessor()
        document_classifier = DocumentClassifier()
        document_analyzer = DocumentAnalyzer()
        groq_client = GroqClient()
        neo4j_manager = Neo4jManager()
        
        analysis_results = {
            'documents_analyzed': 0,
            'ambiguities_detected': 0,
            'compliance_issues': 0,
            'analysis_details': [],
            'ambiguities': []
        }
        
        # Procesar archivos de memoria
        if 'memoria' in request.files and request.files['memoria']:
            logger.info(f"Analizando {len(request.files['memoria'])} archivos de memoria")
            
            for file_data in request.files['memoria']:
                try:
                    # Simular procesamiento de archivo (en producción sería real)
                    analysis_detail = {
                        'document_name': file_data.get('name', 'memoria.pdf'),
                        'document_type': 'memoria',
                        'confidence': 0.95,
                        'pages_analyzed': 10,
                        'key_findings': [
                            'Memoria descriptiva completa',
                            'Cálculos estructurales incluidos',
                            'Especificaciones técnicas detalladas'
                        ]
                    }
                    
                    analysis_results['analysis_details'].append(analysis_detail)
                    analysis_results['documents_analyzed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando memoria {file_data.get('name', 'unknown')}: {e}")
        
        # Procesar archivos de planos
        if 'planos' in request.files and request.files['planos']:
            logger.info(f"Analizando {len(request.files['planos'])} archivos de planos")
            
            for file_data in request.files['planos']:
                try:
                    # Simular procesamiento de archivo (en producción sería real)
                    analysis_detail = {
                        'document_name': file_data.get('name', 'plano.pdf'),
                        'document_type': 'plano',
                        'confidence': 0.92,
                        'pages_analyzed': 5,
                        'key_findings': [
                            'Planta de distribución clara',
                            'Secciones constructivas incluidas',
                            'Detalles de fachada presentes'
                        ]
                    }
                    
                    analysis_results['analysis_details'].append(analysis_detail)
                    analysis_results['documents_analyzed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando plano {file_data.get('name', 'unknown')}: {e}")
        
        # Detectar ambigüedades usando IA
        ambiguities = await detect_ambiguities_with_ai(
            request.project_data, 
            analysis_results['analysis_details'],
            groq_client
        )
        
        analysis_results['ambiguities'] = ambiguities
        analysis_results['ambiguities_detected'] = len(ambiguities)
        
        # Detectar problemas de cumplimiento
        compliance_issues = await detect_compliance_issues(
            request.project_data,
            analysis_results['analysis_details'],
            groq_client
        )
        
        analysis_results['compliance_issues'] = len(compliance_issues)
        
        # Guardar en Neo4j
        await save_analysis_to_neo4j(
            request.project_data,
            analysis_results,
            neo4j_manager
        )
        
        # Calcular tiempo de procesamiento
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = DocumentAnalysisResponse(
            status="completed",
            documents_analyzed=analysis_results['documents_analyzed'],
            ambiguities_detected=analysis_results['ambiguities_detected'],
            compliance_issues=analysis_results['compliance_issues'],
            analysis_details=analysis_results['analysis_details'],
            ambiguities=analysis_results['ambiguities'],
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Análisis completado: {analysis_results['documents_analyzed']} documentos, "
                   f"{analysis_results['ambiguities_detected']} ambigüedades, "
                   f"{analysis_results['compliance_issues']} problemas de cumplimiento")
        
        return response
        
    except Exception as e:
        logger.error(f"Error en análisis de documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

async def detect_ambiguities_with_ai(project_data: Dict[str, Any], 
                                   analysis_details: List[Dict[str, Any]], 
                                   groq_client: GroqClient) -> List[Dict[str, Any]]:
    """
    Detecta ambigüedades usando IA basada en el análisis de documentos.
    """
    try:
        # Simular detección de ambigüedades (en producción sería real con Groq)
        ambiguities = []
        
        # Ambigüedad de ejemplo basada en el tipo de proyecto
        if project_data.get('primary_use') == 'residencial':
            ambiguities.append({
                'id': 'amb_001',
                'title': 'Altura de entreplanta no especificada',
                'description': 'La altura de la entreplanta no está claramente definida en los planos. Esto puede afectar el cumplimiento de la normativa de accesibilidad.',
                'priority': 'high',
                'document_name': 'plano_planta.pdf',
                'page_number': 2,
                'normative_reference': 'DB-SU 1.1',
                'suggested_question': '¿Cuál es la altura libre de la entreplanta?',
                'expected_answer_type': 'numeric'
            })
        
        if project_data.get('is_existing_building', False):
            ambiguities.append({
                'id': 'amb_002',
                'title': 'Estado de conservación no documentado',
                'description': 'No se ha documentado el estado de conservación del edificio existente, necesario para aplicar la normativa específica.',
                'priority': 'medium',
                'document_name': 'memoria_descriptiva.pdf',
                'page_number': 5,
                'normative_reference': 'PGOUM Art. 15',
                'suggested_question': '¿Cuál es el estado de conservación del edificio existente?',
                'expected_answer_type': 'categorical'
            })
        
        # Ambigüedad genérica
        ambiguities.append({
            'id': 'amb_003',
            'title': 'Uso de espacios no definido claramente',
            'description': 'Algunos espacios en los planos no tienen un uso claramente definido, lo que puede generar dudas sobre la normativa aplicable.',
            'priority': 'low',
            'document_name': 'plano_distribucion.pdf',
            'page_number': 1,
            'normative_reference': 'PGOUM Art. 12',
            'suggested_question': '¿Cuál es el uso específico de los espacios sin etiquetar?',
            'expected_answer_type': 'text'
        })
        
        return ambiguities
        
    except Exception as e:
        logger.error(f"Error detectando ambigüedades: {e}")
        return []

async def detect_compliance_issues(project_data: Dict[str, Any], 
                                 analysis_details: List[Dict[str, Any]], 
                                 groq_client: GroqClient) -> List[Dict[str, Any]]:
    """
    Detecta problemas de cumplimiento normativo.
    """
    try:
        # Simular detección de problemas de cumplimiento
        issues = []
        
        # Verificar si hay memoria descriptiva
        has_memoria = any(detail['document_type'] == 'memoria' for detail in analysis_details)
        if not has_memoria:
            issues.append({
                'id': 'comp_001',
                'title': 'Falta memoria descriptiva',
                'description': 'No se ha detectado una memoria descriptiva completa del proyecto.',
                'severity': 'critical',
                'normative_reference': 'CTE Art. 2.1'
            })
        
        # Verificar si hay planos
        has_planos = any(detail['document_type'] == 'plano' for detail in analysis_details)
        if not has_planos:
            issues.append({
                'id': 'comp_002',
                'title': 'Faltan planos arquitectónicos',
                'description': 'No se han detectado planos arquitectónicos del proyecto.',
                'severity': 'critical',
                'normative_reference': 'CTE Art. 2.2'
            })
        
        return issues
        
    except Exception as e:
        logger.error(f"Error detectando problemas de cumplimiento: {e}")
        return []

@analysis_router.get("/analysis-status/{project_id}")
async def get_analysis_status(project_id: str):
    """
    Obtiene el estado del análisis de documentos para un proyecto.
    """
    try:
        # En una implementación real, esto consultaría la base de datos
        return {
            "project_id": project_id,
            "status": "completed",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del análisis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def save_analysis_to_neo4j(project_data: Dict[str, Any], 
                                analysis_results: Dict[str, Any], 
                                neo4j_manager: Neo4jManager):
    """
    Guarda el análisis de documentos en Neo4j.
    """
    try:
        project_id = project_data.get('project_id', 'unknown')
        
        # Crear nodo del proyecto
        project_node_id = neo4j_manager.create_project_node({
            'id': project_id,
            'name': f"Proyecto {project_id}",
            'type': project_data.get('primary_use', 'residencial'),
            'location': 'Madrid',
            'status': 'analyzing'
        })
        
        # Crear nodos de documentos
        for detail in analysis_results.get('analysis_details', []):
            document_node_id = neo4j_manager.create_document_node({
                'id': f"{project_id}_{detail['document_name']}",
                'name': detail['document_name'],
                'type': detail['document_type'],
                'file_path': f"/uploads/{detail['document_name']}",
                'pages': detail.get('pages_analyzed', 0),
                'size': 0,  # Tamaño estimado
                'extracted_text': str(detail.get('key_findings', []))
            }, project_id)
            
            # Crear relación proyecto -> documento
            neo4j_manager.create_relationship(
                project_node_id,
                document_node_id,
                'contains',
                {'created_at': datetime.now().isoformat()}
            )
        
        # Crear nodos de ambigüedades
        for ambiguity in analysis_results.get('ambiguities', []):
            ambiguity_node_id = neo4j_manager.create_issue_node({
                'id': f"{project_id}_{ambiguity['id']}",
                'title': ambiguity['title'],
                'description': ambiguity['description'],
                'priority': ambiguity['priority'],
                'status': 'pending',
                'type': 'ambiguity'
            }, project_id)
            
            # Crear relación proyecto -> ambigüedad
            neo4j_manager.create_relationship(
                project_node_id,
                ambiguity_node_id,
                'generates',
                {'created_at': datetime.now().isoformat()}
            )
        
        logger.info(f"Análisis guardado en Neo4j para proyecto {project_id}")
        
    except Exception as e:
        logger.error(f"Error guardando análisis en Neo4j: {e}")

@analysis_router.post("/cleanup-old-data")
async def cleanup_old_neo4j_data(days_old: int = 30):
    """
    Limpia datos antiguos de Neo4j.
    """
    try:
        neo4j_manager = Neo4jManager()
        
        # Calcular fecha de corte
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Limpiar proyectos antiguos
        cleaned_count = neo4j_manager.cleanup_old_projects(cutoff_date)
        
        return {
            "status": "success",
            "cleaned_projects": cleaned_count,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"Limpieza completada: {cleaned_count} proyectos eliminados"
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de Neo4j: {e}")
        raise HTTPException(status_code=500, detail=str(e))
