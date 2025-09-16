"""
Generador de Reportes Detallados
Fase 3: Sistema de Preguntas Inteligentes
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import pandas as pd

from .config import get_config
from .logging_config import get_logger
from .ai_client import get_ai_client, AIResponse
from .neo4j_manager import Neo4jManager

logger = get_logger(__name__)

class ReportType(Enum):
    """Tipos de reportes"""
    COMPREHENSIVE = "comprehensive"
    COMPLIANCE = "compliance"
    TECHNICAL = "technical"
    AMBIGUITY = "ambiguity"
    QUESTION_ANALYSIS = "question_analysis"
    EXECUTIVE_SUMMARY = "executive_summary"

@dataclass
class ReportSection:
    """Sección de un reporte"""
    section_id: str
    title: str
    content: str
    subsections: List['ReportSection']
    charts: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    priority: str  # 'HIGH', 'MEDIUM', 'LOW'

@dataclass
class Report:
    """Reporte completo"""
    report_id: str
    project_id: str
    report_type: ReportType
    title: str
    sections: List[ReportSection]
    metadata: Dict[str, Any]
    generated_at: str
    file_path: str

class ReportGenerator:
    """Generador de reportes detallados para verificación arquitectónica"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Cliente de IA
        self.ai_client = get_ai_client()
        
        # Gestor de Neo4j
        self.neo4j_manager = Neo4jManager()
        
        # Configuración de reportes
        self.report_templates = self._initialize_report_templates()
        
        # Configuración de gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def _initialize_report_templates(self) -> Dict[ReportType, Dict[str, Any]]:
        """Inicializa plantillas de reportes"""
        return {
            ReportType.COMPREHENSIVE: {
                'title': 'Reporte Integral de Verificación Arquitectónica',
                'sections': [
                    'executive_summary',
                    'project_overview',
                    'document_analysis',
                    'plan_analysis',
                    'compliance_check',
                    'ambiguity_analysis',
                    'question_analysis',
                    'recommendations',
                    'conclusions'
                ]
            },
            ReportType.COMPLIANCE: {
                'title': 'Reporte de Cumplimiento Normativo',
                'sections': [
                    'compliance_summary',
                    'regulatory_analysis',
                    'violations_detected',
                    'recommendations',
                    'action_plan'
                ]
            },
            ReportType.TECHNICAL: {
                'title': 'Reporte Técnico Detallado',
                'sections': [
                    'technical_overview',
                    'dimension_analysis',
                    'structural_analysis',
                    'accessibility_analysis',
                    'fire_safety_analysis',
                    'technical_recommendations'
                ]
            },
            ReportType.AMBIGUITY: {
                'title': 'Análisis de Ambigüedades y Resoluciones',
                'sections': [
                    'ambiguity_summary',
                    'ambiguities_detected',
                    'resolution_strategies',
                    'pending_issues',
                    'recommendations'
                ]
            },
            ReportType.QUESTION_ANALYSIS: {
                'title': 'Análisis de Preguntas Inteligentes',
                'sections': [
                    'question_summary',
                    'questions_generated',
                    'answer_analysis',
                    'knowledge_gaps',
                    'recommendations'
                ]
            },
            ReportType.EXECUTIVE_SUMMARY: {
                'title': 'Resumen Ejecutivo',
                'sections': [
                    'project_summary',
                    'key_findings',
                    'critical_issues',
                    'recommendations',
                    'next_steps'
                ]
            }
        }
    
    def generate_comprehensive_report(self, project_data: Dict[str, Any], 
                                    analysis_results: Dict[str, Any]) -> Report:
        """Genera un reporte integral completo"""
        try:
            self.logger.info("Generando reporte integral...")
            
            report_id = f"report_{project_data.get('id', 'unknown')}_{int(datetime.now().timestamp())}"
            
            # Crear secciones del reporte
            sections = []
            
            # 1. Resumen ejecutivo
            executive_summary = self._generate_executive_summary(project_data, analysis_results)
            sections.append(executive_summary)
            
            # 2. Visión general del proyecto
            project_overview = self._generate_project_overview(project_data)
            sections.append(project_overview)
            
            # 3. Análisis de documentos
            document_analysis = self._generate_document_analysis_section(analysis_results.get('document_analysis', {}))
            sections.append(document_analysis)
            
            # 4. Análisis de planos
            plan_analysis = self._generate_plan_analysis_section(analysis_results.get('plan_analysis', {}))
            sections.append(plan_analysis)
            
            # 5. Verificación de cumplimiento
            compliance_check = self._generate_compliance_section(analysis_results.get('compliance_check', {}))
            sections.append(compliance_check)
            
            # 6. Análisis de ambigüedades
            ambiguity_analysis = self._generate_ambiguity_analysis_section(analysis_results.get('ambiguities', []))
            sections.append(ambiguity_analysis)
            
            # 7. Análisis de preguntas
            question_analysis = self._generate_question_analysis_section(analysis_results.get('questions', []))
            sections.append(question_analysis)
            
            # 8. Recomendaciones
            recommendations = self._generate_recommendations_section(analysis_results)
            sections.append(recommendations)
            
            # 9. Conclusiones
            conclusions = self._generate_conclusions_section(analysis_results)
            sections.append(conclusions)
            
            # Crear reporte
            report = Report(
                report_id=report_id,
                project_id=project_data.get('id', 'unknown'),
                report_type=ReportType.COMPREHENSIVE,
                title=self.report_templates[ReportType.COMPREHENSIVE]['title'],
                sections=sections,
                metadata={
                    'project_name': project_data.get('name', ''),
                    'project_type': project_data.get('type', ''),
                    'generated_by': 'AI Verification System',
                    'version': '1.0'
                },
                generated_at=datetime.now().isoformat(),
                file_path=''
            )
            
            # Generar archivo PDF
            file_path = self._generate_pdf_report(report)
            report.file_path = file_path
            
            # Guardar en Neo4j
            self._save_report_to_graph(report)
            
            self.logger.info(f"Reporte integral generado: {file_path}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte integral: {e}")
            return None
    
    def _generate_executive_summary(self, project_data: Dict[str, Any], 
                                  analysis_results: Dict[str, Any]) -> ReportSection:
        """Genera el resumen ejecutivo"""
        try:
            # Calcular métricas clave
            overall_score = analysis_results.get('overall_score', 0.0)
            critical_issues = len(analysis_results.get('critical_issues', []))
            total_questions = len(analysis_results.get('questions', []))
            ambiguities = len(analysis_results.get('ambiguities', []))
            
            # Generar contenido con IA
            prompt = f"""
            Genera un resumen ejecutivo para un proyecto arquitectónico con los siguientes datos:
            
            Proyecto: {project_data.get('name', 'N/A')}
            Tipo: {project_data.get('type', 'N/A')}
            Puntuación general: {overall_score:.2f}/10
            Problemas críticos: {critical_issues}
            Preguntas generadas: {total_questions}
            Ambigüedades detectadas: {ambiguities}
            
            El resumen debe incluir:
            1. Estado general del proyecto
            2. Principales hallazgos
            3. Problemas críticos identificados
            4. Recomendaciones prioritarias
            5. Próximos pasos sugeridos
            
            Resumen ejecutivo:
            """
            
            response = self.ai_client.generate_response(prompt)
            content = response.content if response and response.success else "No se pudo generar el resumen ejecutivo."
            
            # Crear gráfico de resumen
            charts = self._create_executive_summary_charts(analysis_results)
            
            return ReportSection(
                section_id="executive_summary",
                title="Resumen Ejecutivo",
                content=content,
                subsections=[],
                charts=charts,
                tables=[],
                priority="HIGH"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando resumen ejecutivo: {e}")
            return ReportSection(
                section_id="executive_summary",
                title="Resumen Ejecutivo",
                content="Error generando resumen ejecutivo.",
                subsections=[],
                charts=[],
                tables=[],
                priority="HIGH"
            )
    
    def _generate_project_overview(self, project_data: Dict[str, Any]) -> ReportSection:
        """Genera la visión general del proyecto"""
        try:
            content = f"""
            ## Información General del Proyecto
            
            **Nombre del Proyecto:** {project_data.get('name', 'N/A')}
            **Tipo de Proyecto:** {project_data.get('type', 'N/A')}
            **Ubicación:** {project_data.get('location', 'N/A')}
            **Arquitecto:** {project_data.get('architect', 'N/A')}
            **Cliente:** {project_data.get('client', 'N/A')}
            **Estado:** {project_data.get('status', 'N/A')}
            **Fecha de Análisis:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
            
            ## Descripción del Proyecto
            
            Este proyecto ha sido analizado utilizando un sistema de verificación arquitectónica 
            basado en inteligencia artificial que evalúa el cumplimiento normativo, la calidad 
            técnica y la coherencia de la documentación.
            """
            
            return ReportSection(
                section_id="project_overview",
                title="Visión General del Proyecto",
                content=content,
                subsections=[],
                charts=[],
                tables=[],
                priority="MEDIUM"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando visión general: {e}")
            return ReportSection(
                section_id="project_overview",
                title="Visión General del Proyecto",
                content="Error generando visión general.",
                subsections=[],
                charts=[],
                priority="MEDIUM"
            )
    
    def _generate_document_analysis_section(self, document_analysis: Dict[str, Any]) -> ReportSection:
        """Genera la sección de análisis de documentos"""
        try:
            confidence_score = document_analysis.get('confidence_score', 0.0)
            extracted_data = document_analysis.get('extracted_data', {})
            contradictions = document_analysis.get('contradictions', [])
            
            content = f"""
            ## Análisis de Documentos
            
            **Puntuación de Confianza:** {confidence_score:.2f}/10
            
            ### Datos Extraídos
            """
            
            for key, value in extracted_data.items():
                if isinstance(value, str) and len(value) > 0:
                    content += f"\n- **{key.replace('_', ' ').title()}:** {value[:200]}{'...' if len(str(value)) > 200 else ''}"
            
            if contradictions:
                content += "\n\n### Contradicciones Detectadas\n"
                for i, contradiction in enumerate(contradictions, 1):
                    content += f"\n{i}. **{contradiction.get('title', 'Contradicción')}**\n"
                    content += f"   - Descripción: {contradiction.get('description', '')}\n"
                    content += f"   - Fuente 1: {contradiction.get('source1', '')}\n"
                    content += f"   - Fuente 2: {contradiction.get('source2', '')}\n"
            
            # Crear gráfico de confianza
            charts = [self._create_confidence_chart(confidence_score)]
            
            return ReportSection(
                section_id="document_analysis",
                title="Análisis de Documentos",
                content=content,
                subsections=[],
                charts=charts,
                tables=[],
                priority="HIGH"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando análisis de documentos: {e}")
            return ReportSection(
                section_id="document_analysis",
                title="Análisis de Documentos",
                content="Error generando análisis de documentos.",
                subsections=[],
                charts=[],
                priority="HIGH"
            )
    
    def _generate_plan_analysis_section(self, plan_analysis: Dict[str, Any]) -> ReportSection:
        """Genera la sección de análisis de planos"""
        try:
            elements = plan_analysis.get('elements', [])
            accessibility_issues = plan_analysis.get('accessibility_issues', [])
            fire_safety_issues = plan_analysis.get('fire_safety_issues', [])
            structural_issues = plan_analysis.get('structural_issues', [])
            
            content = f"""
            ## Análisis de Planos
            
            **Elementos Detectados:** {len(elements)}
            **Problemas de Accesibilidad:** {len(accessibility_issues)}
            **Problemas de Seguridad contra Incendios:** {len(fire_safety_issues)}
            **Problemas Estructurales:** {len(structural_issues)}
            
            ### Elementos Arquitectónicos Detectados
            """
            
            # Agrupar elementos por tipo
            element_types = {}
            for element in elements:
                element_type = element.get('type', 'unknown')
                if element_type not in element_types:
                    element_types[element_type] = []
                element_types[element_type].append(element)
            
            for element_type, elements_list in element_types.items():
                content += f"\n#### {element_type.replace('_', ' ').title()} ({len(elements_list)})\n"
                for element in elements_list[:5]:  # Mostrar solo los primeros 5
                    content += f"- {element.get('name', 'Elemento')} (Confianza: {element.get('confidence', 0):.2f})\n"
                if len(elements_list) > 5:
                    content += f"- ... y {len(elements_list) - 5} más\n"
            
            if accessibility_issues:
                content += "\n### Problemas de Accesibilidad\n"
                for issue in accessibility_issues:
                    content += f"- {issue}\n"
            
            if fire_safety_issues:
                content += "\n### Problemas de Seguridad contra Incendios\n"
                for issue in fire_safety_issues:
                    content += f"- {issue}\n"
            
            if structural_issues:
                content += "\n### Problemas Estructurales\n"
                for issue in structural_issues:
                    content += f"- {issue}\n"
            
            # Crear gráficos
            charts = [
                self._create_element_distribution_chart(element_types),
                self._create_issues_chart(accessibility_issues, fire_safety_issues, structural_issues)
            ]
            
            return ReportSection(
                section_id="plan_analysis",
                title="Análisis de Planos",
                content=content,
                subsections=[],
                charts=charts,
                tables=[],
                priority="HIGH"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando análisis de planos: {e}")
            return ReportSection(
                section_id="plan_analysis",
                title="Análisis de Planos",
                content="Error generando análisis de planos.",
                subsections=[],
                charts=[],
                priority="HIGH"
            )
    
    def _generate_compliance_section(self, compliance_check: Dict[str, Any]) -> ReportSection:
        """Genera la sección de verificación de cumplimiento"""
        try:
            dimension_compliance = compliance_check.get('dimension_compliance', 0.0)
            accessibility_compliance = compliance_check.get('accessibility_compliance', 0.0)
            fire_safety_compliance = compliance_check.get('fire_safety_compliance', 0.0)
            structural_compliance = compliance_check.get('structural_compliance', 0.0)
            
            content = f"""
            ## Verificación de Cumplimiento Normativo
            
            **Cumplimiento de Dimensiones:** {dimension_compliance:.1f}%
            **Cumplimiento de Accesibilidad:** {accessibility_compliance:.1f}%
            **Cumplimiento de Seguridad contra Incendios:** {fire_safety_compliance:.1f}%
            **Cumplimiento Estructural:** {structural_compliance:.1f}%
            
            ### Análisis Detallado
            """
            
            # Analizar cada área de cumplimiento
            compliance_areas = [
                ("Dimensiones", dimension_compliance, "Verificación de medidas y dimensiones según normativa"),
                ("Accesibilidad", accessibility_compliance, "Cumplimiento de accesibilidad universal"),
                ("Seguridad contra Incendios", fire_safety_compliance, "Medidas de seguridad contra incendios"),
                ("Estructural", structural_compliance, "Aspectos estructurales y de resistencia")
            ]
            
            for area_name, score, description in compliance_areas:
                content += f"\n#### {area_name}\n"
                content += f"**Puntuación:** {score:.1f}%\n"
                content += f"**Descripción:** {description}\n"
                
                if score >= 80:
                    content += "✅ **Estado:** Cumplimiento adecuado\n"
                elif score >= 60:
                    content += "⚠️ **Estado:** Cumplimiento parcial\n"
                else:
                    content += "❌ **Estado:** Incumplimiento significativo\n"
            
            # Crear gráfico de cumplimiento
            charts = [self._create_compliance_chart(compliance_areas)]
            
            return ReportSection(
                section_id="compliance_check",
                title="Verificación de Cumplimiento",
                content=content,
                subsections=[],
                charts=charts,
                tables=[],
                priority="HIGH"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando verificación de cumplimiento: {e}")
            return ReportSection(
                section_id="compliance_check",
                title="Verificación de Cumplimiento",
                content="Error generando verificación de cumplimiento.",
                subsections=[],
                charts=[],
                priority="HIGH"
            )
    
    def _generate_ambiguity_analysis_section(self, ambiguities: List[Dict[str, Any]]) -> ReportSection:
        """Genera la sección de análisis de ambigüedades"""
        try:
            content = f"""
            ## Análisis de Ambigüedades
            
            **Total de Ambigüedades Detectadas:** {len(ambiguities)}
            """
            
            if ambiguities:
                # Agrupar por severidad
                high_severity = [a for a in ambiguities if a.get('severity') == 'HIGH']
                medium_severity = [a for a in ambiguities if a.get('severity') == 'MEDIUM']
                low_severity = [a for a in ambiguities if a.get('severity') == 'LOW']
                
                content += f"""
                - **Alta Severidad:** {len(high_severity)}
                - **Media Severidad:** {len(medium_severity)}
                - **Baja Severidad:** {len(low_severity)}
                """
                
                content += "\n### Ambigüedades por Severidad\n"
                
                for severity, ambiguities_list in [("Alta", high_severity), ("Media", medium_severity), ("Baja", low_severity)]:
                    if ambiguities_list:
                        content += f"\n#### {severity} Severidad\n"
                        for i, ambiguity in enumerate(ambiguities_list, 1):
                            content += f"{i}. **{ambiguity.get('title', 'Ambigüedad')}**\n"
                            content += f"   - Tipo: {ambiguity.get('type', 'N/A')}\n"
                            content += f"   - Descripción: {ambiguity.get('description', '')}\n"
                            content += f"   - Confianza: {ambiguity.get('confidence', 0):.2f}\n"
            else:
                content += "\n✅ **No se detectaron ambigüedades significativas**\n"
            
            # Crear gráfico de ambigüedades
            charts = [self._create_ambiguity_chart(ambiguities)]
            
            return ReportSection(
                section_id="ambiguity_analysis",
                title="Análisis de Ambigüedades",
                content=content,
                subsections=[],
                charts=charts,
                tables=[],
                priority="MEDIUM"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando análisis de ambigüedades: {e}")
            return ReportSection(
                section_id="ambiguity_analysis",
                title="Análisis de Ambigüedades",
                content="Error generando análisis de ambigüedades.",
                subsections=[],
                charts=[],
                priority="MEDIUM"
            )
    
    def _generate_question_analysis_section(self, questions: List[Dict[str, Any]]) -> ReportSection:
        """Genera la sección de análisis de preguntas"""
        try:
            content = f"""
            ## Análisis de Preguntas Inteligentes
            
            **Total de Preguntas Generadas:** {len(questions)}
            """
            
            if questions:
                # Agrupar por tipo
                question_types = {}
                for question in questions:
                    question_type = question.get('type', 'unknown')
                    if question_type not in question_types:
                        question_types[question_type] = []
                    question_types[question_type].append(question)
                
                content += "\n### Distribución por Tipo de Pregunta\n"
                for question_type, questions_list in question_types.items():
                    content += f"- **{question_type.replace('_', ' ').title()}:** {len(questions_list)}\n"
                
                content += "\n### Preguntas Generadas\n"
                for i, question in enumerate(questions[:10], 1):  # Mostrar solo las primeras 10
                    content += f"\n{i}. **{question.get('text', 'Pregunta')}**\n"
                    content += f"   - Tipo: {question.get('type', 'N/A')}\n"
                    content += f"   - Prioridad: {question.get('priority', 'N/A')}\n"
                    content += f"   - Estado: {question.get('status', 'N/A')}\n"
                
                if len(questions) > 10:
                    content += f"\n... y {len(questions) - 10} preguntas más\n"
            else:
                content += "\n✅ **No se generaron preguntas específicas**\n"
            
            # Crear gráfico de preguntas
            charts = [self._create_question_chart(questions)]
            
            return ReportSection(
                section_id="question_analysis",
                title="Análisis de Preguntas",
                content=content,
                subsections=[],
                charts=charts,
                tables=[],
                priority="MEDIUM"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando análisis de preguntas: {e}")
            return ReportSection(
                section_id="question_analysis",
                title="Análisis de Preguntas",
                content="Error generando análisis de preguntas.",
                subsections=[],
                charts=[],
                priority="MEDIUM"
            )
    
    def _generate_recommendations_section(self, analysis_results: Dict[str, Any]) -> ReportSection:
        """Genera la sección de recomendaciones"""
        try:
            # Generar recomendaciones con IA
            prompt = f"""
            Basándote en el análisis de verificación arquitectónica, genera recomendaciones 
            específicas y accionables para mejorar el proyecto:
            
            Puntuación general: {analysis_results.get('overall_score', 0):.2f}/10
            Problemas críticos: {len(analysis_results.get('critical_issues', []))}
            Ambigüedades: {len(analysis_results.get('ambiguities', []))}
            Preguntas generadas: {len(analysis_results.get('questions', []))}
            
            Genera recomendaciones organizadas por:
            1. Prioridad Alta (problemas críticos)
            2. Prioridad Media (mejoras importantes)
            3. Prioridad Baja (optimizaciones)
            
            Recomendaciones:
            """
            
            response = self.ai_client.generate_response(prompt)
            content = response.content if response and response.success else "No se pudieron generar recomendaciones específicas."
            
            return ReportSection(
                section_id="recommendations",
                title="Recomendaciones",
                content=content,
                subsections=[],
                charts=[],
                tables=[],
                priority="HIGH"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando recomendaciones: {e}")
            return ReportSection(
                section_id="recommendations",
                title="Recomendaciones",
                content="Error generando recomendaciones.",
                subsections=[],
                charts=[],
                priority="HIGH"
            )
    
    def _generate_conclusions_section(self, analysis_results: Dict[str, Any]) -> ReportSection:
        """Genera la sección de conclusiones"""
        try:
            overall_score = analysis_results.get('overall_score', 0.0)
            critical_issues = len(analysis_results.get('critical_issues', []))
            
            content = f"""
            ## Conclusiones
            
            ### Resumen del Análisis
            
            El proyecto ha sido evaluado utilizando un sistema de verificación arquitectónica 
            basado en inteligencia artificial. Los resultados indican:
            
            - **Puntuación General:** {overall_score:.2f}/10
            - **Problemas Críticos Identificados:** {critical_issues}
            - **Estado del Proyecto:** {'Aprobado' if overall_score >= 7.0 else 'Requiere Revisión'}
            
            ### Próximos Pasos Recomendados
            
            1. **Revisar problemas críticos** identificados en el análisis
            2. **Resolver ambigüedades** pendientes
            3. **Implementar recomendaciones** de mejora
            4. **Verificar cumplimiento** normativo completo
            5. **Documentar cambios** realizados
            
            ### Contacto y Soporte
            
            Para consultas adicionales o aclaraciones sobre este análisis, 
            contacte con el equipo técnico especializado.
            """
            
            return ReportSection(
                section_id="conclusions",
                title="Conclusiones",
                content=content,
                subsections=[],
                charts=[],
                tables=[],
                priority="HIGH"
            )
            
        except Exception as e:
            self.logger.error(f"Error generando conclusiones: {e}")
            return ReportSection(
                section_id="conclusions",
                title="Conclusiones",
                content="Error generando conclusiones.",
                subsections=[],
                charts=[],
                priority="HIGH"
            )
    
    def _create_executive_summary_charts(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crea gráficos para el resumen ejecutivo"""
        try:
            charts = []
            
            # Gráfico de puntuación general
            overall_score = analysis_results.get('overall_score', 0.0)
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Crear gráfico de barras horizontales
            categories = ['Puntuación General']
            scores = [overall_score]
            colors = ['green' if overall_score >= 7 else 'orange' if overall_score >= 5 else 'red']
            
            bars = ax.barh(categories, scores, color=colors)
            ax.set_xlim(0, 10)
            ax.set_xlabel('Puntuación (0-10)')
            ax.set_title('Puntuación General del Proyecto')
            
            # Añadir valor en la barra
            for bar, score in zip(bars, scores):
                ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                       f'{score:.2f}', ha='left', va='center')
            
            charts.append({
                'type': 'executive_score',
                'figure': fig,
                'title': 'Puntuación General'
            })
            
            return charts
            
        except Exception as e:
            self.logger.error(f"Error creando gráficos ejecutivos: {e}")
            return []
    
    def _create_confidence_chart(self, confidence_score: float) -> Dict[str, Any]:
        """Crea gráfico de confianza"""
        try:
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # Crear gráfico circular
            sizes = [confidence_score, 10 - confidence_score]
            labels = ['Confianza', 'Incertidumbre']
            colors = ['lightgreen', 'lightcoral']
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            
            ax.set_title(f'Confianza del Análisis: {confidence_score:.2f}/10')
            
            return {
                'type': 'confidence_pie',
                'figure': fig,
                'title': 'Confianza del Análisis'
            }
            
        except Exception as e:
            self.logger.error(f"Error creando gráfico de confianza: {e}")
            return {}
    
    def _create_element_distribution_chart(self, element_types: Dict[str, List]) -> Dict[str, Any]:
        """Crea gráfico de distribución de elementos"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            types = list(element_types.keys())
            counts = [len(elements) for elements in element_types.values()]
            
            bars = ax.bar(types, counts, color='skyblue', edgecolor='navy')
            ax.set_xlabel('Tipo de Elemento')
            ax.set_ylabel('Cantidad')
            ax.set_title('Distribución de Elementos Arquitectónicos')
            ax.tick_params(axis='x', rotation=45)
            
            # Añadir valores en las barras
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                       str(count), ha='center', va='bottom')
            
            return {
                'type': 'element_distribution',
                'figure': fig,
                'title': 'Distribución de Elementos'
            }
            
        except Exception as e:
            self.logger.error(f"Error creando gráfico de distribución: {e}")
            return {}
    
    def _create_issues_chart(self, accessibility_issues: List, fire_safety_issues: List, 
                           structural_issues: List) -> Dict[str, Any]:
        """Crea gráfico de problemas detectados"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            categories = ['Accesibilidad', 'Seguridad Incendios', 'Estructural']
            counts = [len(accessibility_issues), len(fire_safety_issues), len(structural_issues)]
            colors = ['orange', 'red', 'purple']
            
            bars = ax.bar(categories, counts, color=colors, edgecolor='black')
            ax.set_ylabel('Número de Problemas')
            ax.set_title('Problemas Detectados por Categoría')
            
            # Añadir valores en las barras
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                       str(count), ha='center', va='bottom')
            
            return {
                'type': 'issues_bar',
                'figure': fig,
                'title': 'Problemas Detectados'
            }
            
        except Exception as e:
            self.logger.error(f"Error creando gráfico de problemas: {e}")
            return {}
    
    def _create_compliance_chart(self, compliance_areas: List[Tuple[str, float, str]]) -> Dict[str, Any]:
        """Crea gráfico de cumplimiento"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            areas = [area[0] for area in compliance_areas]
            scores = [area[1] for area in compliance_areas]
            colors = ['green' if score >= 80 else 'orange' if score >= 60 else 'red' 
                     for score in scores]
            
            bars = ax.bar(areas, scores, color=colors, edgecolor='black')
            ax.set_ylabel('Porcentaje de Cumplimiento')
            ax.set_title('Cumplimiento Normativo por Área')
            ax.set_ylim(0, 100)
            ax.tick_params(axis='x', rotation=45)
            
            # Añadir valores en las barras
            for bar, score in zip(bars, scores):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                       f'{score:.1f}%', ha='center', va='bottom')
            
            return {
                'type': 'compliance_bar',
                'figure': fig,
                'title': 'Cumplimiento Normativo'
            }
            
        except Exception as e:
            self.logger.error(f"Error creando gráfico de cumplimiento: {e}")
            return {}
    
    def _create_ambiguity_chart(self, ambiguities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea gráfico de ambigüedades"""
        try:
            if not ambiguities:
                return {}
            
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Agrupar por severidad
            severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            for ambiguity in ambiguities:
                severity = ambiguity.get('severity', 'LOW')
                severity_counts[severity] += 1
            
            severities = list(severity_counts.keys())
            counts = list(severity_counts.values())
            colors = ['red', 'orange', 'yellow']
            
            bars = ax.bar(severities, counts, color=colors, edgecolor='black')
            ax.set_ylabel('Número de Ambigüedades')
            ax.set_title('Ambigüedades por Severidad')
            
            # Añadir valores en las barras
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                       str(count), ha='center', va='bottom')
            
            return {
                'type': 'ambiguity_bar',
                'figure': fig,
                'title': 'Ambigüedades por Severidad'
            }
            
        except Exception as e:
            self.logger.error(f"Error creando gráfico de ambigüedades: {e}")
            return {}
    
    def _create_question_chart(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea gráfico de preguntas"""
        try:
            if not questions:
                return {}
            
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Agrupar por tipo
            type_counts = {}
            for question in questions:
                question_type = question.get('type', 'unknown')
                type_counts[question_type] = type_counts.get(question_type, 0) + 1
            
            types = list(type_counts.keys())
            counts = list(type_counts.values())
            
            bars = ax.bar(types, counts, color='lightblue', edgecolor='navy')
            ax.set_ylabel('Número de Preguntas')
            ax.set_title('Preguntas Generadas por Tipo')
            ax.tick_params(axis='x', rotation=45)
            
            # Añadir valores en las barras
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                       str(count), ha='center', va='bottom')
            
            return {
                'type': 'question_bar',
                'figure': fig,
                'title': 'Preguntas por Tipo'
            }
            
        except Exception as e:
            self.logger.error(f"Error creando gráfico de preguntas: {e}")
            return {}
    
    def _generate_pdf_report(self, report: Report) -> str:
        """Genera el archivo PDF del reporte"""
        try:
            # Crear directorio de reportes si no existe
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Nombre del archivo
            filename = f"{report.report_id}.pdf"
            filepath = os.path.join(reports_dir, filename)
            
            # Crear PDF
            with PdfPages(filepath) as pdf:
                # Página de portada
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.axis('off')
                ax.text(0.5, 0.8, report.title, ha='center', va='center', 
                       fontsize=24, fontweight='bold')
                ax.text(0.5, 0.7, f"Proyecto: {report.metadata.get('project_name', 'N/A')}", 
                       ha='center', va='center', fontsize=16)
                ax.text(0.5, 0.6, f"Generado: {report.generated_at}", 
                       ha='center', va='center', fontsize=12)
                ax.text(0.5, 0.5, f"Versión: {report.metadata.get('version', '1.0')}", 
                       ha='center', va='center', fontsize=12)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                
                # Páginas de contenido
                for section in report.sections:
                    # Crear página de sección
                    fig, ax = plt.subplots(figsize=(8.5, 11))
                    ax.axis('off')
                    
                    # Título de sección
                    ax.text(0.1, 0.95, section.title, ha='left', va='top', 
                           fontsize=18, fontweight='bold')
                    
                    # Contenido de sección (simplificado para PDF)
                    content_lines = section.content.split('\n')
                    y_position = 0.9
                    
                    for line in content_lines[:30]:  # Limitar líneas para PDF
                        if line.strip():
                            ax.text(0.1, y_position, line, ha='left', va='top', 
                                   fontsize=10, wrap=True)
                            y_position -= 0.03
                    
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)
                    
                    # Gráficos de la sección
                    for chart in section.charts:
                        if chart and 'figure' in chart:
                            pdf.savefig(chart['figure'], bbox_inches='tight')
                            plt.close(chart['figure'])
            
            self.logger.info(f"Reporte PDF generado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error generando PDF: {e}")
            return ""
    
    def _save_report_to_graph(self, report: Report):
        """Guarda el reporte en el grafo de conocimiento"""
        try:
            report_data = {
                'id': report.report_id,
                'name': report.title,
                'type': 'report',
                'file_path': report.file_path,
                'generated_at': report.generated_at,
                'metadata': json.dumps(report.metadata)
            }
            
            # Crear nodo de documento en Neo4j
            self.neo4j_manager.create_document_node(report_data, report.project_id)
            
        except Exception as e:
            self.logger.error(f"Error guardando reporte en grafo: {e}")
    
    def generate_specific_report(self, report_type: ReportType, project_data: Dict[str, Any], 
                               analysis_results: Dict[str, Any]) -> Report:
        """Genera un reporte específico según el tipo"""
        try:
            if report_type == ReportType.COMPREHENSIVE:
                return self.generate_comprehensive_report(project_data, analysis_results)
            else:
                # Implementar otros tipos de reportes específicos
                self.logger.warning(f"Tipo de reporte {report_type} no implementado completamente")
                return self.generate_comprehensive_report(project_data, analysis_results)
                
        except Exception as e:
            self.logger.error(f"Error generando reporte específico: {e}")
            return None
