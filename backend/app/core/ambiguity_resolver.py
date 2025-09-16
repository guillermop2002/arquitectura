"""
Resolutor de Ambigüedades Automático
Fase 3: Sistema de Preguntas Inteligentes
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import difflib

from .config import get_config
from .logging_config import get_logger
from .ai_client import get_ai_client, AIResponse
from .neo4j_manager import Neo4jManager

logger = get_logger(__name__)

class AmbiguityType(Enum):
    """Tipos de ambigüedades"""
    CONTRADICTION = "contradiction"
    INCOMPLETE_INFO = "incomplete_info"
    UNCLEAR_SPECIFICATION = "unclear_specification"
    MISSING_DIMENSIONS = "missing_dimensions"
    REGULATORY_CONFLICT = "regulatory_conflict"
    TECHNICAL_UNCERTAINTY = "technical_uncertainty"

class ResolutionStrategy(Enum):
    """Estrategias de resolución"""
    ASK_CLARIFICATION = "ask_clarification"
    USE_DEFAULT = "use_default"
    INFER_FROM_CONTEXT = "infer_from_context"
    REQUEST_DOCUMENTATION = "request_documentation"
    CONSULT_EXPERT = "consult_expert"

@dataclass
class Ambiguity:
    """Ambigüedad detectada en el proyecto"""
    ambiguity_id: str
    type: AmbiguityType
    description: str
    context: str
    severity: str  # 'HIGH', 'MEDIUM', 'LOW'
    confidence: float
    source_documents: List[str]
    related_elements: List[str]
    suggested_resolution: str
    resolution_strategy: ResolutionStrategy
    detected_at: str
    status: str  # 'detected', 'resolving', 'resolved', 'failed'

@dataclass
class Resolution:
    """Resolución de una ambigüedad"""
    resolution_id: str
    ambiguity_id: str
    strategy_used: ResolutionStrategy
    resolution_text: str
    confidence: float
    supporting_evidence: List[str]
    resolved_at: str
    verified: bool

class AmbiguityResolver:
    """Resolutor automático de ambigüedades arquitectónicas"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Cliente de IA
        self.ai_client = get_ai_client()
        
        # Gestor de Neo4j
        self.neo4j_manager = Neo4jManager()
        
        # Patrones de ambigüedad
        self.ambiguity_patterns = self._initialize_ambiguity_patterns()
        
        # Estrategias de resolución
        self.resolution_strategies = self._initialize_resolution_strategies()
    
    def _initialize_ambiguity_patterns(self) -> Dict[AmbiguityType, List[str]]:
        """Inicializa patrones para detectar ambigüedades"""
        return {
            AmbiguityType.CONTRADICTION: [
                r'contradice', r'conflicto', r'inconsistente', r'discrepancia',
                r'no coincide', r'diferente a', r'opuesto a'
            ],
            AmbiguityType.INCOMPLETE_INFO: [
                r'no especifica', r'falta información', r'incompleto',
                r'no se menciona', r'sin detalle', r'parcial'
            ],
            AmbiguityType.UNCLEAR_SPECIFICATION: [
                r'no está claro', r'ambiguo', r'confuso', r'poco específico',
                r'vago', r'impreciso', r'no definido'
            ],
            AmbiguityType.MISSING_DIMENSIONS: [
                r'sin dimensiones', r'no especifica medidas', r'falta tamaño',
                r'sin cotas', r'dimensiones no indicadas'
            ],
            AmbiguityType.REGULATORY_CONFLICT: [
                r'no cumple', r'viola', r'contraviene', r'incumple normativa',
                r'no conforme', r'fuera de norma'
            ],
            AmbiguityType.TECHNICAL_UNCERTAINTY: [
                r'no se especifica', r'por determinar', r'a definir',
                r'sin especificar', r'pendiente de'
            ]
        }
    
    def _initialize_resolution_strategies(self) -> Dict[AmbiguityType, List[ResolutionStrategy]]:
        """Inicializa estrategias de resolución por tipo de ambigüedad"""
        return {
            AmbiguityType.CONTRADICTION: [
                ResolutionStrategy.ASK_CLARIFICATION,
                ResolutionStrategy.INFER_FROM_CONTEXT,
                ResolutionStrategy.CONSULT_EXPERT
            ],
            AmbiguityType.INCOMPLETE_INFO: [
                ResolutionStrategy.REQUEST_DOCUMENTATION,
                ResolutionStrategy.ASK_CLARIFICATION,
                ResolutionStrategy.INFER_FROM_CONTEXT
            ],
            AmbiguityType.UNCLEAR_SPECIFICATION: [
                ResolutionStrategy.ASK_CLARIFICATION,
                ResolutionStrategy.INFER_FROM_CONTEXT,
                ResolutionStrategy.USE_DEFAULT
            ],
            AmbiguityType.MISSING_DIMENSIONS: [
                ResolutionStrategy.INFER_FROM_CONTEXT,
                ResolutionStrategy.USE_DEFAULT,
                ResolutionStrategy.ASK_CLARIFICATION
            ],
            AmbiguityType.REGULATORY_CONFLICT: [
                ResolutionStrategy.CONSULT_EXPERT,
                ResolutionStrategy.ASK_CLARIFICATION,
                ResolutionStrategy.REQUEST_DOCUMENTATION
            ],
            AmbiguityType.TECHNICAL_UNCERTAINTY: [
                ResolutionStrategy.ASK_CLARIFICATION,
                ResolutionStrategy.INFER_FROM_CONTEXT,
                ResolutionStrategy.CONSULT_EXPERT
            ]
        }
    
    def detect_ambiguities(self, project_data: Dict[str, Any], 
                          document_analysis: Dict[str, Any],
                          plan_analysis: Dict[str, Any]) -> List[Ambiguity]:
        """Detecta ambigüedades en el proyecto"""
        try:
            self.logger.info("Detectando ambigüedades en el proyecto...")
            
            ambiguities = []
            
            # 1. Detectar contradicciones en documentos
            contradictions = self._detect_contradictions(document_analysis)
            ambiguities.extend(contradictions)
            
            # 2. Detectar información incompleta
            incomplete_info = self._detect_incomplete_information(document_analysis, plan_analysis)
            ambiguities.extend(incomplete_info)
            
            # 3. Detectar especificaciones poco claras
            unclear_specs = self._detect_unclear_specifications(document_analysis)
            ambiguities.extend(unclear_specs)
            
            # 4. Detectar dimensiones faltantes
            missing_dims = self._detect_missing_dimensions(plan_analysis)
            ambiguities.extend(missing_dims)
            
            # 5. Detectar conflictos normativos
            regulatory_conflicts = self._detect_regulatory_conflicts(project_data)
            ambiguities.extend(regulatory_conflicts)
            
            # 6. Detectar incertidumbres técnicas
            technical_uncertainties = self._detect_technical_uncertainties(document_analysis)
            ambiguities.extend(technical_uncertainties)
            
            # Filtrar y priorizar ambigüedades
            filtered_ambiguities = self._filter_and_prioritize_ambiguities(ambiguities)
            
            # Guardar en Neo4j
            for ambiguity in filtered_ambiguities:
                self._save_ambiguity_to_graph(ambiguity, project_data.get('id', 'unknown'))
            
            self.logger.info(f"Detectadas {len(filtered_ambiguities)} ambigüedades")
            return filtered_ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando ambigüedades: {e}")
            return []
    
    def _detect_contradictions(self, document_analysis: Dict[str, Any]) -> List[Ambiguity]:
        """Detecta contradicciones en los documentos"""
        try:
            ambiguities = []
            contradictions = document_analysis.get('contradictions', [])
            
            for i, contradiction in enumerate(contradictions):
                ambiguity = Ambiguity(
                    ambiguity_id=f"contradiction_{i+1}",
                    type=AmbiguityType.CONTRADICTION,
                    description=f"Contradicción entre {contradiction.get('source1', '')} y {contradiction.get('source2', '')}",
                    context=contradiction.get('description', ''),
                    severity='HIGH',
                    confidence=contradiction.get('confidence', 0.8),
                    source_documents=contradiction.get('source_documents', []),
                    related_elements=contradiction.get('related_elements', []),
                    suggested_resolution="Aclarar la información contradictoria",
                    resolution_strategy=ResolutionStrategy.ASK_CLARIFICATION,
                    detected_at=datetime.now().isoformat(),
                    status='detected'
                )
                ambiguities.append(ambiguity)
            
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando contradicciones: {e}")
            return []
    
    def _detect_incomplete_information(self, document_analysis: Dict[str, Any], 
                                     plan_analysis: Dict[str, Any]) -> List[Ambiguity]:
        """Detecta información incompleta"""
        try:
            ambiguities = []
            
            # Verificar confianza del análisis de documentos
            doc_confidence = document_analysis.get('confidence_score', 0)
            if doc_confidence < 0.7:
                ambiguity = Ambiguity(
                    ambiguity_id="incomplete_doc_analysis",
                    type=AmbiguityType.INCOMPLETE_INFO,
                    description="Análisis de documentos con baja confianza",
                    context=f"Confianza del análisis: {doc_confidence:.2f}",
                    severity='MEDIUM',
                    confidence=0.8,
                    source_documents=['document_analysis'],
                    related_elements=[],
                    suggested_resolution="Mejorar calidad de documentos o proporcionar información adicional",
                    resolution_strategy=ResolutionStrategy.REQUEST_DOCUMENTATION,
                    detected_at=datetime.now().isoformat(),
                    status='detected'
                )
                ambiguities.append(ambiguity)
            
            # Verificar elementos de planos con baja confianza
            if plan_analysis.get('elements'):
                low_confidence_elements = [
                    elem for elem in plan_analysis['elements'] 
                    if elem.get('confidence', 0) < 0.6
                ]
                
                if low_confidence_elements:
                    ambiguity = Ambiguity(
                        ambiguity_id="incomplete_plan_elements",
                        type=AmbiguityType.INCOMPLETE_INFO,
                        description=f"Elementos de planos con baja confianza de detección",
                        context=f"{len(low_confidence_elements)} elementos con confianza < 0.6",
                        severity='MEDIUM',
                        confidence=0.7,
                        source_documents=['plan_analysis'],
                        related_elements=[elem.get('id', '') for elem in low_confidence_elements],
                        suggested_resolution="Proporcionar planos de mejor calidad o especificaciones detalladas",
                        resolution_strategy=ResolutionStrategy.REQUEST_DOCUMENTATION,
                        detected_at=datetime.now().isoformat(),
                        status='detected'
                    )
                    ambiguities.append(ambiguity)
            
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando información incompleta: {e}")
            return []
    
    def _detect_unclear_specifications(self, document_analysis: Dict[str, Any]) -> List[Ambiguity]:
        """Detecta especificaciones poco claras"""
        try:
            ambiguities = []
            
            # Buscar texto con patrones de ambigüedad
            extracted_data = document_analysis.get('extracted_data', {})
            
            for key, value in extracted_data.items():
                if isinstance(value, str):
                    for ambiguity_type, patterns in self.ambiguity_patterns.items():
                        if ambiguity_type == AmbiguityType.UNCLEAR_SPECIFICATION:
                            for pattern in patterns:
                                if re.search(pattern, value.lower()):
                                    ambiguity = Ambiguity(
                                        ambiguity_id=f"unclear_spec_{key}",
                                        type=AmbiguityType.UNCLEAR_SPECIFICATION,
                                        description=f"Especificación poco clara en {key}",
                                        context=f"Valor: {value[:200]}...",
                                        severity='MEDIUM',
                                        confidence=0.6,
                                        source_documents=['document_analysis'],
                                        related_elements=[key],
                                        suggested_resolution="Aclarar especificación técnica",
                                        resolution_strategy=ResolutionStrategy.ASK_CLARIFICATION,
                                        detected_at=datetime.now().isoformat(),
                                        status='detected'
                                    )
                                    ambiguities.append(ambiguity)
                                    break
            
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando especificaciones poco claras: {e}")
            return []
    
    def _detect_missing_dimensions(self, plan_analysis: Dict[str, Any]) -> List[Ambiguity]:
        """Detecta dimensiones faltantes"""
        try:
            ambiguities = []
            
            # Verificar elementos sin dimensiones
            if plan_analysis.get('elements'):
                elements_without_dimensions = [
                    elem for elem in plan_analysis['elements']
                    if not elem.get('dimensions') or not elem.get('dimensions').get('width')
                ]
                
                if elements_without_dimensions:
                    ambiguity = Ambiguity(
                        ambiguity_id="missing_dimensions",
                        type=AmbiguityType.MISSING_DIMENSIONS,
                        description="Elementos arquitectónicos sin dimensiones especificadas",
                        context=f"{len(elements_without_dimensions)} elementos sin dimensiones",
                        severity='HIGH',
                        confidence=0.9,
                        source_documents=['plan_analysis'],
                        related_elements=[elem.get('id', '') for elem in elements_without_dimensions],
                        suggested_resolution="Proporcionar dimensiones de todos los elementos",
                        resolution_strategy=ResolutionStrategy.ASK_CLARIFICATION,
                        detected_at=datetime.now().isoformat(),
                        status='detected'
                    )
                    ambiguities.append(ambiguity)
            
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando dimensiones faltantes: {e}")
            return []
    
    def _detect_regulatory_conflicts(self, project_data: Dict[str, Any]) -> List[Ambiguity]:
        """Detecta conflictos normativos"""
        try:
            ambiguities = []
            
            # Buscar problemas de cumplimiento
            compliance_issues = project_data.get('compliance_issues', [])
            
            for i, issue in enumerate(compliance_issues):
                if issue.get('severity') in ['HIGH', 'CRITICAL']:
                    ambiguity = Ambiguity(
                        ambiguity_id=f"regulatory_conflict_{i+1}",
                        type=AmbiguityType.REGULATORY_CONFLICT,
                        description=f"Conflicto normativo: {issue.get('title', '')}",
                        context=issue.get('description', ''),
                        severity='HIGH',
                        confidence=0.9,
                        source_documents=['compliance_analysis'],
                        related_elements=issue.get('related_elements', []),
                        suggested_resolution="Resolver conflicto normativo",
                        resolution_strategy=ResolutionStrategy.CONSULT_EXPERT,
                        detected_at=datetime.now().isoformat(),
                        status='detected'
                    )
                    ambiguities.append(ambiguity)
            
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando conflictos normativos: {e}")
            return []
    
    def _detect_technical_uncertainties(self, document_analysis: Dict[str, Any]) -> List[Ambiguity]:
        """Detecta incertidumbres técnicas"""
        try:
            ambiguities = []
            
            # Buscar términos que indican incertidumbre
            extracted_data = document_analysis.get('extracted_data', {})
            
            uncertainty_terms = [
                'por determinar', 'a definir', 'pendiente de', 'sin especificar',
                'por confirmar', 'a verificar', 'tentativo', 'provisional'
            ]
            
            for key, value in extracted_data.items():
                if isinstance(value, str):
                    for term in uncertainty_terms:
                        if term in value.lower():
                            ambiguity = Ambiguity(
                                ambiguity_id=f"technical_uncertainty_{key}",
                                type=AmbiguityType.TECHNICAL_UNCERTAINTY,
                                description=f"Incertidumbre técnica en {key}",
                                context=f"Término: '{term}' en {value[:200]}...",
                                severity='MEDIUM',
                                confidence=0.7,
                                source_documents=['document_analysis'],
                                related_elements=[key],
                                suggested_resolution="Definir especificación técnica",
                                resolution_strategy=ResolutionStrategy.ASK_CLARIFICATION,
                                detected_at=datetime.now().isoformat(),
                                status='detected'
                            )
                            ambiguities.append(ambiguity)
                            break
            
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando incertidumbres técnicas: {e}")
            return []
    
    def _filter_and_prioritize_ambiguities(self, ambiguities: List[Ambiguity]) -> List[Ambiguity]:
        """Filtra y prioriza las ambigüedades detectadas"""
        try:
            # Eliminar duplicados
            unique_ambiguities = self._remove_duplicate_ambiguities(ambiguities)
            
            # Priorizar por severidad y confianza
            prioritized_ambiguities = sorted(
                unique_ambiguities,
                key=lambda a: (
                    a.severity == 'HIGH',
                    a.confidence,
                    a.type in [AmbiguityType.CONTRADICTION, AmbiguityType.REGULATORY_CONFLICT]
                ),
                reverse=True
            )
            
            # Limitar número de ambigüedades
            max_ambiguities = 15
            filtered_ambiguities = prioritized_ambiguities[:max_ambiguities]
            
            return filtered_ambiguities
            
        except Exception as e:
            self.logger.error(f"Error filtrando ambigüedades: {e}")
            return ambiguities
    
    def _remove_duplicate_ambiguities(self, ambiguities: List[Ambiguity]) -> List[Ambiguity]:
        """Elimina ambigüedades duplicadas"""
        try:
            unique_ambiguities = []
            seen_descriptions = set()
            
            for ambiguity in ambiguities:
                # Crear clave única basada en descripción y tipo
                key = f"{ambiguity.type.value}_{ambiguity.description[:100]}"
                
                if key not in seen_descriptions:
                    unique_ambiguities.append(ambiguity)
                    seen_descriptions.add(key)
            
            return unique_ambiguities
            
        except Exception as e:
            self.logger.error(f"Error eliminando duplicados: {e}")
            return ambiguities
    
    def resolve_ambiguity(self, ambiguity: Ambiguity, context: Dict[str, Any] = None) -> Resolution:
        """Resuelve una ambigüedad específica"""
        try:
            self.logger.info(f"Resolviendo ambigüedad: {ambiguity.ambiguity_id}")
            
            # Seleccionar estrategia de resolución
            strategy = self._select_resolution_strategy(ambiguity, context)
            
            # Aplicar estrategia
            resolution = self._apply_resolution_strategy(ambiguity, strategy, context)
            
            # Guardar resolución
            self._save_resolution_to_graph(resolution, ambiguity)
            
            return resolution
            
        except Exception as e:
            self.logger.error(f"Error resolviendo ambigüedad: {e}")
            return None
    
    def _select_resolution_strategy(self, ambiguity: Ambiguity, context: Dict[str, Any] = None) -> ResolutionStrategy:
        """Selecciona la mejor estrategia de resolución"""
        try:
            available_strategies = self.resolution_strategies.get(ambiguity.type, [])
            
            # Priorizar estrategias según el contexto
            if context and context.get('has_expert_available'):
                if ResolutionStrategy.CONSULT_EXPERT in available_strategies:
                    return ResolutionStrategy.CONSULT_EXPERT
            
            if context and context.get('has_additional_docs'):
                if ResolutionStrategy.REQUEST_DOCUMENTATION in available_strategies:
                    return ResolutionStrategy.REQUEST_DOCUMENTATION
            
            # Estrategia por defecto
            return available_strategies[0] if available_strategies else ResolutionStrategy.ASK_CLARIFICATION
            
        except Exception as e:
            self.logger.error(f"Error seleccionando estrategia: {e}")
            return ResolutionStrategy.ASK_CLARIFICATION
    
    def _apply_resolution_strategy(self, ambiguity: Ambiguity, strategy: ResolutionStrategy, 
                                 context: Dict[str, Any] = None) -> Resolution:
        """Aplica la estrategia de resolución seleccionada"""
        try:
            if strategy == ResolutionStrategy.ASK_CLARIFICATION:
                return self._resolve_by_clarification(ambiguity, context)
            elif strategy == ResolutionStrategy.USE_DEFAULT:
                return self._resolve_by_default(ambiguity, context)
            elif strategy == ResolutionStrategy.INFER_FROM_CONTEXT:
                return self._resolve_by_inference(ambiguity, context)
            elif strategy == ResolutionStrategy.REQUEST_DOCUMENTATION:
                return self._resolve_by_documentation(ambiguity, context)
            elif strategy == ResolutionStrategy.CONSULT_EXPERT:
                return self._resolve_by_expert(ambiguity, context)
            else:
                return self._resolve_by_clarification(ambiguity, context)
                
        except Exception as e:
            self.logger.error(f"Error aplicando estrategia: {e}")
            return None
    
    def _resolve_by_clarification(self, ambiguity: Ambiguity, context: Dict[str, Any] = None) -> Resolution:
        """Resuelve pidiendo aclaración"""
        try:
            resolution_text = f"Se requiere aclaración sobre: {ambiguity.description}"
            
            if ambiguity.type == AmbiguityType.CONTRADICTION:
                resolution_text += "\n\nPor favor, aclare cuál de las dos versiones es la correcta."
            elif ambiguity.type == AmbiguityType.INCOMPLETE_INFO:
                resolution_text += "\n\nPor favor, proporcione la información faltante."
            elif ambiguity.type == AmbiguityType.UNCLEAR_SPECIFICATION:
                resolution_text += "\n\nPor favor, proporcione una especificación más detallada."
            elif ambiguity.type == AmbiguityType.MISSING_DIMENSIONS:
                resolution_text += "\n\nPor favor, proporcione las dimensiones de los elementos mencionados."
            elif ambiguity.type == AmbiguityType.REGULATORY_CONFLICT:
                resolution_text += "\n\nPor favor, explique cómo se cumple con la normativa aplicable."
            elif ambiguity.type == AmbiguityType.TECHNICAL_UNCERTAINTY:
                resolution_text += "\n\nPor favor, defina la especificación técnica requerida."
            
            return Resolution(
                resolution_id=f"resolution_{ambiguity.ambiguity_id}",
                ambiguity_id=ambiguity.ambiguity_id,
                strategy_used=ResolutionStrategy.ASK_CLARIFICATION,
                resolution_text=resolution_text,
                confidence=0.8,
                supporting_evidence=[],
                resolved_at=datetime.now().isoformat(),
                verified=False
            )
            
        except Exception as e:
            self.logger.error(f"Error resolviendo por aclaración: {e}")
            return None
    
    def _resolve_by_default(self, ambiguity: Ambiguity, context: Dict[str, Any] = None) -> Resolution:
        """Resuelve usando valores por defecto"""
        try:
            default_values = {
                AmbiguityType.MISSING_DIMENSIONS: "Usar dimensiones estándar según normativa",
                AmbiguityType.UNCLEAR_SPECIFICATION: "Aplicar especificación estándar",
                AmbiguityType.TECHNICAL_UNCERTAINTY: "Usar especificación conservadora"
            }
            
            resolution_text = default_values.get(ambiguity.type, "Aplicar valor por defecto")
            
            return Resolution(
                resolution_id=f"resolution_{ambiguity.ambiguity_id}",
                ambiguity_id=ambiguity.ambiguity_id,
                strategy_used=ResolutionStrategy.USE_DEFAULT,
                resolution_text=resolution_text,
                confidence=0.6,
                supporting_evidence=["Valores estándar de la industria"],
                resolved_at=datetime.now().isoformat(),
                verified=False
            )
            
        except Exception as e:
            self.logger.error(f"Error resolviendo por defecto: {e}")
            return None
    
    def _resolve_by_inference(self, ambiguity: Ambiguity, context: Dict[str, Any] = None) -> Resolution:
        """Resuelve inferiendo del contexto"""
        try:
            # Usar IA para inferir resolución
            prompt = f"""
            Contexto del proyecto: {context or 'No disponible'}
            
            Ambigüedad detectada:
            - Tipo: {ambiguity.type.value}
            - Descripción: {ambiguity.description}
            - Contexto: {ambiguity.context}
            
            Proporciona una resolución inferida basada en el contexto y las mejores prácticas arquitectónicas.
            Resolución:
            """
            
            response = self.ai_client.generate_response(prompt)
            
            if response and response.success:
                resolution_text = response.content
                confidence = 0.7
            else:
                resolution_text = "No se pudo inferir resolución del contexto"
                confidence = 0.3
            
            return Resolution(
                resolution_id=f"resolution_{ambiguity.ambiguity_id}",
                ambiguity_id=ambiguity.ambiguity_id,
                strategy_used=ResolutionStrategy.INFER_FROM_CONTEXT,
                resolution_text=resolution_text,
                confidence=confidence,
                supporting_evidence=["Inferencia del contexto del proyecto"],
                resolved_at=datetime.now().isoformat(),
                verified=False
            )
            
        except Exception as e:
            self.logger.error(f"Error resolviendo por inferencia: {e}")
            return None
    
    def _resolve_by_documentation(self, ambiguity: Ambiguity, context: Dict[str, Any] = None) -> Resolution:
        """Resuelve solicitando documentación adicional"""
        try:
            resolution_text = f"Se requiere documentación adicional para resolver: {ambiguity.description}"
            
            if ambiguity.type == AmbiguityType.INCOMPLETE_INFO:
                resolution_text += "\n\nDocumentos requeridos:\n- Planos detallados\n- Especificaciones técnicas\n- Memoria descriptiva completa"
            elif ambiguity.type == AmbiguityType.MISSING_DIMENSIONS:
                resolution_text += "\n\nDocumentos requeridos:\n- Planos con cotas\n- Detalles constructivos\n- Especificaciones dimensionales"
            elif ambiguity.type == AmbiguityType.REGULATORY_CONFLICT:
                resolution_text += "\n\nDocumentos requeridos:\n- Justificación de cumplimiento\n- Cálculos de verificación\n- Certificados técnicos"
            
            return Resolution(
                resolution_id=f"resolution_{ambiguity.ambiguity_id}",
                ambiguity_id=ambiguity.ambiguity_id,
                strategy_used=ResolutionStrategy.REQUEST_DOCUMENTATION,
                resolution_text=resolution_text,
                confidence=0.8,
                supporting_evidence=["Solicitud de documentación adicional"],
                resolved_at=datetime.now().isoformat(),
                verified=False
            )
            
        except Exception as e:
            self.logger.error(f"Error resolviendo por documentación: {e}")
            return None
    
    def _resolve_by_expert(self, ambiguity: Ambiguity, context: Dict[str, Any] = None) -> Resolution:
        """Resuelve consultando con experto"""
        try:
            resolution_text = f"Se requiere consulta con experto para resolver: {ambiguity.description}"
            
            if ambiguity.type == AmbiguityType.REGULATORY_CONFLICT:
                resolution_text += "\n\nConsultar con:\n- Técnico especializado en normativa\n- Arquitecto supervisor\n- Ingeniero de la edificación"
            elif ambiguity.type == AmbiguityType.CONTRADICTION:
                resolution_text += "\n\nConsultar con:\n- Arquitecto del proyecto\n- Técnico responsable\n- Supervisor de obra"
            else:
                resolution_text += "\n\nConsultar con técnico especializado en la materia."
            
            return Resolution(
                resolution_id=f"resolution_{ambiguity.ambiguity_id}",
                ambiguity_id=ambiguity.ambiguity_id,
                strategy_used=ResolutionStrategy.CONSULT_EXPERT,
                resolution_text=resolution_text,
                confidence=0.9,
                supporting_evidence=["Consulta con experto requerida"],
                resolved_at=datetime.now().isoformat(),
                verified=False
            )
            
        except Exception as e:
            self.logger.error(f"Error resolviendo por experto: {e}")
            return None
    
    def _save_ambiguity_to_graph(self, ambiguity: Ambiguity, project_id: str):
        """Guarda una ambigüedad en el grafo de conocimiento"""
        try:
            ambiguity_data = {
                'id': ambiguity.ambiguity_id,
                'type': ambiguity.type.value,
                'description': ambiguity.description,
                'context': ambiguity.context,
                'severity': ambiguity.severity,
                'confidence': ambiguity.confidence,
                'status': ambiguity.status
            }
            
            # Crear nodo de problema en Neo4j
            self.neo4j_manager.create_issue_node(ambiguity_data, project_id)
            
        except Exception as e:
            self.logger.error(f"Error guardando ambigüedad en grafo: {e}")
    
    def _save_resolution_to_graph(self, resolution: Resolution, ambiguity: Ambiguity):
        """Guarda una resolución en el grafo de conocimiento"""
        try:
            # Actualizar estado de la ambigüedad
            ambiguity.status = 'resolved'
            
            # Guardar resolución como nodo de respuesta
            resolution_data = {
                'id': resolution.resolution_id,
                'text': resolution.resolution_text,
                'type': 'resolution',
                'context': f"Resolución de {ambiguity.ambiguity_id}",
                'priority': 'HIGH',
                'status': 'completed',
                'answer': resolution.resolution_text
            }
            
            # Crear nodo de pregunta/respuesta en Neo4j
            self.neo4j_manager.create_question_node(resolution_data, 'system')
            
        except Exception as e:
            self.logger.error(f"Error guardando resolución en grafo: {e}")
    
    def get_ambiguity_resolution_summary(self, project_id: str) -> Dict[str, Any]:
        """Obtiene un resumen de las ambigüedades y resoluciones del proyecto"""
        try:
            # Buscar ambigüedades en el grafo
            with self.neo4j_manager.get_session() as session:
                query = """
                MATCH (i:Issue)
                WHERE i.id STARTS WITH $project_prefix
                RETURN i
                ORDER BY i.severity DESC
                """
                
                result = session.run(query, {'project_prefix': f"project_{project_id}"})
                
                ambiguities = []
                for record in result:
                    ambiguity = dict(record["i"])
                    ambiguities.append(ambiguity)
                
                # Estadísticas
                total_ambiguities = len(ambiguities)
                high_severity = len([a for a in ambiguities if a.get('severity') == 'HIGH'])
                medium_severity = len([a for a in ambiguities if a.get('severity') == 'MEDIUM'])
                low_severity = len([a for a in ambiguities if a.get('severity') == 'LOW'])
                
                return {
                    'total_ambiguities': total_ambiguities,
                    'high_severity': high_severity,
                    'medium_severity': medium_severity,
                    'low_severity': low_severity,
                    'ambiguities': ambiguities,
                    'resolution_rate': 0.0  # TODO: Calcular tasa de resolución
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen de ambigüedades: {e}")
            return {}
