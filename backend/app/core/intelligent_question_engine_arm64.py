"""
Motor de Preguntas Inteligentes - Versión ARM64
Fase 3: Sistema de Preguntas Inteligentes
Optimizado para Oracle Cloud Ampere A1 (ARM64)
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
# Alternativa ARM64 para FAISS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
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

class ARM64SimilaritySearch:
    """Alternativa ARM64 para búsqueda de similitud usando scikit-learn"""
    
    def __init__(self, dimension: int = 384):
        """Inicializar búsqueda de similitud ARM64"""
        self.dimension = dimension
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='spanish',
            ngram_range=(1, 2)
        )
        self.embeddings = None
        self.texts = []
        
    def add_texts(self, texts: List[str]):
        """Añadir textos para búsqueda"""
        self.texts.extend(texts)
        # Crear embeddings usando TF-IDF
        tfidf_matrix = self.vectorizer.fit_transform(self.texts)
        self.embeddings = tfidf_matrix.toarray()
        
    def search(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Buscar textos similares"""
        if self.embeddings is None:
            return []
            
        # Vectorizar query
        query_vector = self.vectorizer.transform([query]).toarray()
        
        # Calcular similitud coseno
        similarities = cosine_similarity(query_vector, self.embeddings)[0]
        
        # Obtener top-k resultados
        top_indices = np.argsort(similarities)[::-1][:k]
        results = [(idx, similarities[idx]) for idx in top_indices if similarities[idx] > 0.1]
        
        return results

class IntelligentQuestionEngine:
    """Motor de preguntas inteligentes con IA - Versión ARM64"""
    
    def __init__(self):
        """Inicializar motor de preguntas"""
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.neo4j_manager = Neo4jManager()
        
        # Inicializar modelo de embeddings ARM64
        try:
            self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Modelo de embeddings ARM64 cargado correctamente")
        except Exception as e:
            logger.warning(f"Error cargando modelo de embeddings: {e}")
            self.sentence_model = None
            
        # Inicializar búsqueda de similitud ARM64
        self.similarity_search = ARM64SimilaritySearch()
        
        # Configuración de preguntas
        self.question_templates = {
            'clarification': [
                "¿Puede aclarar {element} en {context}?",
                "¿Es correcto que {element} tiene {value}?",
                "¿Confirma que {element} cumple con {regulation}?"
            ],
            'compliance': [
                "¿Cumple {element} con la normativa {regulation}?",
                "¿Está {element} dentro de los límites permitidos?",
                "¿Se ha verificado {requirement} en {element}?"
            ],
            'technical': [
                "¿Cuál es la justificación técnica de {element}?",
                "¿Se han considerado todas las cargas en {element}?",
                "¿Es adecuado el material {material} para {element}?"
            ],
            'design': [
                "¿Es funcional el diseño de {element}?",
                "¿Cumple {element} con los requisitos de accesibilidad?",
                "¿Es eficiente energéticamente {element}?"
            ],
            'regulation': [
                "¿Aplica la normativa {regulation} a este proyecto?",
                "¿Cuál es la interpretación de {regulation} para {element}?",
                "¿Hay excepciones aplicables a {regulation}?"
            ]
        }
        
        # Preguntas generadas
        self.generated_questions: List[IntelligentQuestion] = []
        
    def generate_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Generar preguntas inteligentes basadas en el contexto"""
        try:
            logger.info("Generando preguntas inteligentes...")
            
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
            
            # 5. Preguntas normativas
            regulation_questions = self._generate_regulation_questions(context)
            questions.extend(regulation_questions)
            
            # Filtrar y priorizar preguntas
            filtered_questions = self._filter_and_prioritize_questions(questions)
            
            # Añadir a la lista de preguntas generadas
            self.generated_questions.extend(filtered_questions)
            
            logger.info(f"Generadas {len(filtered_questions)} preguntas inteligentes")
            return filtered_questions
            
        except Exception as e:
            logger.error(f"Error generando preguntas: {e}")
            return []
    
    def _generate_clarification_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Generar preguntas de clarificación"""
        questions = []
        
        # Analizar discrepancias entre documentos
        if context.document_analysis.get('discrepancies'):
            for discrepancy in context.document_analysis['discrepancies']:
                question = IntelligentQuestion(
                    question_id=f"clar_{len(questions)}",
                    text=f"¿Puede aclarar la discrepancia en {discrepancy.get('element', 'elemento')}?",
                    question_type='clarification',
                    context=discrepancy.get('context', ''),
                    priority='HIGH',
                    confidence=0.8,
                    related_elements=[discrepancy.get('element', '')],
                    related_regulations=[],
                    suggested_answers=[],
                    generated_at=datetime.now().isoformat(),
                    status='pending'
                )
                questions.append(question)
        
        return questions
    
    def _generate_compliance_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Generar preguntas de cumplimiento"""
        questions = []
        
        # Analizar problemas de cumplimiento
        if context.compliance_issues:
            for issue in context.compliance_issues:
                question = IntelligentQuestion(
                    question_id=f"comp_{len(questions)}",
                    text=f"¿Cumple {issue.get('element', 'elemento')} con {issue.get('regulation', 'la normativa')}?",
                    question_type='compliance',
                    context=issue.get('context', ''),
                    priority='HIGH',
                    confidence=0.9,
                    related_elements=[issue.get('element', '')],
                    related_regulations=[issue.get('regulation', '')],
                    suggested_answers=[],
                    generated_at=datetime.now().isoformat(),
                    status='pending'
                )
                questions.append(question)
        
        return questions
    
    def _generate_technical_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Generar preguntas técnicas"""
        questions = []
        
        # Analizar datos estructurales
        if context.project_data.get('structural_data'):
            structural = context.project_data['structural_data']
            if structural.get('materials'):
                question = IntelligentQuestion(
                    question_id=f"tech_{len(questions)}",
                    text=f"¿Es adecuado el material {structural['materials'][0]} para la estructura?",
                    question_type='technical',
                    context='Análisis estructural',
                    priority='MEDIUM',
                    confidence=0.7,
                    related_elements=['estructura'],
                    related_regulations=[],
                    suggested_answers=[],
                    generated_at=datetime.now().isoformat(),
                    status='pending'
                )
                questions.append(question)
        
        return questions
    
    def _generate_design_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Generar preguntas de diseño"""
        questions = []
        
        # Analizar datos de accesibilidad
        if context.project_data.get('safety_data', {}).get('accessibility'):
            question = IntelligentQuestion(
                question_id=f"design_{len(questions)}",
                text="¿Cumple el diseño con todos los requisitos de accesibilidad?",
                question_type='design',
                context='Análisis de accesibilidad',
                priority='HIGH',
                confidence=0.8,
                related_elements=['accesibilidad'],
                related_regulations=['CTE DB-SUA'],
                suggested_answers=[],
                generated_at=datetime.now().isoformat(),
                status='pending'
            )
            questions.append(question)
        
        return questions
    
    def _generate_regulation_questions(self, context: QuestionContext) -> List[IntelligentQuestion]:
        """Generar preguntas normativas"""
        questions = []
        
        # Analizar normativas aplicables
        regulations = ['CTE DB-HE', 'CTE DB-HR', 'CTE DB-SI', 'CTE DB-SUA']
        for regulation in regulations:
            question = IntelligentQuestion(
                question_id=f"reg_{len(questions)}",
                text=f"¿Se ha verificado el cumplimiento de {regulation}?",
                question_type='regulation',
                context='Verificación normativa',
                priority='HIGH',
                confidence=0.9,
                related_elements=[],
                related_regulations=[regulation],
                suggested_answers=[],
                generated_at=datetime.now().isoformat(),
                status='pending'
            )
            questions.append(question)
        
        return questions
    
    def _filter_and_prioritize_questions(self, questions: List[IntelligentQuestion]) -> List[IntelligentQuestion]:
        """Filtrar y priorizar preguntas"""
        # Filtrar preguntas duplicadas
        unique_questions = []
        seen_texts = set()
        
        for question in questions:
            if question.text not in seen_texts:
                unique_questions.append(question)
                seen_texts.add(question.text)
        
        # Ordenar por prioridad y confianza
        priority_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        unique_questions.sort(
            key=lambda q: (priority_order.get(q.priority, 0), q.confidence),
            reverse=True
        )
        
        # Limitar a 10 preguntas por análisis
        return unique_questions[:10]
    
    def answer_question(self, question_id: str, answer: str) -> bool:
        """Responder a una pregunta"""
        try:
            # Buscar la pregunta
            question = next((q for q in self.generated_questions if q.question_id == question_id), None)
            if not question:
                logger.warning(f"Pregunta {question_id} no encontrada")
                return False
            
            # Actualizar estado
            question.status = 'answered'
            question.suggested_answers.append(answer)
            
            logger.info(f"Pregunta {question_id} respondida: {answer}")
            return True
            
        except Exception as e:
            logger.error(f"Error respondiendo pregunta {question_id}: {e}")
            return False
    
    def get_question_context(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Obtener contexto de una pregunta"""
        question = next((q for q in self.generated_questions if q.question_id == question_id), None)
        if not question:
            return None
        
        return {
            'question': question.text,
            'context': question.context,
            'related_elements': question.related_elements,
            'related_regulations': question.related_regulations,
            'priority': question.priority,
            'confidence': question.confidence
        }
    
    def get_all_questions(self, status: Optional[str] = None) -> List[IntelligentQuestion]:
        """Obtener todas las preguntas o filtrar por estado"""
        if status:
            return [q for q in self.generated_questions if q.status == status]
        return self.generated_questions
    
    def clear_questions(self):
        """Limpiar todas las preguntas"""
        self.generated_questions.clear()
        logger.info("Preguntas limpiadas")
