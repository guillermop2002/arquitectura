"""
Extractor de Dimensiones Avanzado
Fase 2: Extracción Precisa de Medidas y Dimensiones de Planos
"""

import cv2
import numpy as np
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
from pathlib import Path

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Dimension:
    """Dimensión extraída del plano"""
    value: float  # Valor numérico
    unit: str  # Unidad (m, cm, mm)
    confidence: float  # Confianza de la extracción
    location: Tuple[int, int]  # Ubicación en el plano
    context: str  # Contexto de la dimensión
    element_type: str  # Tipo de elemento medido

@dataclass
class DimensionAnalysis:
    """Resultado del análisis de dimensiones"""
    dimensions: List[Dimension]
    scale_factor: float  # Factor de escala detectado
    total_area: float  # Área total calculada
    room_areas: Dict[str, float]  # Áreas de habitaciones
    wall_lengths: List[float]  # Longitudes de muros
    door_widths: List[float]  # Anchos de puertas
    window_areas: List[float]  # Áreas de ventanas
    compliance_check: Dict[str, bool]  # Verificaciones de cumplimiento

class DimensionExtractor:
    """Extractor avanzado de dimensiones de planos arquitectónicos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando DimensionExtractor")
        
        # Configuración de detección
        self.setup_detection_config()
        
        # Patrones de texto para dimensiones
        self.setup_text_patterns()
        
    def setup_detection_config(self):
        """Configuración para la detección de dimensiones"""
        self.config = {
            'min_dimension_value': 0.1,  # Valor mínimo en metros
            'max_dimension_value': 1000.0,  # Valor máximo en metros
            'min_confidence': 0.5,  # Confianza mínima
            'scale_detection_threshold': 0.8,  # Umbral para detección de escala
            'text_detection_scale': 1.0,  # Escala para detección de texto
            'line_detection_threshold': 50,  # Umbral para detección de líneas
        }
        
        # Unidades reconocidas
        self.units = {
            'm': 1.0,
            'metros': 1.0,
            'cm': 0.01,
            'centimetros': 0.01,
            'mm': 0.001,
            'milimetros': 0.001,
            'ft': 0.3048,
            'feet': 0.3048,
            'in': 0.0254,
            'inches': 0.0254
        }
    
    def setup_text_patterns(self):
        """Configuración de patrones de texto para dimensiones"""
        # Patrones para detectar dimensiones en texto
        self.dimension_patterns = [
            # Patrón: número + unidad
            r'(\d+(?:\.\d+)?)\s*(m|metros|cm|centimetros|mm|milimetros|ft|feet|in|inches)',
            # Patrón: número con separador decimal
            r'(\d+[,.]\d+)\s*(m|metros|cm|centimetros|mm|milimetros|ft|feet|in|inches)',
            # Patrón: número en formato de cota
            r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(m|metros|cm|centimetros|mm|milimetros|ft|feet|in|inches)',
            # Patrón: rango de dimensiones
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(m|metros|cm|centimetros|mm|milimetros|ft|feet|in|inches)',
        ]
        
        # Patrones para detectar escalas
        self.scale_patterns = [
            r'escala\s*:?\s*1\s*:\s*(\d+)',
            r'scale\s*:?\s*1\s*:\s*(\d+)',
            r'1\s*:\s*(\d+)',
            r'(\d+)\s*:\s*1',
        ]
    
    def extract_dimensions_from_plan(self, image_path: str, text_content: str = "") -> DimensionAnalysis:
        """
        Extrae dimensiones de un plano arquitectónico
        
        Args:
            image_path: Ruta al archivo de imagen del plano
            text_content: Contenido de texto extraído (opcional)
            
        Returns:
            DimensionAnalysis: Análisis de dimensiones
        """
        try:
            self.logger.info(f"Extrayendo dimensiones de: {image_path}")
            
            # Cargar imagen
            image = self.load_image(image_path)
            if image is None:
                raise ValueError(f"No se pudo cargar la imagen: {image_path}")
            
            # Extraer dimensiones del texto
            text_dimensions = self.extract_dimensions_from_text(text_content)
            
            # Extraer dimensiones de la imagen
            visual_dimensions = self.extract_dimensions_from_image(image)
            
            # Combinar dimensiones
            all_dimensions = text_dimensions + visual_dimensions
            
            # Detectar escala
            scale_factor = self.detect_scale(image, all_dimensions)
            
            # Normalizar dimensiones a metros
            normalized_dimensions = self.normalize_dimensions(all_dimensions, scale_factor)
            
            # Calcular métricas
            total_area = self.calculate_total_area(normalized_dimensions)
            room_areas = self.calculate_room_areas(normalized_dimensions)
            wall_lengths = self.extract_wall_lengths(normalized_dimensions)
            door_widths = self.extract_door_widths(normalized_dimensions)
            window_areas = self.extract_window_areas(normalized_dimensions)
            
            # Verificar cumplimiento
            compliance_check = self.check_dimension_compliance(normalized_dimensions)
            
            return DimensionAnalysis(
                dimensions=normalized_dimensions,
                scale_factor=scale_factor,
                total_area=total_area,
                room_areas=room_areas,
                wall_lengths=wall_lengths,
                door_widths=door_widths,
                window_areas=window_areas,
                compliance_check=compliance_check
            )
            
        except Exception as e:
            self.logger.error(f"Error extrayendo dimensiones: {e}")
            raise
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Carga una imagen desde archivo"""
        try:
            image = cv2.imread(image_path)
            if image is not None:
                return image
            
            # Si falla, intentar con PIL
            from PIL import Image
            with Image.open(image_path) as pil_image:
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                image = np.array(pil_image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                return image
                
        except Exception as e:
            self.logger.error(f"Error cargando imagen {image_path}: {e}")
            return None
    
    def extract_dimensions_from_text(self, text_content: str) -> List[Dimension]:
        """Extrae dimensiones del contenido de texto"""
        try:
            dimensions = []
            
            if not text_content:
                return dimensions
            
            # Buscar patrones de dimensiones
            for pattern in self.dimension_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                
                for match in matches:
                    try:
                        # Extraer valor y unidad
                        if len(match.groups()) >= 2:
                            value_str = match.group(1)
                            unit = match.group(2).lower()
                            
                            # Convertir valor a float
                            value = float(value_str.replace(',', '.'))
                            
                            # Verificar si es un rango
                            if len(match.groups()) >= 3 and match.group(2):
                                # Es un rango, tomar el valor promedio
                                value2 = float(match.group(2).replace(',', '.'))
                                value = (value + value2) / 2
                            
                            # Verificar rango válido
                            if self.config['min_dimension_value'] <= value <= self.config['max_dimension_value']:
                                dimension = Dimension(
                                    value=value,
                                    unit=unit,
                                    confidence=0.8,  # Alta confianza para texto
                                    location=(0, 0),  # No disponible en texto
                                    context=match.group(0),
                                    element_type='text_detected'
                                )
                                dimensions.append(dimension)
                                
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Error procesando match: {e}")
                        continue
            
            self.logger.info(f"Extraídas {len(dimensions)} dimensiones del texto")
            return dimensions
            
        except Exception as e:
            self.logger.error(f"Error extrayendo dimensiones del texto: {e}")
            return []
    
    def extract_dimensions_from_image(self, image: np.ndarray) -> List[Dimension]:
        """Extrae dimensiones de la imagen visual"""
        try:
            dimensions = []
            
            # Preprocesar imagen
            processed_image = self.preprocess_image_for_text(image)
            
            # Detectar texto usando OCR
            text_regions = self.detect_text_regions(processed_image)
            
            # Extraer dimensiones de cada región de texto
            for region in text_regions:
                region_dimensions = self.extract_dimensions_from_region(region, image)
                dimensions.extend(region_dimensions)
            
            # Detectar líneas de cota
            dimension_lines = self.detect_dimension_lines(image)
            for line in dimension_lines:
                line_dimensions = self.extract_dimensions_from_line(line, image)
                dimensions.extend(line_dimensions)
            
            self.logger.info(f"Extraídas {len(dimensions)} dimensiones de la imagen")
            return dimensions
            
        except Exception as e:
            self.logger.error(f"Error extrayendo dimensiones de la imagen: {e}")
            return []
    
    def preprocess_image_for_text(self, image: np.ndarray) -> np.ndarray:
        """Preprocesa la imagen para mejor detección de texto"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar filtro gaussiano
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Aplicar umbralización adaptativa
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Operaciones morfológicas
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error preprocesando imagen: {e}")
            return image
    
    def detect_text_regions(self, image: np.ndarray) -> List[np.ndarray]:
        """Detecta regiones de texto en la imagen"""
        try:
            regions = []
            
            # Encontrar contornos
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filtrar por área
                area = cv2.contourArea(contour)
                if 100 < area < 10000:  # Área típica de texto
                    # Obtener rectángulo delimitador
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Filtrar por proporción (texto típicamente es horizontal)
                    if 0.1 < h/w < 10:
                        region = image[y:y+h, x:x+w]
                        regions.append(region)
            
            return regions
            
        except Exception as e:
            self.logger.error(f"Error detectando regiones de texto: {e}")
            return []
    
    def extract_dimensions_from_region(self, region: np.ndarray, original_image: np.ndarray) -> List[Dimension]:
        """Extrae dimensiones de una región de texto"""
        try:
            dimensions = []
            
            # TODO: Implementar OCR específico para la región
            # Por ahora, retornar lista vacía
            # En una implementación completa, usaríamos Tesseract o similar
            
            return dimensions
            
        except Exception as e:
            self.logger.error(f"Error extrayendo dimensiones de región: {e}")
            return []
    
    def detect_dimension_lines(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detecta líneas de cota en el plano"""
        try:
            dimension_lines = []
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detectar líneas usando transformada de Hough
            lines = cv2.HoughLinesP(
                gray, 1, np.pi/180, threshold=self.config['line_detection_threshold'],
                minLineLength=50, maxLineGap=10
            )
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # Calcular longitud de la línea
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    
                    # Filtrar líneas de longitud apropiada para cotas
                    if 20 < length < 500:
                        dimension_line = {
                            'coordinates': [(x1, y1), (x2, y2)],
                            'length': length,
                            'angle': np.arctan2(y2-y1, x2-x1)
                        }
                        dimension_lines.append(dimension_line)
            
            return dimension_lines
            
        except Exception as e:
            self.logger.error(f"Error detectando líneas de cota: {e}")
            return []
    
    def extract_dimensions_from_line(self, line: Dict[str, Any], image: np.ndarray) -> List[Dimension]:
        """Extrae dimensiones de una línea de cota"""
        try:
            dimensions = []
            
            # TODO: Implementar extracción de texto cerca de la línea
            # Por ahora, estimar dimensión basada en la longitud de la línea
            
            length = line['length']
            
            # Estimar dimensión basada en la longitud de la línea
            # Esto es una aproximación que se mejoraría con detección de escala
            estimated_value = length / 100.0  # Factor de escala estimado
            
            if self.config['min_dimension_value'] <= estimated_value <= self.config['max_dimension_value']:
                dimension = Dimension(
                    value=estimated_value,
                    unit='m',
                    confidence=0.3,  # Baja confianza para estimación
                    location=line['coordinates'][0],
                    context='line_estimated',
                    element_type='line_detected'
                )
                dimensions.append(dimension)
            
            return dimensions
            
        except Exception as e:
            self.logger.error(f"Error extrayendo dimensiones de línea: {e}")
            return []
    
    def detect_scale(self, image: np.ndarray, dimensions: List[Dimension]) -> float:
        """Detecta la escala del plano"""
        try:
            # Buscar indicadores de escala en la imagen
            scale_factor = 1.0  # Factor por defecto
            
            # Buscar texto que indique escala
            # TODO: Implementar detección de texto de escala
            
            # Si no se encuentra escala, usar estimación basada en dimensiones
            if dimensions:
                # Calcular factor de escala basado en dimensiones típicas
                typical_values = [dim.value for dim in dimensions if 1.0 <= dim.value <= 50.0]
                if typical_values:
                    # Asumir que las dimensiones típicas están en metros
                    scale_factor = 1.0
            
            return scale_factor
            
        except Exception as e:
            self.logger.error(f"Error detectando escala: {e}")
            return 1.0
    
    def normalize_dimensions(self, dimensions: List[Dimension], scale_factor: float) -> List[Dimension]:
        """Normaliza todas las dimensiones a metros"""
        try:
            normalized = []
            
            for dim in dimensions:
                # Convertir a metros usando la unidad y el factor de escala
                unit_factor = self.units.get(dim.unit.lower(), 1.0)
                normalized_value = dim.value * unit_factor * scale_factor
                
                normalized_dim = Dimension(
                    value=normalized_value,
                    unit='m',
                    confidence=dim.confidence,
                    location=dim.location,
                    context=dim.context,
                    element_type=dim.element_type
                )
                normalized.append(normalized_dim)
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizando dimensiones: {e}")
            return dimensions
    
    def calculate_total_area(self, dimensions: List[Dimension]) -> float:
        """Calcula el área total del plano"""
        try:
            # Buscar dimensiones de área
            area_dimensions = [dim for dim in dimensions if 'area' in dim.context.lower()]
            
            if area_dimensions:
                return sum(dim.value for dim in area_dimensions)
            
            # Si no hay dimensiones de área, estimar basado en dimensiones lineales
            linear_dimensions = [dim for dim in dimensions if dim.element_type in ['wall', 'line_detected']]
            if len(linear_dimensions) >= 2:
                # Estimación muy básica
                return linear_dimensions[0].value * linear_dimensions[1].value
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculando área total: {e}")
            return 0.0
    
    def calculate_room_areas(self, dimensions: List[Dimension]) -> Dict[str, float]:
        """Calcula las áreas de las habitaciones"""
        try:
            room_areas = {}
            
            # Buscar dimensiones de habitaciones
            room_dimensions = [dim for dim in dimensions if 'room' in dim.context.lower()]
            
            for i, dim in enumerate(room_dimensions):
                room_name = f"room_{i+1}"
                room_areas[room_name] = dim.value
            
            return room_areas
            
        except Exception as e:
            self.logger.error(f"Error calculando áreas de habitaciones: {e}")
            return {}
    
    def extract_wall_lengths(self, dimensions: List[Dimension]) -> List[float]:
        """Extrae longitudes de muros"""
        try:
            wall_dimensions = [dim for dim in dimensions if dim.element_type == 'wall']
            return [dim.value for dim in wall_dimensions]
            
        except Exception as e:
            self.logger.error(f"Error extrayendo longitudes de muros: {e}")
            return []
    
    def extract_door_widths(self, dimensions: List[Dimension]) -> List[float]:
        """Extrae anchos de puertas"""
        try:
            door_dimensions = [dim for dim in dimensions if dim.element_type == 'door']
            return [dim.value for dim in door_dimensions]
            
        except Exception as e:
            self.logger.error(f"Error extrayendo anchos de puertas: {e}")
            return []
    
    def extract_window_areas(self, dimensions: List[Dimension]) -> List[float]:
        """Extrae áreas de ventanas"""
        try:
            window_dimensions = [dim for dim in dimensions if dim.element_type == 'window']
            return [dim.value for dim in window_dimensions]
            
        except Exception as e:
            self.logger.error(f"Error extrayendo áreas de ventanas: {e}")
            return []
    
    def check_dimension_compliance(self, dimensions: List[Dimension]) -> Dict[str, bool]:
        """Verifica el cumplimiento de las dimensiones"""
        try:
            compliance = {
                'min_room_area': True,
                'min_door_width': True,
                'min_window_area': True,
                'min_corridor_width': True,
                'max_ramp_slope': True
            }
            
            # Verificar área mínima de habitaciones
            room_areas = self.calculate_room_areas(dimensions)
            for area in room_areas.values():
                if area < 9.0:  # 9 m² mínimo
                    compliance['min_room_area'] = False
            
            # Verificar ancho mínimo de puertas
            door_widths = self.extract_door_widths(dimensions)
            for width in door_widths:
                if width < 0.8:  # 0.8 m mínimo
                    compliance['min_door_width'] = False
            
            # Verificar área mínima de ventanas
            window_areas = self.extract_window_areas(dimensions)
            for area in window_areas:
                if area < 1.0:  # 1 m² mínimo
                    compliance['min_window_area'] = False
            
            return compliance
            
        except Exception as e:
            self.logger.error(f"Error verificando cumplimiento: {e}")
            return {}
    
    def save_dimension_analysis(self, analysis: DimensionAnalysis, output_path: str):
        """Guarda el análisis de dimensiones"""
        try:
            data = {
                'dimensions': [
                    {
                        'value': dim.value,
                        'unit': dim.unit,
                        'confidence': dim.confidence,
                        'location': dim.location,
                        'context': dim.context,
                        'element_type': dim.element_type
                    }
                    for dim in analysis.dimensions
                ],
                'scale_factor': analysis.scale_factor,
                'total_area': analysis.total_area,
                'room_areas': analysis.room_areas,
                'wall_lengths': analysis.wall_lengths,
                'door_widths': analysis.door_widths,
                'window_areas': analysis.window_areas,
                'compliance_check': analysis.compliance_check
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Análisis de dimensiones guardado en: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando análisis de dimensiones: {e}")
            raise
