"""
Lógica de verificación de cumplimiento para producción.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    """Niveles de cumplimiento normativo."""
    FULL = "full"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"

class NormativeStandard(Enum):
    """Estándares normativos aplicables."""
    CTE = "cte"  # Código Técnico de la Edificación
    LOUA = "loua"  # Ley de Ordenación Urbanística de Andalucía
    PGOU = "pgou"  # Plan General de Ordenación Urbanística
    NBE = "nbe"  # Normas Básicas de la Edificación
    OTHER = "other"

@dataclass
class ComplianceCheck:
    """Verificación de cumplimiento individual."""
    id: str
    title: str
    description: str
    standard: NormativeStandard
    level: ComplianceLevel
    evidence: List[str]
    recommendations: List[str]
    severity: str = "medium"
    checked_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now()

@dataclass
class ComplianceReport:
    """Reporte completo de cumplimiento."""
    project_id: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    partial_checks: int
    not_applicable_checks: int
    compliance_percentage: float
    checks: List[ComplianceCheck]
    generated_at: datetime
    standards_checked: List[NormativeStandard]
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()

class ProductionComplianceChecker:
    """Verificador de cumplimiento para producción."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar el verificador de cumplimiento.
        
        Args:
            config: Configuración del verificador
        """
        self.config = config or {}
        self.standards = self.config.get('standards', [NormativeStandard.CTE])
        self.strict_mode = self.config.get('strict_mode', False)
        
        # Cargar reglas de cumplimiento
        self.compliance_rules = self._load_compliance_rules()
        
        logger.info("ProductionComplianceChecker initialized")
    
    def _load_compliance_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Cargar reglas de cumplimiento desde configuración.
        
        Returns:
            Diccionario de reglas por estándar
        """
        rules = {
            NormativeStandard.CTE.value: [
                {
                    "id": "cte_01",
                    "title": "Seguridad estructural",
                    "description": "Verificar cumplimiento de la seguridad estructural según CTE",
                    "required_documents": ["memoria_calculo", "planos_estructura"],
                    "severity": "critical"
                },
                {
                    "id": "cte_02", 
                    "title": "Seguridad contra incendios",
                    "description": "Verificar medidas de protección contra incendios",
                    "required_documents": ["memoria_incendios", "planos_evacuacion"],
                    "severity": "critical"
                },
                {
                    "id": "cte_03",
                    "title": "Seguridad de utilización",
                    "description": "Verificar accesibilidad y seguridad de uso",
                    "required_documents": ["memoria_accesibilidad", "planos_accesibilidad"],
                    "severity": "high"
                },
                {
                    "id": "cte_04",
                    "title": "Salubridad",
                    "description": "Verificar condiciones de salubridad",
                    "required_documents": ["memoria_salubridad", "planos_instalaciones"],
                    "severity": "high"
                },
                {
                    "id": "cte_05",
                    "title": "Ahorro de energía",
                    "description": "Verificar eficiencia energética",
                    "required_documents": ["memoria_energetica", "certificado_eficiencia"],
                    "severity": "medium"
                }
            ],
            NormativeStandard.LOUA.value: [
                {
                    "id": "loua_01",
                    "title": "Ordenación territorial",
                    "description": "Verificar cumplimiento de ordenación territorial",
                    "required_documents": ["memoria_urbanistica", "planos_ordenacion"],
                    "severity": "high"
                },
                {
                    "id": "loua_02",
                    "title": "Impacto ambiental",
                    "description": "Verificar evaluación de impacto ambiental",
                    "required_documents": ["estudio_impacto", "declaracion_impacto"],
                    "severity": "high"
                }
            ]
        }
        
        return rules
    
    def check_project_compliance(self, project_data: Dict[str, Any]) -> ComplianceReport:
        """
        Verificar cumplimiento de un proyecto.
        
        Args:
            project_data: Datos del proyecto a verificar
            
        Returns:
            Reporte de cumplimiento
        """
        project_id = project_data.get('project_id', 'unknown')
        documents = project_data.get('documents', [])
        project_type = project_data.get('type', 'residential')
        
        checks = []
        standards_checked = []
        
        # Verificar cada estándar configurado
        for standard in self.standards:
            if standard.value in self.compliance_rules:
                standards_checked.append(standard)
                standard_checks = self._check_standard_compliance(
                    standard, documents, project_type
                )
                checks.extend(standard_checks)
        
        # Calcular estadísticas
        total_checks = len(checks)
        passed_checks = len([c for c in checks if c.level == ComplianceLevel.FULL])
        failed_checks = len([c for c in checks if c.level == ComplianceLevel.NON_COMPLIANT])
        partial_checks = len([c for c in checks if c.level == ComplianceLevel.PARTIAL])
        not_applicable_checks = len([c for c in checks if c.level == ComplianceLevel.NOT_APPLICABLE])
        
        compliance_percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        return ComplianceReport(
            project_id=project_id,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            partial_checks=partial_checks,
            not_applicable_checks=not_applicable_checks,
            compliance_percentage=compliance_percentage,
            checks=checks,
            generated_at=datetime.now(),
            standards_checked=standards_checked
        )
    
    def _check_standard_compliance(self, 
                                 standard: NormativeStandard, 
                                 documents: List[Dict[str, Any]], 
                                 project_type: str) -> List[ComplianceCheck]:
        """
        Verificar cumplimiento de un estándar específico.
        
        Args:
            standard: Estándar a verificar
            documents: Lista de documentos del proyecto
            project_type: Tipo de proyecto
            
        Returns:
            Lista de verificaciones realizadas
        """
        checks = []
        rules = self.compliance_rules.get(standard.value, [])
        
        for rule in rules:
            check = self._evaluate_rule(rule, documents, project_type)
            checks.append(check)
        
        return checks
    
    def _evaluate_rule(self, 
                      rule: Dict[str, Any], 
                      documents: List[Dict[str, Any]], 
                      project_type: str) -> ComplianceCheck:
        """
        Evaluar una regla específica.
        
        Args:
            rule: Regla a evaluar
            documents: Documentos disponibles
            project_type: Tipo de proyecto
            
        Returns:
            Verificación de cumplimiento
        """
        required_docs = rule.get('required_documents', [])
        found_docs = []
        missing_docs = []
        
        # Verificar documentos requeridos
        for req_doc in required_docs:
            if self._find_document(documents, req_doc):
                found_docs.append(req_doc)
            else:
                missing_docs.append(req_doc)
        
        # Determinar nivel de cumplimiento
        if not missing_docs:
            level = ComplianceLevel.FULL
            evidence = found_docs
            recommendations = []
        elif len(found_docs) > 0:
            level = ComplianceLevel.PARTIAL
            evidence = found_docs
            recommendations = [f"Falta: {doc}" for doc in missing_docs]
        else:
            level = ComplianceLevel.NON_COMPLIANT
            evidence = []
            recommendations = [f"Requerido: {doc}" for doc in missing_docs]
        
        return ComplianceCheck(
            id=rule['id'],
            title=rule['title'],
            description=rule['description'],
            standard=NormativeStandard(rule.get('standard', 'cte')),
            level=level,
            evidence=evidence,
            recommendations=recommendations,
            severity=rule.get('severity', 'medium')
        )
    
    def _find_document(self, documents: List[Dict[str, Any]], doc_type: str) -> bool:
        """
        Buscar un tipo de documento en la lista.
        
        Args:
            documents: Lista de documentos
            doc_type: Tipo de documento a buscar
            
        Returns:
            True si se encuentra el documento
        """
        for doc in documents:
            doc_name = doc.get('name', '').lower()
            doc_type_lower = doc_type.lower()
            
            # Buscar coincidencias parciales
            if (doc_type_lower in doc_name or 
                any(keyword in doc_name for keyword in doc_type_lower.split('_'))):
                return True
        
        return False
    
    def get_compliance_summary(self, report: ComplianceReport) -> Dict[str, Any]:
        """
        Obtener resumen del reporte de cumplimiento.
        
        Args:
            report: Reporte de cumplimiento
            
        Returns:
            Resumen del cumplimiento
        """
        critical_issues = [c for c in report.checks if c.severity == 'critical' and c.level == ComplianceLevel.NON_COMPLIANT]
        high_issues = [c for c in report.checks if c.severity == 'high' and c.level == ComplianceLevel.NON_COMPLIANT]
        
        return {
            'project_id': report.project_id,
            'compliance_percentage': report.compliance_percentage,
            'total_checks': report.total_checks,
            'passed_checks': report.passed_checks,
            'failed_checks': report.failed_checks,
            'critical_issues': len(critical_issues),
            'high_priority_issues': len(high_issues),
            'standards_checked': [s.value for s in report.standards_checked],
            'overall_status': self._get_overall_status(report),
            'generated_at': report.generated_at.isoformat()
        }
    
    def _get_overall_status(self, report: ComplianceReport) -> str:
        """
        Determinar el estado general del cumplimiento.
        
        Args:
            report: Reporte de cumplimiento
            
        Returns:
            Estado general
        """
        if report.compliance_percentage >= 90:
            return "excellent"
        elif report.compliance_percentage >= 75:
            return "good"
        elif report.compliance_percentage >= 50:
            return "acceptable"
        else:
            return "needs_improvement"
    
    def generate_recommendations(self, report: ComplianceReport) -> List[str]:
        """
        Generar recomendaciones basadas en el reporte.
        
        Args:
            report: Reporte de cumplimiento
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Recomendaciones por severidad
        critical_issues = [c for c in report.checks if c.severity == 'critical' and c.level != ComplianceLevel.FULL]
        if critical_issues:
            recommendations.append("URGENTE: Resolver problemas críticos de cumplimiento antes de continuar")
        
        high_issues = [c for c in report.checks if c.severity == 'high' and c.level != ComplianceLevel.FULL]
        if high_issues:
            recommendations.append("ALTA PRIORIDAD: Atender problemas de alta prioridad para mejorar el cumplimiento")
        
        # Recomendaciones generales
        if report.compliance_percentage < 50:
            recommendations.append("El proyecto requiere una revisión completa de cumplimiento normativo")
        elif report.compliance_percentage < 75:
            recommendations.append("Se recomienda mejorar el cumplimiento antes de la aprobación final")
        
        return recommendations
