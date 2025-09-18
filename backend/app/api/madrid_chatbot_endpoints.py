"""
Endpoints del chatbot Madrid para resolución de ambigüedades.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import uuid
from datetime import datetime

from ..core.madrid_chatbot_system import MadridChatbotSystem, ChatbotSession, ChatbotMessage
from ..core.madrid_ambiguity_detector import MadridAmbiguityDetector
from ..core.madrid_verification_engine import MadridVerificationEngine
from ..core.madrid_floor_processor import MadridFloorProcessor
from ..models.madrid_schemas import MadridProjectData

logger = logging.getLogger(__name__)

# Router para endpoints del chatbot Madrid
chatbot_router = APIRouter(prefix="/madrid/chatbot", tags=["Madrid Chatbot"])

# Instancias globales
chatbot_system = None
ambiguity_detector = MadridAmbiguityDetector()
floor_processor = MadridFloorProcessor()

# Modelos Pydantic
class ChatbotStartRequest(BaseModel):
    """Request para iniciar chatbot."""
    project_data: MadridProjectData = Field(..., description="Datos del proyecto Madrid")
    session_id: Optional[str] = Field(None, description="ID de sesión (opcional)")

class ChatbotStartResponse(BaseModel):
    """Response de inicio de chatbot."""
    session_id: str = Field(..., description="ID de sesión")
    project_id: str = Field(..., description="ID del proyecto")
    state: str = Field(..., description="Estado del chatbot")
    message: Dict[str, Any] = Field(..., description="Mensaje inicial")
    ambiguities_count: int = Field(..., description="Número de ambigüedades detectadas")
    requires_response: bool = Field(..., description="Si requiere respuesta del usuario")

class ChatbotMessageRequest(BaseModel):
    """Request para enviar mensaje al chatbot."""
    session_id: str = Field(..., description="ID de sesión")
    message: str = Field(..., description="Mensaje del usuario")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")

class ChatbotMessageResponse(BaseModel):
    """Response de mensaje del chatbot."""
    message_id: str = Field(..., description="ID del mensaje")
    type: str = Field(..., description="Tipo de respuesta")
    content: str = Field(..., description="Contenido de la respuesta")
    context: Dict[str, Any] = Field(..., description="Contexto de la respuesta")
    suggested_actions: List[Dict[str, Any]] = Field(..., description="Acciones sugeridas")
    requires_response: bool = Field(..., description="Si requiere respuesta del usuario")
    session_status: Dict[str, Any] = Field(..., description="Estado de la sesión")

class ChatbotStatusResponse(BaseModel):
    """Response de estado del chatbot."""
    session_id: str = Field(..., description="ID de sesión")
    project_id: str = Field(..., description="ID del proyecto")
    state: str = Field(..., description="Estado actual")
    ambiguities_remaining: int = Field(..., description="Ambigüedades pendientes")
    ambiguities_resolved: int = Field(..., description="Ambigüedades resueltas")
    conversation_length: int = Field(..., description="Longitud de la conversación")
    last_activity: str = Field(..., description="Última actividad")

class ChatbotCompleteResponse(BaseModel):
    """Response de finalización del chatbot."""
    session_id: str = Field(..., description="ID de sesión")
    project_id: str = Field(..., description="ID del proyecto")
    completed: bool = Field(..., description="Si se completó exitosamente")
    project_data: Dict[str, Any] = Field(..., description="Datos del proyecto actualizados")
    resolved_ambiguities: List[Dict[str, Any]] = Field(..., description="Ambigüedades resueltas")
    conversation_summary: Dict[str, Any] = Field(..., description="Resumen de la conversación")

# Dependencias
async def get_chatbot_system():
    """Obtener instancia del sistema de chatbot."""
    global chatbot_system
    if chatbot_system is None:
        chatbot_system = MadridChatbotSystem(
            ambiguity_detector=ambiguity_detector,
            floor_processor=floor_processor
        )
    return chatbot_system

# Endpoints

@chatbot_router.post("/start", response_model=ChatbotStartResponse)
async def start_chatbot_session(
    request: ChatbotStartRequest,
    chatbot: MadridChatbotSystem = Depends(get_chatbot_system)
):
    """
    Iniciar sesión de chatbot para resolución de ambigüedades.
    
    Analiza el proyecto y detecta ambigüedades que requieren aclaración.
    """
    try:
        logger.info(f"Iniciando sesión de chatbot para proyecto: {request.project_data.primary_use}")
        
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
        
        # Iniciar sesión
        session = await chatbot.start_ambiguity_resolution(
            project_data=project_data,
            session_id=request.session_id
        )
        
        # Obtener último mensaje
        last_message = session.conversation_history[-1] if session.conversation_history else None
        
        response = ChatbotStartResponse(
            session_id=session.session_id,
            project_id=session.project_id,
            state=session.state.value,
            message={
                'id': last_message.id if last_message else '',
                'type': last_message.type.value if last_message else 'information',
                'content': last_message.content if last_message else '',
                'context': last_message.context if last_message else {},
                'suggested_actions': last_message.suggested_actions if last_message else [],
                'timestamp': last_message.timestamp if last_message else datetime.now().isoformat()
            },
            ambiguities_count=len(session.current_ambiguities),
            requires_response=last_message.requires_response if last_message else False
        )
        
        logger.info(f"Sesión de chatbot iniciada: {session.session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error iniciando sesión de chatbot: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando chatbot: {str(e)}")

@chatbot_router.post("/message", response_model=ChatbotMessageResponse)
async def send_message_to_chatbot(
    request: ChatbotMessageRequest,
    chatbot: MadridChatbotSystem = Depends(get_chatbot_system)
):
    """
    Enviar mensaje al chatbot.
    
    Procesa la respuesta del usuario y devuelve la respuesta del chatbot.
    """
    try:
        logger.info(f"Procesando mensaje en sesión: {request.session_id}")
        
        # Procesar mensaje
        response = await chatbot.process_user_message(
            session_id=request.session_id,
            user_message=request.message,
            context=request.context
        )
        
        # Obtener estado de la sesión
        session_status = await chatbot.get_session_status(request.session_id)
        
        chatbot_response = ChatbotMessageResponse(
            message_id=response.id,
            type=response.type.value,
            content=response.content,
            context=response.context,
            suggested_actions=response.suggested_actions,
            requires_response=response.requires_response,
            session_status=session_status or {}
        )
        
        logger.info(f"Mensaje procesado: {response.id}")
        return chatbot_response
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")

@chatbot_router.get("/status/{session_id}", response_model=ChatbotStatusResponse)
async def get_chatbot_status(
    session_id: str,
    chatbot: MadridChatbotSystem = Depends(get_chatbot_system)
):
    """
    Obtener estado de la sesión del chatbot.
    
    Args:
        session_id: ID de la sesión
        
    Returns:
        Estado actual de la sesión
    """
    try:
        status = await chatbot.get_session_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        return ChatbotStatusResponse(
            session_id=status['session_id'],
            project_id=status['project_id'],
            state=status['state'],
            ambiguities_remaining=status['ambiguities_remaining'],
            ambiguities_resolved=status['ambiguities_resolved'],
            conversation_length=status['conversation_length'],
            last_activity=status['last_activity']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado del chatbot: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@chatbot_router.post("/complete/{session_id}", response_model=ChatbotCompleteResponse)
async def complete_chatbot_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    chatbot: MadridChatbotSystem = Depends(get_chatbot_system)
):
    """
    Completar sesión del chatbot y obtener datos del proyecto.
    
    Finaliza la resolución de ambigüedades y devuelve los datos del proyecto actualizados.
    """
    try:
        logger.info(f"Completando sesión de chatbot: {session_id}")
        
        # Completar sesión
        result = await chatbot.complete_session(session_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Iniciar verificación en background si se solicita
        background_tasks.add_task(
            _start_verification_background,
            result['project_data']
        )
        
        response = ChatbotCompleteResponse(
            session_id=session_id,
            project_id=result['project_data'].get('project_id', 'unknown'),
            completed=True,
            project_data=result['project_data'],
            resolved_ambiguities=result['resolved_ambiguities'],
            conversation_summary=result['conversation_summary']
        )
        
        logger.info(f"Sesión de chatbot completada: {session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completando sesión del chatbot: {e}")
        raise HTTPException(status_code=500, detail=f"Error completando sesión: {str(e)}")

@chatbot_router.get("/sessions")
async def list_active_sessions(
    chatbot: MadridChatbotSystem = Depends(get_chatbot_system)
):
    """
    Listar sesiones activas del chatbot.
    
    Returns:
        Lista de sesiones activas
    """
    try:
        sessions = []
        
        for session_id, session in chatbot.active_sessions.items():
            status = await chatbot.get_session_status(session_id)
            if status:
                sessions.append(status)
        
        return {
            'active_sessions': len(sessions),
            'sessions': sessions
        }
        
    except Exception as e:
        logger.error(f"Error listando sesiones: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando sesiones: {str(e)}")

@chatbot_router.delete("/sessions/{session_id}")
async def delete_chatbot_session(
    session_id: str,
    chatbot: MadridChatbotSystem = Depends(get_chatbot_system)
):
    """
    Eliminar sesión del chatbot.
    
    Args:
        session_id: ID de la sesión a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    try:
        if session_id in chatbot.active_sessions:
            del chatbot.active_sessions[session_id]
            logger.info(f"Sesión eliminada: {session_id}")
            return {"message": f"Sesión {session_id} eliminada exitosamente"}
        else:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando sesión: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando sesión: {str(e)}")

@chatbot_router.post("/detect-ambiguities")
async def detect_ambiguities_only(
    project_data: MadridProjectData,
    detector: MadridAmbiguityDetector = Depends(lambda: ambiguity_detector)
):
    """
    Detectar ambigüedades sin iniciar sesión de chatbot.
    
    Útil para verificar ambigüedades antes de iniciar el proceso de resolución.
    """
    try:
        # Convertir datos del proyecto
        project_data_dict = {
            'project_id': str(uuid.uuid4()),
            'is_existing_building': project_data.is_existing_building,
            'primary_use': project_data.primary_use.value,
            'has_secondary_uses': project_data.has_secondary_uses,
            'secondary_uses': [
                {
                    'use_type': use.use_type.value,
                    'floors': use.floors
                } for use in project_data.secondary_uses
            ],
            'files': project_data.files
        }
        
        # Detectar ambigüedades
        ambiguities = detector.detect_ambiguities(project_data_dict)
        
        return {
            'project_id': project_data_dict['project_id'],
            'ambiguities_detected': len(ambiguities),
            'ambiguities': [
                {
                    'id': amb.id,
                    'type': amb.type.value,
                    'severity': amb.severity.value,
                    'title': amb.title,
                    'description': amb.description,
                    'detected_in': amb.detected_in,
                    'suggested_questions': amb.suggested_questions,
                    'possible_resolutions': amb.possible_resolutions
                } for amb in ambiguities
            ]
        }
        
    except Exception as e:
        logger.error(f"Error detectando ambigüedades: {e}")
        raise HTTPException(status_code=500, detail=f"Error detectando ambigüedades: {str(e)}")

# Funciones de background
async def _start_verification_background(project_data: Dict[str, Any]):
    """Iniciar verificación en background."""
    try:
        # Aquí se podría iniciar la verificación automáticamente
        # después de completar la resolución de ambigüedades
        logger.info(f"Iniciando verificación en background para proyecto: {project_data.get('project_id')}")
        
        # Por ahora, solo loggear
        # En implementación real, se llamaría al motor de verificación
        
    except Exception as e:
        logger.error(f"Error en verificación background: {e}")
