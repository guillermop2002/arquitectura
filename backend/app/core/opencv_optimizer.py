"""
Optimizaciones específicas para OpenCV en el sistema de verificación arquitectónica.
Optimizado para detección eficiente de elementos arquitectónicos.
"""

import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class DetectionConfig:
    """Configuración para detección de elementos arquitectónicos."""
    # Parámetros de preprocesado
    gaussian_kernel_size: int = 5
    canny_low_threshold: int = 50
    canny_high_threshold: int = 150
    
    # Parámetros de contornos
    min_contour_area: int = 100
    max_contour_area: int = 50000
    
    # Parámetros específicos por elemento
    door_width_range: Tuple[int, int] = (60, 120)
    door_height_range: Tuple[int, int] = (10, 50)
    window_width_range: Tuple[int, int] = (40, 200)
    window_height_range: Tuple[int, int] = (10, 30)
    
    # Parámetros de morfología
    morph_kernel_size: int = 3
    morph_iterations: int = 2

class OpenCVOptimizer:
    """Optimizador para detección de elementos arquitectónicos con OpenCV."""
    
    def __init__(self, config: Optional[DetectionConfig] = None):
        """Inicializar el optimizador con configuración."""
        self.config = config or DetectionConfig()
        self.logger = logging.getLogger(__name__)
        
        # Crear kernels de morfología
        self.morph_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, 
            (self.config.morph_kernel_size, self.config.morph_kernel_size)
        )
        
        self.logger.info("OpenCV Optimizer initialized")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocesar imagen para detección optimizada."""
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Aplicar filtro gaussiano
            blurred = cv2.GaussianBlur(
                gray, 
                (self.config.gaussian_kernel_size, self.config.gaussian_kernel_size), 
                0
            )
            
            # Detección de bordes con Canny
            edges = cv2.Canny(
                blurred, 
                self.config.canny_low_threshold, 
                self.config.canny_high_threshold
            )
            
            # Operaciones morfológicas para limpiar
            cleaned = cv2.morphologyEx(
                edges, 
                cv2.MORPH_CLOSE, 
                self.morph_kernel, 
                iterations=self.config.morph_iterations
            )
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            return image
    
    def detect_architectural_elements(self, image: np.ndarray) -> List[Dict]:
        """Detectar elementos arquitectónicos de forma optimizada."""
        try:
            # Preprocesar imagen
            processed = self.preprocess_image(image)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(
                processed, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            elements = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filtrar por área
                if not (self.config.min_contour_area < area < self.config.max_contour_area):
                    continue
                
                # Obtener rectángulo delimitador
                x, y, w, h = cv2.boundingRect(contour)
                
                # Clasificar elemento
                element_type = self._classify_element(w, h, area)
                
                if element_type:
                    element = {
                        'type': element_type,
                        'coordinates': [(x, y), (x + w, y + h)],
                        'dimensions': {'width': w, 'height': h, 'area': area},
                        'confidence': self._calculate_confidence(w, h, area, element_type),
                        'contour': contour.tolist()
                    }
                    elements.append(element)
            
            self.logger.info(f"Detected {len(elements)} architectural elements")
            return elements
            
        except Exception as e:
            self.logger.error(f"Error detecting architectural elements: {e}")
            return []
    
    def _classify_element(self, width: int, height: int, area: float) -> Optional[str]:
        """Clasificar elemento basado en dimensiones."""
        aspect_ratio = width / height if height > 0 else 0
        
        # Detección de puertas
        if (self.config.door_width_range[0] <= width <= self.config.door_width_range[1] and
            self.config.door_height_range[0] <= height <= self.config.door_height_range[1]):
            return 'door'
        
        # Detección de ventanas
        if (self.config.window_width_range[0] <= width <= self.config.window_width_range[1] and
            self.config.window_height_range[0] <= height <= self.config.window_height_range[1]):
            return 'window'
        
        # Detección de muros
        if width > 100 and height > 20 and aspect_ratio > 3:
            return 'wall'
        
        # Detección de columnas
        if 20 <= width <= 60 and 20 <= height <= 60 and 0.5 <= aspect_ratio <= 2:
            return 'column'
        
        # Detección de escaleras
        if 50 <= width <= 200 and 100 <= height <= 300 and 0.3 <= aspect_ratio <= 0.8:
            return 'stair'
        
        return None
    
    def _calculate_confidence(self, width: int, height: int, area: float, element_type: str) -> float:
        """Calcular confianza en la detección."""
        base_confidence = 0.7
        
        # Ajustar confianza basado en el tipo de elemento
        if element_type == 'door':
            if self.config.door_width_range[0] <= width <= self.config.door_width_range[1]:
                base_confidence += 0.2
        elif element_type == 'window':
            if self.config.window_width_range[0] <= width <= self.config.window_width_range[1]:
                base_confidence += 0.2
        elif element_type == 'wall':
            if width > 100 and height > 20:
                base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def detect_rooms(self, image: np.ndarray) -> List[Dict]:
        """Detectar habitaciones de forma optimizada."""
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Umbralización adaptativa
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Encontrar contornos de habitaciones
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            rooms = []
            room_id = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filtrar por área mínima de habitación
                if area < 1000:
                    continue
                
                # Obtener rectángulo delimitador
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calcular centro
                center = (x + w/2, y + h/2)
                
                room = {
                    'room_id': f"room_{room_id}",
                    'room_type': 'unknown',  # Será clasificado por IA
                    'area': area,
                    'center': center,
                    'boundaries': [(x, y), (x + w, y + h)],
                    'doors': [],
                    'windows': []
                }
                rooms.append(room)
                room_id += 1
            
            self.logger.info(f"Detected {len(rooms)} rooms")
            return rooms
            
        except Exception as e:
            self.logger.error(f"Error detecting rooms: {e}")
            return []
    
    def extract_dimensions(self, image: np.ndarray) -> List[Dict]:
        """Extraer dimensiones y cotas de la imagen."""
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Detectar líneas (para cotas)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
            
            dimensions = []
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # Calcular longitud
                    length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    
                    # Filtrar líneas muy cortas o muy largas
                    if 20 < length < 500:
                        dimension = {
                            'type': 'line',
                            'start': (x1, y1),
                            'end': (x2, y2),
                            'length': length,
                            'confidence': 0.8
                        }
                        dimensions.append(dimension)
            
            self.logger.info(f"Extracted {len(dimensions)} dimensions")
            return dimensions
            
        except Exception as e:
            self.logger.error(f"Error extracting dimensions: {e}")
            return []
    
    def optimize_for_arm64(self) -> Dict:
        """Optimizaciones específicas para arquitectura ARM64."""
        optimizations = {
            'threading': {
                'max_threads': 4,  # ARM64 típicamente tiene 4-8 cores
                'use_parallel': True
            },
            'memory': {
                'max_image_size': (2048, 2048),  # Reducir tamaño para ARM64
                'use_float32': True  # Más eficiente en ARM64
            },
            'processing': {
                'batch_size': 4,
                'use_gpu': False  # OpenCV en ARM64 generalmente sin GPU
            }
        }
        
        # Aplicar optimizaciones
        cv2.setNumThreads(optimizations['threading']['max_threads'])
        
        self.logger.info("ARM64 optimizations applied")
        return optimizations
    
    def get_performance_metrics(self) -> Dict:
        """Obtener métricas de rendimiento."""
        return {
            'config': {
                'gaussian_kernel_size': self.config.gaussian_kernel_size,
                'canny_thresholds': (self.config.canny_low_threshold, self.config.canny_high_threshold),
                'contour_limits': (self.config.min_contour_area, self.config.max_contour_area)
            },
            'optimizations': {
                'morph_kernel_size': self.config.morph_kernel_size,
                'morph_iterations': self.config.morph_iterations
            }
        }

# =============================================================================
# UTILIDADES DE OPTIMIZACIÓN
# =============================================================================

def create_optimized_config(architecture: str = "x64") -> DetectionConfig:
    """Crear configuración optimizada para la arquitectura especificada."""
    config = DetectionConfig()
    
    if architecture == "arm64":
        # Optimizaciones para ARM64
        config.gaussian_kernel_size = 3  # Kernel más pequeño
        config.canny_low_threshold = 30  # Umbrales más bajos
        config.canny_high_threshold = 100
        config.min_contour_area = 50  # Área mínima más pequeña
        config.max_contour_area = 30000  # Área máxima más pequeña
        config.morph_kernel_size = 2  # Kernel morfológico más pequeño
        config.morph_iterations = 1  # Menos iteraciones
    
    return config

def benchmark_detection(image_path: str, config: DetectionConfig) -> Dict:
    """Hacer benchmark de la detección con la configuración dada."""
    import time
    
    # Cargar imagen
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "Could not load image"}
    
    # Crear optimizador
    optimizer = OpenCVOptimizer(config)
    
    # Medir tiempo de detección
    start_time = time.time()
    elements = optimizer.detect_architectural_elements(image)
    rooms = optimizer.detect_rooms(image)
    dimensions = optimizer.extract_dimensions(image)
    end_time = time.time()
    
    return {
        "processing_time": end_time - start_time,
        "elements_detected": len(elements),
        "rooms_detected": len(rooms),
        "dimensions_extracted": len(dimensions),
        "config_used": config.__dict__
    }
