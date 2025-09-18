"""
Gestor de archivos para la aplicación.
"""
import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos del sistema."""
    
    def __init__(self, base_path: str = "."):
        """
        Inicializar el gestor de archivos.
        
        Args:
            base_path: Directorio base para archivos
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Directorios específicos
        self.uploads_dir = self.base_path / "uploads"
        self.temp_dir = self.base_path / "temp"
        self.reports_dir = self.base_path / "reports"
        self.analysis_dir = self.base_path / "analysis_results"
        
        # Crear directorios si no existen
        for directory in [self.uploads_dir, self.temp_dir, self.reports_dir, self.analysis_dir]:
            directory.mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, subdirectory: str = "uploads") -> Dict[str, Any]:
        """
        Guardar un archivo en el sistema.
        
        Args:
            file_content: Contenido del archivo
            filename: Nombre del archivo
            subdirectory: Subdirectorio donde guardar
            
        Returns:
            Información del archivo guardado
        """
        try:
            # Determinar directorio de destino
            target_dir = self.base_path / subdirectory
            target_dir.mkdir(exist_ok=True)
            
            # Generar nombre único si el archivo ya existe
            file_path = target_dir / filename
            counter = 1
            while file_path.exists():
                name, ext = os.path.splitext(filename)
                file_path = target_dir / f"{name}_{counter}{ext}"
                counter += 1
            
            # Guardar archivo
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Calcular hash del archivo
            file_hash = self._calculate_file_hash(file_path)
            
            # Información del archivo
            file_info = {
                "filename": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "hash": file_hash,
                "subdirectory": subdirectory
            }
            
            logger.info(f"Archivo guardado: {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error guardando archivo {filename}: {e}")
            raise
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Obtener contenido de un archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Contenido del archivo o None si no existe
        """
        try:
            path = Path(file_path)
            if path.exists():
                with open(path, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Error obteniendo archivo {file_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Eliminar un archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Archivo eliminado: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando archivo {file_path}: {e}")
            return False
    
    def list_files(self, subdirectory: str = "uploads") -> List[Dict[str, Any]]:
        """
        Listar archivos en un subdirectorio.
        
        Args:
            subdirectory: Subdirectorio a listar
            
        Returns:
            Lista de información de archivos
        """
        try:
            target_dir = self.base_path / subdirectory
            if not target_dir.exists():
                return []
            
            files = []
            for file_path in target_dir.iterdir():
                if file_path.is_file():
                    files.append({
                        "filename": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
            
            return files
        except Exception as e:
            logger.error(f"Error listando archivos en {subdirectory}: {e}")
            return []
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Limpiar archivos temporales antiguos.
        
        Args:
            max_age_hours: Edad máxima en horas
            
        Returns:
            Número de archivos eliminados
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            deleted_count = 0
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Archivo temporal eliminado: {file_path}")
            
            logger.info(f"Limpieza completada: {deleted_count} archivos eliminados")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error en limpieza de archivos temporales: {e}")
            return 0
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcular hash MD5 de un archivo."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Obtener información del almacenamiento.
        
        Returns:
            Información del almacenamiento
        """
        try:
            total_size = 0
            file_count = 0
            
            for directory in [self.uploads_dir, self.temp_dir, self.reports_dir, self.analysis_dir]:
                if directory.exists():
                    for file_path in directory.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
            
            return {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "directories": {
                    "uploads": str(self.uploads_dir),
                    "temp": str(self.temp_dir),
                    "reports": str(self.reports_dir),
                    "analysis": str(self.analysis_dir)
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo información de almacenamiento: {e}")
            return {}
    
    async def process_uploaded_files(self, files: List[Any], job_id: str, is_existing_building: bool) -> Dict[str, Any]:
        """
        Procesar archivos subidos con clasificación automática.
        
        Args:
            files: Lista de archivos subidos
            job_id: ID del trabajo
            is_existing_building: Si es edificio existente
            
        Returns:
            Datos extraídos de los archivos
        """
        try:
            logger.info(f"Procesando {len(files)} archivos para trabajo {job_id}")
            
            # Crear directorio del trabajo
            job_dir = self.temp_dir / job_id
            job_dir.mkdir(exist_ok=True)
            
            # Importar procesadores
            from .pdf_processor import PDFProcessor
            from .document_classifier import DocumentClassifier
            from .document_analyzer import DocumentAnalyzer
            from .ai_client import AIClient
            
            # Inicializar procesadores
            pdf_processor = PDFProcessor()
            ai_client = AIClient()
            classifier = DocumentClassifier(ai_client)
            analyzer = DocumentAnalyzer()
            
            # Procesar archivos
            processed_files = []
            extracted_data = {}
            
            for file in files:
                try:
                    # Guardar archivo
                    file_path = job_dir / file.filename
                    with open(file_path, 'wb') as f:
                        f.write(await file.read())
                    
                    # Procesar PDF
                    pdf_doc = pdf_processor.process_pdf(str(file_path))
                    
                    # Clasificar documento
                    classification = await classifier.classify_document(str(file_path))
                    
                    # Analizar contenido
                    content = analyzer.analyze_document(pdf_doc, classification)
                    
                    # Guardar resultados
                    file_result = {
                        'filename': file.filename,
                        'file_path': str(file_path),
                        'classification': classification,
                        'content': content,
                        'pdf_document': pdf_doc
                    }
                    
                    processed_files.append(file_result)
                    extracted_data[file.filename] = file_result
                    
                    logger.info(f"Archivo procesado: {file.filename} - {classification.document_type}")
                    
                except Exception as e:
                    logger.error(f"Error procesando archivo {file.filename}: {e}")
                    continue
            
            # Crear resumen del procesamiento
            summary = {
                'total_files': len(files),
                'processed_files': len(processed_files),
                'memoria_files': [f for f in processed_files if f['classification'].document_type == 'memoria'],
                'plano_files': [f for f in processed_files if f['classification'].document_type == 'plano'],
                'processing_complete': True,
                'job_id': job_id,
                'is_existing_building': is_existing_building
            }
            
            # Guardar datos del trabajo
            await self.update_job_data(job_id, {
                'extracted_data': extracted_data,
                'summary': summary,
                'processing_complete': True,
                'created_at': datetime.now().isoformat()
            })
            
            return {
                'extracted_data': extracted_data,
                'summary': summary,
                'job_id': job_id
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivos: {e}")
            raise
    
    async def update_job_data(self, job_id: str, data: Dict[str, Any]) -> bool:
        """
        Actualizar datos de un trabajo.
        
        Args:
            job_id: ID del trabajo
            data: Datos a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            job_file = self.temp_dir / job_id / 'job_data.json'
            
            # Cargar datos existentes
            existing_data = {}
            if job_file.exists():
                with open(job_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Actualizar datos
            existing_data.update(data)
            existing_data['updated_at'] = datetime.now().isoformat()
            
            # Guardar datos actualizados
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando datos del trabajo {job_id}: {e}")
            return False
    
    async def get_job_data(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos de un trabajo.
        
        Args:
            job_id: ID del trabajo
            
        Returns:
            Datos del trabajo o None si no existe
        """
        try:
            job_file = self.temp_dir / job_id / 'job_data.json'
            
            if not job_file.exists():
                return None
            
            with open(job_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error obteniendo datos del trabajo {job_id}: {e}")
            return None