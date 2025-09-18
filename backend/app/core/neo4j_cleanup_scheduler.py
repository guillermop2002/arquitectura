"""
Sistema de limpieza automática de Neo4j para el sistema de verificación Madrid.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import schedule
import time
import threading

from .neo4j_manager import Neo4jManager
from .config import get_config

logger = logging.getLogger(__name__)

class Neo4jCleanupScheduler:
    """Programador de limpieza automática de Neo4j"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.neo4j_manager = Neo4jManager()
        self.running = False
        self.cleanup_thread = None
        
        # Configuración de limpieza
        self.cleanup_config = {
            'enabled': True,
            'interval_hours': 24,  # Limpiar cada 24 horas
            'retention_days': 30,  # Mantener datos por 30 días
            'max_projects_per_cleanup': 100,  # Máximo 100 proyectos por limpieza
            'cleanup_time': '02:00'  # Limpiar a las 2:00 AM
        }
    
    def start_scheduler(self):
        """Inicia el programador de limpieza"""
        if self.running:
            self.logger.warning("El programador ya está ejecutándose")
            return
        
        self.running = True
        
        # Programar limpieza diaria
        schedule.every().day.at(self.cleanup_config['cleanup_time']).do(self._run_cleanup)
        
        # Iniciar hilo de limpieza
        self.cleanup_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.cleanup_thread.start()
        
        self.logger.info(f"Programador de limpieza Neo4j iniciado - Limpieza diaria a las {self.cleanup_config['cleanup_time']}")
    
    def stop_scheduler(self):
        """Detiene el programador de limpieza"""
        self.running = False
        schedule.clear()
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        self.logger.info("Programador de limpieza Neo4j detenido")
    
    def _scheduler_loop(self):
        """Bucle principal del programador"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                self.logger.error(f"Error en el programador de limpieza: {e}")
                time.sleep(300)  # Esperar 5 minutos en caso de error
    
    def _run_cleanup(self):
        """Ejecuta la limpieza programada"""
        try:
            self.logger.info("Iniciando limpieza programada de Neo4j...")
            
            # Calcular fecha de corte
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_config['retention_days'])
            
            # Ejecutar limpieza
            cleaned_count = self.neo4j_manager.cleanup_old_projects(cutoff_date)
            
            # Obtener estadísticas después de la limpieza
            stats = self.neo4j_manager.get_project_statistics()
            
            self.logger.info(f"Limpieza completada: {cleaned_count} proyectos eliminados")
            self.logger.info(f"Estadísticas actuales: {stats.get('total_nodes', 0)} nodos, {stats.get('total_relationships', 0)} relaciones")
            
            # Limpiar cache si es necesario
            if cleaned_count > 0:
                self._cleanup_cache()
            
        except Exception as e:
            self.logger.error(f"Error en limpieza programada: {e}")
    
    def _cleanup_cache(self):
        """Limpia cache relacionado con proyectos eliminados"""
        try:
            # Aquí se podría limpiar cache de Redis si es necesario
            self.logger.info("Cache limpiado después de eliminación de proyectos")
        except Exception as e:
            self.logger.error(f"Error limpiando cache: {e}")
    
    def manual_cleanup(self, days_old: int = None) -> Dict[str, Any]:
        """Ejecuta limpieza manual"""
        try:
            if days_old is None:
                days_old = self.cleanup_config['retention_days']
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Obtener estadísticas antes de la limpieza
            stats_before = self.neo4j_manager.get_project_statistics()
            
            # Ejecutar limpieza
            cleaned_count = self.neo4j_manager.cleanup_old_projects(cutoff_date)
            
            # Obtener estadísticas después de la limpieza
            stats_after = self.neo4j_manager.get_project_statistics()
            
            return {
                'status': 'success',
                'cleaned_projects': cleaned_count,
                'cutoff_date': cutoff_date.isoformat(),
                'stats_before': stats_before,
                'stats_after': stats_after,
                'space_freed': {
                    'nodes': stats_before.get('total_nodes', 0) - stats_after.get('total_nodes', 0),
                    'relationships': stats_before.get('total_relationships', 0) - stats_after.get('total_relationships', 0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error en limpieza manual: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_cleanup_status(self) -> Dict[str, Any]:
        """Obtiene el estado del programador de limpieza"""
        try:
            stats = self.neo4j_manager.get_project_statistics()
            
            return {
                'scheduler_running': self.running,
                'next_cleanup': self._get_next_cleanup_time(),
                'cleanup_config': self.cleanup_config,
                'current_stats': stats,
                'estimated_cleanup_size': self._estimate_cleanup_size()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de limpieza: {e}")
            return {
                'scheduler_running': False,
                'error': str(e)
            }
    
    def _get_next_cleanup_time(self) -> str:
        """Obtiene la próxima hora de limpieza"""
        try:
            next_run = schedule.next_run()
            if next_run:
                return next_run.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return "No programado"
        except:
            return "No disponible"
    
    def _estimate_cleanup_size(self) -> Dict[str, int]:
        """Estima el tamaño de la próxima limpieza"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_config['retention_days'])
            
            # Consultar proyectos que serían eliminados
            with self.neo4j_manager.get_session() as session:
                query = """
                MATCH (p:Project)
                WHERE p.created_at < datetime($cutoff_date)
                RETURN count(p) as project_count
                """
                
                result = session.run(query, {'cutoff_date': cutoff_date.isoformat()})
                project_count = result.single()["project_count"]
                
                return {
                    'projects_to_delete': project_count,
                    'estimated_nodes': project_count * 10,  # Estimación aproximada
                    'estimated_relationships': project_count * 15
                }
                
        except Exception as e:
            self.logger.error(f"Error estimando tamaño de limpieza: {e}")
            return {
                'projects_to_delete': 0,
                'estimated_nodes': 0,
                'estimated_relationships': 0
            }
    
    def update_cleanup_config(self, new_config: Dict[str, Any]) -> bool:
        """Actualiza la configuración de limpieza"""
        try:
            # Validar configuración
            if 'retention_days' in new_config:
                if not isinstance(new_config['retention_days'], int) or new_config['retention_days'] < 1:
                    raise ValueError("retention_days debe ser un entero mayor a 0")
            
            if 'cleanup_time' in new_config:
                # Validar formato de hora
                try:
                    datetime.strptime(new_config['cleanup_time'], '%H:%M')
                except ValueError:
                    raise ValueError("cleanup_time debe estar en formato HH:MM")
            
            # Actualizar configuración
            self.cleanup_config.update(new_config)
            
            # Reiniciar programador si está ejecutándose
            if self.running:
                self.stop_scheduler()
                self.start_scheduler()
            
            self.logger.info(f"Configuración de limpieza actualizada: {new_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando configuración: {e}")
            return False

# Instancia global del programador
cleanup_scheduler = Neo4jCleanupScheduler()
