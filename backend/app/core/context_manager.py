"""
Gestión de Contexto Mejorada para Sistema Conversacional
Fase 4: Sistema Conversacional Avanzado
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import AppConfig
from backend.app.core.neo4j_manager import Neo4jManager

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """Tipos de contexto de conversación."""
    PROJECT_ANALYSIS = "project_analysis"
    NORM_COMPLIANCE = "norm_compliance"
    DIMENSION_VERIFICATION = "dimension_verification"
    ACCESSIBILITY_CHECK = "accessibility_check"
    FIRE_SAFETY_CHECK = "fire_safety_check"
    STRUCTURAL_ANALYSIS = "structural_analysis"
    PLAN_ANALYSIS = "plan_analysis"
    DOCUMENT_VERIFICATION = "document_verification"
    COMPLIANCE_REPORT = "compliance_report"
    TECHNICAL_SPECIFICATION = "technical_specification"
    REGULATION_LOOKUP = "regulation_lookup"

@dataclass
class ProjectContext:
    """Contexto del proyecto actual."""
    project_id: str
    project_type: str
    project_name: Optional[str] = None
    location: Optional[str] = None
    building_type: Optional[str] = None
    total_area: Optional[float] = None
    floors: Optional[int] = None
    created_at: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class ConversationContext:
    """Contexto de la conversación actual."""
    session_id: str
    user_id: str
    current_intent: Optional[str] = None
    current_entities: List[Dict[str, Any]] = None
    conversation_history: List[Dict[str, Any]] = None
    project_context: Optional[ProjectContext] = None
    analysis_results: Optional[Dict[str, Any]] = None
    pending_questions: List[str] = None
    resolved_issues: List[str] = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.current_entities is None:
            self.current_entities = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.pending_questions is None:
            self.pending_questions = []
        if self.resolved_issues is None:
            self.resolved_issues = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()

@dataclass
class ContextMemory:
    """Memoria de contexto persistente."""
    user_preferences: Dict[str, Any] = None
    project_templates: Dict[str, Any] = None
    norm_knowledge: Dict[str, Any] = None
    analysis_patterns: Dict[str, Any] = None
    common_issues: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.project_templates is None:
            self.project_templates = {}
        if self.norm_knowledge is None:
            self.norm_knowledge = {}
        if self.analysis_patterns is None:
            self.analysis_patterns = {}
        if self.common_issues is None:
            self.common_issues = {}

class ContextManager:
    """Gestor de contexto mejorado para conversaciones arquitectónicas."""
    
    def __init__(self, config: AppConfig):
        """Inicializar gestor de contexto."""
        self.config = config
        self.neo4j_manager = Neo4jManager(config.neo4j)
        
        # Almacenamiento en memoria de contextos activos
        self.active_contexts: Dict[str, ConversationContext] = {}
        self.project_contexts: Dict[str, ProjectContext] = {}
        self.context_memory = ContextMemory()
        
        # Configuración de persistencia
        self.context_storage_path = Path("context_storage")
        self.context_storage_path.mkdir(exist_ok=True)
        
        logger.info("ContextManager initialized successfully")
    
    async def create_conversation_context(self, 
                                        session_id: str, 
                                        user_id: str,
                                        project_context: Optional[ProjectContext] = None) -> ConversationContext:
        """Crear nuevo contexto de conversación."""
        try:
            context = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                project_context=project_context
            )
            
            self.active_contexts[session_id] = context
            
            # Persistir en Neo4j
            await self._persist_conversation_context(context)
            
            logger.info(f"Created conversation context for session {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error creating conversation context: {e}")
            raise
    
    async def update_conversation_context(self, 
                                        session_id: str, 
                                        intent: str,
                                        entities: List[Dict[str, Any]],
                                        message: str,
                                        response: str) -> ConversationContext:
        """Actualizar contexto de conversación."""
        try:
            if session_id not in self.active_contexts:
                raise ValueError(f"Conversation context {session_id} not found")
            
            context = self.active_contexts[session_id]
            
            # Actualizar contexto
            context.current_intent = intent
            context.current_entities = entities
            context.last_activity = datetime.now()
            
            # Agregar mensaje al historial
            context.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "role": "user",
                "content": message,
                "intent": intent,
                "entities": entities
            })
            
            context.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "role": "assistant",
                "content": response,
                "intent": intent
            })
            
            # Mantener solo los últimos 50 mensajes
            if len(context.conversation_history) > 50:
                context.conversation_history = context.conversation_history[-50:]
            
            # Actualizar contexto en Neo4j
            await self._persist_conversation_context(context)
            
            logger.info(f"Updated conversation context for session {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error updating conversation context: {e}")
            raise
    
    async def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Obtener contexto de conversación."""
        try:
            if session_id in self.active_contexts:
                return self.active_contexts[session_id]
            
            # Intentar cargar desde Neo4j
            context = await self._load_conversation_context(session_id)
            if context:
                self.active_contexts[session_id] = context
                return context
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return None
    
    async def update_project_context(self, 
                                   project_id: str, 
                                   project_data: Dict[str, Any]) -> ProjectContext:
        """Actualizar contexto del proyecto."""
        try:
            if project_id in self.project_contexts:
                project_context = self.project_contexts[project_id]
                # Actualizar campos
                for key, value in project_data.items():
                    if hasattr(project_context, key):
                        setattr(project_context, key, value)
                project_context.last_updated = datetime.now()
            else:
                project_context = ProjectContext(
                    project_id=project_id,
                    **project_data
                )
                self.project_contexts[project_id] = project_context
            
            # Persistir en Neo4j
            await self._persist_project_context(project_context)
            
            logger.info(f"Updated project context for project {project_id}")
            return project_context
            
        except Exception as e:
            logger.error(f"Error updating project context: {e}")
            raise
    
    async def get_project_context(self, project_id: str) -> Optional[ProjectContext]:
        """Obtener contexto del proyecto."""
        try:
            if project_id in self.project_contexts:
                return self.project_contexts[project_id]
            
            # Intentar cargar desde Neo4j
            project_context = await self._load_project_context(project_id)
            if project_context:
                self.project_contexts[project_id] = project_context
                return project_context
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return None
    
    async def add_analysis_result(self, 
                                session_id: str, 
                                analysis_type: str,
                                result: Dict[str, Any]) -> bool:
        """Agregar resultado de análisis al contexto."""
        try:
            context = await self.get_conversation_context(session_id)
            if not context:
                return False
            
            if context.analysis_results is None:
                context.analysis_results = {}
            
            context.analysis_results[analysis_type] = {
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Actualizar en memoria y persistir
            self.active_contexts[session_id] = context
            await self._persist_conversation_context(context)
            
            logger.info(f"Added analysis result for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding analysis result: {e}")
            return False
    
    async def add_pending_question(self, 
                                 session_id: str, 
                                 question: str) -> bool:
        """Agregar pregunta pendiente al contexto."""
        try:
            context = await self.get_conversation_context(session_id)
            if not context:
                return False
            
            if question not in context.pending_questions:
                context.pending_questions.append(question)
                context.last_activity = datetime.now()
                
                # Actualizar en memoria y persistir
                self.active_contexts[session_id] = context
                await self._persist_conversation_context(context)
            
            logger.info(f"Added pending question for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding pending question: {e}")
            return False
    
    async def resolve_question(self, 
                             session_id: str, 
                             question: str,
                             resolution: str) -> bool:
        """Resolver pregunta pendiente."""
        try:
            context = await self.get_conversation_context(session_id)
            if not context:
                return False
            
            if question in context.pending_questions:
                context.pending_questions.remove(question)
                context.resolved_issues.append({
                    "question": question,
                    "resolution": resolution,
                    "timestamp": datetime.now().isoformat()
                })
                context.last_activity = datetime.now()
                
                # Actualizar en memoria y persistir
                self.active_contexts[session_id] = context
                await self._persist_conversation_context(context)
            
            logger.info(f"Resolved question for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving question: {e}")
            return False
    
    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtener resumen del contexto de conversación."""
        try:
            context = await self.get_conversation_context(session_id)
            if not context:
                return {}
            
            return {
                "session_id": session_id,
                "user_id": context.user_id,
                "current_intent": context.current_intent,
                "project_info": asdict(context.project_context) if context.project_context else None,
                "conversation_length": len(context.conversation_history),
                "pending_questions": len(context.pending_questions),
                "resolved_issues": len(context.resolved_issues),
                "analysis_results": list(context.analysis_results.keys()) if context.analysis_results else [],
                "last_activity": context.last_activity.isoformat(),
                "created_at": context.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return {}
    
    async def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """Limpiar contextos antiguos."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            # Limpiar contextos en memoria
            sessions_to_remove = []
            for session_id, context in self.active_contexts.items():
                if context.last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.active_contexts[session_id]
                cleaned_count += 1
            
            # Limpiar contextos en Neo4j
            await self._cleanup_neo4j_contexts(cutoff_time)
            
            logger.info(f"Cleaned up {cleaned_count} old contexts")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old contexts: {e}")
            return 0
    
    async def _persist_conversation_context(self, context: ConversationContext) -> bool:
        """Persistir contexto de conversación en Neo4j."""
        try:
            # Crear nodo de contexto de conversación
            context_data = {
                "session_id": context.session_id,
                "user_id": context.user_id,
                "current_intent": context.current_intent,
                "created_at": context.created_at.isoformat(),
                "last_activity": context.last_activity.isoformat(),
                "conversation_length": len(context.conversation_history),
                "pending_questions_count": len(context.pending_questions),
                "resolved_issues_count": len(context.resolved_issues)
            }
            
            await self.neo4j_manager.create_node(
                "ConversationContext",
                context.session_id,
                context_data
            )
            
            # Crear relaciones con proyecto si existe
            if context.project_context:
                await self.neo4j_manager.create_relationship(
                    "ConversationContext",
                    context.session_id,
                    "HAS_PROJECT",
                    "Project",
                    context.project_context.project_id
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error persisting conversation context: {e}")
            return False
    
    async def _load_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Cargar contexto de conversación desde Neo4j."""
        try:
            # Implementar carga desde Neo4j
            # Por ahora retornar None
            return None
            
        except Exception as e:
            logger.error(f"Error loading conversation context: {e}")
            return None
    
    async def _persist_project_context(self, project_context: ProjectContext) -> bool:
        """Persistir contexto del proyecto en Neo4j."""
        try:
            project_data = asdict(project_context)
            project_data["created_at"] = project_context.created_at.isoformat()
            project_data["last_updated"] = project_context.last_updated.isoformat()
            
            await self.neo4j_manager.create_node(
                "Project",
                project_context.project_id,
                project_data
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error persisting project context: {e}")
            return False
    
    async def _load_project_context(self, project_id: str) -> Optional[ProjectContext]:
        """Cargar contexto del proyecto desde Neo4j."""
        try:
            # Implementar carga desde Neo4j
            # Por ahora retornar None
            return None
            
        except Exception as e:
            logger.error(f"Error loading project context: {e}")
            return None
    
    async def _cleanup_neo4j_contexts(self, cutoff_time: datetime) -> int:
        """Limpiar contextos antiguos en Neo4j."""
        try:
            # Implementar limpieza en Neo4j
            # Por ahora retornar 0
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up Neo4j contexts: {e}")
            return 0
