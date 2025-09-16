"""
Acciones personalizadas para Rasa.
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionAnalyzeProject(Action):
    """Acción para analizar un proyecto arquitectónico."""
    
    def name(self) -> Text:
        return "action_analyze_project"
    
    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obtener información del proyecto
        project_type = tracker.get_slot("project_type")
        
        if project_type:
            dispatcher.utter_message(
                text=f"Perfecto, voy a analizar tu proyecto de {project_type}. "
                     "Procesando los documentos y verificando el cumplimiento normativo..."
            )
        else:
            dispatcher.utter_message(
                text="Voy a analizar tu proyecto. Procesando los documentos y verificando el cumplimiento normativo..."
            )
        
        return [SlotSet("project_analyzed", True)]

class ActionCheckCompliance(Action):
    """Acción para verificar cumplimiento normativo."""
    
    def name(self) -> Text:
        return "action_check_compliance"
    
    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker, 
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="Verificando cumplimiento del CTE y normativas aplicables. "
                 "Revisando seguridad estructural, protección contra incendios, "
                 "accesibilidad y eficiencia energética..."
        )
        
        return [SlotSet("compliance_checked", True)]
