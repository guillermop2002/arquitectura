"""
Sistema Conversacional para Resolución de Dudas
Fase 3: Sistema de Preguntas Inteligentes
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .config import get_config
from .logging_config import get_logger
from .ai_client import get_ai_client, AIResponse
from .neo4j_manager import Neo4jManager
from .intelligent_question_engine import IntelligentQuestion

logger = get_logger(__name__)

class ConversationState(Enum):
    """Estados de la conversación"""
    INITIAL = "initial"
    QUESTION_ANALYSIS = "question_analysis"
    INFORMATION_GATHERING = "information_gathering"
    SOLUTION_PROPOSAL = "solution_proposal"
    CLARIFICATION = "clarification"
    RESOLUTION = "resolution"
    COMPLETED = "completed"

@dataclass
class ConversationMessage:
    """Mensaje en la conversación"""
    message_id: str
    user_id: str
    session_id: str
    content: str
    message_type: str  # 'user', 'assistant', 'system'
    timestamp: str
    context: Dict[str, Any]
    intent: Optional[str] = None
    entities: List[Dict[str, Any]] = None

@dataclass
class ConversationSession:
    """Sesión de conversación"""
    session_id: str
    user_id: str
    project_id: str
    state: ConversationState
    messages: List[ConversationMessage]
    current_question: Optional[IntelligentQuestion] = None
    context_data: Dict[str, Any] = None
    created_at: str = None
    updated_at: str = None

class ConversationalAI:
    """Sistema conversacional para resolución de dudas arquitectónicas"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Cliente de IA
        self.ai_client = get_ai_client()
        
        # Gestor de Neo4j
        self.neo4j_manager = Neo4jManager()
        
        # Sesiones activas
        self.active_sessions: Dict[str, ConversationSession] = {}
        
        # Patrones de intención
        self.intent_patterns = self._initialize_intent_patterns()
        
        # Respuestas predefinidas
        self.predefined_responses = self._initialize_predefined_responses()
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Inicializa patrones de reconocimiento de intenciones"""
        return {
            'greeting': [
                r'hola', r'buenos días', r'buenas tardes', r'buenas noches',
                r'¿cómo estás\?', r'¿qué tal\?'
            ],
            'question_about_compliance': [
                r'¿.*cumplimiento.*\?', r'¿.*normativa.*\?', r'¿.*regulación.*\?',
                r'¿.*CTE.*\?', r'¿.*DB-.*\?'
            ],
            'question_about_dimensions': [
                r'¿.*dimensiones.*\?', r'¿.*medidas.*\?', r'¿.*tamaño.*\?',
                r'¿.*área.*\?', r'¿.*metros.*\?'
            ],
            'question_about_accessibility': [
                r'¿.*accesibilidad.*\?', r'¿.*discapacidad.*\?', r'¿.*rampa.*\?',
                r'¿.*ascensor.*\?', r'¿.*puerta.*ancha.*\?'
            ],
            'question_about_fire_safety': [
                r'¿.*incendio.*\?', r'¿.*seguridad.*\?', r'¿.*salida.*emergencia.*\?',
                r'¿.*evacuación.*\?', r'¿.*extintor.*\?'
            ],
            'question_about_structure': [
                r'¿.*estructura.*\?', r'¿.*muro.*\?', r'¿.*columna.*\?',
                r'¿.*viga.*\?', r'¿.*cimentación.*\?'
            ],
            'request_help': [
                r'ayuda', r'¿.*ayudar.*\?', r'¿.*puedes.*ayudar.*\?',
                r'¿.*cómo.*funciona.*\?', r'¿.*qué.*puedes.*hacer.*\?'
            ],
            'request_explanation': [
                r'¿.*explicar.*\?', r'¿.*qué.*significa.*\?', r'¿.*por qué.*\?',
                r'¿.*cómo.*funciona.*\?', r'¿.*puedes.*explicar.*\?'
            ],
            'confirmation': [
                r'sí', r'correcto', r'vale', r'ok', r'perfecto',
                r'está bien', r'de acuerdo'
            ],
            'negation': [
                r'no', r'incorrecto', r'no es así', r'no estoy de acuerdo',
                r'no es correcto'
            ],
            'goodbye': [
                r'adiós', r'hasta luego', r'nos vemos', r'gracias',
                r'chao', r'bye'
            ]
        }
    
    def _initialize_predefined_responses(self) -> Dict[str, str]:
        """Inicializa respuestas predefinidas"""
        return {
            'greeting': "¡Hola! Soy tu asistente especializado en verificación de proyectos arquitectónicos. ¿En qué puedo ayudarte hoy?",
            'help': "Puedo ayudarte con:\n• Preguntas sobre cumplimiento normativo\n• Dudas sobre dimensiones y medidas\n• Consultas de accesibilidad\n• Seguridad contra incendios\n• Aspectos estructurales\n• Resolución de ambigüedades en tu proyecto",
            'goodbye': "¡Ha sido un placer ayudarte! Si tienes más dudas sobre tu proyecto, no dudes en preguntar.",
            'unclear': "No estoy seguro de entender tu pregunta. ¿Podrías reformularla o ser más específico?",
            'no_context': "Para poder ayudarte mejor, necesito que me proporciones más contexto sobre tu proyecto o pregunta específica."
        }
    
    def start_conversation(self, user_id: str, project_id: str, initial_message: str = None) -> ConversationSession:
        """Inicia una nueva conversación"""
        try:
            session_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"
            
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                project_id=project_id,
                state=ConversationState.INITIAL,
                messages=[],
                context_data={},
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # Agregar mensaje inicial del sistema
            if initial_message:
                self._add_message(session, "assistant", initial_message)
            else:
                self._add_message(session, "assistant", self.predefined_responses['greeting'])
            
            # Guardar sesión
            self.active_sessions[session_id] = session
            
            self.logger.info(f"Conversación iniciada: {session_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error iniciando conversación: {e}")
            return None
    
    def process_message(self, session_id: str, user_message: str) -> str:
        """Procesa un mensaje del usuario"""
        try:
            if session_id not in self.active_sessions:
                return "Sesión no encontrada. Por favor, inicia una nueva conversación."
            
            session = self.active_sessions[session_id]
            
            # Agregar mensaje del usuario
            self._add_message(session, "user", user_message)
            
            # Analizar intención
            intent = self._analyze_intent(user_message)
            
            # Procesar según el estado y la intención
            response = self._process_intent(session, user_message, intent)
            
            # Agregar respuesta del asistente
            self._add_message(session, "assistant", response)
            
            # Actualizar estado de la conversación
            self._update_conversation_state(session, intent)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")
            return "Lo siento, ha ocurrido un error. Por favor, intenta de nuevo."
    
    def _add_message(self, session: ConversationSession, message_type: str, content: str, 
                    context: Dict[str, Any] = None, intent: str = None):
        """Agrega un mensaje a la sesión"""
        message = ConversationMessage(
            message_id=f"msg_{len(session.messages) + 1}",
            user_id=session.user_id,
            session_id=session.session_id,
            content=content,
            message_type=message_type,
            timestamp=datetime.now().isoformat(),
            context=context or {},
            intent=intent
        )
        
        session.messages.append(message)
        session.updated_at = datetime.now().isoformat()
    
    def _analyze_intent(self, message: str) -> str:
        """Analiza la intención del mensaje"""
        try:
            message_lower = message.lower()
            
            # Buscar patrones de intención
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, message_lower):
                        return intent
            
            # Si no se encuentra patrón específico, usar IA para clasificar
            return self._classify_intent_with_ai(message)
            
        except Exception as e:
            self.logger.error(f"Error analizando intención: {e}")
            return "unclear"
    
    def _classify_intent_with_ai(self, message: str) -> str:
        """Clasifica la intención usando IA"""
        try:
            prompt = f"""
            Clasifica la siguiente pregunta del usuario en una de estas categorías:
            - greeting: Saludo inicial
            - question_about_compliance: Pregunta sobre cumplimiento normativo
            - question_about_dimensions: Pregunta sobre dimensiones o medidas
            - question_about_accessibility: Pregunta sobre accesibilidad
            - question_about_fire_safety: Pregunta sobre seguridad contra incendios
            - question_about_structure: Pregunta sobre aspectos estructurales
            - request_help: Solicitud de ayuda general
            - request_explanation: Solicitud de explicación
            - confirmation: Confirmación o acuerdo
            - negation: Negación o desacuerdo
            - goodbye: Despedida
            - unclear: No está claro o no se puede clasificar
            
            Pregunta: "{message}"
            
            Responde solo con la categoría correspondiente:
            """
            
            response = self.ai_client.generate_response(prompt)
            
            if response and response.success:
                intent = response.content.strip().lower()
                if intent in self.intent_patterns:
                    return intent
            
            return "unclear"
            
        except Exception as e:
            self.logger.error(f"Error clasificando intención con IA: {e}")
            return "unclear"
    
    def _process_intent(self, session: ConversationSession, message: str, intent: str) -> str:
        """Procesa la intención y genera respuesta"""
        try:
            if intent == "greeting":
                return self._handle_greeting(session)
            elif intent == "request_help":
                return self._handle_help_request(session)
            elif intent == "question_about_compliance":
                return self._handle_compliance_question(session, message)
            elif intent == "question_about_dimensions":
                return self._handle_dimensions_question(session, message)
            elif intent == "question_about_accessibility":
                return self._handle_accessibility_question(session, message)
            elif intent == "question_about_fire_safety":
                return self._handle_fire_safety_question(session, message)
            elif intent == "question_about_structure":
                return self._handle_structure_question(session, message)
            elif intent == "request_explanation":
                return self._handle_explanation_request(session, message)
            elif intent == "confirmation":
                return self._handle_confirmation(session, message)
            elif intent == "negation":
                return self._handle_negation(session, message)
            elif intent == "goodbye":
                return self._handle_goodbye(session)
            else:
                return self._handle_unclear_intent(session, message)
                
        except Exception as e:
            self.logger.error(f"Error procesando intención: {e}")
            return self.predefined_responses['unclear']
    
    def _handle_greeting(self, session: ConversationSession) -> str:
        """Maneja saludos"""
        return self.predefined_responses['greeting']
    
    def _handle_help_request(self, session: ConversationSession) -> str:
        """Maneja solicitudes de ayuda"""
        return self.predefined_responses['help']
    
    def _handle_compliance_question(self, session: ConversationSession, message: str) -> str:
        """Maneja preguntas sobre cumplimiento"""
        try:
            # Buscar información relevante en el grafo de conocimiento
            project_id = session.project_id
            
            # Obtener problemas de cumplimiento del proyecto
            compliance_issues = self.neo4j_manager.find_compliance_issues(project_id)
            
            if compliance_issues:
                response = "He encontrado los siguientes problemas de cumplimiento en tu proyecto:\n\n"
                for i, issue in enumerate(compliance_issues[:5], 1):
                    response += f"{i}. **{issue.get('title', 'Problema')}**\n"
                    response += f"   - Severidad: {issue.get('severity', 'MEDIUM')}\n"
                    response += f"   - Descripción: {issue.get('description', '')}\n\n"
                
                response += "¿Te gustaría que profundice en alguno de estos problemas?"
            else:
                response = "No he encontrado problemas de cumplimiento específicos en tu proyecto. ¿Podrías ser más específico sobre qué aspecto del cumplimiento te interesa?"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error manejando pregunta de cumplimiento: {e}")
            return "Lo siento, no puedo acceder a la información de cumplimiento en este momento. ¿Podrías reformular tu pregunta?"
    
    def _handle_dimensions_question(self, session: ConversationSession, message: str) -> str:
        """Maneja preguntas sobre dimensiones"""
        try:
            # Buscar información de dimensiones en el contexto
            if session.context_data and 'dimension_analysis' in session.context_data:
                dim_analysis = session.context_data['dimension_analysis']
                
                response = "Aquí tienes información sobre las dimensiones de tu proyecto:\n\n"
                
                if dim_analysis.get('total_area'):
                    response += f"• **Área total**: {dim_analysis['total_area']:.2f} m²\n"
                
                if dim_analysis.get('room_areas'):
                    response += "• **Áreas de habitaciones**:\n"
                    for room, area in dim_analysis['room_areas'].items():
                        response += f"  - {room}: {area:.2f} m²\n"
                
                if dim_analysis.get('wall_lengths'):
                    response += f"• **Longitudes de muros**: {len(dim_analysis['wall_lengths'])} muros detectados\n"
                
                if dim_analysis.get('door_widths'):
                    response += f"• **Anchos de puertas**: {len(dim_analysis['door_widths'])} puertas detectadas\n"
                
                response += "\n¿Hay alguna dimensión específica que te interese?"
            else:
                response = "No tengo información de dimensiones disponible en este momento. ¿Podrías proporcionar más detalles sobre qué dimensiones te interesan?"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error manejando pregunta de dimensiones: {e}")
            return "Lo siento, no puedo acceder a la información de dimensiones en este momento."
    
    def _handle_accessibility_question(self, session: ConversationSession, message: str) -> str:
        """Maneja preguntas sobre accesibilidad"""
        try:
            response = "**Información sobre Accesibilidad:**\n\n"
            
            # Buscar características de accesibilidad en el proyecto
            if session.context_data and 'plan_analysis' in session.context_data:
                plan_analysis = session.context_data['plan_analysis']
                
                if plan_analysis.get('accessibility_issues'):
                    response += "**Problemas detectados:**\n"
                    for issue in plan_analysis['accessibility_issues']:
                        response += f"• {issue}\n"
                else:
                    response += "✅ No se han detectado problemas de accesibilidad\n"
                
                if plan_analysis.get('accessibility_features'):
                    response += "\n**Características detectadas:**\n"
                    for feature in plan_analysis['accessibility_features']:
                        response += f"• {feature}\n"
            
            response += "\n**Requisitos básicos de accesibilidad:**\n"
            response += "• Puertas con ancho mínimo de 0.8m\n"
            response += "• Pasillos con ancho mínimo de 1.2m\n"
            response += "• Rampas con pendiente máxima del 8%\n"
            response += "• Ascensores en edificios de más de 3 plantas\n"
            
            response += "\n¿Hay algún aspecto específico de accesibilidad que te preocupe?"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error manejando pregunta de accesibilidad: {e}")
            return "Lo siento, no puedo acceder a la información de accesibilidad en este momento."
    
    def _handle_fire_safety_question(self, session: ConversationSession, message: str) -> str:
        """Maneja preguntas sobre seguridad contra incendios"""
        try:
            response = "**Información sobre Seguridad contra Incendios:**\n\n"
            
            # Buscar información de seguridad contra incendios
            if session.context_data and 'plan_analysis' in session.context_data:
                plan_analysis = session.context_data['plan_analysis']
                
                if plan_analysis.get('fire_safety_issues'):
                    response += "**Problemas detectados:**\n"
                    for issue in plan_analysis['fire_safety_issues']:
                        response += f"• {issue}\n"
                else:
                    response += "✅ No se han detectado problemas de seguridad contra incendios\n"
            
            response += "\n**Requisitos básicos de seguridad contra incendios:**\n"
            response += "• Mínimo 2 salidas de emergencia\n"
            response += "• Distancia máxima de evacuación: 30m\n"
            response += "• Compartimentación resistente al fuego\n"
            response += "• Sistemas de detección y alarma\n"
            response += "• Extintores en ubicaciones estratégicas\n"
            
            response += "\n¿Hay algún aspecto específico de seguridad contra incendios que te interese?"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error manejando pregunta de seguridad contra incendios: {e}")
            return "Lo siento, no puedo acceder a la información de seguridad contra incendios en este momento."
    
    def _handle_structure_question(self, session: ConversationSession, message: str) -> str:
        """Maneja preguntas sobre aspectos estructurales"""
        try:
            response = "**Información sobre Aspectos Estructurales:**\n\n"
            
            # Buscar información estructural
            if session.context_data and 'plan_analysis' in session.context_data:
                plan_analysis = session.context_data['plan_analysis']
                
                if plan_analysis.get('structural_issues'):
                    response += "**Problemas detectados:**\n"
                    for issue in plan_analysis['structural_issues']:
                        response += f"• {issue}\n"
                else:
                    response += "✅ No se han detectado problemas estructurales\n"
            
            response += "\n**Aspectos estructurales importantes:**\n"
            response += "• Cimentación adecuada para el tipo de suelo\n"
            response += "• Estructura portante resistente\n"
            response += "• Muros de carga con espesor mínimo\n"
            response += "• Vigas y columnas dimensionadas correctamente\n"
            response += "• Conexiones estructurales apropiadas\n"
            
            response += "\n¿Hay algún aspecto estructural específico que te preocupe?"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error manejando pregunta estructural: {e}")
            return "Lo siento, no puedo acceder a la información estructural en este momento."
    
    def _handle_explanation_request(self, session: ConversationSession, message: str) -> str:
        """Maneja solicitudes de explicación"""
        try:
            # Usar IA para generar explicación detallada
            prompt = f"""
            El usuario solicita una explicación sobre: "{message}"
            
            Contexto del proyecto:
            - Proyecto ID: {session.project_id}
            - Estado: {session.state.value}
            
            Proporciona una explicación clara y detallada, incluyendo:
            1. Qué significa el concepto o término
            2. Por qué es importante en arquitectura
            3. Cómo se aplica en su proyecto
            4. Referencias normativas si es relevante
            
            Explicación:
            """
            
            response = self.ai_client.generate_response(prompt)
            
            if response and response.success:
                return response.content
            else:
                return "Lo siento, no puedo proporcionar una explicación detallada en este momento. ¿Podrías ser más específico sobre qué te gustaría que explique?"
                
        except Exception as e:
            self.logger.error(f"Error manejando solicitud de explicación: {e}")
            return "Lo siento, no puedo proporcionar una explicación en este momento."
    
    def _handle_confirmation(self, session: ConversationSession, message: str) -> str:
        """Maneja confirmaciones"""
        return "Perfecto, continuemos. ¿Hay algo más en lo que pueda ayudarte?"
    
    def _handle_negation(self, session: ConversationSession, message: str) -> str:
        """Maneja negaciones"""
        return "Entiendo. ¿Podrías explicarme mejor cuál es tu situación o qué necesitas?"
    
    def _handle_goodbye(self, session: ConversationSession) -> str:
        """Maneja despedidas"""
        # Marcar sesión como completada
        session.state = ConversationState.COMPLETED
        return self.predefined_responses['goodbye']
    
    def _handle_unclear_intent(self, session: ConversationSession, message: str) -> str:
        """Maneja intenciones no claras"""
        return self.predefined_responses['unclear']
    
    def _update_conversation_state(self, session: ConversationSession, intent: str):
        """Actualiza el estado de la conversación"""
        try:
            if intent == "goodbye":
                session.state = ConversationState.COMPLETED
            elif intent in ["question_about_compliance", "question_about_dimensions", 
                          "question_about_accessibility", "question_about_fire_safety", 
                          "question_about_structure"]:
                session.state = ConversationState.QUESTION_ANALYSIS
            elif intent == "request_explanation":
                session.state = ConversationState.INFORMATION_GATHERING
            elif intent == "confirmation":
                session.state = ConversationState.SOLUTION_PROPOSAL
            elif intent == "negation":
                session.state = ConversationState.CLARIFICATION
            
            session.updated_at = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error actualizando estado de conversación: {e}")
    
    def set_context_data(self, session_id: str, context_data: Dict[str, Any]):
        """Establece datos de contexto para la sesión"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].context_data = context_data
                self.logger.info(f"Contexto actualizado para sesión {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error estableciendo contexto: {e}")
    
    def get_conversation_history(self, session_id: str) -> List[ConversationMessage]:
        """Obtiene el historial de la conversación"""
        try:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id].messages
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def end_conversation(self, session_id: str) -> bool:
        """Termina una conversación"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].state = ConversationState.COMPLETED
                del self.active_sessions[session_id]
                self.logger.info(f"Conversación {session_id} terminada")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error terminando conversación: {e}")
            return False
