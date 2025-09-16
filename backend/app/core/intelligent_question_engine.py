"""
Motor de Preguntas Inteligentes
Fase 3: Sistema de Preguntas Inteligentes
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import textstat

from .config import get_config
from .logging_config import get_logger
from .ai_client import get_ai_client, AIResponse
from .neo4j_manager import Neo4jManager

logger = get_logger(__name__)

@dataclass
class IntelligentQuestion:
    """Pregunta inteligente generada por el sistema"""
    question_id: str
    text: str
    question_type: str  # 'clarification', 'compliance', 'technical', 'design', 'regulation'
    context: str
    priority: str  # 'HIGH', 'MEDIUM', 'LOW'
    confidence: float
    related_elements: List[str]
    related_regulations: List[str]
    suggested_answers: List[str]
    generated_at: str
    status: str  # 'pending', 'answered', 'resolved'

@dataclass
class QuestionContext:
    """Contexto para la generación de preguntas"""
    project_data: Dict[str, Any]
    document_analysis: Dict[str, Any]
    plan_analysis: Dict[str, Any]
    dimension_analysis: Dict[str, Any]
    compliance_issues: List[Dict[str, Any]]
    previous_questions: List[IntelligentQuestion]

class IntelligentQuestionEngine:
    """Motor de preguntas inteligentes con IA"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Cliente de IA
        self.ai_client = get_ai_client()
        
        # Gestor de Neo4j
        self.neo4j_manager = Neo4jManager()
        
        # Modelo de embeddings para similitud semántica
        self.embedding_model = None
        self.embedding_index = None
        
        # Inicializar componentes
        self.initialize_components()
    
    def initialize_components(self):
        """Inicializa los componentes del motor de preguntas"""
        try:
            # Cargar modelo de embeddings
            self.logger.info("Cargando modelo de embeddings para preguntas inteligentes...")
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Inicializar índice FAISS
            self.embedding_index = faiss.IndexFlatIP(384)  # Dimensión del modelo
            
            self.logger.info("Motor de preguntas inteligentes inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando motor de preguntas: {e}")
            raise
    
    def generate_intelligent_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Genera preguntas inteligentes basadas en el contexto del proyecto"""
        try:
            self.logger.info("Generando preguntas inteligentes...")
            
            questions = []
            
            # 1. Preguntas de clarificación
            clarification_questions = self._generate_clarification_questions(context)
            questions.extend(clarification_questions)
            
            # 2. Preguntas de cumplimiento
            compliance_questions = self._generate_compliance_questions(context)
            questions.extend(compliance_questions)
            
            # 3. Preguntas técnicas
            technical_questions = self._generate_technical_questions(context)
            questions.extend(technical_questions)
            
            # 4. Preguntas de diseño
            design_questions = self._generate_design_questions(context)
            questions.extend(design_questions)
            
            # 5. Preguntas de normativa
            regulation_questions = self._generate_regulation_questions(context)
            questions.extend(regulation_questions)
            
            # Filtrar y priorizar preguntas
            filtered_questions = self._filter_and_prioritize_questions(questions, context)
            
            # Guardar preguntas en Neo4j
            for question in filtered_questions:
                self._save_question_to_graph(question, context.project_data.get('id', 'unknown'))
            
            self.logger.info(f"Generadas {len(filtered_questions)} preguntas inteligentes")
            return filtered_questions
            
        except Exception as e:
            self.logger.error(f"Error generando preguntas inteligentes: {e}")
            return []
    
    def _generate_clarification_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Genera preguntas de clarificación"""
        try:
            questions = []
            
            # Detectar ambigüedades en documentos
            ambiguities = self._detect_document_ambiguities(context.document_analysis)
            
            for ambiguity in ambiguities:
                question = IntelligentQuestion(
                    question_id=f"clarification_{len(questions) + 1}",
                    text=f"¿Podría aclarar {ambiguity['text']}?",
                    question_type="clarification",
                    context=ambiguity['context'],
                    priority="HIGH" if ambiguity['severity'] == 'high' else "MEDIUM",
                    confidence=ambiguity['confidence'],
                    related_elements=ambiguity.get('related_elements', []),
                    related_regulations=ambiguity.get('related_regulations', []),
                    suggested_answers=ambiguity.get('suggested_answers', []),
                    generated_at=datetime.now().isoformat(),
                    status="pending"
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generando preguntas de clarificación: {e}")
            return []
    
    def _generate_compliance_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Genera preguntas de cumplimiento"""
        try:
            questions = []
            
            # Analizar problemas de cumplimiento
            for issue in context.compliance_issues:
                if issue.get('severity') in ['HIGH', 'CRITICAL']:
                    question = IntelligentQuestion(
                        question_id=f"compliance_{len(questions) + 1}",
                        text=f"¿Cómo planea resolver el problema de cumplimiento: {issue.get('title', '')}?",
                        question_type="compliance",
                        context=f"Problema: {issue.get('description', '')}",
                        priority="HIGH",
                        confidence=0.9,
                        related_elements=issue.get('related_elements', []),
                        related_regulations=issue.get('related_regulations', []),
                        suggested_answers=self._generate_compliance_suggestions(issue),
                        generated_at=datetime.now().isoformat(),
                        status="pending"
                    )
                    questions.append(question)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generando preguntas de cumplimiento: {e}")
            return []
    
    def _generate_technical_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Genera preguntas técnicas"""
        try:
            questions = []
            
            # Analizar elementos arquitectónicos
            if context.plan_analysis.get('elements'):
                for element in context.plan_analysis['elements']:
                    if element.get('confidence', 0) < 0.7:  # Elementos con baja confianza
                        question = IntelligentQuestion(
                            question_id=f"technical_{len(questions) + 1}",
                            text=f"¿Podría confirmar las dimensiones y características del {element.get('type', 'elemento')}?",
                            question_type="technical",
                            context=f"Elemento detectado: {element.get('type', 'unknown')} con confianza {element.get('confidence', 0):.2f}",
                            priority="MEDIUM",
                            confidence=element.get('confidence', 0),
                            related_elements=[element.get('id', '')],
                            related_regulations=[],
                            suggested_answers=self._generate_technical_suggestions(element),
                            generated_at=datetime.now().isoformat(),
                            status="pending"
                        )
                        questions.append(question)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generando preguntas técnicas: {e}")
            return []
    
    def _generate_design_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Genera preguntas de diseño"""
        try:
            questions = []
            
            # Analizar dimensiones y espacios
            if context.dimension_analysis.get('room_areas'):
                for room_name, area in context.dimension_analysis['room_areas'].items():
                    if area < 9.0:  # Área mínima de habitaciones
                        question = IntelligentQuestion(
                            question_id=f"design_{len(questions) + 1}",
                            text=f"¿La habitación {room_name} cumple con el área mínima requerida de 9m²?",
                            question_type="design",
                            context=f"Área actual: {area:.2f}m², Área mínima requerida: 9.0m²",
                            priority="HIGH",
                            confidence=0.95,
                            related_elements=[room_name],
                            related_regulations=["CTE DB-SU"],
                            suggested_answers=["Ampliar la habitación", "Reorganizar el espacio", "Solicitar excepción"],
                            generated_at=datetime.now().isoformat(),
                            status="pending"
                        )
                        questions.append(question)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generando preguntas de diseño: {e}")
            return []
    
    def _generate_regulation_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Genera preguntas de normativa"""
        try:
            questions = []
            
            # Analizar cumplimiento normativo
            if context.compliance_issues:
                for issue in context.compliance_issues:
                    if 'regulation' in issue.get('category', '').lower():
                        question = IntelligentQuestion(
                            question_id=f"regulation_{len(questions) + 1}",
                            text=f"¿Cómo se cumple con la normativa {issue.get('regulation_reference', '')}?",
                            question_type="regulation",
                            context=f"Normativa: {issue.get('title', '')}",
                            priority="HIGH",
                            confidence=0.9,
                            related_elements=issue.get('related_elements', []),
                            related_regulations=[issue.get('regulation_reference', '')],
                            suggested_answers=self._generate_regulation_suggestions(issue),
                            generated_at=datetime.now().isoformat(),
                            status="pending"
                        )
                        questions.append(question)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generando preguntas de normativa: {e}")
            return []
    
    def _detect_document_ambiguities(self, document_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta ambigüedades en los documentos"""
        try:
            ambiguities = []
            
            # Buscar contradicciones
            contradictions = document_analysis.get('contradictions', [])
            for contradiction in contradictions:
                ambiguity = {
                    'text': f"contradicción entre {contradiction.get('source1', '')} y {contradiction.get('source2', '')}",
                    'context': contradiction.get('description', ''),
                    'severity': 'high',
                    'confidence': 0.8,
                    'related_elements': contradiction.get('related_elements', []),
                    'related_regulations': contradiction.get('related_regulations', []),
                    'suggested_answers': ['Aclarar la información', 'Proporcionar documentación adicional']
                }
                ambiguities.append(ambiguity)
            
            # Buscar información incompleta
            if document_analysis.get('confidence_score', 0) < 0.7:
                ambiguity = {
                    'text': "información incompleta en los documentos",
                    'context': f"Confianza del análisis: {document_analysis.get('confidence_score', 0):.2f}",
                    'severity': 'medium',
                    'confidence': 0.6,
                    'related_elements': [],
                    'related_regulations': [],
                    'suggested_answers': ['Completar la documentación', 'Proporcionar información adicional']
                }
                ambiguities.append(ambiguity)
            
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando ambigüedades: {e}")
            return []
    
    def _generate_compliance_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Genera sugerencias para problemas de cumplimiento"""
        try:
            suggestions = []
            
            issue_type = issue.get('category', '').lower()
            
            if 'accessibility' in issue_type:
                suggestions.extend([
                    "Instalar rampa de accesibilidad",
                    "Ampliar puertas a mínimo 0.8m",
                    "Añadir ascensor si es necesario"
                ])
            elif 'fire' in issue_type:
                suggestions.extend([
                    "Añadir salidas de emergencia",
                    "Instalar sistemas de detección de incendios",
                    "Mejorar compartimentación"
                ])
            elif 'structural' in issue_type:
                suggestions.extend([
                    "Reforzar estructura",
                    "Verificar cálculos estructurales",
                    "Consultar con ingeniero estructural"
                ])
            else:
                suggestions.extend([
                    "Revisar normativa aplicable",
                    "Consultar con técnico especializado",
                    "Proporcionar documentación adicional"
                ])
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generando sugerencias de cumplimiento: {e}")
            return ["Consultar con técnico especializado"]
    
    def _generate_technical_suggestions(self, element: Dict[str, Any]) -> List[str]:
        """Genera sugerencias para elementos técnicos"""
        try:
            suggestions = []
            
            element_type = element.get('type', '').lower()
            
            if 'door' in element_type:
                suggestions.extend([
                    "Verificar ancho mínimo de 0.8m",
                    "Confirmar tipo de apertura",
                    "Verificar altura de paso"
                ])
            elif 'window' in element_type:
                suggestions.extend([
                    "Verificar área mínima de iluminación",
                    "Confirmar tipo de vidrio",
                    "Verificar dimensiones"
                ])
            elif 'stair' in element_type:
                suggestions.extend([
                    "Verificar dimensiones de escalones",
                    "Confirmar altura de paso",
                    "Verificar barandillas"
                ])
            else:
                suggestions.extend([
                    "Verificar dimensiones",
                    "Confirmar características técnicas",
                    "Proporcionar especificaciones"
                ])
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generando sugerencias técnicas: {e}")
            return ["Verificar especificaciones técnicas"]
    
    def _generate_regulation_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Genera sugerencias para problemas normativos"""
        try:
            suggestions = []
            
            regulation = issue.get('regulation_reference', '').upper()
            
            if 'DB-SU' in regulation:
                suggestions.extend([
                    "Revisar accesibilidad universal",
                    "Verificar dimensiones de pasillos",
                    "Confirmar instalación de ascensores"
                ])
            elif 'DB-SI' in regulation:
                suggestions.extend([
                    "Revisar seguridad contra incendios",
                    "Verificar salidas de emergencia",
                    "Confirmar compartimentación"
                ])
            elif 'DB-HE' in regulation:
                suggestions.extend([
                    "Revisar eficiencia energética",
                    "Verificar aislamiento térmico",
                    "Confirmar instalaciones eficientes"
                ])
            else:
                suggestions.extend([
                    "Revisar normativa específica",
                    "Consultar técnico especializado",
                    "Proporcionar documentación de cumplimiento"
                ])
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generando sugerencias normativas: {e}")
            return ["Consultar normativa aplicable"]
    
    def _filter_and_prioritize_questions(self, questions: List[IntelligentQuestion], 
                                       context: QuestionContext) -> List[IntelligentQuestion]:
        """Filtra y prioriza las preguntas generadas"""
        try:
            # Filtrar preguntas duplicadas
            unique_questions = self._remove_duplicate_questions(questions)
            
            # Priorizar por importancia
            prioritized_questions = sorted(
                unique_questions,
                key=lambda q: (
                    q.priority == 'HIGH',
                    q.confidence,
                    q.question_type in ['compliance', 'regulation']
                ),
                reverse=True
            )
            
            # Limitar número de preguntas
            max_questions = 20
            filtered_questions = prioritized_questions[:max_questions]
            
            return filtered_questions
            
        except Exception as e:
            self.logger.error(f"Error filtrando preguntas: {e}")
            return questions
    
    def _remove_duplicate_questions(self, questions: List[IntelligentQuestion]) -> List[IntelligentQuestion]:
        """Elimina preguntas duplicadas usando embeddings"""
        try:
            if not questions:
                return []
            
            # Generar embeddings para las preguntas
            question_texts = [q.text for q in questions]
            embeddings = self.embedding_model.encode(question_texts)
            
            # Usar FAISS para encontrar similitudes
            if self.embedding_index.ntotal == 0:
                self.embedding_index.add(embeddings.astype('float32'))
            else:
                self.embedding_index.add(embeddings.astype('float32'))
            
            # Encontrar duplicados
            unique_questions = []
            used_indices = set()
            
            for i, question in enumerate(questions):
                if i in used_indices:
                    continue
                
                unique_questions.append(question)
                used_indices.add(i)
                
                # Buscar preguntas similares
                if i < len(embeddings):
                    similarities, indices = self.embedding_index.search(
                        embeddings[i:i+1].astype('float32'), 
                        min(5, len(questions))
                    )
                    
                    for j, sim in zip(indices[0], similarities[0]):
                        if j != i and j not in used_indices and sim > 0.8:
                            used_indices.add(j)
            
            return unique_questions
            
        except Exception as e:
            self.logger.error(f"Error eliminando duplicados: {e}")
            return questions
    
    def _save_question_to_graph(self, question: IntelligentQuestion, project_id: str):
        """Guarda una pregunta en el grafo de conocimiento"""
        try:
            question_data = {
                'id': question.question_id,
                'text': question.text,
                'type': question.question_type,
                'context': question.context,
                'priority': question.priority,
                'status': question.status,
                'answer': ''
            }
            
            self.neo4j_manager.create_question_node(question_data, project_id)
            
        except Exception as e:
            self.logger.error(f"Error guardando pregunta en grafo: {e}")
    
    def answer_question(self, question_id: str, answer: str) -> bool:
        """Responde una pregunta específica"""
        try:
            # Actualizar en Neo4j
            success = self.neo4j_manager.update_question_answer(question_id, answer)
            
            if success:
                self.logger.info(f"Pregunta {question_id} respondida correctamente")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error respondiendo pregunta: {e}")
            return False
    
    def get_question_suggestions(self, question_id: str) -> List[str]:
        """Obtiene sugerencias para responder una pregunta"""
        try:
            # Buscar pregunta en el grafo
            with self.neo4j_manager.get_session() as session:
                query = """
                MATCH (q:Question {id: $question_id})
                RETURN q.suggested_answers as suggestions
                """
                
                result = session.run(query, {'question_id': question_id})
                record = result.single()
                
                if record and record['suggestions']:
                    return json.loads(record['suggestions'])
                else:
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo sugerencias: {e}")
            return []
    
    def analyze_question_quality(self, question: IntelligentQuestion) -> Dict[str, Any]:
        """Analiza la calidad de una pregunta"""
        try:
            # Análisis de legibilidad
            readability_score = textstat.flesch_reading_ease(question.text)
            
            # Análisis de complejidad
            complexity_score = textstat.flesch_kincaid_grade(question.text)
            
            # Análisis de longitud
            word_count = len(question.text.split())
            
            # Análisis de claridad
            clarity_score = self._calculate_clarity_score(question.text)
            
            return {
                'readability_score': readability_score,
                'complexity_score': complexity_score,
                'word_count': word_count,
                'clarity_score': clarity_score,
                'overall_quality': (readability_score + clarity_score) / 2
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando calidad de pregunta: {e}")
            return {}
    
    def _calculate_clarity_score(self, text: str) -> float:
        """Calcula un score de claridad para el texto"""
        try:
            # Factores que mejoran la claridad
            clarity_factors = 0
            
            # Preguntas directas
            if text.strip().endswith('?'):
                clarity_factors += 20
            
            # Longitud apropiada (10-30 palabras)
            word_count = len(text.split())
            if 10 <= word_count <= 30:
                clarity_factors += 20
            elif 5 <= word_count < 10 or 30 < word_count <= 50:
                clarity_factors += 10
            
            # Uso de palabras técnicas apropiadas
            technical_words = ['dimensiones', 'cumplimiento', 'normativa', 'accesibilidad', 'seguridad']
            technical_count = sum(1 for word in technical_words if word in text.lower())
            clarity_factors += min(technical_count * 10, 30)
            
            # Evitar jerga excesiva
            jargon_words = ['per se', 'ipso facto', 'ergo', 'viz']
            jargon_count = sum(1 for word in jargon_words if word in text.lower())
            clarity_factors -= jargon_count * 10
            
            return max(0, min(100, clarity_factors))
            
        except Exception as e:
            self.logger.error(f"Error calculando claridad: {e}")
            return 50.0
