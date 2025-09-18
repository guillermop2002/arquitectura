"""
Generador de Reporte Final para Verificación Arquitectónica de Madrid.
Genera reportes completos con checklist final y recomendaciones.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from .madrid_final_checklist_system import FinalChecklist, ChecklistItem, ChecklistCategory

logger = logging.getLogger(__name__)

@dataclass
class FinalReport:
    """Reporte final completo del proyecto."""
    project_id: str
    project_name: str
    building_type: str
    is_existing_building: bool
    report_date: datetime
    executive_summary: Dict[str, Any]
    checklist_summary: Dict[str, Any]
    compliance_analysis: Dict[str, Any]
    normative_analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    next_steps: List[Dict[str, Any]]
    technical_details: Dict[str, Any]
    appendices: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class MadridFinalReportGenerator:
    """Generador de reportes finales para Madrid."""
    
    def __init__(self):
        """Inicializar el generador de reportes."""
        self.report_templates = self._load_report_templates()
        
        logger.info("MadridFinalReportGenerator initialized")
    
    def _load_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Cargar plantillas de reporte por tipo de edificio."""
        return {
            "residencial": {
                "title": "Reporte Final de Verificación Arquitectónica - Edificio Residencial",
                "sections": [
                    "resumen_ejecutivo",
                    "analisis_normativo",
                    "verificacion_cumplimiento",
                    "checklist_final",
                    "recomendaciones",
                    "proximos_pasos"
                ]
            },
            "industrial": {
                "title": "Reporte Final de Verificación Arquitectónica - Edificio Industrial",
                "sections": [
                    "resumen_ejecutivo",
                    "analisis_normativo",
                    "verificacion_cumplimiento",
                    "checklist_final",
                    "recomendaciones",
                    "proximos_pasos"
                ]
            }
        }
    
    def generate_final_report(self, 
                            checklist: FinalChecklist, 
                            compliance_results: Dict[str, Any], 
                            normative_application: Dict[str, Any],
                            project_data: Dict[str, Any]) -> FinalReport:
        """
        Generar reporte final completo.
        
        Args:
            checklist: Checklist final del proyecto
            compliance_results: Resultados de verificación de cumplimiento
            normative_application: Aplicación de normativa específica
            project_data: Datos del proyecto
            
        Returns:
            Reporte final completo
        """
        try:
            logger.info(f"Generando reporte final para proyecto {checklist.project_id}")
            
            # Generar resumen ejecutivo
            executive_summary = self._generate_executive_summary(checklist, compliance_results)
            
            # Generar resumen del checklist
            checklist_summary = self._generate_checklist_summary(checklist)
            
            # Generar análisis de cumplimiento
            compliance_analysis = self._generate_compliance_analysis(compliance_results)
            
            # Generar análisis normativo
            normative_analysis = self._generate_normative_analysis(normative_application)
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(checklist, compliance_results)
            
            # Generar próximos pasos
            next_steps = self._generate_next_steps(checklist, compliance_results)
            
            # Generar detalles técnicos
            technical_details = self._generate_technical_details(checklist, compliance_results, project_data)
            
            # Generar apéndices
            appendices = self._generate_appendices(checklist, compliance_results, normative_application)
            
            # Crear reporte final
            report = FinalReport(
                project_id=checklist.project_id,
                project_name=checklist.project_name,
                building_type=checklist.building_type,
                is_existing_building=checklist.is_existing_building,
                report_date=datetime.now(),
                executive_summary=executive_summary,
                checklist_summary=checklist_summary,
                compliance_analysis=compliance_analysis,
                normative_analysis=normative_analysis,
                recommendations=recommendations,
                next_steps=next_steps,
                technical_details=technical_details,
                appendices=appendices,
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "template_version": "1.0",
                    "system_version": "Madrid Verification System v1.0"
                }
            )
            
            logger.info(f"Reporte final generado para proyecto {checklist.project_id}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte final: {e}")
            raise
    
    def _generate_executive_summary(self, 
                                  checklist: FinalChecklist, 
                                  compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generar resumen ejecutivo del reporte."""
        # Calcular estadísticas generales
        total_checks = checklist.total_items
        completed_checks = checklist.completed_items
        completion_percentage = checklist.overall_completion
        
        # Contar problemas por severidad
        critical_issues = len([item for item in self._get_all_items(checklist) 
                             if item.priority.value == "critical" and item.status.value == "failed"])
        high_issues = len([item for item in self._get_all_items(checklist) 
                          if item.priority.value == "high" and item.status.value == "failed"])
        
        # Determinar estado general
        if critical_issues > 0:
            overall_status = "CRÍTICO"
            status_color = "danger"
        elif high_issues > 0:
            overall_status = "REQUIERE ATENCIÓN"
            status_color = "warning"
        elif completion_percentage >= 90:
            overall_status = "CUMPLE"
            status_color = "success"
        else:
            overall_status = "EN PROGRESO"
            status_color = "info"
        
        return {
            "overall_status": overall_status,
            "status_color": status_color,
            "completion_percentage": completion_percentage,
            "total_checks": total_checks,
            "completed_checks": completed_checks,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "building_type": checklist.building_type,
            "is_existing_building": checklist.is_existing_building,
            "project_name": checklist.project_name,
            "report_date": datetime.now().strftime("%d/%m/%Y"),
            "summary_text": self._generate_summary_text(checklist, compliance_results)
        }
    
    def _generate_summary_text(self, 
                             checklist: FinalChecklist, 
                             compliance_results: Dict[str, Any]) -> str:
        """Generar texto de resumen ejecutivo."""
        completion = checklist.overall_completion
        critical_issues = len([item for item in self._get_all_items(checklist) 
                             if item.priority.value == "critical" and item.status.value == "failed"])
        
        if critical_issues > 0:
            return f"El proyecto presenta {critical_issues} problemas críticos que requieren resolución inmediata antes de continuar con el proceso de verificación. El cumplimiento general es del {completion:.1f}%."
        elif completion >= 90:
            return f"El proyecto cumple con la normativa aplicable con un {completion:.1f}% de verificación completada. Se recomienda revisar los elementos pendientes antes de la aprobación final."
        else:
            return f"El proyecto está en proceso de verificación con un {completion:.1f}% completado. Se requieren acciones adicionales para cumplir con todos los requisitos normativos."
    
    def _generate_checklist_summary(self, checklist: FinalChecklist) -> Dict[str, Any]:
        """Generar resumen del checklist."""
        categories_summary = []
        
        for category in checklist.categories:
            categories_summary.append({
                "name": category.name,
                "completion_percentage": category.completion_percentage,
                "total_items": category.total_items,
                "completed_items": category.completed_items,
                "pending_items": category.total_items - category.completed_items,
                "critical_items": len([item for item in category.items if item.priority.value == "critical"]),
                "high_priority_items": len([item for item in category.items if item.priority.value == "high"])
            })
        
        return {
            "overall_completion": checklist.overall_completion,
            "total_items": checklist.total_items,
            "completed_items": checklist.completed_items,
            "pending_items": checklist.total_items - checklist.completed_items,
            "critical_items": checklist.critical_items,
            "high_priority_items": checklist.high_priority_items,
            "categories": categories_summary
        }
    
    def _generate_compliance_analysis(self, compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generar análisis de cumplimiento."""
        return {
            "overall_score": compliance_results.get('compliance_score', 0.0),
            "total_checks": compliance_results.get('total_checks', 0),
            "passed_checks": compliance_results.get('passed_checks', 0),
            "failed_checks": compliance_results.get('failed_checks', 0),
            "critical_issues": compliance_results.get('critical_issues', 0),
            "high_issues": compliance_results.get('high_issues', 0),
            "medium_issues": compliance_results.get('medium_issues', 0),
            "low_issues": compliance_results.get('low_issues', 0),
            "issues_by_category": self._categorize_issues(compliance_results.get('issues', [])),
            "floor_analysis": compliance_results.get('floor_compliance', {}),
            "document_analysis": compliance_results.get('document_compliance', {})
        }
    
    def _categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorizar problemas por tipo."""
        categorized = {}
        
        for issue in issues:
            category = issue.get('category', 'general')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(issue)
        
        return categorized
    
    def _generate_normative_analysis(self, normative_application: Dict[str, Any]) -> Dict[str, Any]:
        """Generar análisis normativo."""
        return {
            "primary_use": normative_application.get('primary_use', ''),
            "secondary_uses": normative_application.get('secondary_uses', []),
            "is_existing_building": normative_application.get('is_existing_building', False),
            "applicable_documents": normative_application.get('applicable_documents', []),
            "total_documents": len(normative_application.get('applicable_documents', [])),
            "documents_by_type": self._categorize_documents(normative_application.get('applicable_documents', [])),
            "floor_assignments": normative_application.get('floor_assignments', {}),
            "compliance_requirements": normative_application.get('compliance_requirements', {})
        }
    
    def _categorize_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorizar documentos por tipo."""
        categorized = {"basic": 0, "pgoum": 0, "support": 0}
        
        for doc in documents:
            doc_type = doc.get('type', 'basic')
            if doc_type in categorized:
                categorized[doc_type] += 1
        
        return categorized
    
    def _generate_recommendations(self, 
                                checklist: FinalChecklist, 
                                compliance_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generar recomendaciones basadas en el análisis."""
        recommendations = []
        
        # Recomendaciones por problemas críticos
        critical_items = [item for item in self._get_all_items(checklist) 
                         if item.priority.value == "critical" and item.status.value == "failed"]
        
        if critical_items:
            recommendations.append({
                "priority": "critical",
                "title": "Resolver problemas críticos",
                "description": f"Se identificaron {len(critical_items)} problemas críticos que requieren resolución inmediata",
                "action": "Revisar y corregir todos los elementos marcados como críticos",
                "items": [item.title for item in critical_items],
                "timeline": "Inmediato"
            })
        
        # Recomendaciones por categoría incompleta
        for category in checklist.categories:
            if category.completion_percentage < 70:
                recommendations.append({
                    "priority": "high",
                    "title": f"Completar verificación de {category.name}",
                    "description": f"La categoría {category.name} está solo {category.completion_percentage:.1f}% completa",
                    "action": f"Completar los elementos pendientes en {category.name}",
                    "items": [item.title for item in category.items if item.status.value == "pending"],
                    "timeline": "1-2 semanas"
                })
        
        # Recomendaciones por cumplimiento general
        if checklist.overall_completion < 80:
            recommendations.append({
                "priority": "medium",
                "title": "Mejorar cumplimiento general",
                "description": f"El cumplimiento general es del {checklist.overall_completion:.1f}%",
                "action": "Revisar y completar elementos pendientes en todas las categorías",
                "items": [],
                "timeline": "2-4 semanas"
            })
        
        return recommendations
    
    def _generate_next_steps(self, 
                           checklist: FinalChecklist, 
                           compliance_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generar próximos pasos basados en el estado actual."""
        next_steps = []
        
        # Próximos pasos por prioridad
        high_priority_pending = [item for item in self._get_all_items(checklist) 
                               if item.priority.value == "high" and item.status.value == "pending"]
        
        if high_priority_pending:
            next_steps.append({
                "step": 1,
                "title": "Completar elementos de alta prioridad",
                "description": f"Completar {len(high_priority_pending)} elementos de alta prioridad",
                "estimated_time": "1-2 semanas",
                "responsible": "Equipo técnico",
                "items": [item.title for item in high_priority_pending[:3]]
            })
        
        # Próximos pasos por categoría
        for category in checklist.categories:
            pending_items = [item for item in category.items if item.status.value == "pending"]
            if pending_items:
                next_steps.append({
                    "step": len(next_steps) + 1,
                    "title": f"Completar {category.name}",
                    "description": f"Completar {len(pending_items)} elementos pendientes en {category.name}",
                    "estimated_time": "1 semana",
                    "responsible": "Equipo técnico",
                    "items": [item.title for item in pending_items[:3]]
                })
        
        return next_steps
    
    def _generate_technical_details(self, 
                                  checklist: FinalChecklist, 
                                  compliance_results: Dict[str, Any], 
                                  project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generar detalles técnicos del reporte."""
        return {
            "project_metadata": {
                "project_id": checklist.project_id,
                "project_name": checklist.project_name,
                "building_type": checklist.building_type,
                "is_existing_building": checklist.is_existing_building,
                "created_at": checklist.created_at.isoformat(),
                "updated_at": checklist.updated_at.isoformat()
            },
            "checklist_metadata": {
                "total_categories": len(checklist.categories),
                "total_items": checklist.total_items,
                "completed_items": checklist.completed_items,
                "critical_items": checklist.critical_items,
                "high_priority_items": checklist.high_priority_items
            },
            "compliance_metadata": {
                "overall_score": compliance_results.get('compliance_score', 0.0),
                "total_checks": compliance_results.get('total_checks', 0),
                "passed_checks": compliance_results.get('passed_checks', 0),
                "failed_checks": compliance_results.get('failed_checks', 0)
            },
            "system_metadata": {
                "generated_at": datetime.now().isoformat(),
                "template_version": "1.0",
                "system_version": "Madrid Verification System v1.0"
            }
        }
    
    def _generate_appendices(self, 
                           checklist: FinalChecklist, 
                           compliance_results: Dict[str, Any], 
                           normative_application: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generar apéndices del reporte."""
        appendices = []
        
        # Apéndice A: Checklist completo
        appendices.append({
            "id": "A",
            "title": "Checklist Completo de Verificación",
            "content": self._format_checklist_for_appendix(checklist)
        })
        
        # Apéndice B: Análisis de cumplimiento detallado
        appendices.append({
            "id": "B",
            "title": "Análisis de Cumplimiento Detallado",
            "content": compliance_results
        })
        
        # Apéndice C: Normativa aplicada
        appendices.append({
            "id": "C",
            "title": "Normativa Aplicada",
            "content": normative_application
        })
        
        return appendices
    
    def _format_checklist_for_appendix(self, checklist: FinalChecklist) -> Dict[str, Any]:
        """Formatear checklist para apéndice."""
        return {
            "project_info": {
                "project_id": checklist.project_id,
                "project_name": checklist.project_name,
                "building_type": checklist.building_type,
                "is_existing_building": checklist.is_existing_building
            },
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "completion_percentage": category.completion_percentage,
                    "items": [
                        {
                            "id": item.id,
                            "title": item.title,
                            "description": item.description,
                            "priority": item.priority.value,
                            "status": item.status.value,
                            "normative_reference": item.normative_reference,
                            "evidence_required": item.evidence_required,
                            "current_evidence": item.current_evidence,
                            "notes": item.notes
                        }
                        for item in category.items
                    ]
                }
                for category in checklist.categories
            ]
        }
    
    def _get_all_items(self, checklist: FinalChecklist) -> List[ChecklistItem]:
        """Obtener todos los elementos del checklist."""
        all_items = []
        for category in checklist.categories:
            all_items.extend(category.items)
        return all_items
    
    def export_report_to_json(self, report: FinalReport) -> str:
        """Exportar reporte a JSON."""
        try:
            # Convertir datetime a string para JSON
            report_dict = {
                "project_id": report.project_id,
                "project_name": report.project_name,
                "building_type": report.building_type,
                "is_existing_building": report.is_existing_building,
                "report_date": report.report_date.isoformat(),
                "executive_summary": report.executive_summary,
                "checklist_summary": report.checklist_summary,
                "compliance_analysis": report.compliance_analysis,
                "normative_analysis": report.normative_analysis,
                "recommendations": report.recommendations,
                "next_steps": report.next_steps,
                "technical_details": report.technical_details,
                "appendices": report.appendices,
                "metadata": report.metadata
            }
            
            return json.dumps(report_dict, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error exportando reporte a JSON: {e}")
            raise
