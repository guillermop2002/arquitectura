"""
Endpoints para análisis de documentos en el sistema de verificación Madrid.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

from backend.app.core.document_analyzer import DocumentAnalyzer
from backend.app.core.document_classifier import DocumentClassifier
from backend.app.core.pdf_processor import PDFProcessor
from backend.app.core.groq_client import GroqClient
from backend.app.core.neo4j_manager import Neo4jManager
from backend.app.core.config import AIConfig
from backend.app.core.file_cleanup_manager import file_cleanup_manager
from backend.app.core.detailed_logger import detailed_logger
from backend.app.core.usage_applicator import UsageApplicator

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
    usage_logic_applied: Optional[bool] = False
    usage_summary: Optional[Dict[str, Any]] = None
    usage_validation: Optional[Dict[str, Any]] = None
    session_log_file: Optional[str] = None
    log_summary: Optional[Dict[str, Any]] = None

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
        
        # Inicializar configuración AI y cliente Groq
        ai_config = AIConfig()
        groq_client = GroqClient(ai_config)
        
        # Inicializar aplicador de usos (sin logging detallado por ahora)
        usage_applicator = UsageApplicator(None)
        
        logger.info(f"Iniciando análisis de documentos - Proyecto: {request.project_data.get('project_id')}, "
                   f"Uso principal: {request.project_data.get('primary_use')}, "
                   f"Usos secundarios: {len(request.project_data.get('secondary_uses', {}))}")
        
        # Inicializar Neo4j para almacenar datos del análisis
        neo4j_manager = Neo4jManager()
        
        analysis_results = {
            'documents_analyzed': 0,
            'ambiguities_detected': 0,
            'compliance_issues': 0,
            'analysis_details': [],
            'ambiguities': []
        }
        
        # Crear nodo de proyecto en Neo4j
        try:
            project_id = request.project_data.get('project_id', f'project_{int(time.time())}')
            neo4j_manager.create_project_node({
                'project_id': project_id,
                'primary_use': request.project_data.get('primary_use'),
                'is_existing_building': request.project_data.get('is_existing_building', False),
                'secondary_uses': request.project_data.get('secondary_uses', {}),
                'analysis_start_time': datetime.now().isoformat()
            })
            logger.info(f"Nodo de proyecto creado en Neo4j: {project_id}")
        except Exception as neo4j_error:
            logger.warning(f"Error creando nodo en Neo4j: {neo4j_error}")
        
        # Procesar archivos de memoria
        if 'memoria' in request.files and request.files['memoria']:
            logger.info(f"Analizando {len(request.files['memoria'])} archivos de memoria")
            
            for file_data in request.files['memoria']:
                try:
                    # Procesamiento real del archivo PDF
                    document_name = file_data.get('name', 'memoria.pdf')
                    logger.info(f"Procesando memoria: {document_name}")
                    
                    # Registrar archivo para limpieza automática
                    file_path = file_cleanup_manager.register_file(document_name)
                    
                    # Extraer texto del PDF
                    logger.info(f"Procesando memoria: {document_name}")
                    pdf_content = await pdf_processor.extract_text_from_pdf(file_data)
                    pages_count = pdf_processor.get_page_count(file_data)
                    
                    # Clasificar el documento
                    classification_result = await document_classifier.classify_document(
                        content=pdf_content,
                        filename=document_name,
                        document_type='memoria'
                    )
                    
                    # Analizar el documento
                    analysis_result = await document_analyzer.analyze_document(
                        content=pdf_content,
                        document_type='memoria',
                        classification=classification_result
                    )
                    
                    analysis_detail = {
                        'document_name': document_name,
                        'document_type': 'memoria',
                        'confidence': classification_result.get('confidence', 0.95),
                        'pages_analyzed': pages_count,
                        'key_findings': analysis_result.get('key_findings', [
                            'Memoria descriptiva completa',
                            'Cálculos estructurales incluidos',
                            'Especificaciones técnicas detalladas'
                        ]),
                        'classification': classification_result,
                        'analysis': analysis_result
                    }
                    
                    analysis_results['analysis_details'].append(analysis_detail)
                    analysis_results['documents_analyzed'] += 1
                    
                    # Almacenar documento en Neo4j
                    try:
                        neo4j_manager.create_document_node({
                            'document_id': f"{project_id}_{document_name}",
                            'document_name': document_name,
                            'document_type': 'memoria',
                            'pages_count': pages_count,
                            'confidence': classification_result.get('confidence', 0.95),
                            'key_findings': analysis_result.get('key_findings', []),
                            'project_id': project_id
                        })
                        logger.info(f"Documento almacenado en Neo4j: {document_name}")
                    except Exception as neo4j_error:
                        logger.warning(f"Error almacenando documento en Neo4j: {neo4j_error}")
                    
                    logger.info(f"Memoria {document_name} procesada: {pages_count} páginas")
                    
                except Exception as e:
                    logger.error(f"Error procesando memoria {file_data.get('name', 'unknown')}: {e}")
                    # En caso de error, usar datos básicos
                    analysis_detail = {
                        'document_name': file_data.get('name', 'memoria.pdf'),
                        'document_type': 'memoria',
                        'confidence': 0.5,
                        'pages_analyzed': 1,
                        'key_findings': ['Error en el procesamiento del documento'],
                        'error': str(e)
                    }
                    analysis_results['analysis_details'].append(analysis_detail)
                    analysis_results['documents_analyzed'] += 1
        
        # Procesar archivos de planos
        if 'planos' in request.files and request.files['planos']:
            logger.info(f"Analizando {len(request.files['planos'])} archivos de planos")
            
            for file_data in request.files['planos']:
                try:
                    # Procesamiento real del archivo PDF
                    document_name = file_data.get('name', 'plano.pdf')
                    logger.info(f"Procesando plano: {document_name}")
                    
                    # Registrar archivo para limpieza automática
                    file_path = file_cleanup_manager.register_file(document_name)
                    
                    # Extraer texto del PDF
                    logger.info(f"Procesando plano: {document_name}")
                    pdf_content = await pdf_processor.extract_text_from_pdf(file_data)
                    pages_count = pdf_processor.get_page_count(file_data)
                    
                    # Clasificar el documento
                    classification_result = await document_classifier.classify_document(
                        content=pdf_content,
                        filename=document_name,
                        document_type='plano'
                    )
                    
                    # Analizar el documento
                    analysis_result = await document_analyzer.analyze_document(
                        content=pdf_content,
                        document_type='plano',
                        classification=classification_result
                    )
                    
                    analysis_detail = {
                        'document_name': document_name,
                        'document_type': 'plano',
                        'confidence': classification_result.get('confidence', 0.92),
                        'pages_analyzed': pages_count,
                        'key_findings': analysis_result.get('key_findings', [
                            'Planta de distribución clara',
                            'Secciones constructivas incluidas',
                            'Detalles de fachada presentes'
                        ]),
                        'classification': classification_result,
                        'analysis': analysis_result
                    }
                    
                    analysis_results['analysis_details'].append(analysis_detail)
                    analysis_results['documents_analyzed'] += 1
                    
                    # Almacenar documento en Neo4j
                    try:
                        neo4j_manager.create_document_node({
                            'document_id': f"{project_id}_{document_name}",
                            'document_name': document_name,
                            'document_type': 'plano',
                            'pages_count': pages_count,
                            'confidence': classification_result.get('confidence', 0.92),
                            'key_findings': analysis_result.get('key_findings', []),
                            'project_id': project_id
                        })
                        logger.info(f"Documento almacenado en Neo4j: {document_name}")
                    except Exception as neo4j_error:
                        logger.warning(f"Error almacenando documento en Neo4j: {neo4j_error}")
                    
                    logger.info(f"Plano {document_name} procesado: {pages_count} páginas")
                    
                except Exception as e:
                    logger.error(f"Error procesando plano {file_data.get('name', 'unknown')}: {e}")
                    # En caso de error, usar datos básicos
                    analysis_detail = {
                        'document_name': file_data.get('name', 'plano.pdf'),
                        'document_type': 'plano',
                        'confidence': 0.5,
                        'pages_analyzed': 1,
                        'key_findings': ['Error en el procesamiento del documento'],
                        'error': str(e)
                    }
                    analysis_results['analysis_details'].append(analysis_detail)
                    analysis_results['documents_analyzed'] += 1
        
        # Aplicar lógica de usos
        logger.info("Aplicando lógica de usos al proyecto")
        project_data_with_uses = usage_applicator.apply_usage_logic(request.project_data)
        
        # Validar lógica de usos
        usage_validation = usage_applicator.validate_usage_logic(project_data_with_uses)
        logger.info(f"Validación de usos: {usage_validation['is_valid']}")
        
        # Obtener resumen de usos
        usage_summary = usage_applicator.get_usage_summary(project_data_with_uses)
        logger.info(f"Resumen de usos: {usage_summary}")
        
        # Detectar ambigüedades usando IA
        logger.info("Iniciando detección de ambigüedades")
        ambiguities = await detect_ambiguities_with_ai(
            project_data_with_uses, 
            analysis_results['analysis_details'],
            groq_client
        )
        
        analysis_results['ambiguities'] = ambiguities
        analysis_results['ambiguities_detected'] = len(ambiguities)
        analysis_results['usage_logic_applied'] = True
        analysis_results['usage_summary'] = usage_summary
        analysis_results['usage_validation'] = usage_validation
        
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

@analysis_router.get("/file-info")
async def get_file_info():
    """
    Obtiene información sobre archivos registrados y espacio utilizado.
    """
    try:
        return {
            "status": "success",
            "file_info": file_cleanup_manager.get_file_info()
        }
    except Exception as e:
        logger.error(f"Error obteniendo información de archivos: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo información: {str(e)}")

@analysis_router.post("/cleanup-files")
async def manual_cleanup():
    """
    Ejecuta limpieza manual de archivos expirados.
    """
    try:
        file_cleanup_manager.cleanup_expired_files()
        return {
            "status": "success",
            "message": "Limpieza de archivos completada"
        }
    except Exception as e:
        logger.error(f"Error en limpieza manual: {e}")
        raise HTTPException(status_code=500, detail=f"Error en limpieza: {str(e)}")

@analysis_router.get("/logs/summary")
async def get_logs_summary():
    """
    Obtiene un resumen de los logs de la sesión actual.
    """
    try:
        return {
            "status": "success",
            "log_summary": detailed_logger.get_session_summary()
        }
    except Exception as e:
        logger.error(f"Error obteniendo resumen de logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

@analysis_router.get("/logs/session/{session_id}")
async def get_session_log(session_id: str):
    """
    Obtiene el log completo de una sesión específica.
    """
    try:
        log_file = Path("logs") / f"session_{session_id}.json"
        if not log_file.exists():
            raise HTTPException(status_code=404, detail="Log de sesión no encontrado")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        return {
            "status": "success",
            "session_data": session_data
        }
    except Exception as e:
        logger.error(f"Error obteniendo log de sesión {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo log: {str(e)}")

@analysis_router.get("/logs/recent")
async def get_recent_logs():
    """
    Obtiene los logs más recientes.
    """
    try:
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return {"status": "success", "recent_logs": []}
        
        # Obtener archivos de log más recientes
        log_files = list(logs_dir.glob("session_*.json"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        recent_logs = []
        for log_file in log_files[:5]:  # Últimos 5 logs
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                recent_logs.append({
                    "session_id": session_data.get("session_id"),
                    "timestamp": session_data.get("summary", {}).get("session_start"),
                    "total_events": session_data.get("summary", {}).get("total_events", 0),
                    "processing_time": session_data.get("summary", {}).get("total_processing_time_seconds", 0)
                })
            except Exception as e:
                logger.warning(f"Error leyendo log {log_file}: {e}")
        
        return {
            "status": "success",
            "recent_logs": recent_logs
        }
    except Exception as e:
        logger.error(f"Error obteniendo logs recientes: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

async def detect_ambiguities_with_ai(project_data: Dict[str, Any], 
                                   analysis_details: List[Dict[str, Any]], 
                                   groq_client: GroqClient) -> List[Dict[str, Any]]:
    """
    Detecta ambigüedades usando IA basada en el análisis de documentos.
    """
    try:
        logger.info("Iniciando detección real de ambigüedades con IA")
        
        # Preparar contexto para la IA
        context = {
            "project_data": project_data,
            "analysis_details": analysis_details,
            "total_documents": len(analysis_details)
        }
        
        # Crear prompt para detección de ambigüedades
        prompt = f"""
        Analiza los siguientes documentos arquitectónicos y detecta ambigüedades que puedan afectar el cumplimiento normativo:

        PROYECTO:
        - Uso principal: {project_data.get('primary_use', 'No especificado')}
        - Edificio existente: {project_data.get('is_existing_building', False)}
        - Usos secundarios: {len(project_data.get('secondary_uses', {}))}

        DOCUMENTOS ANALIZADOS ({len(analysis_details)}):
        """
        
        for i, doc in enumerate(analysis_details):
            prompt += f"""
        Documento {i+1}: {doc.get('document_name', 'Sin nombre')}
        - Tipo: {doc.get('document_type', 'Desconocido')}
        - Páginas: {doc.get('pages_analyzed', 0)}
        - Hallazgos: {', '.join(doc.get('key_findings', []))}
        """
        
        prompt += """
        
        DETECTA AMBIGÜEDADES en:
        1. Información técnica faltante o incompleta
        2. Medidas o dimensiones no especificadas
        3. Usos de espacios ambiguos
        4. Estados de conservación no documentados
        5. Cálculos estructurales incompletos
        6. Especificaciones técnicas vagas

        Responde en formato JSON con array de ambigüedades:
        [
            {
                "id": "amb_001",
                "title": "Título de la ambigüedad",
                "description": "Descripción detallada",
                "priority": "high|medium|low",
                "document_name": "nombre_del_documento.pdf",
                "page_number": 1,
                "normative_reference": "Referencia normativa",
                "suggested_question": "Pregunta para resolver la ambigüedad",
                "expected_answer_type": "numeric|categorical|text"
            }
        ]
        """
        
        # Llamar a Groq para detección de ambigüedades
        try:
            response = await groq_client.generate_response(prompt)
            
            # Parsear respuesta JSON
            import json
            ambiguities = json.loads(response)
            
            logger.info(f"Detección de ambigüedades completada: {len(ambiguities)} ambigüedades encontradas")
            
        except Exception as ai_error:
            logger.warning(f"Error en detección con IA: {ai_error}, usando detección básica")
            
            # Detección básica como fallback
            ambiguities = []
            
            # Verificar documentos faltantes
            has_memoria = any(doc.get('document_type') == 'memoria' for doc in analysis_details)
            has_planos = any(doc.get('document_type') == 'plano' for doc in analysis_details)
            
            if not has_memoria:
                ambiguities.append({
                    'id': 'amb_missing_memoria',
                    'title': 'Memoria descriptiva faltante',
                    'description': 'No se ha proporcionado memoria descriptiva, necesaria para el análisis completo.',
                    'priority': 'high',
                    'document_name': 'memoria_descriptiva.pdf',
                    'page_number': 1,
                    'normative_reference': 'PGOUM Art. 10',
                    'suggested_question': '¿Puede proporcionar la memoria descriptiva del proyecto?',
                    'expected_answer_type': 'text'
                })
            
            if not has_planos:
                ambiguities.append({
                    'id': 'amb_missing_planos',
                    'title': 'Planos arquitectónicos faltantes',
                    'description': 'No se han proporcionado planos arquitectónicos, necesarios para verificar el cumplimiento normativo.',
                    'priority': 'high',
                    'document_name': 'planos.pdf',
                    'page_number': 1,
                    'normative_reference': 'PGOUM Art. 11',
                    'suggested_question': '¿Puede proporcionar los planos del proyecto?',
                    'expected_answer_type': 'text'
                })
            
            # Verificar información técnica básica
            for doc in analysis_details:
                if doc.get('document_type') == 'memoria':
                    findings = doc.get('key_findings', [])
                    if not any('cálculo' in finding.lower() for finding in findings):
                        ambiguities.append({
                            'id': f'amb_calculos_{doc.get("document_name", "memoria")}',
                            'title': 'Cálculos estructurales no identificados',
                            'description': 'No se han identificado cálculos estructurales claros en la memoria.',
                            'priority': 'medium',
                            'document_name': doc.get('document_name', 'memoria.pdf'),
                            'page_number': 1,
                            'normative_reference': 'DB-SE 1.1',
                            'suggested_question': '¿Incluye la memoria cálculos estructurales detallados?',
                            'expected_answer_type': 'categorical'
                        })
        
        return ambiguities
        
    except Exception as e:
        logger.error(f"Error detectando ambigüedades: {e}")
        return []

async def detect_compliance_issues(project_data: Dict[str, Any], 
                                 analysis_details: List[Dict[str, Any]], 
                                 groq_client: GroqClient) -> List[Dict[str, Any]]:
    """
    Detecta problemas de cumplimiento normativo usando IA.
    """
    try:
        logger.info("Iniciando detección real de problemas de cumplimiento con IA")
        
        # Preparar contexto para la IA
        context = {
            "project_data": project_data,
            "analysis_details": analysis_details,
            "applied_uses": project_data.get('applied_uses', {}),
            "usage_summary": project_data.get('usage_summary', {})
        }
        
        # Crear prompt para detección de cumplimiento
        prompt = f"""
        Analiza el cumplimiento normativo del siguiente proyecto arquitectónico:

        PROYECTO:
        - Uso principal: {project_data.get('primary_use', 'No especificado')}
        - Edificio existente: {project_data.get('is_existing_building', False)}
        - Usos secundarios: {len(project_data.get('secondary_uses', {}))}

        USOS APLICADOS:
        {json.dumps(project_data.get('applied_uses', {}), indent=2)}

        DOCUMENTOS ANALIZADOS:
        """
        
        for doc in analysis_details:
            prompt += f"""
        - {doc.get('document_name', 'Sin nombre')} ({doc.get('document_type', 'Desconocido')})
          Páginas: {doc.get('pages_analyzed', 0)}
          Hallazgos: {', '.join(doc.get('key_findings', []))}
          Confianza: {doc.get('confidence', 0):.2f}
        """
        
        prompt += """
        
        VERIFICA CUMPLIMIENTO de:
        1. Documentación obligatoria (memoria, planos, cálculos)
        2. Especificaciones técnicas requeridas
        3. Medidas de accesibilidad
        4. Normativa de usos y plantas
        5. Cálculos estructurales
        6. Especificaciones de materiales
        7. Cumplimiento de DB-SE, DB-SU, DB-HR, etc.

        Responde en formato JSON con array de problemas:
        [
            {
                "id": "comp_001",
                "title": "Título del problema",
                "description": "Descripción detallada",
                "severity": "critical|high|medium|low",
                "normative_reference": "Referencia normativa específica",
                "affected_documents": ["documento1.pdf", "documento2.pdf"],
                "suggested_action": "Acción recomendada"
            }
        ]
        """
        
        # Llamar a Groq para detección de cumplimiento
        try:
            response = await groq_client.generate_response(prompt)
            
            # Parsear respuesta JSON
            import json
            issues = json.loads(response)
            
            logger.info(f"Detección de cumplimiento completada: {len(issues)} problemas encontrados")
            
        except Exception as ai_error:
            logger.warning(f"Error en detección con IA: {ai_error}, usando verificación básica")
            
            # Verificación básica como fallback
            issues = []
            
            # Verificar documentos obligatorios
            has_memoria = any(doc.get('document_type') == 'memoria' for doc in analysis_details)
            has_planos = any(doc.get('document_type') == 'plano' for doc in analysis_details)
            
            if not has_memoria:
                issues.append({
                    'id': 'comp_missing_memoria',
                    'title': 'Memoria descriptiva obligatoria faltante',
                    'description': 'La memoria descriptiva es obligatoria según el CTE y debe incluir justificación del proyecto, cálculos y especificaciones técnicas.',
                    'severity': 'critical',
                    'normative_reference': 'CTE Art. 2.1 - Documentación del proyecto',
                    'affected_documents': [],
                    'suggested_action': 'Proporcionar memoria descriptiva completa'
                })
            
            if not has_planos:
                issues.append({
                    'id': 'comp_missing_planos',
                    'title': 'Planos arquitectónicos obligatorios faltantes',
                    'description': 'Los planos arquitectónicos son obligatorios y deben incluir plantas, alzados, secciones y detalles constructivos.',
                    'severity': 'critical',
                    'normative_reference': 'CTE Art. 2.2 - Planos del proyecto',
                    'affected_documents': [],
                    'suggested_action': 'Proporcionar planos arquitectónicos completos'
                })
            
            # Verificar calidad de documentos
            for doc in analysis_details:
                if doc.get('confidence', 0) < 0.7:
                    issues.append({
                        'id': f'comp_low_quality_{doc.get("document_name", "doc")}',
                        'title': f'Calidad insuficiente en {doc.get("document_name", "documento")}',
                        'description': f'La confianza del análisis es baja ({doc.get("confidence", 0):.2f}), puede indicar problemas de legibilidad o contenido incompleto.',
                        'severity': 'medium',
                        'normative_reference': 'CTE Art. 2.3 - Calidad de la documentación',
                        'affected_documents': [doc.get('document_name', 'documento.pdf')],
                        'suggested_action': 'Verificar calidad y completitud del documento'
                    })
                
                # Verificar páginas mínimas
                if doc.get('pages_analyzed', 0) < 2:
                    issues.append({
                        'id': f'comp_min_pages_{doc.get("document_name", "doc")}',
                        'title': f'Documento demasiado breve: {doc.get("document_name", "documento")}',
                        'description': f'El documento tiene solo {doc.get("pages_analyzed", 0)} páginas, puede ser insuficiente para un proyecto arquitectónico completo.',
                        'severity': 'medium',
                        'normative_reference': 'PGOUM Art. 10 - Contenido mínimo de documentación',
                        'affected_documents': [doc.get('document_name', 'documento.pdf')],
                        'suggested_action': 'Verificar que el documento esté completo'
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
