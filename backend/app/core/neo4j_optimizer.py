"""
Optimizador de Neo4j para el sistema de verificación arquitectónica.
Optimizado para el plan gratuito de 90 días de Neo4j AuraDB.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import time

from neo4j import GraphDatabase
from .config import get_config
from .logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class Neo4jLimits:
    """Límites del plan gratuito de Neo4j AuraDB."""
    max_nodes: int = 50000
    max_relationships: int = 175000
    max_storage_gb: float = 0.5
    max_operations_per_month: int = 200000
    max_concurrent_queries: int = 2
    max_query_time_seconds: int = 30

@dataclass
class OptimizationConfig:
    """Configuración de optimización para Neo4j."""
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay: float = 1.0
    query_timeout: int = 25  # Menos que el límite de 30s
    use_indexes: bool = True
    compress_data: bool = True
    cleanup_frequency_hours: int = 24

class Neo4jOptimizer:
    """Optimizador para Neo4j con límites del plan gratuito."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.limits = Neo4jLimits()
        self.opt_config = OptimizationConfig()
        
        # Conectar a Neo4j
        self.driver = None
        self._connect()
        
        # Métricas de uso
        self.usage_metrics = {
            'nodes_created': 0,
            'relationships_created': 0,
            'queries_executed': 0,
            'storage_used_gb': 0.0,
            'last_cleanup': datetime.now()
        }
        
        # Inicializar optimizaciones
        self._setup_optimizations()
    
    def _connect(self):
        """Conectar a Neo4j con configuración optimizada."""
        try:
            neo4j_config = self.config.neo4j
            
            self.driver = GraphDatabase.driver(
                neo4j_config.uri,
                auth=(neo4j_config.username, neo4j_config.password),
                max_connection_lifetime=3000,  # 50 minutos
                max_connection_pool_size=2,    # Límite del plan gratuito
                connection_timeout=10
            )
            
            # Verificar conexión
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            self.logger.info("Neo4j connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def test_connection(self):
        """Verificar la conexión a Neo4j."""
        try:
            if not self.driver:
                return False
            
            # Usar verify_connectivity() como recomienda la documentación oficial
            self.driver.verify_connectivity()
            self.logger.info("Neo4j connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Neo4j connection test failed: {e}")
            return False
    
    def _setup_optimizations(self):
        """Configurar optimizaciones para el plan gratuito."""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # Crear índices para optimizar consultas
                if self.opt_config.use_indexes:
                    self._create_indexes(session)
                
                # Configurar límites de consulta
                self._configure_query_limits(session)
                
                # Limpiar datos antiguos si es necesario
                self._cleanup_old_data(session)
                
            self.logger.info("Neo4j optimizations configured")
            
        except Exception as e:
            self.logger.error(f"Error setting up optimizations: {e}")
    
    def _create_indexes(self, session):
        """Crear índices para optimizar consultas."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:Project) ON (n.project_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Document) ON (n.document_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Element) ON (n.element_type)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Regulation) ON (n.regulation_code)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Issue) ON (n.severity)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Question) ON (n.status)"
        ]
        
        for index_query in indexes:
            try:
                session.run(index_query)
            except Exception as e:
                self.logger.warning(f"Could not create index: {e}")
    
    def _configure_query_limits(self, session):
        """Configurar límites de consulta."""
        try:
            # Configurar timeout de consulta
            session.run("CALL dbms.setConfigValue('dbms.query.timeout', '25s')")
            
            # Configurar límite de memoria
            session.run("CALL dbms.setConfigValue('dbms.memory.heap.max_size', '512m')")
            
        except Exception as e:
            self.logger.warning(f"Could not configure query limits: {e}")
    
    def _cleanup_old_data(self, session):
        """Limpiar datos antiguos para mantener dentro de los límites."""
        try:
            # Eliminar datos de proyectos antiguos (más de 30 días)
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            cleanup_queries = [
                f"MATCH (n:Project) WHERE n.created_at < '{cutoff_date}' DETACH DELETE n",
                f"MATCH (n:Document) WHERE n.created_at < '{cutoff_date}' DETACH DELETE n",
                f"MATCH (n:Element) WHERE n.created_at < '{cutoff_date}' DETACH DELETE n"
            ]
            
            for query in cleanup_queries:
                result = session.run(query)
                deleted_count = result.consume().counters.nodes_deleted
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old nodes")
            
            self.usage_metrics['last_cleanup'] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def check_limits(self) -> Dict[str, Any]:
        """Verificar límites del plan gratuito."""
        if not self.driver:
            return {"error": "No connection to Neo4j"}
        
        try:
            with self.driver.session() as session:
                # Contar nodos
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = result.single()['node_count']
                
                # Contar relaciones
                result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = result.single()['rel_count']
                
                # Obtener tamaño de la base de datos
                result = session.run("CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes') YIELD attributes RETURN attributes")
                db_size = 0.0
                try:
                    size_data = result.single()['attributes']
                    if 'TotalStoreSize' in size_data:
                        db_size = size_data['TotalStoreSize'] / (1024**3)  # Convertir a GB
                except:
                    pass
                
                # Verificar límites
                limits_status = {
                    'nodes': {
                        'current': node_count,
                        'limit': self.limits.max_nodes,
                        'percentage': (node_count / self.limits.max_nodes) * 100,
                        'status': 'OK' if node_count < self.limits.max_nodes else 'WARNING'
                    },
                    'relationships': {
                        'current': rel_count,
                        'limit': self.limits.max_relationships,
                        'percentage': (rel_count / self.limits.max_relationships) * 100,
                        'status': 'OK' if rel_count < self.limits.max_relationships else 'WARNING'
                    },
                    'storage': {
                        'current_gb': db_size,
                        'limit_gb': self.limits.max_storage_gb,
                        'percentage': (db_size / self.limits.max_storage_gb) * 100,
                        'status': 'OK' if db_size < self.limits.max_storage_gb else 'WARNING'
                    }
                }
                
                return {
                    'limits_status': limits_status,
                    'recommendations': self._get_recommendations(limits_status)
                }
                
        except Exception as e:
            self.logger.error(f"Error checking limits: {e}")
            return {"error": str(e)}
    
    def _get_recommendations(self, limits_status: Dict) -> List[str]:
        """Obtener recomendaciones basadas en el estado de los límites."""
        recommendations = []
        
        for limit_type, status in limits_status.items():
            if status['percentage'] > 80:
                recommendations.append(f"⚠️ {limit_type.title()} usage is at {status['percentage']:.1f}% - consider cleanup")
            elif status['percentage'] > 60:
                recommendations.append(f"ℹ️ {limit_type.title()} usage is at {status['percentage']:.1f}% - monitor closely")
        
        if not recommendations:
            recommendations.append("✅ All limits are within safe ranges")
        
        return recommendations
    
    def optimize_query(self, query: str) -> str:
        """Optimizar consulta Cypher para el plan gratuito."""
        # Añadir límites a las consultas
        if 'MATCH' in query and 'LIMIT' not in query:
            query += f" LIMIT {self.opt_config.batch_size}"
        
        # Añadir timeout
        query = f"CYPHER timeout={self.opt_config.query_timeout} {query}"
        
        return query
    
    def execute_optimized_query(self, query: str, parameters: Dict = None) -> Any:
        """Ejecutar consulta optimizada con manejo de errores."""
        if not self.driver:
            return {"error": "No connection to Neo4j"}
        
        optimized_query = self.optimize_query(query)
        
        for attempt in range(self.opt_config.max_retries):
            try:
                with self.driver.session() as session:
                    result = session.run(optimized_query, parameters or {})
                    
                    # Actualizar métricas
                    self.usage_metrics['queries_executed'] += 1
                    
                    return result.data()
                    
            except Exception as e:
                if attempt < self.opt_config.max_retries - 1:
                    self.logger.warning(f"Query failed (attempt {attempt + 1}): {e}")
                    time.sleep(self.opt_config.retry_delay * (2 ** attempt))  # Backoff exponencial
                else:
                    self.logger.error(f"Query failed after {self.opt_config.max_retries} attempts: {e}")
                    return {"error": str(e)}
    
    def batch_create_nodes(self, nodes: List[Dict]) -> Dict[str, Any]:
        """Crear nodos en lotes para optimizar el rendimiento."""
        if not self.driver:
            return {"error": "No connection to Neo4j"}
        
        try:
            # Verificar límites antes de crear
            limits_check = self.check_limits()
            if limits_check.get('limits_status', {}).get('nodes', {}).get('percentage', 0) > 90:
                return {"error": "Node limit nearly reached, cannot create more nodes"}
            
            created_count = 0
            
            # Procesar en lotes
            for i in range(0, len(nodes), self.opt_config.batch_size):
                batch = nodes[i:i + self.opt_config.batch_size]
                
                query = """
                UNWIND $nodes AS node
                CREATE (n:Node)
                SET n = node
                RETURN count(n) as created
                """
                
                result = self.execute_optimized_query(query, {"nodes": batch})
                if result and not result.get('error'):
                    created_count += result[0]['created']
            
            # Actualizar métricas
            self.usage_metrics['nodes_created'] += created_count
            
            return {
                "created": created_count,
                "total": len(nodes),
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating nodes in batch: {e}")
            return {"error": str(e)}
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Obtener resumen de uso del plan gratuito."""
        limits_check = self.check_limits()
        
        return {
            'usage_metrics': self.usage_metrics,
            'limits_check': limits_check,
            'optimization_config': self.opt_config.__dict__,
            'recommendations': self._get_optimization_recommendations()
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Obtener recomendaciones de optimización."""
        recommendations = []
        
        # Verificar frecuencia de limpieza
        hours_since_cleanup = (datetime.now() - self.usage_metrics['last_cleanup']).total_seconds() / 3600
        if hours_since_cleanup > self.opt_config.cleanup_frequency_hours:
            recommendations.append("🧹 Run cleanup to remove old data")
        
        # Verificar tamaño de lotes
        if self.opt_config.batch_size > 1000:
            recommendations.append("📦 Consider reducing batch size for better performance")
        
        # Verificar uso de índices
        if not self.opt_config.use_indexes:
            recommendations.append("🔍 Enable indexes for better query performance")
        
        return recommendations
    
    def close(self):
        """Cerrar conexión a Neo4j."""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")

# =============================================================================
# UTILIDADES DE OPTIMIZACIÓN
# =============================================================================

def create_optimized_neo4j_manager() -> Neo4jOptimizer:
    """Crear un gestor de Neo4j optimizado para el plan gratuito."""
    return Neo4jOptimizer()

def get_neo4j_usage_report() -> Dict[str, Any]:
    """Obtener reporte de uso de Neo4j."""
    manager = Neo4jOptimizer()
    try:
        return manager.get_usage_summary()
    finally:
        manager.close()

def optimize_neo4j_for_free_tier() -> Dict[str, Any]:
    """Optimizar Neo4j para el plan gratuito."""
    manager = Neo4jOptimizer()
    try:
        # Ejecutar limpieza
        with manager.driver.session() as session:
            manager._cleanup_old_data(session)
        
        # Verificar límites
        limits_check = manager.check_limits()
        
        return {
            "optimization_completed": True,
            "limits_check": limits_check,
            "recommendations": manager._get_optimization_recommendations()
        }
    finally:
        manager.close()
