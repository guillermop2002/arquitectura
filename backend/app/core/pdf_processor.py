"""
Procesador de documentos PDF para el sistema de verificación arquitectónica.
Extrae texto, imágenes y metadatos de archivos PDF.
"""

import os
import logging
import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

@dataclass
class PDFPage:
    """Información de una página PDF."""
    page_number: int
    text: str
    images: List[Dict[str, Any]]
    dimensions: Tuple[float, float]  # width, height
    rotation: int
    has_text: bool
    has_images: bool

@dataclass
class PDFDocument:
    """Información completa de un documento PDF."""
    filename: str
    file_path: str
    file_size: int
    page_count: int
    pages: List[PDFPage]
    metadata: Dict[str, Any]
    text_content: str
    images: List[Dict[str, Any]]
    processing_time: float
    file_hash: str

class PDFProcessor:
    """Procesador de documentos PDF."""
    
    def __init__(self, max_pages: int = 100, max_file_size: int = 50 * 1024 * 1024):
        """
        Inicializar el procesador PDF.
        
        Args:
            max_pages: Número máximo de páginas a procesar
            max_file_size: Tamaño máximo de archivo en bytes (50MB por defecto)
        """
        self.max_pages = max_pages
        self.max_file_size = max_file_size
        
        logger.info("PDFProcessor initialized")
    
    def process_pdf(self, file_path: str) -> PDFDocument:
        """
        Procesar un archivo PDF completo.
        
        Args:
            file_path: Ruta del archivo PDF
            
        Returns:
            Documento PDF procesado
        """
        start_time = time.time()
        
        try:
            logger.info(f"Procesando PDF: {file_path}")
            
            # Verificar archivo
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"Archivo demasiado grande: {file_size} bytes")
            
            # Calcular hash del archivo
            file_hash = self._calculate_file_hash(file_path)
            
            # Abrir documento PDF
            doc = fitz.open(file_path)
            
            try:
                # Obtener metadatos
                metadata = doc.metadata
                
                # Procesar páginas
                pages = []
                all_text = ""
                all_images = []
                
                page_count = min(len(doc), self.max_pages)
                
                for page_num in range(page_count):
                    page = doc[page_num]
                    page_info = self._process_page(page, page_num)
                    pages.append(page_info)
                    
                    all_text += f"\n--- PÁGINA {page_num + 1} ---\n{page_info.text}\n"
                    all_images.extend(page_info.images)
                
                processing_time = time.time() - start_time
                
                # Crear documento PDF
                pdf_doc = PDFDocument(
                    filename=Path(file_path).name,
                    file_path=file_path,
                    file_size=file_size,
                    page_count=page_count,
                    pages=pages,
                    metadata=metadata,
                    text_content=all_text,
                    images=all_images,
                    processing_time=processing_time,
                    file_hash=file_hash
                )
                
                logger.info(f"PDF procesado exitosamente: {page_count} páginas, "
                           f"{len(all_images)} imágenes, {processing_time:.2f}s")
                
                return pdf_doc
                
            finally:
                doc.close()
                
        except Exception as e:
            logger.error(f"Error procesando PDF {file_path}: {e}")
            raise
    
    def _process_page(self, page, page_num: int) -> PDFPage:
        """Procesar una página individual del PDF."""
        try:
            # Extraer texto
            text = page.get_text()
            
            # Obtener dimensiones y rotación
            rect = page.rect
            dimensions = (rect.width, rect.height)
            rotation = page.rotation
            
            # Extraer imágenes
            images = self._extract_page_images(page, page_num)
            
            return PDFPage(
                page_number=page_num + 1,
                text=text,
                images=images,
                dimensions=dimensions,
                rotation=rotation,
                has_text=bool(text.strip()),
                has_images=len(images) > 0
            )
            
        except Exception as e:
            logger.error(f"Error procesando página {page_num + 1}: {e}")
            return PDFPage(
                page_number=page_num + 1,
                text="",
                images=[],
                dimensions=(0, 0),
                rotation=0,
                has_text=False,
                has_images=False
            )
    
    def _extract_page_images(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Extraer imágenes de una página."""
        try:
            images = []
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        img_size = len(img_data)
                        
                        # Solo procesar imágenes pequeñas para evitar problemas de memoria
                        if img_size < 1024 * 1024:  # 1MB
                            images.append({
                                'page': page_num + 1,
                                'index': img_index,
                                'xref': xref,
                                'size': img_size,
                                'format': 'png',
                                'data': img_data
                            })
                    
                    pix = None
                    
                except Exception as e:
                    logger.warning(f"Error extrayendo imagen {img_index} de página {page_num + 1}: {e}")
                    continue
            
            return images
            
        except Exception as e:
            logger.error(f"Error extrayendo imágenes de página {page_num + 1}: {e}")
            return []
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcular hash MD5 de un archivo."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_text_only(self, file_path: str) -> str:
        """
        Extraer solo el texto de un PDF (más rápido).
        
        Args:
            file_path: Ruta del archivo PDF
            
        Returns:
            Texto extraído del PDF
        """
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(min(len(doc), self.max_pages)):
                page = doc[page_num]
                text += page.get_text() + "\n"
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de {file_path}: {e}")
            return ""
    
    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtener información básica de un PDF sin procesar completamente.
        
        Args:
            file_path: Ruta del archivo PDF
            
        Returns:
            Información básica del documento
        """
        try:
            doc = fitz.open(file_path)
            
            info = {
                'filename': Path(file_path).name,
                'file_size': os.path.getsize(file_path),
                'page_count': len(doc),
                'metadata': doc.metadata,
                'is_encrypted': doc.is_encrypted,
                'needs_password': doc.needs_pass,
                'file_hash': self._calculate_file_hash(file_path)
            }
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información de {file_path}: {e}")
            return {
                'filename': Path(file_path).name,
                'file_size': 0,
                'page_count': 0,
                'metadata': {},
                'is_encrypted': False,
                'needs_password': False,
                'file_hash': "",
                'error': str(e)
            }
    
    def validate_pdf(self, file_path: str) -> Tuple[bool, str]:
        """
        Validar si un archivo es un PDF válido.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        try:
            if not os.path.exists(file_path):
                return False, "Archivo no encontrado"
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "Archivo vacío"
            
            if file_size > self.max_file_size:
                return False, f"Archivo demasiado grande ({file_size} bytes)"
            
            # Intentar abrir el PDF
            doc = fitz.open(file_path)
            
            if doc.is_encrypted:
                doc.close()
                return False, "PDF encriptado"
            
            if doc.needs_pass:
                doc.close()
                return False, "PDF requiere contraseña"
            
            page_count = len(doc)
            if page_count == 0:
                doc.close()
                return False, "PDF sin páginas"
            
            if page_count > self.max_pages:
                doc.close()
                return False, f"Demasiadas páginas ({page_count})"
            
            doc.close()
            return True, "PDF válido"
            
        except Exception as e:
            return False, f"Error validando PDF: {str(e)}"
    
    def process_multiple_pdfs(self, file_paths: List[str]) -> List[PDFDocument]:
        """
        Procesar múltiples archivos PDF.
        
        Args:
            file_paths: Lista de rutas de archivos
            
        Returns:
            Lista de documentos PDF procesados
        """
        documents = []
        
        for file_path in file_paths:
            try:
                # Validar PDF primero
                is_valid, error_msg = self.validate_pdf(file_path)
                if not is_valid:
                    logger.warning(f"PDF inválido {file_path}: {error_msg}")
                    continue
                
                # Procesar PDF
                doc = self.process_pdf(file_path)
                documents.append(doc)
                
            except Exception as e:
                logger.error(f"Error procesando {file_path}: {e}")
                continue
        
        return documents
