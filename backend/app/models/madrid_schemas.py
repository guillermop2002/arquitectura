"""
Esquemas de datos específicos para el sistema Madrid.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

class BuildingType(Enum):
    """Tipos de uso de edificio según PGOUM Madrid."""
    RESIDENCIAL = "residencial"
    INDUSTRIAL = "industrial"
    GARAJE_APARCAMIENTO = "garaje-aparcamiento"
    SERVICIOS_TERCIARIOS = "servicios_terciarios"
    DOTACIONAL_ZONA_VERDE = "dotacional_zona_verde"
    DOTACIONAL_DEPORTIVO = "dotacional_deportivo"
    DOTACIONAL_EQUIPAMIENTO = "dotacional_equipamiento"
    DOTACIONAL_SERVICIOS_PUBLICOS = "dotacional_servicios_publicos"
    DOTACIONAL_ADMINISTRACION_PUBLICA = "dotacional_administracion_publica"
    DOTACIONAL_INFRAESTRUCTURAL = "dotacional_infraestructural"
    DOTACIONAL_VIA_PUBLICA = "dotacional_via_publica"
    DOTACIONAL_TRANSPORTE = "dotacional_transporte"

@dataclass
class SecondaryUse:
    """Uso secundario con información de plantas."""
    use_type: BuildingType
    floors: List[Union[int, float]]  # Permite 0.5 y -0.5 para plantas especiales

@dataclass
class MadridProjectData:
    """Datos específicos de un proyecto Madrid."""
    is_existing_building: bool
    primary_use: BuildingType
    has_secondary_uses: bool
    secondary_uses: List[SecondaryUse]
    files: List[str]
    project_id: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.project_id is None:
            self.project_id = f"MADRID_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class AmbiguityType(Enum):
    """Tipos de ambigüedades detectadas."""
    INVALID_BUILDING_TYPE = "invalid_building_type"
    MISSING_SECONDARY_USES = "missing_secondary_uses"
    AMBIGUOUS_FLOOR_DESCRIPTIONS = "ambiguous_floor_descriptions"
    INCONSISTENT_USE_ASSIGNMENTS = "inconsistent_use_assignments"
    MISSING_NORMATIVE_REFERENCES = "missing_normative_references"
    UNCLEAR_DOCUMENTATION = "unclear_documentation"

class AmbiguitySeverity(Enum):
    """Niveles de severidad de ambigüedades."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Ambiguity:
    """Representa una ambigüedad detectada."""
    id: str
    type: AmbiguityType
    severity: AmbiguitySeverity
    title: str
    description: str
    context: Optional[Dict[str, Any]] = None
    suggestions: List[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.created_at is None:
            self.created_at = datetime.now()

class VerificationStatus(Enum):
    """Estados de verificación."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    ERROR = "error"

@dataclass
class VerificationItem:
    """Item individual de verificación."""
    id: str
    title: str
    description: str
    status: VerificationStatus
    compliance_percentage: float
    normative_reference: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class VerificationResult:
    """Resultado completo de verificación Madrid."""
    verification_id: str
    project_id: str
    overall_status: VerificationStatus
    compliance_percentage: float
    total_items: int
    compliant_items: int
    non_compliant_items: int
    verification_items: List[VerificationItem]
    normative_documents: List[str]
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class ChatbotSessionStatus(Enum):
    """Estados de sesión del chatbot."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class ChatbotSession:
    """Sesión del chatbot para resolución de ambigüedades."""
    session_id: str
    project_id: str
    status: ChatbotSessionStatus
    ambiguities: List[Ambiguity]
    resolved_ambiguities: List[str]
    messages: List[Dict[str, Any]]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class NormativeReference:
    """Referencia normativa específica."""
    document_name: str
    page_number: int
    section: str
    subsection: Optional[str] = None
    paragraph: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ReportData:
    """Datos para generación de reportes."""
    report_id: str
    project_id: str
    verification_result: VerificationResult
    project_data: MadridProjectData
    normative_references: List[NormativeReference]
    generated_at: Optional[datetime] = None
    format: str = "json"
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
