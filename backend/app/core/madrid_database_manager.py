"""
Gestor de base de datos para el sistema Madrid.
Integra PostgreSQL para normativa y Neo4j para relaciones.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime
import asyncio
import asyncpg
from .neo4j_manager import Neo4jManager
from .madrid_normative_processor import NormativeDocument, NormativeSection

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Configuración de base de datos."""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_database: str = "madrid_normative"
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

class MadridDatabaseManager:
    """Gestor de base de datos para Madrid."""
    
    def __init__(self, config: DatabaseConfig = None):
        self.logger = logging.getLogger(f"{__name__}.MadridDatabaseManager")
        self.config = config or DatabaseConfig()
        self.pg_pool = None
        self.neo4j_manager = Neo4jManager()
        
    async def initialize(self):
        """Inicializar conexiones a bases de datos."""
        try:
            # Inicializar PostgreSQL
            await self._init_postgresql()
            
            # Inicializar Neo4j
            self.neo4j_manager.initialize_connection()
            
            self.logger.info("Conexiones a bases de datos inicializadas")
            
        except Exception as e:
            self.logger.error(f"Error inicializando bases de datos: {e}")
            raise
    
    async def _init_postgresql(self):
        """Inicializar conexión a PostgreSQL."""
        try:
            self.pg_pool = await asyncpg.create_pool(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                database=self.config.postgres_database,
                min_size=1,
                max_size=10
            )
            
            # Crear tablas si no existen
            await self._create_tables()
            
            self.logger.info("PostgreSQL inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando PostgreSQL: {e}")
            raise
    
    async def _create_tables(self):
        """Crear tablas necesarias en PostgreSQL."""
        async with self.pg_pool.acquire() as conn:
            # Tabla de documentos normativos
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS normative_documents (
                    id VARCHAR(12) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    path TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    building_type VARCHAR(100),
                    pages INTEGER DEFAULT 0,
                    file_size BIGINT DEFAULT 0,
                    checksum VARCHAR(32),
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de secciones normativas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS normative_sections (
                    id SERIAL PRIMARY KEY,
                    section_id VARCHAR(100) NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    document_id VARCHAR(12) NOT NULL,
                    building_types TEXT[],  -- Array de tipos de edificio
                    floor_applicability FLOAT[],  -- Array de plantas aplicables
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES normative_documents(id)
                )
            """)
            
            # Tabla de índices de búsqueda
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS normative_search_index (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(12) NOT NULL,
                    section_id VARCHAR(100),
                    search_terms TEXT[] NOT NULL,
                    content_hash VARCHAR(32) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES normative_documents(id)
                )
            """)
            
            # Crear índices para búsqueda
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normative_documents_category 
                ON normative_documents(category)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normative_documents_building_type 
                ON normative_documents(building_type)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normative_sections_document_id 
                ON normative_sections(document_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normative_sections_building_types 
                ON normative_sections USING GIN(building_types)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_normative_sections_floor_applicability 
                ON normative_sections USING GIN(floor_applicability)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_terms 
                ON normative_search_index USING GIN(search_terms)
            """)
    
    async def store_normative_document(self, document: NormativeDocument) -> bool:
        """Almacenar documento normativo en PostgreSQL."""
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO normative_documents 
                    (id, name, path, category, building_type, pages, file_size, checksum, processed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        path = EXCLUDED.path,
                        category = EXCLUDED.category,
                        building_type = EXCLUDED.building_type,
                        pages = EXCLUDED.pages,
                        file_size = EXCLUDED.file_size,
                        checksum = EXCLUDED.checksum,
                        processed_at = EXCLUDED.processed_at
                """, 
                document.id, document.name, document.path, document.category,
                document.building_type, document.pages, document.file_size,
                document.checksum, document.processed_at)
                
                self.logger.debug(f"Documento almacenado: {document.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error almacenando documento {document.name}: {e}")
            return False
    
    async def store_normative_section(self, section: NormativeSection) -> bool:
        """Almacenar sección normativa en PostgreSQL."""
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO normative_sections 
                    (section_id, title, content, page_number, document_id, building_types, floor_applicability)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (section_id, document_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        page_number = EXCLUDED.page_number,
                        building_types = EXCLUDED.building_types,
                        floor_applicability = EXCLUDED.floor_applicability
                """,
                section.section_id, section.title, section.content, section.page_number,
                section.document_id, section.building_types, section.floor_applicability)
                
                self.logger.debug(f"Sección almacenada: {section.section_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error almacenando sección {section.section_id}: {e}")
            return False
    
    async def search_normative_content(self, 
                                     query: str, 
                                     building_types: List[str] = None,
                                     floors: List[float] = None,
                                     categories: List[str] = None) -> List[Dict[str, Any]]:
        """Buscar contenido normativo."""
        try:
            async with self.pg_pool.acquire() as conn:
                # Construir consulta SQL
                sql = """
                    SELECT DISTINCT
                        ns.section_id,
                        ns.title,
                        ns.content,
                        ns.page_number,
                        nd.name as document_name,
                        nd.category,
                        nd.building_type
                    FROM normative_sections ns
                    JOIN normative_documents nd ON ns.document_id = nd.id
                    WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # Filtro por texto
                if query:
                    param_count += 1
                    sql += f" AND (ns.title ILIKE ${param_count} OR ns.content ILIKE ${param_count})"
                    params.append(f"%{query}%")
                
                # Filtro por tipos de edificio
                if building_types:
                    param_count += 1
                    sql += f" AND (nd.building_type = ANY(${param_count}) OR ns.building_types && ${param_count})"
                    params.append(building_types)
                
                # Filtro por plantas
                if floors:
                    param_count += 1
                    sql += f" AND (ns.floor_applicability && ${param_count} OR ns.floor_applicability IS NULL)"
                    params.append(floors)
                
                # Filtro por categorías
                if categories:
                    param_count += 1
                    sql += f" AND nd.category = ANY(${param_count})"
                    params.append(categories)
                
                sql += " ORDER BY nd.category, ns.page_number"
                
                rows = await conn.fetch(sql, *params)
                
                results = []
                for row in rows:
                    results.append({
                        'section_id': row['section_id'],
                        'title': row['title'],
                        'content': row['content'],
                        'page_number': row['page_number'],
                        'document_name': row['document_name'],
                        'category': row['category'],
                        'building_type': row['building_type']
                    })
                
                self.logger.info(f"Búsqueda completada: {len(results)} resultados")
                return results
                
        except Exception as e:
            self.logger.error(f"Error en búsqueda normativa: {e}")
            return []
    
    async def get_applicable_normative(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtener normativa aplicable a un proyecto."""
        try:
            # Determinar tipos de edificio del proyecto
            building_types = [project_data.get('primary_use')]
            
            # Agregar usos secundarios
            for secondary_use in project_data.get('secondary_uses', []):
                building_types.append(secondary_use.get('use_type'))
            
            # Determinar plantas del proyecto
            floors = []
            for secondary_use in project_data.get('secondary_uses', []):
                floors.extend(secondary_use.get('floors', []))
            
            # Determinar categorías aplicables
            categories = ['cte', 'pgoum_general']
            
            if project_data.get('is_existing_building', False):
                categories.append('support')
            
            # Buscar normativa aplicable
            results = await self.search_normative_content(
                query="",
                building_types=building_types,
                floors=floors,
                categories=categories
            )
            
            self.logger.info(f"Normativa aplicable encontrada: {len(results)} secciones")
            return results
            
        except Exception as e:
            self.logger.error(f"Error obteniendo normativa aplicable: {e}")
            return []
    
    async def create_project_normative_nodes(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """Crear nodos de normativa en Neo4j para un proyecto."""
        try:
            # Obtener normativa aplicable
            applicable_normative = await self.get_applicable_normative(project_data)
            
            # Crear nodos en Neo4j
            for normative_item in applicable_normative:
                # Crear nodo de sección normativa
                section_node = {
                    'id': f"{project_id}_{normative_item['section_id']}",
                    'section_id': normative_item['section_id'],
                    'title': normative_item['title'],
                    'content': normative_item['content'],
                    'page_number': normative_item['page_number'],
                    'document_name': normative_item['document_name'],
                    'category': normative_item['category'],
                    'building_type': normative_item['building_type'],
                    'project_id': project_id
                }
                
                # Crear nodo en Neo4j
                self.neo4j_manager.create_node(
                    node_type="NormativeSection",
                    properties=section_node
                )
                
                # Crear relación con proyecto
                self.neo4j_manager.create_relationship(
                    source_id=project_id,
                    target_id=section_node['id'],
                    relationship_type="APPLIES_TO",
                    properties={
                        'building_type': normative_item['building_type'],
                        'category': normative_item['category']
                    }
                )
            
            self.logger.info(f"Nodos de normativa creados para proyecto {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando nodos de normativa: {e}")
            return False
    
    async def close(self):
        """Cerrar conexiones."""
        if self.pg_pool:
            await self.pg_pool.close()
        
        if self.neo4j_manager:
            self.neo4j_manager.close()
        
        self.logger.info("Conexiones cerradas")
