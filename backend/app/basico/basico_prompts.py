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

BASICO_VERIFICACION_DOCUMENTOS = f"""{BASICO_GROQ_BASE}

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
{{texto_proyecto}}

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

BASICO_ANALISIS_MEMORIA = f"""{BASICO_GROQ_BASE}

Analiza la memoria del proyecto y extrae los datos técnicos principales.

TEXTO DE LA MEMORIA:
{{{{memoria_texto}}}}

CONFIGURACIÓN DEL PROYECTO:
{{{{config_proyecto}}}}

Responde en este formato JSON exacto:
{{
  "datos_proyecto": {{
    "uso_principal": "string",
    "superficie_total": number,
    "superficie_construida": number,
    "plantas": number,
    "altura_total": number,
    "ubicacion": "string",
    "referencia_catastral": "string"
  }},
  "analisis_tecnico": {{
    "sistema_estructural": "string",
    "tipo_cimentacion": "string",
    "instalaciones": ["instalacion1", "instalacion2"],
    "materiales_principales": ["material1", "material2"]
  }},
  "normativa_mencionada": ["norma1", "norma2"],
  "observaciones": ["observacion1", "observacion2"]
}}
"""

BASICO_VERIFICACION_COHERENCIA = f"""{BASICO_GROQ_BASE}

Verifica la coherencia entre los datos extraídos de la memoria y la configuración proporcionada.

DATOS DE LA MEMORIA:
{{{{datos_memoria}}}}

CONFIGURACIÓN ESPERADA:
{{{{config_esperada}}}}

DATOS DE PLANOS (si disponibles):
{{{{datos_planos}}}}

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

BASICO_VERIFICACION_NORMATIVA = f"""{BASICO_GROQ_BASE}

Verifica el cumplimiento normativo del proyecto según el CTE y normativa española.

TEXTO DEL PROYECTO:
{{texto_proyecto}}

DATOS DEL PROYECTO:
{{{{datos_proyecto}}}}

CONTEXTO DE FASES ANTERIORES:
{{{{contexto_fases}}}}

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

BASICO_VERIFICACION_CTE = f"""{BASICO_GROQ_BASE}

Verifica específicamente el cumplimiento del Código Técnico de la Edificación.

TEXTO DEL PROYECTO:
{{texto_proyecto}}

CONFIGURACIÓN DEL PROYECTO:
{{{{config_proyecto}}}}

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

BASICO_VERIFICACION_PGOUM = f"""{BASICO_GROQ_BASE}

Verifica el cumplimiento del Plan General de Ordenación Urbana Municipal (PGOUM).

TEXTO DEL PROYECTO:
{{texto_proyecto}}

CONFIGURACIÓN DEL PROYECTO:
{{{{config_proyecto}}}}

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

BASICO_ANALISIS_PLANOS = f"""{BASICO_GROQ_BASE}
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

TEXTO EXTRAÍDO DE PLANOS: {{{{plans_text}}}}
DATOS DE MEMORIA: {{{{memory_data}}}}"""

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
