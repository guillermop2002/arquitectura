"""
Prompts optimizados específicamente para Groq API (Llama 3.3 70B).
Diseñados para máxima eficiencia y precisión con el modelo de Groq.
"""

# =============================================================================
# PROMPTS OPTIMIZADOS PARA GROQ API
# =============================================================================

# Prompt base optimizado para Groq
GROQ_BASE_PROMPT = """Eres un experto arquitecto español especializado en CTE.
Responde SOLO en JSON válido, sin explicaciones adicionales.
Usa el siguiente formato exacto:"""

# =============================================================================
# EXTRACCIÓN DE DATOS ESTRUCTURADA
# =============================================================================

GROQ_PROJECT_DATA_EXTRACTION = f"""{GROQ_BASE_PROMPT}
{{
  "project_info": {{
    "building_type": "string",
    "total_area": "number",
    "floors": "number",
    "height": "number",
    "location": "string"
  }},
  "structural_data": {{
    "system": "string",
    "materials": "array",
    "fire_resistance": "object"
  }},
  "compliance_issues": {{
    "db_si": "array",
    "db_sua": "array", 
    "db_he": "array",
    "db_hr": "array"
  }}
}}

DOCUMENTOS: {{project_text}}"""

# =============================================================================
# ANÁLISIS DE CUMPLIMIENTO NORMATIVO
# =============================================================================

GROQ_COMPLIANCE_ANALYSIS = f"""{GROQ_BASE_PROMPT}
{{
  "compliance_summary": {{
    "overall_score": "number",
    "critical_issues": "number",
    "minor_issues": "number"
  }},
  "db_si_analysis": {{
    "evacuation_routes": "object",
    "fire_resistance": "object",
    "smoke_control": "object"
  }},
  "db_sua_analysis": {{
    "accessibility": "object",
    "safety_measures": "object",
    "structural_safety": "object"
  }},
  "recommendations": "array"
}}

DATOS DEL PROYECTO: {{project_data}}"""

# =============================================================================
# DETECCIÓN DE CONTRADICCIONES
# =============================================================================

GROQ_CONTRADICTION_DETECTION = f"""{GROQ_BASE_PROMPT}
{{
  "contradictions": [
    {{
      "type": "string",
      "description": "string",
      "severity": "string",
      "documents_involved": "array",
      "resolution": "string"
    }}
  ],
  "data_consistency": {{
    "memory_plans_match": "boolean",
    "calculations_consistent": "boolean",
    "specifications_complete": "boolean"
  }}
}}

MEMORIA: {{memory_text}}
PLANOS: {{plans_text}}"""

# =============================================================================
# CLASIFICACIÓN DE ELEMENTOS ARQUITECTÓNICOS
# =============================================================================

GROQ_ARCHITECTURAL_CLASSIFICATION = f"""{GROQ_BASE_PROMPT}
{{
  "elements": [
    {{
      "type": "string",
      "confidence": "number",
      "dimensions": "object",
      "properties": "object"
    }}
  ],
  "rooms": [
    {{
      "type": "string",
      "area": "number",
      "accessibility": "boolean"
    }}
  ]
}}

ELEMENTOS DETECTADOS: {{elements_data}}"""

# =============================================================================
# GENERACIÓN DE PREGUNTAS INTELIGENTES
# =============================================================================

GROQ_QUESTION_GENERATION = f"""{GROQ_BASE_PROMPT}
{{
  "questions": [
    {{
      "id": "string",
      "question": "string",
      "context": "string",
      "priority": "string",
      "expected_answer_type": "string"
    }}
  ],
  "ambiguities": [
    {{
      "description": "string",
      "impact": "string",
      "resolution_options": "array"
    }}
  ]
}}

ANÁLISIS PREVIO: {{analysis_data}}"""

# =============================================================================
# ANÁLISIS DE PLANOS CON VISIÓN POR COMPUTADOR
# =============================================================================

GROQ_PLAN_ANALYSIS = f"""{GROQ_BASE_PROMPT}
{{
  "detected_elements": [
    {{
      "element_type": "string",
      "coordinates": "array",
      "confidence": "number",
      "dimensions": "object"
    }}
  ],
  "room_analysis": [
    {{
      "room_id": "string",
      "room_type": "string",
      "area": "number",
      "accessibility_features": "array"
    }}
  ],
  "compliance_check": {{
    "door_widths": "array",
    "evacuation_distances": "array",
    "accessibility_issues": "array"
  }}
}}

ELEMENTOS DETECTADOS: {{cv_elements}}
CONTEXTO: {{plan_context}}"""

# =============================================================================
# OPTIMIZACIÓN DE RENDIMIENTO
# =============================================================================

# Prompts cortos para respuestas rápidas
GROQ_QUICK_CLASSIFICATION = """Clasifica: {text}
Respuesta: {{"type": "string", "confidence": "number"}}"""

GROQ_QUICK_VALIDATION = """Valida: {data}
Respuesta: {{"valid": "boolean", "issues": "array"}}"""

# Prompts para análisis en lotes
GROQ_BATCH_ANALYSIS = f"""{GROQ_BASE_PROMPT}
{{
  "results": [
    {{
      "item_id": "string",
      "analysis": "object",
      "confidence": "number"
    }}
  ]
}}

ITEMS: {{batch_data}}"""

# =============================================================================
# CONFIGURACIÓN ESPECÍFICA PARA GROQ
# =============================================================================

GROQ_MODEL_CONFIG = {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.1,
    "max_tokens": 4096,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

# Configuración para diferentes tipos de análisis
GROQ_ANALYSIS_CONFIGS = {
    "quick": {
        "temperature": 0.0,
        "max_tokens": 512,
        "timeout": 10
    },
    "detailed": {
        "temperature": 0.1,
        "max_tokens": 4096,
        "timeout": 30
    },
    "creative": {
        "temperature": 0.3,
        "max_tokens": 2048,
        "timeout": 20
    }
}

# =============================================================================
# UTILIDADES PARA OPTIMIZACIÓN
# =============================================================================

def get_optimized_prompt(prompt_type: str, **kwargs) -> str:
    """Obtiene un prompt optimizado para Groq basado en el tipo."""
    prompts = {
        "project_data": GROQ_PROJECT_DATA_EXTRACTION,
        "compliance": GROQ_COMPLIANCE_ANALYSIS,
        "contradictions": GROQ_CONTRADICTION_DETECTION,
        "classification": GROQ_ARCHITECTURAL_CLASSIFICATION,
        "questions": GROQ_QUESTION_GENERATION,
        "plan_analysis": GROQ_PLAN_ANALYSIS,
        "quick_classification": GROQ_QUICK_CLASSIFICATION,
        "quick_validation": GROQ_QUICK_VALIDATION,
        "batch_analysis": GROQ_BATCH_ANALYSIS
    }
    
    base_prompt = prompts.get(prompt_type, GROQ_BASE_PROMPT)
    return base_prompt.format(**kwargs)

def get_groq_config(analysis_type: str = "detailed") -> dict:
    """Obtiene la configuración optimizada para Groq."""
    config = GROQ_MODEL_CONFIG.copy()
    config.update(GROQ_ANALYSIS_CONFIGS.get(analysis_type, {}))
    return config

# =============================================================================
# PROMPTS ESPECÍFICOS POR FASE
# =============================================================================

# Fase 1: Análisis de documentos
GROQ_PHASE1_DOCUMENT_ANALYSIS = f"""{GROQ_BASE_PROMPT}
{{
  "document_structure": {{
    "sections": "array",
    "completeness": "object",
    "quality": "number"
  }},
  "extracted_data": {{
    "general_info": "object",
    "technical_specs": "object",
    "calculations": "object"
  }},
  "next_steps": "array"
}}

DOCUMENTO: {{document_text}}"""

# Fase 2: Análisis de planos
GROQ_PHASE2_PLAN_ANALYSIS = f"""{GROQ_BASE_PROMPT}
{{
  "plan_elements": {{
    "walls": "array",
    "doors": "array",
    "windows": "array",
    "rooms": "array"
  }},
  "measurements": {{
    "areas": "array",
    "distances": "array",
    "dimensions": "array"
  }},
  "compliance_issues": "array"
}}

PLANOS: {{plan_data}}"""

# Fase 3: Integración
GROQ_PHASE3_INTEGRATION = f"""{GROQ_BASE_PROMPT}
{{
  "integration_analysis": {{
    "consistency": "object",
    "completeness": "object",
    "accuracy": "object"
  }},
  "correlation_results": {{
    "memory_plan_match": "boolean",
    "calculation_accuracy": "number",
    "specification_completeness": "number"
  }},
  "recommendations": "array"
}}

MEMORIA: {{memory_data}}
PLANOS: {{plan_data}}"""

# Fase 4: Sistema conversacional
GROQ_PHASE4_CONVERSATION = f"""{GROQ_BASE_PROMPT}
{{
  "response": {{
    "type": "string",
    "content": "string",
    "confidence": "number",
    "next_questions": "array"
  }},
  "context_update": {{
    "new_information": "object",
    "resolved_ambiguities": "array"
  }}
}}

CONTEXTO: {{conversation_context}}
PREGUNTA: {{user_question}}"""

# Fase 5: Optimización
GROQ_PHASE5_OPTIMIZATION = f"""{GROQ_BASE_PROMPT}
{{
  "optimization_analysis": {{
    "performance_metrics": "object",
    "bottlenecks": "array",
    "improvements": "array"
  }},
  "production_readiness": {{
    "score": "number",
    "issues": "array",
    "recommendations": "array"
  }}
}}

SISTEMA: {{system_data}}"""
