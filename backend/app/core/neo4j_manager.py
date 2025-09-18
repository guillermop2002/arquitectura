"""
Gestor de Neo4j para Grafo de Conocimiento
Fase 3: Sistema de Preguntas Inteligentes
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from neo4j import GraphDatabase
from .config import get_config
from .logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class KnowledgeNode:
    """Nodo en el grafo de conocimiento"""
    node_id: str
    node_type: str  # 'project', 'document', 'plan', 'element', 'regulation', 'issue', 'question'
    properties: Dict[str, Any]
    labels: List[str]
    created_at: str
    updated_at: str

@dataclass
class KnowledgeRelationship:
    """Relación en el grafo de conocimiento"""
    relationship_id: str
    relationship_type: str  # 'contains', 'relates_to', 'violates', 'complies_with', 'generates', 'resolves'
    source_node_id: str
    target_node_id: str
    properties: Dict[str, Any]
    created_at: str

@dataclass
class KnowledgeGraph:
    """Grafo de conocimiento completo"""
    nodes: List[KnowledgeNode]
    relationships: List[KnowledgeRelationship]
    metadata: Dict[str, Any]

class Neo4jManager:
    """Gestor de Neo4j para el grafo de conocimiento arquitectónico"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Configuración de Neo4j
        self.uri = self.config.neo4j.uri
        self.username = self.config.neo4j.username
        self.password = self.config.neo4j.password
        self.database = self.config.neo4j.database
        
        # Driver de Neo4j
        self.driver = None
        self.session = None
        
        # Inicializar conexión
        self.initialize_connection()
    
    def initialize_connection(self):
        """Inicializa la conexión con Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            
            # Verificar conexión
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                
            if test_value == 1:
                self.logger.info("Conexión con Neo4j establecida correctamente")
            else:
                raise Exception("Error verificando conexión con Neo4j")
                
        except Exception as e:
            self.logger.error(f"Error conectando con Neo4j: {e}")
            self.driver = None
    
    def get_session(self):
        """Obtiene una sesión de Neo4j"""
        if not self.driver:
            self.initialize_connection()
        
        if self.driver:
            return self.driver.session(database=self.database)
        else:
            raise Exception("No hay conexión con Neo4j")
    
    def create_project_node(self, project_data: Dict[str, Any]) -> str:
        """Crea un nodo de proyecto en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"project_{project_data.get('id', 'unknown')}"
                
                query = """
                MERGE (p:Project {id: $node_id})
                SET p.name = $name,
                    p.type = $type,
                    p.location = $location,
                    p.architect = $architect,
                    p.client = $client,
                    p.status = $status,
                    p.created_at = datetime(),
                    p.updated_at = datetime()
                RETURN p.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'name': project_data.get('name', ''),
                    'type': project_data.get('type', 'residential'),
                    'location': project_data.get('location', ''),
                    'architect': project_data.get('architect', ''),
                    'client': project_data.get('client', ''),
                    'status': project_data.get('status', 'in_progress')
                })
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de proyecto: {e}")
            return None
    
    def create_document_node(self, document_data: Dict[str, Any], project_id: str) -> str:
        """Crea un nodo de documento en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"document_{document_data.get('id', 'unknown')}"
                
                query = """
                MERGE (d:Document {id: $node_id})
                SET d.name = $name,
                    d.type = $type,
                    d.file_path = $file_path,
                    d.pages = $pages,
                    d.size = $size,
                    d.extracted_text = $extracted_text,
                    d.created_at = datetime(),
                    d.updated_at = datetime()
                RETURN d.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'name': document_data.get('name', ''),
                    'type': document_data.get('type', 'unknown'),
                    'file_path': document_data.get('file_path', ''),
                    'pages': document_data.get('pages', 0),
                    'size': document_data.get('size', 0),
                    'extracted_text': document_data.get('extracted_text', '')[:1000]  # Limitar texto
                })
                
                # Crear relación con proyecto
                if project_id:
                    self.create_relationship(
                        project_id, node_id, "CONTAINS", 
                        {"relationship_type": "project_document"}
                    )
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de documento: {e}")
            return None
    
    def create_plan_node(self, plan_data: Dict[str, Any], project_id: str) -> str:
        """Crea un nodo de plano en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"plan_{plan_data.get('id', 'unknown')}"
                
                query = """
                MERGE (p:Plan {id: $node_id})
                SET p.name = $name,
                    p.type = $type,
                    p.scale = $scale,
                    p.orientation = $orientation,
                    p.elements_count = $elements_count,
                    p.compliance_score = $compliance_score,
                    p.created_at = datetime(),
                    p.updated_at = datetime()
                RETURN p.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'name': plan_data.get('name', ''),
                    'type': plan_data.get('type', 'general'),
                    'scale': plan_data.get('scale', 100.0),
                    'orientation': plan_data.get('orientation', 'unknown'),
                    'elements_count': plan_data.get('elements_count', 0),
                    'compliance_score': plan_data.get('compliance_score', 0.0)
                })
                
                # Crear relación con proyecto
                if project_id:
                    self.create_relationship(
                        project_id, node_id, "CONTAINS", 
                        {"relationship_type": "project_plan"}
                    )
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de plano: {e}")
            return None
    
    def create_element_node(self, element_data: Dict[str, Any], plan_id: str) -> str:
        """Crea un nodo de elemento arquitectónico en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"element_{element_data.get('id', 'unknown')}"
                
                query = """
                MERGE (e:Element {id: $node_id})
                SET e.type = $type,
                    e.name = $name,
                    e.dimensions = $dimensions,
                    e.coordinates = $coordinates,
                    e.properties = $properties,
                    e.confidence = $confidence,
                    e.created_at = datetime(),
                    e.updated_at = datetime()
                RETURN e.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'type': element_data.get('type', 'unknown'),
                    'name': element_data.get('name', ''),
                    'dimensions': json.dumps(element_data.get('dimensions', {})),
                    'coordinates': json.dumps(element_data.get('coordinates', [])),
                    'properties': json.dumps(element_data.get('properties', {})),
                    'confidence': element_data.get('confidence', 0.0)
                })
                
                # Crear relación con plano
                if plan_id:
                    self.create_relationship(
                        plan_id, node_id, "CONTAINS", 
                        {"relationship_type": "plan_element"}
                    )
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de elemento: {e}")
            return None
    
    def create_regulation_node(self, regulation_data: Dict[str, Any]) -> str:
        """Crea un nodo de normativa en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"regulation_{regulation_data.get('id', 'unknown')}"
                
                query = """
                MERGE (r:Regulation {id: $node_id})
                SET r.name = $name,
                    r.type = $type,
                    r.section = $section,
                    r.article = $article,
                    r.content = $content,
                    r.applicable_uses = $applicable_uses,
                    r.created_at = datetime(),
                    r.updated_at = datetime()
                RETURN r.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'name': regulation_data.get('name', ''),
                    'type': regulation_data.get('type', 'CTE'),
                    'section': regulation_data.get('section', ''),
                    'article': regulation_data.get('article', ''),
                    'content': regulation_data.get('content', '')[:2000],  # Limitar contenido
                    'applicable_uses': json.dumps(regulation_data.get('applicable_uses', []))
                })
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de normativa: {e}")
            return None
    
    def create_issue_node(self, issue_data: Dict[str, Any], project_id: str) -> str:
        """Crea un nodo de problema en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"issue_{issue_data.get('id', 'unknown')}"
                
                query = """
                MERGE (i:Issue {id: $node_id})
                SET i.title = $title,
                    i.description = $description,
                    i.severity = $severity,
                    i.category = $category,
                    i.status = $status,
                    i.regulation_reference = $regulation_reference,
                    i.created_at = datetime(),
                    i.updated_at = datetime()
                RETURN i.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'title': issue_data.get('title', ''),
                    'description': issue_data.get('description', ''),
                    'severity': issue_data.get('severity', 'MEDIUM'),
                    'category': issue_data.get('category', 'compliance'),
                    'status': issue_data.get('status', 'open'),
                    'regulation_reference': issue_data.get('regulation_reference', '')
                })
                
                # Crear relación con proyecto
                if project_id:
                    self.create_relationship(
                        project_id, node_id, "HAS_ISSUE", 
                        {"relationship_type": "project_issue"}
                    )
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de problema: {e}")
            return None
    
    def create_question_node(self, question_data: Dict[str, Any], project_id: str) -> str:
        """Crea un nodo de pregunta en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"question_{question_data.get('id', 'unknown')}"
                
                query = """
                MERGE (q:Question {id: $node_id})
                SET q.text = $text,
                    q.type = $type,
                    q.context = $context,
                    q.priority = $priority,
                    q.status = $status,
                    q.answer = $answer,
                    q.created_at = datetime(),
                    q.updated_at = datetime()
                RETURN q.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'text': question_data.get('text', ''),
                    'type': question_data.get('type', 'clarification'),
                    'context': question_data.get('context', ''),
                    'priority': question_data.get('priority', 'MEDIUM'),
                    'status': question_data.get('status', 'pending'),
                    'answer': question_data.get('answer', '')
                })
                
                # Crear relación con proyecto
                if project_id:
                    self.create_relationship(
                        project_id, node_id, "GENERATES", 
                        {"relationship_type": "project_question"}
                    )
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de pregunta: {e}")
            return None
    
    def create_relationship(self, source_id: str, target_id: str, 
                          relationship_type: str, properties: Dict[str, Any] = None) -> str:
        """Crea una relación en el grafo"""
        try:
            with self.get_session() as session:
                relationship_id = f"rel_{source_id}_{target_id}_{relationship_type}"
                
                query = """
                MATCH (source), (target)
                WHERE source.id = $source_id AND target.id = $target_id
                MERGE (source)-[r:RELATIONSHIP {id: $relationship_id}]->(target)
                SET r.type = $relationship_type,
                    r.properties = $properties,
                    r.created_at = datetime()
                RETURN r.id as relationship_id
                """
                
                result = session.run(query, {
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_id': relationship_id,
                    'relationship_type': relationship_type,
                    'properties': json.dumps(properties or {})
                })
                
                return result.single()["relationship_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando relación: {e}")
            return None
    
    def find_related_nodes(self, node_id: str, relationship_types: List[str] = None, 
                          max_depth: int = 2) -> List[Dict[str, Any]]:
        """Encuentra nodos relacionados en el grafo"""
        try:
            with self.get_session() as session:
                if relationship_types:
                    rel_filter = f"AND type(r) IN {relationship_types}"
                else:
                    rel_filter = ""
                
                query = f"""
                MATCH (start {{id: $node_id}})
                MATCH path = (start)-[r*1..{max_depth}]-(related)
                WHERE 1=1 {rel_filter}
                RETURN DISTINCT related, length(path) as depth
                ORDER BY depth
                """
                
                result = session.run(query, {'node_id': node_id})
                
                related_nodes = []
                for record in result:
                    node = dict(record["related"])
                    node["depth"] = record["depth"]
                    related_nodes.append(node)
                
                return related_nodes
                
        except Exception as e:
            self.logger.error(f"Error encontrando nodos relacionados: {e}")
            return []
    
    def find_compliance_issues(self, project_id: str) -> List[Dict[str, Any]]:
        """Encuentra problemas de cumplimiento en el proyecto"""
        try:
            with self.get_session() as session:
                query = """
                MATCH (p:Project {id: $project_id})-[:HAS_ISSUE]->(i:Issue)
                WHERE i.category = 'compliance'
                RETURN i
                ORDER BY i.severity DESC, i.created_at DESC
                """
                
                result = session.run(query, {'project_id': project_id})
                
                issues = []
                for record in result:
                    issue = dict(record["i"])
                    issues.append(issue)
                
                return issues
                
        except Exception as e:
            self.logger.error(f"Error encontrando problemas de cumplimiento: {e}")
            return []
    
    def find_pending_questions(self, project_id: str) -> List[Dict[str, Any]]:
        """Encuentra preguntas pendientes del proyecto"""
        try:
            with self.get_session() as session:
                query = """
                MATCH (p:Project {id: $project_id})-[:GENERATES]->(q:Question)
                WHERE q.status = 'pending'
                RETURN q
                ORDER BY q.priority DESC, q.created_at DESC
                """
                
                result = session.run(query, {'project_id': project_id})
                
                questions = []
                for record in result:
                    question = dict(record["q"])
                    questions.append(question)
                
                return questions
                
        except Exception as e:
            self.logger.error(f"Error encontrando preguntas pendientes: {e}")
            return []
    
    def update_question_answer(self, question_id: str, answer: str) -> bool:
        """Actualiza la respuesta de una pregunta"""
        try:
            with self.get_session() as session:
                query = """
                MATCH (q:Question {id: $question_id})
                SET q.answer = $answer,
                    q.status = 'answered',
                    q.updated_at = datetime()
                RETURN q.id as question_id
                """
                
                result = session.run(query, {
                    'question_id': question_id,
                    'answer': answer
                })
                
                return result.single()["question_id"] is not None
                
        except Exception as e:
            self.logger.error(f"Error actualizando respuesta: {e}")
            return False
    
    def get_project_knowledge_graph(self, project_id: str) -> KnowledgeGraph:
        """Obtiene el grafo de conocimiento completo del proyecto"""
        try:
            with self.get_session() as session:
                # Obtener todos los nodos del proyecto
                nodes_query = """
                MATCH (n)
                WHERE n.id STARTS WITH $project_prefix
                RETURN n
                """
                
                result = session.run(nodes_query, {'project_prefix': f"project_{project_id}"})
                
                nodes = []
                for record in result:
                    node_data = dict(record["n"])
                    node = KnowledgeNode(
                        node_id=node_data.get("id", ""),
                        node_type=node_data.get("type", "unknown"),
                        properties=node_data,
                        labels=node_data.get("labels", []),
                        created_at=node_data.get("created_at", ""),
                        updated_at=node_data.get("updated_at", "")
                    )
                    nodes.append(node)
                
                # Obtener todas las relaciones del proyecto
                relationships_query = """
                MATCH (source)-[r]->(target)
                WHERE source.id STARTS WITH $project_prefix OR target.id STARTS WITH $project_prefix
                RETURN r, source.id as source_id, target.id as target_id
                """
                
                result = session.run(relationships_query, {'project_prefix': f"project_{project_id}"})
                
                relationships = []
                for record in result:
                    rel_data = dict(record["r"])
                    relationship = KnowledgeRelationship(
                        relationship_id=rel_data.get("id", ""),
                        relationship_type=rel_data.get("type", "RELATES_TO"),
                        source_node_id=record["source_id"],
                        target_node_id=record["target_id"],
                        properties=rel_data.get("properties", {}),
                        created_at=rel_data.get("created_at", "")
                    )
                    relationships.append(relationship)
                
                return KnowledgeGraph(
                    nodes=nodes,
                    relationships=relationships,
                    metadata={
                        'project_id': project_id,
                        'total_nodes': len(nodes),
                        'total_relationships': len(relationships),
                        'created_at': datetime.now().isoformat()
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error obteniendo grafo de conocimiento: {e}")
            return KnowledgeGraph(nodes=[], relationships=[], metadata={})
    
    def clear_project_data(self, project_id: str) -> bool:
        """Limpia todos los datos de un proyecto del grafo"""
        try:
            with self.get_session() as session:
                query = """
                MATCH (n)
                WHERE n.id STARTS WITH $project_prefix
                DETACH DELETE n
                """
                
                session.run(query, {'project_prefix': f"project_{project_id}"})
                self.logger.info(f"Datos del proyecto {project_id} eliminados del grafo")
                return True
                
        except Exception as e:
            self.logger.error(f"Error limpiando datos del proyecto: {e}")
            return False
    
    def create_issue_node(self, issue_data: Dict[str, Any], project_id: str) -> str:
        """Crea un nodo de problema/ambigüedad en el grafo"""
        try:
            with self.get_session() as session:
                node_id = f"issue_{issue_data.get('id', 'unknown')}"
                
                query = """
                MERGE (i:Issue {id: $node_id})
                SET i.title = $title,
                    i.description = $description,
                    i.priority = $priority,
                    i.status = $status,
                    i.type = $type,
                    i.project_id = $project_id,
                    i.created_at = datetime(),
                    i.updated_at = datetime()
                RETURN i.id as node_id
                """
                
                result = session.run(query, {
                    'node_id': node_id,
                    'title': issue_data.get('title', ''),
                    'description': issue_data.get('description', ''),
                    'priority': issue_data.get('priority', 'medium'),
                    'status': issue_data.get('status', 'pending'),
                    'type': issue_data.get('type', 'issue'),
                    'project_id': project_id
                })
                
                return result.single()["node_id"]
                
        except Exception as e:
            self.logger.error(f"Error creando nodo de problema: {e}")
            return None
    
    def create_relationship(self, source_id: str, target_id: str, 
                          relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """Crea una relación entre dos nodos"""
        try:
            with self.get_session() as session:
                query = """
                MATCH (source {id: $source_id})
                MATCH (target {id: $target_id})
                MERGE (source)-[r:RELATIONSHIP {type: $rel_type}]->(target)
                SET r += $properties,
                    r.created_at = datetime()
                RETURN r
                """
                
                result = session.run(query, {
                    'source_id': source_id,
                    'target_id': target_id,
                    'rel_type': relationship_type,
                    'properties': properties or {}
                })
                
                return result.single() is not None
                
        except Exception as e:
            self.logger.error(f"Error creando relación: {e}")
            return False
    
    def cleanup_old_projects(self, cutoff_date: datetime) -> int:
        """Limpia proyectos antiguos del grafo"""
        try:
            with self.get_session() as session:
                # Eliminar proyectos y todos sus nodos relacionados
                query = """
                MATCH (p:Project)
                WHERE p.created_at < datetime($cutoff_date)
                DETACH DELETE p
                RETURN count(p) as deleted_count
                """
                
                result = session.run(query, {'cutoff_date': cutoff_date.isoformat()})
                deleted_count = result.single()["deleted_count"]
                
                self.logger.info(f"Limpieza Neo4j: {deleted_count} proyectos eliminados")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error en limpieza de Neo4j: {e}")
            return 0
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del grafo de conocimiento"""
        try:
            with self.get_session() as session:
                # Contar nodos por tipo
                nodes_query = """
                MATCH (n)
                RETURN labels(n)[0] as node_type, count(n) as count
                """
                
                result = session.run(nodes_query)
                node_counts = {record["node_type"]: record["count"] for record in result}
                
                # Contar relaciones por tipo
                rels_query = """
                MATCH ()-[r]->()
                RETURN r.type as rel_type, count(r) as count
                """
                
                result = session.run(rels_query)
                rel_counts = {record["rel_type"]: record["count"] for record in result}
                
                return {
                    'node_counts': node_counts,
                    'relationship_counts': rel_counts,
                    'total_nodes': sum(node_counts.values()),
                    'total_relationships': sum(rel_counts.values())
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def close(self):
        """Cierra la conexión con Neo4j"""
        if self.driver:
            self.driver.close()
            self.logger.info("Conexión con Neo4j cerrada")
