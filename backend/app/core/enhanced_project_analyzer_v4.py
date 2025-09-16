"""
Enhanced Project Analyzer V4 - Integración Completa
Fase 3: Sistema de Preguntas Inteligentes
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from .config import get_config
from .logging_config import get_logger
from .error_handling import handle_exception
from .file_manager import FileManager
from .enhanced_ocr_processor import EnhancedOCRProcessor
from .computer_vision_analyzer import ComputerVisionAnalyzer
from .plan_analyzer import PlanAnalyzer
from .dimension_extractor import DimensionExtractor
from .advanced_nlp_processor import AdvancedNLPProcessor
from .advanced_rule_engine import AdvancedRuleEngine
from .production_checker_logic import ProductionComplianceChecker
from .neo4j_manager import Neo4jManager
from .intelligent_question_engine import IntelligentQuestionEngine, QuestionContext
from .conversational_ai import ConversationalAI
from .ambiguity_resolver import AmbiguityResolver
from .report_generator import ReportGenerator, ReportType

logger = get_logger(__name__)

@dataclass
class ComprehensiveAnalysisResult:
    """Resultado del análisis integral completo"""
    project_id: str
    overall_score: float
    document_analysis: Dict[str, Any]
    plan_analysis: Dict[str, Any]
    dimension_analysis: Dict[str, Any]
    compliance_analysis: Dict[str, Any]
    nlp_analysis: Dict[str, Any]
    rule_analysis: Dict[str, Any]
    ambiguities: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    knowledge_graph: Dict[str, Any]
    conversation_summary: Dict[str, Any]
    report_path: str
    processing_time: float
    files_processed: int
    critical_issues: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]

class EnhancedProjectAnalyzerV4:
    """Analizador de proyectos arquitectónicos con todas las fases integradas"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Gestor de archivos
        self.file_manager = FileManager()
        
        # Procesadores de Fase 1 (NLP Avanzado)
        self.ocr_processor = EnhancedOCRProcessor()
        self.nlp_processor = AdvancedNLPProcessor()
        self.rule_engine = AdvancedRuleEngine()
        
        # Procesadores de Fase 2 (Visión por Computador)
        self.cv_analyzer = ComputerVisionAnalyzer()
        self.plan_analyzer = PlanAnalyzer()
        self.dimension_extractor = DimensionExtractor()
        
        # Procesadores de Fase 3 (Sistema de Preguntas Inteligentes)
        self.neo4j_manager = Neo4jManager()
        self.question_engine = IntelligentQuestionEngine()
        self.conversational_ai = ConversationalAI()
        self.ambiguity_resolver = AmbiguityResolver()
        self.report_generator = ReportGenerator()
        
        # Verificador de cumplimiento
        self.compliance_checker = ProductionComplianceChecker()
        
        # Inicializar componentes
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa todos los componentes del sistema"""
        try:
            self.logger.info("Inicializando Enhanced Project Analyzer V4...")
            
            # Inicializar reglas de cumplimiento (ya se cargan en __init__)
            # self.rule_engine.load_compliance_rules()  # Comentado: ya se cargan en __init__
            
            # Inicializar modelos de IA
            self.nlp_processor.initialize_models()
            
            # Inicializar gestor de Neo4j
            self.neo4j_manager.initialize_connection()
            
            self.logger.info("Enhanced Project Analyzer V4 inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando componentes: {e}")
            raise
    
    @handle_exception
    def analyze_project_comprehensive(self, memory_file: str, plans_directory: str, 
                                    project_type: str = "residential") -> ComprehensiveAnalysisResult:
        """Realiza análisis integral completo del proyecto"""
        try:
            start_time = datetime.now()
            self.logger.info(f"Iniciando análisis integral para proyecto tipo: {project_type}")
            
            # Crear ID único del proyecto
            project_id = f"project_{int(datetime.now().timestamp())}"
            
            # 1. FASE 1: Procesamiento Avanzado de Documentos
            self.logger.info("=== FASE 1: Procesamiento Avanzado de Documentos ===")
            document_analysis = self._analyze_documents_advanced(memory_file, project_id)
            
            # 2. FASE 2: Visión por Computador para Planos
            self.logger.info("=== FASE 2: Visión por Computador para Planos ===")
            plan_analysis = self._analyze_plans_computer_vision(plans_directory, project_id)
            
            # 3. Análisis de Dimensiones
            self.logger.info("=== Análisis de Dimensiones ===")
            dimension_analysis = self._analyze_dimensions(plans_directory, project_id)
            
            # 4. Verificación de Cumplimiento
            self.logger.info("=== Verificación de Cumplimiento ===")
            compliance_analysis = self._analyze_compliance(
                document_analysis, plan_analysis, dimension_analysis, project_type
            )
            
            # 5. FASE 3: Sistema de Preguntas Inteligentes
            self.logger.info("=== FASE 3: Sistema de Preguntas Inteligentes ===")
            
            # Detectar ambigüedades
            ambiguities = self._detect_and_resolve_ambiguities(
                project_id, document_analysis, plan_analysis, dimension_analysis
            )
            
            # Generar preguntas inteligentes
            questions = self._generate_intelligent_questions(
                project_id, document_analysis, plan_analysis, dimension_analysis, ambiguities
            )
            
            # Crear grafo de conocimiento
            knowledge_graph = self._build_knowledge_graph(
                project_id, document_analysis, plan_analysis, dimension_analysis, 
                compliance_analysis, ambiguities, questions
            )
            
            # 6. Análisis NLP Avanzado
            self.logger.info("=== Análisis NLP Avanzado ===")
            nlp_analysis = self._perform_advanced_nlp_analysis(document_analysis, project_id)
            
            # 7. Análisis con Motor de Reglas
            self.logger.info("=== Análisis con Motor de Reglas ===")
            rule_analysis = self._perform_rule_analysis(
                document_analysis, plan_analysis, dimension_analysis, compliance_analysis
            )
            
            # 8. Generar reporte integral
            self.logger.info("=== Generación de Reporte Integral ===")
            report_path = self._generate_comprehensive_report(
                project_id, document_analysis, plan_analysis, dimension_analysis,
                compliance_analysis, nlp_analysis, rule_analysis, ambiguities, questions
            )
            
            # 9. Calcular puntuación general
            overall_score = self._calculate_overall_score(
                document_analysis, plan_analysis, dimension_analysis, 
                compliance_analysis, nlp_analysis, rule_analysis
            )
            
            # 10. Identificar problemas críticos y recomendaciones
            critical_issues = self._identify_critical_issues(
                compliance_analysis, ambiguities, plan_analysis
            )
            
            recommendations = self._generate_recommendations(
                overall_score, critical_issues, compliance_analysis, ambiguities
            )
            
            # Calcular tiempo de procesamiento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Contar archivos procesados
            files_processed = self._count_processed_files(memory_file, plans_directory)
            
            # Crear resultado integral
            result = ComprehensiveAnalysisResult(
                project_id=project_id,
                overall_score=overall_score,
                document_analysis=document_analysis,
                plan_analysis=plan_analysis,
                dimension_analysis=dimension_analysis,
                compliance_analysis=compliance_analysis,
                nlp_analysis=nlp_analysis,
                rule_analysis=rule_analysis,
                ambiguities=ambiguities,
                questions=questions,
                knowledge_graph=knowledge_graph,
                conversation_summary={},
                report_path=report_path,
                processing_time=processing_time,
                files_processed=files_processed,
                critical_issues=critical_issues,
                recommendations=recommendations,
                metadata={
                    'project_type': project_type,
                    'analysis_version': '4.0',
                    'phases_completed': ['phase1', 'phase2', 'phase3'],
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            self.logger.info(f"Análisis integral completado en {processing_time:.2f} segundos")
            self.logger.info(f"Puntuación general: {overall_score:.2f}/10")
            self.logger.info(f"Archivos procesados: {files_processed}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error en análisis integral: {e}")
            raise
    
    def _analyze_documents_advanced(self, memory_file: str, project_id: str) -> Dict[str, Any]:
        """Análisis avanzado de documentos (Fase 1)"""
        try:
            self.logger.info("Procesando documentos con OCR avanzado...")
            
            # Procesar documento con OCR
            ocr_result = self.ocr_processor.process_document(memory_file)
            
            # Análisis NLP avanzado
            nlp_result = self.nlp_processor.analyze_text_advanced(ocr_result.get('extracted_text', ''))
            
            # Detectar contradicciones
            contradictions = self.nlp_processor.detect_contradictions(nlp_result)
            
            # Extraer entidades
            entities = self.nlp_processor.extract_entities(ocr_result.get('extracted_text', ''))
            
            # Análisis de sentimientos
            sentiment = self.nlp_processor.analyze_sentiment(ocr_result.get('extracted_text', ''))
            
            # Crear nodo de documento en Neo4j
            document_data = {
                'id': f"doc_{project_id}",
                'name': os.path.basename(memory_file),
                'type': 'memory',
                'file_path': memory_file,
                'pages': ocr_result.get('pages', 0),
                'size': os.path.getsize(memory_file) if os.path.exists(memory_file) else 0,
                'extracted_text': ocr_result.get('extracted_text', '')
            }
            
            self.neo4j_manager.create_document_node(document_data, project_id)
            
            return {
                'confidence_score': ocr_result.get('confidence', 0.0),
                'extracted_text': ocr_result.get('extracted_text', ''),
                'extracted_data': nlp_result.get('extracted_data', {}),
                'contradictions': contradictions,
                'entities': entities,
                'sentiment': sentiment,
                'nlp_confidence': nlp_result.get('confidence', 0.0),
                'processing_time': ocr_result.get('processing_time', 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis avanzado de documentos: {e}")
            return {}
    
    def _analyze_plans_computer_vision(self, plans_directory: str, project_id: str) -> Dict[str, Any]:
        """Análisis de planos con visión por computador (Fase 2)"""
        try:
            self.logger.info("Analizando planos con visión por computador...")
            
            if not os.path.exists(plans_directory):
                self.logger.warning(f"Directorio de planos no encontrado: {plans_directory}")
                return {}
            
            # Obtener archivos de planos
            plan_files = [f for f in os.listdir(plans_directory) if f.lower().endswith('.pdf')]
            
            if not plan_files:
                self.logger.warning("No se encontraron archivos PDF en el directorio de planos")
                return {}
            
            all_elements = []
            all_rooms = []
            accessibility_issues = []
            fire_safety_issues = []
            structural_issues = []
            
            for plan_file in plan_files:
                plan_path = os.path.join(plans_directory, plan_file)
                
                try:
                    # Análisis con visión por computador
                    cv_result = self.cv_analyzer.analyze_plan(plan_path)
                    
                    # Análisis específico de planos
                    plan_result = self.plan_analyzer.analyze_plan(plan_path)
                    
                    # Combinar resultados
                    elements = cv_result.get('elements', []) + plan_result.get('elements', [])
                    all_elements.extend(elements)
                    
                    rooms = plan_result.get('rooms', [])
                    all_rooms.extend(rooms)
                    
                    # Recopilar problemas
                    accessibility_issues.extend(plan_result.get('accessibility_issues', []))
                    fire_safety_issues.extend(plan_result.get('fire_safety_issues', []))
                    structural_issues.extend(plan_result.get('structural_issues', []))
                    
                    # Crear nodo de plano en Neo4j
                    plan_data = {
                        'id': f"plan_{os.path.splitext(plan_file)[0]}",
                        'name': plan_file,
                        'type': 'architectural_plan',
                        'elements_count': len(elements),
                        'compliance_score': plan_result.get('compliance_score', 0.0)
                    }
                    
                    self.neo4j_manager.create_plan_node(plan_data, project_id)
                    
                    # Crear nodos de elementos
                    for element in elements:
                        element_data = {
                            'id': element.get('id', f"elem_{len(all_elements)}"),
                            'type': element.get('type', 'unknown'),
                            'name': element.get('name', ''),
                            'dimensions': element.get('dimensions', {}),
                            'coordinates': element.get('coordinates', []),
                            'properties': element.get('properties', {}),
                            'confidence': element.get('confidence', 0.0)
                        }
                        
                        self.neo4j_manager.create_element_node(element_data, plan_data['id'])
                    
                except Exception as e:
                    self.logger.error(f"Error procesando plano {plan_file}: {e}")
                    continue
            
            # Calcular puntuación de cumplimiento general
            overall_compliance = self._calculate_plan_compliance(
                all_elements, accessibility_issues, fire_safety_issues, structural_issues
            )
            
            return {
                'elements': all_elements,
                'rooms': all_rooms,
                'accessibility_issues': accessibility_issues,
                'fire_safety_issues': fire_safety_issues,
                'structural_issues': structural_issues,
                'overall_compliance': overall_compliance,
                'plans_processed': len(plan_files),
                'total_elements': len(all_elements)
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de planos: {e}")
            return {}
    
    def _analyze_dimensions(self, plans_directory: str, project_id: str) -> Dict[str, Any]:
        """Análisis de dimensiones"""
        try:
            self.logger.info("Analizando dimensiones...")
            
            if not os.path.exists(plans_directory):
                return {}
            
            plan_files = [f for f in os.listdir(plans_directory) if f.lower().endswith('.pdf')]
            
            all_dimensions = []
            room_areas = {}
            wall_lengths = []
            door_widths = []
            
            for plan_file in plan_files:
                plan_path = os.path.join(plans_directory, plan_file)
                
                try:
                    # Extraer dimensiones
                    dimensions = self.dimension_extractor.extract_dimensions(plan_path)
                    all_dimensions.extend(dimensions)
                    
                    # Procesar dimensiones específicas
                    for dim in dimensions:
                        if dim.get('type') == 'room_area':
                            room_name = dim.get('room_name', 'unknown')
                            area = dim.get('value', 0)
                            room_areas[room_name] = area
                        elif dim.get('type') == 'wall_length':
                            wall_lengths.append(dim.get('value', 0))
                        elif dim.get('type') == 'door_width':
                            door_widths.append(dim.get('value', 0))
                    
                except Exception as e:
                    self.logger.error(f"Error extrayendo dimensiones de {plan_file}: {e}")
                    continue
            
            # Calcular área total
            total_area = sum(room_areas.values())
            
            return {
                'total_area': total_area,
                'room_areas': room_areas,
                'wall_lengths': wall_lengths,
                'door_widths': door_widths,
                'total_dimensions': len(all_dimensions),
                'rooms_count': len(room_areas)
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de dimensiones: {e}")
            return {}
    
    def _analyze_compliance(self, document_analysis: Dict[str, Any], 
                          plan_analysis: Dict[str, Any], 
                          dimension_analysis: Dict[str, Any], 
                          project_type: str) -> Dict[str, Any]:
        """Análisis de cumplimiento normativo"""
        try:
            self.logger.info("Verificando cumplimiento normativo...")
            
            # Verificar cumplimiento de dimensiones
            dimension_compliance = self._check_dimension_compliance(dimension_analysis)
            
            # Verificar cumplimiento de accesibilidad
            accessibility_compliance = self._check_accessibility_compliance(plan_analysis)
            
            # Verificar cumplimiento de seguridad contra incendios
            fire_safety_compliance = self._check_fire_safety_compliance(plan_analysis)
            
            # Verificar cumplimiento estructural
            structural_compliance = self._check_structural_compliance(plan_analysis)
            
            # Verificar cumplimiento general
            overall_compliance = (
                dimension_compliance + accessibility_compliance + 
                fire_safety_compliance + structural_compliance
            ) / 4
            
            return {
                'dimension_compliance': dimension_compliance,
                'accessibility_compliance': accessibility_compliance,
                'fire_safety_compliance': fire_safety_compliance,
                'structural_compliance': structural_compliance,
                'overall_compliance': overall_compliance,
                'project_type': project_type
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis de cumplimiento: {e}")
            return {}
    
    def _detect_and_resolve_ambiguities(self, project_id: str, document_analysis: Dict[str, Any],
                                      plan_analysis: Dict[str, Any], 
                                      dimension_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta y resuelve ambigüedades (Fase 3)"""
        try:
            self.logger.info("Detectando y resolviendo ambigüedades...")
            
            # Crear datos del proyecto para el resolutor
            project_data = {
                'id': project_id,
                'compliance_issues': []  # Se llenará con problemas de cumplimiento
            }
            
            # Detectar ambigüedades
            ambiguities = self.ambiguity_resolver.detect_ambiguities(
                project_data, document_analysis, plan_analysis
            )
            
            # Resolver ambigüedades automáticamente
            resolved_ambiguities = []
            for ambiguity in ambiguities:
                try:
                    resolution = self.ambiguity_resolver.resolve_ambiguity(ambiguity)
                    if resolution:
                        resolved_ambiguities.append({
                            'ambiguity': ambiguity.__dict__,
                            'resolution': resolution.__dict__
                        })
                except Exception as e:
                    self.logger.error(f"Error resolviendo ambigüedad {ambiguity.ambiguity_id}: {e}")
                    resolved_ambiguities.append({
                        'ambiguity': ambiguity.__dict__,
                        'resolution': None
                    })
            
            return resolved_ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando ambigüedades: {e}")
            return []
    
    def _generate_intelligent_questions(self, project_id: str, document_analysis: Dict[str, Any],
                                      plan_analysis: Dict[str, Any], 
                                      dimension_analysis: Dict[str, Any],
                                      ambiguities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Genera preguntas inteligentes (Fase 3)"""
        try:
            self.logger.info("Generando preguntas inteligentes...")
            
            # Crear contexto para el motor de preguntas
            context = QuestionContext(
                project_data={'id': project_id},
                document_analysis=document_analysis,
                plan_analysis=plan_analysis,
                dimension_analysis=dimension_analysis,
                compliance_issues=[],
                previous_questions=[]
            )
            
            # Generar preguntas inteligentes
            questions = self.question_engine.generate_intelligent_questions(context)
            
            # Convertir a diccionarios para serialización
            questions_dict = []
            for question in questions:
                questions_dict.append(question.__dict__)
            
            return questions_dict
            
        except Exception as e:
            self.logger.error(f"Error generando preguntas inteligentes: {e}")
            return []
    
    def _build_knowledge_graph(self, project_id: str, document_analysis: Dict[str, Any],
                             plan_analysis: Dict[str, Any], dimension_analysis: Dict[str, Any],
                             compliance_analysis: Dict[str, Any], ambiguities: List[Dict[str, Any]],
                             questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Construye el grafo de conocimiento (Fase 3)"""
        try:
            self.logger.info("Construyendo grafo de conocimiento...")
            
            # Obtener grafo de conocimiento del proyecto
            knowledge_graph = self.neo4j_manager.get_project_knowledge_graph(project_id)
            
            return {
                'total_nodes': knowledge_graph.metadata.get('total_nodes', 0),
                'total_relationships': knowledge_graph.metadata.get('total_relationships', 0),
                'node_types': self._get_node_types(knowledge_graph.nodes),
                'relationship_types': self._get_relationship_types(knowledge_graph.relationships)
            }
            
        except Exception as e:
            self.logger.error(f"Error construyendo grafo de conocimiento: {e}")
            return {}
    
    def _perform_advanced_nlp_analysis(self, document_analysis: Dict[str, Any], 
                                     project_id: str) -> Dict[str, Any]:
        """Realiza análisis NLP avanzado"""
        try:
            self.logger.info("Realizando análisis NLP avanzado...")
            
            extracted_text = document_analysis.get('extracted_text', '')
            
            # Análisis de coherencia
            coherence = self.nlp_processor.analyze_coherence(extracted_text)
            
            # Análisis de complejidad
            complexity = self.nlp_processor.analyze_complexity(extracted_text)
            
            # Análisis de legibilidad
            readability = self.nlp_processor.analyze_readability(extracted_text)
            
            return {
                'coherence_score': coherence.get('score', 0.0),
                'complexity_score': complexity.get('score', 0.0),
                'readability_score': readability.get('score', 0.0),
                'analysis_confidence': (coherence.get('confidence', 0.0) + 
                                     complexity.get('confidence', 0.0) + 
                                     readability.get('confidence', 0.0)) / 3
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis NLP avanzado: {e}")
            return {}
    
    def _perform_rule_analysis(self, document_analysis: Dict[str, Any], 
                             plan_analysis: Dict[str, Any], 
                             dimension_analysis: Dict[str, Any],
                             compliance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza análisis con motor de reglas"""
        try:
            self.logger.info("Realizando análisis con motor de reglas...")
            
            # Crear contexto para el motor de reglas
            context = {
                'document_data': document_analysis.get('extracted_data', {}),
                'plan_data': plan_analysis,
                'dimension_data': dimension_analysis,
                'compliance_data': compliance_analysis
            }
            
            # Ejecutar reglas de cumplimiento
            rule_results = self.rule_engine.evaluate_rules(context)
            
            return {
                'rules_evaluated': rule_results.get('total_rules', 0),
                'rules_passed': rule_results.get('passed_rules', 0),
                'rules_failed': rule_results.get('failed_rules', 0),
                'compliance_score': rule_results.get('compliance_score', 0.0),
                'violations': rule_results.get('violations', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error en análisis con motor de reglas: {e}")
            return {}
    
    def _generate_comprehensive_report(self, project_id: str, document_analysis: Dict[str, Any],
                                     plan_analysis: Dict[str, Any], dimension_analysis: Dict[str, Any],
                                     compliance_analysis: Dict[str, Any], nlp_analysis: Dict[str, Any],
                                     rule_analysis: Dict[str, Any], ambiguities: List[Dict[str, Any]],
                                     questions: List[Dict[str, Any]]) -> str:
        """Genera reporte integral"""
        try:
            self.logger.info("Generando reporte integral...")
            
            # Crear datos del proyecto
            project_data = {
                'id': project_id,
                'name': f"Proyecto {project_id}",
                'type': 'residential'
            }
            
            # Crear resultados de análisis
            analysis_results = {
                'document_analysis': document_analysis,
                'plan_analysis': plan_analysis,
                'dimension_analysis': dimension_analysis,
                'compliance_check': compliance_analysis,
                'nlp_analysis': nlp_analysis,
                'rule_analysis': rule_analysis,
                'ambiguities': ambiguities,
                'questions': questions
            }
            
            # Generar reporte
            report = self.report_generator.generate_comprehensive_report(
                project_data, analysis_results
            )
            
            return report.file_path if report else ""
            
        except Exception as e:
            self.logger.error(f"Error generando reporte integral: {e}")
            return ""
    
    def _calculate_overall_score(self, document_analysis: Dict[str, Any], 
                               plan_analysis: Dict[str, Any], 
                               dimension_analysis: Dict[str, Any],
                               compliance_analysis: Dict[str, Any], 
                               nlp_analysis: Dict[str, Any],
                               rule_analysis: Dict[str, Any]) -> float:
        """Calcula la puntuación general del proyecto"""
        try:
            # Ponderaciones para cada componente
            weights = {
                'document_confidence': 0.15,
                'plan_compliance': 0.25,
                'dimension_compliance': 0.20,
                'compliance_overall': 0.25,
                'nlp_analysis': 0.10,
                'rule_analysis': 0.05
            }
            
            # Calcular puntuaciones individuales
            doc_score = document_analysis.get('confidence_score', 0.0) * 10
            plan_score = plan_analysis.get('overall_compliance', 0.0) * 10
            dim_score = dimension_analysis.get('compliance_score', 0.0) * 10
            comp_score = compliance_analysis.get('overall_compliance', 0.0) * 10
            nlp_score = nlp_analysis.get('analysis_confidence', 0.0) * 10
            rule_score = rule_analysis.get('compliance_score', 0.0) * 10
            
            # Calcular puntuación ponderada
            overall_score = (
                doc_score * weights['document_confidence'] +
                plan_score * weights['plan_compliance'] +
                dim_score * weights['dimension_compliance'] +
                comp_score * weights['compliance_overall'] +
                nlp_score * weights['nlp_analysis'] +
                rule_score * weights['rule_analysis']
            )
            
            return min(10.0, max(0.0, overall_score))
            
        except Exception as e:
            self.logger.error(f"Error calculando puntuación general: {e}")
            return 0.0
    
    def _identify_critical_issues(self, compliance_analysis: Dict[str, Any],
                                ambiguities: List[Dict[str, Any]], 
                                plan_analysis: Dict[str, Any]) -> List[str]:
        """Identifica problemas críticos"""
        try:
            critical_issues = []
            
            # Problemas de cumplimiento críticos
            if compliance_analysis.get('overall_compliance', 0) < 0.6:
                critical_issues.append("Cumplimiento normativo insuficiente")
            
            if compliance_analysis.get('accessibility_compliance', 0) < 0.5:
                critical_issues.append("Problemas críticos de accesibilidad")
            
            if compliance_analysis.get('fire_safety_compliance', 0) < 0.5:
                critical_issues.append("Problemas críticos de seguridad contra incendios")
            
            # Ambigüedades de alta severidad
            for ambiguity in ambiguities:
                if ambiguity.get('ambiguity', {}).get('severity') == 'HIGH':
                    critical_issues.append(f"Ambigüedad crítica: {ambiguity.get('ambiguity', {}).get('description', '')}")
            
            # Problemas de planos
            if len(plan_analysis.get('accessibility_issues', [])) > 5:
                critical_issues.append("Múltiples problemas de accesibilidad en planos")
            
            if len(plan_analysis.get('fire_safety_issues', [])) > 3:
                critical_issues.append("Múltiples problemas de seguridad contra incendios")
            
            return critical_issues
            
        except Exception as e:
            self.logger.error(f"Error identificando problemas críticos: {e}")
            return []
    
    def _generate_recommendations(self, overall_score: float, critical_issues: List[str],
                                compliance_analysis: Dict[str, Any], 
                                ambiguities: List[Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones"""
        try:
            recommendations = []
            
            # Recomendaciones basadas en puntuación general
            if overall_score < 5.0:
                recommendations.append("Revisión completa del proyecto requerida")
            elif overall_score < 7.0:
                recommendations.append("Mejoras significativas recomendadas")
            else:
                recommendations.append("Proyecto en buen estado, optimizaciones menores")
            
            # Recomendaciones específicas por área
            if compliance_analysis.get('accessibility_compliance', 0) < 0.7:
                recommendations.append("Mejorar accesibilidad universal del proyecto")
            
            if compliance_analysis.get('fire_safety_compliance', 0) < 0.7:
                recommendations.append("Reforzar medidas de seguridad contra incendios")
            
            # Recomendaciones para ambigüedades
            if len(ambiguities) > 10:
                recommendations.append("Resolver ambigüedades pendientes antes de continuar")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generando recomendaciones: {e}")
            return []
    
    def _calculate_plan_compliance(self, elements: List[Dict[str, Any]], 
                                 accessibility_issues: List[str],
                                 fire_safety_issues: List[str], 
                                 structural_issues: List[str]) -> float:
        """Calcula cumplimiento de planos"""
        try:
            total_issues = len(accessibility_issues) + len(fire_safety_issues) + len(structural_issues)
            total_elements = len(elements)
            
            if total_elements == 0:
                return 0.0
            
            # Calcular puntuación basada en problemas vs elementos
            issue_ratio = total_issues / total_elements
            compliance = max(0.0, 1.0 - issue_ratio)
            
            return compliance
            
        except Exception as e:
            self.logger.error(f"Error calculando cumplimiento de planos: {e}")
            return 0.0
    
    def _check_dimension_compliance(self, dimension_analysis: Dict[str, Any]) -> float:
        """Verifica cumplimiento de dimensiones"""
        try:
            room_areas = dimension_analysis.get('room_areas', {})
            door_widths = dimension_analysis.get('door_widths', [])
            
            compliance_score = 0.0
            total_checks = 0
            
            # Verificar áreas mínimas de habitaciones
            for room_name, area in room_areas.items():
                total_checks += 1
                if area >= 9.0:  # Área mínima de habitaciones
                    compliance_score += 1.0
            
            # Verificar anchos mínimos de puertas
            for width in door_widths:
                total_checks += 1
                if width >= 0.8:  # Ancho mínimo de puertas
                    compliance_score += 1.0
            
            return compliance_score / total_checks if total_checks > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error verificando cumplimiento de dimensiones: {e}")
            return 0.0
    
    def _check_accessibility_compliance(self, plan_analysis: Dict[str, Any]) -> float:
        """Verifica cumplimiento de accesibilidad"""
        try:
            accessibility_issues = plan_analysis.get('accessibility_issues', [])
            
            # Puntuación base
            base_score = 1.0
            
            # Penalizar por problemas de accesibilidad
            penalty = len(accessibility_issues) * 0.1
            
            return max(0.0, base_score - penalty)
            
        except Exception as e:
            self.logger.error(f"Error verificando cumplimiento de accesibilidad: {e}")
            return 0.0
    
    def _check_fire_safety_compliance(self, plan_analysis: Dict[str, Any]) -> float:
        """Verifica cumplimiento de seguridad contra incendios"""
        try:
            fire_safety_issues = plan_analysis.get('fire_safety_issues', [])
            
            # Puntuación base
            base_score = 1.0
            
            # Penalizar por problemas de seguridad contra incendios
            penalty = len(fire_safety_issues) * 0.15
            
            return max(0.0, base_score - penalty)
            
        except Exception as e:
            self.logger.error(f"Error verificando cumplimiento de seguridad contra incendios: {e}")
            return 0.0
    
    def _check_structural_compliance(self, plan_analysis: Dict[str, Any]) -> float:
        """Verifica cumplimiento estructural"""
        try:
            structural_issues = plan_analysis.get('structural_issues', [])
            
            # Puntuación base
            base_score = 1.0
            
            # Penalizar por problemas estructurales
            penalty = len(structural_issues) * 0.2
            
            return max(0.0, base_score - penalty)
            
        except Exception as e:
            self.logger.error(f"Error verificando cumplimiento estructural: {e}")
            return 0.0
    
    def _count_processed_files(self, memory_file: str, plans_directory: str) -> int:
        """Cuenta archivos procesados"""
        try:
            count = 0
            
            # Contar archivo de memoria
            if os.path.exists(memory_file):
                count += 1
            
            # Contar archivos de planos
            if os.path.exists(plans_directory):
                plan_files = [f for f in os.listdir(plans_directory) if f.lower().endswith('.pdf')]
                count += len(plan_files)
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error contando archivos procesados: {e}")
            return 0
    
    def _get_node_types(self, nodes: List) -> Dict[str, int]:
        """Obtiene tipos de nodos en el grafo"""
        try:
            node_types = {}
            for node in nodes:
                node_type = node.node_type
                node_types[node_type] = node_types.get(node_type, 0) + 1
            return node_types
        except Exception as e:
            self.logger.error(f"Error obteniendo tipos de nodos: {e}")
            return {}
    
    def _get_relationship_types(self, relationships: List) -> Dict[str, int]:
        """Obtiene tipos de relaciones en el grafo"""
        try:
            rel_types = {}
            for rel in relationships:
                rel_type = rel.relationship_type
                rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
            return rel_types
        except Exception as e:
            self.logger.error(f"Error obteniendo tipos de relaciones: {e}")
            return {}
    
    def start_conversation(self, project_id: str, user_id: str = "user") -> str:
        """Inicia una conversación para el proyecto"""
        try:
            session = self.conversational_ai.start_conversation(user_id, project_id)
            return session.session_id if session else None
        except Exception as e:
            self.logger.error(f"Error iniciando conversación: {e}")
            return None
    
    def process_conversation_message(self, session_id: str, message: str) -> str:
        """Procesa un mensaje en la conversación"""
        try:
            return self.conversational_ai.process_message(session_id, message)
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")
            return "Lo siento, ha ocurrido un error. Por favor, intenta de nuevo."
    
    def close(self):
        """Cierra el analizador y libera recursos"""
        try:
            if hasattr(self, 'neo4j_manager'):
                self.neo4j_manager.close()
            self.logger.info("Enhanced Project Analyzer V4 cerrado correctamente")
        except Exception as e:
            self.logger.error(f"Error cerrando analizador: {e}")
