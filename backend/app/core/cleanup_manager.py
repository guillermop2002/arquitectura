"""
Sistema de limpieza automática para Neo4j y cache.
Elimina datos de proyectos completados para optimizar espacio.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import json

from .neo4j_optimizer import Neo4jOptimizer
from .config import get_config
from .logging_config import get_logger

logger = get_logger(__name__)

class CleanupManager:
    """Gestor de limpieza automática para optimizar espacio."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.neo4j_optimizer = Neo4jOptimizer()
        
        # Configuración de limpieza
        self.cleanup_config = {
            'neo4j_retention_days': 7,  # Mantener datos por 7 días
            'cache_retention_hours': 24,  # Mantener cache por 24 horas
            'temp_files_retention_hours': 6,  # Mantener archivos temp por 6 horas
            'max_projects_in_neo4j': 50,  # Máximo 50 proyectos en Neo4j
            'max_cache_size_mb': 100,  # Máximo 100MB de cache
            'cleanup_frequency_hours': 1,  # Limpiar cada hora
        }
        
        # Métricas de limpieza
        self.cleanup_metrics = {
            'last_cleanup': None,
            'projects_deleted': 0,
            'cache_cleared': 0,
            'space_freed_mb': 0,
            'total_cleanups': 0
        }
        
        self.logger.info("CleanupManager initialized")
    
    def cleanup_project_data(self, project_id: str, force: bool = False) -> Dict[str, Any]:
        """Limpiar datos de un proyecto específico."""
        try:
            self.logger.info(f"🧹 Iniciando limpieza del proyecto: {project_id}")
            
            results = {
                'project_id': project_id,
                'neo4j_cleaned': False,
                'cache_cleaned': False,
                'temp_files_cleaned': False,
                'space_freed_mb': 0,
                'errors': []
            }
            
            # 1. Limpiar datos de Neo4j
            try:
                neo4j_result = self._cleanup_neo4j_project(project_id)
                results['neo4j_cleaned'] = neo4j_result['success']
                results['space_freed_mb'] += neo4j_result.get('space_freed_mb', 0)
                if neo4j_result.get('error'):
                    results['errors'].append(f"Neo4j: {neo4j_result['error']}")
            except Exception as e:
                results['errors'].append(f"Neo4j: {str(e)}")
            
            # 2. Limpiar cache del proyecto
            try:
                cache_result = self._cleanup_project_cache(project_id)
                results['cache_cleaned'] = cache_result['success']
                results['space_freed_mb'] += cache_result.get('space_freed_mb', 0)
                if cache_result.get('error'):
                    results['errors'].append(f"Cache: {cache_result['error']}")
            except Exception as e:
                results['errors'].append(f"Cache: {str(e)}")
            
            # 3. Limpiar archivos temporales del proyecto
            try:
                temp_result = self._cleanup_project_temp_files(project_id)
                results['temp_files_cleaned'] = temp_result['success']
                results['space_freed_mb'] += temp_result.get('space_freed_mb', 0)
                if temp_result.get('error'):
                    results['errors'].append(f"Temp files: {temp_result['error']}")
            except Exception as e:
                results['errors'].append(f"Temp files: {str(e)}")
            
            # Actualizar métricas
            self.cleanup_metrics['projects_deleted'] += 1
            self.cleanup_metrics['space_freed_mb'] += results['space_freed_mb']
            
            self.logger.info(f"✅ Limpieza del proyecto {project_id} completada: {results['space_freed_mb']:.2f}MB liberados")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza del proyecto {project_id}: {e}")
            return {
                'project_id': project_id,
                'neo4j_cleaned': False,
                'cache_cleaned': False,
                'temp_files_cleaned': False,
                'space_freed_mb': 0,
                'errors': [str(e)]
            }
    
    def _cleanup_neo4j_project(self, project_id: str) -> Dict[str, Any]:
        """Limpiar datos de un proyecto en Neo4j."""
        try:
            if not self.neo4j_optimizer.driver:
                return {'success': False, 'error': 'Neo4j no conectado'}
            
            with self.neo4j_optimizer.driver.session() as session:
                # Contar nodos antes de eliminar
                result = session.run("""
                    MATCH (p:Project {id: $project_id})
                    OPTIONAL MATCH (p)-[r]-(n)
                    RETURN count(n) as nodes_count, count(r) as relationships_count
                """, project_id=project_id)
                
                counts = result.single()
                nodes_count = counts['nodes_count'] if counts else 0
                relationships_count = counts['relationships_count'] if counts else 0
                
                # Eliminar proyecto y todos sus datos relacionados
                session.run("""
                    MATCH (p:Project {id: $project_id})
                    DETACH DELETE p
                """, project_id=project_id)
                
                # Calcular espacio liberado (estimación)
                space_freed_mb = (nodes_count * 0.001) + (relationships_count * 0.0005)
                
                self.logger.info(f"🗄️ Neo4j: Eliminados {nodes_count} nodos y {relationships_count} relaciones")
                
                return {
                    'success': True,
                    'nodes_deleted': nodes_count,
                    'relationships_deleted': relationships_count,
                    'space_freed_mb': space_freed_mb
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error limpiando Neo4j para proyecto {project_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _cleanup_project_cache(self, project_id: str) -> Dict[str, Any]:
        """Limpiar cache de un proyecto específico."""
        try:
            cache_dir = Path("cache")
            if not cache_dir.exists():
                return {'success': True, 'space_freed_mb': 0}
            
            project_cache_dir = cache_dir / project_id
            space_freed = 0
            
            if project_cache_dir.exists():
                # Calcular tamaño antes de eliminar
                for file_path in project_cache_dir.rglob('*'):
                    if file_path.is_file():
                        space_freed += file_path.stat().st_size
                
                # Eliminar directorio del proyecto
                shutil.rmtree(project_cache_dir)
                space_freed_mb = space_freed / (1024 * 1024)
                
                self.logger.info(f"🗂️ Cache: Eliminado cache del proyecto {project_id}: {space_freed_mb:.2f}MB")
                
                return {
                    'success': True,
                    'space_freed_mb': space_freed_mb
                }
            else:
                return {'success': True, 'space_freed_mb': 0}
                
        except Exception as e:
            self.logger.error(f"❌ Error limpiando cache para proyecto {project_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _cleanup_project_temp_files(self, project_id: str) -> Dict[str, Any]:
        """Limpiar archivos temporales de un proyecto."""
        try:
            temp_dir = Path("temp")
            if not temp_dir.exists():
                return {'success': True, 'space_freed_mb': 0}
            
            space_freed = 0
            files_deleted = 0
            
            # Buscar archivos del proyecto en temp
            for file_path in temp_dir.rglob(f"*{project_id}*"):
                if file_path.is_file():
                    space_freed += file_path.stat().st_size
                    file_path.unlink()
                    files_deleted += 1
            
            space_freed_mb = space_freed / (1024 * 1024)
            
            if files_deleted > 0:
                self.logger.info(f"🗑️ Temp: Eliminados {files_deleted} archivos del proyecto {project_id}: {space_freed_mb:.2f}MB")
            
            return {
                'success': True,
                'files_deleted': files_deleted,
                'space_freed_mb': space_freed_mb
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando archivos temp para proyecto {project_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def cleanup_old_data(self, force: bool = False) -> Dict[str, Any]:
        """Limpiar datos antiguos según configuración de retención."""
        try:
            self.logger.info("🧹 Iniciando limpieza de datos antiguos")
            
            results = {
                'neo4j_cleaned': False,
                'cache_cleaned': False,
                'temp_files_cleaned': False,
                'projects_deleted': 0,
                'space_freed_mb': 0,
                'errors': []
            }
            
            # 1. Limpiar proyectos antiguos en Neo4j
            try:
                neo4j_result = self._cleanup_old_neo4j_projects()
                results['neo4j_cleaned'] = neo4j_result['success']
                results['projects_deleted'] += neo4j_result.get('projects_deleted', 0)
                results['space_freed_mb'] += neo4j_result.get('space_freed_mb', 0)
                if neo4j_result.get('error'):
                    results['errors'].append(f"Neo4j: {neo4j_result['error']}")
            except Exception as e:
                results['errors'].append(f"Neo4j: {str(e)}")
            
            # 2. Limpiar cache antiguo
            try:
                cache_result = self._cleanup_old_cache()
                results['cache_cleaned'] = cache_result['success']
                results['space_freed_mb'] += cache_result.get('space_freed_mb', 0)
                if cache_result.get('error'):
                    results['errors'].append(f"Cache: {cache_result['error']}")
            except Exception as e:
                results['errors'].append(f"Cache: {str(e)}")
            
            # 3. Limpiar archivos temporales antiguos
            try:
                temp_result = self._cleanup_old_temp_files()
                results['temp_files_cleaned'] = temp_result['success']
                results['space_freed_mb'] += temp_result.get('space_freed_mb', 0)
                if temp_result.get('error'):
                    results['errors'].append(f"Temp files: {temp_result['error']}")
            except Exception as e:
                results['errors'].append(f"Temp files: {str(e)}")
            
            # Actualizar métricas
            self.cleanup_metrics['last_cleanup'] = datetime.now()
            self.cleanup_metrics['total_cleanups'] += 1
            self.cleanup_metrics['space_freed_mb'] += results['space_freed_mb']
            
            self.logger.info(f"✅ Limpieza de datos antiguos completada: {results['space_freed_mb']:.2f}MB liberados")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza de datos antiguos: {e}")
            return {
                'neo4j_cleaned': False,
                'cache_cleaned': False,
                'temp_files_cleaned': False,
                'projects_deleted': 0,
                'space_freed_mb': 0,
                'errors': [str(e)]
            }
    
    def _cleanup_old_neo4j_projects(self) -> Dict[str, Any]:
        """Limpiar proyectos antiguos en Neo4j."""
        try:
            if not self.neo4j_optimizer.driver:
                return {'success': False, 'error': 'Neo4j no conectado'}
            
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_config['neo4j_retention_days'])
            
            with self.neo4j_optimizer.driver.session() as session:
                # Buscar proyectos antiguos
                result = session.run("""
                    MATCH (p:Project)
                    WHERE p.created_at < $cutoff_date OR p.created_at IS NULL
                    RETURN p.id as project_id, p.created_at as created_at
                    ORDER BY p.created_at ASC
                """, cutoff_date=cutoff_date)
                
                old_projects = list(result)
                projects_to_delete = old_projects[:self.cleanup_config['max_projects_in_neo4j']]
                
                projects_deleted = 0
                space_freed = 0
                
                for project in projects_to_delete:
                    project_id = project['project_id']
                    
                    # Contar nodos antes de eliminar
                    count_result = session.run("""
                        MATCH (p:Project {id: $project_id})
                        OPTIONAL MATCH (p)-[r]-(n)
                        RETURN count(n) as nodes_count, count(r) as relationships_count
                    """, project_id=project_id)
                    
                    counts = count_result.single()
                    if counts:
                        nodes_count = counts['nodes_count']
                        relationships_count = counts['relationships_count']
                        space_freed += (nodes_count * 0.001) + (relationships_count * 0.0005)
                    
                    # Eliminar proyecto
                    session.run("""
                        MATCH (p:Project {id: $project_id})
                        DETACH DELETE p
                    """, project_id=project_id)
                    
                    projects_deleted += 1
                
                space_freed_mb = space_freed
                
                self.logger.info(f"🗄️ Neo4j: Eliminados {projects_deleted} proyectos antiguos: {space_freed_mb:.2f}MB")
                
                return {
                    'success': True,
                    'projects_deleted': projects_deleted,
                    'space_freed_mb': space_freed_mb
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error limpiando proyectos antiguos en Neo4j: {e}")
            return {'success': False, 'error': str(e)}
    
    def _cleanup_old_cache(self) -> Dict[str, Any]:
        """Limpiar cache antiguo."""
        try:
            cache_dir = Path("cache")
            if not cache_dir.exists():
                return {'success': True, 'space_freed_mb': 0}
            
            cutoff_time = time.time() - (self.cleanup_config['cache_retention_hours'] * 3600)
            space_freed = 0
            files_deleted = 0
            
            for file_path in cache_dir.rglob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        space_freed += file_path.stat().st_size
                        file_path.unlink()
                        files_deleted += 1
            
            space_freed_mb = space_freed / (1024 * 1024)
            
            if files_deleted > 0:
                self.logger.info(f"🗂️ Cache: Eliminados {files_deleted} archivos antiguos: {space_freed_mb:.2f}MB")
            
            return {
                'success': True,
                'files_deleted': files_deleted,
                'space_freed_mb': space_freed_mb
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando cache antiguo: {e}")
            return {'success': False, 'error': str(e)}
    
    def _cleanup_old_temp_files(self) -> Dict[str, Any]:
        """Limpiar archivos temporales antiguos."""
        try:
            temp_dir = Path("temp")
            if not temp_dir.exists():
                return {'success': True, 'space_freed_mb': 0}
            
            cutoff_time = time.time() - (self.cleanup_config['temp_files_retention_hours'] * 3600)
            space_freed = 0
            files_deleted = 0
            
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        space_freed += file_path.stat().st_size
                        file_path.unlink()
                        files_deleted += 1
            
            space_freed_mb = space_freed / (1024 * 1024)
            
            if files_deleted > 0:
                self.logger.info(f"🗑️ Temp: Eliminados {files_deleted} archivos temporales antiguos: {space_freed_mb:.2f}MB")
            
            return {
                'success': True,
                'files_deleted': files_deleted,
                'space_freed_mb': space_freed_mb
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando archivos temp antiguos: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_cleanup_status(self) -> Dict[str, Any]:
        """Obtener estado actual del sistema de limpieza."""
        try:
            # Obtener estadísticas de Neo4j
            neo4j_stats = self._get_neo4j_stats()
            
            # Obtener estadísticas de cache
            cache_stats = self._get_cache_stats()
            
            # Obtener estadísticas de archivos temp
            temp_stats = self._get_temp_stats()
            
            return {
                'cleanup_metrics': self.cleanup_metrics,
                'neo4j_stats': neo4j_stats,
                'cache_stats': cache_stats,
                'temp_stats': temp_stats,
                'cleanup_config': self.cleanup_config,
                'last_cleanup': self.cleanup_metrics['last_cleanup'],
                'next_cleanup_due': self._get_next_cleanup_time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estado de limpieza: {e}")
            return {'error': str(e)}
    
    def _get_neo4j_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de Neo4j."""
        try:
            if not self.neo4j_optimizer.driver:
                return {'connected': False, 'error': 'Neo4j no conectado'}
            
            with self.neo4j_optimizer.driver.session() as session:
                # Contar proyectos
                result = session.run("MATCH (p:Project) RETURN count(p) as project_count")
                project_count = result.single()['project_count']
                
                # Contar nodos totales
                result = session.run("MATCH (n) RETURN count(n) as total_nodes")
                total_nodes = result.single()['total_nodes']
                
                # Contar relaciones totales
                result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
                total_relationships = result.single()['total_relationships']
                
                return {
                    'connected': True,
                    'project_count': project_count,
                    'total_nodes': total_nodes,
                    'total_relationships': total_relationships,
                    'estimated_size_mb': (total_nodes * 0.001) + (total_relationships * 0.0005)
                }
                
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de cache."""
        try:
            cache_dir = Path("cache")
            if not cache_dir.exists():
                return {'exists': False, 'size_mb': 0, 'file_count': 0}
            
            total_size = 0
            file_count = 0
            
            for file_path in cache_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'exists': True,
                'size_mb': total_size / (1024 * 1024),
                'file_count': file_count
            }
            
        except Exception as e:
            return {'exists': False, 'error': str(e)}
    
    def _get_temp_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de archivos temporales."""
        try:
            temp_dir = Path("temp")
            if not temp_dir.exists():
                return {'exists': False, 'size_mb': 0, 'file_count': 0}
            
            total_size = 0
            file_count = 0
            
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'exists': True,
                'size_mb': total_size / (1024 * 1024),
                'file_count': file_count
            }
            
        except Exception as e:
            return {'exists': False, 'error': str(e)}
    
    def _get_next_cleanup_time(self) -> Optional[datetime]:
        """Calcular cuándo debe ejecutarse la próxima limpieza."""
        if not self.cleanup_metrics['last_cleanup']:
            return datetime.now()
        
        next_cleanup = self.cleanup_metrics['last_cleanup'] + timedelta(
            hours=self.cleanup_config['cleanup_frequency_hours']
        )
        
        return next_cleanup if next_cleanup > datetime.now() else datetime.now()
    
    def force_cleanup_all(self) -> Dict[str, Any]:
        """Forzar limpieza completa de todo el sistema."""
        try:
            self.logger.info("🧹 Iniciando limpieza forzada completa")
            
            results = {
                'neo4j_cleaned': False,
                'cache_cleaned': False,
                'temp_files_cleaned': False,
                'projects_deleted': 0,
                'space_freed_mb': 0,
                'errors': []
            }
            
            # Limpiar todos los proyectos en Neo4j
            try:
                if self.neo4j_optimizer.driver:
                    with self.neo4j_optimizer.driver.session() as session:
                        # Obtener todos los proyectos
                        result = session.run("MATCH (p:Project) RETURN p.id as project_id")
                        all_projects = [record['project_id'] for record in result]
                        
                        # Eliminar todos los proyectos
                        for project_id in all_projects:
                            session.run("""
                                MATCH (p:Project {id: $project_id})
                                DETACH DELETE p
                            """, project_id=project_id)
                            results['projects_deleted'] += 1
                        
                        results['neo4j_cleaned'] = True
                        self.logger.info(f"🗄️ Neo4j: Eliminados todos los {len(all_projects)} proyectos")
            except Exception as e:
                results['errors'].append(f"Neo4j: {str(e)}")
            
            # Limpiar todo el cache
            try:
                cache_dir = Path("cache")
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    results['cache_cleaned'] = True
                    self.logger.info("🗂️ Cache: Eliminado completamente")
            except Exception as e:
                results['errors'].append(f"Cache: {str(e)}")
            
            # Limpiar todos los archivos temporales
            try:
                temp_dir = Path("temp")
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    temp_dir.mkdir(exist_ok=True)
                    results['temp_files_cleaned'] = True
                    self.logger.info("🗑️ Temp: Eliminados todos los archivos temporales")
            except Exception as e:
                results['errors'].append(f"Temp files: {str(e)}")
            
            # Actualizar métricas
            self.cleanup_metrics['last_cleanup'] = datetime.now()
            self.cleanup_metrics['total_cleanups'] += 1
            self.cleanup_metrics['projects_deleted'] += results['projects_deleted']
            
            self.logger.info(f"✅ Limpieza forzada completada: {results['projects_deleted']} proyectos eliminados")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza forzada: {e}")
            return {
                'neo4j_cleaned': False,
                'cache_cleaned': False,
                'temp_files_cleaned': False,
                'projects_deleted': 0,
                'space_freed_mb': 0,
                'errors': [str(e)]
            }
