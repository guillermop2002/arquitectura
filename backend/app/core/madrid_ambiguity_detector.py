"""
Sistema de detección de ambigüedades para el sistema Madrid.
Identifica dudas específicas que requieren aclaración del usuario.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)

class AmbiguityType(Enum):
    """Tipos de ambigüedades detectadas."""
    BUILDING_TYPE = "building_type"
    FLOOR_DESCRIPTION = "floor_description"
    USE_CLASSIFICATION = "use_classification"
    DOCUMENT_MISSING = "document_missing"
    CONFLICTING_DATA = "conflicting_data"
    INCOMPLETE_DATA = "incomplete_data"
    NORMATIVE_UNCLEAR = "normative_unclear"

class AmbiguitySeverity(Enum):
    """Severidad de la ambigüedad."""
    CRITICAL = "critical"  # Bloquea la verificación
    HIGH = "high"         # Requiere aclaración importante
    MEDIUM = "medium"     # Recomendable aclarar
    LOW = "low"          # Opcional aclarar

@dataclass
class AmbiguityItem:
    """Item de ambigüedad detectado."""
    id: str
    type: AmbiguityType
    severity: AmbiguitySeverity
    title: str
    description: str
    detected_in: str  # Campo o sección donde se detectó
    suggested_questions: List[str] = field(default_factory=list)
    possible_resolutions: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class AmbiguityResolution:
    """Resolución de ambigüedad."""
    ambiguity_id: str
    resolution_type: str
    resolved_value: Any
    confidence: float
    resolved_by: str  # 'user', 'system', 'inference'
    resolved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""

class MadridAmbiguityDetector:
    """Detector de ambigüedades para el sistema Madrid."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MadridAmbiguityDetector")
        
        # Patrones para detectar ambigüedades
        self.ambiguity_patterns = self._initialize_ambiguity_patterns()
        
        # Reglas de detección específicas
        self.detection_rules = self._initialize_detection_rules()
    
    def _initialize_ambiguity_patterns(self) -> Dict[str, List[str]]:
        """Inicializar patrones para detectar ambigüedades."""
        return {
            'building_type_ambiguous': [
                r'mixto|mixed|combinado|combinación',
                r'residencial.*comercial|comercial.*residencial',
                r'vivienda.*oficina|oficina.*vivienda',
                r'industrial.*residencial|residencial.*industrial'
            ],
            'floor_description_ambiguous': [
                r'entre.*planta|entre.*piso',
                r'planta.*baja.*primera|primera.*planta.*baja',
                r'sótano.*bajo|bajo.*sótano',
                r'planta.*intermedia|intermedia.*planta',
                r'planta.*media|media.*planta'
            ],
            'use_classification_ambiguous': [
                r'terciario.*residencial|residencial.*terciario',
                r'comercial.*oficina|oficina.*comercial',
                r'servicios.*públicos.*privados|privados.*públicos.*servicios',
                r'dotacional.*comercial|comercial.*dotacional'
            ],
            'document_missing': [
                r'sin.*memoria|memoria.*faltante|falta.*memoria',
                r'sin.*planos|planos.*faltantes|faltan.*planos',
                r'documentación.*incompleta|incompleta.*documentación',
                r'falta.*documento|documento.*faltante'
            ],
            'conflicting_data': [
                r'contradicción|contradictorio|conflicto',
                r'datos.*inconsistentes|inconsistentes.*datos',
                r'información.*conflictiva|conflictiva.*información',
                r'valores.*diferentes|diferentes.*valores'
            ]
        }
    
    def _initialize_detection_rules(self) -> Dict[str, Dict[str, Any]]:
        """Inicializar reglas de detección específicas."""
        return {
            'building_type_validation': {
                'required_fields': ['primary_use'],
                'valid_types': [
                    'residencial', 'industrial', 'garaje-aparcamiento',
                    'servicios_terciarios', 'dotacional_zona_verde',
                    'dotacional_deportivo', 'dotacional_equipamiento',
                    'dotacional_servicios_publicos', 'dotacional_administracion_publica',
                    'dotacional_infraestructural', 'dotacional_via_publica',
                    'dotacional_transporte'
                ],
                'ambiguous_combinations': [
                    ['residencial', 'servicios_terciarios'],
                    ['industrial', 'residencial'],
                    ['garaje-aparcamiento', 'servicios_terciarios']
                ]
            },
            'floor_validation': {
                'special_floors': [-0.5, 0, 0.5],
                'valid_range': [-100, 100],
                'ambiguous_descriptions': [
                    'entreplanta', 'entresótano', 'planta intermedia',
                    'planta baja primera', 'sótano bajo'
                ]
            },
            'secondary_uses_validation': {
                'max_secondary_uses': 5,
                'required_fields': ['use_type', 'floors'],
                'floor_validation': True
            }
        }
    
    def detect_ambiguities(self, project_data: Dict[str, Any]) -> List[AmbiguityItem]:
        """
        Detectar ambigüedades en los datos del proyecto.
        
        Args:
            project_data: Datos del proyecto Madrid
            
        Returns:
            Lista de ambigüedades detectadas
        """
        try:
            self.logger.info(f"Detectando ambigüedades en proyecto: {project_data.get('project_id', 'unknown')}")
            
            ambiguities = []
            
            # Detectar ambigüedades en tipo de edificio
            ambiguities.extend(self._detect_building_type_ambiguities(project_data))
            
            # Detectar ambigüedades en descripciones de plantas
            ambiguities.extend(self._detect_floor_ambiguities(project_data))
            
            # Detectar ambigüedades en usos secundarios
            ambiguities.extend(self._detect_secondary_uses_ambiguities(project_data))
            
            # Detectar ambigüedades en documentos
            ambiguities.extend(self._detect_document_ambiguities(project_data))
            
            # Detectar ambigüedades en datos conflictivos
            ambiguities.extend(self._detect_conflicting_data_ambiguities(project_data))
            
            # Detectar ambigüedades en datos incompletos
            ambiguities.extend(self._detect_incomplete_data_ambiguities(project_data))
            
            self.logger.info(f"Ambigüedades detectadas: {len(ambiguities)}")
            return ambiguities
            
        except Exception as e:
            self.logger.error(f"Error detectando ambigüedades: {e}")
            return []
    
    def _detect_building_type_ambiguities(self, project_data: Dict[str, Any]) -> List[AmbiguityItem]:
        """Detectar ambigüedades en tipo de edificio."""
        ambiguities = []
        
        primary_use = project_data.get('primary_use', '')
        secondary_uses = project_data.get('secondary_uses', [])
        
        # Verificar si el tipo principal es válido
        valid_types = self.detection_rules['building_type_validation']['valid_types']
        if primary_use and primary_use not in valid_types:
            ambiguities.append(AmbiguityItem(
                id=f"building_type_invalid_{primary_use}",
                type=AmbiguityType.BUILDING_TYPE,
                severity=AmbiguitySeverity.CRITICAL,
                title="Tipo de edificio no válido",
                description=f"El tipo de edificio '{primary_use}' no está en la lista de tipos válidos",
                detected_in="primary_use",
                suggested_questions=[
                    "¿Cuál es el uso principal del edificio?",
                    "Seleccione uno de los tipos válidos: residencial, industrial, garaje-aparcamiento, etc."
                ],
                possible_resolutions=[
                    {"value": "residencial", "description": "Edificio residencial"},
                    {"value": "industrial", "description": "Edificio industrial"},
                    {"value": "garaje-aparcamiento", "description": "Garaje o aparcamiento"}
                ]
            ))
        
        # Verificar combinaciones ambiguas
        ambiguous_combinations = self.detection_rules['building_type_validation']['ambiguous_combinations']
        for combination in ambiguous_combinations:
            if primary_use == combination[0]:
                for secondary_use in secondary_uses:
                    if secondary_use.get('use_type') == combination[1]:
                        ambiguities.append(AmbiguityItem(
                            id=f"building_type_ambiguous_{primary_use}_{combination[1]}",
                            type=AmbiguityType.BUILDING_TYPE,
                            severity=AmbiguitySeverity.HIGH,
                            title="Combinación de usos ambigua",
                            description=f"La combinación de uso principal '{primary_use}' con uso secundario '{combination[1]}' puede ser ambigua",
                            detected_in="primary_use + secondary_uses",
                            suggested_questions=[
                                "¿Cuál es el uso predominante del edificio?",
                                "¿Qué porcentaje del edificio corresponde a cada uso?",
                                "¿Hay separación física entre los diferentes usos?"
                            ],
                            possible_resolutions=[
                                {"value": "primary_dominant", "description": "El uso principal es dominante"},
                                {"value": "mixed_use", "description": "Uso mixto equilibrado"},
                                {"value": "secondary_dominant", "description": "El uso secundario es dominante"}
                            ]
                        ))
        
        return ambiguities
    
    def _detect_floor_ambiguities(self, project_data: Dict[str, Any]) -> List[AmbiguityItem]:
        """Detectar ambigüedades en descripciones de plantas."""
        ambiguities = []
        
        secondary_uses = project_data.get('secondary_uses', [])
        
        for i, secondary_use in enumerate(secondary_uses):
            floors = secondary_use.get('floors', [])
            use_type = secondary_use.get('use_type', '')
            
            # Verificar si hay plantas ambiguas
            for floor in floors:
                if isinstance(floor, str):
                    # Verificar patrones ambiguos en descripciones de plantas
                    for pattern in self.ambiguity_patterns['floor_description_ambiguous']:
                        if re.search(pattern, floor.lower()):
                            ambiguities.append(AmbiguityItem(
                                id=f"floor_ambiguous_{use_type}_{i}_{floor}",
                                type=AmbiguityType.FLOOR_DESCRIPTION,
                                severity=AmbiguitySeverity.MEDIUM,
                                title="Descripción de planta ambigua",
                                description=f"La descripción '{floor}' para el uso '{use_type}' es ambigua",
                                detected_in=f"secondary_uses[{i}].floors",
                                suggested_questions=[
                                    f"¿A qué planta se refiere '{floor}'?",
                                    "¿Es una planta completa o una entreplanta?",
                                    "¿Es sótano, planta baja, o planta superior?"
                                ],
                                possible_resolutions=[
                                    {"value": -1, "description": "Sótano 1"},
                                    {"value": 0, "description": "Planta Baja"},
                                    {"value": 0.5, "description": "Entreplanta"},
                                    {"value": 1, "description": "Primer Piso"}
                                ],
                                context={"original_description": floor, "use_type": use_type}
                            ))
                            break
            
            # Verificar si hay plantas fuera del rango válido
            for floor in floors:
                if isinstance(floor, (int, float)):
                    valid_range = self.detection_rules['floor_validation']['valid_range']
                    if not (valid_range[0] <= floor <= valid_range[1]):
                        ambiguities.append(AmbiguityItem(
                            id=f"floor_out_of_range_{use_type}_{i}_{floor}",
                            type=AmbiguityType.FLOOR_DESCRIPTION,
                            severity=AmbiguitySeverity.HIGH,
                            title="Planta fuera del rango válido",
                            description=f"La planta {floor} está fuera del rango válido ({valid_range[0]} a {valid_range[1]})",
                            detected_in=f"secondary_uses[{i}].floors",
                            suggested_questions=[
                                f"¿La planta {floor} es correcta?",
                                "¿Hay un error en la numeración de plantas?",
                                "¿Se refiere a una planta diferente?"
                            ],
                            possible_resolutions=[
                                {"value": floor, "description": "Confirmar que es correcta"},
                                {"value": "corrected", "description": "Corregir a un valor válido"}
                            ]
                        ))
        
        return ambiguities
    
    def _detect_secondary_uses_ambiguities(self, project_data: Dict[str, Any]) -> List[AmbiguityItem]:
        """Detectar ambigüedades en usos secundarios."""
        ambiguities = []
        
        secondary_uses = project_data.get('secondary_uses', [])
        has_secondary_uses = project_data.get('has_secondary_uses', False)
        
        # Verificar inconsistencia entre has_secondary_uses y secondary_uses
        if has_secondary_uses and not secondary_uses:
            ambiguities.append(AmbiguityItem(
                id="secondary_uses_missing",
                type=AmbiguityType.INCOMPLETE_DATA,
                severity=AmbiguitySeverity.HIGH,
                title="Usos secundarios faltantes",
                description="Se indicó que hay usos secundarios pero no se proporcionaron",
                detected_in="has_secondary_uses + secondary_uses",
                suggested_questions=[
                    "¿Cuáles son los usos secundarios del edificio?",
                    "¿En qué plantas se ubican los usos secundarios?",
                    "¿Hay algún uso adicional además del principal?"
                ],
                possible_resolutions=[
                    {"value": "add_secondary_uses", "description": "Agregar usos secundarios"},
                    {"value": "no_secondary_uses", "description": "No hay usos secundarios"}
                ]
            ))
        
        # Verificar si hay demasiados usos secundarios
        max_secondary_uses = self.detection_rules['secondary_uses_validation']['max_secondary_uses']
        if len(secondary_uses) > max_secondary_uses:
            ambiguities.append(AmbiguityItem(
                id="too_many_secondary_uses",
                type=AmbiguityType.USE_CLASSIFICATION,
                severity=AmbiguitySeverity.MEDIUM,
                title="Demasiados usos secundarios",
                description=f"Se han definido {len(secondary_uses)} usos secundarios, el máximo recomendado es {max_secondary_uses}",
                detected_in="secondary_uses",
                suggested_questions=[
                    "¿Todos los usos secundarios son necesarios?",
                    "¿Se pueden agrupar algunos usos similares?",
                    "¿Cuáles son los usos más importantes?"
                ],
                possible_resolutions=[
                    {"value": "reduce_uses", "description": "Reducir número de usos"},
                    {"value": "keep_all", "description": "Mantener todos los usos"}
                ]
            ))
        
        # Verificar usos secundarios individuales
        for i, secondary_use in enumerate(secondary_uses):
            use_type = secondary_use.get('use_type', '')
            floors = secondary_use.get('floors', [])
            
            # Verificar si el tipo de uso es válido
            valid_types = self.detection_rules['building_type_validation']['valid_types']
            if use_type and use_type not in valid_types:
                ambiguities.append(AmbiguityItem(
                    id=f"secondary_use_invalid_{i}_{use_type}",
                    type=AmbiguityType.USE_CLASSIFICATION,
                    severity=AmbiguitySeverity.HIGH,
                    title="Tipo de uso secundario no válido",
                    description=f"El tipo de uso secundario '{use_type}' no es válido",
                    detected_in=f"secondary_uses[{i}].use_type",
                    suggested_questions=[
                        "¿Cuál es el tipo correcto de uso secundario?",
                        "Seleccione uno de los tipos válidos disponibles"
                    ],
                    possible_resolutions=[
                        {"value": "residencial", "description": "Uso residencial"},
                        {"value": "servicios_terciarios", "description": "Servicios terciarios"},
                        {"value": "garaje-aparcamiento", "description": "Garaje o aparcamiento"}
                    ]
                ))
            
            # Verificar si hay plantas definidas
            if not floors:
                ambiguities.append(AmbiguityItem(
                    id=f"secondary_use_no_floors_{i}_{use_type}",
                    type=AmbiguityType.INCOMPLETE_DATA,
                    severity=AmbiguitySeverity.HIGH,
                    title="Faltan plantas para uso secundario",
                    description=f"El uso secundario '{use_type}' no tiene plantas definidas",
                    detected_in=f"secondary_uses[{i}].floors",
                    suggested_questions=[
                        f"¿En qué plantas se ubica el uso '{use_type}'?",
                        "¿Hay plantas específicas para este uso?",
                        "¿Se distribuye en todas las plantas?"
                    ],
                    possible_resolutions=[
                        {"value": "specific_floors", "description": "Plantas específicas"},
                        {"value": "all_floors", "description": "Todas las plantas"},
                        {"value": "ground_floor", "description": "Solo planta baja"}
                    ]
                ))
        
        return ambiguities
    
    def _detect_document_ambiguities(self, project_data: Dict[str, Any]) -> List[AmbiguityItem]:
        """Detectar ambigüedades relacionadas con documentos."""
        ambiguities = []
        
        files = project_data.get('files', [])
        
        # Verificar si hay archivos subidos
        if not files:
            ambiguities.append(AmbiguityItem(
                id="no_files_uploaded",
                type=AmbiguityType.DOCUMENT_MISSING,
                severity=AmbiguitySeverity.CRITICAL,
                title="No se han subido archivos",
                description="No se han subido memoria ni planos del proyecto",
                detected_in="files",
                suggested_questions=[
                    "¿Tiene la memoria del proyecto?",
                    "¿Tiene los planos del edificio?",
                    "¿Puede subir los documentos necesarios?"
                ],
                possible_resolutions=[
                    {"value": "upload_files", "description": "Subir archivos necesarios"},
                    {"value": "files_coming", "description": "Los archivos se subirán después"}
                ]
            ))
        
        # Verificar tipos de archivos
        required_file_types = ['memoria', 'planos']
        uploaded_types = []
        
        for file in files:
            file_lower = file.lower()
            if any(required_type in file_lower for required_type in required_file_types):
                uploaded_types.extend([required_type for required_type in required_file_types if required_type in file_lower])
        
        missing_types = [required_type for required_type in required_file_types if required_type not in uploaded_types]
        
        for missing_type in missing_types:
            ambiguities.append(AmbiguityItem(
                id=f"missing_{missing_type}",
                type=AmbiguityType.DOCUMENT_MISSING,
                severity=AmbiguitySeverity.HIGH,
                title=f"Falta {missing_type}",
                description=f"No se ha subido {missing_type} del proyecto",
                detected_in="files",
                suggested_questions=[
                    f"¿Tiene la {missing_type} del proyecto?",
                    f"¿Puede subir el archivo de {missing_type}?",
                    f"¿La {missing_type} está en otro formato?"
                ],
                possible_resolutions=[
                    {"value": f"upload_{missing_type}", "description": f"Subir {missing_type}"},
                    {"value": f"no_{missing_type}", "description": f"No hay {missing_type} disponible"}
                ]
            ))
        
        return ambiguities
    
    def _detect_conflicting_data_ambiguities(self, project_data: Dict[str, Any]) -> List[AmbiguityItem]:
        """Detectar ambigüedades por datos conflictivos."""
        ambiguities = []
        
        # Verificar conflictos entre datos
        primary_use = project_data.get('primary_use', '')
        secondary_uses = project_data.get('secondary_uses', [])
        
        # Verificar si el uso principal aparece también en usos secundarios
        for secondary_use in secondary_uses:
            if secondary_use.get('use_type') == primary_use:
                ambiguities.append(AmbiguityItem(
                    id=f"primary_use_duplicated_{primary_use}",
                    type=AmbiguityType.CONFLICTING_DATA,
                    severity=AmbiguitySeverity.MEDIUM,
                    title="Uso principal duplicado",
                    description=f"El uso principal '{primary_use}' también aparece en usos secundarios",
                    detected_in="primary_use + secondary_uses",
                    suggested_questions=[
                        "¿El uso principal es diferente de los usos secundarios?",
                        "¿Hay un error en la clasificación de usos?",
                        "¿Se puede eliminar la duplicación?"
                    ],
                    possible_resolutions=[
                        {"value": "remove_duplicate", "description": "Eliminar duplicación"},
                        {"value": "different_primary", "description": "Cambiar uso principal"},
                        {"value": "keep_as_is", "description": "Mantener como está"}
                    ]
                ))
        
        return ambiguities
    
    def _detect_incomplete_data_ambiguities(self, project_data: Dict[str, Any]) -> List[AmbiguityItem]:
        """Detectar ambigüedades por datos incompletos."""
        ambiguities = []
        
        # Verificar campos obligatorios
        required_fields = ['is_existing_building', 'primary_use', 'has_secondary_uses']
        
        for field in required_fields:
            if field not in project_data or project_data[field] is None:
                ambiguities.append(AmbiguityItem(
                    id=f"missing_{field}",
                    type=AmbiguityType.INCOMPLETE_DATA,
                    severity=AmbiguitySeverity.CRITICAL,
                    title=f"Campo obligatorio faltante: {field}",
                    description=f"El campo '{field}' es obligatorio pero no se ha proporcionado",
                    detected_in=field,
                    suggested_questions=[
                        f"¿Cuál es el valor para '{field}'?",
                        f"¿Puede proporcionar información sobre '{field}'?"
                    ],
                    possible_resolutions=[
                        {"value": "provide_value", "description": "Proporcionar valor"},
                        {"value": "skip_field", "description": "Omitir campo"}
                    ]
                ))
        
        return ambiguities
    
    def resolve_ambiguity(self, 
                         ambiguity_id: str, 
                         resolution: AmbiguityResolution,
                         project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolver una ambigüedad específica.
        
        Args:
            ambiguity_id: ID de la ambigüedad
            resolution: Resolución propuesta
            project_data: Datos del proyecto
            
        Returns:
            Datos del proyecto actualizados
        """
        try:
            self.logger.info(f"Resolviendo ambigüedad: {ambiguity_id}")
            
            # Aplicar resolución según el tipo de ambigüedad
            if "building_type" in ambiguity_id:
                return self._resolve_building_type_ambiguity(ambiguity_id, resolution, project_data)
            elif "floor" in ambiguity_id:
                return self._resolve_floor_ambiguity(ambiguity_id, resolution, project_data)
            elif "secondary_use" in ambiguity_id:
                return self._resolve_secondary_use_ambiguity(ambiguity_id, resolution, project_data)
            elif "document" in ambiguity_id or "files" in ambiguity_id:
                return self._resolve_document_ambiguity(ambiguity_id, resolution, project_data)
            else:
                self.logger.warning(f"Tipo de ambigüedad no reconocido: {ambiguity_id}")
                return project_data
                
        except Exception as e:
            self.logger.error(f"Error resolviendo ambigüedad {ambiguity_id}: {e}")
            return project_data
    
    def _resolve_building_type_ambiguity(self, 
                                       ambiguity_id: str, 
                                       resolution: AmbiguityResolution,
                                       project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolver ambigüedad de tipo de edificio."""
        if "invalid" in ambiguity_id:
            project_data['primary_use'] = resolution.resolved_value
        elif "ambiguous" in ambiguity_id:
            # Aplicar resolución de combinación ambigua
            if resolution.resolved_value == "primary_dominant":
                # Mantener uso principal, ajustar secundarios
                pass
            elif resolution.resolved_value == "mixed_use":
                # Marcar como uso mixto
                project_data['is_mixed_use'] = True
        
        return project_data
    
    def _resolve_floor_ambiguity(self, 
                               ambiguity_id: str, 
                               resolution: AmbiguityResolution,
                               project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolver ambigüedad de plantas."""
        # Extraer información del ID de ambigüedad
        parts = ambiguity_id.split('_')
        if len(parts) >= 4:
            use_type = parts[2]
            floor_index = int(parts[3])
            
            # Actualizar planta específica
            for i, secondary_use in enumerate(project_data.get('secondary_uses', [])):
                if i == floor_index and secondary_use.get('use_type') == use_type:
                    floors = secondary_use.get('floors', [])
                    # Reemplazar planta ambigua con valor resuelto
                    if resolution.resolved_value in floors:
                        floors[floors.index(resolution.resolved_value)] = resolution.resolved_value
                    else:
                        floors.append(resolution.resolved_value)
                    secondary_use['floors'] = floors
                    break
        
        return project_data
    
    def _resolve_secondary_use_ambiguity(self, 
                                       ambiguity_id: str, 
                                       resolution: AmbiguityResolution,
                                       project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolver ambigüedad de usos secundarios."""
        if "invalid" in ambiguity_id:
            # Corregir tipo de uso secundario
            parts = ambiguity_id.split('_')
            if len(parts) >= 4:
                use_index = int(parts[3])
                secondary_uses = project_data.get('secondary_uses', [])
                if use_index < len(secondary_uses):
                    secondary_uses[use_index]['use_type'] = resolution.resolved_value
        
        return project_data
    
    def _resolve_document_ambiguity(self, 
                                  ambiguity_id: str, 
                                  resolution: AmbiguityResolution,
                                  project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolver ambigüedad de documentos."""
        if resolution.resolved_value == "upload_files":
            # Marcar que se subirán archivos
            project_data['files_pending'] = True
        elif resolution.resolved_value == "no_files":
            # Marcar que no hay archivos disponibles
            project_data['no_files_available'] = True
        
        return project_data
