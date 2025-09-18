"""
Verificador de cumplimiento específico para normativa de Madrid.
Verifica el cumplimiento de la normativa aplicada según el tipo de edificio y plantas.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .madrid_normative_applicator import NormativeApplication, NormativeDocument
from .ai_client import AIClient

logger = logging.getLogger(__name__)

@dataclass
class ComplianceIssue:
    """Problema de cumplimiento detectado."""
    id: str
    title: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str
    document_reference: str
    floor: str
    current_value: Optional[str]
    required_value: Optional[str]
    recommendation: str
    page_reference: Optional[str]
    detected_at: datetime

@dataclass
class ComplianceResult:
    """Resultado de verificación de cumplimiento."""
    project_id: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    compliance_score: float
    issues: List[ComplianceIssue]
    floor_compliance: Dict[str, Dict[str, Any]]
    document_compliance: Dict[str, Dict[str, Any]]
    summary: Dict[str, Any]

class MadridComplianceChecker:
    """Verificador de cumplimiento específico para Madrid."""
    
    def __init__(self, ai_client: AIClient = None):
        """
        Inicializar el verificador de cumplimiento.
        
        Args:
            ai_client: Cliente de IA para análisis de documentos
        """
        self.ai_client = ai_client or AIClient()
        
        # Prompts específicos para cada tipo de verificación
        self.compliance_prompts = self._initialize_compliance_prompts()
        
        logger.info("MadridComplianceChecker initialized")
    
    def _initialize_compliance_prompts(self) -> Dict[str, str]:
        """Inicializar prompts específicos para verificación de cumplimiento."""
        return {
            "energy": """
            Eres un experto en eficiencia energética especializado en DB-HE y normativa de Madrid.
            
            Verifica el cumplimiento de los requisitos energéticos en el siguiente proyecto:
            
            DATOS DEL PROYECTO:
            {project_data}
            
            TEXTO DEL PROYECTO:
            {project_text}
            
            NORMATIVA APLICABLE:
            {normative_text}
            
            PLANTA: {floor}
            
            VERIFICACIONES ESPECÍFICAS:
            1. Limitación de demanda energética
            2. Eficiencia energética de instalaciones
            3. Aislamiento térmico
            4. Sistemas de climatización
            5. Iluminación eficiente
            
            Responde ÚNICAMENTE en formato JSON:
            {{
                "energy_issues": [
                    {{
                        "id": "string",
                        "title": "string",
                        "description": "string",
                        "severity": "CRITICAL/HIGH/MEDIUM/LOW",
                        "current_value": "string",
                        "required_value": "string",
                        "recommendation": "string",
                        "page_reference": "string"
                    }}
                ],
                "compliance_score": "number",
                "verification_notes": ["string"]
            }}
            """,
            
            "fire_safety": """
            Eres un experto en seguridad contra incendios especializado en DB-SI y normativa de Madrid.
            
            Verifica el cumplimiento de los requisitos de seguridad contra incendios:
            
            DATOS DEL PROYECTO:
            {project_data}
            
            TEXTO DEL PROYECTO:
            {project_text}
            
            NORMATIVA APLICABLE:
            {normative_text}
            
            PLANTA: {floor}
            
            VERIFICACIONES ESPECÍFICAS:
            1. Clasificación de resistencia al fuego
            2. Medios de evacuación
            3. Compartimentación
            4. Extintores y sistemas de protección
            5. Señalización de seguridad
            
            Responde ÚNICAMENTE en formato JSON:
            {{
                "fire_safety_issues": [
                    {{
                        "id": "string",
                        "title": "string",
                        "description": "string",
                        "severity": "CRITICAL/HIGH/MEDIUM/LOW",
                        "current_value": "string",
                        "required_value": "string",
                        "recommendation": "string",
                        "page_reference": "string"
                    }}
                ],
                "compliance_score": "number",
                "verification_notes": ["string"]
            }}
            """,
            
            "accessibility": """
            Eres un experto en accesibilidad especializado en DB-SU y normativa de Madrid.
            
            Verifica el cumplimiento de los requisitos de accesibilidad:
            
            DATOS DEL PROYECTO:
            {project_data}
            
            TEXTO DEL PROYECTO:
            {project_text}
            
            NORMATIVA APLICABLE:
            {normative_text}
            
            PLANTA: {floor}
            
            VERIFICACIONES ESPECÍFICAS:
            1. Accesibilidad universal
            2. Rampas y escaleras accesibles
            3. Anchuras mínimas
            4. Altura de pasamanos
            5. Superficies antideslizantes
            
            Responde ÚNICAMENTE en formato JSON:
            {{
                "accessibility_issues": [
                    {{
                        "id": "string",
                        "title": "string",
                        "description": "string",
                        "severity": "CRITICAL/HIGH/MEDIUM/LOW",
                        "current_value": "string",
                        "required_value": "string",
                        "recommendation": "string",
                        "page_reference": "string"
                    }}
                ],
                "compliance_score": "number",
                "verification_notes": ["string"]
            }}
            """,
            
            "residential": """
            Eres un experto en normativa residencial especializado en PGOUM de Madrid.
            
            Verifica el cumplimiento de los requisitos residenciales:
            
            DATOS DEL PROYECTO:
            {project_data}
            
            TEXTO DEL PROYECTO:
            {project_text}
            
            NORMATIVA APLICABLE:
            {normative_text}
            
            PLANTA: {floor}
            
            VERIFICACIONES ESPECÍFICAS:
            1. Superficie mínima de viviendas
            2. Iluminación natural
            3. Ventilación
            4. Distribución de espacios
            5. Instalaciones básicas
            
            Responde ÚNICAMENTE en formato JSON:
            {{
                "residential_issues": [
                    {{
                        "id": "string",
                        "title": "string",
                        "description": "string",
                        "severity": "CRITICAL/HIGH/MEDIUM/LOW",
                        "current_value": "string",
                        "required_value": "string",
                        "recommendation": "string",
                        "page_reference": "string"
                    }}
                ],
                "compliance_score": "number",
                "verification_notes": ["string"]
            }}
            """,
            
            "parking": """
            Eres un experto en normativa de aparcamientos especializado en PGOUM de Madrid.
            
            Verifica el cumplimiento de los requisitos de aparcamiento:
            
            DATOS DEL PROYECTO:
            {project_data}
            
            TEXTO DEL PROYECTO:
            {project_text}
            
            NORMATIVA APLICABLE:
            {normative_text}
            
            PLANTA: {floor}
            
            VERIFICACIONES ESPECÍFICAS:
            1. Dimensiones de plazas
            2. Accesos y circulaciones
            3. Ventilación
            4. Iluminación
            5. Señalización
            
            Responde ÚNICAMENTE en formato JSON:
            {{
                "parking_issues": [
                    {{
                        "id": "string",
                        "title": "string",
                        "description": "string",
                        "severity": "CRITICAL/HIGH/MEDIUM/LOW",
                        "current_value": "string",
                        "required_value": "string",
                        "recommendation": "string",
                        "page_reference": "string"
                    }}
                ],
                "compliance_score": "number",
                "verification_notes": ["string"]
            }}
            """
        }
    
    async def check_compliance(self, 
                             normative_application: NormativeApplication, 
                             project_data: Dict[str, Any], 
                             project_text: str) -> ComplianceResult:
        """
        Verificar cumplimiento de la normativa aplicada.
        
        Args:
            normative_application: Aplicación de normativa específica
            project_data: Datos del proyecto
            project_text: Texto extraído de los documentos
            
        Returns:
            Resultado de verificación de cumplimiento
        """
        try:
            logger.info(f"Verificando cumplimiento para proyecto {normative_application.project_id}")
            
            all_issues = []
            floor_compliance = {}
            document_compliance = {}
            
            # Verificar cumplimiento por planta
            for floor, documents in normative_application.floor_assignments.items():
                floor_issues = []
                floor_scores = []
                
                for doc_name in documents:
                    doc_issues, doc_score = await self._check_document_compliance(
                        doc_name, floor, project_data, project_text, normative_application
                    )
                    floor_issues.extend(doc_issues)
                    floor_scores.append(doc_score)
                    
                    # Actualizar cumplimiento por documento
                    if doc_name not in document_compliance:
                        document_compliance[doc_name] = {
                            "total_checks": 0,
                            "passed_checks": 0,
                            "failed_checks": 0,
                            "issues": []
                        }
                    
                    document_compliance[doc_name]["issues"].extend(doc_issues)
                    document_compliance[doc_name]["total_checks"] += len(doc_issues)
                    document_compliance[doc_name]["failed_checks"] += len([i for i in doc_issues if i.severity != "low"])
                
                # Calcular cumplimiento de la planta
                floor_score = sum(floor_scores) / len(floor_scores) if floor_scores else 0
                floor_compliance[floor] = {
                    "score": floor_score,
                    "total_issues": len(floor_issues),
                    "critical_issues": len([i for i in floor_issues if i.severity == "critical"]),
                    "high_issues": len([i for i in floor_issues if i.severity == "high"]),
                    "medium_issues": len([i for i in floor_issues if i.severity == "medium"]),
                    "low_issues": len([i for i in floor_issues if i.severity == "low"]),
                    "documents": documents
                }
                
                all_issues.extend(floor_issues)
            
            # Calcular estadísticas generales
            total_checks = len(all_issues)
            passed_checks = len([i for i in all_issues if i.severity == "low"])
            failed_checks = total_checks - passed_checks
            
            critical_issues = len([i for i in all_issues if i.severity == "critical"])
            high_issues = len([i for i in all_issues if i.severity == "high"])
            medium_issues = len([i for i in all_issues if i.severity == "medium"])
            low_issues = len([i for i in all_issues if i.severity == "low"])
            
            # Calcular puntuación de cumplimiento
            if total_checks > 0:
                compliance_score = (passed_checks / total_checks) * 100
            else:
                compliance_score = 100.0
            
            # Crear resumen
            summary = {
                "project_id": normative_application.project_id,
                "primary_use": normative_application.primary_use,
                "is_existing_building": normative_application.is_existing_building,
                "total_documents": len(normative_application.applicable_documents),
                "total_floors": len(normative_application.floor_assignments),
                "overall_score": compliance_score,
                "status": self._determine_compliance_status(compliance_score, critical_issues)
            }
            
            # Crear resultado
            result = ComplianceResult(
                project_id=normative_application.project_id,
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                critical_issues=critical_issues,
                high_issues=high_issues,
                medium_issues=medium_issues,
                low_issues=low_issues,
                compliance_score=compliance_score,
                issues=all_issues,
                floor_compliance=floor_compliance,
                document_compliance=document_compliance,
                summary=summary
            )
            
            logger.info(f"Verificación completada: {compliance_score:.1f}% cumplimiento, "
                       f"{critical_issues} problemas críticos")
            
            return result
            
        except Exception as e:
            logger.error(f"Error verificando cumplimiento: {e}")
            raise
    
    async def _check_document_compliance(self, 
                                       doc_name: str, 
                                       floor: str, 
                                       project_data: Dict[str, Any], 
                                       project_text: str, 
                                       normative_application: NormativeApplication) -> Tuple[List[ComplianceIssue], float]:
        """Verificar cumplimiento de un documento específico en una planta."""
        try:
            # Determinar categoría de verificación
            category = self._determine_verification_category(doc_name)
            
            if category not in self.compliance_prompts:
                logger.warning(f"No hay prompt para categoría {category}")
                return [], 0.0
            
            # Obtener texto normativo (simulado - en producción se extraería del PDF)
            normative_text = self._get_normative_text(doc_name)
            
            # Preparar prompt
            prompt = self.compliance_prompts[category].format(
                project_data=json.dumps(project_data, indent=2),
                project_text=project_text[:2000],  # Limitar tamaño
                normative_text=normative_text,
                floor=floor
            )
            
            # Llamar a IA
            response = await self.ai_client.generate_response(prompt)
            
            # Parsear respuesta
            try:
                result = json.loads(response)
                issues = self._parse_compliance_issues(result, doc_name, floor, category)
                score = result.get("compliance_score", 0.0)
                
                return issues, score
                
            except json.JSONDecodeError:
                logger.error(f"Error parseando respuesta de IA para {doc_name}")
                return [], 0.0
                
        except Exception as e:
            logger.error(f"Error verificando cumplimiento de {doc_name}: {e}")
            return [], 0.0
    
    def _determine_verification_category(self, doc_name: str) -> str:
        """Determinar categoría de verificación según el nombre del documento."""
        doc_lower = doc_name.lower()
        
        if "dbhe" in doc_lower:
            return "energy"
        elif "dbsi" in doc_lower:
            return "fire_safety"
        elif "dbsua" in doc_lower:
            return "accessibility"
        elif "residencial" in doc_lower:
            return "residential"
        elif "garaje" in doc_lower or "aparcamiento" in doc_lower:
            return "parking"
        else:
            return "general"
    
    def _get_normative_text(self, doc_name: str) -> str:
        """Obtener texto normativo del documento (simulado)."""
        # En producción, esto extraería el texto del PDF
        return f"Texto normativo del documento {doc_name} (simulado)"
    
    def _parse_compliance_issues(self, 
                               result: Dict[str, Any], 
                               doc_name: str, 
                               floor: str, 
                               category: str) -> List[ComplianceIssue]:
        """Parsear problemas de cumplimiento de la respuesta de IA."""
        issues = []
        
        # Buscar problemas en diferentes categorías
        issue_keys = [
            "energy_issues", "fire_safety_issues", "accessibility_issues",
            "residential_issues", "parking_issues", "general_issues"
        ]
        
        for key in issue_keys:
            if key in result and isinstance(result[key], list):
                for issue_data in result[key]:
                    try:
                        issue = ComplianceIssue(
                            id=issue_data.get("id", f"{doc_name}_{len(issues)}"),
                            title=issue_data.get("title", "Problema de cumplimiento"),
                            description=issue_data.get("description", ""),
                            severity=issue_data.get("severity", "medium").lower(),
                            category=category,
                            document_reference=doc_name,
                            floor=floor,
                            current_value=issue_data.get("current_value"),
                            required_value=issue_data.get("required_value"),
                            recommendation=issue_data.get("recommendation", ""),
                            page_reference=issue_data.get("page_reference"),
                            detected_at=datetime.now()
                        )
                        issues.append(issue)
                    except Exception as e:
                        logger.warning(f"Error parseando problema: {e}")
                        continue
        
        return issues
    
    def _determine_compliance_status(self, score: float, critical_issues: int) -> str:
        """Determinar estado de cumplimiento."""
        if critical_issues > 0:
            return "non_compliant"
        elif score >= 90:
            return "compliant"
        elif score >= 70:
            return "partially_compliant"
        else:
            return "non_compliant"
    
    def generate_compliance_report(self, result: ComplianceResult) -> Dict[str, Any]:
        """Generar reporte de cumplimiento detallado."""
        return {
            "project_summary": result.summary,
            "overall_compliance": {
                "score": result.compliance_score,
                "status": result.summary.get("status", "unknown"),
                "total_checks": result.total_checks,
                "passed_checks": result.passed_checks,
                "failed_checks": result.failed_checks
            },
            "issues_by_severity": {
                "critical": result.critical_issues,
                "high": result.high_issues,
                "medium": result.medium_issues,
                "low": result.low_issues
            },
            "floor_analysis": result.floor_compliance,
            "document_analysis": result.document_compliance,
            "detailed_issues": [
                {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description,
                    "severity": issue.severity,
                    "category": issue.category,
                    "floor": issue.floor,
                    "document": issue.document_reference,
                    "current_value": issue.current_value,
                    "required_value": issue.required_value,
                    "recommendation": issue.recommendation,
                    "page_reference": issue.page_reference
                }
                for issue in result.issues
            ],
            "recommendations": self._generate_recommendations(result)
        }
    
    def _generate_recommendations(self, result: ComplianceResult) -> List[Dict[str, Any]]:
        """Generar recomendaciones basadas en los problemas encontrados."""
        recommendations = []
        
        # Recomendaciones por severidad
        if result.critical_issues > 0:
            recommendations.append({
                "priority": "critical",
                "title": "Resolver problemas críticos",
                "description": f"Se encontraron {result.critical_issues} problemas críticos que deben resolverse antes de continuar",
                "action": "Revisar y corregir todos los problemas marcados como críticos"
            })
        
        if result.high_issues > 0:
            recommendations.append({
                "priority": "high",
                "title": "Atender problemas importantes",
                "description": f"Se encontraron {result.high_issues} problemas importantes que requieren atención",
                "action": "Revisar y corregir los problemas marcados como importantes"
            })
        
        # Recomendaciones por categoría
        categories = {}
        for issue in result.issues:
            if issue.category not in categories:
                categories[issue.category] = 0
            categories[issue.category] += 1
        
        for category, count in categories.items():
            if count > 0:
                recommendations.append({
                    "priority": "medium",
                    "title": f"Mejorar cumplimiento en {category}",
                    "description": f"Se encontraron {count} problemas relacionados con {category}",
                    "action": f"Revisar la normativa específica de {category} y corregir los problemas identificados"
                })
        
        return recommendations
