"""
Gestor de limpieza de archivos temporales.
Limpia automáticamente archivos PDF subidos después de 2 horas.
"""

import os
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileCleanupManager:
    """Gestor de limpieza de archivos temporales."""
    
    def __init__(self, upload_dir: str = "uploads", temp_dir: str = "temp"):
        self.upload_dir = Path(upload_dir)
        self.temp_dir = Path(temp_dir)
        self.file_timestamps: Dict[str, float] = {}
        self.cleanup_interval = 3600  # 1 hora
        self.file_lifetime = 7200  # 2 horas
        
        # Crear directorios si no existen
        self.upload_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"FileCleanupManager inicializado - Upload: {self.upload_dir}, Temp: {self.temp_dir}")
    
    def register_file(self, filename: str, file_path: str = None) -> str:
        """
        Registra un archivo para limpieza automática.
        
        Args:
            filename: Nombre del archivo
            file_path: Ruta del archivo (opcional)
            
        Returns:
            Ruta completa del archivo
        """
        if file_path is None:
            file_path = str(self.upload_dir / filename)
        
        # Registrar timestamp
        self.file_timestamps[file_path] = time.time()
        
        logger.info(f"Archivo registrado para limpieza: {file_path}")
        return file_path
    
    def cleanup_expired_files(self):
        """Limpia archivos que han expirado."""
        current_time = time.time()
        files_to_remove = []
        
        # Verificar archivos registrados
        for file_path, timestamp in list(self.file_timestamps.items()):
            if current_time - timestamp > self.file_lifetime:
                files_to_remove.append(file_path)
        
        # Limpiar archivos registrados
        for file_path in files_to_remove:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Archivo expirado eliminado: {file_path}")
                del self.file_timestamps[file_path]
            except Exception as e:
                logger.error(f"Error eliminando archivo {file_path}: {e}")
        
        # Limpiar archivos huérfanos en directorios
        self._cleanup_orphaned_files()
        
        logger.info(f"Limpieza completada: {len(files_to_remove)} archivos eliminados")
    
    def _cleanup_orphaned_files(self):
        """Limpia archivos huérfanos en los directorios."""
        current_time = time.time()
        
        # Limpiar uploads
        for file_path in self.upload_dir.glob("*.pdf"):
            try:
                file_mtime = os.path.getmtime(file_path)
                if current_time - file_mtime > self.file_lifetime:
                    file_path.unlink()
                    logger.info(f"Archivo huérfano eliminado: {file_path}")
            except Exception as e:
                logger.error(f"Error eliminando archivo huérfano {file_path}: {e}")
        
        # Limpiar temp
        for file_path in self.temp_dir.glob("*"):
            try:
                file_mtime = os.path.getmtime(file_path)
                if current_time - file_mtime > self.file_lifetime:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        import shutil
                        shutil.rmtree(file_path)
                    logger.info(f"Archivo/directorio temporal eliminado: {file_path}")
            except Exception as e:
                logger.error(f"Error eliminando archivo temporal {file_path}: {e}")
    
    def get_file_info(self) -> Dict[str, Any]:
        """Obtiene información sobre archivos registrados."""
        current_time = time.time()
        
        return {
            "total_files": len(self.file_timestamps),
            "files": [
                {
                    "path": file_path,
                    "age_seconds": current_time - timestamp,
                    "age_hours": (current_time - timestamp) / 3600,
                    "expires_in_hours": (self.file_lifetime - (current_time - timestamp)) / 3600
                }
                for file_path, timestamp in self.file_timestamps.items()
            ],
            "upload_dir_size": self._get_directory_size(self.upload_dir),
            "temp_dir_size": self._get_directory_size(self.temp_dir)
        }
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calcula el tamaño total de un directorio."""
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"Error calculando tamaño de {directory}: {e}")
        return total_size
    
    async def start_cleanup_scheduler(self):
        """Inicia el planificador de limpieza automática."""
        logger.info("Iniciando planificador de limpieza automática")
        
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_expired_files()
            except Exception as e:
                logger.error(f"Error en planificador de limpieza: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar

# Instancia global
file_cleanup_manager = FileCleanupManager()
