"""
Analizador de contenido de documentos arquitectónicos.
Analiza y extrae información específica de memorias y planos.
"""

import os
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

from .pdf_processor import PDFDocument, PDFPage
from .document_classifier import DocumentClassification
from .enhanced_ocr_processor import EnhancedOCRProcessor

logger = logging.getLogger(__name__)

@dataclass
class DocumentContent:
    """Contenido extraído de un documento."""
    document_type: str
    title: str
    sections: List[Dict[str, Any]]
    technical_data: Dict[str, Any]
    visual_elements: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    confidence: float

@dataclass
class MemoryAnalysis:
    """Análisis específico de una memoria."""
    title: str
    sections: List[Dict[str, Any]]
    technical_specifications: Dict[str, Any]
    calculations: List[Dict[str, Any]]
    normative_references: List[str]
    compliance_indicators: List[Dict[str, Any]]

@dataclass
class PlanAnalysis:
    """Análisis específico de un plano."""
    title: str
    plan_type: str  # 'planta', 'alzado', 'sección', 'detalle'
    scale: str
    dimensions: Dict[str, Any]
    architectural_elements: List[Dict[str, Any]]
    technical_annotations: List[str]
    compliance_indicators: List[Dict[str, Any]]

class DocumentAnalyzer:
    """Analizador de contenido de documentos arquitectónicos."""
    
    def __init__(self, ocr_processor: EnhancedOCRProcessor = None):
        """
        Inicializar el analizador de documentos.
        
        Args:
            ocr_processor: Procesador OCR para análisis de imágenes
        """
        self.ocr_processor = ocr_processor or EnhancedOCRProcessor()
        
        # Patrones para extraer información específica
        self.memory_patterns = self._initialize_memory_patterns()
        self.plan_patterns = self._initialize_plan_patterns()
        
        logger.info("DocumentAnalyzer initialized")
    
    def _initialize_memory_patterns(self) -> Dict[str, List[str]]:
        """Inicializar patrones para análisis de memorias."""
        return {
            'title_patterns': [
                r'memoria\s+(?:descriptiva|técnica|constructiva|justificativa)',
                r'memoria\s+de\s+cálculo',
                r'proyecto\s+de\s+[^.]*',
                r'descripción\s+general',
                r'justificación\s+del\s+proyecto'
            ],
            'section_patterns': [
                r'^\s*\d+\.\s*([^.\n]+)',
                r'^\s*\d+\.\d+\s*([^.\n]+)',
                r'^\s*[A-Z][^.\n]*:',
                r'^\s*[a-z][^.\n]*:'
            ],
            'technical_patterns': [
                r'superficie\s*:?\s*(\d+(?:\.\d+)?)\s*m²',
                r'altura\s*:?\s*(\d+(?:\.\d+)?)\s*m',
                r'plantas\s*:?\s*(\d+)',
                r'aforo\s*:?\s*(\d+)',
                r'carga\s*:?\s*(\d+(?:\.\d+)?)\s*kg/m²',
                r'resistencia\s*:?\s*(\d+(?:\.\d+)?)\s*MPa'
            ],
            'normative_patterns': [
                r'cte\s+db-[a-z]+',
                r'código\s+técnico\s+de\s+la\s+edificación',
                r'normativa\s+[^.\n]*',
                r'reglamento\s+[^.\n]*',
                r'ley\s+[^.\n]*'
            ]
        }
    
    def _initialize_plan_patterns(self) -> Dict[str, List[str]]:
        """Inicializar patrones para análisis de planos."""
        return {
            'title_patterns': [
                r'planta\s+(?:baja|primera|segunda|tercera)',
                r'alzado\s+[^.\n]*',
                r'sección\s+[^.\n]*',
                r'detalle\s+[^.\n]*',
                r'fachada\s+[^.\n]*'
            ],
            'scale_patterns': [
                r'escala\s*:?\s*1:(\d+)',
                r'escala\s*:?\s*1/(\d+)',
                r'1:(\d+)',
                r'1/(\d+)'
            ],
            'dimension_patterns': [
                r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*m\s*x\s*(\d+(?:\.\d+)?)\s*m',
                r'(\d+(?:\.\d+)?)\s*mm\s*x\s*(\d+(?:\.\d+)?)\s*mm'
            ],
            'architectural_patterns': [
                r'muro\s+[^.\n]*',
                r'tabique\s+[^.\n]*',
                r'forjado\s+[^.\n]*',
                r'viga\s+[^.\n]*',
                r'pilar\s+[^.\n]*',
                r'puerta\s+[^.\n]*',
                r'ventana\s+[^.\n]*'
            ]
        }
    
    def analyze_document(self, pdf_doc: PDFDocument, classification: DocumentClassification) -> DocumentContent:
        """
        Analizar el contenido de un documento.
        
        Args:
            pdf_doc: Documento PDF procesado
            classification: Clasificación del documento
            
        Returns:
            Contenido extraído del documento
        """
        try:
            logger.info(f"Analizando documento: {pdf_doc.filename}")
            
            if classification.document_type == 'memoria':
                return self._analyze_memory(pdf_doc, classification)
            elif classification.document_type == 'plano':
                return self._analyze_plan(pdf_doc, classification)
            else:
                return self._analyze_generic(pdf_doc, classification)
                
        except Exception as e:
            logger.error(f"Error analizando documento {pdf_doc.filename}: {e}")
            raise
    
    def _analyze_memory(self, pdf_doc: PDFDocument, classification: DocumentClassification) -> DocumentContent:
        """Analizar una memoria descriptiva."""
        try:
            text = pdf_doc.text_content
            
            # Extraer título
            title = self._extract_title(text, self.memory_patterns['title_patterns'])
            
            # Extraer secciones
            sections = self._extract_sections(text, self.memory_patterns['section_patterns'])
            
            # Extraer datos técnicos
            technical_data = self._extract_technical_data(text, self.memory_patterns['technical_patterns'])
            
            # Extraer referencias normativas
            normative_refs = self._extract_normative_references(text, self.memory_patterns['normative_patterns'])
            
            # Analizar elementos visuales
            visual_elements = self._analyze_visual_elements(pdf_doc.images)
            
            # Crear análisis específico de memoria
            memory_analysis = MemoryAnalysis(
                title=title,
                sections=sections,
                technical_specifications=technical_data,
                calculations=self._extract_calculations(text),
                normative_references=normative_refs,
                compliance_indicators=self._extract_compliance_indicators(text, 'memoria')
            )
            
            return DocumentContent(
                document_type='memoria',
                title=title,
                sections=sections,
                technical_data=technical_data,
                visual_elements=visual_elements,
                metadata={
                    'page_count': pdf_doc.page_count,
                    'file_size': pdf_doc.file_size,
                    'processing_time': pdf_doc.processing_time,
                    'memory_analysis': memory_analysis
                },
                confidence=classification.confidence
            )
            
        except Exception as e:
            logger.error(f"Error analizando memoria: {e}")
            raise
    
    def _analyze_plan(self, pdf_doc: PDFDocument, classification: DocumentClassification) -> DocumentContent:
        """Analizar un plano arquitectónico."""
        try:
            text = pdf_doc.text_content
            
            # Extraer título
            title = self._extract_title(text, self.plan_patterns['title_patterns'])
            
            # Determinar tipo de plano
            plan_type = self._determine_plan_type(text, title)
            
            # Extraer escala
            scale = self._extract_scale(text, self.plan_patterns['scale_patterns'])
            
            # Extraer dimensiones
            dimensions = self._extract_dimensions(text, self.plan_patterns['dimension_patterns'])
            
            # Extraer elementos arquitectónicos
            architectural_elements = self._extract_architectural_elements(text, self.plan_patterns['architectural_patterns'])
            
            # Analizar elementos visuales
            visual_elements = self._analyze_visual_elements(pdf_doc.images)
            
            # Crear análisis específico de plano
            plan_analysis = PlanAnalysis(
                title=title,
                plan_type=plan_type,
                scale=scale,
                dimensions=dimensions,
                architectural_elements=architectural_elements,
                technical_annotations=self._extract_technical_annotations(text),
                compliance_indicators=self._extract_compliance_indicators(text, 'plano')
            )
            
            return DocumentContent(
                document_type='plano',
                title=title,
                sections=[],  # Los planos no tienen secciones como las memorias
                technical_data=dimensions,
                visual_elements=visual_elements,
                metadata={
                    'page_count': pdf_doc.page_count,
                    'file_size': pdf_doc.file_size,
                    'processing_time': pdf_doc.processing_time,
                    'plan_analysis': plan_analysis
                },
                confidence=classification.confidence
            )
            
        except Exception as e:
            logger.error(f"Error analizando plano: {e}")
            raise
    
    def _analyze_generic(self, pdf_doc: PDFDocument, classification: DocumentClassification) -> DocumentContent:
        """Analizar un documento genérico."""
        try:
            text = pdf_doc.text_content
            
            # Extraer título genérico
            title = self._extract_generic_title(text)
            
            # Extraer secciones genéricas
            sections = self._extract_generic_sections(text)
            
            # Analizar elementos visuales
            visual_elements = self._analyze_visual_elements(pdf_doc.images)
            
            return DocumentContent(
                document_type=classification.document_type,
                title=title,
                sections=sections,
                technical_data={},
                visual_elements=visual_elements,
                metadata={
                    'page_count': pdf_doc.page_count,
                    'file_size': pdf_doc.file_size,
                    'processing_time': pdf_doc.processing_time
                },
                confidence=classification.confidence
            )
            
        except Exception as e:
            logger.error(f"Error analizando documento genérico: {e}")
            raise
    
    def _extract_title(self, text: str, patterns: List[str]) -> str:
        """Extraer título del documento."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(0).strip()
        
        # Fallback: usar las primeras líneas
        lines = text.split('\n')[:5]
        for line in lines:
            if len(line.strip()) > 10:
                return line.strip()
        
        return "Sin título"
    
    def _extract_sections(self, text: str, patterns: List[str]) -> List[Dict[str, Any]]:
        """Extraer secciones del documento."""
        sections = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                section_text = match.group(1) if match.groups() else match.group(0)
                sections.append({
                    'title': section_text.strip(),
                    'pattern': pattern,
                    'position': match.start()
                })
        
        return sections
    
    def _extract_technical_data(self, text: str, patterns: List[str]) -> Dict[str, Any]:
        """Extraer datos técnicos del documento."""
        technical_data = {}
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                key = match.group(0).split(':')[0].strip().lower()
                value = match.group(1) if match.groups() else match.group(0)
                technical_data[key] = value
        
        return technical_data
    
    def _extract_normative_references(self, text: str, patterns: List[str]) -> List[str]:
        """Extraer referencias normativas."""
        references = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref = match.group(0).strip()
                if ref not in references:
                    references.append(ref)
        
        return references
    
    def _extract_calculations(self, text: str) -> List[Dict[str, Any]]:
        """Extraer cálculos del documento."""
        calculations = []
        
        # Patrones para cálculos
        calc_patterns = [
            r'(\d+(?:\.\d+)?)\s*[+\-*/]\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in calc_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                calculations.append({
                    'expression': match.group(0),
                    'operands': match.groups()[:2],
                    'result': match.groups()[2] if len(match.groups()) > 2 else None
                })
        
        return calculations
    
    def _determine_plan_type(self, text: str, title: str) -> str:
        """Determinar el tipo de plano."""
        text_lower = text.lower()
        title_lower = title.lower()
        
        if 'planta' in title_lower or 'planta' in text_lower:
            return 'planta'
        elif 'alzado' in title_lower or 'alzado' in text_lower:
            return 'alzado'
        elif 'sección' in title_lower or 'sección' in text_lower:
            return 'sección'
        elif 'detalle' in title_lower or 'detalle' in text_lower:
            return 'detalle'
        elif 'fachada' in title_lower or 'fachada' in text_lower:
            return 'fachada'
        else:
            return 'plano'
    
    def _extract_scale(self, text: str, patterns: List[str]) -> str:
        """Extraer escala del plano."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"1:{match.group(1)}"
        
        return "Sin escala"
    
    def _extract_dimensions(self, text: str, patterns: List[str]) -> Dict[str, Any]:
        """Extraer dimensiones del plano."""
        dimensions = {}
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    dimensions[f"dimension_{len(dimensions)}"] = {
                        'width': match.group(1),
                        'height': match.group(2),
                        'expression': match.group(0)
                    }
        
        return dimensions
    
    def _extract_architectural_elements(self, text: str, patterns: List[str]) -> List[Dict[str, Any]]:
        """Extraer elementos arquitectónicos."""
        elements = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                elements.append({
                    'type': match.group(0).split()[0].lower(),
                    'description': match.group(0).strip(),
                    'position': match.start()
                })
        
        return elements
    
    def _extract_technical_annotations(self, text: str) -> List[str]:
        """Extraer anotaciones técnicas del plano."""
        annotations = []
        
        # Patrones para anotaciones técnicas
        annotation_patterns = [
            r'cota\s*:?\s*[^.\n]*',
            r'nivel\s*:?\s*[^.\n]*',
            r'altura\s*:?\s*[^.\n]*',
            r'espesor\s*:?\s*[^.\n]*'
        ]
        
        for pattern in annotation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                annotations.append(match.group(0).strip())
        
        return annotations
    
    def _extract_compliance_indicators(self, text: str, doc_type: str) -> List[Dict[str, Any]]:
        """Extraer indicadores de cumplimiento normativo."""
        indicators = []
        
        # Patrones específicos por tipo de documento
        if doc_type == 'memoria':
            compliance_patterns = [
                r'cte\s+db-[a-z]+',
                r'normativa\s+[^.\n]*',
                r'cumplimiento\s+[^.\n]*',
                r'verificación\s+[^.\n]*'
            ]
        else:  # plano
            compliance_patterns = [
                r'escala\s+[^.\n]*',
                r'cotas\s+[^.\n]*',
                r'dimensiones\s+[^.\n]*',
                r'símbolos\s+[^.\n]*'
            ]
        
        for pattern in compliance_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                indicators.append({
                    'type': 'compliance',
                    'content': match.group(0).strip(),
                    'pattern': pattern
                })
        
        return indicators
    
    def _analyze_visual_elements(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analizar elementos visuales de las imágenes."""
        visual_elements = []
        
        for img in images:
            if 'data' in img:
                try:
                    # Aquí se podría usar OCR para analizar las imágenes
                    # Por ahora, solo extraemos información básica
                    visual_elements.append({
                        'page': img.get('page', 0),
                        'index': img.get('index', 0),
                        'size': img.get('size', 0),
                        'format': img.get('format', 'unknown'),
                        'has_text': False  # Se podría implementar OCR aquí
                    })
                except Exception as e:
                    logger.warning(f"Error analizando imagen: {e}")
        
        return visual_elements
    
    def _extract_generic_title(self, text: str) -> str:
        """Extraer título genérico del documento."""
        lines = text.split('\n')[:10]
        for line in lines:
            if len(line.strip()) > 5 and len(line.strip()) < 100:
                return line.strip()
        return "Documento sin título"
    
    def _extract_generic_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extraer secciones genéricas del documento."""
        sections = []
        
        # Patrón genérico para secciones
        pattern = r'^\s*\d+\.\s*([^.\n]+)'
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            sections.append({
                'title': match.group(1).strip(),
                'pattern': pattern,
                'position': match.start()
            })
        
        return sections
