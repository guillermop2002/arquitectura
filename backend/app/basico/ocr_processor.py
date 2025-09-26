import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import re
import numpy as np
import cv2
from skimage import measure, morphology
from pdf2image import convert_from_path
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging
import hashlib
import json

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
        
        # Cache para resultados procesados
        self.cache_dir = Path("cache/ocr")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extraer texto de PDF con OCR inteligente y análisis dimensional - PARTE 1 MEJORADO"""
        
        logger.info(f"🔍 INICIANDO EXTRACCIÓN AVANZADA DE PDF: {pdf_path}")
        
        try:
            # Verificar cache primero
            file_hash = self._get_file_hash(pdf_path)
            cached_result = self._get_cached_result(file_hash)
            if cached_result:
                logger.info(f"📋 USANDO RESULTADO EN CACHÉ: {file_hash[:8]}...")
                return cached_result
            
            doc = fitz.open(pdf_path)
            
            # Detectar tipo de PDF
            pdf_type = self._detect_pdf_type(doc)
            logger.info(f"📊 TIPO DE PDF DETECTADO: {pdf_type['type']} (confianza: {pdf_type['confidence']:.2f})")
            
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
                    # Usar OCR avanzado con preprocesamiento mejorado
                    page_data = self._extract_with_advanced_ocr(page, page_num + 1, pdf_type)
                    page_text = page_data['text']
                    extraction_method = 'advanced_ocr'
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
                    'heights': page_heights,
                    'pdf_type': pdf_type['type']
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
                'pdf_type': pdf_type,
                'dimensional_analysis': dimensional_analysis,
                'extracted_dimensions': {
                    'dimensions': all_dimensions,
                    'areas': all_areas,
                    'heights': all_heights
                },
                'processing_metadata': {
                    'cache_key': file_hash,
                    'processing_time': 0,  # Se calculará después
                    'advanced_features': True
                }
            }
            
            # Guardar en cache
            self._cache_result(file_hash, result)
            
            logger.info(f"✅ EXTRACCIÓN AVANZADA COMPLETADA: {len(doc)} páginas, {len(all_dimensions)} dimensiones, {len(all_areas)} áreas, {len(all_heights)} alturas")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en extracción avanzada de PDF: {str(e)}")
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
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generar hash único del archivo para cache"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return hashlib.md5(file_content).hexdigest()
        except Exception as e:
            logger.warning(f"⚠️ Error generando hash: {str(e)}")
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def _get_cached_result(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Obtener resultado desde cache"""
        try:
            cache_file = self.cache_dir / f"{file_hash}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Error leyendo cache: {str(e)}")
        return None
    
    def _cache_result(self, file_hash: str, result: Dict[str, Any]):
        """Guardar resultado en cache"""
        try:
            cache_file = self.cache_dir / f"{file_hash}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 Resultado guardado en cache: {file_hash[:8]}...")
        except Exception as e:
            logger.warning(f"⚠️ Error guardando cache: {str(e)}")
    
    def _detect_pdf_type(self, doc) -> Dict[str, Any]:
        """Detectar tipo de PDF: vectorial, raster o mixto"""
        try:
            total_pages = len(doc)
            vectorial_pages = 0
            raster_pages = 0
            total_text_length = 0
            total_images = 0
            
            # Analizar primeras 5 páginas o todas si son menos
            sample_pages = min(5, total_pages)
            
            for page_num in range(sample_pages):
                page = doc.load_page(page_num)
                
                # Extraer texto nativo
                text_dict = page.get_text("dict")
                text_length = len(page.get_text())
                total_text_length += text_length
                
                # Contar imágenes
                image_list = page.get_images()
                total_images += len(image_list)
                
                # Determinar tipo de página
                if text_length > 100 and len(text_dict.get("blocks", [])) > 0:
                    # Verificar si el texto es nativo (vectorial)
                    has_native_text = any(
                        block.get("type") == 0 and len(block.get("lines", [])) > 0
                        for block in text_dict.get("blocks", [])
                    )
                    if has_native_text:
                        vectorial_pages += 1
                    else:
                        raster_pages += 1
                else:
                    raster_pages += 1
            
            # Calcular ratios
            vectorial_ratio = vectorial_pages / sample_pages
            raster_ratio = raster_pages / sample_pages
            avg_text_per_page = total_text_length / sample_pages
            avg_images_per_page = total_images / sample_pages
            
            # Determinar tipo principal
            if vectorial_ratio > 0.7:
                pdf_type = "vectorial"
                confidence = vectorial_ratio
            elif raster_ratio > 0.7:
                pdf_type = "raster"
                confidence = raster_ratio
            else:
                pdf_type = "mixto"
                confidence = max(vectorial_ratio, raster_ratio)
            
            return {
                "type": pdf_type,
                "confidence": confidence,
                "vectorial_ratio": vectorial_ratio,
                "raster_ratio": raster_ratio,
                "avg_text_per_page": avg_text_per_page,
                "avg_images_per_page": avg_images_per_page,
                "total_pages": total_pages,
                "sample_pages": sample_pages
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando tipo de PDF: {str(e)}")
            return {
                "type": "desconocido",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _adaptive_rasterization(self, page, pdf_type: Dict[str, Any]) -> Image.Image:
        """Rasterizar con DPI óptimo según tipo de documento"""
        try:
            # Determinar DPI óptimo
            if pdf_type["type"] == "vectorial":
                dpi = 300  # DPI estándar para texto vectorial
            elif pdf_type["type"] == "raster":
                dpi = 600  # DPI alto para texto escaneado
            else:  # mixto
                dpi = 450  # DPI intermedio
            
            # Rasterizar con PyMuPDF
            mat = fitz.Matrix(dpi/72, dpi/72)  # 72 DPI es el estándar de PyMuPDF
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convertir a PIL Image
            image = Image.open(io.BytesIO(img_data))
            
            logger.debug(f"📐 Rasterización adaptativa: {dpi} DPI para tipo {pdf_type['type']}")
            
            return image
            
        except Exception as e:
            logger.warning(f"⚠️ Error en rasterización adaptativa: {str(e)}")
            # Fallback a rasterización estándar
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            return Image.open(io.BytesIO(img_data))
    
    def _advanced_preprocessing(self, image: Image.Image) -> Image.Image:
        """Preprocesamiento avanzado con OpenCV"""
        try:
            # Convertir PIL a OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 1. Conversión a escala de grises
            if len(cv_image.shape) == 3:
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = cv_image
            
            # 2. Reducción de ruido con filtro bilateral
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # 3. Deskew automático (detección de ángulo)
            angle = self._detect_skew_angle(denoised)
            if abs(angle) > 0.5:  # Solo rotar si el ángulo es significativo
                denoised = self._rotate_image(denoised, angle)
                logger.debug(f"🔄 Imagen rotada {angle:.2f} grados")
            
            # 4. Binarización adaptativa
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 5. Operaciones morfológicas para limpiar
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Convertir de vuelta a PIL
            result_image = Image.fromarray(cleaned)
            
            logger.debug("🔧 Preprocesamiento avanzado completado")
            return result_image
            
        except Exception as e:
            logger.warning(f"⚠️ Error en preprocesamiento avanzado: {str(e)}")
            # Fallback a preprocesamiento básico
            return self._preprocess_image_for_ocr(image)
    
    def _detect_skew_angle(self, image: np.ndarray) -> float:
        """Detectar ángulo de inclinación de la imagen"""
        try:
            # Detectar bordes
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detectar líneas con Hough
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                angles = []
                for line in lines:
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi - 90
                    if -45 < angle < 45:  # Solo ángulos razonables
                        angles.append(angle)
                
                if angles:
                    # Usar la mediana para evitar outliers
                    return np.median(angles)
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"⚠️ Error detectando ángulo de inclinación: {str(e)}")
            return 0.0
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotar imagen por el ángulo especificado"""
        try:
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            
            # Matriz de rotación
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Rotar imagen
            rotated = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                   flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            return rotated
            
        except Exception as e:
            logger.warning(f"⚠️ Error rotando imagen: {str(e)}")
            return image
    
    def _detect_text_regions(self, image: Image.Image) -> List[Dict]:
        """Detectar regiones de texto para OCR por zonas"""
        try:
            # Convertir a OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detectar componentes conectados
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(gray, connectivity=8)
            
            text_regions = []
            
            for i in range(1, num_labels):  # Saltar el fondo (label 0)
                x, y, w, h, area = stats[i]
                
                # Filtrar por tamaño y forma
                if area > 100 and w > 20 and h > 10:  # Tamaño mínimo
                    aspect_ratio = w / h
                    if 0.1 < aspect_ratio < 10:  # Forma razonable para texto
                        text_regions.append({
                            "bbox": [x, y, x + w, y + h],
                            "area": area,
                            "aspect_ratio": aspect_ratio,
                            "confidence": min(1.0, area / 1000)  # Confianza basada en área
                        })
            
            # Ordenar por confianza
            text_regions.sort(key=lambda x: x["confidence"], reverse=True)
            
            logger.debug(f"🔍 Detectadas {len(text_regions)} regiones de texto")
            return text_regions[:20]  # Limitar a las 20 mejores
            
        except Exception as e:
            logger.warning(f"⚠️ Error detectando regiones de texto: {str(e)}")
            return []
    
    def _extract_with_advanced_ocr(self, page, page_number: int, pdf_type: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer texto usando OCR avanzado con preprocesamiento mejorado"""
        
        try:
            # 1. Rasterización adaptativa
            image = self._adaptive_rasterization(page, pdf_type)
            
            # 2. Preprocesamiento avanzado
            enhanced_image = self._advanced_preprocessing(image)
            
            # 3. Detectar regiones de texto
            text_regions = self._detect_text_regions(enhanced_image)
            
            # 4. OCR por regiones si se detectaron, sino OCR global
            if text_regions:
                combined_text = self._ocr_by_regions(enhanced_image, text_regions)
                method = 'advanced_ocr_by_regions'
            else:
                combined_text = self._ocr_global_enhanced(enhanced_image)
                method = 'advanced_ocr_global'
            
            # 5. Calcular confianza
            confidence = self._calculate_ocr_confidence(enhanced_image, combined_text)
            
            return {
                'text': combined_text,
                'confidence': confidence,
                'page_number': page_number,
                'method': method,
                'text_regions_count': len(text_regions),
                'pdf_type': pdf_type['type']
            }
            
        except Exception as e:
            logger.error(f"❌ Error en OCR avanzado: {str(e)}")
            # Fallback a OCR básico
            return self._extract_with_enhanced_ocr(page, page_number)
    
    def _ocr_by_regions(self, image: Image.Image, text_regions: List[Dict]) -> str:
        """OCR por regiones detectadas"""
        try:
            texts = []
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            for region in text_regions:
                x1, y1, x2, y2 = region["bbox"]
                
                # Recortar región
                roi = cv_image[y1:y2, x1:x2]
                roi_pil = Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
                
                # OCR en la región
                try:
                    text = pytesseract.image_to_string(roi_pil, config=self.tesseract_config)
                    if text.strip():
                        texts.append(text.strip())
                except:
                    continue
            
            return '\n'.join(texts)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en OCR por regiones: {str(e)}")
            return self._ocr_global_enhanced(image)
    
    def _ocr_global_enhanced(self, image: Image.Image) -> str:
        """OCR global mejorado con múltiples configuraciones"""
        try:
            texts = []
            
            # Configuraciones optimizadas
            configs = [
                '--oem 3 --psm 6 -l spa',  # Estándar
                '--oem 3 --psm 8 -l spa',  # Una palabra
                '--oem 3 --psm 7 -l spa',  # Una línea
                '--oem 3 --psm 11 -l spa', # Texto disperso
                '--oem 3 --psm 3 -l spa'   # Automático
            ]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, config=config)
                    if text.strip():
                        texts.append(text.strip())
                except:
                    continue
            
            # Combinar resultados únicos
            return self._combine_ocr_texts(texts)
            
        except Exception as e:
            logger.warning(f"⚠️ Error en OCR global mejorado: {str(e)}")
            return ""
    
    def _calculate_ocr_confidence(self, image: Image.Image, text: str) -> float:
        """Calcular confianza del OCR"""
        try:
            if not text.strip():
                return 0.0
            
            # Obtener datos de confianza de Tesseract
            try:
                data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    return min(1.0, avg_confidence / 100.0)
            except:
                pass
            
            # Fallback: confianza basada en longitud del texto
            text_length = len(text.strip())
            if text_length > 100:
                return 0.8
            elif text_length > 50:
                return 0.6
            else:
                return 0.4
                
        except Exception as e:
            logger.warning(f"⚠️ Error calculando confianza OCR: {str(e)}")
            return 0.5
    
    def _extract_with_enhanced_ocr(self, page, page_number: int) -> Dict[str, Any]:
        """Extraer texto usando OCR mejorado con preprocesamiento de imagen (método original)"""
        
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
