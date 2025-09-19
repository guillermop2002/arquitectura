"""
Gestor de estado para la aplicación.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class StateManager:
    """Gestor de estado del sistema."""
    
    def __init__(self, state_file: str = "state.json"):
        """
        Inicializar el gestor de estado.
        
        Args:
            state_file: Archivo de estado
        """
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.StateManager")
        self._lock = threading.Lock()
        self._state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Cargar estado desde archivo."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                self.logger.info("Estado cargado desde archivo")
                return state
            else:
                self.logger.info("Creando nuevo estado")
                return self._create_initial_state()
        except Exception as e:
            self.logger.error(f"Error cargando estado: {e}")
            return self._create_initial_state()
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """Crear estado inicial."""
        return {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "active_projects": {},
            "system_status": {
                "initialized": True,
                "last_health_check": None,
                "error_count": 0
            },
            "settings": {
                "auto_save": True,
                "backup_enabled": True,
                "max_projects": 100
            }
        }
    
    def _save_state(self) -> bool:
        """Guardar estado en archivo."""
        try:
            with self._lock:
                self._state["last_updated"] = datetime.now().isoformat()
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(self._state, f, indent=2, ensure_ascii=False)
                self.logger.debug("Estado guardado")
                return True
        except Exception as e:
            self.logger.error(f"Error guardando estado: {e}")
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """Obtener estado actual."""
        with self._lock:
            return self._state.copy()
    
    def update_state(self, updates: Dict[str, Any]) -> bool:
        """
        Actualizar estado.
        
        Args:
            updates: Actualizaciones a aplicar
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            with self._lock:
                self._state.update(updates)
                return self._save_state()
        except Exception as e:
            self.logger.error(f"Error actualizando estado: {e}")
            return False
    
    def add_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """
        Agregar proyecto al estado.
        
        Args:
            project_id: ID del proyecto
            project_data: Datos del proyecto
            
        Returns:
            True si se agregó correctamente
        """
        try:
            with self._lock:
                if len(self._state["active_projects"]) >= self._state["settings"]["max_projects"]:
                    self.logger.warning("Límite de proyectos alcanzado")
                    return False
                
                self._state["active_projects"][project_id] = {
                    "data": project_data,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "status": "active"
                }
                
                self.logger.info(f"Proyecto {project_id} agregado al estado")
                return self._save_state()
        except Exception as e:
            self.logger.error(f"Error agregando proyecto {project_id}: {e}")
            return False
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener proyecto del estado.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Datos del proyecto o None si no existe
        """
        with self._lock:
            return self._state["active_projects"].get(project_id)
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """
        Actualizar proyecto en el estado.
        
        Args:
            project_id: ID del proyecto
            updates: Actualizaciones a aplicar
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            with self._lock:
                if project_id not in self._state["active_projects"]:
                    self.logger.warning(f"Proyecto {project_id} no encontrado")
                    return False
                
                self._state["active_projects"][project_id].update(updates)
                self._state["active_projects"][project_id]["last_updated"] = datetime.now().isoformat()
                
                self.logger.info(f"Proyecto {project_id} actualizado")
                return self._save_state()
        except Exception as e:
            self.logger.error(f"Error actualizando proyecto {project_id}: {e}")
            return False
    
    def remove_project(self, project_id: str) -> bool:
        """
        Eliminar proyecto del estado.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            with self._lock:
                if project_id in self._state["active_projects"]:
                    del self._state["active_projects"][project_id]
                    self.logger.info(f"Proyecto {project_id} eliminado del estado")
                    return self._save_state()
                else:
                    self.logger.warning(f"Proyecto {project_id} no encontrado para eliminar")
                    return False
        except Exception as e:
            self.logger.error(f"Error eliminando proyecto {project_id}: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificar el estado de salud del StateManager.
        
        Returns:
            Estado de salud del sistema
        """
        try:
            with self._lock:
                return {
                    "status": "ok",
                    "active_projects": len(self._state["active_projects"]),
                    "last_updated": self._state["last_updated"],
                    "version": self._state["version"]
                }
        except Exception as e:
            self.logger.error(f"Error en health check: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_active_projects(self) -> List[str]:
        """Obtener lista de proyectos activos."""
        with self._lock:
            return list(self._state["active_projects"].keys())
    
    def cleanup_old_projects(self, max_age_hours: int = 24) -> int:
        """
        Limpiar proyectos antiguos.
        
        Args:
            max_age_hours: Edad máxima en horas
            
        Returns:
            Número de proyectos eliminados
        """
        try:
            with self._lock:
                current_time = datetime.now()
                max_age = timedelta(hours=max_age_hours)
                projects_to_remove = []
                
                for project_id, project_data in self._state["active_projects"].items():
                    last_updated = datetime.fromisoformat(project_data["last_updated"])
                    if current_time - last_updated > max_age:
                        projects_to_remove.append(project_id)
                
                for project_id in projects_to_remove:
                    del self._state["active_projects"][project_id]
                
                if projects_to_remove:
                    self.logger.info(f"Eliminados {len(projects_to_remove)} proyectos antiguos")
                    self._save_state()
                
                return len(projects_to_remove)
        except Exception as e:
            self.logger.error(f"Error limpiando proyectos antiguos: {e}")
            return 0
    
    def update_system_status(self, status_updates: Dict[str, Any]) -> bool:
        """
        Actualizar estado del sistema.
        
        Args:
            status_updates: Actualizaciones de estado
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            with self._lock:
                self._state["system_status"].update(status_updates)
                self._state["system_status"]["last_health_check"] = datetime.now().isoformat()
                return self._save_state()
        except Exception as e:
            self.logger.error(f"Error actualizando estado del sistema: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema."""
        with self._lock:
            return self._state["system_status"].copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del estado."""
        try:
            with self._lock:
                active_projects = len(self._state["active_projects"])
                total_errors = self._state["system_status"]["error_count"]
                
                # Calcular edad promedio de proyectos
                current_time = datetime.now()
                project_ages = []
                for project_data in self._state["active_projects"].values():
                    created_at = datetime.fromisoformat(project_data["created_at"])
                    age_hours = (current_time - created_at).total_seconds() / 3600
                    project_ages.append(age_hours)
                
                avg_age_hours = sum(project_ages) / len(project_ages) if project_ages else 0
                
                return {
                    "active_projects": active_projects,
                    "total_errors": total_errors,
                    "average_project_age_hours": round(avg_age_hours, 2),
                    "last_updated": self._state["last_updated"],
                    "state_file_size": self.state_file.stat().st_size if self.state_file.exists() else 0
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def close(self) -> None:
        """
        Cerrar el StateManager y guardar el estado final.
        """
        try:
            with self._lock:
                self._state["last_updated"] = datetime.now().isoformat()
                self._state["system_status"]["last_health_check"] = datetime.now().isoformat()
                self._save_state()
                self.logger.info("StateManager cerrado correctamente")
        except Exception as e:
            self.logger.error(f"Error cerrando StateManager: {e}")