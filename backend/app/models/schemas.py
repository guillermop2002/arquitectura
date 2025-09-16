"""
Esquemas de datos para la aplicación de verificación arquitectónica.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

class SeverityLevel(Enum):
    """Niveles de severidad para los problemas encontrados."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProjectStatus(Enum):
    """Estados posibles de un proyecto."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Issue:
    """Representa un problema encontrado durante la verificación."""
    id: str
    title: str
    description: str
    severity: SeverityLevel
    category: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Question:
    """Representa una pregunta del sistema conversacional."""
    id: str
    text: str
    context: Optional[str] = None
    answer: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class VerificationResult:
    """Resultado de la verificación de un proyecto."""
    project_id: str
    status: ProjectStatus
    issues: List[Issue]
    score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    errors: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito como porcentaje."""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_checks / self.total_checks) * 100
    
    @property
    def critical_issues(self) -> List[Issue]:
        """Retorna solo los problemas críticos."""
        return [issue for issue in self.issues if issue.severity == SeverityLevel.CRITICAL]
    
    @property
    def high_priority_issues(self) -> List[Issue]:
        """Retorna problemas de alta prioridad (HIGH y CRITICAL)."""
        return [issue for issue in self.issues if issue.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]]
