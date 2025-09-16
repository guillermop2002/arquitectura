"""
Advanced rule engine for building regulation compliance checking.
Implements sophisticated rule evaluation with context-aware reasoning.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import networkx as nx
from datetime import datetime

from .config import get_config
from .logging_config import get_logger
from .error_handling import handle_exception
from ..models.schemas import Issue, SeverityLevel

logger = get_logger(__name__)

class RuleType(Enum):
    """Types of rules in the system."""
    DIMENSIONAL = "dimensional"
    MATERIAL = "material"
    ACCESSIBILITY = "accessibility"
    FIRE_SAFETY = "fire_safety"
    ENERGY_EFFICIENCY = "energy_efficiency"
    STRUCTURAL = "structural"
    INSTALLATION = "installation"

class RuleOperator(Enum):
    """Operators for rule conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    IN_RANGE = "in_range"
    NOT_IN_RANGE = "not_in_range"

@dataclass
class RuleCondition:
    """Represents a condition in a rule."""
    field: str
    operator: RuleOperator
    value: Any
    context: Optional[str] = None
    confidence: float = 1.0

@dataclass
class RuleAction:
    """Represents an action when a rule is violated."""
    action_type: str
    message: str
    severity: SeverityLevel
    reference: str
    suggestion: Optional[str] = None

@dataclass
class ComplianceRule:
    """Represents a compliance rule."""
    rule_id: str
    name: str
    description: str
    rule_type: RuleType
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    applicable_uses: List[str]
    cte_reference: str
    madrid_specific: bool = False
    priority: int = 1
    enabled: bool = True

@dataclass
class RuleEvaluationResult:
    """Result of rule evaluation."""
    rule_id: str
    passed: bool
    confidence: float
    violations: List[str]
    suggestions: List[str]
    context: Dict[str, Any]

class AdvancedRuleEngine:
    """
    Advanced rule engine for building regulation compliance checking.
    Implements sophisticated rule evaluation with context-aware reasoning.
    """
    
    def __init__(self):
        """Initialize the advanced rule engine."""
        self.config = get_config()
        
        # Rule storage
        self.rules: Dict[str, ComplianceRule] = {}
        self.rule_graph = nx.DiGraph()
        
        # Evaluation context
        self.evaluation_context = {}
        
        # Performance tracking
        self._evaluation_stats = {
            'rules_evaluated': 0,
            'violations_found': 0,
            'rules_passed': 0,
            'evaluation_time': 0.0
        }
        
        # Initialize rules
        self._initialize_building_rules()
        
        logger.info("Advanced rule engine initialized")
    
    def _initialize_building_rules(self):
        """Initialize comprehensive building regulation rules."""
        try:
            # Load CTE rules
            self._load_cte_rules()
            
            # Load Madrid-specific rules
            self._load_madrid_rules()
            
            # Load accessibility rules
            self._load_accessibility_rules()
            
            # Load fire safety rules
            self._load_fire_safety_rules()
            
            # Load energy efficiency rules
            self._load_energy_efficiency_rules()
            
            logger.info(f"Loaded {len(self.rules)} compliance rules")
            
        except Exception as e:
            logger.error(f"Error initializing building rules: {e}")
            raise
    
    def _load_cte_rules(self):
        """Load CTE (Código Técnico de la Edificación) rules."""
        cte_rules = [
            # DB-SI: Fire Safety Rules
            ComplianceRule(
                rule_id="DB-SI-001",
                name="Resistencia al fuego de elementos estructurales",
                description="Los elementos estructurales deben tener la resistencia al fuego adecuada según el uso y altura del edificio",
                rule_type=RuleType.FIRE_SAFETY,
                conditions=[
                    RuleCondition("building_use", RuleOperator.IN, ["residencial", "comercial", "oficinas"]),
                    RuleCondition("height", RuleOperator.GREATER_THAN, 0),
                    RuleCondition("fire_resistance", RuleOperator.CONTAINS, "RF-")
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="Falta especificación de resistencia al fuego de elementos estructurales",
                        severity=SeverityLevel.HIGH,
                        reference="DB-SI Artículo 3.1"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas", "publico"],
                cte_reference="DB-SI",
                priority=1
            ),
            
            ComplianceRule(
                rule_id="DB-SI-002",
                name="Ancho mínimo de escaleras de evacuación",
                description="Las escaleras de evacuación deben tener un ancho mínimo según el aforo",
                rule_type=RuleType.FIRE_SAFETY,
                conditions=[
                    RuleCondition("stair_type", RuleOperator.EQUALS, "evacuacion"),
                    RuleCondition("occupancy", RuleOperator.GREATER_THAN, 50),
                    RuleCondition("stair_width", RuleOperator.LESS_THAN, 1.0)
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="El ancho de escalera de evacuación es insuficiente para el aforo",
                        severity=SeverityLevel.HIGH,
                        reference="DB-SI Artículo 4.1",
                        suggestion="Aumentar el ancho de escalera a mínimo 1.0m"
                    )
                ],
                applicable_uses=["comercial", "oficinas", "publico"],
                cte_reference="DB-SI",
                priority=1
            ),
            
            # DB-SU: Safety of Use Rules
            ComplianceRule(
                rule_id="DB-SU-001",
                name="Pendiente máxima de rampas",
                description="Las rampas no pueden tener pendiente superior al 8%",
                rule_type=RuleType.ACCESSIBILITY,
                conditions=[
                    RuleCondition("element_type", RuleOperator.EQUALS, "rampa"),
                    RuleCondition("slope", RuleOperator.GREATER_THAN, 8.0)
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="La pendiente de la rampa excede el máximo permitido (8%)",
                        severity=SeverityLevel.HIGH,
                        reference="DB-SU Artículo 2.1",
                        suggestion="Reducir la pendiente de la rampa a máximo 8%"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas", "publico"],
                cte_reference="DB-SU",
                priority=1
            ),
            
            ComplianceRule(
                rule_id="DB-SU-002",
                name="Dimensiones de escaleras",
                description="Las escaleras deben cumplir con las dimensiones mínimas de huella y contrahuella",
                rule_type=RuleType.ACCESSIBILITY,
                conditions=[
                    RuleCondition("element_type", RuleOperator.EQUALS, "escalera"),
                    RuleCondition("tread", RuleOperator.LESS_THAN, 28),
                    RuleCondition("riser", RuleOperator.GREATER_THAN, 18)
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="Las dimensiones de la escalera no cumplen con los requisitos mínimos",
                        severity=SeverityLevel.MEDIUM,
                        reference="DB-SU Artículo 2.2",
                        suggestion="Ajustar huella (mín. 28cm) y contrahuella (máx. 18cm)"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas", "publico"],
                cte_reference="DB-SU",
                priority=2
            ),
            
            # DB-HE: Energy Efficiency Rules
            ComplianceRule(
                rule_id="DB-HE-001",
                name="Transmitancia térmica de cerramientos",
                description="Los cerramientos deben cumplir con los límites de transmitancia térmica",
                rule_type=RuleType.ENERGY_EFFICIENCY,
                conditions=[
                    RuleCondition("element_type", RuleOperator.IN, ["muro", "cubierta", "suelo"]),
                    RuleCondition("thermal_transmittance", RuleOperator.GREATER_THAN, 0.57)
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="La transmitancia térmica excede el límite permitido",
                        severity=SeverityLevel.HIGH,
                        reference="DB-HE Artículo 2.1",
                        suggestion="Mejorar el aislamiento térmico del cerramiento"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas"],
                cte_reference="DB-HE",
                priority=1
            ),
            
            ComplianceRule(
                rule_id="DB-HE-002",
                name="Demanda energética del edificio",
                description="El edificio no puede superar la demanda energética máxima",
                rule_type=RuleType.ENERGY_EFFICIENCY,
                conditions=[
                    RuleCondition("energy_demand", RuleOperator.GREATER_THAN, 30.0)
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="La demanda energética excede el límite máximo permitido",
                        severity=SeverityLevel.HIGH,
                        reference="DB-HE Artículo 3.1",
                        suggestion="Mejorar la eficiencia energética del edificio"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas"],
                cte_reference="DB-HE",
                priority=1
            )
        ]
        
        # Add rules to engine
        for rule in cte_rules:
            self.add_rule(rule)
    
    def _load_madrid_rules(self):
        """Load Madrid-specific rules."""
        madrid_rules = [
            ComplianceRule(
                rule_id="MAD-001",
                name="Ascensor requerido en Madrid",
                description="Los edificios de más de 2 plantas requieren ascensor en Madrid",
                rule_type=RuleType.ACCESSIBILITY,
                conditions=[
                    RuleCondition("building_use", RuleOperator.IN, ["residencial", "comercial", "oficinas"]),
                    RuleCondition("floors", RuleOperator.GREATER_THAN, 2),
                    RuleCondition("elevator", RuleOperator.NOT_CONTAINS, "ascensor")
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="Se requiere ascensor para edificios de más de 2 plantas en Madrid",
                        severity=SeverityLevel.HIGH,
                        reference="Ordenanza de Accesibilidad de Madrid",
                        suggestion="Instalar ascensor accesible"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas"],
                cte_reference="Madrid",
                madrid_specific=True,
                priority=1
            ),
            
            ComplianceRule(
                rule_id="MAD-002",
                name="Aislamiento acústico en Madrid",
                description="Madrid requiere información específica sobre aislamiento acústico",
                rule_type=RuleType.MATERIAL,
                conditions=[
                    RuleCondition("acoustic_insulation", RuleOperator.NOT_CONTAINS, "aislamiento acústico")
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="Falta información de aislamiento acústico requerida en Madrid",
                        severity=SeverityLevel.MEDIUM,
                        reference="Ordenanza de Ruido de Madrid",
                        suggestion="Incluir especificaciones de aislamiento acústico"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas"],
                cte_reference="Madrid",
                madrid_specific=True,
                priority=2
            )
        ]
        
        # Add Madrid rules to engine
        for rule in madrid_rules:
            self.add_rule(rule)
    
    def _load_accessibility_rules(self):
        """Load accessibility-specific rules."""
        accessibility_rules = [
            ComplianceRule(
                rule_id="ACC-001",
                name="Ancho mínimo de puertas accesibles",
                description="Las puertas en itinerarios accesibles deben tener ancho mínimo de 0.8m",
                rule_type=RuleType.ACCESSIBILITY,
                conditions=[
                    RuleCondition("door_type", RuleOperator.EQUALS, "accesible"),
                    RuleCondition("door_width", RuleOperator.LESS_THAN, 0.8)
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="El ancho de puerta accesible es insuficiente (mín. 0.8m)",
                        severity=SeverityLevel.HIGH,
                        reference="DB-SU Artículo 2.1",
                        suggestion="Aumentar el ancho de puerta a mínimo 0.8m"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas", "publico"],
                cte_reference="DB-SU",
                priority=1
            ),
            
            ComplianceRule(
                rule_id="ACC-002",
                name="Altura de pasamanos",
                description="Los pasamanos deben estar entre 90-100cm de altura",
                rule_type=RuleType.ACCESSIBILITY,
                conditions=[
                    RuleCondition("element_type", RuleOperator.EQUALS, "pasamanos"),
                    RuleCondition("handrail_height", RuleOperator.NOT_IN_RANGE, [90, 100])
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="La altura del pasamanos debe estar entre 90-100cm",
                        severity=SeverityLevel.MEDIUM,
                        reference="DB-SU Artículo 2.3",
                        suggestion="Ajustar la altura del pasamanos a 90-100cm"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas", "publico"],
                cte_reference="DB-SU",
                priority=2
            )
        ]
        
        # Add accessibility rules to engine
        for rule in accessibility_rules:
            self.add_rule(rule)
    
    def _load_fire_safety_rules(self):
        """Load fire safety-specific rules."""
        fire_safety_rules = [
            ComplianceRule(
                rule_id="FIRE-001",
                name="Distancia máxima de evacuación",
                description="La distancia máxima de evacuación no puede exceder los límites establecidos",
                rule_type=RuleType.FIRE_SAFETY,
                conditions=[
                    RuleCondition("evacuation_distance", RuleOperator.GREATER_THAN, 15),
                    RuleCondition("building_use", RuleOperator.IN, ["residencial", "comercial"])
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="La distancia de evacuación excede el máximo permitido (15m)",
                        severity=SeverityLevel.HIGH,
                        reference="DB-SI Artículo 4.1",
                        suggestion="Reducir la distancia de evacuación o añadir salidas adicionales"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas", "publico"],
                cte_reference="DB-SI",
                priority=1
            ),
            
            ComplianceRule(
                rule_id="FIRE-002",
                name="Sistemas de protección contra incendios",
                description="Los edificios de uso público requieren sistemas de protección contra incendios",
                rule_type=RuleType.FIRE_SAFETY,
                conditions=[
                    RuleCondition("building_use", RuleOperator.EQUALS, "publico"),
                    RuleCondition("total_area", RuleOperator.GREATER_THAN, 1000),
                    RuleCondition("fire_protection_systems", RuleOperator.NOT_CONTAINS, "extintor")
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="Se requieren sistemas de protección contra incendios para edificios públicos",
                        severity=SeverityLevel.HIGH,
                        reference="DB-SI Artículo 5.1",
                        suggestion="Instalar sistemas de protección contra incendios"
                    )
                ],
                applicable_uses=["publico"],
                cte_reference="DB-SI",
                priority=1
            )
        ]
        
        # Add fire safety rules to engine
        for rule in fire_safety_rules:
            self.add_rule(rule)
    
    def _load_energy_efficiency_rules(self):
        """Load energy efficiency-specific rules."""
        energy_rules = [
            ComplianceRule(
                rule_id="ENERGY-001",
                name="Instalaciones térmicas eficientes",
                description="Las instalaciones térmicas deben ser eficientes",
                rule_type=RuleType.ENERGY_EFFICIENCY,
                conditions=[
                    RuleCondition("thermal_installations", RuleOperator.NOT_CONTAINS, "eficiente")
                ],
                actions=[
                    RuleAction(
                        action_type="violation",
                        message="Falta información sobre eficiencia de instalaciones térmicas",
                        severity=SeverityLevel.MEDIUM,
                        reference="DB-HE Artículo 4.1",
                        suggestion="Incluir especificaciones de eficiencia energética"
                    )
                ],
                applicable_uses=["residencial", "comercial", "oficinas"],
                cte_reference="DB-HE",
                priority=2
            )
        ]
        
        # Add energy efficiency rules to engine
        for rule in energy_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: ComplianceRule):
        """Add a rule to the engine."""
        self.rules[rule.rule_id] = rule
        
        # Add to rule graph
        self.rule_graph.add_node(rule.rule_id, **rule.__dict__)
        
        # Add relationships based on rule type
        for other_rule_id, other_rule in self.rules.items():
            if other_rule_id != rule.rule_id:
                if rule.rule_type == other_rule.rule_type:
                    self.rule_graph.add_edge(rule.rule_id, other_rule_id, relationship="same_type")
                
                if any(use in other_rule.applicable_uses for use in rule.applicable_uses):
                    self.rule_graph.add_edge(rule.rule_id, other_rule_id, relationship="same_use")
    
    @handle_exception
    def evaluate_rules(self, project_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[RuleEvaluationResult]:
        """
        Evaluate all applicable rules against project data.
        
        Args:
            project_data: Project data to evaluate
            context: Additional context for evaluation
            
        Returns:
            List of rule evaluation results
        """
        try:
            start_time = datetime.now()
            results = []
            
            # Set evaluation context
            self.evaluation_context = project_data.copy()
            if context:
                self.evaluation_context.update(context)
            
            # Get applicable rules
            applicable_rules = self._get_applicable_rules(project_data)
            
            # Evaluate each rule
            for rule in applicable_rules:
                if rule.enabled:
                    result = self._evaluate_single_rule(rule)
                    results.append(result)
                    
                    self._evaluation_stats['rules_evaluated'] += 1
                    if result.passed:
                        self._evaluation_stats['rules_passed'] += 1
                    else:
                        self._evaluation_stats['violations_found'] += 1
            
            # Calculate evaluation time
            evaluation_time = (datetime.now() - start_time).total_seconds()
            self._evaluation_stats['evaluation_time'] += evaluation_time
            
            logger.info(f"Evaluated {len(results)} rules in {evaluation_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating rules: {e}")
            return []
    
    def _get_applicable_rules(self, project_data: Dict[str, Any]) -> List[ComplianceRule]:
        """Get rules applicable to the project."""
        applicable_rules = []
        
        building_use = project_data.get('building_use', '').lower()
        is_madrid = project_data.get('location', '').lower().find('madrid') != -1
        
        for rule in self.rules.values():
            # Check if rule applies to building use
            if 'general' in rule.applicable_uses or building_use in rule.applicable_uses:
                # Check Madrid-specific rules
                if rule.madrid_specific and not is_madrid:
                    continue
                
                applicable_rules.append(rule)
        
        # Sort by priority
        applicable_rules.sort(key=lambda x: x.priority)
        
        return applicable_rules
    
    def _evaluate_single_rule(self, rule: ComplianceRule) -> RuleEvaluationResult:
        """Evaluate a single rule against project data."""
        try:
            violations = []
            suggestions = []
            confidence = 1.0
            
            # Evaluate each condition
            for condition in rule.conditions:
                condition_result = self._evaluate_condition(condition)
                
                if not condition_result['passed']:
                    violations.append(condition_result['message'])
                    confidence *= condition_result['confidence']
            
            # Determine if rule passed
            passed = len(violations) == 0
            
            # Get suggestions from actions
            for action in rule.actions:
                if action.suggestion and not passed:
                    suggestions.append(action.suggestion)
            
            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                passed=passed,
                confidence=confidence,
                violations=violations,
                suggestions=suggestions,
                context=self.evaluation_context
            )
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                passed=False,
                confidence=0.0,
                violations=[f"Error evaluating rule: {str(e)}"],
                suggestions=[],
                context={}
            )
    
    def _evaluate_condition(self, condition: RuleCondition) -> Dict[str, Any]:
        """Evaluate a single condition."""
        try:
            field_value = self._get_field_value(condition.field)
            
            if field_value is None:
                return {
                    'passed': False,
                    'message': f"Field '{condition.field}' not found in project data",
                    'confidence': 0.0
                }
            
            # Apply operator
            result = self._apply_operator(field_value, condition.operator, condition.value)
            
            return {
                'passed': result,
                'message': f"Condition {condition.field} {condition.operator.value} {condition.value} failed" if not result else "",
                'confidence': condition.confidence
            }
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return {
                'passed': False,
                'message': f"Error evaluating condition: {str(e)}",
                'confidence': 0.0
            }
    
    def _get_field_value(self, field: str) -> Any:
        """Get field value from evaluation context."""
        # Handle nested fields (e.g., "building.height")
        if '.' in field:
            parts = field.split('.')
            value = self.evaluation_context
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        
        # Handle direct fields
        return self.evaluation_context.get(field)
    
    def _apply_operator(self, field_value: Any, operator: RuleOperator, expected_value: Any) -> bool:
        """Apply operator to field value and expected value."""
        try:
            if operator == RuleOperator.EQUALS:
                return field_value == expected_value
            elif operator == RuleOperator.NOT_EQUALS:
                return field_value != expected_value
            elif operator == RuleOperator.GREATER_THAN:
                return float(field_value) > float(expected_value)
            elif operator == RuleOperator.LESS_THAN:
                return float(field_value) < float(expected_value)
            elif operator == RuleOperator.GREATER_EQUAL:
                return float(field_value) >= float(expected_value)
            elif operator == RuleOperator.LESS_EQUAL:
                return float(field_value) <= float(expected_value)
            elif operator == RuleOperator.CONTAINS:
                return expected_value in str(field_value).lower()
            elif operator == RuleOperator.NOT_CONTAINS:
                return expected_value not in str(field_value).lower()
            elif operator == RuleOperator.IN_RANGE:
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    return float(expected_value[0]) <= float(field_value) <= float(expected_value[1])
                return False
            elif operator == RuleOperator.NOT_IN_RANGE:
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    return not (float(expected_value[0]) <= float(field_value) <= float(expected_value[1]))
                return True
            else:
                return False
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error applying operator {operator} to {field_value}: {e}")
            return False
    
    def generate_issues_from_results(self, results: List[RuleEvaluationResult]) -> List[Issue]:
        """Generate issues from rule evaluation results."""
        issues = []
        
        for result in results:
            if not result.passed:
                rule = self.rules[result.rule_id]
                
                for action in rule.actions:
                    issue = Issue(
                        title=action.message,
                        description=f"Regla: {rule.name}\\nViolaciones: {', '.join(result.violations)}",
                        severity=action.severity,
                        reference=action.reference,
                        file_name="Sistema de reglas",
                        page_number=0,
                        confidence=result.confidence
                    )
                    issues.append(issue)
        
        return issues
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get rule engine statistics."""
        return {
            **self._evaluation_stats,
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
            'rule_types': len(set(r.rule_type for r in self.rules.values())),
            'graph_nodes': self.rule_graph.number_of_nodes(),
            'graph_edges': self.rule_graph.number_of_edges()
        }
    
    def export_rules(self, filepath: str):
        """Export rules to JSON file."""
        try:
            rules_data = {}
            for rule_id, rule in self.rules.items():
                rules_data[rule_id] = {
                    'name': rule.name,
                    'description': rule.description,
                    'rule_type': rule.rule_type.value,
                    'conditions': [
                        {
                            'field': c.field,
                            'operator': c.operator.value,
                            'value': c.value,
                            'context': c.context,
                            'confidence': c.confidence
                        } for c in rule.conditions
                    ],
                    'actions': [
                        {
                            'action_type': a.action_type,
                            'message': a.message,
                            'severity': a.severity.value,
                            'reference': a.reference,
                            'suggestion': a.suggestion
                        } for a in rule.actions
                    ],
                    'applicable_uses': rule.applicable_uses,
                    'cte_reference': rule.cte_reference,
                    'madrid_specific': rule.madrid_specific,
                    'priority': rule.priority,
                    'enabled': rule.enabled
                }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Rules exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting rules: {e}")
    
    def import_rules(self, filepath: str):
        """Import rules from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            for rule_id, rule_data in rules_data.items():
                # Reconstruct rule from data
                conditions = [
                    RuleCondition(
                        field=c['field'],
                        operator=RuleOperator(c['operator']),
                        value=c['value'],
                        context=c.get('context'),
                        confidence=c.get('confidence', 1.0)
                    ) for c in rule_data['conditions']
                ]
                
                actions = [
                    RuleAction(
                        action_type=a['action_type'],
                        message=a['message'],
                        severity=SeverityLevel(a['severity']),
                        reference=a['reference'],
                        suggestion=a.get('suggestion')
                    ) for a in rule_data['actions']
                ]
                
                rule = ComplianceRule(
                    rule_id=rule_id,
                    name=rule_data['name'],
                    description=rule_data['description'],
                    rule_type=RuleType(rule_data['rule_type']),
                    conditions=conditions,
                    actions=actions,
                    applicable_uses=rule_data['applicable_uses'],
                    cte_reference=rule_data['cte_reference'],
                    madrid_specific=rule_data.get('madrid_specific', False),
                    priority=rule_data.get('priority', 1),
                    enabled=rule_data.get('enabled', True)
                )
                
                self.add_rule(rule)
            
            logger.info(f"Rules imported from {filepath}")
            
        except Exception as e:
            logger.error(f"Error importing rules: {e}")
