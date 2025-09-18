"""
Clasificador automático de documentos arquitectónicos.
Clasifica automáticamente entre memorias y planos usando IA y análisis de contenido.
"""

import os
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io
import cv2
import numpy as np

from .enhanced_ocr_processor import EnhancedOCRProcessor
from .ai_client import AIClient

logger = logging.getLogger(__name__)

@dataclass
class DocumentClassification:
    """Resultado de la clasificación de un documento."""
    document_type: str  # 'memoria' o 'plano'
    confidence: float
    reasoning: str
    detected_elements: List[str]
    page_count: int
    text_content: str
    visual_elements: List[Dict[str, Any]]
    processing_time: float

@dataclass
class DocumentAnalysis:
    """Análisis completo de un documento."""
    filename: str
    classification: DocumentClassification
    extracted_data: Dict[str, Any]
    metadata: Dict[str, Any]

class DocumentClassifier:
    """Clasificador automático de documentos arquitectónicos."""
    
    def __init__(self, ai_client: AIClient = None, ocr_processor: EnhancedOCRProcessor = None):
        """
        Inicializar el clasificador de documentos.
        
        Args:
            ai_client: Cliente de IA para análisis de contenido
            ocr_processor: Procesador OCR para análisis de imágenes
        """
        self.ai_client = ai_client or AIClient()
        self.ocr_processor = ocr_processor or EnhancedOCRProcessor()
        
        # Patrones para identificar tipos de documentos
        self.memoria_patterns = self._initialize_memoria_patterns()
        self.plano_patterns = self._initialize_plano_patterns()
        
        # Configuración de clasificación
        self.min_confidence = 0.6
        self.max_pages_for_full_analysis = 50
        
        logger.info("DocumentClassifier initialized")
    
    def _initialize_memoria_patterns(self) -> Dict[str, List[str]]:
        """Inicializar patrones para identificar memorias."""
        return {
            'title_keywords': [
                'memoria', 'memoria descriptiva', 'memoria de cálculo',
                'memoria técnica', 'memoria constructiva', 'memoria justificativa',
                'descripción', 'justificación', 'cálculo', 'análisis'
            ],
            'content_keywords': [
                'objeto del proyecto', 'descripción general', 'justificación',
                'cálculos', 'análisis', 'dimensionamiento', 'criterios',
                'normativa aplicable', 'condiciones generales', 'especificaciones',
                'materiales', 'sistemas constructivos', 'instalaciones',
                'medidas de seguridad', 'accesibilidad', 'eficiencia energética'
            ],
            'section_headers': [
                '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.',
                '1.1', '1.2', '1.3', '2.1', '2.2', '2.3',
                'introducción', 'objeto', 'descripción', 'cálculos',
                'conclusiones', 'anexos', 'bibliografía'
            ],
            'technical_terms': [
                'carga', 'resistencia', 'deformación', 'tensión',
                'coeficiente', 'factor', 'módulo', 'esfuerzo',
                'dimensionamiento', 'verificación', 'comprobación',
                'normativa', 'reglamento', 'código técnico', 'cte'
            ]
        }
    
    def _initialize_plano_patterns(self) -> Dict[str, List[str]]:
        """Inicializar patrones para identificar planos."""
        return {
            'title_keywords': [
                'plano', 'planos', 'planta', 'plantas', 'alzado', 'alzados',
                'sección', 'secciones', 'corte', 'cortes', 'detalle', 'detalles',
                'fachada', 'fachadas', 'perspectiva', 'perspectivas'
            ],
            'content_keywords': [
                'escala', 'norte', 'cota', 'nivel', 'altura', 'dimensión',
                'planta baja', 'primera planta', 'segunda planta', 'sótano',
                'entreplanta', 'azotea', 'cubierta', 'garaje', 'aparcamiento',
                'escalera', 'ascensor', 'rampa', 'pasillo', 'vestíbulo'
            ],
            'visual_elements': [
                'líneas', 'rectángulos', 'círculos', 'texto', 'dimensiones',
                'cotas', 'símbolos', 'leyenda', 'norte', 'escala'
            ],
            'architectural_terms': [
                'muro', 'tabique', 'forjado', 'viga', 'pilar', 'columna',
                'puerta', 'ventana', 'hueco', 'vanos', 'escalera', 'rampa',
                'ascensor', 'montacargas', 'garaje', 'aparcamiento'
            ]
        }
    
    async def classify_document(self, file_path: str) -> DocumentAnalysis:
        """
        Clasificar un documento automáticamente.
        
        Args:
            file_path: Ruta del archivo PDF
            
        Returns:
            Análisis completo del documento
        """
        try:
            logger.info(f"Clasificando documento: {file_path}")
            
            # Extraer contenido del PDF
            pdf_content = self._extract_pdf_content(file_path)
            
            # Analizar contenido textual
            text_analysis = self._analyze_text_content(pdf_content['text'])
            
            # Analizar elementos visuales
            visual_analysis = self._analyze_visual_elements(pdf_content['images'])
            
            # Clasificar usando IA
            ai_classification = await self._classify_with_ai(
                pdf_content['text'], 
                visual_analysis
            )
            
            # Combinar análisis para clasificación final
            final_classification = self._combine_analyses(
                text_analysis, 
                visual_analysis, 
                ai_classification
            )
            
            # Crear análisis completo
            analysis = DocumentAnalysis(
                filename=Path(file_path).name,
                classification=final_classification,
                extracted_data=pdf_content,
                metadata={
                    'file_size': os.path.getsize(file_path),
                    'page_count': pdf_content['page_count'],
                    'processing_time': final_classification.processing_time
                }
            )
            
            logger.info(f"Documento clasificado como: {final_classification.document_type} "
                       f"(confianza: {final_classification.confidence:.2f})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error clasificando documento {file_path}: {e}")
            raise
    
    def _extract_pdf_content(self, file_path: str) -> Dict[str, Any]:
        """Extraer contenido de un archivo PDF."""
        try:
            doc = fitz.open(file_path)
            text_content = ""
            images = []
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc[page_num]
                
                # Extraer texto
                page_text = page.get_text()
                text_content += f"\n--- PÁGINA {page_num + 1} ---\n{page_text}\n"
                
                # Extraer imágenes si no es demasiado largo
                if page_count <= self.max_pages_for_full_analysis:
                    page_images = self._extract_page_images(page, page_num)
                    images.extend(page_images)
            
            doc.close()
            
            return {
                'text': text_content,
                'images': images,
                'page_count': page_count
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo contenido PDF: {e}")
            return {
                'text': "",
                'images': [],
                'page_count': 0
            }
    
    def _extract_page_images(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Extraer imágenes de una página PDF."""
        try:
            images = []
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    img_array = np.frombuffer(img_data, dtype=np.uint8)
                    cv_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    # Analizar imagen con OCR
                    ocr_result = self.ocr_processor.extract_text_from_image(cv_image)
                    
                    images.append({
                        'page': page_num,
                        'index': img_index,
                        'text': ocr_result.text,
                        'confidence': ocr_result.confidence,
                        'bounding_boxes': ocr_result.bounding_boxes
                    })
                
                pix = None
            
            return images
            
        except Exception as e:
            logger.error(f"Error extrayendo imágenes de página {page_num}: {e}")
            return []
    
    def _analyze_text_content(self, text: str) -> Dict[str, Any]:
        """Analizar contenido textual del documento."""
        text_lower = text.lower()
        
        # Contar patrones de memoria
        memoria_score = 0
        memoria_elements = []
        
        for category, patterns in self.memoria_patterns.items():
            for pattern in patterns:
                if re.search(pattern.lower(), text_lower):
                    memoria_score += 1
                    memoria_elements.append(pattern)
        
        # Contar patrones de plano
        plano_score = 0
        plano_elements = []
        
        for category, patterns in self.plano_patterns.items():
            for pattern in patterns:
                if re.search(pattern.lower(), text_lower):
                    plano_score += 1
                    plano_elements.append(pattern)
        
        # Calcular confianza
        total_patterns = len(memoria_elements) + len(plano_elements)
        memoria_confidence = memoria_score / total_patterns if total_patterns > 0 else 0
        plano_confidence = plano_score / total_patterns if total_patterns > 0 else 0
        
        return {
            'memoria_score': memoria_score,
            'plano_score': plano_score,
            'memoria_confidence': memoria_confidence,
            'plano_confidence': plano_confidence,
            'memoria_elements': memoria_elements,
            'plano_elements': plano_elements,
            'text_length': len(text),
            'word_count': len(text.split())
        }
    
    def _analyze_visual_elements(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar elementos visuales del documento."""
        if not images:
            return {
                'has_visual_content': False,
                'text_in_images': [],
                'architectural_elements': [],
                'confidence': 0.0
            }
        
        architectural_elements = []
        text_in_images = []
        
        for img in images:
            if img['text']:
                text_in_images.append(img['text'])
                
                # Buscar elementos arquitectónicos en el texto de las imágenes
                for term in self.plano_patterns['architectural_terms']:
                    if term.lower() in img['text'].lower():
                        architectural_elements.append(term)
        
        # Calcular confianza basada en elementos arquitectónicos
        confidence = min(len(architectural_elements) / 10.0, 1.0) if architectural_elements else 0.0
        
        return {
            'has_visual_content': True,
            'text_in_images': text_in_images,
            'architectural_elements': architectural_elements,
            'confidence': confidence,
            'image_count': len(images)
        }
    
    async def _classify_with_ai(self, text: str, visual_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Clasificar documento usando IA."""
        try:
            # Preparar prompt para IA
            prompt = f"""
            Analiza el siguiente documento arquitectónico y clasifícalo como 'memoria' o 'plano'.
            
            CONTENIDO DEL DOCUMENTO:
            {text[:2000]}  # Limitar tamaño para evitar tokens excesivos
            
            ELEMENTOS VISUALES DETECTADOS:
            {visual_analysis.get('architectural_elements', [])}
            
            CRITERIOS DE CLASIFICACIÓN:
            - MEMORIA: Documento textual con descripciones, cálculos, justificaciones, especificaciones técnicas
            - PLANO: Documento gráfico con dibujos, planos, alzados, secciones, detalles arquitectónicos
            
            Responde ÚNICAMENTE en formato JSON:
            {{
                "document_type": "memoria" o "plano",
                "confidence": 0.0-1.0,
                "reasoning": "explicación breve de la clasificación",
                "key_indicators": ["indicador1", "indicador2", ...]
            }}
            """
            
            response = await self.ai_client.generate_response(prompt)
            
            # Parsear respuesta JSON
            import json
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback si no se puede parsear JSON
                return {
                    "document_type": "memoria" if "memoria" in response.lower() else "plano",
                    "confidence": 0.5,
                    "reasoning": "Clasificación basada en análisis de texto",
                    "key_indicators": []
                }
                
        except Exception as e:
            logger.error(f"Error en clasificación con IA: {e}")
            return {
                "document_type": "memoria",
                "confidence": 0.3,
                "reasoning": "Error en análisis de IA, usando clasificación por defecto",
                "key_indicators": []
            }
    
    def _combine_analyses(self, 
                         text_analysis: Dict[str, Any], 
                         visual_analysis: Dict[str, Any], 
                         ai_classification: Dict[str, Any]) -> DocumentClassification:
        """Combinar todos los análisis para la clasificación final."""
        
        # Pesos para cada tipo de análisis
        text_weight = 0.4
        visual_weight = 0.3
        ai_weight = 0.3
        
        # Calcular confianza combinada
        text_confidence = max(text_analysis['memoria_confidence'], text_analysis['plano_confidence'])
        visual_confidence = visual_analysis['confidence']
        ai_confidence = ai_classification['confidence']
        
        combined_confidence = (
            text_confidence * text_weight +
            visual_confidence * visual_weight +
            ai_confidence * ai_weight
        )
        
        # Determinar tipo de documento
        if text_analysis['memoria_confidence'] > text_analysis['plano_confidence']:
            text_type = 'memoria'
        else:
            text_type = 'plano'
        
        ai_type = ai_classification['document_type']
        
        # Decidir tipo final
        if text_type == ai_type:
            final_type = text_type
        else:
            # Si hay conflicto, usar el que tenga mayor confianza
            if text_analysis['memoria_confidence'] > ai_confidence:
                final_type = text_type
            else:
                final_type = ai_type
        
        # Crear reasoning
        reasoning = f"""
        Análisis textual: {text_type} (confianza: {text_analysis['memoria_confidence']:.2f})
        Análisis visual: {visual_analysis['confidence']:.2f}
        Análisis IA: {ai_type} (confianza: {ai_confidence:.2f})
        Clasificación final: {final_type}
        """
        
        # Detectar elementos
        detected_elements = []
        detected_elements.extend(text_analysis['memoria_elements'][:5])
        detected_elements.extend(text_analysis['plano_elements'][:5])
        detected_elements.extend(visual_analysis['architectural_elements'][:5])
        detected_elements.extend(ai_classification.get('key_indicators', [])[:5])
        
        return DocumentClassification(
            document_type=final_type,
            confidence=combined_confidence,
            reasoning=reasoning,
            detected_elements=list(set(detected_elements)),
            page_count=0,  # Se actualizará después
            text_content="",  # Se actualizará después
            visual_elements=visual_analysis.get('architectural_elements', []),
            processing_time=0.0  # Se actualizará después
        )
    
    def classify_multiple_documents(self, file_paths: List[str]) -> List[DocumentAnalysis]:
        """
        Clasificar múltiples documentos.
        
        Args:
            file_paths: Lista de rutas de archivos
            
        Returns:
            Lista de análisis de documentos
        """
        analyses = []
        
        for file_path in file_paths:
            try:
                analysis = self.classify_document(file_path)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error clasificando {file_path}: {e}")
                # Crear análisis de error
                error_analysis = DocumentAnalysis(
                    filename=Path(file_path).name,
                    classification=DocumentClassification(
                        document_type="error",
                        confidence=0.0,
                        reasoning=f"Error en procesamiento: {str(e)}",
                        detected_elements=[],
                        page_count=0,
                        text_content="",
                        visual_elements=[],
                        processing_time=0.0
                    ),
                    extracted_data={},
                    metadata={'error': str(e)}
                )
                analyses.append(error_analysis)
        
        return analyses
