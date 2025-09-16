"""
Módulo de Integración con Rasa como Microservicio
Sistema Conversacional Avanzado
"""

import os
import sys
import json
import logging
import httpx
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import AppConfig

logger = logging.getLogger(__name__)

class RasaIntegration:
    """Integración con Rasa como microservicio."""
    
    def __init__(self, config: AppConfig):
        """Inicializar integración con Rasa."""
        self.config = config
        self.rasa_url = config.rasa.url
        self.timeout = config.rasa.timeout
        self.max_retries = config.rasa.max_retries
        self.enabled = config.rasa.enabled
        
        # Cliente HTTP para comunicación con Rasa
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Estado de conversaciones activas
        self.active_sessions: Dict[str, Dict] = {}
        
        logger.info(f"RasaIntegration initialized - URL: {self.rasa_url}, Enabled: {self.enabled}")
    
    async def process_message(self, 
                            message: str, 
                            session_id: str,
                            project_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Procesar mensaje del usuario usando Rasa como microservicio.
        
        Args:
            message: Mensaje del usuario
            session_id: ID de la sesión
            project_context: Contexto del proyecto (opcional)
            
        Returns:
            Dict con la respuesta procesada
        """
        try:
            if not self.enabled:
                return {
                    "response": "El sistema conversacional está temporalmente deshabilitado.",
                    "intent": "system_disabled",
                    "confidence": 1.0,
                    "entities": [],
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Preparar payload para Rasa
            payload = {
                "sender": session_id,
                "message": message
            }
            
            # Agregar contexto del proyecto si está disponible
            if project_context:
                payload["metadata"] = {
                    "project_context": project_context
                }
            
            # Enviar mensaje a Rasa
            response = await self.client.post(
                f"{self.rasa_url}/webhooks/rest/webhook",
                json=payload
            )
            
            if response.status_code == 200:
                rasa_data = response.json()
                
                # Procesar respuesta de Rasa
                if rasa_data and len(rasa_data) > 0:
                    rasa_response = rasa_data[0]
                    return {
                        "response": rasa_response.get("text", "No pude procesar tu mensaje."),
                        "intent": rasa_response.get("intent", "unknown"),
                        "confidence": rasa_response.get("confidence", 0.0),
                        "entities": rasa_response.get("entities", []),
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "rasa_metadata": rasa_response.get("metadata", {})
                    }
                else:
                    return {
                        "response": "No recibí una respuesta válida del sistema conversacional.",
                        "intent": "no_response",
                        "confidence": 0.0,
                        "entities": [],
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                logger.error(f"Rasa API error: {response.status_code} - {response.text}")
                return {
                    "response": "El sistema conversacional no está disponible en este momento.",
                    "intent": "service_unavailable",
                    "confidence": 0.0,
                    "entities": [],
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing message with Rasa: {e}")
            return {
                "response": "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo.",
                "intent": "error",
                "confidence": 0.0,
                "entities": [],
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Obtener historial de conversación de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Lista de mensajes del historial
        """
        try:
            if not self.enabled:
                return []
            
            # Obtener historial de Rasa
            response = await self.client.get(
                f"{self.rasa_url}/conversations/{session_id}/tracker/events"
            )
            
            if response.status_code == 200:
                events = response.json()
                history = []
                
                for event in events:
                    if event.get("event") == "user":
                        history.append({
                            "type": "user",
                            "message": event.get("text", ""),
                            "timestamp": event.get("timestamp", "")
                        })
                    elif event.get("event") == "bot":
                        history.append({
                            "type": "assistant",
                            "message": event.get("text", ""),
                            "timestamp": event.get("timestamp", "")
                        })
                
                return history
            else:
                logger.error(f"Error getting session history: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []
    
    async def clear_session(self, session_id: str) -> bool:
        """
        Limpiar conversación de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            True si se limpió correctamente
        """
        try:
            if not self.enabled:
                return True
            
            # Limpiar sesión en Rasa
            response = await self.client.post(
                f"{self.rasa_url}/conversations/{session_id}/tracker/events",
                json={"event": "restart"}
            )
            
            if response.status_code == 200:
                # Limpiar sesión local
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                return True
            else:
                logger.error(f"Error clearing session: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verificar estado del microservicio de Rasa.
        
        Returns:
            Dict con el estado del servicio
        """
        try:
            if not self.enabled:
                return {
                    "status": "disabled",
                    "message": "Rasa está deshabilitado en la configuración"
                }
            
            response = await self.client.get(f"{self.rasa_url}/health")
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "message": "Rasa está funcionando correctamente",
                    "rasa_url": self.rasa_url
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Rasa respondió con código {response.status_code}",
                    "rasa_url": self.rasa_url
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error conectando con Rasa: {str(e)}",
                "rasa_url": self.rasa_url
            }
    
    async def close(self):
        """Cerrar cliente HTTP."""
        try:
            await self.client.aclose()
            logger.info("RasaIntegration client closed")
        except Exception as e:
            logger.error(f"Error closing RasaIntegration client: {e}")
    
    def __del__(self):
        """Destructor para cerrar cliente."""
        try:
            if hasattr(self, 'client'):
                asyncio.create_task(self.client.aclose())
        except:
            pass