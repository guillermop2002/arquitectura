"""
Acción SIMPLE para Rasa: Solo recibe mensajes y los pasa a la LLM.
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import json

class ActionProcesarConLLM(Action):
    """Acción que recibe cualquier mensaje y lo pasa a la LLM para procesamiento."""
    
    def name(self) -> Text:
        return "action_procesar_con_llm"
    
    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obtener el mensaje del usuario
        user_message = tracker.latest_message.get('text', '')
        
        # Enviar a la LLM (Groq) a través de la API de la aplicación principal
        try:
            # Llamar a la API de la aplicación principal
            response = requests.post(
                'http://verificacion-app:5000/api/chat',
                json={
                    'message': user_message,
                    'session_id': tracker.sender_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                llm_response = data.get('response', 'No se pudo procesar la consulta.')
                dispatcher.utter_message(text=llm_response)
            else:
                dispatcher.utter_message(text="Error al procesar la consulta. Inténtalo de nuevo.")
                
        except Exception as e:
            dispatcher.utter_message(text=f"Error de conexión: {str(e)}")
        
        return []
