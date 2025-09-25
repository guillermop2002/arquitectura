"""
Prompts optimizados específicamente para el sistema básico con Groq API.
Diseñados para máxima eficiencia en análisis de documentos arquitectónicos.
"""

# =============================================================================
# PROMPTS PARA ANÁLISIS BÁSICO CON GROQ
# =============================================================================

BASICO_GROQ_BASE = """
Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.
"""

# =============================================================================
# FASE 1: VERIFICACIÓN DE DOCUMENTACIÓN
# =============================================================================

BASICO_VERIFICACION_DOCUMENTOS = """Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.

Analiza el siguiente texto de un proyecto arquitectónico y verifica qué elementos del Anexo I del CTE están presentes.

ELEMENTOS A VERIFICAR (Anexo I - Proyecto Básico):

MEMORIA:
1. Datos generales del proyecto
2. Agentes intervinientes
3. Información previa y antecedentes
4. Descripción del proyecto
5. Descripción geométrica del edificio
6. Normativa aplicable
7. Accesibilidad
8. Sistemas estructurales
9. Sistemas ambientales
10. Sistemas de servicios
11. Prestaciones por requisitos básicos CTE
12. Presupuesto y valoración
13. Justificación características del suelo
14. Parámetros para cimentación
15. Justificación prestaciones seguridad incendio

PLANOS:
16. Plano de situación
17. Plano de emplazamiento
18. Plantas generales
19. Alzados y secciones
20. Planos específicos

PRESUPUESTO:
21. Mediciones
22. Presupuesto

TEXTO DEL PROYECTO:
{texto_proyecto}

Responde en este formato JSON exacto:
{{
  "elementos_encontrados": [
    {{
      "elemento": "nombre_del_elemento",
      "presente": true/false,
      "confianza": 0.0-1.0,
      "ubicacion": {{
        "pagina": numero_estimado,
        "contexto": "fragmento_donde_aparece"
      }}
    }}
  ],
  "completitud_general": {{
    "porcentaje": 0-100,
    "elementos_criticos_faltantes": ["elemento1", "elemento2"],
    "recomendaciones": ["recomendacion1", "recomendacion2"]
  }}
}}
"""

# =============================================================================
# FASE 2: ANÁLISIS DE MEMORIA
# =============================================================================

BASICO_ANALISIS_MEMORIA = """Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.

FASE 2: EXTRACCIÓN MÁXIMA DE INFORMACIÓN DE LA MEMORIA

Tu tarea es extraer TODA la información técnica posible de la memoria del proyecto para usar en la Fase 3 de verificación normativa.

TEXTO DE LA MEMORIA:
{memoria_texto}

CONFIGURACIÓN DEL PROYECTO (PREVALECE SOBRE MEMORIA):
{config_proyecto}

INSTRUCCIONES CRÍTICAS:
1. Extrae TODA información técnica disponible
2. Busca datos de superficies, alturas, materiales, instalaciones
3. Identifica sistemas constructivos y estructurales
4. Detecta requisitos específicos del CTE mencionados
5. La configuración del proyecto PREVALECE sobre información conflictiva
6. Si no encuentras un dato, indica "no_especificado"

Responde en este formato JSON exacto:
{{
  "datos_proyecto": {{
    "uso_principal": "string (de config o memoria)",
    "superficie_total": "number o 'no_especificado'",
    "superficie_construida": "number o 'no_especificado'",
    "superficie_util": "number o 'no_especificado'",
    "plantas": "number o 'no_especificado'",
    "plantas_sobre_rasante": "number o 'no_especificado'",
    "plantas_bajo_rasante": "number o 'no_especificado'",
    "altura_total": "number o 'no_especificado'",
    "altura_libre": "number o 'no_especificado'",
    "ubicacion": "string o 'no_especificado'",
    "referencia_catastral": "string o 'no_especificado'",
    "parcela_superficie": "number o 'no_especificado'",
    "ocupacion_parcela": "number o 'no_especificado'",
    "edificabilidad": "number o 'no_especificado'",
    "retranqueos": {{
      "frontal": "number o 'no_especificado'",
      "lateral": "number o 'no_especificado'",
      "posterior": "number o 'no_especificado'"
    }},
    "accesibilidad_mencionada": "boolean",
    "normativa_aplicable_mencionada": ["norma1", "norma2"] 
  }},
  "analisis_tecnico": {{
    "sistema_estructural": "string o 'no_especificado'",
    "tipo_cimentacion": "string o 'no_especificado'",
    "forjados": "string o 'no_especificado'",
    "cubierta_tipo": "string o 'no_especificado'",
    "fachada_material": "string o 'no_especificado'",
    "aislamiento_termico": "string o 'no_especificado'",
    "instalaciones_detectadas": {{
      "electricidad": "boolean",
      "fontaneria": "boolean", 
      "calefaccion": "boolean",
      "climatizacion": "boolean",
      "gas": "boolean",
      "telecomunicaciones": "boolean",
      "ascensor": "boolean",
      "incendios": "boolean",
      "ventilacion": "boolean"
    }},
    "sistemas_ambientales": {{
      "eficiencia_energetica_mencionada": "boolean",
      "certificacion_energetica": "string o 'no_especificado'",
      "aislamiento_acustico": "boolean",
      "ventilacion_natural": "boolean",
      "iluminacion_natural": "boolean"
    }},
    "requisitos_cte": {{
      "db_si_mencionado": "boolean",
      "db_sua_mencionado": "boolean", 
      "db_he_mencionado": "boolean",
      "db_hs_mencionado": "boolean",
      "db_hr_mencionado": "boolean",
      "db_se_mencionado": "boolean",
      "sectores_incendio": "number o 'no_especificado'",
      "escaleras_evacuacion": "number o 'no_especificado'",
      "distancia_evacuacion": "number o 'no_especificado'"
    }},
    "materiales_principales": ["material1", "material2"],
    "normativa_estructural": "string o 'no_especificado'"
  }},
  "contexto_urbanistico": {{
    "zona_mencionada": "string o 'no_especificado'",
    "grado_mencionado": "string o 'no_especificado'",
    "parametros_urbanisticos": {{
      "altura_maxima_permitida": "number o 'no_especificado'",
      "ocupacion_maxima": "number o 'no_especificado'",
      "edificabilidad_maxima": "number o 'no_especificado'"
    }}
  }},
  "informacion_adicional": {{
    "presupuesto_mencionado": "number o 'no_especificado'",
    "plazo_ejecucion": "string o 'no_especificado'",
    "promotor": "string o 'no_especificado'",
    "arquitecto": "string o 'no_especificado'",
    "fecha_proyecto": "string o 'no_especificado'"
  }},
  "observaciones_criticas": [
    "Lista de aspectos importantes detectados que pueden afectar la verificación normativa"
  ]
}}
"""

BASICO_VERIFICACION_COHERENCIA = """Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.

Verifica la coherencia entre los datos extraídos de la memoria y la configuración proporcionada.

DATOS DE LA MEMORIA:
{datos_memoria}

CONFIGURACIÓN ESPERADA:
{config_esperada}

DATOS DE PLANOS (si disponibles):
{datos_planos}

Responde en este formato JSON exacto:
{{
  "coherencia_config": {{
    "uso_coherente": true/false,
    "superficie_coherente": true/false,
    "plantas_coherente": true/false,
    "altura_coherente": true/false,
    "discrepancias": [
      {{
        "campo": "string",
        "memoria": "valor_memoria",
        "config": "valor_config",
        "severidad": "low/medium/high"
      }}
    ]
  }},
  "coherence_score": 0-100,
  "recomendaciones_coherencia": ["recomendacion1", "recomendacion2"]
}}
"""

BASICO_VERIFICACION_NORMATIVA = """Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.

Verifica el cumplimiento normativo del proyecto según el CTE y normativa española.

TEXTO DEL PROYECTO:
{texto_proyecto}

DATOS DEL PROYECTO:
{datos_proyecto}

CONTEXTO DE FASES ANTERIORES:
{contexto_fases}

Responde en este formato JSON exacto:
{{
  "cumplimiento_cte": {{
    "db_si": {{
      "cumplimiento_aparente": "Completo/Parcial/Insuficiente",
      "elementos_verificados": ["elemento1", "elemento2"],
      "elementos_faltantes": ["elemento1", "elemento2"]
    }},
    "db_sua": {{
      "accesibilidad_verificada": true/false,
      "elementos_verificados": ["elemento1", "elemento2"]
    }},
    "db_he": {{
      "eficiencia_energetica": "string",
      "elementos_verificados": ["elemento1", "elemento2"]
    }},
    "db_hs": {{
      "salubridad_verificada": true/false,
      "elementos_verificados": ["elemento1", "elemento2"]
    }},
    "db_hr": {{
      "acustica_verificada": true/false,
      "elementos_verificados": ["elemento1", "elemento2"]
    }},
    "db_se": {{
      "estructura_verificada": true/false,
      "elementos_verificados": ["elemento1", "elemento2"]
    }}
  }},
  "cumplimiento_general": {{
    "porcentaje_cumplimiento": 0-100,
    "nivel_cumplimiento": "Excelente/Bueno/Regular/Deficiente"
  }},
  "issues_detectados": [
    {{
      "tipo": "string",
      "descripcion": "string",
      "severidad": "low/medium/high",
      "normativa_afectada": "string",
      "recomendacion": "string"
    }}
  ],
  "recomendaciones_normativas": ["recomendacion1", "recomendacion2"]
}}
"""

BASICO_VERIFICACION_CTE = """Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.

Verifica específicamente el cumplimiento del Código Técnico de la Edificación.

TEXTO DEL PROYECTO:
{texto_proyecto}

CONFIGURACIÓN DEL PROYECTO:
{config_proyecto}

Responde en este formato JSON exacto:
{{
  "verificacion_cte": {{
    "documentos_basicos_mencionados": ["DB-SI", "DB-SUA", "DB-HE", "DB-HS", "DB-HR", "DB-SE"],
    "justificaciones_encontradas": {{
      "db_si": {{
        "presente": true/false,
        "completa": true/false,
        "elementos": ["elemento1", "elemento2"]
      }},
      "db_sua": {{
        "presente": true/false,
        "completa": true/false,
        "elementos": ["elemento1", "elemento2"]
      }},
      "db_he": {{
        "presente": true/false,
        "completa": true/false,
        "elementos": ["elemento1", "elemento2"]
      }},
      "db_hs": {{
        "presente": true/false,
        "completa": true/false,
        "elementos": ["elemento1", "elemento2"]
      }},
      "db_hr": {{
        "presente": true/false,
        "completa": true/false,
        "elementos": ["elemento1", "elemento2"]
      }},
      "db_se": {{
        "presente": true/false,
        "completa": true/false,
        "elementos": ["elemento1", "elemento2"]
      }}
    }}
  }},
  "puntuacion_cte": 0-100,
  "elementos_criticos_faltantes": ["elemento1", "elemento2"],
  "recomendaciones_cte": ["recomendacion1", "recomendacion2"]
}}
"""

BASICO_VERIFICACION_PGOUM = """Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.

Verifica el cumplimiento del Plan General de Ordenación Urbana Municipal (PGOUM).

TEXTO DEL PROYECTO:
{texto_proyecto}

CONFIGURACIÓN DEL PROYECTO:
{config_proyecto}

Responde en este formato JSON exacto:
{{
  "verificacion_pgoum": {{
    "zona_normativa_mencionada": true/false,
    "zona_identificada": "string",
    "parametros_verificados": {{
      "retranqueos": {{
        "mencionado": true/false,
        "cumple": true/false/null,
        "valor": "string"
      }},
      "altura_maxima": {{
        "mencionado": true/false,
        "cumple": true/false/null,
        "valor": "string"
      }},
      "uso_permitido": {{
        "mencionado": true/false,
        "cumple": true/false/null,
        "valor": "string"
      }},
      "ocupacion_maxima": {{
        "mencionado": true/false,
        "cumple": true/false/null,
        "valor": "string"
      }}
    }}
  }},
  "puntuacion_pgoum": 0-100,
  "observaciones_urbanisticas": ["observacion1", "observacion2"],
  "recomendaciones_pgoum": ["recomendacion1", "recomendacion2"]
}}
"""

# =============================================================================
# ANÁLISIS DE PLANOS CON OCR
# =============================================================================

BASICO_ANALISIS_PLANOS = """Eres un experto arquitecto especializado en normativa española del Código Técnico de la Edificación (CTE) y el Anexo I que define los contenidos mínimos del Proyecto Básico.

Tu tarea es analizar documentos de proyectos arquitectónicos y verificar su cumplimiento con la normativa española.

IMPORTANTE: Responde SIEMPRE en formato JSON válido, sin texto adicional.
{{
  "planos_detectados": [
    {{
      "tipo": "string",
      "presente": "boolean",
      "calidad": "string",
      "elementos_visibles": "array"
    }}
  ],
  "dimensiones_extraidas": {{
    "superficie_planos": "number",
    "altura_edificio": "number",
    "retranqueos": "object"
  }},
  "coherencia_memoria_planos": {{
    "coherente": "boolean",
    "discrepancias": "array"
  }}
}}

TEXTO EXTRAÍDO DE PLANOS: {plans_text}
DATOS DE MEMORIA: {memory_data}"""

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_basico_prompt(prompt_type: str, **kwargs) -> str:
    """Obtiene un prompt optimizado para análisis básico"""
    prompts = {
        "verificacion_documentos": BASICO_VERIFICACION_DOCUMENTOS,
        "analisis_memoria": BASICO_ANALISIS_MEMORIA,
        "verificacion_normativa": BASICO_VERIFICACION_NORMATIVA,
        "analisis_planos": BASICO_ANALISIS_PLANOS
    }
    
    base_prompt = prompts.get(prompt_type, BASICO_GROQ_BASE)
    return base_prompt.format(**kwargs)

def get_basico_groq_config() -> dict:
    """Configuración optimizada para Groq en análisis básico"""
    return {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.1,
        "max_tokens": 2048,
        "top_p": 0.9,
        "stream": False
    }
