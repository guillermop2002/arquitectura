import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import re
import numpy as np
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging

# Configurar logger específico
logger = logging.getLogger("basico.ocr_processor")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class BasicoOCRProcessor:
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6 -l spa'
        self.dimension_patterns = [
            r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)',
            r'(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)',
            r'(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)',
            r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)'
        ]
        self.area_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:m²|m2|metros?\s*cuadrados?)',
            r'(\d+(?:\.\d+)?)\s*(?:m²|m2)',
            r'(\d+(?:\.\d+)?)\s*metros?\s*cuadrados?'
        ]
        self.height_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)\s*(?:de\s*)?altura',
            r'altura[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)',
            r'(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)\s*(?:de\s*)?alto',
            r'alto[:\s]*(\d+(?:\.\d+)?)\s*(?:m|metros?|mm|cm)'
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extraer texto de PDF con OCR inteligente y análisis dimensional"""
        
        logger.info(f"🔍 INICIANDO EXTRACCIÓN DE PDF: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            full_text = []
            page_texts = []
            total_confidence = 0
            extraction_methods = []
            all_dimensions = []
            all_areas = []
            all_heights = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Intentar extraer texto directo primero
                direct_text = page.get_text()
                
                if len(direct_text.strip()) > 50:
                    # Texto directo disponible
                    page_text = direct_text
                    extraction_method = 'direct'
                    confidence = 0.95
                else:
                    # Usar OCR mejorado para imágenes/texto escaneado
                    page_data = self._extract_with_enhanced_ocr(page, page_num + 1)
                    page_text = page_data['text']
                    extraction_method = 'enhanced_ocr'
                    confidence = page_data['confidence']
                
                # Extraer dimensiones de esta página
                page_dimensions = self._extract_dimensions_from_text(page_text)
                page_areas = self._extract_areas_from_text(page_text)
                page_heights = self._extract_heights_from_text(page_text)
                
                page_texts.append({
                    'page_number': page_num + 1,
                    'text': page_text,
                    'method': extraction_method,
                    'confidence': confidence,
                    'dimensions': page_dimensions,
                    'areas': page_areas,
                    'heights': page_heights
                })
                
                full_text.append(f"\n--- Página {page_num + 1} ---\n")
                full_text.append(page_text)
                
                # Acumular dimensiones
                all_dimensions.extend(page_dimensions)
                all_areas.extend(page_areas)
                all_heights.extend(page_heights)
                
                total_confidence += confidence
                extraction_methods.append(extraction_method)
            
            doc.close()
            
            # Calcular estadísticas
            avg_confidence = total_confidence / len(doc) if len(doc) > 0 else 0
            primary_method = max(set(extraction_methods), key=extraction_methods.count)
            
            # Análisis dimensional consolidado
            dimensional_analysis = self._analyze_extracted_dimensions(all_dimensions, all_areas, all_heights)
            
            result = {
                'full_text': '\n'.join(full_text),
                'page_texts': page_texts,
                'total_pages': len(doc),
                'extraction_method': primary_method,
                'confidence': avg_confidence,
                'file_path': pdf_path,
                'dimensional_analysis': dimensional_analysis,
                'extracted_dimensions': {
                    'dimensions': all_dimensions,
                    'areas': all_areas,
                    'heights': all_heights
                }
            }
            
            logger.info(f"✅ EXTRACCIÓN COMPLETADA: {len(doc)} páginas, {len(all_dimensions)} dimensiones, {len(all_areas)} áreas, {len(all_heights)} alturas")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en extracción de PDF: {str(e)}")
            return {
                'full_text': '',
                'page_texts': [],
                'total_pages': 0,
                'extraction_method': 'error',
                'confidence': 0.0,
                'error': str(e),
                'file_path': pdf_path,
                'dimensional_analysis': {},
                'extracted_dimensions': {'dimensions': [], 'areas': [], 'heights': []}
            }
    
    def _extract_with_enhanced_ocr(self, page, page_number: int) -> Dict[str, Any]:
        """Extraer texto usando OCR mejorado con preprocesamiento de imagen"""
        
        try:
            # Convertir página a imagen con mayor resolución
            mat = fitz.Matrix(3.0, 3.0)  # Escalar 3x para mejor OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Procesar imagen para mejorar OCR
            image = Image.open(io.BytesIO(img_data))
            
            # Preprocesamiento de imagen
            enhanced_image = self._preprocess_image_for_ocr(image)
            
            # Extraer texto con múltiples configuraciones
            texts = []
            confidences = []
            
            # Configuración estándar
            text1 = pytesseract.image_to_string(enhanced_image, config=self.tesseract_config)
            texts.append(text1)
            
            # Configuración para texto de planos
            config_planos = '--oem 3 --psm 8 -l spa'  # PSM 8 para texto de una sola palabra
            text2 = pytesseract.image_to_string(enhanced_image, config=config_planos)
            texts.append(text2)
            
            # Configuración para números y dimensiones
            config_nums = '--oem 3 --psm 7 -l spa'  # PSM 7 para texto de una línea
            text3 = pytesseract.image_to_string(enhanced_image, config=config_nums)
            texts.append(text3)
            
            # Combinar textos únicos
            combined_text = self._combine_ocr_texts(texts)
            
            # Obtener datos de confianza
            try:
                data = pytesseract.image_to_data(enhanced_image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence = avg_confidence / 100.0  # Normalizar a 0-1
            except:
                confidence = 0.7  # Confianza por defecto
            
            return {
                'text': combined_text,
                'confidence': confidence,
                'page_number': page_number,
                'method': 'enhanced_tesseract_ocr'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en OCR mejorado: {str(e)}")
            return {
                'text': '',
                'confidence': 0.0,
                'page_number': page_number,
                'method': 'enhanced_ocr_error',
                'error': str(e)
            }
    
    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocesar imagen para mejorar OCR"""
        
        try:
            # Convertir a escala de grises
            if image.mode != 'L':
                image = image.convert('L')
            
            # Mejorar contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Mejorar nitidez
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Aplicar filtro para reducir ruido
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            logger.warning(f"⚠️ Error en preprocesamiento de imagen: {str(e)}")
            return image
    
    def _combine_ocr_texts(self, texts: List[str]) -> str:
        """Combinar múltiples resultados de OCR eliminando duplicados"""
        
        try:
            # Filtrar textos vacíos
            valid_texts = [text.strip() for text in texts if text.strip()]
            
            if not valid_texts:
                return ""
            
            # Si solo hay un texto válido, devolverlo
            if len(valid_texts) == 1:
                return valid_texts[0]
            
            # Combinar textos únicos
            combined_lines = set()
            for text in valid_texts:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 2:  # Filtrar líneas muy cortas
                        combined_lines.add(line)
            
            return '\n'.join(sorted(combined_lines))
            
        except Exception as e:
            logger.warning(f"⚠️ Error combinando textos OCR: {str(e)}")
            return texts[0] if texts else ""
    
    def _extract_dimensions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extraer dimensiones del texto usando patrones regex"""
        
        dimensions = []
        
        try:
            for pattern in self.dimension_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        dimensions.append({
                            'type': 'dimension',
                            'values': [float(g) for g in groups if g],
                            'text': match.group(0),
                            'position': match.start(),
                            'pattern_used': pattern
                        })
                    elif len(groups) == 1:
                        dimensions.append({
                            'type': 'single_dimension',
                            'value': float(groups[0]),
                            'text': match.group(0),
                            'position': match.start(),
                            'pattern_used': pattern
                        })
            
            logger.debug(f"📏 Dimensiones extraídas: {len(dimensions)}")
            return dimensions
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo dimensiones: {str(e)}")
            return []
    
    def _extract_areas_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extraer áreas del texto usando patrones regex"""
        
        areas = []
        
        try:
            for pattern in self.area_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if groups:
                        areas.append({
                            'type': 'area',
                            'value': float(groups[0]),
                            'text': match.group(0),
                            'position': match.start(),
                            'pattern_used': pattern
                        })
            
            logger.debug(f"📐 Áreas extraídas: {len(areas)}")
            return areas
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo áreas: {str(e)}")
            return []
    
    def _extract_heights_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extraer alturas del texto usando patrones regex"""
        
        heights = []
        
        try:
            for pattern in self.height_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if groups:
                        heights.append({
                            'type': 'height',
                            'value': float(groups[0]),
                            'text': match.group(0),
                            'position': match.start(),
                            'pattern_used': pattern
                        })
            
            logger.debug(f"📏 Alturas extraídas: {len(heights)}")
            return heights
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo alturas: {str(e)}")
            return []
    
    def _analyze_extracted_dimensions(self, dimensions: List[Dict], areas: List[Dict], heights: List[Dict]) -> Dict[str, Any]:
        """Analizar dimensiones extraídas y generar resumen"""
        
        try:
            analysis = {
                'total_dimensions': len(dimensions),
                'total_areas': len(areas),
                'total_heights': len(heights),
                'dimension_summary': {},
                'area_summary': {},
                'height_summary': {},
                'statistical_analysis': {}
            }
            
            # Análisis de dimensiones
            if dimensions:
                dim_values = []
                for dim in dimensions:
                    if 'values' in dim:
                        dim_values.extend(dim['values'])
                    elif 'value' in dim:
                        dim_values.append(dim['value'])
                
                if dim_values:
                    analysis['dimension_summary'] = {
                        'count': len(dim_values),
                        'min': min(dim_values),
                        'max': max(dim_values),
                        'avg': sum(dim_values) / len(dim_values),
                        'values': dim_values
                    }
            
            # Análisis de áreas
            if areas:
                area_values = [area['value'] for area in areas]
                analysis['area_summary'] = {
                    'count': len(area_values),
                    'min': min(area_values),
                    'max': max(area_values),
                    'avg': sum(area_values) / len(area_values),
                    'values': area_values
                }
            
            # Análisis de alturas
            if heights:
                height_values = [height['value'] for height in heights]
                analysis['height_summary'] = {
                    'count': len(height_values),
                    'min': min(height_values),
                    'max': max(height_values),
                    'avg': sum(height_values) / len(height_values),
                    'values': height_values
                }
            
            # Análisis estadístico general
            all_values = []
            if 'dimension_summary' in analysis and 'values' in analysis['dimension_summary']:
                all_values.extend(analysis['dimension_summary']['values'])
            if 'area_summary' in analysis and 'values' in analysis['area_summary']:
                all_values.extend(analysis['area_summary']['values'])
            if 'height_summary' in analysis and 'values' in analysis['height_summary']:
                all_values.extend(analysis['height_summary']['values'])
            
            if all_values:
                analysis['statistical_analysis'] = {
                    'total_measurements': len(all_values),
                    'range': max(all_values) - min(all_values),
                    'most_common_range': self._find_most_common_range(all_values),
                    'outliers': self._find_outliers(all_values)
                }
            
            logger.info(f"📊 Análisis dimensional completado: {analysis['total_dimensions']} dimensiones, {analysis['total_areas']} áreas, {analysis['total_heights']} alturas")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error en análisis dimensional: {str(e)}")
            return {
                'total_dimensions': 0,
                'total_areas': 0,
                'total_heights': 0,
                'error': str(e)
            }
    
    def _find_most_common_range(self, values: List[float]) -> Dict[str, Any]:
        """Encontrar el rango más común de valores"""
        
        try:
            if not values:
                return {}
            
            # Agrupar valores en rangos
            ranges = {}
            for value in values:
                # Redondear a rangos de 0.5
                range_key = round(value * 2) / 2
                if range_key not in ranges:
                    ranges[range_key] = 0
                ranges[range_key] += 1
            
            # Encontrar el rango más común
            most_common = max(ranges.items(), key=lambda x: x[1])
            
            return {
                'range': most_common[0],
                'count': most_common[1],
                'percentage': (most_common[1] / len(values)) * 100
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error encontrando rango común: {str(e)}")
            return {}
    
    def _find_outliers(self, values: List[float]) -> List[float]:
        """Encontrar valores atípicos usando el método IQR"""
        
        try:
            if len(values) < 4:
                return []
            
            sorted_values = sorted(values)
            q1 = sorted_values[len(sorted_values) // 4]
            q3 = sorted_values[3 * len(sorted_values) // 4]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [v for v in values if v < lower_bound or v > upper_bound]
            
            return outliers
            
        except Exception as e:
            logger.warning(f"⚠️ Error encontrando outliers: {str(e)}")
            return []
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extraer texto de imagen usando OCR"""
        
        try:
            image = Image.open(image_path)
            
            # Extraer texto
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            # Obtener confianza
            try:
                data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence = avg_confidence / 100.0
            except:
                confidence = 0.7
            
            return {
                'text': text,
                'confidence': confidence,
                'method': 'image_ocr',
                'file_path': image_path
            }
            
        except Exception as e:
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'image_error',
                'error': str(e),
                'file_path': image_path
            }
    
    def get_ocr_info(self) -> Dict[str, Any]:
        """Obtener información sobre la configuración OCR"""
        
        try:
            tesseract_version = pytesseract.get_tesseract_version()
            languages = pytesseract.get_languages()
            
            return {
                'tesseract_available': True,
                'tesseract_version': str(tesseract_version),
                'languages_available': languages,
                'spanish_available': 'spa' in languages,
                'config_used': self.tesseract_config
            }
            
        except Exception as e:
            return {
                'tesseract_available': False,
                'error': str(e),
                'config_used': self.tesseract_config
            }
