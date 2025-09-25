import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Dict, Any, List
from pathlib import Path

class BasicoOCRProcessor:
    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6 -l spa'
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extraer texto de PDF con OCR inteligente"""
        
        try:
            doc = fitz.open(pdf_path)
            
            full_text = []
            page_texts = []
            total_confidence = 0
            extraction_methods = []
            
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
                    # Usar OCR para imágenes/texto escaneado
                    page_data = self._extract_with_ocr(page, page_num + 1)
                    page_text = page_data['text']
                    extraction_method = 'ocr'
                    confidence = page_data['confidence']
                
                page_texts.append({
                    'page_number': page_num + 1,
                    'text': page_text,
                    'method': extraction_method,
                    'confidence': confidence
                })
                
                full_text.append(f"\n--- Página {page_num + 1} ---\n")
                full_text.append(page_text)
                
                total_confidence += confidence
                extraction_methods.append(extraction_method)
            
            doc.close()
            
            # Calcular estadísticas
            avg_confidence = total_confidence / len(doc) if len(doc) > 0 else 0
            primary_method = max(set(extraction_methods), key=extraction_methods.count)
            
            return {
                'full_text': '\n'.join(full_text),
                'page_texts': page_texts,
                'total_pages': len(doc),
                'extraction_method': primary_method,
                'confidence': avg_confidence,
                'file_path': pdf_path
            }
            
        except Exception as e:
            return {
                'full_text': '',
                'page_texts': [],
                'total_pages': 0,
                'extraction_method': 'error',
                'confidence': 0.0,
                'error': str(e),
                'file_path': pdf_path
            }
    
    def _extract_with_ocr(self, page, page_number: int) -> Dict[str, Any]:
        """Extraer texto usando OCR"""
        
        try:
            # Convertir página a imagen
            mat = fitz.Matrix(2.0, 2.0)  # Escalar 2x para mejor OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Procesar con Tesseract
            image = Image.open(io.BytesIO(img_data))
            
            # Extraer texto
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            # Obtener datos de confianza
            try:
                data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence = avg_confidence / 100.0  # Normalizar a 0-1
            except:
                confidence = 0.7  # Confianza por defecto
            
            return {
                'text': text,
                'confidence': confidence,
                'page_number': page_number,
                'method': 'tesseract_ocr'
            }
            
        except Exception as e:
            return {
                'text': '',
                'confidence': 0.0,
                'page_number': page_number,
                'method': 'ocr_error',
                'error': str(e)
            }
    
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
