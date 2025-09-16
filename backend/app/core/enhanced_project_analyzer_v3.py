"""
Enhanced Project Analyzer V3
Fase 2: Integración Completa con Visión por Computador
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Importar módulos de Fase 1 y 2
from .enhanced_project_analyzer_v2 import EnhancedProjectAnalyzerV2
from .computer_vision_analyzer import ComputerVisionAnalyzer, PlanAnalysis
from .plan_analyzer import PlanAnalyzer, PlanAnalysisResult
from .dimension_extractor import DimensionExtractor, DimensionAnalysis
from .enhanced_ocr_processor import EnhancedOCRProcessor
from .production_checker_logic import ProductionComplianceChecker

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveAnalysisResult:
    """Resultado del análisis integral del proyecto"""
    # Análisis de documentos (Fase 1)
    document_analysis: Dict[str, Any]
    
    # Análisis de planos (Fase 2)
    plan_analysis: PlanAnalysisResult
    
    # Análisis de dimensiones (Fase 2)
    dimension_analysis: DimensionAnalysis
    
    # Verificación de cumplimiento
    compliance_check: Dict[str, Any]
    
    # Análisis integral
    overall_score: float
    critical_issues: List[str]
    recommendations: List[str]
    
    # Metadatos
    timestamp: str
    processing_time: float
    files_processed: int

class EnhancedProjectAnalyzerV3:
    """Analizador integral de proyectos arquitectónicos con visión por computador"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando EnhancedProjectAnalyzerV3")
        
        # Inicializar componentes de Fase 1
        self.analyzer_v2 = EnhancedProjectAnalyzerV2()
        
        # Inicializar componentes de Fase 2
        self.cv_analyzer = ComputerVisionAnalyzer()
        self.plan_analyzer = PlanAnalyzer()
        self.dimension_extractor = DimensionExtractor()
        self.ocr_processor = EnhancedOCRProcessor()
        self.compliance_checker = ProductionComplianceChecker()
        
        # Configuración
        self.setup_configuration()
        
    def setup_configuration(self):
        """Configuración del analizador V3"""
        self.config = {
            'min_confidence_threshold': 0.6,
            'max_processing_time': 300,  # 5 minutos
            'enable_computer_vision': True,
            'enable_dimension_extraction': True,
            'enable_plan_analysis': True,
            'output_directory': 'analysis_results'
        }
        
        # Crear directorio de salida si no existe
        os.makedirs(self.config['output_directory'], exist_ok=True)
    
    def analyze_project_comprehensive(self, 
                                    memory_file: str, 
                                    plans_directory: str,
                                    project_type: str = "residential") -> ComprehensiveAnalysisResult:
        """
        Análisis integral de un proyecto arquitectónico
        
        Args:
            memory_file: Archivo de memoria del proyecto
            plans_directory: Directorio con los planos
            project_type: Tipo de proyecto (residential, commercial, etc.)
            
        Returns:
            ComprehensiveAnalysisResult: Resultado del análisis integral
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Iniciando análisis integral del proyecto: {project_type}")
            
            # PASO 1: Análisis de documentos (Fase 1)
            self.logger.info("PASO 1: Analizando documentos...")
            document_analysis = self.analyze_documents(memory_file)
            
            # PASO 2: Análisis de planos (Fase 2)
            self.logger.info("PASO 2: Analizando planos...")
            plan_analysis = self.analyze_plans(plans_directory)
            
            # PASO 3: Análisis de dimensiones (Fase 2)
            self.logger.info("PASO 3: Extrayendo dimensiones...")
            dimension_analysis = self.analyze_dimensions(plans_directory)
            
            # PASO 4: Verificación de cumplimiento integral
            self.logger.info("PASO 4: Verificando cumplimiento...")
            compliance_check = self.verify_comprehensive_compliance(
                document_analysis, plan_analysis, dimension_analysis, project_type
            )
            
            # PASO 5: Análisis integral y recomendaciones
            self.logger.info("PASO 5: Generando análisis integral...")
            overall_score, critical_issues, recommendations = self.generate_integral_analysis(
                document_analysis, plan_analysis, dimension_analysis, compliance_check
            )
            
            # Calcular tiempo de procesamiento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Contar archivos procesados
            files_processed = self.count_processed_files(memory_file, plans_directory)
            
            result = ComprehensiveAnalysisResult(
                document_analysis=document_analysis,
                plan_analysis=plan_analysis,
                dimension_analysis=dimension_analysis,
                compliance_check=compliance_check,
                overall_score=overall_score,
                critical_issues=critical_issues,
                recommendations=recommendations,
                timestamp=start_time.isoformat(),
                processing_time=processing_time,
                files_processed=files_processed
            )
            
            # Guardar resultado
            self.save_comprehensive_analysis(result)
            
            self.logger.info(f"Análisis integral completado en {processing_time:.2f} segundos")
            return result
            
        except Exception as e:
            self.logger.error(f"Error en análisis integral: {e}")
            raise
    
    def analyze_documents(self, memory_file: str) -> Dict[str, Any]:
        """Analiza los documentos del proyecto (Fase 1)"""
        try:
            self.logger.info(f"Analizando documento: {memory_file}")
            
            # Usar el analizador V2 para documentos
            analysis_result = self.analyzer_v2.analyze_project_comprehensive(memory_file)
            
            return {
                'extracted_data': analysis_result.get('extracted_data', {}),
                'contradictions': analysis_result.get('contradictions', []),
                'compliance_issues': analysis_result.get('compliance_issues', []),
                'questions': analysis_result.get('questions', []),
                'confidence_score': analysis_result.get('confidence_score', 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error analizando documentos: {e}")
            return {
                'extracted_data': {},
                'contradictions': [],
                'compliance_issues': [f"Error analizando documentos: {str(e)}"],
                'questions': [],
                'confidence_score': 0.0
            }
    
    def analyze_plans(self, plans_directory: str) -> PlanAnalysisResult:
        """Analiza los planos del proyecto (Fase 2)"""
        try:
            self.logger.info(f"Analizando planos en: {plans_directory}")
            
            if not os.path.exists(plans_directory):
                raise ValueError(f"Directorio de planos no encontrado: {plans_directory}")
            
            # Usar el analizador de planos
            plan_analysis = self.plan_analyzer.analyze_plans(plans_directory)
            
            return plan_analysis
            
        except Exception as e:
            self.logger.error(f"Error analizando planos: {e}")
            # Retornar análisis vacío en caso de error
            from .plan_analyzer import PlanAnalysisResult
            return PlanAnalysisResult(
                plans_analyzed=0,
                total_elements=0,
                compliance_results=[],
                overall_compliance=0.0,
                critical_issues=[f"Error analizando planos: {str(e)}"],
                accessibility_issues=[],
                fire_safety_issues=[],
                structural_issues=[],
                recommendations=[]
            )
    
    def analyze_dimensions(self, plans_directory: str) -> DimensionAnalysis:
        """Analiza las dimensiones de los planos (Fase 2)"""
        try:
            self.logger.info(f"Extrayendo dimensiones de: {plans_directory}")
            
            # Encontrar archivos de planos
            plan_files = self.find_plan_files(plans_directory)
            
            if not plan_files:
                raise ValueError(f"No se encontraron planos en: {plans_directory}")
            
            # Analizar dimensiones del primer plano (como ejemplo)
            first_plan = plan_files[0]
            
            # Extraer texto del PDF si es necesario
            text_content = ""
            if first_plan.lower().endswith('.pdf'):
                text_content = self.ocr_processor.extract_text_from_pdf(first_plan)
            
            # Convertir PDF a imagen si es necesario
            image_path = first_plan
            if first_plan.lower().endswith('.pdf'):
                image_path = self.convert_pdf_to_image(first_plan)
                if not image_path:
                    raise ValueError("No se pudo convertir PDF a imagen")
            
            # Extraer dimensiones
            dimension_analysis = self.dimension_extractor.extract_dimensions_from_plan(
                image_path, text_content
            )
            
            # Limpiar archivo temporal si se creó
            if image_path != first_plan and os.path.exists(image_path):
                os.remove(image_path)
            
            return dimension_analysis
            
        except Exception as e:
            self.logger.error(f"Error analizando dimensiones: {e}")
            # Retornar análisis vacío en caso de error
            from .dimension_extractor import DimensionAnalysis
            return DimensionAnalysis(
                dimensions=[],
                scale_factor=1.0,
                total_area=0.0,
                room_areas={},
                wall_lengths=[],
                door_widths=[],
                window_areas=[],
                compliance_check={}
            )
    
    def find_plan_files(self, directory: str) -> List[str]:
        """Encuentra archivos de planos en el directorio"""
        try:
            plan_files = []
            directory_path = Path(directory)
            
            # Extensiones de archivos de planos
            plan_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
            
            for ext in plan_extensions:
                files = list(directory_path.glob(f"*{ext}"))
                plan_files.extend([str(f) for f in files])
            
            return sorted(plan_files)
            
        except Exception as e:
            self.logger.error(f"Error buscando archivos de planos: {e}")
            return []
    
    def convert_pdf_to_image(self, pdf_path: str) -> Optional[str]:
        """Convierte la primera página de un PDF a imagen"""
        try:
            import fitz  # PyMuPDF
            import tempfile
            
            # Abrir PDF
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                return None
            
            # Obtener primera página
            page = doc[0]
            
            # Convertir a imagen
            mat = fitz.Matrix(2.0, 2.0)  # Escala 2x
            pix = page.get_pixmap(matrix=mat)
            
            # Guardar imagen temporal
            temp_dir = tempfile.gettempdir()
            image_path = os.path.join(temp_dir, f"temp_plan_{os.getpid()}.png")
            pix.save(image_path)
            
            doc.close()
            return image_path
            
        except Exception as e:
            self.logger.error(f"Error convirtiendo PDF a imagen: {e}")
            return None
    
    def verify_comprehensive_compliance(self, 
                                      document_analysis: Dict[str, Any],
                                      plan_analysis: PlanAnalysisResult,
                                      dimension_analysis: DimensionAnalysis,
                                      project_type: str) -> Dict[str, Any]:
        """Verifica el cumplimiento integral del proyecto"""
        try:
            self.logger.info("Verificando cumplimiento integral...")
            
            compliance_results = {
                'document_compliance': 0.0,
                'plan_compliance': 0.0,
                'dimension_compliance': 0.0,
                'overall_compliance': 0.0,
                'critical_issues': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Verificar cumplimiento de documentos
            doc_confidence = document_analysis.get('confidence_score', 0.0)
            doc_issues = document_analysis.get('compliance_issues', [])
            compliance_results['document_compliance'] = doc_confidence
            compliance_results['critical_issues'].extend(doc_issues)
            
            # Verificar cumplimiento de planos
            plan_compliance = plan_analysis.overall_compliance
            plan_issues = plan_analysis.critical_issues
            compliance_results['plan_compliance'] = plan_compliance
            compliance_results['critical_issues'].extend(plan_issues)
            
            # Verificar cumplimiento de dimensiones
            dim_compliance = self.calculate_dimension_compliance(dimension_analysis)
            compliance_results['dimension_compliance'] = dim_compliance
            
            # Verificar cumplimiento específico por tipo de proyecto
            project_specific_compliance = self.verify_project_specific_compliance(
                project_type, document_analysis, plan_analysis, dimension_analysis
            )
            compliance_results['critical_issues'].extend(project_specific_compliance['issues'])
            compliance_results['warnings'].extend(project_specific_compliance['warnings'])
            compliance_results['recommendations'].extend(project_specific_compliance['recommendations'])
            
            # Calcular cumplimiento general
            compliance_scores = [
                compliance_results['document_compliance'],
                compliance_results['plan_compliance'],
                compliance_results['dimension_compliance']
            ]
            compliance_results['overall_compliance'] = sum(compliance_scores) / len(compliance_scores)
            
            return compliance_results
            
        except Exception as e:
            self.logger.error(f"Error verificando cumplimiento integral: {e}")
            return {
                'document_compliance': 0.0,
                'plan_compliance': 0.0,
                'dimension_compliance': 0.0,
                'overall_compliance': 0.0,
                'critical_issues': [f"Error verificando cumplimiento: {str(e)}"],
                'warnings': [],
                'recommendations': []
            }
    
    def calculate_dimension_compliance(self, dimension_analysis: DimensionAnalysis) -> float:
        """Calcula el cumplimiento de las dimensiones"""
        try:
            compliance_check = dimension_analysis.compliance_check
            
            if not compliance_check:
                return 0.0
            
            # Contar verificaciones pasadas
            passed_checks = sum(1 for check in compliance_check.values() if check)
            total_checks = len(compliance_check)
            
            return (passed_checks / total_checks) * 100.0 if total_checks > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculando cumplimiento de dimensiones: {e}")
            return 0.0
    
    def verify_project_specific_compliance(self, 
                                         project_type: str,
                                         document_analysis: Dict[str, Any],
                                         plan_analysis: PlanAnalysisResult,
                                         dimension_analysis: DimensionAnalysis) -> Dict[str, List[str]]:
        """Verifica cumplimiento específico por tipo de proyecto"""
        try:
            issues = []
            warnings = []
            recommendations = []
            
            if project_type.lower() == "residential":
                # Verificaciones específicas para viviendas
                issues.extend(self.verify_residential_compliance(
                    document_analysis, plan_analysis, dimension_analysis
                ))
            elif project_type.lower() == "commercial":
                # Verificaciones específicas para comerciales
                issues.extend(self.verify_commercial_compliance(
                    document_analysis, plan_analysis, dimension_analysis
                ))
            
            return {
                'issues': issues,
                'warnings': warnings,
                'recommendations': recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error verificando cumplimiento específico: {e}")
            return {'issues': [], 'warnings': [], 'recommendations': []}
    
    def verify_residential_compliance(self, 
                                    document_analysis: Dict[str, Any],
                                    plan_analysis: PlanAnalysisResult,
                                    dimension_analysis: DimensionAnalysis) -> List[str]:
        """Verificaciones específicas para viviendas"""
        issues = []
        
        # Verificar área mínima de habitaciones
        room_areas = dimension_analysis.room_areas
        for room_name, area in room_areas.items():
            if area < 9.0:  # 9 m² mínimo para habitaciones
                issues.append(f"Habitación {room_name} con área insuficiente: {area:.2f} m²")
        
        # Verificar accesibilidad
        if not plan_analysis.accessibility_issues:
            issues.append("No se detectaron características de accesibilidad")
        
        return issues
    
    def verify_commercial_compliance(self, 
                                   document_analysis: Dict[str, Any],
                                   plan_analysis: PlanAnalysisResult,
                                   dimension_analysis: DimensionAnalysis) -> List[str]:
        """Verificaciones específicas para comerciales"""
        issues = []
        
        # Verificar salidas de emergencia
        if len(plan_analysis.critical_issues) < 2:
            issues.append("Insuficientes salidas de emergencia para uso comercial")
        
        # Verificar accesibilidad
        if not plan_analysis.accessibility_issues:
            issues.append("Accesibilidad requerida para uso comercial")
        
        return issues
    
    def generate_integral_analysis(self, 
                                 document_analysis: Dict[str, Any],
                                 plan_analysis: PlanAnalysisResult,
                                 dimension_analysis: DimensionAnalysis,
                                 compliance_check: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Genera el análisis integral y recomendaciones"""
        try:
            self.logger.info("Generando análisis integral...")
            
            # Calcular puntuación general
            doc_score = document_analysis.get('confidence_score', 0.0)
            plan_score = plan_analysis.overall_compliance
            dim_score = compliance_check.get('dimension_compliance', 0.0)
            
            overall_score = (doc_score + plan_score + dim_score) / 3.0
            
            # Recopilar problemas críticos
            critical_issues = []
            critical_issues.extend(document_analysis.get('compliance_issues', []))
            critical_issues.extend(plan_analysis.critical_issues)
            critical_issues.extend(compliance_check.get('critical_issues', []))
            
            # Generar recomendaciones
            recommendations = []
            recommendations.extend(document_analysis.get('questions', []))
            recommendations.extend(plan_analysis.recommendations)
            recommendations.extend(compliance_check.get('recommendations', []))
            
            # Añadir recomendaciones específicas basadas en la puntuación
            if overall_score < 50:
                recommendations.append("PRIORIDAD ALTA: Revisión completa del proyecto requerida")
            elif overall_score < 75:
                recommendations.append("PRIORIDAD MEDIA: Mejoras recomendadas en varios aspectos")
            else:
                recommendations.append("Proyecto en buen estado, revisar detalles menores")
            
            return overall_score, critical_issues, recommendations
            
        except Exception as e:
            self.logger.error(f"Error generando análisis integral: {e}")
            return 0.0, [f"Error en análisis integral: {str(e)}"], []
    
    def count_processed_files(self, memory_file: str, plans_directory: str) -> int:
        """Cuenta los archivos procesados"""
        try:
            count = 0
            
            # Contar archivo de memoria
            if memory_file and os.path.exists(memory_file):
                count += 1
            
            # Contar archivos de planos
            plan_files = self.find_plan_files(plans_directory)
            count += len(plan_files)
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error contando archivos procesados: {e}")
            return 0
    
    def save_comprehensive_analysis(self, result: ComprehensiveAnalysisResult):
        """Guarda el análisis integral"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_analysis_{timestamp}.json"
            filepath = os.path.join(self.config['output_directory'], filename)
            
            # Convertir a diccionario serializable
            data = {
                'timestamp': result.timestamp,
                'processing_time': result.processing_time,
                'files_processed': result.files_processed,
                'overall_score': result.overall_score,
                'critical_issues': result.critical_issues,
                'recommendations': result.recommendations,
                'document_analysis': result.document_analysis,
                'plan_analysis': {
                    'plans_analyzed': result.plan_analysis.plans_analyzed,
                    'total_elements': result.plan_analysis.total_elements,
                    'overall_compliance': result.plan_analysis.overall_compliance,
                    'critical_issues': result.plan_analysis.critical_issues,
                    'accessibility_issues': result.plan_analysis.accessibility_issues,
                    'fire_safety_issues': result.plan_analysis.fire_safety_issues,
                    'structural_issues': result.plan_analysis.structural_issues,
                    'recommendations': result.plan_analysis.recommendations
                },
                'dimension_analysis': {
                    'total_area': result.dimension_analysis.total_area,
                    'room_areas': result.dimension_analysis.room_areas,
                    'wall_lengths': result.dimension_analysis.wall_lengths,
                    'door_widths': result.dimension_analysis.door_widths,
                    'window_areas': result.dimension_analysis.window_areas,
                    'compliance_check': result.dimension_analysis.compliance_check
                },
                'compliance_check': result.compliance_check
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Análisis integral guardado en: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error guardando análisis integral: {e}")
            raise
    
    def get_analysis_summary(self, result: ComprehensiveAnalysisResult) -> Dict[str, Any]:
        """Obtiene un resumen del análisis"""
        try:
            return {
                'overall_score': result.overall_score,
                'processing_time': result.processing_time,
                'files_processed': result.files_processed,
                'critical_issues_count': len(result.critical_issues),
                'recommendations_count': len(result.recommendations),
                'document_confidence': result.document_analysis.get('confidence_score', 0.0),
                'plan_compliance': result.plan_analysis.overall_compliance,
                'dimension_compliance': result.compliance_check.get('dimension_compliance', 0.0),
                'accessibility_issues': len(result.plan_analysis.accessibility_issues),
                'fire_safety_issues': len(result.plan_analysis.fire_safety_issues),
                'structural_issues': len(result.plan_analysis.structural_issues)
            }
            
        except Exception as e:
            self.logger.error(f"Error generando resumen: {e}")
            return {}
