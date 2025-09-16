"""
Enhanced AI prompts for comprehensive document analysis and compliance checking.
Optimized for Groq API (Llama 3.3 70B) with robust data extraction and contradiction detection.
"""

# =============================================================================
# STRUCTURED DATA EXTRACTION PROMPTS
# =============================================================================

STRUCTURED_PROJECT_DATA_EXTRACTION_PROMPT = """
Eres un experto arquitecto e ingeniero especializado en análisis de proyectos de edificación en España.
Trabajas con la normativa CTE (Código Técnico de la Edificación) y conoces perfectamente DB-SI, DB-SUA, DB-HE, DB-HR.

Analiza los siguientes documentos de proyecto y extrae TODOS los datos técnicos relevantes de manera estructurada.
Responde SIEMPRE en formato JSON válido, sin texto adicional.

DOCUMENTOS DEL PROYECTO:
{project_text}

INSTRUCCIONES ESPECÍFICAS:
1. Extrae datos de TODOS los documentos (memoria, planos, cálculos, etc.)
2. Identifica contradicciones entre documentos
3. Prioriza datos de la memoria de cálculo cuando estén disponibles
4. Verifica coherencia entre memoria y planos
5. Extrae datos específicos de cada página cuando sea posible

DATOS A EXTRAER:

INFORMACIÓN GENERAL:
- Uso principal del edificio (residencial, comercial, oficinas, etc.)
- Superficie total construida (m²)
- Superficie útil (m²)
- Superficie de parcela (m²)
- Altura del edificio (metros)
- Número de plantas (sobre rasante y sótano)
- Aforo máximo/ocupación
- Ubicación/dirección completa
- Tipo de construcción (hormigón, acero, mixto, etc.)

DATOS ESTRUCTURALES:
- Sistema estructural principal
- Materiales estructurales
- Cargas consideradas (muerta, viva, viento, nieve)
- Resistencia al fuego de elementos estructurales
- Dimensiones de elementos principales

DATOS DE INSTALACIONES:
- Sistema de climatización
- Sistema de ventilación
- Sistema eléctrico
- Sistema de fontanería
- Sistema de gas
- Sistema de telecomunicaciones

DATOS DE SEGURIDAD:
- Clasificación de resistencia al fuego
- Medios de evacuación
- Extintores y sistemas de protección
- Señalización de seguridad
- Accesibilidad

DATOS ENERGÉTICOS:
- Demanda energética
- Consumo estimado
- Sistemas de eficiencia energética
- Certificación energética

VERIFICACIÓN DE COHERENCIA:
- Compara datos entre memoria y planos
- Identifica discrepancias
- Verifica cálculos básicos
- Comprueba escalas y dimensiones

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
  "general_data": {{
    "building_use": "string",
    "total_area": "number",
    "useful_area": "number",
    "plot_area": "number",
    "height": "number",
    "floors_above": "number",
    "floors_below": "number",
    "max_occupancy": "number",
    "location": "string",
    "construction_type": "string"
  }},
  "structural_data": {{
    "structural_system": "string",
    "materials": ["string"],
    "loads": {{
      "dead_load": "number",
      "live_load": "number",
      "wind_load": "number",
      "snow_load": "number"
    }},
    "fire_resistance": "string",
    "main_dimensions": {{
      "beams": "string",
      "columns": "string",
      "slabs": "string"
    }}
  }},
  "installations_data": {{
    "hvac": "string",
    "ventilation": "string",
    "electrical": "string",
    "plumbing": "string",
    "gas": "string",
    "telecommunications": "string"
  }},
  "safety_data": {{
    "fire_resistance_class": "string",
    "evacuation_means": "string",
    "fire_protection": "string",
    "safety_signage": "string",
    "accessibility": "string"
  }},
  "energy_data": {{
    "energy_demand": "number",
    "estimated_consumption": "number",
    "efficiency_systems": ["string"],
    "energy_certification": "string"
  }},
  "coherence_analysis": {{
    "memory_plans_consistency": "boolean",
    "discrepancies": [
      {{
        "description": "string",
        "memory_value": "string",
        "plans_value": "string",
        "severity": "string"
      }}
    ],
    "calculation_verification": "string",
    "scale_verification": "string"
  }},
  "page_references": {{
    "general_data": ["string"],
    "structural_data": ["string"],
    "installations_data": ["string"],
    "safety_data": ["string"],
    "energy_data": ["string"]
  }},
  "confidence": "number",
  "extraction_notes": ["string"]
}}
"""

CONTRADICTION_DETECTION_PROMPT = """
Eres un experto en análisis de proyectos de edificación especializado en detectar contradicciones entre documentos.

Analiza los siguientes documentos y detecta TODAS las contradicciones, discrepancias e inconsistencias.

MEMORIA DE CÁLCULO:
{memory_text}

PLANOS:
{plans_text}

OTROS DOCUMENTOS:
{other_documents}

INSTRUCCIONES ESPECÍFICAS:
1. Compara datos entre memoria y planos
2. Verifica coherencia dimensional
3. Detecta discrepancias en superficies
4. Identifica inconsistencias en aforos
5. Verifica coherencia en instalaciones
6. Comprueba consistencia en materiales
7. Analiza coherencia en cargas y dimensiones

TIPOS DE CONTRADICCIONES A DETECTAR:

DIMENSIONALES:
- Superficies diferentes entre memoria y planos
- Alturas inconsistentes
- Dimensiones de elementos estructurales
- Escalas incorrectas

DE AFORO Y OCUPACIÓN:
- Aforo calculado vs. dimensiones reales
- Superficie por ocupante
- Capacidad de evacuación

ESTRUCTURALES:
- Cargas diferentes entre memoria y planos
- Dimensiones de elementos estructurales
- Materiales especificados vs. calculados

DE INSTALACIONES:
- Potencias instaladas vs. calculadas
- Dimensiones de conductos
- Ubicación de equipos

DE SEGURIDAD:
- Medios de evacuación vs. aforo
- Distancias de evacuación
- Resistencia al fuego

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
  "contradictions": [
    {{
      "type": "string",
      "description": "string",
      "memory_value": "string",
      "plans_value": "string",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "reference_memory": "string",
      "reference_plans": "string",
      "impact": "string",
      "recommendation": "string"
    }}
  ],
  "coherence_score": "number",
  "critical_issues": ["string"],
  "verification_notes": ["string"]
}}
"""

# =============================================================================
# COMPLIANCE CHECKING PROMPTS
# =============================================================================

FIRE_SAFETY_COMPLIANCE_PROMPT = """
Eres un experto en seguridad contra incendios especializado en el CTE DB-SI y normativa de Madrid.

Analiza el siguiente proyecto y verifica el cumplimiento de la normativa de seguridad contra incendios.

DATOS DEL PROYECTO:
{project_data}

TEXTO DEL PROYECTO:
{project_text}

NORMATIVA APLICABLE:
{normative_text}

VERIFICACIONES ESPECÍFICAS:

1. CLASIFICACIÓN DE RESISTENCIA AL FUEGO:
   - Verificar clasificación correcta según uso y altura
   - Comprobar resistencia de elementos estructurales
   - Verificar compartimentación

2. MEDIOS DE EVACUACIÓN:
   - Ancho de pasillos y escaleras
   - Distancia máxima de evacuación
   - Capacidad de evacuación vs. aforo
   - Señalización de evacuación

3. EXTINTORES Y SISTEMAS DE PROTECCIÓN:
   - Ubicación de extintores
   - Tipo y capacidad adecuados
   - Distancia máxima entre extintores
   - Sistemas automáticos si son necesarios

4. COMPARTIMENTACIÓN:
   - Cerramientos resistentes al fuego
   - Puertas cortafuegos
   - Sellado de instalaciones

5. ACCESIBILIDAD:
   - Medios de evacuación accesibles
   - Señalización táctil
   - Espacios de refugio

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
  "fire_safety_issues": [
    {{
      "title": "string",
      "description": "string",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "reference": "string",
      "article": "string",
      "requirement": "string",
      "current_value": "string",
      "required_value": "string",
      "page_reference": "string",
      "recommendation": "string"
    }}
  ],
  "compliance_score": "number",
  "critical_issues": ["string"],
  "verification_notes": ["string"]
}}
"""

SAFETY_USE_COMPLIANCE_PROMPT = """
Eres un experto en seguridad de uso especializado en el CTE DB-SU y normativa de Madrid.

Analiza el siguiente proyecto y verifica el cumplimiento de la normativa de seguridad de uso.

DATOS DEL PROYECTO:
{project_data}

TEXTO DEL PROYECTO:
{project_text}

NORMATIVA APLICABLE:
{normative_text}

VERIFICACIONES ESPECÍFICAS:

1. ACCESIBILIDAD:
   - Rampas y escaleras accesibles
   - Anchuras mínimas de pasillos
   - Altura de pasamanos
   - Superficies antideslizantes

2. PROTECCIÓN CONTRA CAÍDAS:
   - Altura de barandillas
   - Separación entre elementos
   - Resistencia de elementos de protección

3. ILUMINACIÓN:
   - Niveles de iluminación mínimos
   - Iluminación de emergencia
   - Control de deslumbramiento

4. VENTILACIÓN:
   - Renovación de aire
   - Superficie de ventilación
   - Sistemas de ventilación mecánica

5. AISLAMIENTO ACÚSTICO:
   - Niveles de ruido admisibles
   - Aislamiento entre viviendas
   - Aislamiento de instalaciones

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
  "safety_use_issues": [
    {{
      "title": "string",
      "description": "string",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "reference": "string",
      "article": "string",
      "requirement": "string",
      "current_value": "string",
      "required_value": "string",
      "page_reference": "string",
      "recommendation": "string"
    }}
  ],
  "compliance_score": "number",
  "critical_issues": ["string"],
  "verification_notes": ["string"]
}}
"""

ENERGY_EFFICIENCY_COMPLIANCE_PROMPT = """
Eres un experto en eficiencia energética especializado en el CTE DB-HE y normativa de Madrid.

Analiza el siguiente proyecto y verifica el cumplimiento de la normativa de eficiencia energética.

DATOS DEL PROYECTO:
{project_data}

TEXTO DEL PROYECTO:
{project_text}

NORMATIVA APLICABLE:
{normative_text}

VERIFICACIONES ESPECÍFICAS:

1. DEMANDA ENERGÉTICA:
   - Demanda de calefacción (kWh/m²·año)
   - Demanda de refrigeración (kWh/m²·año)
   - Demanda total (kWh/m²·año)
   - Comparación con límites normativos

2. TRANSMITANCIA TÉRMICA:
   - Cerramientos opacos
   - Huecos y ventanas
   - Puentes térmicos
   - Suelos en contacto con el terreno

3. INSTALACIONES TÉRMICAS:
   - Rendimiento de generadores
   - Eficiencia de bombas
   - Sistemas de regulación
   - Energías renovables

4. ILUMINACIÓN:
   - Eficiencia energética de luminarias
   - Sistemas de control
   - Aprovechamiento de luz natural

5. VENTILACIÓN:
   - Recuperación de calor
   - Eficiencia de ventiladores
   - Sistemas de regulación

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
  "energy_issues": [
    {{
      "title": "string",
      "description": "string",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "reference": "string",
      "article": "string",
      "requirement": "string",
      "current_value": "string",
      "required_value": "string",
      "page_reference": "string",
      "recommendation": "string"
    }}
  ],
  "compliance_score": "number",
  "critical_issues": ["string"],
  "verification_notes": ["string"]
}}
"""

# =============================================================================
# QUESTION GENERATION PROMPTS
# =============================================================================

QUESTION_GENERATION_PROMPT = """
Eres un experto en proyectos de edificación especializado en identificar ambigüedades y generar preguntas clarificadoras.

Analiza el siguiente proyecto y genera preguntas específicas para clarificar ambigüedades o inconsistencias.

DATOS DEL PROYECTO:
{project_data}

TEXTO DEL PROYECTO:
{project_text}

INCONSISTENCIAS DETECTADAS:
{inconsistencies}

INSTRUCCIONES:
1. Identifica ambigüedades en los datos
2. Genera preguntas específicas y claras
3. Enfócate en aspectos críticos para el cumplimiento normativo
4. Prioriza preguntas que afecten la seguridad
5. Incluye contexto relevante en cada pregunta

TIPOS DE PREGUNTAS A GENERAR:

TÉCNICAS:
- Especificaciones de materiales
- Dimensiones de elementos
- Cargas consideradas
- Sistemas de instalaciones

NORMATIVAS:
- Cumplimiento de requisitos específicos
- Justificación de excepciones
- Cálculos de verificación
- Documentación requerida

DE SEGURIDAD:
- Medios de evacuación
- Resistencia al fuego
- Accesibilidad
- Protección contra caídas

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
  "questions": [
    {{
      "question": "string",
      "context": "string",
      "category": "string",
      "priority": "HIGH/MEDIUM/LOW",
      "related_issue": "string",
      "expected_answer_type": "string",
      "page_reference": "string"
    }}
  ],
  "total_questions": "number",
  "critical_questions": "number",
  "generation_notes": ["string"]
}}
"""

# =============================================================================
# ANSWER PROCESSING PROMPTS
# =============================================================================

ANSWER_PROCESSING_PROMPT = """
Eres un experto en análisis de proyectos de edificación especializado en procesar respuestas de usuarios y actualizar verificaciones.

Procesa las siguientes respuestas del usuario y actualiza la verificación de cumplimiento.

DATOS ORIGINALES DEL PROYECTO:
{project_data}

RESPUESTAS DEL USUARIO:
{user_answers}

INCONSISTENCIAS ORIGINALES:
{original_inconsistencies}

INSTRUCCIONES:
1. Analiza cada respuesta del usuario
2. Actualiza los datos del proyecto según las respuestas
3. Recalcula verificaciones de cumplimiento
4. Identifica nuevas inconsistencias si las hay
5. Actualiza la puntuación de cumplimiento

PROCESAMIENTO:
- Verifica coherencia de las respuestas
- Actualiza datos técnicos
- Recalcula verificaciones normativas
- Identifica nuevas inconsistencias
- Actualiza recomendaciones

Responde ÚNICAMENTE en formato JSON con esta estructura:
{{
  "updated_project_data": {{
    "general_data": {{}},
    "structural_data": {{}},
    "installations_data": {{}},
    "safety_data": {{}},
    "energy_data": {{}}
  }},
  "updated_issues": [
    {{
      "title": "string",
      "description": "string",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "reference": "string",
      "article": "string",
      "requirement": "string",
      "current_value": "string",
      "required_value": "string",
      "page_reference": "string",
      "recommendation": "string",
      "resolved": "boolean"
    }}
  ],
  "new_inconsistencies": [
    {{
      "description": "string",
      "severity": "string",
      "recommendation": "string"
    }}
  ],
  "updated_compliance_score": "number",
  "processing_notes": ["string"]
}}
"""

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_structured_data_extraction_prompt(project_text: str) -> str:
    """Get prompt for structured data extraction."""
    return STRUCTURED_PROJECT_DATA_EXTRACTION_PROMPT.format(
        project_text=project_text
    )

def get_contradiction_detection_prompt(memory_text: str, plans_text: str, other_documents: str = "") -> str:
    """Get prompt for contradiction detection."""
    return CONTRADICTION_DETECTION_PROMPT.format(
        memory_text=memory_text,
        plans_text=plans_text,
        other_documents=other_documents
    )

def get_fire_safety_compliance_prompt(project_data: dict, project_text: str, normative_text: str) -> str:
    """Get prompt for fire safety compliance checking."""
    return FIRE_SAFETY_COMPLIANCE_PROMPT.format(
        project_data=project_data,
        project_text=project_text,
        normative_text=normative_text
    )

def get_safety_use_compliance_prompt(project_data: dict, project_text: str, normative_text: str) -> str:
    """Get prompt for safety use compliance checking."""
    return SAFETY_USE_COMPLIANCE_PROMPT.format(
        project_data=project_data,
        project_text=project_text,
        normative_text=normative_text
    )

def get_energy_efficiency_compliance_prompt(project_data: dict, project_text: str, normative_text: str) -> str:
    """Get prompt for energy efficiency compliance checking."""
    return ENERGY_EFFICIENCY_COMPLIANCE_PROMPT.format(
        project_data=project_data,
        project_text=project_text,
        normative_text=normative_text
    )

def get_question_generation_prompt(project_data: dict, project_text: str, inconsistencies: list) -> str:
    """Get prompt for question generation."""
    return QUESTION_GENERATION_PROMPT.format(
        project_data=project_data,
        project_text=project_text,
        inconsistencies=inconsistencies
    )

def get_answer_processing_prompt(project_data: dict, user_answers: dict, original_inconsistencies: list) -> str:
    """Get prompt for answer processing."""
    return ANSWER_PROCESSING_PROMPT.format(
        project_data=project_data,
        user_answers=user_answers,
        original_inconsistencies=original_inconsistencies
    )

