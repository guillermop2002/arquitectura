"""
Analizador de Planos Arquitectónicos
Fase 2: Análisis Especializado de Planos con Visión por Computador
"""

import logging
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from datetime import datetime

from .computer_vision_analyzer import ComputerVisionAnalyzer, PlanAnalysis, ArchitecturalElement
from .enhanced_ocr_processor import EnhancedOCRProcessor

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlanCompliance:
    """Resultado de cumplimiento de un plano"""
    plan_type: str  # 'planta', 'alzado', 'seccion', 'detalle'
    compliance_score: float  # Puntuación de cumplimiento (0-100)
    issues: List[str]  # Problemas detectados
    recommendations: List[str]  # Recomendaciones
    accessibility_score: float  # Puntuación de accesibilidad
    fire_safety_score: float  # Puntuación de seguridad contra incendios
    structural_score: float  # Puntuación estructural

@dataclass
class PlanAnalysisResult:
    """Resultado completo del análisis de planos"""
    plans_analyzed: int
    total_elements: int
    compliance_results: List[PlanCompliance]
    overall_compliance: float
    critical_issues: List[str]
    accessibility_issues: List[str]
    fire_safety_issues: List[str]
    structural_issues: List[str]
    recommendations: List[str]

class PlanAnalyzer:
    """Analizador especializado de planos arquitectónicos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando PlanAnalyzer")
        
        # Inicializar componentes
        self.cv_analyzer = ComputerVisionAnalyzer()
        self.ocr_processor = EnhancedOCRProcessor()
        
        # Configuración de análisis
        self.setup_analysis_config()
        
    def setup_analysis_config(self):
        """Configuración para el análisis de planos"""
        self.config = {
            'min_room_area': 9.0,  # m²
            'min_door_width': 0.8,  # m
            'min_window_area': 1.0,  # m²
            'max_ramp_slope': 8.0,  # grados
            'min_elevator_area': 1.5,  # m²
            'min_corridor_width': 1.2,  # m
            'max_stair_rise': 0.18,  # m
            'min_stair_tread': 0.28,  # m
        }
        
        # Reglas de cumplimiento específicas
        self.compliance_rules = {
            'accessibility': {
                'required_ramps': True,
                'required_elevators': True,
                'min_door_width': 0.8,
                'min_corridor_width': 1.2
            },
            'fire_safety': {
                'required_exits': 2,
                'max_escape_distance': 30.0,
                'required_fire_doors': True
            },
            'structural': {
                'min_wall_thickness': 0.2,
                'max_span_ratio': 0.4,
                'required_columns': True
            }
        }
    
    def analyze_plans(self, plans_directory: str) -> PlanAnalysisResult:
        """
        Analiza todos los planos en un directorio
        
        Args:
            plans_directory: Directorio con los planos
            
        Returns:
            PlanAnalysisResult: Resultado del análisis
        """
        try:
            self.logger.info(f"Analizando planos en: {plans_directory}")
            
            # Buscar archivos de planos
            plan_files = self.find_plan_files(plans_directory)
            
            if not plan_files:
                raise ValueError(f"No se encontraron planos en: {plans_directory}")
            
            self.logger.info(f"Encontrados {len(plan_files)} archivos de planos")
            
            # Analizar cada plano
            compliance_results = []
            all_elements = []
            critical_issues = []
            accessibility_issues = []
            fire_safety_issues = []
            structural_issues = []
            
            for plan_file in plan_files:
                try:
                    self.logger.info(f"Analizando plano: {plan_file}")
                    
                    # Determinar tipo de plano
                    plan_type = self.detect_plan_type(plan_file)
                    
                    # Analizar plano
                    plan_analysis = self.analyze_single_plan(plan_file, plan_type)
                    
                    # Evaluar cumplimiento
                    compliance = self.evaluate_plan_compliance(plan_analysis, plan_type)
                    compliance_results.append(compliance)
                    
                    # Recopilar elementos
                    all_elements.extend(plan_analysis.elements)
                    
                    # Recopilar problemas
                    critical_issues.extend(compliance.issues)
                    accessibility_issues.extend(self.filter_accessibility_issues(compliance.issues))
                    fire_safety_issues.extend(self.filter_fire_safety_issues(compliance.issues))
                    structural_issues.extend(self.filter_structural_issues(compliance.issues))
                    
                except Exception as e:
                    self.logger.error(f"Error analizando plano {plan_file}: {e}")
                    continue
            
            # Calcular puntuación general
            overall_compliance = self.calculate_overall_compliance(compliance_results)
            
            # Generar recomendaciones
            recommendations = self.generate_recommendations(
                compliance_results, critical_issues, accessibility_issues, 
                fire_safety_issues, structural_issues
            )
            
            return PlanAnalysisResult(
                plans_analyzed=len(plan_files),
                total_elements=len(all_elements),
                compliance_results=compliance_results,
                overall_compliance=overall_compliance,
                critical_issues=critical_issues,
                accessibility_issues=accessibility_issues,
                fire_safety_issues=fire_safety_issues,
                structural_issues=structural_issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error analizando planos: {e}")
            raise
    
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
            
            # Ordenar por nombre
            plan_files.sort()
            
            return plan_files
            
        except Exception as e:
            self.logger.error(f"Error buscando archivos de planos: {e}")
            return []
    
    def detect_plan_type(self, file_path: str) -> str:
        """Detecta el tipo de plano basado en el nombre del archivo"""
        try:
            filename = Path(file_path).name.lower()
            
            # Palabras clave para diferentes tipos de planos
            if any(word in filename for word in ['planta', 'plant', 'floor']):
                return 'planta'
            elif any(word in filename for word in ['alzado', 'elevation', 'facade']):
                return 'alzado'
            elif any(word in filename for word in ['seccion', 'section', 'corte']):
                return 'seccion'
            elif any(word in filename for word in ['detalle', 'detail']):
                return 'detalle'
            elif any(word in filename for word in ['estructura', 'structure', 'structural']):
                return 'estructura'
            elif any(word in filename for word in ['instalaciones', 'mep', 'utilities']):
                return 'instalaciones'
            else:
                return 'general'
                
        except Exception as e:
            self.logger.error(f"Error detectando tipo de plano: {e}")
            return 'general'
    
    def analyze_single_plan(self, file_path: str, plan_type: str) -> PlanAnalysis:
        """Analiza un plano individual"""
        try:
            # Convertir PDF a imagen si es necesario
            if file_path.lower().endswith('.pdf'):
                # Usar OCR para extraer texto del PDF
                text_content = self.ocr_processor.extract_text_from_pdf(file_path)
                
                # Convertir primera página a imagen para análisis visual
                image_path = self.convert_pdf_to_image(file_path)
                if image_path:
                    analysis = self.cv_analyzer.analyze_plan(image_path)
                    # Limpiar archivo temporal
                    os.remove(image_path)
                else:
                    # Si no se puede convertir, crear análisis básico
                    analysis = self.create_basic_analysis(text_content)
            else:
                # Analizar imagen directamente
                analysis = self.cv_analyzer.analyze_plan(file_path)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analizando plano individual: {e}")
            # Crear análisis básico en caso de error
            return self.create_basic_analysis("")
    
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
    
    def create_basic_analysis(self, text_content: str) -> PlanAnalysis:
        """Crea un análisis básico cuando falla el análisis visual"""
        try:
            # Análisis básico basado en texto
            elements = []
            
            # Detectar elementos básicos en el texto
            if 'puerta' in text_content.lower():
                elements.append(ArchitecturalElement(
                    element_type='door',
                    coordinates=[(0, 0), (100, 100)],
                    dimensions={'width': 0.8, 'height': 2.1},
                    confidence=0.5,
                    properties={'type': 'detected_from_text'}
                ))
            
            if 'ventana' in text_content.lower():
                elements.append(ArchitecturalElement(
                    element_type='window',
                    coordinates=[(0, 0), (100, 100)],
                    dimensions={'width': 1.0, 'height': 1.2},
                    confidence=0.5,
                    properties={'type': 'detected_from_text'}
                ))
            
            return PlanAnalysis(
                elements=elements,
                dimensions={'image_width': 1000, 'image_height': 1000},
                scale=100.0,
                orientation='unknown',
                room_areas={},
                accessibility_features=[],
                compliance_issues=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error creando análisis básico: {e}")
            return PlanAnalysis(
                elements=[],
                dimensions={},
                scale=100.0,
                orientation='unknown',
                room_areas={},
                accessibility_features=[],
                compliance_issues=[]
            )
    
    def evaluate_plan_compliance(self, analysis: PlanAnalysis, plan_type: str) -> PlanCompliance:
        """Evalúa el cumplimiento de un plano"""
        try:
            issues = []
            recommendations = []
            
            # Evaluar accesibilidad
            accessibility_score, acc_issues, acc_recs = self.evaluate_accessibility(analysis)
            issues.extend(acc_issues)
            recommendations.extend(acc_recs)
            
            # Evaluar seguridad contra incendios
            fire_safety_score, fire_issues, fire_recs = self.evaluate_fire_safety(analysis)
            issues.extend(fire_issues)
            recommendations.extend(fire_recs)
            
            # Evaluar aspectos estructurales
            structural_score, struct_issues, struct_recs = self.evaluate_structural(analysis)
            issues.extend(struct_issues)
            recommendations.extend(struct_recs)
            
            # Calcular puntuación general
            compliance_score = (accessibility_score + fire_safety_score + structural_score) / 3
            
            return PlanCompliance(
                plan_type=plan_type,
                compliance_score=compliance_score,
                issues=issues,
                recommendations=recommendations,
                accessibility_score=accessibility_score,
                fire_safety_score=fire_safety_score,
                structural_score=structural_score
            )
            
        except Exception as e:
            self.logger.error(f"Error evaluando cumplimiento: {e}")
            return PlanCompliance(
                plan_type=plan_type,
                compliance_score=0.0,
                issues=[f"Error en evaluación: {str(e)}"],
                recommendations=["Revisar manualmente el plano"],
                accessibility_score=0.0,
                fire_safety_score=0.0,
                structural_score=0.0
            )
    
    def evaluate_accessibility(self, analysis: PlanAnalysis) -> Tuple[float, List[str], List[str]]:
        """Evalúa aspectos de accesibilidad"""
        try:
            score = 100.0
            issues = []
            recommendations = []
            
            # Verificar presencia de rampas
            ramps = [e for e in analysis.elements if e.element_type == 'ramp']
            if not ramps:
                score -= 30
                issues.append("No se detectaron rampas de accesibilidad")
                recommendations.append("Añadir rampas con pendiente máxima del 8%")
            
            # Verificar presencia de ascensores
            elevators = [e for e in analysis.elements if e.element_type == 'elevator']
            if not elevators:
                score -= 20
                issues.append("No se detectaron ascensores")
                recommendations.append("Instalar ascensores para accesibilidad vertical")
            
            # Verificar dimensiones de puertas
            doors = [e for e in analysis.elements if e.element_type == 'door']
            narrow_doors = [d for d in doors if d.dimensions.get('width', 0) < self.config['min_door_width']]
            if narrow_doors:
                score -= 15
                issues.append(f"Se detectaron {len(narrow_doors)} puertas demasiado estrechas")
                recommendations.append("Ampliar puertas a mínimo 0.8m de ancho")
            
            # Verificar características de accesibilidad detectadas
            if analysis.accessibility_features:
                score += 10
                recommendations.append("Buenas características de accesibilidad detectadas")
            
            return max(0, score), issues, recommendations
            
        except Exception as e:
            self.logger.error(f"Error evaluando accesibilidad: {e}")
            return 0.0, [f"Error en evaluación de accesibilidad: {str(e)}"], []
    
    def evaluate_fire_safety(self, analysis: PlanAnalysis) -> Tuple[float, List[str], List[str]]:
        """Evalúa aspectos de seguridad contra incendios"""
        try:
            score = 100.0
            issues = []
            recommendations = []
            
            # Verificar salidas de emergencia
            doors = [e for e in analysis.elements if e.element_type == 'door']
            if len(doors) < 2:
                score -= 40
                issues.append("Insuficientes salidas de emergencia")
                recommendations.append("Añadir al menos 2 salidas de emergencia")
            
            # Verificar escaleras de emergencia
            stairs = [e for e in analysis.elements if e.element_type == 'stair']
            if not stairs:
                score -= 30
                issues.append("No se detectaron escaleras de emergencia")
                recommendations.append("Añadir escaleras de emergencia")
            
            # Verificar dimensiones de pasillos
            # TODO: Implementar detección de pasillos
            
            return max(0, score), issues, recommendations
            
        except Exception as e:
            self.logger.error(f"Error evaluando seguridad contra incendios: {e}")
            return 0.0, [f"Error en evaluación de seguridad: {str(e)}"], []
    
    def evaluate_structural(self, analysis: PlanAnalysis) -> Tuple[float, List[str], List[str]]:
        """Evalúa aspectos estructurales"""
        try:
            score = 100.0
            issues = []
            recommendations = []
            
            # Verificar muros estructurales
            walls = [e for e in analysis.elements if e.element_type == 'wall']
            if len(walls) < 4:
                score -= 20
                issues.append("Insuficientes muros estructurales")
                recommendations.append("Verificar estructura portante")
            
            # Verificar dimensiones de habitaciones
            rooms = [e for e in analysis.elements if e.element_type == 'room']
            small_rooms = [r for r in rooms if r.dimensions.get('area', 0) < self.config['min_room_area']]
            if small_rooms:
                score -= 15
                issues.append(f"Se detectaron {len(small_rooms)} habitaciones demasiado pequeñas")
                recommendations.append("Ampliar habitaciones a mínimo 9m²")
            
            return max(0, score), issues, recommendations
            
        except Exception as e:
            self.logger.error(f"Error evaluando aspectos estructurales: {e}")
            return 0.0, [f"Error en evaluación estructural: {str(e)}"], []
    
    def filter_accessibility_issues(self, issues: List[str]) -> List[str]:
        """Filtra problemas relacionados con accesibilidad"""
        accessibility_keywords = ['rampa', 'ascensor', 'puerta', 'accesibilidad', 'discapacidad']
        return [issue for issue in issues if any(keyword in issue.lower() for keyword in accessibility_keywords)]
    
    def filter_fire_safety_issues(self, issues: List[str]) -> List[str]:
        """Filtra problemas relacionados con seguridad contra incendios"""
        fire_keywords = ['emergencia', 'incendio', 'salida', 'escalera', 'evacuación']
        return [issue for issue in issues if any(keyword in issue.lower() for keyword in fire_keywords)]
    
    def filter_structural_issues(self, issues: List[str]) -> List[str]:
        """Filtra problemas relacionados con aspectos estructurales"""
        structural_keywords = ['muro', 'estructura', 'habitación', 'área', 'dimensión']
        return [issue for issue in issues if any(keyword in issue.lower() for keyword in structural_keywords)]
    
    def calculate_overall_compliance(self, compliance_results: List[PlanCompliance]) -> float:
        """Calcula la puntuación general de cumplimiento"""
        try:
            if not compliance_results:
                return 0.0
            
            total_score = sum(result.compliance_score for result in compliance_results)
            return total_score / len(compliance_results)
            
        except Exception as e:
            self.logger.error(f"Error calculando cumplimiento general: {e}")
            return 0.0
    
    def generate_recommendations(self, compliance_results: List[PlanCompliance], 
                               critical_issues: List[str], accessibility_issues: List[str],
                               fire_safety_issues: List[str], structural_issues: List[str]) -> List[str]:
        """Genera recomendaciones generales"""
        try:
            recommendations = []
            
            # Recomendaciones por categoría
            if accessibility_issues:
                recommendations.append("PRIORIDAD ALTA: Mejorar accesibilidad del edificio")
            
            if fire_safety_issues:
                recommendations.append("PRIORIDAD ALTA: Revisar sistemas de seguridad contra incendios")
            
            if structural_issues:
                recommendations.append("PRIORIDAD MEDIA: Verificar aspectos estructurales")
            
            # Recomendaciones generales
            if len(critical_issues) > 5:
                recommendations.append("Revisión completa del proyecto recomendada")
            
            # Recomendaciones específicas de cada plano
            for result in compliance_results:
                recommendations.extend(result.recommendations)
            
            # Eliminar duplicados
            recommendations = list(set(recommendations))
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generando recomendaciones: {e}")
            return ["Error generando recomendaciones"]
    
    def save_analysis_result(self, result: PlanAnalysisResult, output_path: str):
        """Guarda el resultado del análisis"""
        try:
            # Convertir a diccionario serializable
            data = {
                'timestamp': datetime.now().isoformat(),
                'plans_analyzed': result.plans_analyzed,
                'total_elements': result.total_elements,
                'overall_compliance': result.overall_compliance,
                'compliance_results': [
                    {
                        'plan_type': cr.plan_type,
                        'compliance_score': cr.compliance_score,
                        'issues': cr.issues,
                        'recommendations': cr.recommendations,
                        'accessibility_score': cr.accessibility_score,
                        'fire_safety_score': cr.fire_safety_score,
                        'structural_score': cr.structural_score
                    }
                    for cr in result.compliance_results
                ],
                'critical_issues': result.critical_issues,
                'accessibility_issues': result.accessibility_issues,
                'fire_safety_issues': result.fire_safety_issues,
                'structural_issues': result.structural_issues,
                'recommendations': result.recommendations
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Resultado del análisis guardado en: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando resultado del análisis: {e}")
            raise
