"""
Generador de reportes Madrid con referencias específicas de normativa.
Incluye referencias exactas a documentos y páginas.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path

from .madrid_verification_engine import VerificationResult, VerificationItem, NormativeReference

logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    """Sección de reporte."""
    title: str
    content: str
    subsections: List['ReportSection'] = None
    normative_references: List[NormativeReference] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.normative_references is None:
            self.normative_references = []

class MadridReportGenerator:
    """Generador de reportes Madrid."""
    
    def __init__(self, output_dir: str = "reports"):
        self.logger = logging.getLogger(f"{__name__}.MadridReportGenerator")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_verification_report(self, 
                                   result: VerificationResult, 
                                   project_data: Dict[str, Any],
                                   format: str = "json") -> Dict[str, Any]:
        """
        Generar reporte completo de verificación.
        
        Args:
            result: Resultado de verificación
            project_data: Datos del proyecto
            format: Formato del reporte (json, html, pdf)
            
        Returns:
            Datos del reporte generado
        """
        try:
            self.logger.info(f"Generando reporte de verificación: {result.verification_id}")
            
            # Crear estructura del reporte
            report_data = self._create_report_structure(result, project_data)
            
            # Generar secciones del reporte
            sections = self._generate_report_sections(result, project_data)
            report_data['sections'] = sections
            
            # Agregar resumen ejecutivo
            report_data['executive_summary'] = self._generate_executive_summary(result)
            
            # Agregar referencias normativas
            report_data['normative_references'] = self._extract_normative_references(result)
            
            # Agregar recomendaciones
            report_data['recommendations'] = self._generate_recommendations(result)
            
            # Guardar reporte
            if format == "json":
                self._save_json_report(report_data, result.verification_id)
            elif format == "html":
                self._save_html_report(report_data, result.verification_id)
            
            self.logger.info(f"Reporte generado: {result.verification_id}")
            return report_data
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
            raise
    
    def _create_report_structure(self, result: VerificationResult, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear estructura base del reporte."""
        return {
            'report_id': f"RPT_{result.verification_id}",
            'project_id': result.project_id,
            'verification_id': result.verification_id,
            'project_data': {
                'is_existing_building': project_data.get('is_existing_building', False),
                'primary_use': project_data.get('primary_use', ''),
                'secondary_uses': project_data.get('secondary_uses', []),
                'files_uploaded': project_data.get('files', [])
            },
            'verification_summary': {
                'overall_status': result.overall_status.value,
                'compliance_percentage': result.compliance_percentage,
                'total_items': result.total_items,
                'compliant_items': result.compliant_items,
                'non_compliant_items': result.non_compliant_items,
                'partial_items': result.partial_items
            },
            'generated_at': datetime.now().isoformat(),
            'generator_version': '1.0.0'
        }
    
    def _generate_report_sections(self, result: VerificationResult, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generar secciones del reporte."""
        sections = []
        
        # Sección 1: Resumen de cumplimiento
        sections.append(self._create_compliance_summary_section(result))
        
        # Sección 2: Verificaciones por tipo de edificio
        sections.append(self._create_building_type_verifications_section(result, project_data))
        
        # Sección 3: Incumplimientos críticos
        sections.append(self._create_critical_issues_section(result))
        
        # Sección 4: Verificaciones por plantas
        sections.append(self._create_floor_verifications_section(result, project_data))
        
        # Sección 5: Referencias normativas detalladas
        sections.append(self._create_normative_references_section(result))
        
        return sections
    
    def _create_compliance_summary_section(self, result: VerificationResult) -> Dict[str, Any]:
        """Crear sección de resumen de cumplimiento."""
        status_emoji = {
            'compliant': '✅',
            'non_compliant': '❌',
            'partial': '⚠️',
            'pending': '⏳',
            'error': '🚫'
        }
        
        return {
            'title': 'Resumen de Cumplimiento Normativo',
            'content': f"""
            <h2>Estado General del Proyecto</h2>
            <p><strong>Estado:</strong> {status_emoji.get(result.overall_status.value, '❓')} {result.overall_status.value.upper()}</p>
            <p><strong>Porcentaje de Cumplimiento:</strong> {result.compliance_percentage:.1f}%</p>
            
            <h3>Estadísticas de Verificación</h3>
            <ul>
                <li><strong>Total de verificaciones:</strong> {result.total_items}</li>
                <li><strong>Cumplidas:</strong> {result.compliant_items}</li>
                <li><strong>No cumplidas:</strong> {result.non_compliant_items}</li>
                <li><strong>Parciales:</strong> {result.partial_items}</li>
            </ul>
            
            <h3>Distribución por Severidad</h3>
            <ul>
                <li><strong>Críticas:</strong> {result.summary.get('critical_issues', 0)}</li>
                <li><strong>Altas:</strong> {result.summary.get('high_issues', 0)}</li>
                <li><strong>Medias:</strong> {result.summary.get('medium_issues', 0)}</li>
                <li><strong>Bajas:</strong> {result.summary.get('low_issues', 0)}</li>
            </ul>
            """,
            'normative_references': []
        }
    
    def _create_building_type_verifications_section(self, result: VerificationResult, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear sección de verificaciones por tipo de edificio."""
        primary_use = project_data.get('primary_use', '')
        secondary_uses = project_data.get('secondary_uses', [])
        
        content = f"<h2>Verificaciones por Tipo de Edificio</h2>"
        content += f"<h3>Uso Principal: {primary_use.upper()}</h3>"
        
        # Verificaciones para uso principal
        primary_items = [item for item in result.verification_items if not item.item_id.endswith('_sec_')]
        if primary_items:
            content += "<ul>"
            for item in primary_items:
                status_icon = "✅" if item.status.value == "compliant" else "❌" if item.status.value == "non_compliant" else "⚠️"
                content += f"<li>{status_icon} <strong>{item.title}</strong> - {item.status.value.upper()}</li>"
            content += "</ul>"
        
        # Verificaciones para usos secundarios
        if secondary_uses:
            content += "<h3>Usos Secundarios</h3>"
            for secondary_use in secondary_uses:
                use_type = secondary_use.get('use_type', '')
                floors = secondary_use.get('floors', [])
                content += f"<h4>{use_type.upper()} (Plantas: {', '.join(map(str, floors))})</h4>"
                
                secondary_items = [item for item in result.verification_items if item.item_id.endswith(f'_sec_{use_type}')]
                if secondary_items:
                    content += "<ul>"
                    for item in secondary_items:
                        status_icon = "✅" if item.status.value == "compliant" else "❌" if item.status.value == "non_compliant" else "⚠️"
                        content += f"<li>{status_icon} <strong>{item.title}</strong> - {item.status.value.upper()}</li>"
                    content += "</ul>"
        
        return {
            'title': 'Verificaciones por Tipo de Edificio',
            'content': content,
            'normative_references': []
        }
    
    def _create_critical_issues_section(self, result: VerificationResult) -> Dict[str, Any]:
        """Crear sección de incumplimientos críticos."""
        critical_items = [
            item for item in result.verification_items 
            if item.severity.value == 'critical' and item.status.value == 'non_compliant'
        ]
        
        if not critical_items:
            content = "<h2>Incumplimientos Críticos</h2><p>✅ No se encontraron incumplimientos críticos.</p>"
        else:
            content = "<h2>Incumplimientos Críticos</h2><ul>"
            for item in critical_items:
                content += f"<li><strong>{item.title}</strong><br>"
                content += f"<em>{item.description}</em><br>"
                content += f"<strong>Notas:</strong> {', '.join(item.verification_notes)}</li>"
            content += "</ul>"
        
        return {
            'title': 'Incumplimientos Críticos',
            'content': content,
            'normative_references': []
        }
    
    def _create_floor_verifications_section(self, result: VerificationResult, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear sección de verificaciones por plantas."""
        secondary_uses = project_data.get('secondary_uses', [])
        
        content = "<h2>Verificaciones por Plantas</h2>"
        
        if not secondary_uses:
            content += "<p>No hay usos secundarios que requieran verificación por plantas.</p>"
        else:
            content += "<h3>Distribución de Usos por Plantas</h3>"
            for secondary_use in secondary_uses:
                use_type = secondary_use.get('use_type', '')
                floors = secondary_use.get('floors', [])
                
                content += f"<h4>{use_type.upper()}</h4>"
                content += f"<p><strong>Plantas:</strong> {', '.join(map(str, floors))}</p>"
                
                # Verificaciones específicas para este uso
                related_items = [item for item in result.verification_items if item.item_id.endswith(f'_sec_{use_type}')]
                if related_items:
                    content += "<ul>"
                    for item in related_items:
                        status_icon = "✅" if item.status.value == "compliant" else "❌" if item.status.value == "non_compliant" else "⚠️"
                        content += f"<li>{status_icon} {item.title}</li>"
                    content += "</ul>"
        
        return {
            'title': 'Verificaciones por Plantas',
            'content': content,
            'normative_references': []
        }
    
    def _create_normative_references_section(self, result: VerificationResult) -> Dict[str, Any]:
        """Crear sección de referencias normativas detalladas."""
        content = "<h2>Referencias Normativas Detalladas</h2>"
        
        # Agrupar referencias por documento
        references_by_doc = {}
        for item in result.verification_items:
            for ref in item.normative_references:
                doc_name = ref.document_name
                if doc_name not in references_by_doc:
                    references_by_doc[doc_name] = []
                references_by_doc[doc_name].append({
                    'item_title': item.title,
                    'page_number': ref.page_number,
                    'section_title': ref.section_title,
                    'status': item.status.value
                })
        
        if not references_by_doc:
            content += "<p>No se encontraron referencias normativas específicas.</p>"
        else:
            for doc_name, refs in references_by_doc.items():
                content += f"<h3>{doc_name}</h3><ul>"
                for ref in refs:
                    status_icon = "✅" if ref['status'] == "compliant" else "❌" if ref['status'] == "non_compliant" else "⚠️"
                    content += f"<li>{status_icon} <strong>{ref['item_title']}</strong> - Página {ref['page_number']}: {ref['section_title']}</li>"
                content += "</ul>"
        
        return {
            'title': 'Referencias Normativas Detalladas',
            'content': content,
            'normative_references': []
        }
    
    def _generate_executive_summary(self, result: VerificationResult) -> Dict[str, Any]:
        """Generar resumen ejecutivo."""
        status_description = {
            'compliant': 'El proyecto cumple con todos los requisitos normativos aplicables.',
            'non_compliant': 'El proyecto presenta incumplimientos que requieren corrección.',
            'partial': 'El proyecto cumple parcialmente con los requisitos normativos.',
            'pending': 'La verificación del proyecto está pendiente de completar.',
            'error': 'Se produjeron errores durante la verificación del proyecto.'
        }
        
        return {
            'status': result.overall_status.value,
            'description': status_description.get(result.overall_status.value, 'Estado desconocido'),
            'compliance_percentage': result.compliance_percentage,
            'critical_issues_count': result.summary.get('critical_issues', 0),
            'high_issues_count': result.summary.get('high_issues', 0),
            'recommendations': self._generate_recommendations(result)
        }
    
    def _extract_normative_references(self, result: VerificationResult) -> List[Dict[str, Any]]:
        """Extraer todas las referencias normativas."""
        references = []
        seen_refs = set()
        
        for item in result.verification_items:
            for ref in item.normative_references:
                ref_key = f"{ref.document_name}_{ref.page_number}_{ref.section_title}"
                if ref_key not in seen_refs:
                    references.append({
                        'document_name': ref.document_name,
                        'document_category': ref.document_category,
                        'page_number': ref.page_number,
                        'section_title': ref.section_title,
                        'building_type': ref.building_type,
                        'url': ref.url
                    })
                    seen_refs.add(ref_key)
        
        return references
    
    def _generate_recommendations(self, result: VerificationResult) -> List[str]:
        """Generar recomendaciones basadas en el resultado."""
        recommendations = []
        
        if result.overall_status.value == 'non_compliant':
            recommendations.append("Revisar y corregir todos los incumplimientos identificados antes de proceder con el proyecto.")
        
        if result.summary.get('critical_issues', 0) > 0:
            recommendations.append("Priorizar la resolución de los incumplimientos críticos identificados.")
        
        if result.summary.get('high_issues', 0) > 0:
            recommendations.append("Revisar los incumplimientos de alta prioridad para mejorar el cumplimiento normativo.")
        
        if result.compliance_percentage < 80:
            recommendations.append("Considerar una revisión integral del proyecto para mejorar el cumplimiento normativo.")
        
        if not recommendations:
            recommendations.append("El proyecto cumple adecuadamente con los requisitos normativos aplicables.")
        
        return recommendations
    
    def _save_json_report(self, report_data: Dict[str, Any], verification_id: str):
        """Guardar reporte en formato JSON."""
        filename = f"verification_report_{verification_id}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Reporte JSON guardado: {filepath}")
    
    def _save_html_report(self, report_data: Dict[str, Any], verification_id: str):
        """Guardar reporte en formato HTML."""
        filename = f"verification_report_{verification_id}.html"
        filepath = self.output_dir / filename
        
        html_content = self._generate_html_content(report_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Reporte HTML guardado: {filepath}")
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generar contenido HTML del reporte."""
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reporte de Verificación - {report_data['verification_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .status-compliant {{ color: #28a745; }}
                .status-non-compliant {{ color: #dc3545; }}
                .status-partial {{ color: #ffc107; }}
                .status-pending {{ color: #17a2b8; }}
                .status-error {{ color: #6c757d; }}
                .normative-ref {{ background-color: #e9ecef; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }}
                .recommendations {{ background-color: #d4edda; padding: 15px; border-radius: 5px; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Reporte de Verificación Normativa Madrid</h1>
                <p><strong>ID de Verificación:</strong> {report_data['verification_id']}</p>
                <p><strong>ID de Proyecto:</strong> {report_data['project_id']}</p>
                <p><strong>Generado:</strong> {report_data['generated_at']}</p>
            </div>
        """
        
        # Agregar secciones
        for section in report_data.get('sections', []):
            html += f"""
            <div class="section">
                <h2>{section['title']}</h2>
                {section['content']}
            </div>
            """
        
        # Agregar recomendaciones
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            html += f"""
            <div class="section recommendations">
                <h2>Recomendaciones</h2>
                <ul>
                    {''.join(f'<li>{rec}</li>' for rec in recommendations)}
                </ul>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
