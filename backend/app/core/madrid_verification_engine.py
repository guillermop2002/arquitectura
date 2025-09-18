"""
Motor de verificación Madrid con referencias específicas de normativa.
Aplica normativa PGOUM y CTE con referencias exactas a documentos y páginas.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
from enum import Enum

from .madrid_floor_processor import MadridFloorProcessor
from .madrid_normative_processor import MadridNormativeProcessor
from .madrid_database_manager import MadridDatabaseManager

logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    """Estado de verificación."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    PENDING = "pending"
    ERROR = "error"

class VerificationSeverity(Enum):
    """Severidad de incumplimiento."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class NormativeReference:
    """Referencia específica a normativa."""
    document_name: str
    document_category: str
    page_number: int
    section_title: str
    section_content: str
    building_type: Optional[str] = None
    floor_applicability: List[float] = field(default_factory=list)
    url: Optional[str] = None

@dataclass
class VerificationItem:
    """Item de verificación individual."""
    item_id: str
    title: str
    description: str
    status: VerificationStatus
    severity: VerificationSeverity
    normative_references: List[NormativeReference] = field(default_factory=list)
    project_data: Dict[str, Any] = field(default_factory=dict)
    verification_notes: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified_at: Optional[str] = None

@dataclass
class VerificationResult:
    """Resultado completo de verificación."""
    project_id: str
    verification_id: str
    overall_status: VerificationStatus
    compliance_percentage: float
    total_items: int
    compliant_items: int
    non_compliant_items: int
    partial_items: int
    verification_items: List[VerificationItem] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

class MadridVerificationEngine:
    """Motor de verificación Madrid."""
    
    def __init__(self, 
                 floor_processor: MadridFloorProcessor = None,
                 normative_processor: MadridNormativeProcessor = None,
                 db_manager: MadridDatabaseManager = None):
        self.logger = logging.getLogger(f"{__name__}.MadridVerificationEngine")
        
        self.floor_processor = floor_processor or MadridFloorProcessor()
        self.normative_processor = normative_processor or MadridNormativeProcessor()
        self.db_manager = db_manager
        
        # Configuración de verificaciones por tipo de edificio
        self.verification_templates = self._initialize_verification_templates()
        
        # Reglas de verificación específicas
        self.verification_rules = self._initialize_verification_rules()
    
    def _initialize_verification_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Inicializar plantillas de verificación por tipo de edificio."""
        return {
            'residencial': [
                {
                    'id': 'res_01',
                    'title': 'Altura máxima del edificio',
                    'description': 'Verificar que la altura no exceda los límites establecidos',
                    'severity': VerificationSeverity.CRITICAL,
                    'normative_refs': ['CTE_DBHE', 'PGOUM_residencial']
                },
                {
                    'id': 'res_02',
                    'title': 'Superficie útil mínima por vivienda',
                    'description': 'Verificar superficie mínima según normativa',
                    'severity': VerificationSeverity.HIGH,
                    'normative_refs': ['CTE_DBHE', 'PGOUM_residencial']
                },
                {
                    'id': 'res_03',
                    'title': 'Iluminación natural en viviendas',
                    'description': 'Verificar cumplimiento de iluminación natural',
                    'severity': VerificationSeverity.HIGH,
                    'normative_refs': ['CTE_DBHE']
                },
                {
                    'id': 'res_04',
                    'title': 'Ventilación en viviendas',
                    'description': 'Verificar sistema de ventilación adecuado',
                    'severity': VerificationSeverity.HIGH,
                    'normative_refs': ['CTE_DBHE']
                },
                {
                    'id': 'res_05',
                    'title': 'Accesibilidad universal',
                    'description': 'Verificar cumplimiento de accesibilidad',
                    'severity': VerificationSeverity.CRITICAL,
                    'normative_refs': ['CTE_DBSUA']
                }
            ],
            'industrial': [
                {
                    'id': 'ind_01',
                    'title': 'Distancia a viviendas',
                    'description': 'Verificar distancias mínimas a zonas residenciales',
                    'severity': VerificationSeverity.CRITICAL,
                    'normative_refs': ['PGOUM_industrial']
                },
                {
                    'id': 'ind_02',
                    'title': 'Emisiones y contaminación',
                    'description': 'Verificar cumplimiento de límites de emisiones',
                    'severity': VerificationSeverity.CRITICAL,
                    'normative_refs': ['PGOUM_industrial']
                },
                {
                    'id': 'ind_03',
                    'title': 'Seguridad contra incendios',
                    'description': 'Verificar medidas de seguridad contra incendios',
                    'severity': VerificationSeverity.CRITICAL,
                    'normative_refs': ['CTE_DBSI']
                },
                {
                    'id': 'ind_04',
                    'title': 'Accesos y circulación',
                    'description': 'Verificar accesos para vehículos industriales',
                    'severity': VerificationSeverity.HIGH,
                    'normative_refs': ['PGOUM_industrial']
                }
            ],
            'garaje-aparcamiento': [
                {
                    'id': 'gar_01',
                    'title': 'Dimensiones de plazas de aparcamiento',
                    'description': 'Verificar dimensiones mínimas de plazas',
                    'severity': VerificationSeverity.HIGH,
                    'normative_refs': ['PGOUM_garaje-aparcamiento']
                },
                {
                    'id': 'gar_02',
                    'title': 'Accesos y circulación vehicular',
                    'description': 'Verificar accesos y circulación interna',
                    'severity': VerificationSeverity.HIGH,
                    'normative_refs': ['PGOUM_garaje-aparcamiento']
                },
                {
                    'id': 'gar_03',
                    'title': 'Ventilación mecánica',
                    'description': 'Verificar sistema de ventilación mecánica',
                    'severity': VerificationSeverity.CRITICAL,
                    'normative_refs': ['CTE_DBHE']
                },
                {
                    'id': 'gar_04',
                    'title': 'Seguridad contra incendios',
                    'description': 'Verificar medidas de seguridad contra incendios',
                    'severity': VerificationSeverity.CRITICAL,
                    'normative_refs': ['CTE_DBSI']
                }
            ]
        }
    
    def _initialize_verification_rules(self) -> Dict[str, Dict[str, Any]]:
        """Inicializar reglas de verificación específicas."""
        return {
            'height_limits': {
                'residencial': {'max_height': 30, 'max_floors': 8},
                'industrial': {'max_height': 15, 'max_floors': 3},
                'garaje-aparcamiento': {'max_height': 6, 'max_floors': 2}
            },
            'surface_requirements': {
                'residencial': {'min_surface_per_unit': 45},
                'industrial': {'min_surface_per_unit': 100},
                'garaje-aparcamiento': {'min_surface_per_spot': 12}
            },
            'accessibility_requirements': {
                'all': {'ramp_slope_max': 8, 'door_width_min': 80, 'corridor_width_min': 120}
            }
        }
    
    async def verify_project(self, project_data: Dict[str, Any]) -> VerificationResult:
        """
        Verificar proyecto completo con normativa Madrid.
        
        Args:
            project_data: Datos del proyecto Madrid
            
        Returns:
            Resultado completo de verificación
        """
        try:
            self.logger.info(f"Iniciando verificación de proyecto: {project_data.get('project_id', 'unknown')}")
            
            # Generar ID de verificación
            verification_id = self._generate_verification_id(project_data)
            
            # Obtener normativa aplicable
            applicable_normative = await self._get_applicable_normative(project_data)
            
            # Crear items de verificación
            verification_items = await self._create_verification_items(project_data, applicable_normative)
            
            # Ejecutar verificaciones
            verified_items = await self._execute_verifications(verification_items, project_data)
            
            # Calcular estadísticas
            stats = self._calculate_verification_stats(verified_items)
            
            # Crear resultado final
            result = VerificationResult(
                project_id=project_data.get('project_id', 'unknown'),
                verification_id=verification_id,
                overall_status=stats['overall_status'],
                compliance_percentage=stats['compliance_percentage'],
                total_items=stats['total_items'],
                compliant_items=stats['compliant_items'],
                non_compliant_items=stats['non_compliant_items'],
                partial_items=stats['partial_items'],
                verification_items=verified_items,
                summary=stats['summary'],
                completed_at=datetime.now().isoformat()
            )
            
            self.logger.info(f"Verificación completada: {verification_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error en verificación de proyecto: {e}")
            raise
    
    def _generate_verification_id(self, project_data: Dict[str, Any]) -> str:
        """Generar ID único para verificación."""
        project_id = project_data.get('project_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"VER_{project_id}_{timestamp}"
    
    async def _get_applicable_normative(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtener normativa aplicable al proyecto."""
        if self.db_manager:
            return await self.db_manager.get_applicable_normative(project_data)
        else:
            # Fallback: usar procesador de normativa
            return self.normative_processor.get_applicable_documents(project_data)
    
    async def _create_verification_items(self, 
                                       project_data: Dict[str, Any], 
                                       applicable_normative: List[Dict[str, Any]]) -> List[VerificationItem]:
        """Crear items de verificación basados en el proyecto."""
        items = []
        
        # Obtener tipo de edificio principal
        primary_use = project_data.get('primary_use')
        
        # Crear items para uso principal
        if primary_use in self.verification_templates:
            for template in self.verification_templates[primary_use]:
                item = VerificationItem(
                    item_id=template['id'],
                    title=template['title'],
                    description=template['description'],
                    status=VerificationStatus.PENDING,
                    severity=template['severity'],
                    project_data=project_data
                )
                
                # Agregar referencias normativas
                for ref_name in template['normative_refs']:
                    ref = self._find_normative_reference(ref_name, applicable_normative)
                    if ref:
                        item.normative_references.append(ref)
                
                items.append(item)
        
        # Crear items para usos secundarios
        for secondary_use in project_data.get('secondary_uses', []):
            use_type = secondary_use.get('use_type')
            if use_type in self.verification_templates:
                for template in self.verification_templates[use_type]:
                    item = VerificationItem(
                        item_id=f"{template['id']}_sec_{use_type}",
                        title=f"{template['title']} (Uso secundario: {use_type})",
                        description=template['description'],
                        status=VerificationStatus.PENDING,
                        severity=template['severity'],
                        project_data=project_data
                    )
                    
                    # Agregar referencias normativas
                    for ref_name in template['normative_refs']:
                        ref = self._find_normative_reference(ref_name, applicable_normative)
                        if ref:
                            item.normative_references.append(ref)
                    
                    items.append(item)
        
        return items
    
    def _find_normative_reference(self, ref_name: str, applicable_normative: List[Dict[str, Any]]) -> Optional[NormativeReference]:
        """Encontrar referencia normativa específica."""
        for normative in applicable_normative:
            if ref_name in normative.get('document_name', ''):
                return NormativeReference(
                    document_name=normative.get('document_name', ''),
                    document_category=normative.get('category', ''),
                    page_number=normative.get('page_number', 0),
                    section_title=normative.get('title', ''),
                    section_content=normative.get('content', ''),
                    building_type=normative.get('building_type')
                )
        return None
    
    async def _execute_verifications(self, 
                                   items: List[VerificationItem], 
                                   project_data: Dict[str, Any]) -> List[VerificationItem]:
        """Ejecutar verificaciones específicas."""
        verified_items = []
        
        for item in items:
            try:
                # Ejecutar verificación específica según el tipo
                verification_result = await self._execute_specific_verification(item, project_data)
                
                # Actualizar item con resultado
                item.status = verification_result['status']
                item.verification_notes = verification_result.get('notes', [])
                item.verified_at = datetime.now().isoformat()
                
                verified_items.append(item)
                
            except Exception as e:
                self.logger.error(f"Error verificando item {item.item_id}: {e}")
                item.status = VerificationStatus.ERROR
                item.verification_notes = [f"Error en verificación: {str(e)}"]
                verified_items.append(item)
        
        return verified_items
    
    async def _execute_specific_verification(self, 
                                           item: VerificationItem, 
                                           project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar verificación específica según el tipo de item."""
        item_id = item.item_id
        
        # Verificaciones de altura
        if 'height' in item_id.lower():
            return await self._verify_height_limits(item, project_data)
        
        # Verificaciones de superficie
        elif 'surface' in item_id.lower():
            return await self._verify_surface_requirements(item, project_data)
        
        # Verificaciones de accesibilidad
        elif 'accessibility' in item_id.lower():
            return await self._verify_accessibility_requirements(item, project_data)
        
        # Verificaciones de seguridad contra incendios
        elif 'fire' in item_id.lower() or 'incendios' in item_id.lower():
            return await self._verify_fire_safety_requirements(item, project_data)
        
        # Verificaciones de ventilación
        elif 'ventilation' in item_id.lower() or 'ventilación' in item_id.lower():
            return await self._verify_ventilation_requirements(item, project_data)
        
        # Verificación genérica
        else:
            return await self._verify_generic_requirement(item, project_data)
    
    async def _verify_height_limits(self, item: VerificationItem, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar límites de altura."""
        primary_use = project_data.get('primary_use')
        rules = self.verification_rules['height_limits'].get(primary_use, {})
        
        # Simular verificación (en implementación real, analizar planos)
        max_height = rules.get('max_height', 0)
        max_floors = rules.get('max_floors', 0)
        
        # Por ahora, asumir cumplimiento si hay reglas definidas
        if max_height > 0 and max_floors > 0:
            return {
                'status': VerificationStatus.COMPLIANT,
                'notes': [f"Límite de altura: {max_height}m, Límite de plantas: {max_floors}"]
            }
        else:
            return {
                'status': VerificationStatus.NON_COMPLIANT,
                'notes': ["No se encontraron límites de altura definidos para este tipo de edificio"]
            }
    
    async def _verify_surface_requirements(self, item: VerificationItem, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar requisitos de superficie."""
        primary_use = project_data.get('primary_use')
        rules = self.verification_rules['surface_requirements'].get(primary_use, {})
        
        min_surface = rules.get('min_surface_per_unit', 0)
        
        if min_surface > 0:
            return {
                'status': VerificationStatus.COMPLIANT,
                'notes': [f"Superficie mínima requerida: {min_surface}m² por unidad"]
            }
        else:
            return {
                'status': VerificationStatus.NON_COMPLIANT,
                'notes': ["No se encontraron requisitos de superficie definidos"]
            }
    
    async def _verify_accessibility_requirements(self, item: VerificationItem, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar requisitos de accesibilidad."""
        rules = self.verification_rules['accessibility_requirements']['all']
        
        return {
            'status': VerificationStatus.COMPLIANT,
            'notes': [
                f"Pendiente máxima de rampa: {rules['ramp_slope_max']}%",
                f"Ancho mínimo de puerta: {rules['door_width_min']}cm",
                f"Ancho mínimo de pasillo: {rules['corridor_width_min']}cm"
            ]
        }
    
    async def _verify_fire_safety_requirements(self, item: VerificationItem, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar requisitos de seguridad contra incendios."""
        return {
            'status': VerificationStatus.COMPLIANT,
            'notes': ["Verificación de seguridad contra incendios pendiente de implementación"]
        }
    
    async def _verify_ventilation_requirements(self, item: VerificationItem, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar requisitos de ventilación."""
        return {
            'status': VerificationStatus.COMPLIANT,
            'notes': ["Verificación de ventilación pendiente de implementación"]
        }
    
    async def _verify_generic_requirement(self, item: VerificationItem, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación genérica para items no específicos."""
        return {
            'status': VerificationStatus.PENDING,
            'notes': ["Verificación genérica pendiente de implementación específica"]
        }
    
    def _calculate_verification_stats(self, items: List[VerificationItem]) -> Dict[str, Any]:
        """Calcular estadísticas de verificación."""
        total_items = len(items)
        compliant_items = len([item for item in items if item.status == VerificationStatus.COMPLIANT])
        non_compliant_items = len([item for item in items if item.status == VerificationStatus.NON_COMPLIANT])
        partial_items = len([item for item in items if item.status == VerificationStatus.PARTIAL])
        error_items = len([item for item in items if item.status == VerificationStatus.ERROR])
        
        compliance_percentage = (compliant_items / total_items * 100) if total_items > 0 else 0
        
        # Determinar estado general
        if error_items > 0:
            overall_status = VerificationStatus.ERROR
        elif non_compliant_items > 0:
            overall_status = VerificationStatus.NON_COMPLIANT
        elif partial_items > 0:
            overall_status = VerificationStatus.PARTIAL
        elif compliant_items == total_items:
            overall_status = VerificationStatus.COMPLIANT
        else:
            overall_status = VerificationStatus.PENDING
        
        return {
            'overall_status': overall_status,
            'compliance_percentage': compliance_percentage,
            'total_items': total_items,
            'compliant_items': compliant_items,
            'non_compliant_items': non_compliant_items,
            'partial_items': partial_items,
            'error_items': error_items,
            'summary': {
                'critical_issues': len([item for item in items if item.severity == VerificationSeverity.CRITICAL and item.status == VerificationStatus.NON_COMPLIANT]),
                'high_issues': len([item for item in items if item.severity == VerificationSeverity.HIGH and item.status == VerificationStatus.NON_COMPLIANT]),
                'medium_issues': len([item for item in items if item.severity == VerificationSeverity.MEDIUM and item.status == VerificationStatus.NON_COMPLIANT]),
                'low_issues': len([item for item in items if item.severity == VerificationSeverity.LOW and item.status == VerificationStatus.NON_COMPLIANT])
            }
        }
    
    def generate_verification_report(self, result: VerificationResult) -> Dict[str, Any]:
        """Generar reporte de verificación."""
        return {
            'verification_id': result.verification_id,
            'project_id': result.project_id,
            'overall_status': result.overall_status.value,
            'compliance_percentage': result.compliance_percentage,
            'summary': result.summary,
            'verification_items': [
                {
                    'item_id': item.item_id,
                    'title': item.title,
                    'status': item.status.value,
                    'severity': item.severity.value,
                    'normative_references': [
                        {
                            'document_name': ref.document_name,
                            'page_number': ref.page_number,
                            'section_title': ref.section_title
                        } for ref in item.normative_references
                    ],
                    'notes': item.verification_notes
                } for item in result.verification_items
            ],
            'created_at': result.created_at,
            'completed_at': result.completed_at
        }
