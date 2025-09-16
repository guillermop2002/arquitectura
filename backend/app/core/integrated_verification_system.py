"""
Integrated Verification System that combines all analysis methods.
Integrates OCR, AI, Computer Vision, and NLP for comprehensive building verification.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .production_project_analyzer import ProductionProjectAnalyzer
from .advanced_plan_analyzer import AdvancedPlanAnalyzer
from .enhanced_ocr_processor import EnhancedOCRProcessor
from .ai_client import get_ai_client
from ..models.schemas import Issue, Question, ProjectData, SeverityLevel

logger = logging.getLogger(__name__)

class IntegratedVerificationSystem:
    """
    Integrated verification system that combines all analysis methods.
    """
    
    def __init__(self):
        """Initialize the integrated verification system."""
        self.ocr_processor = EnhancedOCRProcessor()
        self.project_analyzer = ProductionProjectAnalyzer()
        self.plan_analyzer = AdvancedPlanAnalyzer()
        self.ai_client = get_ai_client()
        
        logger.info("Integrated Verification System initialized")
    
    def verify_project_comprehensive(
        self, 
        pdf_files: List[str],
        is_existing_building: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive project verification using all available methods.
        
        Args:
            pdf_files: List of PDF file paths
            is_existing_building: Whether this is an existing building
            
        Returns:
            Comprehensive verification results
        """
        try:
            logger.info(f"Starting comprehensive verification of {len(pdf_files)} files")
            
            # Phase 1: OCR Processing
            ocr_results = self._process_all_pdfs(pdf_files)
            
            # Phase 2: Plan Analysis (if plan files detected)
            plan_analysis = self._analyze_plans(pdf_files, ocr_results)
            
            # Phase 3: Project Data Extraction
            project_data = self._extract_project_data(ocr_results)
            
            # Phase 4: Normative Compliance Check
            compliance_results = self._check_normative_compliance(
                project_data, ocr_results, plan_analysis, is_existing_building
            )
            
            # Phase 5: Cross-validation and Integration
            integrated_results = self._integrate_all_results(
                ocr_results, plan_analysis, project_data, compliance_results
            )
            
            # Phase 6: Generate Questions and Recommendations
            questions = self._generate_questions(integrated_results)
            recommendations = self._generate_recommendations(integrated_results)
            
            # Final results
            final_results = {
                'success': True,
                'verification_timestamp': str(Path().cwd()),
                'files_processed': len(pdf_files),
                'ocr_results': ocr_results,
                'plan_analysis': plan_analysis,
                'project_data': project_data.dict() if project_data else {},
                'compliance_results': compliance_results,
                'integrated_analysis': integrated_results,
                'questions': questions,
                'recommendations': recommendations,
                'summary': self._generate_summary(integrated_results)
            }
            
            logger.info("Comprehensive verification completed successfully")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive verification: {e}")
            return {
                'success': False,
                'error': str(e),
                'files_processed': len(pdf_files) if pdf_files else 0
            }
    
    def _process_all_pdfs(self, pdf_files: List[str]) -> Dict[str, Any]:
        """Process all PDF files with OCR."""
        try:
            ocr_results = {}
            
            for pdf_file in pdf_files:
                logger.info(f"Processing PDF: {pdf_file}")
                
                # Extract text from PDF
                result = self.ocr_processor.extract_text_from_pdf(pdf_file)
                
                if result['success']:
                    ocr_results[Path(pdf_file).name] = result
                else:
                    logger.warning(f"Failed to process {pdf_file}: {result.get('errors', [])}")
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"Error processing PDFs: {e}")
            return {}
    
    def _analyze_plans(self, pdf_files: List[str], ocr_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze plan files using computer vision."""
        try:
            plan_files = []
            
            # Identify plan files based on filename and content
            for pdf_file in pdf_files:
                filename = Path(pdf_file).name.lower()
                if any(keyword in filename for keyword in ['plano', 'planos', 'planta', 'plantas']):
                    plan_files.append(pdf_file)
                else:
                    # Check content for plan indicators
                    file_data = ocr_results.get(Path(pdf_file).name, {})
                    pages = file_data.get('pages', [])
                    
                    for page in pages:
                        text = page.get('text', '').lower()
                        if any(keyword in text for keyword in ['planta', 'plano', 'escala', 'nivel']):
                            plan_files.append(pdf_file)
                            break
            
            if not plan_files:
                logger.info("No plan files detected")
                return {}
            
            # Analyze plan files
            plan_analysis = {}
            for plan_file in plan_files:
                logger.info(f"Analyzing plan: {plan_file}")
                
                # Analyze with computer vision
                analysis_result = self.plan_analyzer.analyze_plan_pdf(plan_file)
                plan_analysis[Path(plan_file).name] = analysis_result
            
            return plan_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing plans: {e}")
            return {}
    
    def _extract_project_data(self, ocr_results: Dict[str, Any]) -> Optional[ProjectData]:
        """Extract project data using AI."""
        try:
            # Combine all text for analysis
            combined_text = self._combine_all_texts(ocr_results)
            
            if not combined_text:
                logger.warning("No text found for project data extraction")
                return None
            
            # Extract project data
            project_data = self.project_analyzer.extract_project_data(ocr_results)
            
            return project_data
            
        except Exception as e:
            logger.error(f"Error extracting project data: {e}")
            return None
    
    def _check_normative_compliance(
        self, 
        project_data: Optional[ProjectData], 
        ocr_results: Dict[str, Any], 
        plan_analysis: Dict[str, Any],
        is_existing_building: bool
    ) -> Dict[str, Any]:
        """Check normative compliance using all available data."""
        try:
            compliance_results = {
                'annexe_i_compliance': {},
                'fire_safety_compliance': {},
                'accessibility_compliance': {},
                'energy_efficiency_compliance': {},
                'structural_compliance': {},
                'total_issues': 0,
                'high_severity_issues': 0,
                'medium_severity_issues': 0,
                'low_severity_issues': 0
            }
            
            # Check Annexe I compliance
            anexe_i_result = self.project_analyzer.check_annexe_i_compliance(ocr_results)
            compliance_results['annexe_i_compliance'] = anexe_i_result
            
            # Check complete compliance
            if project_data:
                from .data_loader import DataLoader
                data_loader = DataLoader()
                normative_docs = data_loader.load_normative_documents(
                    project_data.building_use, 
                    is_existing_building
                )
                
                complete_compliance = self.project_analyzer.check_complete_compliance(
                    project_data, ocr_results, normative_docs
                )
                
                compliance_results.update(complete_compliance)
            
            # Add plan-based compliance issues
            plan_issues = self._extract_plan_compliance_issues(plan_analysis)
            compliance_results['plan_based_issues'] = plan_issues
            
            # Count issues by severity
            all_issues = compliance_results.get('issues', []) + plan_issues
            for issue in all_issues:
                if isinstance(issue, dict):
                    severity = issue.get('severity', 'medium')
                else:
                    severity = getattr(issue, 'severity', 'medium')
                
                if severity == 'high':
                    compliance_results['high_severity_issues'] += 1
                elif severity == 'medium':
                    compliance_results['medium_severity_issues'] += 1
                else:
                    compliance_results['low_severity_issues'] += 1
            
            compliance_results['total_issues'] = len(all_issues)
            
            return compliance_results
            
        except Exception as e:
            logger.error(f"Error checking normative compliance: {e}")
            return {'error': str(e)}
    
    def _extract_plan_compliance_issues(self, plan_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract compliance issues from plan analysis."""
        issues = []
        
        try:
            for plan_name, analysis in plan_analysis.items():
                if analysis.get('success'):
                    compliance_issues = analysis.get('compliance_issues', [])
                    for issue in compliance_issues:
                        issue['source'] = 'plan_analysis'
                        issue['plan_file'] = plan_name
                        issues.append(issue)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error extracting plan compliance issues: {e}")
            return []
    
    def _integrate_all_results(
        self, 
        ocr_results: Dict[str, Any], 
        plan_analysis: Dict[str, Any], 
        project_data: Optional[ProjectData], 
        compliance_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate all analysis results."""
        try:
            integrated = {
                'total_pages_processed': 0,
                'total_elements_detected': 0,
                'total_rooms_detected': 0,
                'connectivity_analysis': {},
                'cross_validation_issues': [],
                'confidence_scores': {}
            }
            
            # Count pages processed
            for file_data in ocr_results.values():
                if file_data.get('success'):
                    integrated['total_pages_processed'] += file_data.get('page_count', 0)
            
            # Count elements and rooms from plan analysis
            for plan_data in plan_analysis.values():
                if plan_data.get('success'):
                    integrated['total_elements_detected'] += plan_data.get('total_elements', 0)
                    integrated['total_rooms_detected'] += plan_data.get('total_rooms', 0)
                    
                    # Store connectivity analysis
                    connectivity = plan_data.get('connectivity_graph', {})
                    if connectivity:
                        integrated['connectivity_analysis'][plan_data.get('plan_name', 'unknown')] = connectivity
            
            # Cross-validation between OCR and plan analysis
            cross_validation_issues = self._perform_cross_validation(ocr_results, plan_analysis)
            integrated['cross_validation_issues'] = cross_validation_issues
            
            # Calculate confidence scores
            confidence_scores = self._calculate_integrated_confidence(
                ocr_results, plan_analysis, compliance_results
            )
            integrated['confidence_scores'] = confidence_scores
            
            return integrated
            
        except Exception as e:
            logger.error(f"Error integrating results: {e}")
            return {}
    
    def _perform_cross_validation(
        self, 
        ocr_results: Dict[str, Any], 
        plan_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform cross-validation between OCR and plan analysis."""
        issues = []
        
        try:
            # Extract dimensions from OCR
            ocr_dimensions = self._extract_ocr_dimensions(ocr_results)
            
            # Extract dimensions from plan analysis
            plan_dimensions = self._extract_plan_dimensions(plan_analysis)
            
            # Compare dimensions
            for ocr_dim in ocr_dimensions:
                for plan_dim in plan_dimensions:
                    if self._are_dimensions_comparable(ocr_dim, plan_dim):
                        difference = abs(ocr_dim['value'] - plan_dim['value'])
                        if difference > 0.1:  # 10cm tolerance
                            issues.append({
                                'type': 'dimension_mismatch',
                                'description': f'Discrepancia dimensional: OCR {ocr_dim["value"]:.2f}m vs Planos {plan_dim["value"]:.2f}m',
                                'severity': 'medium',
                                'ocr_value': ocr_dim['value'],
                                'plan_value': plan_dim['value'],
                                'difference': difference
                            })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error in cross-validation: {e}")
            return []
    
    def _extract_ocr_dimensions(self, ocr_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract dimensions from OCR results."""
        dimensions = []
        
        try:
            for file_data in ocr_results.values():
                pages = file_data.get('pages', [])
                for page in pages:
                    text = page.get('text', '')
                    
                    # Extract dimensions using regex
                    import re
                    patterns = [
                        r'(\d+(?:[.,]\d+)?)\s*(?:m|metros?|mm|milímetros?|cm|centímetros?)',
                        r'(?:ancho|anchura|alto|altura|largo|longitud)[\s:]+(\d+(?:[.,]\d+)?)\s*(?:m|metros?|mm|milímetros?|cm|centímetros?)'
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            value = float(match.group(1).replace(',', '.'))
                            dimensions.append({
                                'value': value,
                                'unit': 'm',
                                'source': 'ocr',
                                'text': match.group()
                            })
            
            return dimensions
            
        except Exception as e:
            logger.error(f"Error extracting OCR dimensions: {e}")
            return []
    
    def _extract_plan_dimensions(self, plan_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract dimensions from plan analysis."""
        dimensions = []
        
        try:
            for plan_data in plan_analysis.values():
                elements = plan_data.get('elements', [])
                for element in elements:
                    if element.get('dimensions'):
                        for dim_name, dim_value in element['dimensions'].items():
                            if isinstance(dim_value, (int, float)) and dim_value > 0:
                                # Convert pixels to meters (assuming 1 pixel = 0.01m)
                                value_m = dim_value * 0.01
                                dimensions.append({
                                    'value': value_m,
                                    'unit': 'm',
                                    'source': 'plan_analysis',
                                    'element_type': element.get('element_type', 'unknown'),
                                    'dimension': dim_name
                                })
            
            return dimensions
            
        except Exception as e:
            logger.error(f"Error extracting plan dimensions: {e}")
            return []
    
    def _are_dimensions_comparable(self, dim1: Dict[str, Any], dim2: Dict[str, Any]) -> bool:
        """Check if two dimensions are comparable."""
        try:
            # Same unit
            if dim1.get('unit') != dim2.get('unit'):
                return False
            
            # Similar value range
            ratio = abs(dim1['value'] - dim2['value']) / max(dim1['value'], dim2['value'])
            return ratio < 0.5  # Within 50% difference
            
        except Exception:
            return False
    
    def _calculate_integrated_confidence(
        self, 
        ocr_results: Dict[str, Any], 
        plan_analysis: Dict[str, Any], 
        compliance_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate integrated confidence scores."""
        try:
            scores = {
                'ocr_confidence': 0.0,
                'plan_analysis_confidence': 0.0,
                'compliance_confidence': 0.0,
                'overall_confidence': 0.0
            }
            
            # OCR confidence
            if ocr_results:
                total_confidence = 0
                total_pages = 0
                
                for file_data in ocr_results.values():
                    if file_data.get('success'):
                        pages = file_data.get('pages', [])
                        for page in pages:
                            total_confidence += page.get('confidence', 0)
                            total_pages += 1
                
                if total_pages > 0:
                    scores['ocr_confidence'] = total_confidence / total_pages
            
            # Plan analysis confidence
            if plan_analysis:
                total_confidence = 0
                total_plans = 0
                
                for plan_data in plan_analysis.values():
                    if plan_data.get('success'):
                        elements = plan_data.get('elements', [])
                        if elements:
                            element_confidence = sum(elem.get('confidence', 0) for elem in elements) / len(elements)
                            total_confidence += element_confidence
                            total_plans += 1
                
                if total_plans > 0:
                    scores['plan_analysis_confidence'] = total_confidence / total_plans
            
            # Compliance confidence
            if compliance_results:
                total_issues = compliance_results.get('total_issues', 0)
                if total_issues > 0:
                    # Higher confidence with fewer issues
                    scores['compliance_confidence'] = max(0, 1.0 - (total_issues / 100))
                else:
                    scores['compliance_confidence'] = 1.0
            
            # Overall confidence
            scores['overall_confidence'] = sum(scores.values()) / len(scores)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating confidence scores: {e}")
            return {'ocr_confidence': 0.0, 'plan_analysis_confidence': 0.0, 'compliance_confidence': 0.0, 'overall_confidence': 0.0}
    
    def _generate_questions(self, integrated_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate questions based on integrated analysis."""
        questions = []
        
        try:
            # Generate questions from cross-validation issues
            cross_validation_issues = integrated_results.get('cross_validation_issues', [])
            for issue in cross_validation_issues:
                if issue['type'] == 'dimension_mismatch':
                    question = {
                        'question': f"¿Cuál es la dimensión correcta: {issue['ocr_value']:.2f}m (memoria) o {issue['plan_value']:.2f}m (planos)?",
                        'context': 'Discrepancia entre memoria y planos',
                        'type': 'dimension_clarification',
                        'priority': 'medium'
                    }
                    questions.append(question)
            
            # Generate questions from low confidence areas
            confidence_scores = integrated_results.get('confidence_scores', {})
            if confidence_scores.get('overall_confidence', 0) < 0.7:
                question = {
                    'question': '¿Puede revisar la calidad de los documentos? Algunos elementos no se detectaron con suficiente confianza.',
                    'context': 'Calidad de documentos',
                    'type': 'quality_check',
                    'priority': 'high'
                }
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
    
    def _generate_recommendations(self, integrated_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on integrated analysis."""
        recommendations = []
        
        try:
            # OCR quality recommendations
            total_pages = integrated_results.get('total_pages_processed', 0)
            if total_pages < 10:
                recommendations.append({
                    'type': 'ocr_quality',
                    'priority': 'medium',
                    'title': 'Mejorar calidad de documentos',
                    'description': 'Pocas páginas procesadas. Verificar calidad de escaneo.',
                    'action': 'Revisar resolución y contraste de PDFs'
                })
            
            # Plan analysis recommendations
            total_elements = integrated_results.get('total_elements_detected', 0)
            if total_elements < 20:
                recommendations.append({
                    'type': 'plan_analysis',
                    'priority': 'high',
                    'title': 'Mejorar planos',
                    'description': 'Pocos elementos arquitectónicos detectados.',
                    'action': 'Verificar que los planos muestren claramente muros, puertas y ventanas'
                })
            
            # Connectivity recommendations
            connectivity_analysis = integrated_results.get('connectivity_analysis', {})
            if not connectivity_analysis:
                recommendations.append({
                    'type': 'connectivity',
                    'priority': 'high',
                    'title': 'Análisis de conectividad requerido',
                    'description': 'No se pudo determinar la conectividad entre espacios.',
                    'action': 'Verificar que los planos muestren conexiones entre habitaciones'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _generate_summary(self, integrated_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of verification results."""
        try:
            summary = {
                'total_pages_processed': integrated_results.get('total_pages_processed', 0),
                'total_elements_detected': integrated_results.get('total_elements_detected', 0),
                'total_rooms_detected': integrated_results.get('total_rooms_detected', 0),
                'cross_validation_issues_count': len(integrated_results.get('cross_validation_issues', [])),
                'overall_confidence': integrated_results.get('confidence_scores', {}).get('overall_confidence', 0.0),
                'status': 'completed'
            }
            
            # Determine overall status
            if summary['overall_confidence'] > 0.8:
                summary['status'] = 'excellent'
            elif summary['overall_confidence'] > 0.6:
                summary['status'] = 'good'
            elif summary['overall_confidence'] > 0.4:
                summary['status'] = 'fair'
            else:
                summary['status'] = 'poor'
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _combine_all_texts(self, ocr_results: Dict[str, Any]) -> str:
        """Combine all text from OCR results."""
        text_parts = []
        
        for filename, file_data in ocr_results.items():
            if file_data.get('success'):
                pages = file_data.get('pages', [])
                for page in pages:
                    page_text = page.get('text', '')
                    page_number = page.get('page_number', 0)
                    confidence = page.get('confidence', 0.0)
                    
                    if page_text and confidence > 0.3:
                        text_parts.append(f"--- {filename} - Página {page_number} ---\n{page_text}")
        
        return '\n\n'.join(text_parts)
    
    def export_verification_results(self, results: Dict[str, Any], output_path: str) -> bool:
        """Export verification results to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Verification results exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting verification results: {e}")
            return False
