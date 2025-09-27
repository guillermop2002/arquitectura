import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import re
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from dataclasses import dataclass
import math

# Configurar logger específico
logger = logging.getLogger("basico.advanced_ocr")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@dataclass
class TextZone:
    """Zona de texto detectada"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    text: str
    confidence: float
    zone_type: str  # 'text', 'dimension', 'legend', 'scale'

@dataclass
class DimensionLine:
    """Línea de dimensión detectada"""
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    text_value: str
    computed_value_meters: Optional[float]
    confidence: float
    bbox: Tuple[int, int, int, int]

class AdvancedOCRProcessor:
    """Procesador OCR avanzado con detección de zonas y extracción mejorada"""
    
    def __init__(self):
        self.tesseract_configs = {
            'standard': '--oem 1 --psm 6 -l spa',
            'single_word': '--oem 1 --psm 8 -l spa',
            'single_line': '--oem 1 --psm 7 -l spa',
            'sparse_text': '--oem 1 --psm 11 -l spa',
            'numbers': '--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789.,xX×-'
        }
        
        # Patrones mejorados para extracción
        self.scale_patterns = [
            r'(?:escala|scale|e)[:\s]*1[:/](\d+)',
            r'1[:/](\d+)',
            r'e\s*=\s*1[:/](\d+)',
            r'(\d+)[:/]1'
        ]
        
        self.dimension_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*(?:m|metros?|mm|cm)?',
            r'(\d+(?:[.,]\d+)?)\s*(?:m|metros?|mm|cm)',
            r'(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s*(?:mm|cm)',
            r'Ø\s*(\d+(?:[.,]\d+)?)',  # Diámetros
            r'R\s*(\d+(?:[.,]\d+)?)'   # Radios
        ]
        
        self.area_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:m²|m2|metros?\s*cuadrados?)',
            r'superficie[:\s]*(\d+(?:[.,]\d+)?)\s*(?:m²|m2)',
            r'área[:\s]*(\d+(?:[.,]\d+)?)\s*(?:m²|m2)'
        ]
        
        # Cache para resultados OCR
        self.cache = {}
        
        # Configuración de paralelización
        self.max_workers = min(3, multiprocessing.cpu_count() - 1)
        
    def extract_text_from_pdf_advanced(self, pdf_path: str) -> Dict[str, Any]:
        """Extracción avanzada con detección de zonas y OCR optimizado"""
        
        logger.info(f"🚀 INICIANDO EXTRACCIÓN AVANZADA: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            # Procesar páginas en paralelo
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_page = {
                    executor.submit(self._process_page_advanced, doc, page_num): page_num 
                    for page_num in range(len(doc))
                }
                
                page_results = []
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        result = future.result()
                        result['page_number'] = page_num + 1
                        page_results.append(result)
                    except Exception as e:
                        logger.error(f"❌ Error procesando página {page_num + 1}: {str(e)}")
                        page_results.append({
                            'page_number': page_num + 1,
                            'text': '',
                            'confidence': 0.0,
                            'error': str(e)
                        })
            
            # Ordenar resultados por número de página
            page_results.sort(key=lambda x: x['page_number'])
            
            doc.close()
            
            # Consolidar resultados
            result = self._consolidate_results(page_results, pdf_path)
            
            logger.info(f"✅ EXTRACCIÓN AVANZADA COMPLETADA: {len(page_results)} páginas procesadas")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en extracción avanzada: {str(e)}")
            return {
                'full_text': '',
                'page_results': [],
                'total_pages': 0,
                'extraction_method': 'advanced_error',
                'confidence': 0.0,
                'error': str(e),
                'file_path': pdf_path
            }
    
    def _process_page_advanced(self, doc, page_num: int) -> Dict[str, Any]:
        """Procesar una página con técnicas avanzadas"""
        
        try:
            page = doc.load_page(page_num)
            
            # 1. Intentar extracción vectorial primero
            direct_text = page.get_text()
            
            if len(direct_text.strip()) > 100:
                # Texto vectorial disponible - extraer información estructurada
                logger.debug(f"📄 Página {page_num + 1}: Usando texto vectorial")
                
                # Extraer información técnica del texto vectorial
                technical_info = self._extract_technical_info_from_text(direct_text)
                
                return {
                    'text': direct_text,
                    'extraction_method': 'vectorial',
                    'confidence': 0.95,
                    'technical_info': technical_info,
                    'zones': [],
                    'dimension_lines': []
                }
            
            else:
                # 2. Usar OCR avanzado para planos escaneados
                logger.debug(f"🔍 Página {page_num + 1}: Usando OCR avanzado")
                
                # Rasterizar a alta resolución
                mat = fitz.Matrix(4.0, 4.0)  # 600 DPI aprox
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convertir a OpenCV
                nparr = np.frombuffer(img_data, np.uint8)
                cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Procesar imagen avanzada
                processed_result = self._process_image_advanced(cv_image)
                
                return processed_result
                
        except Exception as e:
            logger.error(f"❌ Error procesando página {page_num + 1}: {str(e)}")
            return {
                'text': '',
                'extraction_method': 'page_error',
                'confidence': 0.0,
                'error': str(e),
                'technical_info': {},
                'zones': [],
                'dimension_lines': []
            }
    
    def _process_image_advanced(self, cv_image: np.ndarray) -> Dict[str, Any]:
        """Procesamiento avanzado de imagen con detección de zonas"""
        
        try:
            # 1. Preprocesamiento avanzado
            preprocessed = self._advanced_preprocessing(cv_image)
            
            # 2. Detección de zonas de texto
            text_zones = self._detect_text_zones(preprocessed)
            
            # 3. Detección de líneas de dimensión
            dimension_lines = self._detect_dimension_lines(preprocessed)
            
            # 4. OCR por zonas
            extracted_text = ""
            total_confidence = 0
            zone_count = 0
            
            for zone in text_zones:
                zone_result = self._ocr_zone(preprocessed, zone)
                if zone_result['text'].strip():
                    extracted_text += f"{zone_result['text']}\n"
                    total_confidence += zone_result['confidence']
                    zone_count += 1
            
            # 5. Extraer información técnica
            technical_info = self._extract_technical_info_from_text(extracted_text)
            
            # 6. Procesar líneas de dimensión
            for dim_line in dimension_lines:
                dim_text = self._extract_dimension_text(preprocessed, dim_line)
                if dim_text:
                    technical_info.setdefault('dimensions_from_lines', []).append({
                        'line': dim_line,
                        'text': dim_text
                    })
            
            avg_confidence = total_confidence / zone_count if zone_count > 0 else 0.5
            
            return {
                'text': extracted_text,
                'extraction_method': 'advanced_ocr',
                'confidence': avg_confidence,
                'technical_info': technical_info,
                'zones': [zone.__dict__ for zone in text_zones],
                'dimension_lines': [line.__dict__ for line in dimension_lines]
            }
            
        except Exception as e:
            logger.error(f"❌ Error en procesamiento avanzado: {str(e)}")
            return {
                'text': '',
                'extraction_method': 'advanced_error',
                'confidence': 0.0,
                'error': str(e),
                'technical_info': {},
                'zones': [],
                'dimension_lines': []
            }
    
    def _advanced_preprocessing(self, image: np.ndarray) -> np.ndarray:
        """Preprocesamiento avanzado de imagen"""
        
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Reducción de ruido con filtro bilateral
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Detección y corrección de inclinación (deskew)
            angle = self._detect_skew_angle(denoised)
            if abs(angle) > 0.5:
                logger.debug(f"🔄 Corrigiendo inclinación: {angle:.2f}°")
                denoised = self._rotate_image(denoised, angle)
            
            # Binarización adaptativa
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Operaciones morfológicas para limpiar
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"⚠️ Error en preprocesamiento avanzado: {str(e)}")
            return image
    
    def _detect_skew_angle(self, image: np.ndarray) -> float:
        """Detectar ángulo de inclinación usando transformada de Hough"""
        
        try:
            # Detectar bordes
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detectar líneas
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                angles = []
                for rho, theta in lines[:20]:  # Solo las primeras 20 líneas
                    angle = np.degrees(theta) - 90
                    if abs(angle) < 45:  # Solo ángulos razonables
                        angles.append(angle)
                
                if angles:
                    # Usar la mediana para robustez
                    return np.median(angles)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando inclinación: {str(e)}")
            return 0.0
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotar imagen para corregir inclinación"""
        
        try:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            
            # Matriz de rotación
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Rotar imagen
            rotated = cv2.warpAffine(image, M, (w, h), 
                                   flags=cv2.INTER_CUBIC, 
                                   borderMode=cv2.BORDER_REPLICATE)
            
            return rotated
            
        except Exception as e:
            logger.warning(f"⚠️ Error rotando imagen: {str(e)}")
            return image
    
    def _detect_text_zones(self, image: np.ndarray) -> List[TextZone]:
        """Detectar zonas de texto usando MSER y heurísticas"""
        
        try:
            zones = []
            
            # Usar MSER para detectar regiones de texto
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(image)
            
            # Filtrar y agrupar regiones
            text_boxes = []
            for region in regions:
                # Calcular bounding box
                x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
                
                # Filtrar por tamaño (evitar ruido)
                if w > 10 and h > 5 and w < image.shape[1] * 0.8 and h < image.shape[0] * 0.3:
                    text_boxes.append((x, y, x + w, y + h))
            
            # Agrupar cajas cercanas
            grouped_boxes = self._group_nearby_boxes(text_boxes)
            
            # Crear zonas de texto
            for i, (x1, y1, x2, y2) in enumerate(grouped_boxes):
                zone_type = self._classify_zone_type(image, (x1, y1, x2, y2))
                
                zones.append(TextZone(
                    bbox=(x1, y1, x2, y2),
                    text="",  # Se llenará en OCR
                    confidence=0.0,  # Se llenará en OCR
                    zone_type=zone_type
                ))
            
            logger.debug(f"🎯 Detectadas {len(zones)} zonas de texto")
            return zones
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando zonas de texto: {str(e)}")
            return []
    
    def _group_nearby_boxes(self, boxes: List[Tuple[int, int, int, int]], 
                           threshold: int = 20) -> List[Tuple[int, int, int, int]]:
        """Agrupar cajas de texto cercanas"""
        
        if not boxes:
            return []
        
        grouped = []
        used = set()
        
        for i, box1 in enumerate(boxes):
            if i in used:
                continue
                
            group = [box1]
            used.add(i)
            
            for j, box2 in enumerate(boxes[i+1:], i+1):
                if j in used:
                    continue
                    
                # Verificar si las cajas están cerca
                if self._boxes_are_close(box1, box2, threshold):
                    group.append(box2)
                    used.add(j)
            
            # Combinar cajas del grupo
            if group:
                x1 = min(box[0] for box in group)
                y1 = min(box[1] for box in group)
                x2 = max(box[2] for box in group)
                y2 = max(box[3] for box in group)
                grouped.append((x1, y1, x2, y2))
        
        return grouped
    
    def _boxes_are_close(self, box1: Tuple[int, int, int, int], 
                        box2: Tuple[int, int, int, int], threshold: int) -> bool:
        """Verificar si dos cajas están cerca"""
        
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calcular distancia entre centros
        center1 = ((x1_1 + x2_1) / 2, (y1_1 + y2_1) / 2)
        center2 = ((x1_2 + x2_2) / 2, (y1_2 + y2_2) / 2)
        
        distance = math.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
        
        return distance < threshold
    
    def _classify_zone_type(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> str:
        """Clasificar tipo de zona basado en características"""
        
        try:
            x1, y1, x2, y2 = bbox
            zone_image = image[y1:y2, x1:x2]
            
            # Características básicas
            height = y2 - y1
            width = x2 - x1
            aspect_ratio = width / height if height > 0 else 0
            
            # Posición relativa
            img_height, img_width = image.shape[:2]
            relative_y = y1 / img_height
            
            # Clasificación heurística
            if relative_y < 0.1 or relative_y > 0.9:
                return 'legend'  # Probablemente leyenda o título
            elif aspect_ratio > 5:
                return 'dimension'  # Probablemente línea de cota
            elif height < 30 and width < 100:
                return 'dimension'  # Texto de medida
            else:
                return 'text'  # Texto general
                
        except Exception as e:
            logger.warning(f"⚠️ Error clasificando zona: {str(e)}")
            return 'text'

    def _detect_dimension_lines(self, image: np.ndarray) -> List[DimensionLine]:
        """Detectar líneas de dimensión en planos"""

        try:
            dimension_lines = []

            # Detectar líneas usando HoughLinesP
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50,
                                   minLineLength=30, maxLineGap=10)

            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]

                    # Filtrar líneas horizontales y verticales (típicas de cotas)
                    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
                    if abs(angle) < 5 or abs(angle - 90) < 5 or abs(angle + 90) < 5:

                        # Buscar texto cerca de la línea
                        text_near_line = self._find_text_near_line(image, (x1, y1, x2, y2))

                        if text_near_line:
                            dimension_lines.append(DimensionLine(
                                start_point=(x1, y1),
                                end_point=(x2, y2),
                                text_value=text_near_line,
                                computed_value_meters=self._parse_dimension_value(text_near_line),
                                confidence=0.7,
                                bbox=(min(x1, x2) - 10, min(y1, y2) - 10,
                                     max(x1, x2) + 10, max(y1, y2) + 10)
                            ))

            logger.debug(f"📏 Detectadas {len(dimension_lines)} líneas de dimensión")
            return dimension_lines

        except Exception as e:
            logger.warning(f"⚠️ Error detectando líneas de dimensión: {str(e)}")
            return []

    def _find_text_near_line(self, image: np.ndarray, line: Tuple[int, int, int, int]) -> str:
        """Buscar texto cerca de una línea de dimensión"""

        try:
            x1, y1, x2, y2 = line

            # Calcular punto medio de la línea
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2

            # Definir área de búsqueda alrededor del punto medio
            search_radius = 30
            x_start = max(0, mid_x - search_radius)
            y_start = max(0, mid_y - search_radius)
            x_end = min(image.shape[1], mid_x + search_radius)
            y_end = min(image.shape[0], mid_y + search_radius)

            # Extraer región
            region = image[y_start:y_end, x_start:x_end]

            if region.size > 0:
                # Convertir a PIL para OCR
                pil_image = Image.fromarray(region)

                # OCR específico para números
                text = pytesseract.image_to_string(
                    pil_image,
                    config=self.tesseract_configs['numbers']
                ).strip()

                # Filtrar solo texto que parece dimensión
                if re.search(r'\d+', text):
                    return text

            return ""

        except Exception as e:
            logger.warning(f"⚠️ Error buscando texto cerca de línea: {str(e)}")
            return ""

    def _parse_dimension_value(self, text: str) -> Optional[float]:
        """Parsear valor de dimensión a metros"""

        try:
            # Buscar números en el texto
            numbers = re.findall(r'(\d+(?:[.,]\d+)?)', text)

            if numbers:
                value = float(numbers[0].replace(',', '.'))

                # Detectar unidades y convertir a metros
                text_lower = text.lower()
                if 'mm' in text_lower:
                    return value / 1000  # mm a m
                elif 'cm' in text_lower:
                    return value / 100   # cm a m
                elif 'm' in text_lower and 'mm' not in text_lower and 'cm' not in text_lower:
                    return value         # ya en metros
                else:
                    # Asumir metros si no hay unidad específica
                    return value

            return None

        except Exception as e:
            logger.warning(f"⚠️ Error parseando dimensión: {str(e)}")
            return None

    def _ocr_zone(self, image: np.ndarray, zone: TextZone) -> Dict[str, Any]:
        """Realizar OCR en una zona específica"""

        try:
            x1, y1, x2, y2 = zone.bbox
            zone_image = image[y1:y2, x1:x2]

            if zone_image.size == 0:
                return {'text': '', 'confidence': 0.0}

            # Convertir a PIL
            pil_image = Image.fromarray(zone_image)

            # Seleccionar configuración según tipo de zona
            if zone.zone_type == 'dimension':
                config = self.tesseract_configs['numbers']
            elif zone.zone_type == 'legend':
                config = self.tesseract_configs['standard']
            else:
                config = self.tesseract_configs['single_line']

            # Realizar OCR
            text = pytesseract.image_to_string(pil_image, config=config).strip()

            # Obtener confianza
            try:
                data = pytesseract.image_to_data(pil_image, config=config,
                                               output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence = avg_confidence / 100.0
            except:
                confidence = 0.6

            # Actualizar zona
            zone.text = text
            zone.confidence = confidence

            return {'text': text, 'confidence': confidence}

        except Exception as e:
            logger.warning(f"⚠️ Error en OCR de zona: {str(e)}")
            return {'text': '', 'confidence': 0.0}

    def _extract_dimension_text(self, image: np.ndarray, dim_line: DimensionLine) -> str:
        """Extraer texto de dimensión específico"""

        try:
            x1, y1, x2, y2 = dim_line.bbox
            region = image[y1:y2, x1:x2]

            if region.size > 0:
                pil_image = Image.fromarray(region)
                text = pytesseract.image_to_string(
                    pil_image,
                    config=self.tesseract_configs['numbers']
                ).strip()

                return text

            return ""

        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo texto de dimensión: {str(e)}")
            return ""

    def _extract_technical_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extraer información técnica estructurada del texto"""

        try:
            technical_info = {
                'scales': [],
                'dimensions': [],
                'areas': [],
                'materials': [],
                'installations': [],
                'structural_elements': [],
                'accessibility_features': [],
                'fire_safety_elements': [],
                'energy_efficiency_data': [],
                'urban_parameters': []
            }

            # Extraer escalas
            for pattern in self.scale_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    scale_value = match.group(1) if match.groups() else match.group(0)
                    technical_info['scales'].append({
                        'text': match.group(0),
                        'scale': scale_value,
                        'position': match.start()
                    })

            # Extraer dimensiones
            for pattern in self.dimension_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    technical_info['dimensions'].append({
                        'text': match.group(0),
                        'values': [float(g.replace(',', '.')) for g in groups if g],
                        'position': match.start(),
                        'pattern': pattern
                    })

            # Extraer áreas
            for pattern in self.area_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if groups:
                        technical_info['areas'].append({
                            'text': match.group(0),
                            'value': float(groups[0].replace(',', '.')),
                            'position': match.start()
                        })

            # Extraer materiales (patrones específicos)
            material_patterns = [
                r'(?:hormigón|concrete|acero|steel|madera|wood|ladrillo|brick|bloque|block)',
                r'(?:HA-\d+|HM-\d+)',  # Hormigones
                r'(?:S\d+|IPE\d+|HEB\d+)',  # Perfiles de acero
                r'(?:cerámica|ceramic|gres|porcelánico)'
            ]

            for pattern in material_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    technical_info['materials'].append({
                        'text': match.group(0),
                        'position': match.start(),
                        'type': 'material'
                    })

            # Extraer elementos estructurales
            structural_patterns = [
                r'(?:viga|beam|pilar|column|forjado|slab|cimentación|foundation)',
                r'(?:zapata|footing|losa|muro|wall|pantalla)',
                r'(?:pilote|pile|encepado|cap)'
            ]

            for pattern in structural_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    technical_info['structural_elements'].append({
                        'text': match.group(0),
                        'position': match.start(),
                        'type': 'structural'
                    })

            # Extraer instalaciones
            installation_patterns = [
                r'(?:fontanería|plumbing|electricidad|electrical|gas|climatización|hvac)',
                r'(?:calefacción|heating|refrigeración|cooling|ventilación|ventilation)',
                r'(?:saneamiento|drainage|telecomunicaciones|telecommunications)'
            ]

            for pattern in installation_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    technical_info['installations'].append({
                        'text': match.group(0),
                        'position': match.start(),
                        'type': 'installation'
                    })

            logger.debug(f"📊 Información técnica extraída: {len(technical_info['dimensions'])} dimensiones, "
                        f"{len(technical_info['areas'])} áreas, {len(technical_info['materials'])} materiales")

            return technical_info

        except Exception as e:
            logger.error(f"❌ Error extrayendo información técnica: {str(e)}")
            return {}

    def _consolidate_results(self, page_results: List[Dict], pdf_path: str) -> Dict[str, Any]:
        """Consolidar resultados de todas las páginas"""

        try:
            full_text = []
            all_technical_info = {
                'scales': [],
                'dimensions': [],
                'areas': [],
                'materials': [],
                'installations': [],
                'structural_elements': [],
                'accessibility_features': [],
                'fire_safety_elements': [],
                'energy_efficiency_data': [],
                'urban_parameters': []
            }

            total_confidence = 0
            extraction_methods = []
            all_zones = []
            all_dimension_lines = []

            for page_result in page_results:
                # Consolidar texto
                if page_result.get('text'):
                    full_text.append(f"\n--- Página {page_result['page_number']} ---\n")
                    full_text.append(page_result['text'])

                # Consolidar información técnica
                if 'technical_info' in page_result:
                    tech_info = page_result['technical_info']
                    for key in all_technical_info.keys():
                        if key in tech_info:
                            all_technical_info[key].extend(tech_info[key])

                # Consolidar métricas
                total_confidence += page_result.get('confidence', 0)
                extraction_methods.append(page_result.get('extraction_method', 'unknown'))

                # Consolidar zonas y líneas
                all_zones.extend(page_result.get('zones', []))
                all_dimension_lines.extend(page_result.get('dimension_lines', []))

            # Calcular métricas globales
            avg_confidence = total_confidence / len(page_results) if page_results else 0
            primary_method = max(set(extraction_methods), key=extraction_methods.count) if extraction_methods else 'unknown'

            # Análisis dimensional consolidado
            dimensional_analysis = self._analyze_consolidated_dimensions(all_technical_info)

            # Detectar escala del proyecto
            project_scale = self._detect_project_scale(all_technical_info['scales'])

            result = {
                'full_text': '\n'.join(full_text),
                'page_results': page_results,
                'total_pages': len(page_results),
                'extraction_method': primary_method,
                'confidence': avg_confidence,
                'file_path': pdf_path,
                'technical_info': all_technical_info,
                'dimensional_analysis': dimensional_analysis,
                'project_scale': project_scale,
                'zones_detected': len(all_zones),
                'dimension_lines_detected': len(all_dimension_lines),
                'processing_summary': {
                    'total_dimensions': len(all_technical_info['dimensions']),
                    'total_areas': len(all_technical_info['areas']),
                    'total_materials': len(all_technical_info['materials']),
                    'total_installations': len(all_technical_info['installations']),
                    'total_structural_elements': len(all_technical_info['structural_elements'])
                }
            }

            logger.info(f"📊 CONSOLIDACIÓN COMPLETADA: {result['processing_summary']}")

            return result

        except Exception as e:
            logger.error(f"❌ Error consolidando resultados: {str(e)}")
            return {
                'full_text': '',
                'page_results': page_results,
                'total_pages': len(page_results),
                'extraction_method': 'consolidation_error',
                'confidence': 0.0,
                'error': str(e),
                'file_path': pdf_path
            }

    def _analyze_consolidated_dimensions(self, technical_info: Dict) -> Dict[str, Any]:
        """Analizar dimensiones consolidadas de todo el documento"""

        try:
            analysis = {
                'dimension_statistics': {},
                'area_statistics': {},
                'scale_analysis': {},
                'material_analysis': {},
                'structural_analysis': {},
                'installation_analysis': {}
            }

            # Análisis de dimensiones
            if technical_info['dimensions']:
                all_values = []
                for dim in technical_info['dimensions']:
                    all_values.extend(dim['values'])

                if all_values:
                    analysis['dimension_statistics'] = {
                        'count': len(all_values),
                        'min': min(all_values),
                        'max': max(all_values),
                        'avg': sum(all_values) / len(all_values),
                        'range': max(all_values) - min(all_values),
                        'most_common_range': self._find_most_common_range(all_values)
                    }

            # Análisis de áreas
            if technical_info['areas']:
                area_values = [area['value'] for area in technical_info['areas']]
                analysis['area_statistics'] = {
                    'count': len(area_values),
                    'min': min(area_values),
                    'max': max(area_values),
                    'avg': sum(area_values) / len(area_values),
                    'total_area': sum(area_values)
                }

            # Análisis de materiales
            if technical_info['materials']:
                material_types = {}
                for material in technical_info['materials']:
                    mat_text = material['text'].lower()
                    if 'hormigón' in mat_text or 'concrete' in mat_text:
                        material_types['concrete'] = material_types.get('concrete', 0) + 1
                    elif 'acero' in mat_text or 'steel' in mat_text:
                        material_types['steel'] = material_types.get('steel', 0) + 1
                    elif 'madera' in mat_text or 'wood' in mat_text:
                        material_types['wood'] = material_types.get('wood', 0) + 1
                    else:
                        material_types['other'] = material_types.get('other', 0) + 1

                analysis['material_analysis'] = {
                    'total_materials': len(technical_info['materials']),
                    'material_distribution': material_types,
                    'primary_material': max(material_types.items(), key=lambda x: x[1])[0] if material_types else 'unknown'
                }

            # Análisis estructural
            if technical_info['structural_elements']:
                structural_types = {}
                for element in technical_info['structural_elements']:
                    elem_text = element['text'].lower()
                    if 'viga' in elem_text or 'beam' in elem_text:
                        structural_types['beams'] = structural_types.get('beams', 0) + 1
                    elif 'pilar' in elem_text or 'column' in elem_text:
                        structural_types['columns'] = structural_types.get('columns', 0) + 1
                    elif 'forjado' in elem_text or 'slab' in elem_text:
                        structural_types['slabs'] = structural_types.get('slabs', 0) + 1
                    elif 'cimentación' in elem_text or 'foundation' in elem_text:
                        structural_types['foundations'] = structural_types.get('foundations', 0) + 1
                    else:
                        structural_types['other'] = structural_types.get('other', 0) + 1

                analysis['structural_analysis'] = {
                    'total_elements': len(technical_info['structural_elements']),
                    'element_distribution': structural_types,
                    'structural_complexity': len(structural_types)
                }

            return analysis

        except Exception as e:
            logger.error(f"❌ Error en análisis consolidado: {str(e)}")
            return {}

    def _detect_project_scale(self, scales: List[Dict]) -> Dict[str, Any]:
        """Detectar escala principal del proyecto"""

        try:
            if not scales:
                return {'detected': False, 'scale': None, 'confidence': 0.0}

            # Contar escalas más comunes
            scale_counts = {}
            for scale_info in scales:
                scale = scale_info['scale']
                scale_counts[scale] = scale_counts.get(scale, 0) + 1

            # Encontrar escala más común
            most_common_scale = max(scale_counts.items(), key=lambda x: x[1])

            # Calcular confianza basada en frecuencia
            total_scales = len(scales)
            confidence = most_common_scale[1] / total_scales

            return {
                'detected': True,
                'scale': most_common_scale[0],
                'scale_ratio': f"1:{most_common_scale[0]}",
                'confidence': confidence,
                'occurrences': most_common_scale[1],
                'total_scale_references': total_scales,
                'all_scales_found': list(scale_counts.keys())
            }

        except Exception as e:
            logger.warning(f"⚠️ Error detectando escala: {str(e)}")
            return {'detected': False, 'error': str(e)}

    def _find_most_common_range(self, values: List[float]) -> Dict[str, Any]:
        """Encontrar el rango más común de valores (método mejorado)"""

        try:
            if not values:
                return {}

            # Agrupar valores en rangos más inteligentes
            ranges = {}
            for value in values:
                # Usar rangos logarítmicos para mejor agrupación
                if value < 1:
                    range_key = round(value, 2)
                elif value < 10:
                    range_key = round(value, 1)
                else:
                    range_key = round(value)

                ranges[range_key] = ranges.get(range_key, 0) + 1

            # Encontrar el rango más común
            most_common = max(ranges.items(), key=lambda x: x[1])

            return {
                'range': most_common[0],
                'count': most_common[1],
                'percentage': (most_common[1] / len(values)) * 100,
                'total_unique_ranges': len(ranges)
            }

        except Exception as e:
            logger.warning(f"⚠️ Error encontrando rango común: {str(e)}")
            return {}

    def get_cache_key(self, pdf_path: str, page_num: int = None) -> str:
        """Generar clave de cache para resultados OCR"""

        try:
            # Usar hash del archivo y página para cache
            with open(pdf_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            if page_num is not None:
                return f"{file_hash}_page_{page_num}"
            else:
                return f"{file_hash}_full"

        except Exception as e:
            logger.warning(f"⚠️ Error generando clave de cache: {str(e)}")
            return f"fallback_{pdf_path}_{page_num}"

    def save_structured_output(self, result: Dict[str, Any], output_path: str) -> bool:
        """Guardar salida estructurada en JSON"""

        try:
            # Preparar datos para serialización
            serializable_result = self._make_serializable(result)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Resultado guardado en: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error guardando resultado: {str(e)}")
            return False

    def _make_serializable(self, obj: Any) -> Any:
        """Hacer objeto serializable para JSON"""

        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (TextZone, DimensionLine)):
            return obj.__dict__
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        else:
            return obj
