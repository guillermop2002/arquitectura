"""
Sistema de Checklist Final para Verificación Arquitectónica de Madrid.
Integra todos los resultados de verificación en un checklist final interactivo.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ChecklistItemStatus(Enum):
    """Estado de un elemento del checklist."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"
    REQUIRES_ATTENTION = "requires_attention"

class ChecklistItemPriority(Enum):
    """Prioridad de un elemento del checklist."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class ChecklistItem:
    """Elemento individual del checklist."""
    id: str
    title: str
    description: str
    category: str
    priority: ChecklistItemPriority
    status: ChecklistItemStatus
    normative_reference: str
    document_requirement: str
    verification_method: str
    evidence_required: List[str]
    current_evidence: List[str] = field(default_factory=list)
    notes: str = ""
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None
    sub_items: List['ChecklistItem'] = field(default_factory=list)

@dataclass
class ChecklistCategory:
    """Categoría del checklist."""
    id: str
    name: str
    description: str
    icon: str
    color: str
    items: List[ChecklistItem] = field(default_factory=list)
    completion_percentage: float = 0.0
    total_items: int = 0
    completed_items: int = 0

@dataclass
class FinalChecklist:
    """Checklist final completo del proyecto."""
    project_id: str
    project_name: str
    building_type: str
    is_existing_building: bool
    categories: List[ChecklistCategory] = field(default_factory=list)
    overall_completion: float = 0.0
    total_items: int = 0
    completed_items: int = 0
    critical_items: int = 0
    high_priority_items: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "draft"  # draft, in_progress, completed, approved
    metadata: Dict[str, Any] = field(default_factory=dict)

class MadridFinalChecklistSystem:
    """Sistema de checklist final para Madrid."""
    
    def __init__(self):
        """Inicializar el sistema de checklist final."""
        self.checklist_templates = self._load_checklist_templates()
        self.normative_mapping = self._initialize_normative_mapping()
        
        logger.info("MadridFinalChecklistSystem initialized")
    
    def _load_checklist_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Cargar plantillas de checklist por tipo de edificio."""
        return {
            "residencial": [
                {
                    "category": "documentacion_basica",
                    "name": "Documentación Básica",
                    "description": "Documentos obligatorios del proyecto",
                    "icon": "fas fa-file-alt",
                    "color": "primary",
                    "items": [
                        {
                            "id": "doc_001",
                            "title": "Memoria Descriptiva",
                            "description": "Memoria descriptiva completa del proyecto",
                            "priority": "critical",
                            "normative_reference": "CTE Art. 2.1",
                            "document_requirement": "Memoria descriptiva firmada por técnico competente",
                            "verification_method": "Verificación de contenido y firma",
                            "evidence_required": ["memoria_descriptiva.pdf", "firma_tecnico.pdf"]
                        },
                        {
                            "id": "doc_002",
                            "title": "Planos Arquitectónicos",
                            "description": "Planos de plantas, alzados y secciones",
                            "priority": "critical",
                            "normative_reference": "CTE Art. 2.2",
                            "document_requirement": "Planos a escala 1:100 o 1:200",
                            "verification_method": "Verificación de escalas y contenido",
                            "evidence_required": ["planos_plantas.pdf", "planos_alzados.pdf", "planos_secciones.pdf"]
                        },
                        {
                            "id": "doc_003",
                            "title": "Memoria de Cálculo",
                            "description": "Cálculos estructurales y de instalaciones",
                            "priority": "high",
                            "normative_reference": "CTE Art. 2.3",
                            "document_requirement": "Cálculos firmados por técnico competente",
                            "verification_method": "Verificación de cálculos y firmas",
                            "evidence_required": ["memoria_calculo_estructura.pdf", "memoria_calculo_instalaciones.pdf"]
                        }
                    ]
                },
                {
                    "category": "seguridad_estructural",
                    "name": "Seguridad Estructural",
                    "description": "Verificación de seguridad estructural",
                    "icon": "fas fa-shield-alt",
                    "color": "danger",
                    "items": [
                        {
                            "id": "est_001",
                            "title": "Cálculo de Cargas",
                            "description": "Verificación de cálculo de cargas",
                            "priority": "critical",
                            "normative_reference": "CTE DB-SE",
                            "document_requirement": "Cálculo de cargas según normativa",
                            "verification_method": "Verificación de cálculos",
                            "evidence_required": ["calculo_cargas.pdf", "planos_estructura.pdf"]
                        },
                        {
                            "id": "est_002",
                            "title": "Dimensionado de Elementos",
                            "description": "Verificación de dimensionado de elementos estructurales",
                            "priority": "high",
                            "normative_reference": "CTE DB-SE Art. 3.1",
                            "document_requirement": "Dimensionado según normativa",
                            "verification_method": "Verificación de dimensiones",
                            "evidence_required": ["dimensionado_vigas.pdf", "dimensionado_pilares.pdf"]
                        }
                    ]
                },
                {
                    "category": "seguridad_incendios",
                    "name": "Seguridad Contra Incendios",
                    "description": "Verificación de seguridad contra incendios",
                    "icon": "fas fa-fire",
                    "color": "warning",
                    "items": [
                        {
                            "id": "inc_001",
                            "title": "Clasificación de Resistencia al Fuego",
                            "description": "Verificación de clasificación de resistencia al fuego",
                            "priority": "critical",
                            "normative_reference": "CTE DB-SI Art. 2.1",
                            "document_requirement": "Clasificación según uso y altura",
                            "verification_method": "Verificación de clasificación",
                            "evidence_required": ["clasificacion_resistencia_fuego.pdf"]
                        },
                        {
                            "id": "inc_002",
                            "title": "Medios de Evacuación",
                            "description": "Verificación de medios de evacuación",
                            "priority": "critical",
                            "normative_reference": "CTE DB-SI Art. 3.1",
                            "document_requirement": "Medios de evacuación según normativa",
                            "verification_method": "Verificación de dimensiones y distancias",
                            "evidence_required": ["planos_evacuacion.pdf", "calculo_evacuacion.pdf"]
                        }
                    ]
                },
                {
                    "category": "accesibilidad",
                    "name": "Accesibilidad",
                    "description": "Verificación de accesibilidad universal",
                    "icon": "fas fa-wheelchair",
                    "color": "info",
                    "items": [
                        {
                            "id": "acc_001",
                            "title": "Accesibilidad Universal",
                            "description": "Verificación de accesibilidad universal",
                            "priority": "high",
                            "normative_reference": "CTE DB-SU Art. 2.1",
                            "document_requirement": "Accesibilidad según normativa",
                            "verification_method": "Verificación de dimensiones y rampas",
                            "evidence_required": ["planos_accesibilidad.pdf", "memoria_accesibilidad.pdf"]
                        }
                    ]
                },
                {
                    "category": "eficiencia_energetica",
                    "name": "Eficiencia Energética",
                    "description": "Verificación de eficiencia energética",
                    "icon": "fas fa-leaf",
                    "color": "success",
                    "items": [
                        {
                            "id": "ener_001",
                            "title": "Limitación de Demanda Energética",
                            "description": "Verificación de limitación de demanda energética",
                            "priority": "high",
                            "normative_reference": "CTE DB-HE Art. 2.1",
                            "document_requirement": "Cumplimiento de límites de demanda",
                            "verification_method": "Verificación de cálculos energéticos",
                            "evidence_required": ["calculo_demanda_energetica.pdf", "certificado_eficiencia.pdf"]
                        }
                    ]
                }
            ],
            "industrial": [
                # Plantilla específica para edificios industriales
                {
                    "category": "documentacion_basica",
                    "name": "Documentación Básica",
                    "description": "Documentos obligatorios del proyecto industrial",
                    "icon": "fas fa-file-alt",
                    "color": "primary",
                    "items": [
                        {
                            "id": "doc_ind_001",
                            "title": "Memoria Descriptiva Industrial",
                            "description": "Memoria descriptiva específica para uso industrial",
                            "priority": "critical",
                            "normative_reference": "CTE Art. 2.1 + PGOUM Industrial",
                            "document_requirement": "Memoria con análisis de uso industrial",
                            "verification_method": "Verificación de contenido industrial",
                            "evidence_required": ["memoria_descriptiva_industrial.pdf"]
                        }
                    ]
                }
            ]
        }
    
    def _initialize_normative_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Inicializar mapeo de normativa por tipo de edificio."""
        return {
            "residencial": {
                "basic_documents": ["DB-HE", "DB-HR", "DB-SI", "DB-SU"],
                "pgoum_documents": ["pgoum_residencial", "pgoum_general universal"],
                "support_documents": ["DA_DB-HE-1", "DA_DB-HE-2", "DA_DB-HE-3"]
            },
            "industrial": {
                "basic_documents": ["DB-HE", "DB-HR", "DB-SI", "DB-SU"],
                "pgoum_documents": ["pgoum_industrial", "pgoum_general universal"],
                "support_documents": ["DA_DB-HE-1", "DA_DB-HE-2", "DA_DB-HE-3"]
            }
        }
    
    def generate_final_checklist(self, 
                               project_data: Dict[str, Any], 
                               normative_application: Dict[str, Any], 
                               compliance_results: Dict[str, Any]) -> FinalChecklist:
        """
        Generar checklist final basado en los datos del proyecto y normativa aplicada.
        
        Args:
            project_data: Datos del proyecto
            normative_application: Aplicación de normativa específica
            compliance_results: Resultados de verificación de cumplimiento
            
        Returns:
            Checklist final completo
        """
        try:
            logger.info(f"Generando checklist final para proyecto {project_data.get('project_id', 'unknown')}")
            
            # Extraer datos del proyecto
            project_id = project_data.get('project_id', 'unknown')
            project_name = project_data.get('project_name', 'Proyecto Sin Nombre')
            building_type = project_data.get('primary_use', 'residencial')
            is_existing_building = project_data.get('is_existing_building', False)
            
            # Obtener plantilla de checklist
            template = self.checklist_templates.get(building_type, self.checklist_templates['residencial'])
            
            # Generar categorías del checklist
            categories = []
            for category_template in template:
                category = self._create_checklist_category(
                    category_template, 
                    normative_application, 
                    compliance_results
                )
                categories.append(category)
            
            # Crear checklist final
            checklist = FinalChecklist(
                project_id=project_id,
                project_name=project_name,
                building_type=building_type,
                is_existing_building=is_existing_building,
                categories=categories,
                metadata={
                    "normative_application": normative_application,
                    "compliance_results": compliance_results,
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            # Calcular estadísticas
            self._calculate_checklist_statistics(checklist)
            
            logger.info(f"Checklist generado: {len(categories)} categorías, {checklist.total_items} elementos")
            
            return checklist
            
        except Exception as e:
            logger.error(f"Error generando checklist final: {e}")
            raise
    
    def _create_checklist_category(self, 
                                 category_template: Dict[str, Any], 
                                 normative_application: Dict[str, Any], 
                                 compliance_results: Dict[str, Any]) -> ChecklistCategory:
        """Crear categoría del checklist basada en plantilla."""
        # Crear elementos del checklist
        items = []
        for item_template in category_template.get('items', []):
            item = self._create_checklist_item(
                item_template, 
                normative_application, 
                compliance_results
            )
            items.append(item)
        
        # Crear categoría
        category = ChecklistCategory(
            id=category_template['category'],
            name=category_template['name'],
            description=category_template['description'],
            icon=category_template['icon'],
            color=category_template['color'],
            items=items
        )
        
        return category
    
    def _create_checklist_item(self, 
                             item_template: Dict[str, Any], 
                             normative_application: Dict[str, Any], 
                             compliance_results: Dict[str, Any]) -> ChecklistItem:
        """Crear elemento del checklist basado en plantilla."""
        # Determinar estado inicial basado en compliance results
        status = self._determine_initial_status(item_template, compliance_results)
        
        # Crear elemento
        item = ChecklistItem(
            id=item_template['id'],
            title=item_template['title'],
            description=item_template['description'],
            category=item_template.get('category', 'general'),
            priority=ChecklistItemPriority(item_template['priority']),
            status=status,
            normative_reference=item_template['normative_reference'],
            document_requirement=item_template['document_requirement'],
            verification_method=item_template['verification_method'],
            evidence_required=item_template['evidence_required'],
            current_evidence=self._get_current_evidence(item_template, compliance_results)
        )
        
        return item
    
    def _determine_initial_status(self, 
                                item_template: Dict[str, Any], 
                                compliance_results: Dict[str, Any]) -> ChecklistItemStatus:
        """Determinar estado inicial del elemento basado en resultados de cumplimiento."""
        item_id = item_template['id']
        
        # Buscar en resultados de cumplimiento
        if 'issues' in compliance_results:
            for issue in compliance_results['issues']:
                if issue.get('id') == item_id:
                    if issue.get('severity') == 'critical':
                        return ChecklistItemStatus.FAILED
                    elif issue.get('severity') == 'high':
                        return ChecklistItemStatus.REQUIRES_ATTENTION
                    else:
                        return ChecklistItemStatus.PENDING
        
        # Estado por defecto
        return ChecklistItemStatus.PENDING
    
    def _get_current_evidence(self, 
                            item_template: Dict[str, Any], 
                            compliance_results: Dict[str, Any]) -> List[str]:
        """Obtener evidencia actual del elemento."""
        # En una implementación real, esto buscaría en los documentos procesados
        # Por ahora, devolver lista vacía
        return []
    
    def _calculate_checklist_statistics(self, checklist: FinalChecklist):
        """Calcular estadísticas del checklist."""
        total_items = 0
        completed_items = 0
        critical_items = 0
        high_priority_items = 0
        
        for category in checklist.categories:
            category_total = len(category.items)
            category_completed = len([item for item in category.items if item.status == ChecklistItemStatus.COMPLETED])
            
            total_items += category_total
            completed_items += category_completed
            
            # Contar por prioridad
            critical_items += len([item for item in category.items if item.priority == ChecklistItemPriority.CRITICAL])
            high_priority_items += len([item for item in category.items if item.priority == ChecklistItemPriority.HIGH])
            
            # Calcular porcentaje de completado de la categoría
            if category_total > 0:
                category.completion_percentage = (category_completed / category_total) * 100
                category.total_items = category_total
                category.completed_items = category_completed
        
        # Actualizar estadísticas del checklist
        checklist.total_items = total_items
        checklist.completed_items = completed_items
        checklist.critical_items = critical_items
        checklist.high_priority_items = high_priority_items
        
        if total_items > 0:
            checklist.overall_completion = (completed_items / total_items) * 100
    
    def update_checklist_item(self, 
                            checklist: FinalChecklist, 
                            item_id: str, 
                            updates: Dict[str, Any]) -> bool:
        """Actualizar elemento del checklist."""
        try:
            for category in checklist.categories:
                for item in category.items:
                    if item.id == item_id:
                        # Actualizar campos
                        for key, value in updates.items():
                            if hasattr(item, key):
                                setattr(item, key, value)
                        
                        item.updated_at = datetime.now()
                        
                        # Recalcular estadísticas
                        self._calculate_checklist_statistics(checklist)
                        
                        logger.info(f"Elemento {item_id} actualizado")
                        return True
            
            logger.warning(f"Elemento {item_id} no encontrado")
            return False
            
        except Exception as e:
            logger.error(f"Error actualizando elemento {item_id}: {e}")
            return False
    
    def generate_checklist_report(self, checklist: FinalChecklist) -> Dict[str, Any]:
        """Generar reporte del checklist."""
        return {
            "project_info": {
                "project_id": checklist.project_id,
                "project_name": checklist.project_name,
                "building_type": checklist.building_type,
                "is_existing_building": checklist.is_existing_building,
                "status": checklist.status,
                "created_at": checklist.created_at.isoformat(),
                "updated_at": checklist.updated_at.isoformat()
            },
            "overall_statistics": {
                "total_items": checklist.total_items,
                "completed_items": checklist.completed_items,
                "completion_percentage": checklist.overall_completion,
                "critical_items": checklist.critical_items,
                "high_priority_items": checklist.high_priority_items
            },
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "completion_percentage": category.completion_percentage,
                    "total_items": category.total_items,
                    "completed_items": category.completed_items,
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
            ],
            "recommendations": self._generate_recommendations(checklist),
            "next_steps": self._generate_next_steps(checklist)
        }
    
    def _generate_recommendations(self, checklist: FinalChecklist) -> List[Dict[str, Any]]:
        """Generar recomendaciones basadas en el estado del checklist."""
        recommendations = []
        
        # Recomendaciones por prioridad
        critical_pending = [item for item in self._get_all_items(checklist) 
                          if item.priority == ChecklistItemPriority.CRITICAL and 
                          item.status == ChecklistItemStatus.PENDING]
        
        if critical_pending:
            recommendations.append({
                "priority": "critical",
                "title": "Resolver elementos críticos pendientes",
                "description": f"Hay {len(critical_pending)} elementos críticos pendientes que requieren atención inmediata",
                "items": [item.title for item in critical_pending]
            })
        
        # Recomendaciones por categoría
        for category in checklist.categories:
            if category.completion_percentage < 50:
                recommendations.append({
                    "priority": "high",
                    "title": f"Completar categoría {category.name}",
                    "description": f"La categoría {category.name} está solo {category.completion_percentage:.1f}% completa",
                    "items": [item.title for item in category.items if item.status == ChecklistItemStatus.PENDING]
                })
        
        return recommendations
    
    def _generate_next_steps(self, checklist: FinalChecklist) -> List[Dict[str, Any]]:
        """Generar próximos pasos basados en el estado del checklist."""
        next_steps = []
        
        # Próximos pasos por prioridad
        high_priority_pending = [item for item in self._get_all_items(checklist) 
                               if item.priority == ChecklistItemPriority.HIGH and 
                               item.status == ChecklistItemStatus.PENDING]
        
        if high_priority_pending:
            next_steps.append({
                "action": "complete_high_priority",
                "title": "Completar elementos de alta prioridad",
                "description": f"Completar {len(high_priority_pending)} elementos de alta prioridad",
                "items": [item.title for item in high_priority_pending[:3]]  # Mostrar solo los primeros 3
            })
        
        return next_steps
    
    def _get_all_items(self, checklist: FinalChecklist) -> List[ChecklistItem]:
        """Obtener todos los elementos del checklist."""
        all_items = []
        for category in checklist.categories:
            all_items.extend(category.items)
        return all_items
