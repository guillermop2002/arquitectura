"""
Sistema de chatbot inteligente para resolución de ambigüedades Madrid.
Integra con Rasa y proporciona respuestas contextuales específicas.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio
import aiohttp
from enum import Enum

from .madrid_ambiguity_detector import MadridAmbiguityDetector, AmbiguityItem, AmbiguityResolution
from .madrid_verification_engine import MadridVerificationEngine
from .madrid_floor_processor import MadridFloorProcessor

logger = logging.getLogger(__name__)

class ChatbotState(Enum):
    """Estados del chatbot."""
    IDLE = "idle"
    DETECTING_AMBIGUITIES = "detecting_ambiguities"
    RESOLVING_AMBIGUITIES = "resolving_ambiguities"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    PROCESSING_RESPONSE = "processing_response"
    COMPLETED = "completed"
    ERROR = "error"

class ChatbotResponseType(Enum):
    """Tipos de respuesta del chatbot."""
    QUESTION = "question"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    INFORMATION = "information"
    ERROR = "error"
    COMPLETION = "completion"

@dataclass
class ChatbotMessage:
    """Mensaje del chatbot."""
    id: str
    type: ChatbotResponseType
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    suggested_actions: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    requires_response: bool = False

@dataclass
class ChatbotSession:
    """Sesión del chatbot."""
    session_id: str
    project_id: str
    state: ChatbotState
    current_ambiguities: List[AmbiguityItem] = field(default_factory=list)
    resolved_ambiguities: List[AmbiguityResolution] = field(default_factory=list)
    conversation_history: List[ChatbotMessage] = field(default_factory=list)
    project_data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())

class MadridChatbotSystem:
    """Sistema de chatbot inteligente para Madrid."""
    
    def __init__(self, 
                 ambiguity_detector: MadridAmbiguityDetector = None,
                 verification_engine: MadridVerificationEngine = None,
                 floor_processor: MadridFloorProcessor = None,
                 rasa_url: str = "http://rasa:5005"):
        self.logger = logging.getLogger(f"{__name__}.MadridChatbotSystem")
        
        self.ambiguity_detector = ambiguity_detector or MadridAmbiguityDetector()
        self.verification_engine = verification_engine
        self.floor_processor = floor_processor or MadridFloorProcessor()
        self.rasa_url = rasa_url
        
        # Sesiones activas
        self.active_sessions: Dict[str, ChatbotSession] = {}
        
        # Plantillas de respuestas
        self.response_templates = self._initialize_response_templates()
        
        # Patrones de reconocimiento
        self.recognition_patterns = self._initialize_recognition_patterns()
    
    def _initialize_response_templates(self) -> Dict[str, Dict[str, str]]:
        """Inicializar plantillas de respuestas."""
        return {
            'greeting': {
                'content': "¡Hola! Soy el asistente de verificación arquitectónica de Madrid. He detectado algunas ambigüedades en tu proyecto que necesito aclarar para proceder con la verificación normativa.",
                'type': 'information'
            },
            'ambiguity_detected': {
                'content': "He detectado {count} ambigüedad(es) en tu proyecto que requieren aclaración:",
                'type': 'information'
            },
            'question_template': {
                'content': "{question}",
                'type': 'question'
            },
            'clarification_needed': {
                'content': "Para continuar con la verificación, necesito que me aclares: {clarification}",
                'type': 'clarification'
            },
            'confirmation_request': {
                'content': "¿Confirmas que {confirmation}?",
                'type': 'confirmation'
            },
            'processing': {
                'content': "Procesando tu respuesta...",
                'type': 'information'
            },
            'completion': {
                'content': "¡Perfecto! He resuelto todas las ambigüedades. Ahora procederé con la verificación normativa completa de tu proyecto.",
                'type': 'completion'
            },
            'error': {
                'content': "Lo siento, ha ocurrido un error: {error}. Por favor, intenta de nuevo.",
                'type': 'error'
            }
        }
    
    def _initialize_recognition_patterns(self) -> Dict[str, List[str]]:
        """Inicializar patrones de reconocimiento."""
        return {
            'yes_responses': [
                r'sí|si|yes|yep|ok|okay|correcto|exacto|afirmativo|claro|por supuesto',
                r'confirmo|confirmado|está bien|perfecto|vale|de acuerdo'
            ],
            'no_responses': [
                r'no|nop|nope|incorrecto|falso|negativo|nada|ninguno',
                r'no confirmo|no está bien|no vale|en desacuerdo'
            ],
            'building_types': [
                r'residencial|vivienda|viviendas|residenciales',
                r'industrial|industria|fabrica|fábrica|taller|almacén',
                r'garaje|aparcamiento|parking|estacionamiento',
                r'comercial|tienda|tiendas|comercio|comercios',
                r'oficina|oficinas|despacho|despachos',
                r'servicios|terciario|terciarios',
                r'dotacional|equipamiento|público|pública'
            ],
            'floor_descriptions': [
                r'sótano|sotano|subterráneo|subterraneo|bajo|baja',
                r'planta baja|pb|p\.b\.|planta 0|p0',
                r'entreplanta|entre-planta|entre planta|entresuelo',
                r'primera|primer|1º|1ª|piso 1|planta 1',
                r'segunda|segundo|2º|2ª|piso 2|planta 2',
                r'tercera|tercero|3º|3ª|piso 3|planta 3'
            ],
            'numbers': [
                r'\d+', r'primera|primero|1', r'segunda|segundo|2',
                r'tercera|tercero|3', r'cuarta|cuarto|4', r'quinta|quinto|5'
            ]
        }
    
    async def start_ambiguity_resolution(self, 
                                       project_data: Dict[str, Any],
                                       session_id: str = None) -> ChatbotSession:
        """
        Iniciar proceso de resolución de ambigüedades.
        
        Args:
            project_data: Datos del proyecto
            session_id: ID de sesión (opcional)
            
        Returns:
            Sesión del chatbot iniciada
        """
        try:
            if not session_id:
                session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.logger.info(f"Iniciando resolución de ambigüedades: {session_id}")
            
            # Crear sesión
            session = ChatbotSession(
                session_id=session_id,
                project_id=project_data.get('project_id', 'unknown'),
                state=ChatbotState.DETECTING_AMBIGUITIES,
                project_data=project_data
            )
            
            # Detectar ambigüedades
            ambiguities = self.ambiguity_detector.detect_ambiguities(project_data)
            session.current_ambiguities = ambiguities
            
            if not ambiguities:
                # No hay ambigüedades, completar inmediatamente
                session.state = ChatbotState.COMPLETED
                message = self._create_message(
                    type=ChatbotResponseType.COMPLETION,
                    content="No se detectaron ambigüedades en tu proyecto. Procederé con la verificación normativa.",
                    context={"ambiguities_count": 0}
                )
                session.conversation_history.append(message)
            else:
                # Hay ambigüedades, iniciar resolución
                session.state = ChatbotState.RESOLVING_AMBIGUITIES
                message = self._create_message(
                    type=ChatbotResponseType.INFORMATION,
                    content=self.response_templates['ambiguity_detected']['content'].format(count=len(ambiguities)),
                    context={"ambiguities_count": len(ambiguities)},
                    suggested_actions=[{"action": "start_resolution", "label": "Comenzar resolución"}]
                )
                session.conversation_history.append(message)
                
                # Agregar detalles de ambigüedades
                for i, ambiguity in enumerate(ambiguities):
                    detail_message = self._create_message(
                        type=ChatbotResponseType.INFORMATION,
                        content=f"{i+1}. {ambiguity.title}: {ambiguity.description}",
                        context={"ambiguity_id": ambiguity.id, "severity": ambiguity.severity.value}
                    )
                    session.conversation_history.append(detail_message)
            
            # Guardar sesión
            self.active_sessions[session_id] = session
            
            return session
            
        except Exception as e:
            self.logger.error(f"Error iniciando resolución de ambigüedades: {e}")
            raise
    
    async def process_user_message(self, 
                                 session_id: str, 
                                 user_message: str,
                                 context: Dict[str, Any] = None) -> ChatbotMessage:
        """
        Procesar mensaje del usuario.
        
        Args:
            session_id: ID de sesión
            user_message: Mensaje del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta del chatbot
        """
        try:
            if session_id not in self.active_sessions:
                return self._create_error_message("Sesión no encontrada")
            
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now().isoformat()
            
            # Agregar mensaje del usuario al historial
            user_msg = self._create_message(
                type=ChatbotResponseType.INFORMATION,
                content=user_message,
                context={"from_user": True}
            )
            session.conversation_history.append(user_msg)
            
            # Procesar según el estado actual
            if session.state == ChatbotState.RESOLVING_AMBIGUITIES:
                return await self._process_ambiguity_resolution(session, user_message, context)
            elif session.state == ChatbotState.WAITING_FOR_CLARIFICATION:
                return await self._process_clarification_response(session, user_message, context)
            elif session.state == ChatbotState.PROCESSING_RESPONSE:
                return await self._process_processing_response(session, user_message, context)
            else:
                return self._create_error_message("Estado de sesión no válido")
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje del usuario: {e}")
            return self._create_error_message(f"Error procesando mensaje: {str(e)}")
    
    async def _process_ambiguity_resolution(self, 
                                          session: ChatbotSession, 
                                          user_message: str,
                                          context: Dict[str, Any] = None) -> ChatbotMessage:
        """Procesar resolución de ambigüedades."""
        if not session.current_ambiguities:
            session.state = ChatbotState.COMPLETED
            return self._create_completion_message()
        
        # Obtener la primera ambigüedad pendiente
        current_ambiguity = session.current_ambiguities[0]
        
        # Analizar respuesta del usuario
        analysis = await self._analyze_user_response(user_message, current_ambiguity)
        
        if analysis['resolved']:
            # Resolver ambigüedad
            resolution = AmbiguityResolution(
                ambiguity_id=current_ambiguity.id,
                resolution_type=analysis['resolution_type'],
                resolved_value=analysis['resolved_value'],
                confidence=analysis['confidence'],
                resolved_by='user',
                notes=user_message
            )
            
            # Aplicar resolución
            session.project_data = self.ambiguity_detector.resolve_ambiguity(
                current_ambiguity.id, resolution, session.project_data
            )
            
            session.resolved_ambiguities.append(resolution)
            session.current_ambiguities.pop(0)
            
            # Verificar si hay más ambigüedades
            if session.current_ambiguities:
                next_ambiguity = session.current_ambiguities[0]
                return self._create_question_message(next_ambiguity)
            else:
                session.state = ChatbotState.COMPLETED
                return self._create_completion_message()
        else:
            # Solicitar aclaración
            return self._create_clarification_message(current_ambiguity, analysis['reason'])
    
    async def _process_clarification_response(self, 
                                            session: ChatbotSession, 
                                            user_message: str,
                                            context: Dict[str, Any] = None) -> ChatbotMessage:
        """Procesar respuesta de aclaración."""
        # Similar a _process_ambiguity_resolution pero con contexto de aclaración
        return await self._process_ambiguity_resolution(session, user_message, context)
    
    async def _process_processing_response(self, 
                                        session: ChatbotSession, 
                                        user_message: str,
                                        context: Dict[str, Any] = None) -> ChatbotMessage:
        """Procesar respuesta durante procesamiento."""
        # El usuario está respondiendo mientras se procesa algo
        return self._create_message(
            type=ChatbotResponseType.INFORMATION,
            content="Procesando tu respuesta anterior. Por favor, espera un momento.",
            context={"processing": True}
        )
    
    async def _analyze_user_response(self, 
                                   user_message: str, 
                                   ambiguity: AmbiguityItem) -> Dict[str, Any]:
        """Analizar respuesta del usuario."""
        user_lower = user_message.lower()
        
        # Verificar respuestas de confirmación
        for pattern in self.recognition_patterns['yes_responses']:
            if re.search(pattern, user_lower):
                return {
                    'resolved': True,
                    'resolution_type': 'confirmation',
                    'resolved_value': True,
                    'confidence': 0.9,
                    'reason': None
                }
        
        for pattern in self.recognition_patterns['no_responses']:
            if re.search(pattern, user_lower):
                return {
                    'resolved': True,
                    'resolution_type': 'confirmation',
                    'resolved_value': False,
                    'confidence': 0.9,
                    'reason': None
                }
        
        # Analizar según el tipo de ambigüedad
        if ambiguity.type.value == 'building_type':
            return await self._analyze_building_type_response(user_message, ambiguity)
        elif ambiguity.type.value == 'floor_description':
            return await self._analyze_floor_response(user_message, ambiguity)
        elif ambiguity.type.value == 'use_classification':
            return await self._analyze_use_classification_response(user_message, ambiguity)
        else:
            return {
                'resolved': False,
                'resolution_type': None,
                'resolved_value': None,
                'confidence': 0.0,
                'reason': 'Tipo de ambigüedad no reconocido'
            }
    
    async def _analyze_building_type_response(self, 
                                            user_message: str, 
                                            ambiguity: AmbiguityItem) -> Dict[str, Any]:
        """Analizar respuesta sobre tipo de edificio."""
        user_lower = user_message.lower()
        
        # Buscar tipos de edificio en la respuesta
        for pattern in self.recognition_patterns['building_types']:
            if re.search(pattern, user_lower):
                # Mapear a tipo válido
                building_type = self._map_to_valid_building_type(pattern)
                if building_type:
                    return {
                        'resolved': True,
                        'resolution_type': 'building_type',
                        'resolved_value': building_type,
                        'confidence': 0.8,
                        'reason': None
                    }
        
        return {
            'resolved': False,
            'resolution_type': None,
            'resolved_value': None,
            'confidence': 0.0,
            'reason': 'No se pudo identificar un tipo de edificio válido'
        }
    
    async def _analyze_floor_response(self, 
                                    user_message: str, 
                                    ambiguity: AmbiguityItem) -> Dict[str, Any]:
        """Analizar respuesta sobre plantas."""
        # Usar el procesador de plantas
        if self.floor_processor:
            floor_number = self.floor_processor.extract_floor_number(user_message)
            if floor_number is not None:
                return {
                    'resolved': True,
                    'resolution_type': 'floor_number',
                    'resolved_value': floor_number,
                    'confidence': 0.9,
                    'reason': None
                }
        
        return {
            'resolved': False,
            'resolution_type': None,
            'resolved_value': None,
            'confidence': 0.0,
            'reason': 'No se pudo interpretar la descripción de planta'
        }
    
    async def _analyze_use_classification_response(self, 
                                                 user_message: str, 
                                                 ambiguity: AmbiguityItem) -> Dict[str, Any]:
        """Analizar respuesta sobre clasificación de usos."""
        # Similar a building_type pero para usos secundarios
        return await self._analyze_building_type_response(user_message, ambiguity)
    
    def _map_to_valid_building_type(self, pattern: str) -> Optional[str]:
        """Mapear patrón a tipo de edificio válido."""
        mapping = {
            'residencial': 'residencial',
            'vivienda': 'residencial',
            'industrial': 'industrial',
            'fabrica': 'industrial',
            'garaje': 'garaje-aparcamiento',
            'aparcamiento': 'garaje-aparcamiento',
            'comercial': 'servicios_terciarios',
            'oficina': 'servicios_terciarios',
            'servicios': 'servicios_terciarios',
            'dotacional': 'dotacional_equipamiento'
        }
        
        for key, value in mapping.items():
            if key in pattern:
                return value
        
        return None
    
    def _create_question_message(self, ambiguity: AmbiguityItem) -> ChatbotMessage:
        """Crear mensaje de pregunta."""
        if ambiguity.suggested_questions:
            question = ambiguity.suggested_questions[0]
        else:
            question = f"¿Puedes aclarar: {ambiguity.description}?"
        
        suggested_actions = []
        for resolution in ambiguity.possible_resolutions:
            suggested_actions.append({
                "action": "select_resolution",
                "label": resolution['description'],
                "value": resolution['value']
            })
        
        return self._create_message(
            type=ChatbotResponseType.QUESTION,
            content=question,
            context={"ambiguity_id": ambiguity.id, "ambiguity_type": ambiguity.type.value},
            suggested_actions=suggested_actions,
            requires_response=True
        )
    
    def _create_clarification_message(self, 
                                    ambiguity: AmbiguityItem, 
                                    reason: str) -> ChatbotMessage:
        """Crear mensaje de aclaración."""
        content = f"Necesito más información: {reason}\n\n{ambiguity.description}"
        
        return self._create_message(
            type=ChatbotResponseType.CLARIFICATION,
            content=content,
            context={"ambiguity_id": ambiguity.id, "reason": reason},
            requires_response=True
        )
    
    def _create_completion_message(self) -> ChatbotMessage:
        """Crear mensaje de finalización."""
        return self._create_message(
            type=ChatbotResponseType.COMPLETION,
            content=self.response_templates['completion']['content'],
            context={"completed": True}
        )
    
    def _create_error_message(self, error: str) -> ChatbotMessage:
        """Crear mensaje de error."""
        return self._create_message(
            type=ChatbotResponseType.ERROR,
            content=self.response_templates['error']['content'].format(error=error),
            context={"error": True}
        )
    
    def _create_message(self, 
                       type: ChatbotResponseType, 
                       content: str,
                       context: Dict[str, Any] = None,
                       suggested_actions: List[Dict[str, Any]] = None,
                       requires_response: bool = False) -> ChatbotMessage:
        """Crear mensaje del chatbot."""
        return ChatbotMessage(
            id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            type=type,
            content=content,
            context=context or {},
            suggested_actions=suggested_actions or [],
            requires_response=requires_response
        )
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de la sesión."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        return {
            'session_id': session.session_id,
            'project_id': session.project_id,
            'state': session.state.value,
            'ambiguities_remaining': len(session.current_ambiguities),
            'ambiguities_resolved': len(session.resolved_ambiguities),
            'conversation_length': len(session.conversation_history),
            'last_activity': session.last_activity
        }
    
    async def complete_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Completar sesión y devolver datos del proyecto."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        session.state = ChatbotState.COMPLETED
        
        # Devolver datos del proyecto actualizados
        return {
            'project_data': session.project_data,
            'resolved_ambiguities': [
                {
                    'id': res.ambiguity_id,
                    'type': res.resolution_type,
                    'value': res.resolved_value,
                    'confidence': res.confidence,
                    'resolved_by': res.resolved_by,
                    'notes': res.notes
                } for res in session.resolved_ambiguities
            ],
            'conversation_summary': {
                'total_messages': len(session.conversation_history),
                'ambiguities_detected': len(session.resolved_ambiguities) + len(session.current_ambiguities),
                'ambiguities_resolved': len(session.resolved_ambiguities)
            }
        }
