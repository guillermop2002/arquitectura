"""
Gestor de limpieza automática de disco para el sistema de verificación arquitectónica.
Maneja la limpieza automática de archivos temporales y sesiones expiradas.
"""

import os
import shutil
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import psutil

logger = logging.getLogger(__name__)

class DiskCleanupManager:
    """Gestor de limpieza automática de disco."""
    
    def __init__(self, 
                 uploads_dir: str = "uploads",
                 temp_dir: str = "temp", 
                 logs_dir: str = "logs",
                 analysis_results_dir: str = "analysis_results",
                 max_disk_usage: float = 80.0,  # Porcentaje máximo de uso de disco (más agresivo)
                 cleanup_interval: int = 1800,  # Intervalo de limpieza en segundos (30 minutos)
                 session_ttl: int = 3600):  # TTL de sesiones en segundos (1 hora)
        """
        Inicializar el gestor de limpieza de disco.
        
        Args:
            uploads_dir: Directorio de archivos subidos
            temp_dir: Directorio de archivos temporales
            logs_dir: Directorio de logs
            analysis_results_dir: Directorio de resultados de análisis
            max_disk_usage: Porcentaje máximo de uso de disco antes de limpiar
            cleanup_interval: Intervalo de limpieza en segundos
            session_ttl: TTL de sesiones en segundos
        """
        self.uploads_dir = Path(uploads_dir)
        self.temp_dir = Path(temp_dir)
        self.logs_dir = Path(logs_dir)
        self.analysis_results_dir = Path(analysis_results_dir)
        self.max_disk_usage = max_disk_usage
        self.cleanup_interval = cleanup_interval
        self.session_ttl = session_ttl
        
        # Crear directorios si no existen
        for directory in [self.uploads_dir, self.temp_dir, self.logs_dir, self.analysis_results_dir]:
            directory.mkdir(exist_ok=True, mode=0o755)
        
        # Iniciar limpieza automática
        self._start_cleanup_thread()
        
        logger.info("DiskCleanupManager initialized")
    
    def _start_cleanup_thread(self):
        """Iniciar hilo de limpieza automática."""
        def cleanup_worker():
            while True:
                try:
                    self.cleanup_all()
                    time.sleep(self.cleanup_interval)
                except Exception as e:
                    logger.error(f"Error en limpieza automática: {e}")
                    time.sleep(300)  # Esperar 5 minutos antes de reintentar
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Hilo de limpieza automática iniciado")
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """
        Obtener información de uso de disco.
        
        Returns:
            Diccionario con información de uso de disco
        """
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': disk_usage.percent,
                'is_critical': disk_usage.percent > self.max_disk_usage
            }
        except Exception as e:
            logger.error(f"Error obteniendo uso de disco: {e}")
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0, 'is_critical': False}
    
    def cleanup_sessions(self) -> Dict[str, Any]:
        """
        Limpiar sesiones expiradas.
        
        Returns:
            Diccionario con información de limpieza
        """
        cleaned_sessions = 0
        freed_space = 0
        
        try:
            if not self.uploads_dir.exists():
                return {'cleaned_sessions': 0, 'freed_space': 0}
            
            current_time = time.time()
            cutoff_time = current_time - self.session_ttl
            
            for session_dir in self.uploads_dir.iterdir():
                if session_dir.is_dir() and session_dir.name.startswith('session_'):
                    try:
                        # Verificar si la sesión ha expirado
                        session_time = session_dir.stat().st_mtime
                        if session_time < cutoff_time:
                            # Calcular espacio a liberar
                            session_size = sum(f.stat().st_size for f in session_dir.rglob('*') if f.is_file())
                            
                            # Eliminar directorio de sesión
                            shutil.rmtree(session_dir)
                            
                            cleaned_sessions += 1
                            freed_space += session_size
                            
                            logger.info(f"Sesión expirada eliminada: {session_dir.name} ({session_size} bytes)")
                    
                    except Exception as e:
                        logger.error(f"Error limpiando sesión {session_dir.name}: {e}")
            
            logger.info(f"Limpieza de sesiones: {cleaned_sessions} sesiones, {freed_space} bytes liberados")
            return {'cleaned_sessions': cleaned_sessions, 'freed_space': freed_space}
            
        except Exception as e:
            logger.error(f"Error en limpieza de sesiones: {e}")
            return {'cleaned_sessions': 0, 'freed_space': 0}
    
    def cleanup_temp_files(self) -> Dict[str, Any]:
        """
        Limpiar archivos temporales.
        
        Returns:
            Diccionario con información de limpieza
        """
        cleaned_files = 0
        freed_space = 0
        
        try:
            if not self.temp_dir.exists():
                return {'cleaned_files': 0, 'freed_space': 0}
            
            current_time = time.time()
            cutoff_time = current_time - 1800  # 30 minutos
            
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_time = file_path.stat().st_mtime
                        if file_time < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            
                            cleaned_files += 1
                            freed_space += file_size
                            
                    except Exception as e:
                        logger.error(f"Error eliminando archivo temporal {file_path}: {e}")
            
            logger.info(f"Limpieza de archivos temporales: {cleaned_files} archivos, {freed_space} bytes liberados")
            return {'cleaned_files': cleaned_files, 'freed_space': freed_space}
            
        except Exception as e:
            logger.error(f"Error en limpieza de archivos temporales: {e}")
            return {'cleaned_files': 0, 'freed_space': 0}
    
    def cleanup_old_logs(self) -> Dict[str, Any]:
        """
        Limpiar logs antiguos.
        
        Returns:
            Diccionario con información de limpieza
        """
        cleaned_files = 0
        freed_space = 0
        
        try:
            if not self.logs_dir.exists():
                return {'cleaned_files': 0, 'freed_space': 0}
            
            current_time = time.time()
            cutoff_time = current_time - 3600  # 1 hora
            
            for file_path in self.logs_dir.rglob('*.log'):
                try:
                    file_time = file_path.stat().st_mtime
                    if file_time < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        
                        cleaned_files += 1
                        freed_space += file_size
                        
                except Exception as e:
                    logger.error(f"Error eliminando log {file_path}: {e}")
            
            logger.info(f"Limpieza de logs: {cleaned_files} archivos, {freed_space} bytes liberados")
            return {'cleaned_files': cleaned_files, 'freed_space': freed_space}
            
        except Exception as e:
            logger.error(f"Error en limpieza de logs: {e}")
            return {'cleaned_files': 0, 'freed_space': 0}
    
    def cleanup_analysis_results(self) -> Dict[str, Any]:
        """
        Limpiar resultados de análisis antiguos.
        
        Returns:
            Diccionario con información de limpieza
        """
        cleaned_files = 0
        freed_space = 0
        
        try:
            if not self.analysis_results_dir.exists():
                return {'cleaned_files': 0, 'freed_space': 0}
            
            current_time = time.time()
            cutoff_time = current_time - (12 * 3600)  # 12 horas
            
            for file_path in self.analysis_results_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_time = file_path.stat().st_mtime
                        if file_time < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            
                            cleaned_files += 1
                            freed_space += file_size
                            
                    except Exception as e:
                        logger.error(f"Error eliminando resultado {file_path}: {e}")
            
            logger.info(f"Limpieza de resultados: {cleaned_files} archivos, {freed_space} bytes liberados")
            return {'cleaned_files': cleaned_files, 'freed_space': freed_space}
            
        except Exception as e:
            logger.error(f"Error en limpieza de resultados: {e}")
            return {'cleaned_files': 0, 'freed_space': 0}
    
    def cleanup_all(self) -> Dict[str, Any]:
        """
        Ejecutar limpieza completa del sistema.
        
        Returns:
            Diccionario con información de limpieza completa
        """
        logger.info("Iniciando limpieza completa del sistema")
        
        # Obtener uso de disco
        disk_usage = self.get_disk_usage()
        
        # Ejecutar limpiezas
        sessions_cleanup = self.cleanup_sessions()
        temp_cleanup = self.cleanup_temp_files()
        logs_cleanup = self.cleanup_old_logs()
        results_cleanup = self.cleanup_analysis_results()
        
        # Calcular totales
        total_cleaned_files = (sessions_cleanup['cleaned_sessions'] + 
                              temp_cleanup['cleaned_files'] + 
                              logs_cleanup['cleaned_files'] + 
                              results_cleanup['cleaned_files'])
        
        total_freed_space = (sessions_cleanup['freed_space'] + 
                            temp_cleanup['freed_space'] + 
                            logs_cleanup['freed_space'] + 
                            results_cleanup['freed_space'])
        
        cleanup_info = {
            'disk_usage_before': disk_usage,
            'sessions_cleanup': sessions_cleanup,
            'temp_cleanup': temp_cleanup,
            'logs_cleanup': logs_cleanup,
            'results_cleanup': results_cleanup,
            'total_cleaned_files': total_cleaned_files,
            'total_freed_space': total_freed_space,
            'cleanup_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Limpieza completa finalizada: {total_cleaned_files} elementos, {total_freed_space} bytes liberados")
        
        return cleanup_info
    
    def force_cleanup(self) -> Dict[str, Any]:
        """
        Forzar limpieza inmediata (usar cuando el disco esté lleno).
        
        Returns:
            Diccionario con información de limpieza
        """
        logger.warning("Ejecutando limpieza forzada del sistema")
        
        # Limpiar todo inmediatamente
        return self.cleanup_all()
    
    def get_cleanup_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual del sistema de limpieza.
        
        Returns:
            Diccionario con estado del sistema
        """
        disk_usage = self.get_disk_usage()
        
        # Contar archivos en cada directorio
        uploads_count = len(list(self.uploads_dir.rglob('*'))) if self.uploads_dir.exists() else 0
        temp_count = len(list(self.temp_dir.rglob('*'))) if self.temp_dir.exists() else 0
        logs_count = len(list(self.logs_dir.rglob('*.log'))) if self.logs_dir.exists() else 0
        results_count = len(list(self.analysis_results_dir.rglob('*'))) if self.analysis_results_dir.exists() else 0
        
        return {
            'disk_usage': disk_usage,
            'files_count': {
                'uploads': uploads_count,
                'temp': temp_count,
                'logs': logs_count,
                'results': results_count
            },
            'cleanup_interval': self.cleanup_interval,
            'session_ttl': self.session_ttl,
            'max_disk_usage': self.max_disk_usage
        }
