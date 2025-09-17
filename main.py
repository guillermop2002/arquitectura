"""
Main FastAPI application for building verification system.
Handles application bootstrap, configuration, and API endpoints.
"""

import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core modules
from backend.app.core.config import get_config
from backend.app.core.logging_config import get_logger, initialize_logging
from backend.app.core.file_manager import FileManager
from backend.app.core.production_project_analyzer import ProductionProjectAnalyzer
from backend.app.core.enhanced_project_analyzer_v2 import EnhancedProjectAnalyzerV2
from backend.app.core.enhanced_project_analyzer_v3 import EnhancedProjectAnalyzerV3
from backend.app.core.enhanced_project_analyzer_v4 import EnhancedProjectAnalyzerV4
from backend.app.core.data_loader import DataLoader
from backend.app.core.state_manager import StateManager
from backend.app.core.enhanced_main_endpoints import EnhancedMainEndpoints
from backend.app.core.rasa_integration import RasaIntegration
from backend.app.core.context_manager import ContextManager, ProjectContext
from backend.app.core.cleanup_manager import CleanupManager

# Initialize logging
initialize_logging()
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Building Verification System",
    description="AI-powered building project verification for Madrid",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config = get_config()
file_manager = FileManager()
project_analyzer = ProductionProjectAnalyzer()
enhanced_analyzer = EnhancedProjectAnalyzerV2()  # Fase 1: PLN Avanzado
enhanced_analyzer_v3 = EnhancedProjectAnalyzerV3()  # Fase 2: Visión por Computador
enhanced_analyzer_v4 = EnhancedProjectAnalyzerV4()  # Fase 3: Sistema de Preguntas Inteligentes
data_loader = DataLoader()
state_manager = StateManager()

# Initialize Fase 4: Sistema Conversacional Avanzado
rasa_integration = RasaIntegration(config)
context_manager = ContextManager(config)

# Initialize cleanup manager
cleanup_manager = CleanupManager()

# Initialize enhanced endpoints
enhanced_endpoints = EnhancedMainEndpoints(app)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # Create necessary directories
        directories = [
            config.file.upload_folder,
            'temp',
            'logs'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Initialize Redis connection
        await state_manager._initialize()
        
        # Clean up old jobs and files
        await state_manager.cleanup_old_jobs()
        await file_manager.cleanup_old_files()
        
        logger.info("=" * 60)
        logger.info("BUILDING VERIFICATION SYSTEM")
        logger.info("=" * 60)
        logger.info(f"Version: {config.version}")
        logger.info(f"Environment: {config.environment}")
        logger.info(f"Debug mode: {config.debug}")
        logger.info(f"Upload folder: {config.file.upload_folder}")
        logger.info(f"Max file size: {config.file.max_file_size / (1024*1024):.1f} MB")
        logger.info(f"Max files: {config.file.max_files}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.critical(f"Failed to initialize application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await state_manager.close()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main frontend interface."""
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Redis connection
        redis_status = await state_manager.health_check()
        
        # Test file manager
        file_manager_status = await file_manager.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "redis": redis_status,
                "file_manager": file_manager_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of a specific job."""
    try:
        job_data = await file_manager.get_job_data(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found or expired")
        
        return {
            "job_id": job_id,
            "status": job_data.get('status', 'unknown'),
            "processing_complete": job_data.get('processing_complete', False),
            "created_at": job_data.get('created_at'),
            "updated_at": job_data.get('updated_at'),
            "total_pages": job_data.get('total_pages', 0),
            "files_processed": len(job_data.get('extracted_data', {}))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup")
async def cleanup_old_files():
    """Manually trigger cleanup of old files."""
    try:
        cleaned_count = await file_manager.cleanup_old_files()
        
        return {
            "status": "success",
            "cleaned_files": cleaned_count,
            "message": f"Cleaned up {cleaned_count} old job directories"
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup/project/{project_id}")
async def cleanup_project(project_id: str, force: bool = False):
    """Limpiar datos de un proyecto específico."""
    try:
        result = cleanup_manager.cleanup_project_data(project_id, force)
        
        return {
            "status": "success",
            "project_id": project_id,
            "neo4j_cleaned": result['neo4j_cleaned'],
            "cache_cleaned": result['cache_cleaned'],
            "temp_files_cleaned": result['temp_files_cleaned'],
            "space_freed_mb": result['space_freed_mb'],
            "errors": result['errors']
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup/old-data")
async def cleanup_old_data(force: bool = False):
    """Limpiar datos antiguos según configuración de retención."""
    try:
        result = cleanup_manager.cleanup_old_data(force)
        
        return {
            "status": "success",
            "neo4j_cleaned": result['neo4j_cleaned'],
            "cache_cleaned": result['cache_cleaned'],
            "temp_files_cleaned": result['temp_files_cleaned'],
            "projects_deleted": result['projects_deleted'],
            "space_freed_mb": result['space_freed_mb'],
            "errors": result['errors']
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup/force-all")
async def force_cleanup_all():
    """Forzar limpieza completa de todo el sistema."""
    try:
        result = cleanup_manager.force_cleanup_all()
        
        return {
            "status": "success",
            "neo4j_cleaned": result['neo4j_cleaned'],
            "cache_cleaned": result['cache_cleaned'],
            "temp_files_cleaned": result['temp_files_cleaned'],
            "projects_deleted": result['projects_deleted'],
            "space_freed_mb": result['space_freed_mb'],
            "errors": result['errors']
        }
        
    except Exception as e:
        logger.error(f"Error in force cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cleanup/status")
async def get_cleanup_status():
    """Obtener estado actual del sistema de limpieza."""
    try:
        status = cleanup_manager.get_cleanup_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting cleanup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify")
async def verify_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    is_existing_building: bool = Form(False)
):
    """
    Phase 1: File upload and Annex I pre-check.
    Centralized processing - files are processed once and stored.
    """
    try:
        # Validate files
        if not files or len(files) > config.file.max_files:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum {config.file.max_files} files allowed"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Process files with centralized file manager (OCR happens only once)
        job_data = await file_manager.process_uploaded_files(files, job_id, is_existing_building)
        
        # Store job state in Redis for quick access
        await state_manager.create_job(job_id, {
            "status": "processed",
            "is_existing_building": is_existing_building,
            "created_at": datetime.now().isoformat()
        })
        
        # Perform Annex I pre-check using advanced analyzer
        anexo_i_result = enhanced_analyzer.check_annexe_i_compliance(job_data['extracted_data'])
        
        # Update job with results
        await file_manager.update_job_data(job_id, {
            "anexo_i_result": anexo_i_result,
            "status": "anexo_i_complete"
        })
        
        return {
            "job_id": job_id,
            "status": anexo_i_result['status'],
            "message": "All required Annex I documents found" if anexo_i_result['status'] == 'completo' else "Some required Annex I documents are missing",
            "found_documents": anexo_i_result['found_documents'],
            "missing_documents": anexo_i_result.get('missing_documents', []),
            "confidence": anexo_i_result['confidence']
        }
        
    except Exception as e:
        logger.error(f"Error in Phase 1 verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/continue-verification")
async def continue_verification(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    is_existing_building: bool = Form(False)
):
    """
    Phase 2: Complete normative verification.
    Uses already processed data - no file re-upload needed.
    """
    try:
        # Get job data from file manager
        job_data = await file_manager.get_job_data(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found or expired")
        
        # Check if processing is complete
        if not job_data.get('processing_complete', False):
            raise HTTPException(status_code=400, detail="Job processing not complete")
        
        extracted_data = job_data.get('extracted_data', {})
        if not extracted_data:
            raise HTTPException(status_code=400, detail="No extracted data found")
        
        # Extract project data using advanced analyzer
        project_data = enhanced_analyzer.extract_project_data(extracted_data)
        
        # Load normative documents
        normative_docs = data_loader.load_normative_documents(
            project_data.building_use, 
            is_existing_building
        )
        
        # Perform complete compliance check using advanced analyzer
        compliance_result = enhanced_analyzer.check_complete_compliance(
            project_data, 
            extracted_data, 
            normative_docs
        )
        
        # Generate questions using advanced analyzer
        questions = enhanced_analyzer.generate_questions(extracted_data, compliance_result['issues'])
        
        # Update job with results
        await file_manager.update_job_data(job_id, {
            "project_data": project_data.dict(),
            "compliance_result": {
                "issues": [issue.dict() for issue in compliance_result['issues']],
                "confidence": compliance_result['confidence']
            },
            "questions": questions,
            "status": "verification_complete"
        })
        
        return {
            "job_id": job_id,
            "status": "success",
            "project_data": project_data.dict(),
            "issues": [issue.dict() for issue in compliance_result['issues']],
            "questions": questions,
            "confidence": compliance_result['confidence'],
            "summary": {
                "total_issues": len(compliance_result['issues']),
                "high_severity": len([i for i in compliance_result['issues'] if i.severity == 'HIGH']),
                "medium_severity": len([i for i in compliance_result['issues'] if i.severity == 'MEDIUM']),
                "low_severity": len([i for i in compliance_result['issues'] if i.severity == 'LOW'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Phase 2 verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-analysis")
async def update_analysis(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    answers: str = Form(...),
    is_existing_building: bool = Form(False)
):
    """
    Phase 3: Update verification with user answers.
    Uses already processed data - no file re-upload needed.
    """
    try:
        # Get job data from file manager
        job_data = await file_manager.get_job_data(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found or expired")
        
        # Check if processing is complete
        if not job_data.get('processing_complete', False):
            raise HTTPException(status_code=400, detail="Job processing not complete")
        
        extracted_data = job_data.get('extracted_data', {})
        if not extracted_data:
            raise HTTPException(status_code=400, detail="No extracted data found")
        
        # Parse answers
        try:
            answers_dict = json.loads(answers)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid answers format")
        
        # Extract project data using advanced analyzer
        project_data = enhanced_analyzer.extract_project_data(extracted_data)
        
        # Load normative documents
        normative_docs = data_loader.load_normative_documents(
            project_data.building_use, 
            is_existing_building
        )
        
        # Update compliance with answers using advanced analyzer
        updated_result = enhanced_analyzer.check_complete_compliance(
            project_data,
            extracted_data,
            normative_docs
        )
        
        # Update job with final results
        await file_manager.update_job_data(job_id, {
            "final_result": {
                "issues": [issue.dict() for issue in updated_result['issues']],
                "confidence": updated_result['confidence']
            },
            "status": "complete"
        })
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_job_files, job_id)
        
        return {
            "job_id": job_id,
            "status": "success",
            "project_data": project_data.dict(),
            "issues": [issue.dict() for issue in updated_result['issues']],
            "confidence": updated_result['confidence'],
            "summary": {
                "total_issues": len(updated_result['issues']),
                "high_severity": len([i for i in updated_result['issues'] if i.severity == 'HIGH']),
                "medium_severity": len([i for i in updated_result['issues'] if i.severity == 'MEDIUM']),
                "low_severity": len([i for i in updated_result['issues'] if i.severity == 'LOW'])
            },
            "answers_processed": len(answers_dict)
        }
        
    except Exception as e:
        logger.error(f"Error in Phase 3 verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def cleanup_job_files(job_id: str):
    """Clean up job files after completion."""
    try:
        # Clean up files using file manager
        await file_manager.cleanup_job_files(job_id)
        
        # Delete job from Redis
        await state_manager.delete_job(job_id)
        
        logger.info(f"Cleaned up job {job_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning up job {job_id}: {e}")

async def cleanup_project_data(project_id: str):
    """Clean up project data after completion."""
    try:
        # Clean up project data using cleanup manager
        result = cleanup_manager.cleanup_project_data(project_id, force=True)
        
        logger.info(f"Cleaned up project {project_id}: {result['space_freed_mb']:.2f}MB freed")
        
    except Exception as e:
        logger.error(f"Error cleaning up project {project_id}: {e}")

@app.post("/verify-phase2")
async def verify_phase2(
    memory_file: UploadFile = File(...),
    plans_directory: str = Form(...),
    project_type: str = Form("residential"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Fase 2: Verificación integral con visión por computador
    Analiza documentos y planos con IA avanzada
    """
    try:
        logger.info(f"Starting Phase 2 verification for project type: {project_type}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save memory file
        memory_path = await file_manager.save_uploaded_file(memory_file, job_id)
        
        # Verify plans directory exists
        if not os.path.exists(plans_directory):
            raise HTTPException(status_code=400, detail=f"Plans directory not found: {plans_directory}")
        
        # Create job entry
        await file_manager.create_job(job_id, {
            "memory_file": memory_path,
            "plans_directory": plans_directory,
            "project_type": project_type,
            "status": "processing",
            "created_at": datetime.now().isoformat()
        })
        
        # Run comprehensive analysis with Phase 2
        result = enhanced_analyzer_v3.analyze_project_comprehensive(
            memory_file=memory_path,
            plans_directory=plans_directory,
            project_type=project_type
        )
        
        # Update job with results
        await file_manager.update_job_data(job_id, {
            "result": {
                "overall_score": result.overall_score,
                "critical_issues": result.critical_issues,
                "recommendations": result.recommendations,
                "processing_time": result.processing_time,
                "files_processed": result.files_processed
            },
            "status": "complete"
        })
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_job_files, job_id)
        
        return {
            "job_id": job_id,
            "status": "success",
            "overall_score": result.overall_score,
            "critical_issues": result.critical_issues,
            "recommendations": result.recommendations,
            "processing_time": result.processing_time,
            "files_processed": result.files_processed,
            "summary": {
                "document_confidence": result.document_analysis.get('confidence_score', 0.0),
                "plan_compliance": result.plan_analysis.overall_compliance,
                "dimension_compliance": result.compliance_check.get('dimension_compliance', 0.0),
                "accessibility_issues": len(result.plan_analysis.accessibility_issues),
                "fire_safety_issues": len(result.plan_analysis.fire_safety_issues),
                "structural_issues": len(result.plan_analysis.structural_issues)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Phase 2 verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-phase3")
async def verify_phase3(
    memory_file: UploadFile = File(...),
    plans_directory: str = Form(...),
    project_type: str = Form("residential"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Fase 3: Sistema de Preguntas Inteligentes
    Análisis integral completo con IA conversacional y resolución de ambigüedades
    """
    try:
        logger.info(f"Starting Phase 3 verification for project type: {project_type}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save memory file
        memory_path = await file_manager.save_uploaded_file(memory_file, job_id)
        
        # Verify plans directory exists
        if not os.path.exists(plans_directory):
            raise HTTPException(status_code=400, detail=f"Plans directory not found: {plans_directory}")
        
        # Create job entry
        await file_manager.create_job(job_id, {
            "memory_file": memory_path,
            "plans_directory": plans_directory,
            "project_type": project_type,
            "status": "processing",
            "created_at": datetime.now().isoformat()
        })
        
        # Run comprehensive analysis with Phase 3
        result = enhanced_analyzer_v4.analyze_project_comprehensive(
            memory_file=memory_path,
            plans_directory=plans_directory,
            project_type=project_type
        )
        
        # Update job with results
        await file_manager.update_job_data(job_id, {
            "result": {
                "overall_score": result.overall_score,
                "critical_issues": result.critical_issues,
                "recommendations": result.recommendations,
                "processing_time": result.processing_time,
                "files_processed": result.files_processed,
                "document_analysis": result.document_analysis,
                "plan_analysis": result.plan_analysis,
                "dimension_analysis": result.dimension_analysis,
                "compliance_analysis": result.compliance_analysis,
                "nlp_analysis": result.nlp_analysis,
                "rule_analysis": result.rule_analysis,
                "ambiguities": result.ambiguities,
                "questions": result.questions,
                "knowledge_graph": result.knowledge_graph,
                "report_path": result.report_path
            },
            "status": "complete"
        })
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_job_files, job_id)
        
        return {
            "job_id": job_id,
            "status": "success",
            "overall_score": result.overall_score,
            "critical_issues": result.critical_issues,
            "recommendations": result.recommendations,
            "processing_time": result.processing_time,
            "files_processed": result.files_processed,
            "summary": {
                "document_confidence": result.document_analysis.get('confidence_score', 0.0),
                "plan_compliance": result.plan_analysis.get('overall_compliance', 0.0),
                "dimension_compliance": result.compliance_analysis.get('dimension_compliance', 0.0),
                "accessibility_issues": len(result.plan_analysis.get('accessibility_issues', [])),
                "fire_safety_issues": len(result.plan_analysis.get('fire_safety_issues', [])),
                "structural_issues": len(result.plan_analysis.get('structural_issues', [])),
                "ambiguities_detected": len(result.ambiguities),
                "questions_generated": len(result.questions),
                "knowledge_graph_nodes": result.knowledge_graph.get('total_nodes', 0),
                "report_generated": bool(result.report_path)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Phase 3 verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/start")
async def start_conversation(
    project_id: str = Form(...),
    user_id: str = Form("user")
):
    """
    Inicia una conversación para un proyecto específico
    """
    try:
        session_id = enhanced_analyzer_v4.start_conversation(project_id, user_id)
        
        if session_id:
            return {
                "session_id": session_id,
                "status": "success",
                "message": "Conversación iniciada correctamente"
            }
        else:
            raise HTTPException(status_code=500, detail="Error iniciando conversación")
            
    except Exception as e:
        logger.error(f"Error iniciando conversación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/message")
async def send_message(
    session_id: str = Form(...),
    message: str = Form(...)
):
    """
    Envía un mensaje en la conversación
    """
    try:
        response = enhanced_analyzer_v4.process_conversation_message(session_id, message)
        
        return {
            "session_id": session_id,
            "response": response,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project/{project_id}/report")
async def get_project_report(project_id: str):
    """
    Obtiene el reporte generado para un proyecto
    """
    try:
        # Buscar reporte en el directorio de reportes
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            raise HTTPException(status_code=404, detail="Directorio de reportes no encontrado")
        
        # Buscar archivo de reporte para el proyecto
        report_files = [f for f in os.listdir(reports_dir) if f.startswith(f"report_{project_id}")]
        
        if not report_files:
            raise HTTPException(status_code=404, detail="Reporte no encontrado para este proyecto")
        
        # Devolver el archivo más reciente
        latest_report = max(report_files, key=lambda f: os.path.getctime(os.path.join(reports_dir, f)))
        report_path = os.path.join(reports_dir, latest_report)
        
        return FileResponse(
            path=report_path,
            filename=latest_report,
            media_type='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo reporte: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# FASE 4: SISTEMA CONVERSACIONAL AVANZADO
# ============================================================================

@app.post("/conversation/start")
async def start_conversation(
    user_id: str = Form(...),
    project_id: Optional[str] = Form(None),
    project_type: Optional[str] = Form("residential"),
    project_name: Optional[str] = Form(None)
):
    """
    Iniciar nueva conversación con el sistema conversacional avanzado.
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Crear contexto del proyecto si se proporciona
        project_context = None
        if project_id:
            project_context = ProjectContext(
                project_id=project_id,
                project_type=project_type,
                project_name=project_name
            )
            await context_manager.update_project_context(project_id, {
                "project_type": project_type,
                "project_name": project_name
            })
        
        # Crear contexto de conversación
        conversation_context = await context_manager.create_conversation_context(
            session_id=session_id,
            user_id=user_id,
            project_context=project_context
        )
        
        # Mensaje de bienvenida personalizado
        welcome_message = "¡Hola! Soy tu asistente especializado en verificación de proyectos arquitectónicos. "
        if project_context:
            welcome_message += f"Veo que estás trabajando en un proyecto {project_type}. "
        welcome_message += "¿En qué puedo ayudarte con tu proyecto de construcción?"
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "project_id": project_id,
            "welcome_message": welcome_message,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/message")
async def send_message(
    session_id: str = Form(...),
    message: str = Form(...),
    project_context: Optional[str] = Form(None)
):
    """
    Enviar mensaje al sistema conversacional avanzado.
    """
    try:
        # Parsear contexto del proyecto si se proporciona
        project_data = None
        if project_context:
            try:
                project_data = json.loads(project_context)
            except json.JSONDecodeError:
                logger.warning("Invalid project context JSON")
        
        # Procesar mensaje con Rasa
        response = await rasa_integration.process_message(
            message=message,
            session_id=session_id,
            project_context=project_data
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{session_id}/history")
async def get_conversation_history(session_id: str):
    """
    Obtener historial de conversación.
    """
    try:
        history = await rasa_integration.get_session_history(session_id)
        context_summary = await context_manager.get_context_summary(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "context_summary": context_summary,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """
    Limpiar conversación.
    """
    try:
        success = await rasa_integration.clear_session(session_id)
        
        return {
            "session_id": session_id,
            "cleared": success,
            "status": "success" if success else "not_found"
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/{session_id}/project")
async def update_project_context(
    session_id: str,
    project_id: str = Form(...),
    project_type: str = Form(...),
    project_name: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    building_type: Optional[str] = Form(None),
    total_area: Optional[float] = Form(None),
    floors: Optional[int] = Form(None)
):
    """
    Actualizar contexto del proyecto en la conversación.
    """
    try:
        project_data = {
            "project_type": project_type,
            "project_name": project_name,
            "location": location,
            "building_type": building_type,
            "total_area": total_area,
            "floors": floors
        }
        
        # Actualizar contexto del proyecto
        project_context = await context_manager.update_project_context(project_id, project_data)
        
        # Obtener contexto de conversación y actualizar
        conversation_context = await context_manager.get_conversation_context(session_id)
        if conversation_context:
            conversation_context.project_context = project_context
            await context_manager._persist_conversation_context(conversation_context)
        
        return {
            "session_id": session_id,
            "project_id": project_id,
            "project_context": {
                "project_type": project_context.project_type,
                "project_name": project_context.project_name,
                "location": project_context.location,
                "building_type": project_context.building_type,
                "total_area": project_context.total_area,
                "floors": project_context.floors
            },
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error updating project context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/{session_id}/analysis")
async def add_analysis_result(
    session_id: str,
    analysis_type: str = Form(...),
    analysis_result: str = Form(...)
):
    """
    Agregar resultado de análisis al contexto de conversación.
    """
    try:
        result_data = json.loads(analysis_result)
        
        success = await context_manager.add_analysis_result(
            session_id=session_id,
            analysis_type=analysis_type,
            result=result_data
        )
        
        return {
            "session_id": session_id,
            "analysis_type": analysis_type,
            "added": success,
            "status": "success" if success else "error"
        }
        
    except Exception as e:
        logger.error(f"Error adding analysis result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/{session_id}/question")
async def add_pending_question(
    session_id: str,
    question: str = Form(...)
):
    """
    Agregar pregunta pendiente al contexto.
    """
    try:
        success = await context_manager.add_pending_question(session_id, question)
        
        return {
            "session_id": session_id,
            "question": question,
            "added": success,
            "status": "success" if success else "error"
        }
        
    except Exception as e:
        logger.error(f"Error adding pending question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/{session_id}/resolve")
async def resolve_question(
    session_id: str,
    question: str = Form(...),
    resolution: str = Form(...)
):
    """
    Resolver pregunta pendiente.
    """
    try:
        success = await context_manager.resolve_question(session_id, question, resolution)
        
        return {
            "session_id": session_id,
            "question": question,
            "resolved": success,
            "status": "success" if success else "error"
        }
        
    except Exception as e:
        logger.error(f"Error resolving question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{session_id}/context")
async def get_conversation_context(session_id: str):
    """
    Obtener contexto completo de la conversación.
    """
    try:
        context_summary = await context_manager.get_context_summary(session_id)
        conversation_context = await context_manager.get_conversation_context(session_id)
        
        return {
            "session_id": session_id,
            "context_summary": context_summary,
            "conversation_context": {
                "current_intent": conversation_context.current_intent if conversation_context else None,
                "current_entities": conversation_context.current_entities if conversation_context else [],
                "pending_questions": conversation_context.pending_questions if conversation_context else [],
                "resolved_issues": conversation_context.resolved_issues if conversation_context else [],
                "analysis_results": list(conversation_context.analysis_results.keys()) if conversation_context and conversation_context.analysis_results else []
            },
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/cleanup")
async def cleanup_old_conversations(
    max_age_hours: int = 24
):
    """
    Limpiar conversaciones antiguas.
    """
    try:
        cleaned_count = await context_manager.cleanup_old_contexts(max_age_hours)
        
        return {
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )