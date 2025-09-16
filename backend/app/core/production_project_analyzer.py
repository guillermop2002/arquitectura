"""
Analizador de proyectos para producción.
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ProductionProjectAnalyzer:
    """Analizador de proyectos optimizado para producción."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializar el analizador de producción.
        
        Args:
            config: Configuración del analizador
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.ProductionProjectAnalyzer")
    
    def analyze_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizar un proyecto de construcción.
        
        Args:
            project_data: Datos del proyecto
            
        Returns:
            Resultado del análisis
        """
        try:
            self.logger.info("Iniciando análisis de proyecto de producción")
            
            # Análisis básico del proyecto
            analysis_result = {
                "project_id": project_data.get("project_id", "unknown"),
                "analysis_type": "production",
                "status": "completed",
                "timestamp": self._get_timestamp(),
                "findings": [],
                "recommendations": [],
                "compliance_status": "pending"
            }
            
            # Verificar datos del proyecto
            if not project_data:
                analysis_result["status"] = "error"
                analysis_result["error"] = "No se proporcionaron datos del proyecto"
                return analysis_result
            
            # Análisis de elementos básicos
            self._analyze_basic_elements(project_data, analysis_result)
            
            # Análisis de cumplimiento normativo
            self._analyze_compliance(project_data, analysis_result)
            
            # Generar recomendaciones
            self._generate_recommendations(analysis_result)
            
            self.logger.info(f"Análisis completado para proyecto {analysis_result['project_id']}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error en análisis de proyecto: {e}")
            return {
                "project_id": project_data.get("project_id", "unknown"),
                "status": "error",
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def _analyze_basic_elements(self, project_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Analizar elementos básicos del proyecto."""
        try:
            # Verificar presencia de elementos clave
            required_elements = [
                "project_type", "building_type", "location", "area"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in project_data or not project_data[element]:
                    missing_elements.append(element)
            
            if missing_elements:
                result["findings"].append({
                    "type": "missing_data",
                    "severity": "warning",
                    "message": f"Elementos faltantes: {', '.join(missing_elements)}"
                })
            else:
                result["findings"].append({
                    "type": "data_completeness",
                    "severity": "info",
                    "message": "Todos los elementos básicos están presentes"
                })
            
            # Análisis de área
            if "area" in project_data:
                area = project_data["area"]
                if isinstance(area, (int, float)) and area > 0:
                    if area < 50:
                        result["findings"].append({
                            "type": "area_analysis",
                            "severity": "info",
                            "message": "Proyecto de área pequeña"
                        })
                    elif area > 1000:
                        result["findings"].append({
                            "type": "area_analysis",
                            "severity": "warning",
                            "message": "Proyecto de gran envergadura - requiere análisis detallado"
                        })
            
        except Exception as e:
            self.logger.error(f"Error analizando elementos básicos: {e}")
    
    def _analyze_compliance(self, project_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Analizar cumplimiento normativo."""
        try:
            # Verificar tipo de edificio
            building_type = project_data.get("building_type", "").lower()
            
            if "residencial" in building_type:
                result["findings"].append({
                    "type": "building_type",
                    "severity": "info",
                    "message": "Proyecto residencial - aplican normativas DB-HR y DB-HE"
                })
            elif "comercial" in building_type:
                result["findings"].append({
                    "type": "building_type",
                    "severity": "info",
                    "message": "Proyecto comercial - aplican normativas DB-SU y DB-SI"
                })
            elif "industrial" in building_type:
                result["findings"].append({
                    "type": "building_type",
                    "severity": "warning",
                    "message": "Proyecto industrial - requiere análisis especializado"
                })
            
            # Verificar si es edificio existente o nuevo
            is_existing = project_data.get("is_existing_building", False)
            if is_existing:
                result["findings"].append({
                    "type": "building_status",
                    "severity": "info",
                    "message": "Edificio existente - aplican normativas de rehabilitación"
                })
            else:
                result["findings"].append({
                    "type": "building_status",
                    "severity": "info",
                    "message": "Edificio nuevo - aplican normativas de nueva construcción"
                })
            
            # Estado de cumplimiento
            result["compliance_status"] = "in_progress"
            
        except Exception as e:
            self.logger.error(f"Error analizando cumplimiento: {e}")
    
    def _generate_recommendations(self, result: Dict[str, Any]) -> None:
        """Generar recomendaciones basadas en el análisis."""
        try:
            recommendations = []
            
            # Recomendaciones basadas en hallazgos
            for finding in result["findings"]:
                if finding["type"] == "missing_data":
                    recommendations.append({
                        "priority": "high",
                        "action": "Completar información faltante del proyecto",
                        "description": "Es necesario proporcionar todos los datos requeridos"
                    })
                elif finding["type"] == "area_analysis" and "gran envergadura" in finding["message"]:
                    recommendations.append({
                        "priority": "medium",
                        "action": "Realizar análisis estructural detallado",
                        "description": "Proyectos de gran envergadura requieren análisis especializado"
                    })
            
            # Recomendaciones generales
            recommendations.append({
                "priority": "low",
                "action": "Verificar documentación técnica",
                "description": "Asegurar que toda la documentación esté actualizada"
            })
            
            result["recommendations"] = recommendations
            
        except Exception as e:
            self.logger.error(f"Error generando recomendaciones: {e}")
    
    def _get_timestamp(self) -> str:
        """Obtener timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener resumen del análisis.
        
        Args:
            analysis_result: Resultado del análisis
            
        Returns:
            Resumen del análisis
        """
        try:
            total_findings = len(analysis_result.get("findings", []))
            total_recommendations = len(analysis_result.get("recommendations", []))
            
            # Contar hallazgos por severidad
            severity_counts = {"info": 0, "warning": 0, "error": 0}
            for finding in analysis_result.get("findings", []):
                severity = finding.get("severity", "info")
                severity_counts[severity] += 1
            
            return {
                "project_id": analysis_result.get("project_id", "unknown"),
                "status": analysis_result.get("status", "unknown"),
                "total_findings": total_findings,
                "total_recommendations": total_recommendations,
                "severity_breakdown": severity_counts,
                "compliance_status": analysis_result.get("compliance_status", "unknown"),
                "timestamp": analysis_result.get("timestamp", "")
            }
            
        except Exception as e:
            self.logger.error(f"Error generando resumen: {e}")
            return {"error": str(e)}
