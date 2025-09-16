"""
Módulo de Visión por Computador para Análisis de Planos Arquitectónicos
Fase 2: Análisis Avanzado de Planos con IA
"""

import cv2
import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import base64
from PIL import Image
import io

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ArchitecturalElement:
    """Elemento arquitectónico detectado en el plano"""
    element_type: str  # 'wall', 'door', 'window', 'stair', 'ramp', 'elevator', 'room'
    coordinates: List[Tuple[int, int]]  # Coordenadas del polígono
    dimensions: Dict[str, float]  # Dimensiones detectadas
    confidence: float  # Confianza de la detección
    properties: Dict[str, Any]  # Propiedades adicionales

@dataclass
class PlanAnalysis:
    """Resultado del análisis de un plano"""
    elements: List[ArchitecturalElement]
    dimensions: Dict[str, float]  # Dimensiones generales del plano
    scale: float  # Escala detectada
    orientation: str  # Orientación del plano
    room_areas: Dict[str, float]  # Áreas de habitaciones
    accessibility_features: List[str]  # Características de accesibilidad
    compliance_issues: List[str]  # Problemas de cumplimiento detectados

class ComputerVisionAnalyzer:
    """Analizador de visión por computador para planos arquitectónicos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando ComputerVisionAnalyzer")
        
        # Configuración de OpenCV
        self.setup_opencv()
        
        # Modelos pre-entrenados (se cargarán bajo demanda)
        self.models = {}
        
    def setup_opencv(self):
        """Configuración inicial de OpenCV"""
        try:
            # Configurar parámetros de detección
            self.detection_params = {
                'min_contour_area': 100,
                'max_contour_area': 50000,
                'line_threshold': 50,
                'corner_threshold': 0.01
            }
            self.logger.info("OpenCV configurado correctamente")
        except Exception as e:
            self.logger.error(f"Error configurando OpenCV: {e}")
            raise
    
    def analyze_plan(self, image_path: str) -> PlanAnalysis:
        """
        Analiza un plano arquitectónico completo
        
        Args:
            image_path: Ruta al archivo de imagen del plano
            
        Returns:
            PlanAnalysis: Resultado del análisis
        """
        try:
            self.logger.info(f"Analizando plano: {image_path}")
            
            # Cargar imagen
            image = self.load_image(image_path)
            if image is None:
                raise ValueError(f"No se pudo cargar la imagen: {image_path}")
            
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)
            
            # Detectar elementos arquitectónicos
            elements = self.detect_architectural_elements(processed_image)
            
            # Extraer dimensiones
            dimensions = self.extract_dimensions(processed_image, elements)
            
            # Detectar escala
            scale = self.detect_scale(processed_image, elements)
            
            # Detectar orientación
            orientation = self.detect_orientation(processed_image)
            
            # Calcular áreas de habitaciones
            room_areas = self.calculate_room_areas(elements)
            
            # Detectar características de accesibilidad
            accessibility_features = self.detect_accessibility_features(elements)
            
            # Detectar problemas de cumplimiento
            compliance_issues = self.detect_compliance_issues(elements, dimensions)
            
            return PlanAnalysis(
                elements=elements,
                dimensions=dimensions,
                scale=scale,
                orientation=orientation,
                room_areas=room_areas,
                accessibility_features=accessibility_features,
                compliance_issues=compliance_issues
            )
            
        except Exception as e:
            self.logger.error(f"Error analizando plano: {e}")
            raise
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Carga una imagen desde archivo"""
        try:
            # Intentar cargar como imagen normal
            image = cv2.imread(image_path)
            if image is not None:
                return image
            
            # Si falla, intentar con PIL y convertir
            with Image.open(image_path) as pil_image:
                # Convertir a RGB si es necesario
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Convertir a numpy array
                image = np.array(pil_image)
                # Convertir de RGB a BGR para OpenCV
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                return image
                
        except Exception as e:
            self.logger.error(f"Error cargando imagen {image_path}: {e}")
            return None
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocesa la imagen para mejor detección"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar filtro gaussiano para reducir ruido
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Aplicar umbralización adaptativa
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Operaciones morfológicas para limpiar la imagen
            kernel = np.ones((3, 3), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error preprocesando imagen: {e}")
            return image
    
    def detect_architectural_elements(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta elementos arquitectónicos en el plano"""
        try:
            elements = []
            
            # Detectar muros
            walls = self.detect_walls(image)
            elements.extend(walls)
            
            # Detectar puertas
            doors = self.detect_doors(image)
            elements.extend(doors)
            
            # Detectar ventanas
            windows = self.detect_windows(image)
            elements.extend(windows)
            
            # Detectar escaleras
            stairs = self.detect_stairs(image)
            elements.extend(stairs)
            
            # Detectar rampas
            ramps = self.detect_ramps(image)
            elements.extend(ramps)
            
            # Detectar ascensores
            elevators = self.detect_elevators(image)
            elements.extend(elevators)
            
            # Detectar habitaciones
            rooms = self.detect_rooms(image)
            elements.extend(rooms)
            
            self.logger.info(f"Detectados {len(elements)} elementos arquitectónicos")
            return elements
            
        except Exception as e:
            self.logger.error(f"Error detectando elementos: {e}")
            return []
    
    def detect_walls(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta muros en el plano"""
        try:
            walls = []
            
            # Detectar líneas usando transformada de Hough
            lines = cv2.HoughLinesP(
                image, 1, np.pi/180, threshold=100,
                minLineLength=50, maxLineGap=10
            )
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # Calcular longitud de la línea
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    
                    if length > 100:  # Solo líneas suficientemente largas
                        wall = ArchitecturalElement(
                            element_type='wall',
                            coordinates=[(x1, y1), (x2, y2)],
                            dimensions={'length': length},
                            confidence=0.8,
                            properties={'thickness': 0.2}  # Grosor estimado
                        )
                        walls.append(wall)
            
            return walls
            
        except Exception as e:
            self.logger.error(f"Error detectando muros: {e}")
            return []
    
    def detect_doors(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta puertas en el plano"""
        try:
            doors = []
            
            # Detectar arcos (puertas típicamente tienen forma de arco)
            circles = cv2.HoughCircles(
                image, cv2.HOUGH_GRADIENT, 1, 20,
                param1=50, param2=30, minRadius=10, maxRadius=50
            )
            
            if circles is not None:
                circles = np.uint16(np.around(circles))
                for circle in circles[0, :]:
                    x, y, r = circle
                    
                    door = ArchitecturalElement(
                        element_type='door',
                        coordinates=[(x-r, y-r), (x+r, y+r)],
                        dimensions={'width': r*2, 'height': r*2},
                        confidence=0.7,
                        properties={'type': 'swing'}
                    )
                    doors.append(door)
            
            return doors
            
        except Exception as e:
            self.logger.error(f"Error detectando puertas: {e}")
            return []
    
    def detect_windows(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta ventanas en el plano"""
        try:
            windows = []
            
            # Detectar rectángulos (ventanas típicamente son rectangulares)
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Aproximar contorno a polígono
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Si es aproximadamente rectangular
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    
                    # Filtrar por tamaño (ventanas típicas)
                    if 20 < w < 200 and 20 < h < 200:
                        window = ArchitecturalElement(
                            element_type='window',
                            coordinates=[(x, y), (x+w, y+h)],
                            dimensions={'width': w, 'height': h},
                            confidence=0.6,
                            properties={'type': 'standard'}
                        )
                        windows.append(window)
            
            return windows
            
        except Exception as e:
            self.logger.error(f"Error detectando ventanas: {e}")
            return []
    
    def detect_stairs(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta escaleras en el plano"""
        try:
            stairs = []
            
            # Detectar patrones de escalera (líneas paralelas)
            lines = cv2.HoughLinesP(
                image, 1, np.pi/180, threshold=50,
                minLineLength=30, maxLineGap=5
            )
            
            if lines is not None:
                # Agrupar líneas paralelas cercanas
                parallel_groups = self.group_parallel_lines(lines)
                
                for group in parallel_groups:
                    if len(group) >= 3:  # Al menos 3 escalones
                        # Calcular dimensiones del grupo
                        x_coords = []
                        y_coords = []
                        for line in group:
                            x1, y1, x2, y2 = line[0]
                            x_coords.extend([x1, x2])
                            y_coords.extend([y1, y2])
                        
                        min_x, max_x = min(x_coords), max(x_coords)
                        min_y, max_y = min(y_coords), max(y_coords)
                        
                        stair = ArchitecturalElement(
                            element_type='stair',
                            coordinates=[(min_x, min_y), (max_x, max_y)],
                            dimensions={'width': max_x-min_x, 'height': max_y-min_y},
                            confidence=0.7,
                            properties={'steps': len(group)}
                        )
                        stairs.append(stair)
            
            return stairs
            
        except Exception as e:
            self.logger.error(f"Error detectando escaleras: {e}")
            return []
    
    def detect_ramps(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta rampas en el plano"""
        try:
            ramps = []
            
            # Detectar líneas diagonales (rampas típicamente son diagonales)
            lines = cv2.HoughLinesP(
                image, 1, np.pi/180, threshold=50,
                minLineLength=100, maxLineGap=10
            )
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # Calcular ángulo de la línea
                    angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi
                    
                    # Rampas típicamente tienen ángulo entre 5 y 15 grados
                    if 5 < abs(angle) < 15:
                        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                        
                        ramp = ArchitecturalElement(
                            element_type='ramp',
                            coordinates=[(x1, y1), (x2, y2)],
                            dimensions={'length': length, 'angle': angle},
                            confidence=0.6,
                            properties={'slope': abs(angle)}
                        )
                        ramps.append(ramp)
            
            return ramps
            
        except Exception as e:
            self.logger.error(f"Error detectando rampas: {e}")
            return []
    
    def detect_elevators(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta ascensores en el plano"""
        try:
            elevators = []
            
            # Detectar rectángulos grandes (ascensores típicamente son rectángulos grandes)
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                # Filtrar por tamaño y proporción (ascensores típicos)
                if (area > 1000 and 
                    0.8 < w/h < 1.2 and  # Aproximadamente cuadrados
                    50 < w < 200 and 50 < h < 200):
                    
                    elevator = ArchitecturalElement(
                        element_type='elevator',
                        coordinates=[(x, y), (x+w, y+h)],
                        dimensions={'width': w, 'height': h},
                        confidence=0.5,
                        properties={'type': 'passenger'}
                    )
                    elevators.append(elevator)
            
            return elevators
            
        except Exception as e:
            self.logger.error(f"Error detectando ascensores: {e}")
            return []
    
    def detect_rooms(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """Detecta habitaciones en el plano"""
        try:
            rooms = []
            
            # Detectar contornos cerrados (habitaciones)
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filtrar por área mínima (habitaciones típicas)
                if area > 5000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calcular perímetro
                    perimeter = cv2.arcLength(contour, True)
                    
                    room = ArchitecturalElement(
                        element_type='room',
                        coordinates=self.contour_to_coordinates(contour),
                        dimensions={'width': w, 'height': h, 'area': area},
                        confidence=0.6,
                        properties={'perimeter': perimeter}
                    )
                    rooms.append(room)
            
            return rooms
            
        except Exception as e:
            self.logger.error(f"Error detectando habitaciones: {e}")
            return []
    
    def group_parallel_lines(self, lines: np.ndarray) -> List[List[np.ndarray]]:
        """Agrupa líneas paralelas cercanas"""
        try:
            groups = []
            used_lines = set()
            
            for i, line1 in enumerate(lines):
                if i in used_lines:
                    continue
                
                group = [line1]
                used_lines.add(i)
                
                x1, y1, x2, y2 = line1[0]
                angle1 = np.arctan2(y2-y1, x2-x1)
                
                for j, line2 in enumerate(lines[i+1:], i+1):
                    if j in used_lines:
                        continue
                    
                    x3, y3, x4, y4 = line2[0]
                    angle2 = np.arctan2(y4-y3, x4-x3)
                    
                    # Verificar si son paralelas (ángulo similar)
                    angle_diff = abs(angle1 - angle2)
                    if angle_diff < np.pi/18:  # 10 grados
                        # Verificar si están cerca
                        dist1 = np.sqrt((x1-x3)**2 + (y1-y3)**2)
                        dist2 = np.sqrt((x2-x4)**2 + (y2-y4)**2)
                        
                        if min(dist1, dist2) < 50:  # Distancia máxima
                            group.append(line2)
                            used_lines.add(j)
                
                if len(group) >= 2:
                    groups.append(group)
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Error agrupando líneas paralelas: {e}")
            return []
    
    def contour_to_coordinates(self, contour: np.ndarray) -> List[Tuple[int, int]]:
        """Convierte contorno a lista de coordenadas"""
        try:
            coordinates = []
            for point in contour:
                x, y = point[0]
                coordinates.append((int(x), int(y)))
            return coordinates
        except Exception as e:
            self.logger.error(f"Error convirtiendo contorno: {e}")
            return []
    
    def extract_dimensions(self, image: np.ndarray, elements: List[ArchitecturalElement]) -> Dict[str, float]:
        """Extrae dimensiones generales del plano"""
        try:
            dimensions = {}
            
            # Obtener dimensiones de la imagen
            height, width = image.shape[:2]
            dimensions['image_width'] = width
            dimensions['image_height'] = height
            
            # Calcular dimensiones de elementos
            if elements:
                total_area = sum(elem.dimensions.get('area', 0) for elem in elements if elem.element_type == 'room')
                dimensions['total_room_area'] = total_area
                
                # Calcular dimensiones promedio
                wall_lengths = [elem.dimensions.get('length', 0) for elem in elements if elem.element_type == 'wall']
                if wall_lengths:
                    dimensions['avg_wall_length'] = np.mean(wall_lengths)
                    dimensions['max_wall_length'] = max(wall_lengths)
            
            return dimensions
            
        except Exception as e:
            self.logger.error(f"Error extrayendo dimensiones: {e}")
            return {}
    
    def detect_scale(self, image: np.ndarray, elements: List[ArchitecturalElement]) -> float:
        """Detecta la escala del plano"""
        try:
            # Buscar indicadores de escala en la imagen
            # Por ahora, usar una escala por defecto basada en el tamaño de la imagen
            height, width = image.shape[:2]
            
            # Escala estimada basada en el tamaño de la imagen
            # Asumiendo que un plano típico es de 1:100
            scale = 100.0  # Escala por defecto
            
            # Buscar texto que indique escala
            # TODO: Implementar OCR para detectar texto de escala
            
            return scale
            
        except Exception as e:
            self.logger.error(f"Error detectando escala: {e}")
            return 100.0
    
    def detect_orientation(self, image: np.ndarray) -> str:
        """Detecta la orientación del plano"""
        try:
            # Analizar la orientación de las líneas principales
            lines = cv2.HoughLinesP(
                image, 1, np.pi/180, threshold=100,
                minLineLength=100, maxLineGap=10
            )
            
            if lines is not None:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi
                    angles.append(angle)
                
                # Determinar orientación dominante
                angle_hist, _ = np.histogram(angles, bins=36, range=(-180, 180))
                dominant_angle = np.argmax(angle_hist) * 10 - 180
                
                if -45 < dominant_angle < 45:
                    return "horizontal"
                elif 45 < dominant_angle < 135:
                    return "vertical"
                else:
                    return "diagonal"
            
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"Error detectando orientación: {e}")
            return "unknown"
    
    def calculate_room_areas(self, elements: List[ArchitecturalElement]) -> Dict[str, float]:
        """Calcula las áreas de las habitaciones"""
        try:
            room_areas = {}
            
            for i, element in enumerate(elements):
                if element.element_type == 'room':
                    area = element.dimensions.get('area', 0)
                    room_name = f"room_{i+1}"
                    room_areas[room_name] = area
            
            return room_areas
            
        except Exception as e:
            self.logger.error(f"Error calculando áreas de habitaciones: {e}")
            return {}
    
    def detect_accessibility_features(self, elements: List[ArchitecturalElement]) -> List[str]:
        """Detecta características de accesibilidad"""
        try:
            features = []
            
            # Detectar rampas
            ramps = [e for e in elements if e.element_type == 'ramp']
            if ramps:
                features.append(f"Rampas detectadas: {len(ramps)}")
            
            # Detectar ascensores
            elevators = [e for e in elements if e.element_type == 'elevator']
            if elevators:
                features.append(f"Ascensores detectados: {len(elevators)}")
            
            # Detectar puertas (accesibilidad)
            doors = [e for e in elements if e.element_type == 'door']
            if doors:
                features.append(f"Puertas detectadas: {len(doors)}")
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error detectando características de accesibilidad: {e}")
            return []
    
    def detect_compliance_issues(self, elements: List[ArchitecturalElement], dimensions: Dict[str, float]) -> List[str]:
        """Detecta problemas de cumplimiento"""
        try:
            issues = []
            
            # Verificar dimensiones mínimas de habitaciones
            for element in elements:
                if element.element_type == 'room':
                    area = element.dimensions.get('area', 0)
                    if area < 9:  # Área mínima de 9 m²
                        issues.append(f"Habitación con área insuficiente: {area:.2f} m²")
            
            # Verificar presencia de ascensores en edificios altos
            elevators = [e for e in elements if e.element_type == 'elevator']
            if not elevators:
                # TODO: Verificar altura del edificio
                issues.append("No se detectaron ascensores")
            
            # Verificar accesibilidad
            ramps = [e for e in elements if e.element_type == 'ramp']
            if not ramps and not elevators:
                issues.append("No se detectaron características de accesibilidad")
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error detectando problemas de cumplimiento: {e}")
            return []
    
    def save_analysis(self, analysis: PlanAnalysis, output_path: str):
        """Guarda el análisis en un archivo JSON"""
        try:
            # Convertir a diccionario serializable
            data = {
                'elements': [
                    {
                        'element_type': elem.element_type,
                        'coordinates': elem.coordinates,
                        'dimensions': elem.dimensions,
                        'confidence': elem.confidence,
                        'properties': elem.properties
                    }
                    for elem in analysis.elements
                ],
                'dimensions': analysis.dimensions,
                'scale': analysis.scale,
                'orientation': analysis.orientation,
                'room_areas': analysis.room_areas,
                'accessibility_features': analysis.accessibility_features,
                'compliance_issues': analysis.compliance_issues
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Análisis guardado en: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando análisis: {e}")
            raise

# Función de utilidad para convertir PDF a imagen
def pdf_to_image(pdf_path: str, page_number: int = 0) -> Optional[str]:
    """Convierte una página de PDF a imagen para análisis"""
    try:
        import fitz  # PyMuPDF
        import tempfile
        import os
        
        # Abrir PDF
        doc = fitz.open(pdf_path)
        
        if page_number >= len(doc):
            page_number = 0
        
        # Obtener página
        page = doc[page_number]
        
        # Convertir a imagen
        mat = fitz.Matrix(2.0, 2.0)  # Escala 2x para mejor calidad
        pix = page.get_pixmap(matrix=mat)
        
        # Guardar imagen temporal
        temp_dir = tempfile.gettempdir()
        image_path = os.path.join(temp_dir, f"plan_page_{page_number}.png")
        pix.save(image_path)
        
        doc.close()
        return image_path
        
    except Exception as e:
        logger.error(f"Error convirtiendo PDF a imagen: {e}")
        return None
