"""
Acciones Personalizadas para Rasa
Fase 4: Sistema Conversacional Avanzado
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Text
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import AppConfig
from backend.app.core.rasa_integration import RasaIntegration
from backend.app.core.enhanced_project_analyzer_v4 import EnhancedProjectAnalyzerV4
from backend.app.core.intelligent_question_engine import IntelligentQuestionEngine
from backend.app.core.neo4j_manager import Neo4jManager

logger = logging.getLogger(__name__)

class ArchitecturalActions:
    """Acciones personalizadas para el chatbot arquitectónico."""
    
    def __init__(self):
        """Inicializar acciones."""
        self.config = AppConfig()
        self.analyzer_v4 = EnhancedProjectAnalyzerV4()
        self.question_engine = IntelligentQuestionEngine()
        self.neo4j_manager = Neo4jManager(self.config.neo4j)
        
        logger.info("ArchitecturalActions initialized")
    
    async def action_architectural_analysis(self, 
                                          tracker, 
                                          dispatcher, 
                                          domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para análisis arquitectónico general."""
        try:
            # Obtener entidades del tracker
            entities = tracker.latest_message.get("entities", [])
            project_type = next((e["value"] for e in entities if e["entity"] == "project_type"), "residencial")
            
            # Generar respuesta contextual
            response = f"Perfecto, voy a realizar un análisis arquitectónico completo para tu proyecto {project_type}. "
            response += "¿Tienes los planos y la memoria técnica disponibles para el análisis?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_architectural_analysis: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en el análisis arquitectónico.")
            return []
    
    async def action_norm_compliance_check(self, 
                                         tracker, 
                                         dispatcher, 
                                         domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para verificación de cumplimiento normativo."""
        try:
            entities = tracker.latest_message.get("entities", [])
            regulation_code = next((e["value"] for e in entities if e["entity"] == "regulation_code"), "CTE")
            building_element = next((e["value"] for e in entities if e["entity"] == "building_element"), "elemento")
            
            # Información específica por normativa
            norm_info = {
                "db-he": "Ahorro de energía - Verificación de aislamiento, eficiencia energética y sostenibilidad",
                "db-si": "Seguridad contra incendios - Distancias de evacuación, compartimentación y detección",
                "db-sua": "Accesibilidad universal - Anchos de paso, rampas, ascensores y señalización",
                "db-se": "Seguridad estructural - Cálculos de resistencia, estabilidad y cimentaciones",
                "db-hr": "Protección frente al ruido - Aislamiento acústico y condiciones de habitabilidad",
                "cte": "Código Técnico de la Edificación - Verificación general de cumplimiento"
            }
            
            regulation_info = norm_info.get(regulation_code.lower(), norm_info["cte"])
            
            response = f"Te ayudo a verificar el cumplimiento de la normativa {regulation_code.upper()}. "
            response += f"Esta normativa se enfoca en: {regulation_info}. "
            response += f"¿Qué elemento específico ({building_element}) quieres verificar según esta normativa?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_norm_compliance_check: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en la verificación normativa.")
            return []
    
    async def action_dimension_verification(self, 
                                          tracker, 
                                          dispatcher, 
                                          domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para verificación de dimensiones."""
        try:
            entities = tracker.latest_message.get("entities", [])
            building_element = next((e["value"] for e in entities if e["entity"] == "building_element"), "elemento")
            dimension_value = next((e["value"] for e in entities if e["entity"] == "dimension_value"), None)
            
            # Dimensiones mínimas según normativa
            min_dimensions = {
                "pasillo": "1.20m de ancho mínimo",
                "puerta": "0.80m de ancho mínimo",
                "ventana": "1/8 de la superficie de la habitación",
                "escalera": "0.80m de ancho mínimo",
                "rampa": "máximo 8% de pendiente",
                "ascensor": "1.10m x 1.40m mínimo",
                "baño": "1.50m x 1.50m mínimo accesible"
            }
            
            element_info = min_dimensions.get(building_element.lower(), "dimensiones específicas según normativa")
            
            response = f"Para verificar las dimensiones del {building_element}, "
            response += f"las dimensiones mínimas son: {element_info}. "
            
            if dimension_value:
                response += f"¿Quieres verificar si la dimensión {dimension_value} cumple con la normativa?"
            else:
                response += "¿Qué dimensión específica necesitas verificar?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_dimension_verification: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en la verificación de dimensiones.")
            return []
    
    async def action_accessibility_check(self, 
                                       tracker, 
                                       dispatcher, 
                                       domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para verificación de accesibilidad."""
        try:
            entities = tracker.latest_message.get("entities", [])
            accessibility_feature = next((e["value"] for e in entities if e["entity"] == "accessibility_feature"), "accesibilidad")
            
            # Requisitos de accesibilidad según DB-SUA
            accessibility_requirements = {
                "rampa": "Pendiente máxima 8%, ancho mínimo 1.20m, pasamanos a 0.90m",
                "ascensor": "Dimensiones mínimas 1.10m x 1.40m, botonera accesible",
                "pasamanos": "Altura 0.90m, diámetro 3-4cm, continuidad en tramos",
                "ancho": "Pasillos 1.20m mínimo, puertas 0.80m mínimo",
                "altura": "Altura libre 2.20m mínimo en itinerarios accesibles",
                "baño": "Superficie mínima 1.50m x 1.50m, elementos accesibles"
            }
            
            feature_info = accessibility_requirements.get(accessibility_feature.lower(), 
                                                        "requisitos específicos según DB-SUA")
            
            response = f"Para la accesibilidad del {accessibility_feature}, "
            response += f"los requisitos son: {feature_info}. "
            response += "¿Quieres verificar algún elemento específico de accesibilidad en tu proyecto?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_accessibility_check: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en la verificación de accesibilidad.")
            return []
    
    async def action_fire_safety_check(self, 
                                     tracker, 
                                     dispatcher, 
                                     domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para verificación de seguridad contra incendios."""
        try:
            entities = tracker.latest_message.get("entities", [])
            safety_requirement = next((e["value"] for e in entities if e["entity"] == "safety_requirement"), "seguridad")
            
            # Requisitos de seguridad según DB-SI
            safety_requirements = {
                "evacuación": "Distancia máxima 30m a salida, ancho mínimo 1.20m",
                "salida": "Ancho mínimo 0.80m, altura 2.00m, apertura hacia afuera",
                "detector": "Uno por habitación, interconectados, alimentación de seguridad",
                "extintor": "Uno cada 200m², señalización visible, accesible",
                "alarma": "Sonora y visual, audible en toda la planta, señalización"
            }
            
            safety_info = safety_requirements.get(safety_requirement.lower(), 
                                                 "requisitos específicos según DB-SI")
            
            response = f"Para la seguridad contra incendios del {safety_requirement}, "
            response += f"los requisitos son: {safety_info}. "
            response += "¿Quieres verificar algún elemento específico de seguridad en tu proyecto?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_fire_safety_check: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en la verificación de seguridad.")
            return []
    
    async def action_structural_analysis(self, 
                                       tracker, 
                                       dispatcher, 
                                       domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para análisis estructural."""
        try:
            entities = tracker.latest_message.get("entities", [])
            structural_component = next((e["value"] for e in entities if e["entity"] == "structural_component"), "elemento")
            
            # Requisitos estructurales según DB-SE
            structural_requirements = {
                "viga": "Cálculo de flexión, cortante y torsión según solicitaciones",
                "pilar": "Cálculo de compresión, pandeo y esbeltez",
                "losa": "Cálculo de flexión, cortante y punzonamiento",
                "cimentación": "Cálculo de capacidad portante y asientos",
                "muro": "Cálculo de resistencia y estabilidad"
            }
            
            component_info = structural_requirements.get(structural_component.lower(), 
                                                       "cálculos específicos según DB-SE")
            
            response = f"Para el análisis estructural del {structural_component}, "
            response += f"se requieren: {component_info}. "
            response += "¿Tienes los cálculos estructurales del proyecto para verificar?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_structural_analysis: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en el análisis estructural.")
            return []
    
    async def action_plan_analysis(self, 
                                 tracker, 
                                 dispatcher, 
                                 domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para análisis de planos."""
        try:
            entities = tracker.latest_message.get("entities", [])
            room_type = next((e["value"] for e in entities if e["entity"] == "room_type"), "habitación")
            
            response = f"Perfecto, voy a analizar los planos de tu proyecto. "
            response += f"¿Qué tipo de análisis necesitas para las {room_type}s?\n\n"
            response += "• Verificación de dimensiones\n"
            response += "• Análisis de accesibilidad\n"
            response += "• Seguridad contra incendios\n"
            response += "• Cumplimiento normativo general\n"
            response += "• Detección de elementos arquitectónicos"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_plan_analysis: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en el análisis de planos.")
            return []
    
    async def action_document_verification(self, 
                                         tracker, 
                                         dispatcher, 
                                         domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para verificación de documentación."""
        try:
            response = "Te ayudo a verificar la documentación técnica de tu proyecto. "
            response += "¿Qué documento específico necesitas analizar?\n\n"
            response += "• Memoria técnica y descriptiva\n"
            response += "• Planos arquitectónicos (plantas, alzados, secciones)\n"
            response += "• Cálculos estructurales\n"
            response += "• Instalaciones (eléctricas, fontanería, climatización)\n"
            response += "• Anexos y especificaciones técnicas\n"
            response += "• Certificados y justificaciones normativas"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_document_verification: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en la verificación de documentación.")
            return []
    
    async def action_compliance_report(self, 
                                     tracker, 
                                     dispatcher, 
                                     domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para generación de reportes de cumplimiento."""
        try:
            entities = tracker.latest_message.get("entities", [])
            project_type = next((e["value"] for e in entities if e["entity"] == "project_type"), "residencial")
            
            response = f"Perfecto, voy a generar un reporte completo de cumplimiento normativo "
            response += f"para tu proyecto {project_type}. El reporte incluirá:\n\n"
            response += "• **Análisis de cumplimiento por normativas**\n"
            response += "• **Verificación de dimensiones y medidas**\n"
            response += "• **Accesibilidad universal (DB-SUA)**\n"
            response += "• **Seguridad contra incendios (DB-SI)**\n"
            response += "• **Ahorro de energía (DB-HE)**\n"
            response += "• **Seguridad estructural (DB-SE)**\n"
            response += "• **Recomendaciones de mejora**\n\n"
            response += "¿Tienes todos los documentos del proyecto listos para el análisis?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_compliance_report: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en la generación del reporte.")
            return []
    
    async def action_technical_specification(self, 
                                           tracker, 
                                           dispatcher, 
                                           domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para especificaciones técnicas."""
        try:
            entities = tracker.latest_message.get("entities", [])
            building_element = next((e["value"] for e in entities if e["entity"] == "building_element"), "elemento")
            
            response = f"Te ayudo con las especificaciones técnicas del {building_element}. "
            response += "¿Qué aspecto específico necesitas verificar?\n\n"
            response += "• **Características de materiales**\n"
            response += "• **Parámetros de diseño**\n"
            response += "• **Requisitos de ejecución**\n"
            response += "• **Condiciones de recepción**\n"
            response += "• **Ensayos y pruebas**\n"
            response += "• **Marcado CE y certificaciones**"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_technical_specification: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en las especificaciones técnicas.")
            return []
    
    async def action_regulation_lookup(self, 
                                     tracker, 
                                     dispatcher, 
                                     domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Acción para consulta de normativas."""
        try:
            entities = tracker.latest_message.get("entities", [])
            regulation_code = next((e["value"] for e in entities if e["entity"] == "regulation_code"), "CTE")
            
            # Información detallada por normativa
            regulation_details = {
                "db-he": {
                    "title": "DB-HE: Ahorro de Energía",
                    "description": "Establece las exigencias básicas de ahorro de energía",
                    "key_points": [
                        "Limitación de demanda energética",
                        "Eficiencia energética de las instalaciones",
                        "Energías renovables",
                        "Certificación energética"
                    ]
                },
                "db-si": {
                    "title": "DB-SI: Seguridad contra Incendios",
                    "description": "Establece las exigencias básicas de seguridad contra incendios",
                    "key_points": [
                        "Compartimentación y sectorización",
                        "Evacuación de ocupantes",
                        "Instalaciones de protección",
                        "Resistencia al fuego de la estructura"
                    ]
                },
                "db-sua": {
                    "title": "DB-SUA: Accesibilidad Universal",
                    "description": "Establece las exigencias básicas de accesibilidad",
                    "key_points": [
                        "Itinerarios accesibles",
                        "Elementos accesibles",
                        "Señalización accesible",
                        "Información accesible"
                    ]
                },
                "db-se": {
                    "title": "DB-SE: Seguridad Estructural",
                    "description": "Establece las exigencias básicas de seguridad estructural",
                    "key_points": [
                        "Resistencia y estabilidad",
                        "Seguridad en caso de incendio",
                        "Seguridad de utilización",
                        "Cimentaciones y contención"
                    ]
                }
            }
            
            reg_info = regulation_details.get(regulation_code.lower(), regulation_details["db-he"])
            
            response = f"**{reg_info['title']}**\n\n"
            response += f"{reg_info['description']}\n\n"
            response += "**Puntos clave:**\n"
            for point in reg_info['key_points']:
                response += f"• {point}\n"
            response += f"\n¿Qué aspecto específico de {regulation_code.upper()} necesitas consultar?"
            
            dispatcher.utter_message(text=response)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in action_regulation_lookup: {e}")
            dispatcher.utter_message(text="Lo siento, hubo un error en la consulta de normativas.")
            return []
