"""
Enhanced project analyzer with advanced NLP integration.
Combines existing functionality with BERT-based analysis and advanced rule engine.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .ai_client import get_ai_client, AIResponse
from .error_handling import handle_exception
from .logging_config import get_logger
from .enhanced_prompts import (
    get_structured_data_extraction_prompt,
    get_contradiction_detection_prompt,
    get_fire_safety_compliance_prompt,
    get_safety_use_compliance_prompt,
    get_energy_efficiency_compliance_prompt,
    get_question_generation_prompt,
    get_answer_processing_prompt
)
from .advanced_nlp_processor import AdvancedNLPProcessor, ArchitecturalEntity, DocumentSection
from .advanced_rule_engine import AdvancedRuleEngine, RuleEvaluationResult

from ..models.schemas import (
    Issue, 
    Question, 
    ProjectData, 
    SeverityLevel,
    DocumentType
)

logger = get_logger(__name__)

class EnhancedProjectAnalyzerV2:
    """
    Enhanced project analyzer with advanced NLP integration.
    Combines existing functionality with BERT-based analysis and advanced rule engine.
    """
    
    def __init__(self):
        """Initialize the enhanced project analyzer."""
        # Get AI client
        self.ai_client = get_ai_client()
        
        # Get configuration
        from .config import get_config
        self.config = get_config()
        
        # Initialize advanced components
        self.nlp_processor = AdvancedNLPProcessor()
        self.rule_engine = AdvancedRuleEngine()
        
        # Text processing limits
        self.max_text_length = 20000
        self.chunk_overlap = 1000
        
        # Performance optimization
        self._text_cache = {}
        self._max_cache_size = 100
        self._processing_stats = {
            'total_analyses': 0,
            'successful_extractions': 0,
            'contradictions_detected': 0,
            'compliance_checks': 0,
            'entities_extracted': 0,
            'rules_evaluated': 0
        }
        
        logger.info("Enhanced project analyzer V2 initialized")
    
    @handle_exception
    def check_annexe_i_compliance(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance with Annexe I requirements using advanced NLP.
        
        Args:
            extracted_data: Dictionary with page-by-page extracted data
            
        Returns:
            Dictionary with compliance results
        """
        try:
            logger.info("Starting Annexe I compliance check with advanced NLP")
            
            # Load Annexe I requirements
            from .data_loader import DataLoader
            data_loader = DataLoader()
            requirements = data_loader.get_annexe_i_requirements()
            
            if not requirements:
                logger.warning("No Annexe I requirements loaded")
                return {
                    'status': 'incompleto',
                    'found_documents': [],
                    'missing_documents': [],
                    'confidence': 0.0,
                    'errors': ['No requirements loaded']
                }
            
            # Process each file's pages with advanced NLP
            found_documents = []
            missing_documents = []
            document_pages = {}
            total_pages_processed = 0
            
            for file_name, file_data in extracted_data.items():
                pages = file_data.get('pages', [])
                total_pages_processed += len(pages)
                
                # Analyze document structure
                sections = self.nlp_processor.analyze_document_structure(pages)
                
                # Extract entities from all pages
                all_entities = []
                for page in pages:
                    entities = self.nlp_processor.extract_architectural_entities(
                        page.get('text', ''),
                        page.get('page_number', 0),
                        file_name
                    )
                    all_entities.extend(entities)
                
                # Check for required documents using advanced NLP
                file_requirements = self._check_file_requirements_advanced(
                    file_name, sections, all_entities, requirements
                )
                
                if file_requirements['found']:
                    found_documents.extend(file_requirements['found'])
                    document_pages[file_name] = {
                        'pages': len(pages),
                        'sections': len(sections),
                        'entities': len(all_entities)
                    }
                else:
                    missing_documents.extend(file_requirements['missing'])
            
            # Calculate overall confidence
            confidence = self._calculate_annexe_confidence(found_documents, missing_documents, total_pages_processed)
            
            # Determine status
            status = 'completo' if len(missing_documents) == 0 else 'incompleto'
            
            result = {
                'status': status,
                'found_documents': found_documents,
                'missing_documents': missing_documents,
                'confidence': confidence,
                'document_pages': document_pages,
                'total_pages_processed': total_pages_processed,
                'entities_extracted': sum(len(entities) for entities in [self.nlp_processor.extract_architectural_entities(page.get('text', ''), page.get('page_number', 0), '') for file_data in extracted_data.values() for page in file_data.get('pages', [])])
            }
            
            self._processing_stats['successful_extractions'] += 1
            
            logger.info(f"Annexe I compliance check completed. Found: {len(found_documents)}, Missing: {len(missing_documents)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Annexe I compliance check: {e}")
            return {
                'status': 'error',
                'found_documents': [],
                'missing_documents': [],
                'confidence': 0.0,
                'errors': [str(e)]
            }
    
    def _check_file_requirements_advanced(self, file_name: str, sections: List[DocumentSection], entities: List[ArchitecturalEntity], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check file requirements using advanced NLP analysis."""
        found = []
        missing = []
        
        # Analyze file name
        file_name_lower = file_name.lower()
        
        # Check for required document types
        for req_name, req_data in requirements.items():
            req_keywords = req_data.get('keywords', [])
            req_sections = req_data.get('sections', [])
            
            # Check file name keywords
            name_match = any(keyword in file_name_lower for keyword in req_keywords)
            
            # Check section titles
            section_match = any(
                any(keyword in section.title.lower() for keyword in req_keywords)
                for section in sections
            )
            
            # Check entity types
            entity_match = any(
                any(keyword in entity.text.lower() for keyword in req_keywords)
                for entity in entities
            )
            
            # Calculate confidence
            confidence = 0.0
            if name_match:
                confidence += 0.4
            if section_match:
                confidence += 0.3
            if entity_match:
                confidence += 0.3
            
            if confidence >= 0.5:  # Threshold for document detection
                found.append({
                    'name': req_name,
                    'confidence': confidence,
                    'evidence': {
                        'file_name': name_match,
                        'sections': section_match,
                        'entities': entity_match
                    }
                })
            else:
                missing.append({
                    'name': req_name,
                    'confidence': confidence,
                    'evidence': {
                        'file_name': name_match,
                        'sections': section_match,
                        'entities': entity_match
                    }
                })
        
        return {
            'found': found,
            'missing': missing
        }
    
    def _calculate_annexe_confidence(self, found_documents: List[Dict], missing_documents: List[Dict], total_pages: int) -> float:
        """Calculate confidence for Annexe I compliance."""
        if not found_documents and not missing_documents:
            return 0.0
        
        # Base confidence from document detection
        total_docs = len(found_documents) + len(missing_documents)
        found_ratio = len(found_documents) / total_docs if total_docs > 0 else 0
        
        # Confidence from individual documents
        avg_confidence = sum(doc['confidence'] for doc in found_documents) / len(found_documents) if found_documents else 0
        
        # Page count factor
        page_factor = min(1.0, total_pages / 50)  # Normalize to 50 pages
        
        # Combine factors
        confidence = (found_ratio * 0.6 + avg_confidence * 0.3 + page_factor * 0.1)
        
        return min(1.0, confidence)
    
    @handle_exception
    def extract_project_data(self, extracted_data: Dict[str, Any]) -> ProjectData:
        """
        Extract project data using advanced NLP analysis.
        
        Args:
            extracted_data: Dictionary with page-by-page extracted data
            
        Returns:
            ProjectData object with extracted information
        """
        try:
            logger.info("Starting advanced project data extraction")
            
            # Combine all text for analysis
            all_text = self._combine_extracted_text(extracted_data)
            
            # Extract entities from all text
            all_entities = []
            for file_name, file_data in extracted_data.items():
                for page in file_data.get('pages', []):
                    entities = self.nlp_processor.extract_architectural_entities(
                        page.get('text', ''),
                        page.get('page_number', 0),
                        file_name
                    )
                    all_entities.extend(entities)
            
            # Analyze document structure
            all_sections = []
            for file_name, file_data in extracted_data.items():
                sections = self.nlp_processor.analyze_document_structure(file_data.get('pages', []))
                all_sections.extend(sections)
            
            # Extract project data using AI and NLP
            project_data = self._extract_project_data_advanced(all_text, all_entities, all_sections)
            
            self._processing_stats['successful_extractions'] += 1
            
            logger.info("Advanced project data extraction completed")
            
            return project_data
            
        except Exception as e:
            logger.error(f"Error in advanced project data extraction: {e}")
            # Return minimal project data
            return ProjectData(
                building_use="desconocido",
                total_area=0.0,
                height=0.0,
                floors=0,
                location="",
                construction_type="",
                max_occupancy=0
            )
    
    def _combine_extracted_text(self, extracted_data: Dict[str, Any]) -> str:
        """Combine text from all extracted data."""
        combined_text = ""
        
        for file_name, file_data in extracted_data.items():
            for page in file_data.get('pages', []):
                text = page.get('text', '')
                if text:
                    combined_text += f"\\n--- {file_name} Página {page.get('page_number', 0)} ---\\n"
                    combined_text += text + "\\n"
        
        return combined_text
    
    def _extract_project_data_advanced(self, text: str, entities: List[ArchitecturalEntity], sections: List[DocumentSection]) -> ProjectData:
        """Extract project data using advanced NLP and AI."""
        try:
            # Use AI for structured extraction
            prompt = get_structured_data_extraction_prompt(text[:self.max_text_length])
            ai_response = self.ai_client.generate_response(prompt)
            
            # Parse AI response
            project_data_dict = self._parse_ai_response(ai_response.content)
            
            # Enhance with entity extraction
            project_data_dict = self._enhance_with_entities(project_data_dict, entities)
            
            # Enhance with section analysis
            project_data_dict = self._enhance_with_sections(project_data_dict, sections)
            
            # Create ProjectData object
            project_data = ProjectData(
                building_use=project_data_dict.get('building_use', 'desconocido'),
                total_area=float(project_data_dict.get('total_area', 0)),
                height=float(project_data_dict.get('height', 0)),
                floors=int(project_data_dict.get('floors', 0)),
                location=project_data_dict.get('location', ''),
                construction_type=project_data_dict.get('construction_type', ''),
                max_occupancy=int(project_data_dict.get('max_occupancy', 0))
            )
            
            return project_data
            
        except Exception as e:
            logger.error(f"Error in advanced project data extraction: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response to extract project data."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\\{.*\\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback: extract key-value pairs
            data = {}
            patterns = {
                'building_use': r'uso[\\s:]+([^\\n]+)',
                'total_area': r'superficie[\\s:]+(\\d+(?:\\.\\d+)?)',
                'height': r'altura[\\s:]+(\\d+(?:\\.\\d+)?)',
                'floors': r'plantas?[\\s:]+(\\d+)',
                'location': r'ubicación[\\s:]+([^\\n]+)',
                'construction_type': r'construcción[\\s:]+([^\\n]+)',
                'max_occupancy': r'aforo[\\s:]+(\\d+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    data[key] = match.group(1)
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return {}
    
    def _enhance_with_entities(self, project_data: Dict[str, Any], entities: List[ArchitecturalEntity]) -> Dict[str, Any]:
        """Enhance project data with extracted entities."""
        try:
            # Extract dimensions
            dimensions = [e for e in entities if e.label == 'dimension']
            if dimensions:
                # Use the most confident dimension
                best_dimension = max(dimensions, key=lambda x: x.confidence)
                project_data['dimensions'] = best_dimension.text
            
            # Extract materials
            materials = [e for e in entities if e.label == 'material']
            if materials:
                project_data['materials'] = [m.text for m in materials]
            
            # Extract areas
            areas = [e for e in entities if e.label == 'area']
            if areas:
                # Extract numeric value
                area_match = re.search(r'(\\d+(?:\\.\\d+)?)', areas[0].text)
                if area_match:
                    project_data['total_area'] = float(area_match.group(1))
            
            return project_data
            
        except Exception as e:
            logger.error(f"Error enhancing with entities: {e}")
            return project_data
    
    def _enhance_with_sections(self, project_data: Dict[str, Any], sections: List[DocumentSection]) -> Dict[str, Any]:
        """Enhance project data with section analysis."""
        try:
            # Find relevant sections
            for section in sections:
                if section.section_type == 'memoria':
                    # Extract building use from memory section
                    if 'residencial' in section.content.lower():
                        project_data['building_use'] = 'residencial'
                    elif 'comercial' in section.content.lower():
                        project_data['building_use'] = 'comercial'
                    elif 'oficinas' in section.content.lower():
                        project_data['building_use'] = 'oficinas'
                
                elif section.section_type == 'calculos':
                    # Extract technical data from calculations
                    area_match = re.search(r'superficie[\\s:]+(\\d+(?:\\.\\d+)?)', section.content, re.IGNORECASE)
                    if area_match:
                        project_data['total_area'] = float(area_match.group(1))
            
            return project_data
            
        except Exception as e:
            logger.error(f"Error enhancing with sections: {e}")
            return project_data
    
    @handle_exception
    def check_complete_compliance(self, project_data: ProjectData, extracted_data: Dict[str, Any], normative_docs: Dict[str, str]) -> Dict[str, Any]:
        """
        Check complete compliance using advanced rule engine and NLP.
        
        Args:
            project_data: Project data to check
            extracted_data: Extracted data from documents
            normative_docs: Normative documents
            
        Returns:
            Dictionary with compliance results
        """
        try:
            logger.info("Starting complete compliance check with advanced analysis")
            
            # Convert project data to dictionary for rule engine
            project_dict = project_data.dict()
            
            # Add extracted data context
            project_dict.update(self._extract_context_from_data(extracted_data))
            
            # Evaluate rules using advanced rule engine
            rule_results = self.rule_engine.evaluate_rules(project_dict)
            
            # Generate issues from rule results
            issues = self.rule_engine.generate_issues_from_results(rule_results)
            
            # Add AI-based compliance checking
            ai_issues = self._check_compliance_with_ai(project_data, extracted_data, normative_docs)
            issues.extend(ai_issues)
            
            # Calculate overall confidence
            confidence = self._calculate_compliance_confidence(rule_results, issues)
            
            self._processing_stats['compliance_checks'] += 1
            self._processing_stats['rules_evaluated'] += len(rule_results)
            
            logger.info(f"Complete compliance check completed. Found {len(issues)} issues")
            
            return {
                'issues': issues,
                'confidence': confidence,
                'rule_results': rule_results,
                'total_rules_evaluated': len(rule_results),
                'rules_passed': len([r for r in rule_results if r.passed]),
                'rules_failed': len([r for r in rule_results if not r.passed])
            }
            
        except Exception as e:
            logger.error(f"Error in complete compliance check: {e}")
            return {
                'issues': [],
                'confidence': 0.0,
                'rule_results': [],
                'total_rules_evaluated': 0,
                'rules_passed': 0,
                'rules_failed': 0,
                'errors': [str(e)]
            }
    
    def _extract_context_from_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context information from extracted data."""
        context = {}
        
        # Extract entities from all data
        all_entities = []
        for file_name, file_data in extracted_data.items():
            for page in file_data.get('pages', []):
                entities = self.nlp_processor.extract_architectural_entities(
                    page.get('text', ''),
                    page.get('page_number', 0),
                    file_name
                )
                all_entities.extend(entities)
        
        # Group entities by type
        entity_groups = {}
        for entity in all_entities:
            if entity.label not in entity_groups:
                entity_groups[entity.label] = []
            entity_groups[entity.label].append(entity.text)
        
        # Add to context
        for label, texts in entity_groups.items():
            context[label] = texts
        
        return context
    
    def _check_compliance_with_ai(self, project_data: ProjectData, extracted_data: Dict[str, Any], normative_docs: Dict[str, str]) -> List[Issue]:
        """Check compliance using AI analysis."""
        try:
            issues = []
            
            # Combine text for AI analysis
            all_text = self._combine_extracted_text(extracted_data)
            
            # Check fire safety compliance
            fire_prompt = get_fire_safety_compliance_prompt(all_text[:self.max_text_length])
            fire_response = self.ai_client.generate_response(fire_prompt)
            fire_issues = self._parse_ai_issues(fire_response.content, "Seguridad contra incendios")
            issues.extend(fire_issues)
            
            # Check safety of use compliance
            safety_prompt = get_safety_use_compliance_prompt(all_text[:self.max_text_length])
            safety_response = self.ai_client.generate_response(safety_prompt)
            safety_issues = self._parse_ai_issues(safety_response.content, "Seguridad de uso")
            issues.extend(safety_issues)
            
            # Check energy efficiency compliance
            energy_prompt = get_energy_efficiency_compliance_prompt(all_text[:self.max_text_length])
            energy_response = self.ai_client.generate_response(energy_prompt)
            energy_issues = self._parse_ai_issues(energy_response.content, "Eficiencia energética")
            issues.extend(energy_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error in AI compliance checking: {e}")
            return []
    
    def _parse_ai_issues(self, response: str, category: str) -> List[Issue]:
        """Parse AI response to extract issues."""
        try:
            issues = []
            
            # Look for issue patterns in response
            issue_patterns = [
                r'\\*\\*Problema\\*\\*:([^\\n]+)',
                r'\\*\\*Incumplimiento\\*\\*:([^\\n]+)',
                r'\\*\\*Error\\*\\*:([^\\n]+)',
                r'\\*\\*Deficiencia\\*\\*:([^\\n]+)'
            ]
            
            for pattern in issue_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                for match in matches:
                    issue = Issue(
                        title=match.strip(),
                        description=f"Análisis AI - {category}",
                        severity=SeverityLevel.MEDIUM,
                        reference="Análisis AI",
                        file_name="Sistema",
                        page_number=0,
                        confidence=0.7
                    )
                    issues.append(issue)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error parsing AI issues: {e}")
            return []
    
    def _calculate_compliance_confidence(self, rule_results: List[RuleEvaluationResult], issues: List[Issue]) -> float:
        """Calculate confidence for compliance results."""
        if not rule_results:
            return 0.0
        
        # Calculate average confidence from rule results
        avg_rule_confidence = sum(r.confidence for r in rule_results) / len(rule_results)
        
        # Calculate confidence from issues
        issue_confidence = 1.0 - (len(issues) / (len(rule_results) * 2))  # Normalize by number of rules
        
        # Combine confidences
        confidence = (avg_rule_confidence * 0.7 + issue_confidence * 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    @handle_exception
    def generate_questions(self, extracted_data: Dict[str, Any], issues: List[Issue]) -> List[Question]:
        """
        Generate questions using advanced NLP analysis.
        
        Args:
            extracted_data: Extracted data from documents
            issues: List of compliance issues
            
        Returns:
            List of generated questions
        """
        try:
            logger.info("Generating questions with advanced NLP")
            
            questions = []
            
            # Generate questions based on issues
            for issue in issues:
                if issue.severity in [SeverityLevel.HIGH, SeverityLevel.MEDIUM]:
                    question = self._generate_question_for_issue(issue, extracted_data)
                    if question:
                        questions.append(question)
            
            # Generate questions based on missing information
            missing_info_questions = self._generate_missing_info_questions(extracted_data)
            questions.extend(missing_info_questions)
            
            # Generate questions based on contradictions
            contradiction_questions = self._generate_contradiction_questions(extracted_data)
            questions.extend(contradiction_questions)
            
            self._processing_stats['contradictions_detected'] += len(contradiction_questions)
            
            logger.info(f"Generated {len(questions)} questions")
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
    
    def _generate_question_for_issue(self, issue: Issue, extracted_data: Dict[str, Any]) -> Optional[Question]:
        """Generate a question for a specific issue."""
        try:
            # Use AI to generate contextual question
            prompt = get_question_generation_prompt(issue.title, issue.description)
            ai_response = self.ai_client.generate_response(prompt)
            
            # Parse AI response
            question_text = ai_response.content.strip()
            
            if question_text and len(question_text) > 10:
                return Question(
                    question_id=f"q_{len(extracted_data)}",
                    question=question_text,
                    context=issue.description,
                    options=["Sí", "No", "No aplica"],
                    required=True,
                    issue_id=issue.title
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating question for issue: {e}")
            return None
    
    def _generate_missing_info_questions(self, extracted_data: Dict[str, Any]) -> List[Question]:
        """Generate questions for missing information."""
        questions = []
        
        # Check for missing critical information
        missing_checks = [
            ("building_use", "¿Cuál es el uso principal del edificio?"),
            ("total_area", "¿Cuál es la superficie total del edificio?"),
            ("height", "¿Cuál es la altura del edificio?"),
            ("floors", "¿Cuántas plantas tiene el edificio?"),
            ("location", "¿Dónde está ubicado el edificio?")
        ]
        
        for field, question_text in missing_checks:
            # Check if field is missing or unclear
            if not self._has_clear_information(extracted_data, field):
                question = Question(
                    question_id=f"missing_{field}",
                    question=question_text,
                    context="Información faltante en los documentos",
                    options=["Residencial", "Comercial", "Oficinas", "Público"],
                    required=True,
                    issue_id=f"missing_{field}"
                )
                questions.append(question)
        
        return questions
    
    def _has_clear_information(self, extracted_data: Dict[str, Any], field: str) -> bool:
        """Check if field has clear information in extracted data."""
        # This is a simplified check - in practice, you'd use NLP to analyze the text
        all_text = self._combine_extracted_text(extracted_data)
        
        field_keywords = {
            "building_use": ["residencial", "comercial", "oficinas", "público"],
            "total_area": ["superficie", "m²", "metros cuadrados"],
            "height": ["altura", "metros", "m"],
            "floors": ["plantas", "pisos", "niveles"],
            "location": ["ubicación", "dirección", "calle", "avenida"]
        }
        
        if field in field_keywords:
            return any(keyword in all_text.lower() for keyword in field_keywords[field])
        
        return False
    
    def _generate_contradiction_questions(self, extracted_data: Dict[str, Any]) -> List[Question]:
        """Generate questions for contradictions."""
        questions = []
        
        try:
            # Use AI to detect contradictions
            all_text = self._combine_extracted_text(extracted_data)
            prompt = get_contradiction_detection_prompt(all_text[:self.max_text_length])
            ai_response = self.ai_client.generate_response(prompt)
            
            # Parse contradictions from AI response
            contradiction_pattern = r'\\*\\*Contradicción\\*\\*:([^\\n]+)'
            matches = re.findall(contradiction_pattern, ai_response.content, re.IGNORECASE)
            
            for i, match in enumerate(matches):
                question = Question(
                    question_id=f"contradiction_{i}",
                    question=f"¿Puede aclarar esta contradicción: {match.strip()}?",
                    context="Posible contradicción detectada en los documentos",
                    options=["Sí, es correcto", "No, hay error", "Necesito revisar"],
                    required=True,
                    issue_id=f"contradiction_{i}"
                )
                questions.append(question)
            
        except Exception as e:
            logger.error(f"Error generating contradiction questions: {e}")
        
        return questions
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            **self._processing_stats,
            'nlp_stats': self.nlp_processor.get_processing_stats(),
            'rule_engine_stats': self.rule_engine.get_rule_statistics()
        }
