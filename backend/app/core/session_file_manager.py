"""
Gestor de archivos por sesión con limpieza automática.
Maneja carpetas únicas por sesión y limpieza automática de archivos.
"""

import os
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import time

logger = logging.getLogger(__name__)

class SessionFileManager:
    """Gestor de archivos por sesión con limpieza automática."""
    
    def __init__(self, upload_base_path: str = "uploads", cleanup_interval_minutes: int = 15):
        """
        Inicializar el gestor de sesiones.
        
        Args:
            upload_base_path: Ruta base para uploads
            cleanup_interval_minutes: Intervalo de limpieza en minutos
        """
        self.upload_base_path = Path(upload_base_path)
        self.upload_base_path.mkdir(exist_ok=True)
        
        self.cleanup_interval = cleanup_interval_minutes
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.cleanup_thread = None
        self.cleanup_running = False
        
        # Iniciar limpieza automática en segundo plano
        self.start_cleanup_scheduler()
        
        logger.info(f"SessionFileManager inicializado - Limpieza cada {cleanup_interval_minutes} minutos")
    
    def create_session(self, user_id: str = None) -> str:
        """
        Crear una nueva sesión única.
        
        Args:
            user_id: ID del usuario (opcional)
            
        Returns:
            ID de la sesión creada
        """
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session_path = self.upload_base_path / session_id
        session_path.mkdir(exist_ok=True)
        
        # Registrar sesión
        self.sessions[session_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'session_path': str(session_path),
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'files_count': 0,
            'files': []
        }
        
        logger.info(f"Sesión creada: {session_id} en {session_path}")
        return session_id
    
    def get_session_path(self, session_id: str) -> Optional[Path]:
        """
        Obtener la ruta de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Ruta de la sesión o None si no existe
        """
        if session_id in self.sessions:
            self.sessions[session_id]['last_accessed'] = datetime.now()
            return Path(self.sessions[session_id]['session_path'])
        return None
    
    def add_file_to_session(self, session_id: str, filename: str, file_path: str, file_type: str = None) -> bool:
        """
        Agregar un archivo a una sesión.
        
        Args:
            session_id: ID de la sesión
            filename: Nombre del archivo
            file_path: Ruta del archivo
            file_type: Tipo de archivo (memoria/plano)
            
        Returns:
            True si se agregó correctamente
        """
        if session_id not in self.sessions:
            logger.error(f"Sesión no encontrada: {session_id}")
            return False
        
        # Actualizar información de la sesión
        self.sessions[session_id]['files_count'] += 1
        self.sessions[session_id]['files'].append({
            'filename': filename,
            'file_path': file_path,
            'file_type': file_type,
            'added_at': datetime.now()
        })
        self.sessions[session_id]['last_accessed'] = datetime.now()
        
        logger.info(f"Archivo agregado a sesión {session_id}: {filename}")
        return True
    
    def get_session_files(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Obtener archivos de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Lista de archivos de la sesión
        """
        if session_id not in self.sessions:
            return []
        
        self.sessions[session_id]['last_accessed'] = datetime.now()
        return self.sessions[session_id]['files']
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Limpiar una sesión específica.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            True si se limpió correctamente
        """
        if session_id not in self.sessions:
            return False
        
        try:
            session_path = Path(self.sessions[session_id]['session_path'])
            
            # Eliminar archivos
            if session_path.exists():
                for file_path in session_path.glob("*"):
                    if file_path.is_file():
                        file_path.unlink()
                        logger.info(f"Archivo eliminado: {file_path}")
                
                # Eliminar directorio
                session_path.rmdir()
                logger.info(f"Directorio eliminado: {session_path}")
            
            # Remover de sesiones activas
            del self.sessions[session_id]
            
            logger.info(f"Sesión limpiada: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error limpiando sesión {session_id}: {e}")
            return False
    
    def cleanup_old_sessions(self) -> int:
        """
        Limpiar sesiones antiguas.
        
        Returns:
            Número de sesiones limpiadas
        """
        now = datetime.now()
        sessions_to_cleanup = []
        
        for session_id, session_data in self.sessions.items():
            # Limpiar sesiones que no se han accedido en el intervalo de limpieza
            time_since_last_access = now - session_data['last_accessed']
            if time_since_last_access >= timedelta(minutes=self.cleanup_interval):
                sessions_to_cleanup.append(session_id)
        
        # Limpiar sesiones
        cleaned_count = 0
        for session_id in sessions_to_cleanup:
            if self.cleanup_session(session_id):
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Limpieza automática: {cleaned_count} sesiones eliminadas")
        
        return cleaned_count
    
    def start_cleanup_scheduler(self):
        """Iniciar el programador de limpieza automática."""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        self.cleanup_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        logger.info("Programador de limpieza automática iniciado")
    
    def stop_cleanup_scheduler(self):
        """Detener el programador de limpieza automática."""
        self.cleanup_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Programador de limpieza automática detenido")
    
    def _cleanup_worker(self):
        """Worker para limpieza automática en segundo plano."""
        while self.cleanup_running:
            try:
                time.sleep(60)  # Verificar cada minuto
                if self.cleanup_running:
                    self.cleanup_old_sessions()
            except Exception as e:
                logger.error(f"Error en worker de limpieza: {e}")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Información de la sesión
        """
        if session_id not in self.sessions:
            return None
        
        session_data = self.sessions[session_id].copy()
        session_data['age_minutes'] = (datetime.now() - session_data['created_at']).total_seconds() / 60
        session_data['last_accessed_minutes_ago'] = (datetime.now() - session_data['last_accessed']).total_seconds() / 60
        
        # Convertir datetime a string para serialización JSON
        session_data['created_at'] = session_data['created_at'].isoformat()
        session_data['last_accessed'] = session_data['last_accessed'].isoformat()
        
        # Convertir datetime en archivos también
        if 'files' in session_data:
            for file_info in session_data['files']:
                if 'added_at' in file_info and isinstance(file_info['added_at'], datetime):
                    file_info['added_at'] = file_info['added_at'].isoformat()
        
        return session_data
    
    def get_all_sessions_info(self) -> Dict[str, Any]:
        """
        Obtener información de todas las sesiones.
        
        Returns:
            Información de todas las sesiones
        """
        sessions_info = {}
        for session_id in self.sessions:
            sessions_info[session_id] = self.get_session_info(session_id)
        
        return {
            'total_sessions': len(self.sessions),
            'cleanup_interval_minutes': self.cleanup_interval,
            'sessions': sessions_info
        }
    
    def force_cleanup_all_sessions(self) -> int:
        """
        Forzar limpieza de todas las sesiones.
        
        Returns:
            Número de sesiones limpiadas
        """
        session_ids = list(self.sessions.keys())
        cleaned_count = 0
        
        for session_id in session_ids:
            if self.cleanup_session(session_id):
                cleaned_count += 1
        
        logger.info(f"Limpieza forzada: {cleaned_count} sesiones eliminadas")
        return cleaned_count

# Instancia global del gestor de sesiones
session_file_manager = SessionFileManager(cleanup_interval_minutes=15)
