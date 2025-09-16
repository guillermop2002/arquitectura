"""
Procesador OCR mejorado para análisis de documentos arquitectónicos.
"""

import os
import sys
import logging
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import pytesseract
from PIL import Image

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Resultado del procesamiento OCR."""
    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]]
    language: str = "spa"
    processing_time: float = 0.0

@dataclass
class TextRegion:
    """Región de texto detectada."""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    language: str = "spa"

class EnhancedOCRProcessor:
    """Procesador OCR mejorado para documentos arquitectónicos."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar el procesador OCR.
        
        Args:
            config: Configuración del procesador
        """
        self.config = config or {}
        self.languages = self.config.get('languages', ['spa', 'eng'])
        self.min_confidence = self.config.get('min_confidence', 30)
        self.preprocessing_enabled = self.config.get('preprocessing', True)
        
        # Configurar Tesseract
        self._setup_tesseract()
        
        logger.info("EnhancedOCRProcessor initialized")
    
    def _setup_tesseract(self):
        """Configurar Tesseract OCR."""
        try:
            # Configurar ruta de Tesseract si es necesario
            tesseract_path = self.config.get('tesseract_path')
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Verificar que Tesseract funciona
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR configured successfully")
        except Exception as e:
            logger.error(f"Error configuring Tesseract: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocesar imagen para mejorar la precisión del OCR.
        
        Args:
            image: Imagen de entrada
            
        Returns:
            Imagen preprocesada
        """
        if not self.preprocessing_enabled:
            return image
        
        try:
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Aplicar filtro gaussiano para reducir ruido
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Aplicar umbralización adaptativa
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Operaciones morfológicas para limpiar la imagen
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Error in image preprocessing: {e}")
            return image
    
    def extract_text_from_image(self, image: np.ndarray, language: str = "spa") -> OCRResult:
        """
        Extraer texto de una imagen usando OCR.
        
        Args:
            image: Imagen de entrada
            language: Idioma para el OCR
            
        Returns:
            Resultado del OCR
        """
        start_time = os.times().elapsed
        
        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)
            
            # Configurar parámetros de Tesseract
            config = f'--oem 3 --psm 6 -l {language}'
            
            # Extraer texto con información de bounding boxes
            data = pytesseract.image_to_data(
                processed_image, 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            # Procesar resultados
            texts = []
            confidences = []
            bounding_boxes = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                if text and confidence > self.min_confidence:
                    texts.append(text)
                    confidences.append(confidence)
                    bounding_boxes.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': (
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        )
                    })
            
            # Combinar texto
            full_text = ' '.join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0
            
            processing_time = os.times().elapsed - start_time
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                language=language,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {e}")
            processing_time = os.times().elapsed - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                bounding_boxes=[],
                language=language,
                processing_time=processing_time
            )
    
    def extract_text_from_file(self, file_path: str, language: str = "spa") -> OCRResult:
        """
        Extraer texto de un archivo de imagen.
        
        Args:
            file_path: Ruta del archivo
            language: Idioma para el OCR
            
        Returns:
            Resultado del OCR
        """
        try:
            # Cargar imagen
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError(f"No se pudo cargar la imagen: {file_path}")
            
            return self.extract_text_from_image(image, language)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                bounding_boxes=[],
                language=language,
                processing_time=0.0
            )
    
    def detect_text_regions(self, image: np.ndarray, language: str = "spa") -> List[TextRegion]:
        """
        Detectar regiones de texto en una imagen.
        
        Args:
            image: Imagen de entrada
            language: Idioma para el OCR
            
        Returns:
            Lista de regiones de texto detectadas
        """
        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)
            
            # Configurar parámetros de Tesseract
            config = f'--oem 3 --psm 6 -l {language}'
            
            # Extraer datos detallados
            data = pytesseract.image_to_data(
                processed_image, 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            regions = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                if text and confidence > self.min_confidence:
                    region = TextRegion(
                        text=text,
                        confidence=confidence,
                        bbox=(
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        ),
                        language=language
                    )
                    regions.append(region)
            
            return regions
            
        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
            return []
    
    def extract_architectural_elements(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extraer elementos arquitectónicos específicos de una imagen.
        
        Args:
            image: Imagen de entrada
            
        Returns:
            Lista de elementos arquitectónicos detectados
        """
        try:
            # Detectar regiones de texto
            text_regions = self.detect_text_regions(image)
            
            elements = []
            for region in text_regions:
                # Analizar texto para elementos arquitectónicos
                text_lower = region.text.lower()
                
                element_type = None
                if any(keyword in text_lower for keyword in ['planta', 'alzado', 'sección']):
                    element_type = 'plan'
                elif any(keyword in text_lower for keyword in ['escala', '1:', '1/']):
                    element_type = 'scale'
                elif any(keyword in text_lower for keyword in ['norte', 'sur', 'este', 'oeste']):
                    element_type = 'orientation'
                elif any(keyword in text_lower for keyword in ['cota', 'nivel', 'altura']):
                    element_type = 'dimension'
                
                if element_type:
                    elements.append({
                        'type': element_type,
                        'text': region.text,
                        'confidence': region.confidence,
                        'bbox': region.bbox
                    })
            
            return elements
            
        except Exception as e:
            logger.error(f"Error extracting architectural elements: {e}")
            return []
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del procesamiento.
        
        Returns:
            Estadísticas del procesador
        """
        return {
            'languages': self.languages,
            'min_confidence': self.min_confidence,
            'preprocessing_enabled': self.preprocessing_enabled,
            'tesseract_version': pytesseract.get_tesseract_version()
        }
