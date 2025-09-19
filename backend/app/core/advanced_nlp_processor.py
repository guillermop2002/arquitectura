"""
Advanced NLP processor using BERT and Transformers for Spanish building regulations.
Implements entity extraction, semantic classification, and document structure analysis.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from pathlib import Path

# Transformers and NLP
from transformers import (
    AutoTokenizer, 
    AutoModel, 
    AutoModelForTokenClassification,
    pipeline,
    BertTokenizer,
    BertForSequenceClassification
)
import torch
import spacy
from spacy import displacy

# Knowledge Graph
import networkx as nx
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL

from .config import get_config
from .logging_config import get_logger
from .error_handling import handle_exception

logger = get_logger(__name__)

@dataclass
class ArchitecturalEntity:
    """Represents an architectural entity extracted from text."""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    context: str
    page_number: int
    document_type: str

@dataclass
class DocumentSection:
    """Represents a structured section of a document."""
    title: str
    content: str
    section_type: str
    page_number: int
    entities: List[ArchitecturalEntity]
    confidence: float

@dataclass
class NormativeRule:
    """Represents a normative rule extracted from regulations."""
    rule_id: str
    title: str
    description: str
    conditions: List[str]
    requirements: List[str]
    applicable_uses: List[str]
    severity: str
    reference: str

class AdvancedNLPProcessor:
    """
    Advanced NLP processor using BERT and specialized models for Spanish building regulations.
    Implements entity extraction, semantic classification, and document structure analysis.
    """
    
    def __init__(self):
        """Initialize the advanced NLP processor."""
        self.config = get_config()
        
        # Model configurations
        self.bert_model_name = "dccuchile/bert-base-spanish-wwm-uncased"
        self.ner_model_name = "mrm8488/bert-spanish-cased-finetuned-ner"
        self.classification_model_name = "microsoft/DialoGPT-medium"
        
        # Initialize models
        self._initialize_models()
        
        # Initialize knowledge graph
        self._initialize_knowledge_graph()
        
        # Architectural entity patterns
        self._initialize_entity_patterns()
        
        # Performance tracking
        self._processing_stats = {
            'documents_processed': 0,
            'entities_extracted': 0,
            'sections_identified': 0,
            'rules_extracted': 0,
            'confidence_scores': []
        }
        
        logger.info("Advanced NLP processor initialized")
    
    def _initialize_models(self):
        """Initialize BERT and other NLP models."""
        try:
            logger.info("Loading BERT models for Spanish text processing...")
            
            # Load Spanish BERT tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.bert_model_name)
            self.bert_model = AutoModel.from_pretrained(self.bert_model_name)
            
            # Load NER pipeline for Spanish
            self.ner_pipeline = pipeline(
                "ner",
                model=self.ner_model_name,
                tokenizer=self.ner_model_name,
                aggregation_strategy="simple"
            )
            
            # Load classification pipeline
            self.classification_pipeline = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True
            )
            
            # Load spaCy Spanish model (optional)
            try:
                self.nlp = spacy.load("es_core_news_sm")
                logger.info("Spanish spaCy model loaded successfully")
            except OSError:
                logger.warning("Spanish spaCy model not found. Continuing without advanced NLP features...")
                self.nlp = None
            
            logger.info("All NLP models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NLP models: {e}")
            raise
    
    def _initialize_knowledge_graph(self):
        """Initialize knowledge graph for architectural concepts."""
        try:
            # Create RDF graph
            self.kg = Graph()
            
            # Define namespaces
            self.cte = Namespace("http://example.org/cte#")
            self.arch = Namespace("http://example.org/architecture#")
            self.madrid = Namespace("http://example.org/madrid#")
            
            # Bind namespaces
            self.kg.bind("cte", self.cte)
            self.kg.bind("arch", self.arch)
            self.kg.bind("madrid", self.madrid)
            
            # Create NetworkX graph for relationships
            self.nx_graph = nx.DiGraph()
            
            # Load architectural ontology
            self._load_architectural_ontology()
            
            logger.info("Knowledge graph initialized")
            
        except Exception as e:
            logger.error(f"Error initializing knowledge graph: {e}")
            raise
    
    def _load_architectural_ontology(self):
        """Load architectural ontology with Spanish building concepts."""
        try:
            # Define architectural concepts
            concepts = {
                # Building types
                "residencial": {
                    "type": "BuildingType",
                    "description": "Edificio de uso residencial",
                    "cte_sections": ["DB-SI", "DB-SU", "DB-HE"],
                    "requirements": ["accesibilidad", "evacuacion", "eficiencia_energetica"]
                },
                "comercial": {
                    "type": "BuildingType", 
                    "description": "Edificio de uso comercial",
                    "cte_sections": ["DB-SI", "DB-SU", "DB-HE", "DB-HR"],
                    "requirements": ["accesibilidad", "evacuacion", "eficiencia_energetica", "proteccion_ruido"]
                },
                "oficinas": {
                    "type": "BuildingType",
                    "description": "Edificio de oficinas",
                    "cte_sections": ["DB-SI", "DB-SU", "DB-HE"],
                    "requirements": ["accesibilidad", "evacuacion", "eficiencia_energetica"]
                },
                
                # Architectural elements
                "puerta": {
                    "type": "ArchitecturalElement",
                    "description": "Puerta de paso",
                    "properties": ["ancho", "alto", "material", "resistencia_fuego"],
                    "requirements": ["accesibilidad", "evacuacion"]
                },
                "ventana": {
                    "type": "ArchitecturalElement",
                    "description": "Ventana o hueco",
                    "properties": ["ancho", "alto", "material", "transmitancia"],
                    "requirements": ["eficiencia_energetica", "iluminacion"]
                },
                "escalera": {
                    "type": "ArchitecturalElement",
                    "description": "Escalera de acceso o evacuación",
                    "properties": ["ancho", "huella", "contrahuella", "material"],
                    "requirements": ["accesibilidad", "evacuacion", "seguridad"]
                },
                "rampa": {
                    "type": "ArchitecturalElement",
                    "description": "Rampa de acceso",
                    "properties": ["ancho", "pendiente", "longitud", "material"],
                    "requirements": ["accesibilidad"]
                },
                
                # Normative requirements
                "accesibilidad": {
                    "type": "NormativeRequirement",
                    "description": "Requisitos de accesibilidad universal",
                    "cte_reference": "DB-SU",
                    "madrid_specific": True,
                    "parameters": ["ancho_puertas", "pendiente_rampas", "altura_pasamanos"]
                },
                "evacuacion": {
                    "type": "NormativeRequirement",
                    "description": "Requisitos de evacuación y seguridad",
                    "cte_reference": "DB-SI",
                    "madrid_specific": False,
                    "parameters": ["distancia_evacuacion", "ancho_escaleras", "resistencia_fuego"]
                },
                "eficiencia_energetica": {
                    "type": "NormativeRequirement",
                    "description": "Requisitos de eficiencia energética",
                    "cte_reference": "DB-HE",
                    "madrid_specific": False,
                    "parameters": ["transmitancia_termica", "demanda_energetica", "renovables"]
                }
            }
            
            # Add concepts to knowledge graph
            for concept_name, concept_data in concepts.items():
                concept_uri = self.arch[concept_name]
                
                # Add concept to RDF graph
                self.kg.add((concept_uri, RDF.type, OWL.Class))
                self.kg.add((concept_uri, RDFS.label, Literal(concept_data["description"])))
                self.kg.add((concept_uri, RDFS.comment, Literal(concept_data["description"])))
                
                # Add to NetworkX graph
                self.nx_graph.add_node(concept_name, **concept_data)
                
                # Add relationships
                if "cte_sections" in concept_data:
                    for section in concept_data["cte_sections"]:
                        self.kg.add((concept_uri, self.cte.appliesTo, self.cte[section]))
                        self.nx_graph.add_edge(concept_name, section, relationship="applies_to")
                
                if "requirements" in concept_data:
                    for req in concept_data["requirements"]:
                        self.kg.add((concept_uri, self.arch.hasRequirement, self.arch[req]))
                        self.nx_graph.add_edge(concept_name, req, relationship="has_requirement")
            
            logger.info(f"Loaded {len(concepts)} architectural concepts")
            
        except Exception as e:
            logger.error(f"Error loading architectural ontology: {e}")
            raise
    
    def _initialize_entity_patterns(self):
        """Initialize regex patterns for architectural entity extraction."""
        self.entity_patterns = {
            # Dimensions
            'dimension': [
                r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*m',
                r'(\d+(?:\.\d+)?)\s*metros?',
                r'(\d+(?:\.\d+)?)\s*cm',
                r'(\d+(?:\.\d+)?)\s*mm'
            ],
            
            # Areas
            'area': [
                r'(\d+(?:\.\d+)?)\s*m²',
                r'(\d+(?:\.\d+)?)\s*metros?\s*cuadrados?',
                r'superficie[\s:]+(\d+(?:\.\d+)?)\s*m²'
            ],
            
            # Building elements
            'puerta': [
                r'puerta[\s:]+([^\\n]+)',
                r'ancho[\s:]+(\d+(?:\.\d+)?)\s*m[\s]*[^\\n]*puerta',
                r'puerta[\s:]+(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)'
            ],
            'ventana': [
                r'ventana[\s:]+([^\\n]+)',
                r'hueco[\s:]+([^\\n]+)',
                r'vanos?[\s:]+([^\\n]+)'
            ],
            'escalera': [
                r'escalera[\s:]+([^\\n]+)',
                r'huella[\s:]+(\d+(?:\.\d+)?)\s*cm',
                r'contrahuella[\s:]+(\d+(?:\.\d+)?)\s*cm'
            ],
            'rampa': [
                r'rampa[\s:]+([^\\n]+)',
                r'pendiente[\s:]+(\d+(?:\.\d+)?)\s*%',
                r'slope[\s:]+(\d+(?:\.\d+)?)\s*%'
            ],
            
            # Materials
            'material': [
                r'material[\s:]+([^\\n]+)',
                r'construcción[\s:]+([^\\n]+)',
                r'estructura[\s:]+([^\\n]+)'
            ],
            
            # Technical specifications
            'resistencia_fuego': [
                r'resistencia[\s:]+([^\\n]+)',
                r'rf-(\d+)',
                r'clasificación[\s:]+([^\\n]+)'
            ],
            'transmitancia': [
                r'transmitancia[\s:]+(\d+(?:\.\d+)?)\s*w/m²k',
                r'u[\s:]+(\d+(?:\.\d+)?)\s*w/m²k',
                r'coeficiente[\s:]+(\d+(?:\.\d+)?)\s*w/m²k'
            ],
            'demanda_energetica': [
                r'demanda[\s:]+(\d+(?:\.\d+)?)\s*kwh/m²año',
                r'consumo[\s:]+(\d+(?:\.\d+)?)\s*kwh/m²año'
            ]
        }
    
    @handle_exception
    def extract_architectural_entities(self, text: str, page_number: int = 0, document_type: str = "unknown") -> List[ArchitecturalEntity]:
        """
        Extract architectural entities from text using BERT and pattern matching.
        
        Args:
            text: Input text to analyze
            page_number: Page number for reference
            document_type: Type of document (memoria, plano, etc.)
            
        Returns:
            List of extracted architectural entities
        """
        try:
            entities = []
            
            # Use BERT NER for general entity extraction
            ner_results = self.ner_pipeline(text)
            
            for result in ner_results:
                if result['score'] > 0.7:  # High confidence threshold
                    entity = ArchitecturalEntity(
                        text=result['word'],
                        label=result['entity_group'],
                        start=result['start'],
                        end=result['end'],
                        confidence=result['score'],
                        context=self._get_context(text, result['start'], result['end']),
                        page_number=page_number,
                        document_type=document_type
                    )
                    entities.append(entity)
            
            # Use pattern matching for architectural-specific entities
            pattern_entities = self._extract_pattern_entities(text, page_number, document_type)
            entities.extend(pattern_entities)
            
            # Use spaCy for additional entity extraction
            spacy_entities = self._extract_spacy_entities(text, page_number, document_type)
            entities.extend(spacy_entities)
            
            # Remove duplicates and sort by confidence
            entities = self._deduplicate_entities(entities)
            entities.sort(key=lambda x: x.confidence, reverse=True)
            
            self._processing_stats['entities_extracted'] += len(entities)
            
            logger.info(f"Extracted {len(entities)} architectural entities from page {page_number}")
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting architectural entities: {e}")
            return []
    
    def _extract_pattern_entities(self, text: str, page_number: int, document_type: str) -> List[ArchitecturalEntity]:
        """Extract entities using regex patterns."""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = ArchitecturalEntity(
                        text=match.group(0),
                        label=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.8,  # Pattern matching confidence
                        context=self._get_context(text, match.start(), match.end()),
                        page_number=page_number,
                        document_type=document_type
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_spacy_entities(self, text: str, page_number: int, document_type: str) -> List[ArchitecturalEntity]:
        """Extract entities using spaCy."""
        entities = []
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'LOC', 'MISC', 'PER']:  # Relevant spaCy labels
                entity = ArchitecturalEntity(
                    text=ent.text,
                    label=f"spacy_{ent.label_}",
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.7,  # spaCy confidence
                    context=self._get_context(text, ent.start_char, ent.end_char),
                    page_number=page_number,
                    document_type=document_type
                )
                entities.append(entity)
        
        return entities
    
    def _get_context(self, text: str, start: int, end: int, context_window: int = 50) -> str:
        """Get context around an entity."""
        context_start = max(0, start - context_window)
        context_end = min(len(text), end + context_window)
        return text[context_start:context_end].strip()
    
    def _deduplicate_entities(self, entities: List[ArchitecturalEntity]) -> List[ArchitecturalEntity]:
        """Remove duplicate entities based on text and position."""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.text.lower(), entity.start, entity.end)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    @handle_exception
    def analyze_document_structure(self, pages: List[Dict[str, Any]]) -> List[DocumentSection]:
        """
        Analyze document structure and identify sections.
        
        Args:
            pages: List of page data from OCR processor
            
        Returns:
            List of identified document sections
        """
        try:
            sections = []
            
            for page in pages:
                text = page.get('text', '')
                page_number = page.get('page_number', 0)
                
                if not text:
                    continue
                
                # Identify section headers
                section_headers = self._identify_section_headers(text)
                
                # Extract entities for this page
                entities = self.extract_architectural_entities(text, page_number, "memoria")
                
                # Create sections
                for header in section_headers:
                    section = DocumentSection(
                        title=header['title'],
                        content=header['content'],
                        section_type=header['type'],
                        page_number=page_number,
                        entities=entities,
                        confidence=header['confidence']
                    )
                    sections.append(section)
            
            self._processing_stats['sections_identified'] += len(sections)
            
            logger.info(f"Identified {len(sections)} document sections")
            
            return sections
            
        except Exception as e:
            logger.error(f"Error analyzing document structure: {e}")
            return []
    
    def _identify_section_headers(self, text: str) -> List[Dict[str, Any]]:
        """Identify section headers in text."""
        sections = []
        
        # Common section patterns
        section_patterns = [
            r'^\s*(\d+\.?\s+[A-ZÁÉÍÓÚÑ][^\\n]+)$',  # Numbered sections
            r'^\s*([A-ZÁÉÍÓÚÑ][^\\n]{10,50})$',     # All caps sections
            r'^\s*(MEMORIA|PLANOS|CÁLCULOS|INSTALACIONES)[^\\n]*$',  # Specific sections
        ]
        
        lines = text.split('\\n')
        
        for i, line in enumerate(lines):
            for pattern in section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    title = match.group(1).strip()
                    
                    # Get content until next section or end
                    content_start = i + 1
                    content_end = len(lines)
                    
                    for j in range(i + 1, len(lines)):
                        if re.match(r'^\s*(\d+\.?\s+[A-ZÁÉÍÓÚÑ]|MEMORIA|PLANOS|CÁLCULOS|INSTALACIONES)', lines[j]):
                            content_end = j
                            break
                    
                    content = '\\n'.join(lines[content_start:content_end])
                    
                    # Classify section type
                    section_type = self._classify_section_type(title)
                    
                    sections.append({
                        'title': title,
                        'content': content,
                        'type': section_type,
                        'confidence': 0.8
                    })
                    break
        
        return sections
    
    def _classify_section_type(self, title: str) -> str:
        """Classify section type based on title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['memoria', 'descripción', 'justificación']):
            return 'memoria'
        elif any(word in title_lower for word in ['planos', 'planta', 'alzado', 'sección']):
            return 'planos'
        elif any(word in title_lower for word in ['cálculo', 'cálculos', 'justificación']):
            return 'calculos'
        elif any(word in title_lower for word in ['instalaciones', 'instalación']):
            return 'instalaciones'
        elif any(word in title_lower for word in ['estructura', 'estructural']):
            return 'estructura'
        else:
            return 'general'
    
    @handle_exception
    def extract_normative_rules(self, normative_text: str) -> List[NormativeRule]:
        """
        Extract normative rules from regulatory documents.
        
        Args:
            normative_text: Text from normative documents
            
        Returns:
            List of extracted normative rules
        """
        try:
            rules = []
            
            # Pattern for rule extraction
            rule_patterns = [
                r'Artículo\s+(\d+)[^\\n]*\\n([^\\n]+)',
                r'Sección\s+(\d+)[^\\n]*\\n([^\\n]+)',
                r'(\d+\.\d+)[^\\n]*\\n([^\\n]+)',
            ]
            
            for pattern in rule_patterns:
                matches = re.finditer(pattern, normative_text, re.MULTILINE)
                for match in matches:
                    rule_id = match.group(1)
                    content = match.group(2)
                    
                    # Extract requirements and conditions
                    requirements = self._extract_requirements(content)
                    conditions = self._extract_conditions(content)
                    
                    # Determine applicable uses
                    applicable_uses = self._determine_applicable_uses(content)
                    
                    # Determine severity
                    severity = self._determine_rule_severity(content)
                    
                    rule = NormativeRule(
                        rule_id=rule_id,
                        title=f"Artículo {rule_id}",
                        description=content,
                        conditions=conditions,
                        requirements=requirements,
                        applicable_uses=applicable_uses,
                        severity=severity,
                        reference=f"CTE-{rule_id}"
                    )
                    rules.append(rule)
            
            self._processing_stats['rules_extracted'] += len(rules)
            
            logger.info(f"Extracted {len(rules)} normative rules")
            
            return rules
            
        except Exception as e:
            logger.error(f"Error extracting normative rules: {e}")
            return []
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements from rule text."""
        requirements = []
        
        # Pattern for requirements
        req_patterns = [
            r'debe\s+([^\\n]+)',
            r'deberá\s+([^\\n]+)',
            r'será\s+([^\\n]+)',
            r'no\s+podrá\s+([^\\n]+)',
        ]
        
        for pattern in req_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            requirements.extend(matches)
        
        return requirements
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditions from rule text."""
        conditions = []
        
        # Pattern for conditions
        cond_patterns = [
            r'cuando\s+([^\\n]+)',
            r'si\s+([^\\n]+)',
            r'en\s+el\s+caso\s+de\s+([^\\n]+)',
        ]
        
        for pattern in cond_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            conditions.extend(matches)
        
        return conditions
    
    def _determine_applicable_uses(self, text: str) -> List[str]:
        """Determine applicable building uses for a rule."""
        text_lower = text.lower()
        uses = []
        
        if any(word in text_lower for word in ['residencial', 'vivienda', 'habitación']):
            uses.append('residencial')
        if any(word in text_lower for word in ['comercial', 'comercio', 'tienda']):
            uses.append('comercial')
        if any(word in text_lower for word in ['oficinas', 'oficina', 'administrativo']):
            uses.append('oficinas')
        if any(word in text_lower for word in ['público', 'pública', 'uso público']):
            uses.append('publico')
        
        return uses if uses else ['general']
    
    def _determine_rule_severity(self, text: str) -> str:
        """Determine rule severity based on text content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['obligatorio', 'debe', 'deberá', 'prohibido']):
            return 'HIGH'
        elif any(word in text_lower for word in ['recomendado', 'se recomienda', 'opcional']):
            return 'LOW'
        else:
            return 'MEDIUM'
    
    @handle_exception
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using BERT.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Tokenize texts
            inputs1 = self.tokenizer(text1, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs2 = self.tokenizer(text2, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            # Get embeddings
            with torch.no_grad():
                outputs1 = self.bert_model(**inputs1)
                outputs2 = self.bert_model(**inputs2)
                
                # Use [CLS] token embedding
                embedding1 = outputs1.last_hidden_state[:, 0, :]
                embedding2 = outputs2.last_hidden_state[:, 0, :]
                
                # Calculate cosine similarity
                similarity = torch.cosine_similarity(embedding1, embedding2, dim=1)
                
                return similarity.item()
                
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            **self._processing_stats,
            'avg_confidence': np.mean(self._processing_stats['confidence_scores']) if self._processing_stats['confidence_scores'] else 0.0,
            'knowledge_graph_nodes': self.nx_graph.number_of_nodes(),
            'knowledge_graph_edges': self.nx_graph.number_of_edges()
        }
    
    def save_knowledge_graph(self, filepath: str):
        """Save knowledge graph to file."""
        try:
            # Save RDF graph
            self.kg.serialize(destination=filepath + ".ttl", format="turtle")
            
            # Save NetworkX graph
            nx.write_gpickle(self.nx_graph, filepath + ".gpickle")
            
            logger.info(f"Knowledge graph saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving knowledge graph: {e}")
    
    def load_knowledge_graph(self, filepath: str):
        """Load knowledge graph from file."""
        try:
            # Load RDF graph
            self.kg.parse(filepath + ".ttl", format="turtle")
            
            # Load NetworkX graph
            self.nx_graph = nx.read_gpickle(filepath + ".gpickle")
            
            logger.info(f"Knowledge graph loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {e}")