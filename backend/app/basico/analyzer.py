import json
from typing import Dict, Any, List
from pathlib import Path
from .anexo_verifier import BasicoAnexoVerifier
from .ocr_processor import BasicoOCRProcessor
from .ai_client import BasicoAIClient
from .normative_loader import BasicoNormativeLoader
from .basico_prompts import *
import logging

# Import advanced OCR only if needed
try:
    from .advanced_ocr_processor import AdvancedOCRProcessor
    ADVANCED_OCR_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger("basico.analyzer")
    logger.warning(f"⚠️ Advanced OCR no disponible: {e}")
    ADVANCED_OCR_AVAILABLE = False
    AdvancedOCRProcessor = None

# Configurar logger detallado
logger = logging.getLogger("basico.analyzer")
logger.setLevel(logging.DEBUG)

# Configurar formato detallado para logs
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class BasicoAnalyzer:
    def __init__(self, use_advanced_ocr: bool = False):
        self.anexo_verifier = BasicoAnexoVerifier()
        self.ocr_processor = BasicoOCRProcessor()
        
        # Only initialize advanced OCR if available and requested
        if use_advanced_ocr and ADVANCED_OCR_AVAILABLE:
            self.advanced_ocr_processor = AdvancedOCRProcessor()
            self.use_advanced_ocr = True
        else:
            self.advanced_ocr_processor = None
            self.use_advanced_ocr = False
            if use_advanced_ocr and not ADVANCED_OCR_AVAILABLE:
                logger.warning("⚠️ Advanced OCR solicitado pero no disponible, usando OCR estándar")
        
        self.ai_client = BasicoAIClient()
        self.normative_loader = BasicoNormativeLoader()

        logger.info(f"🔧 BasicoAnalyzer inicializado con OCR {'avanzado' if self.use_advanced_ocr else 'estándar'}")
    
    async def fase1_verificar_documentacion(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """FASE 1: Verificar presencia de elementos según anexo1.json con IA"""

        logger.info("🚀 INICIANDO FASE 1: Verificación de documentación")
        logger.info(f"📁 Archivos a procesar: {len(session_data.get('files', []))}")

        # 1. Extraer texto de todos los documentos
        logger.info("📄 Extrayendo texto de documentos...")
        all_texts = self._extract_all_texts(session_data)
        combined_text = self._combine_texts(all_texts)
        logger.info(f"✅ Texto extraído: {len(combined_text)} caracteres")

        # 2. Verificación con IA usando Groq
        logger.info("🤖 Iniciando verificación con IA...")
        ai_verification = await self._verify_with_ai(combined_text)
        logger.info(f"✅ Verificación IA completada: {ai_verification.get('completion_percentage', 0)}% completitud")

        # 3. Verificación tradicional con anexo
        logger.info("📋 Iniciando verificación tradicional...")
        traditional_verification = self.anexo_verifier.verify_session_documents(session_data)
        logger.info(f"✅ Verificación tradicional completada: {traditional_verification.get('completion_percentage', 0)}% completitud")

        # 4. Combinar resultados
        logger.info("🔄 Combinando resultados de verificación...")
        combined_verification = self._combine_verifications(ai_verification, traditional_verification)
        
        return {
            "fase": 1,
            "tipo": "verificacion_documentacion",
            "ai_verification": ai_verification,
            "traditional_verification": traditional_verification,
            "combined_results": combined_verification,
            "next_phase_ready": combined_verification.get("completion_percentage", 0) > 50,
            "timestamp": self._get_timestamp()
        }
    
    async def fase2_analizar_memoria(self, session_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """FASE 2: Análisis detallado de memoria con IA"""

        logger.info("🚀 INICIANDO FASE 2: Análisis de memoria y planos")
        logger.info(f"⚙️ Configuración recibida: {list(config.keys())}")

        # 1. Extraer texto de memoria específicamente
        logger.info("📖 Extrayendo texto de memoria...")
        memoria_texts = self._extract_memoria_texts(session_data)
        logger.info(f"✅ Memoria extraída: {len(memoria_texts)} archivos procesados")

        # 2. Análisis con IA
        logger.info("🤖 Iniciando análisis de memoria con IA...")
        ai_analysis = await self._analyze_memoria_with_ai(memoria_texts, config)
        logger.info(f"✅ Análisis de memoria completado")

        # 3. Análisis de planos (si existen)
        logger.info("📐 Iniciando análisis de planos...")
        planos_analysis = await self._analyze_planos_with_ai(session_data)
        logger.info(f"✅ Análisis de planos completado")
        if 'dimensiones_extraidas' in planos_analysis:
            dim_data = planos_analysis['dimensiones_extraidas']
            logger.info(f"   📏 Dimensiones extraídas: {dim_data.get('total_dimensions', 0)}")
            logger.info(f"   📐 Áreas extraídas: {dim_data.get('total_areas', 0)}")

        # 4. Verificación de coherencia
        logger.info("🔍 Verificando coherencia entre memoria y configuración...")
        coherence_check = await self._check_coherence_with_ai(ai_analysis, config, planos_analysis)
        logger.info(f"✅ Verificación de coherencia completada: {coherence_check.get('coherence_score', 0)}% coherencia")
        
        return {
            "fase": 2,
            "tipo": "analisis_memoria",
            "user_config": config,  # Guardar configuración original del usuario
            "datos_proyecto": ai_analysis.get("datos_proyecto", {}),
            "analisis_tecnico": ai_analysis.get("analisis_tecnico", {}),
            "contexto_urbanistico": ai_analysis.get("contexto_urbanistico", {}),
            "informacion_adicional": ai_analysis.get("informacion_adicional", {}),
            "observaciones_criticas": ai_analysis.get("observaciones_criticas", []),
            "planos_analysis": planos_analysis,
            "coherencia_config": coherence_check,
            "coherence_score": coherence_check.get("coherence_score", 0),
            "next_phase_ready": coherence_check.get("coherence_score", 0) > 70,
            "timestamp": self._get_timestamp()
        }
    
    async def fase3_verificar_normativa(self, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """FASE 3: Verificación normativa con IA"""

        logger.info("🚀 INICIANDO FASE 3: Verificación normativa")

        # 1. Preparar datos para análisis normativo
        logger.info("📋 Preparando datos para análisis normativo...")
        project_text = self._prepare_project_text(session_data)
        fase2_result = context.get('fase2', {})
        logger.info(f"✅ Datos preparados: {len(project_text)} caracteres de texto del proyecto")

        # 2. Extraer configuración del usuario de la Fase 2 (config original del usuario)
        logger.info("⚙️ Extrayendo configuración del usuario...")
        user_config = fase2_result.get('user_config', {})
        datos_proyecto = fase2_result.get('datos_proyecto', {})
        analisis_tecnico = fase2_result.get('analisis_tecnico', {})
        logger.info(f"✅ Configuración extraída: {list(user_config.keys())}")

        # 3. Crear contexto enriquecido combinando datos extraídos y configuración del usuario
        logger.info("🔄 Creando contexto enriquecido...")
        enriched_context = {
            "user_config": user_config,  # Configuración original del usuario
            "datos_proyecto": datos_proyecto,  # Datos extraídos de la memoria
            "analisis_tecnico": analisis_tecnico,  # Análisis técnico de la memoria
            "planos_analysis": fase2_result.get('planos_analysis', {}),
            "coherence_check": fase2_result.get('coherencia_config', {})
        }
        logger.info(f"✅ Contexto enriquecido creado con {len(enriched_context)} elementos")

        # 4. Verificación normativa con IA usando contexto enriquecido
        logger.info("📖 Iniciando verificación normativa general...")
        normative_verification = await self._verify_normative_with_ai(project_text, user_config, enriched_context)
        logger.info(f"✅ Verificación normativa completada")

        # 5. Verificación CTE específica
        logger.info("🏗️ Iniciando verificación CTE específica...")
        cte_verification = await self._verify_cte_with_ai(project_text, user_config)
        logger.info(f"✅ Verificación CTE completada")

        # 6. Verificación PGOUM (si aplica)
        logger.info("🏙️ Iniciando verificación PGOUM...")
        pgoum_verification = await self._verify_pgoum_with_ai(project_text, user_config)
        logger.info(f"✅ Verificación PGOUM completada")

        # 7. Calcular puntuación final
        logger.info("📊 Calculando puntuación final...")
        final_score = self._calculate_final_score(normative_verification, cte_verification, pgoum_verification)
        logger.info(f"✅ Puntuación final calculada: {final_score}%")
        
        return {
            "fase": 3,
            "tipo": "verificacion_normativa",
            "normative_verification": normative_verification,
            "cte_verification": cte_verification,
            "pgoum_verification": pgoum_verification,
            "final_compliance_score": final_score,
            "production_ready": final_score > 75,
            "context_used": {
                "user_config": user_config,
                "datos_extraidos": datos_proyecto,
                "analisis_tecnico": analisis_tecnico
            },
            "timestamp": self._get_timestamp()
        }
    
    def _extract_all_texts(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer texto de todos los archivos de la sesión con OCR mejorado"""
        all_texts = {}

        for file_info in session_data.get("files", []):
            file_path = file_info["path"]
            if file_path.lower().endswith('.pdf'):

                # Decidir qué OCR usar según el tipo de archivo
                category = file_info.get("category", "")

                if self.use_advanced_ocr and self.advanced_ocr_processor and self._should_use_advanced_ocr(category):
                    logger.info(f"🚀 Usando OCR avanzado para: {file_info['filename']} (categoría: {category})")
                    text_data = self.advanced_ocr_processor.extract_text_from_pdf_advanced(file_path)
                else:
                    logger.info(f"📄 Usando OCR estándar para: {file_info['filename']} (categoría: {category})")
                    text_data = self.ocr_processor.extract_text_from_pdf(file_path)

                all_texts[file_info["filename"]] = text_data

        return all_texts

    def _should_use_advanced_ocr(self, category: str) -> bool:
        """Determinar si usar OCR avanzado según la categoría del archivo"""

        # Usar OCR avanzado para planos y documentos técnicos
        advanced_categories = [
            "Planos_Situacion_Emplazamiento",
            "Planos_Plantas_Generales",
            "Planos_Alzados_Secciones",
            "Planos_Incendios",
            "Planos_Instalaciones",
            "Documentacion_Adicional"
        ]

        return category in advanced_categories
    
    def _combine_texts(self, all_texts: Dict[str, Any]) -> str:
        """Combinar todos los textos en uno solo"""
        combined = []
        for filename, text_data in all_texts.items():
            combined.append(f"=== {filename} ===")
            combined.append(text_data.get("full_text", ""))
            combined.append("\n")
        
        return "\n".join(combined)
    
    async def _verify_with_ai(self, text: str) -> Dict[str, Any]:
        """Verificar documentos usando IA"""
        prompt = BASICO_VERIFICACION_DOCUMENTOS.format(
            texto_proyecto=text[:8000]  # Limitar texto para API
        )
        
        response = await self.ai_client.generate_response(prompt)
        
        return self._parse_ai_json_response(response)
    
    def _combine_verifications(self, ai_result: Dict[str, Any], traditional_result: Dict[str, Any]) -> Dict[str, Any]:
        """Combinar resultados de verificación IA y tradicional"""
        
        # Usar el mejor resultado de cada método
        ai_completion = ai_result.get("completitud_general", {}).get("porcentaje", 0)
        traditional_completion = traditional_result.get("statistics", {}).get("completion_percentage", 0)
        
        # Promedio ponderado (IA 70%, tradicional 30%)
        combined_completion = (ai_completion * 0.7) + (traditional_completion * 0.3)
        
        return {
            "completion_percentage": combined_completion,
            "ai_confidence": ai_result.get("completitud_general", {}).get("porcentaje", 0) / 100,
            "traditional_confidence": traditional_completion / 100,
            "found_elements": traditional_result.get("statistics", {}).get("found_elements", 0),
            "total_elements": traditional_result.get("statistics", {}).get("total_elements", 22),
            "missing_elements": traditional_result.get("statistics", {}).get("missing_elements", 0),
            "recommendations": ai_result.get("completitud_general", {}).get("recomendaciones", [])
        }
    
    def _extract_memoria_texts(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer textos de TODOS los archivos para análisis inteligente con IA"""
        all_texts = {}
        
        # Extraer texto de TODOS los archivos PDF disponibles
        for file_info in session_data.get("files", []):
            file_path = file_info["path"]
            if file_path.lower().endswith('.pdf'):
                text_data = self.ocr_processor.extract_text_from_pdf(file_path)
                all_texts[file_info["filename"]] = text_data
        
        return all_texts
    
    async def _analyze_memoria_with_ai(self, memoria_texts: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis inteligente de TODOS los documentos con IA - EXTRACCIÓN COMPLETA"""
        combined_memoria = self._combine_texts(memoria_texts)
        
        # Crear prompt inteligente que analiza TODO el contenido
        intelligent_prompt = f"""
        {BASICO_GROQ_BASE}
        
        ANÁLISIS INTELIGENTE COMPLETO DE DOCUMENTACIÓN DEL PROYECTO
        
        CONFIGURACIÓN DEL PROYECTO:
        {json.dumps(config, indent=2)}
        
        DOCUMENTACIÓN COMPLETA DEL PROYECTO:
        {combined_memoria[:15000]}
        
        INSTRUCCIONES PARA ANÁLISIS INTELIGENTE:
        
        Tu tarea es analizar TODA la documentación y extraer CUALQUIER información que pueda ser relevante para la verificación normativa posterior. No te limites a buscar solo lo obvio, sino que debes:
        
        1. **INFORMACIÓN TÉCNICA GENERAL:**
           - Superficies, dimensiones, alturas, volúmenes
           - Número de plantas, altura total del edificio
           - Tipos de uso y distribución de espacios
           - Capacidad de ocupación
        
        2. **SISTEMAS CONSTRUCTIVOS:**
           - Estructura (hormigón, acero, madera, mixta)
           - Cimentación y sistemas de apoyo
           - Muros, forjados, cubiertas
           - Materiales de construcción utilizados
        
        3. **INSTALACIONES:**
           - Eléctricas (potencia, distribución, iluminación)
           - Fontanería y saneamiento
           - Climatización y ventilación
           - Gas, telecomunicaciones
           - Sistemas de seguridad
        
        4. **ACCESIBILIDAD:**
           - Rampas, ascensores, plataformas
           - Anchos de paso, puertas
           - Aseos adaptados
           - Señalización táctil y visual
        
        5. **SEGURIDAD CONTRA INCENDIOS:**
           - Compartimentación
           - Salidas de emergencia
           - Sistemas de detección y extinción
           - Materiales ignífugos
           - Distancias de evacuación
        
        6. **EFICIENCIA ENERGÉTICA:**
           - Aislamiento térmico
           - Sistemas de calefacción/refrigeración
           - Ventilación natural
           - Energías renovables
           - Certificaciones energéticas
        
        7. **PARÁMETROS URBANÍSTICOS:**
           - Ocupación del suelo
           - Edificabilidad
           - Retranqueos y distancias
           - Alturas máximas
           - Usos permitidos
        
        8. **NORMATIVAS MENCIONADAS:**
           - Referencias a CTE, PGOUM, normativas locales
           - Códigos técnicos aplicables
           - Reglamentos específicos
        
        9. **INFORMACIÓN ADICIONAL:**
           - Condicionantes del terreno
           - Impacto ambiental
           - Servidumbres
           - Licencias y permisos
        
        10. **OBSERVACIONES CRÍTICAS:**
            - Inconsistencias detectadas
            - Información faltante
            - Posibles incumplimientos
            - Recomendaciones técnicas
        
        Devuelve un JSON con la siguiente estructura:
        {{
            "datos_proyecto": {{
                "superficie_construida": "valor en m²",
                "superficie_util": "valor en m²",
                "plantas": "número de plantas",
                "altura_total": "valor en m",
                "altura_por_planta": "valor en m",
                "uso_principal": "tipo de uso detectado",
                "usos_secundarios": ["lista de usos"],
                "capacidad_ocupacion": "número de personas"
            }},
            "analisis_tecnico": {{
                "sistema_estructural": "tipo de estructura",
                "cimentacion": "tipo de cimentación",
                "materiales_principales": ["lista de materiales"],
                "sistemas_constructivos": {{
                    "muros": "descripción",
                    "forjados": "descripción",
                    "cubierta": "descripción"
                }}
            }},
            "instalaciones_detectadas": {{
                "electricas": {{
                    "potencia_total": "valor en kW",
                    "distribucion": "descripción",
                    "iluminacion": "descripción"
                }},
                "fontaneria": {{
                    "abastecimiento": "descripción",
                    "saneamiento": "descripción"
                }},
                "climatizacion": {{
                    "calefaccion": "descripción",
                    "refrigeracion": "descripción",
                    "ventilacion": "descripción"
                }},
                "gas": "descripción",
                "telecomunicaciones": "descripción"
            }},
            "accesibilidad": {{
                "rampas": "descripción",
                "ascensores": "descripción",
                "anchos_paso": "descripción",
                "aseos_adaptados": "descripción",
                "señalizacion": "descripción"
            }},
            "seguridad_incendios": {{
                "compartimentacion": "descripción",
                "salidas_emergencia": "descripción",
                "sistemas_deteccion": "descripción",
                "sistemas_extincion": "descripción",
                "materiales_ignifugos": "descripción"
            }},
            "eficiencia_energetica": {{
                "aislamiento_termico": "descripción",
                "sistemas_climatizacion": "descripción",
                "ventilacion_natural": "descripción",
                "energias_renovables": "descripción",
                "certificacion_energetica": "descripción"
            }},
            "parametros_urbanisticos": {{
                "ocupacion_suelo": "valor en m²",
                "edificabilidad": "valor en m²",
                "retranqueos": "descripción",
                "alturas_maximas": "descripción",
                "usos_permitidos": ["lista de usos"]
            }},
            "normativas_mencionadas": {{
                "cte": ["referencias encontradas"],
                "pgoum": ["referencias encontradas"],
                "normativas_locales": ["referencias encontradas"],
                "codigos_tecnicos": ["referencias encontradas"]
            }},
            "informacion_adicional": {{
                "condicionantes_terreno": "descripción",
                "impacto_ambiental": "descripción",
                "servidumbres": "descripción",
                "licencias_permisos": "descripción"
            }},
            "observaciones_criticas": [
                "lista de observaciones importantes"
            ],
            "coherencia_configuracion": {{
                "uso_detectado_vs_configurado": "comparación",
                "norma_zonal_detectada": "si se menciona",
                "grado_detectado": "si se menciona",
                "inconsistencias": ["lista de inconsistencias"]
            }}
        }}
        """
        
        response = await self.ai_client.generate_response(intelligent_prompt, max_tokens=3000)
        
        return self._parse_ai_json_response(response)
    
    async def _analyze_planos_with_ai(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis inteligente de planos con IA - EXTRACCIÓN AVANZADA DE DIMENSIONES Y OCR MEJORADO"""
        logger.info("📐 Iniciando análisis detallado de planos...")

        planos_texts = {}
        dimensional_data = {}
        technical_info_data = {}
        files_processed = 0

        # Extraer texto de TODOS los archivos PDF con OCR avanzado
        for file_info in session_data.get("files", []):
            file_path = file_info["path"]
            if file_path.lower().endswith('.pdf'):
                category = file_info.get("category", "")
                files_processed += 1

                # Usar OCR avanzado para planos
                if self.use_advanced_ocr and self.advanced_ocr_processor and self._should_use_advanced_ocr(category):
                    logger.info(f"🔍 Análisis avanzado de planos: {file_info['filename']} (categoría: {category})")
                    text_data = self.advanced_ocr_processor.extract_text_from_pdf_advanced(file_path)

                    # Extraer información técnica avanzada
                    if "technical_info" in text_data:
                        technical_info_data[file_info["filename"]] = text_data["technical_info"]
                        tech_info = text_data["technical_info"]
                        logger.info(f"   ✅ Info técnica extraída: {len(tech_info.get('dimensions', []))} dimensiones, "
                                   f"{len(tech_info.get('areas', []))} áreas, {len(tech_info.get('materials', []))} materiales")

                    # Extraer análisis dimensional avanzado
                    if "dimensional_analysis" in text_data:
                        dimensional_data[file_info["filename"]] = text_data["dimensional_analysis"]
                        dim_analysis = text_data["dimensional_analysis"]
                        logger.info(f"   ✅ Análisis dimensional: {dim_analysis.get('total_dimensions', 0)} dimensiones totales")

                else:
                    logger.info(f"📄 Análisis estándar de planos: {file_info['filename']} (categoría: {category})")
                    # Usar OCR estándar
                    text_data = self.ocr_processor.extract_text_from_pdf(file_path)

                    # Extraer datos dimensionales estándar
                    if "dimensional_analysis" in text_data:
                        dimensional_data[file_info["filename"]] = text_data["dimensional_analysis"]

                planos_texts[file_info["filename"]] = text_data

        logger.info(f"✅ Procesados {files_processed} archivos de planos")
        
        if not planos_texts:
            return {"message": "No se encontraron archivos para analizar", "dimensiones_extraidas": {}}
        
        combined_planos = self._combine_texts(planos_texts)
        
        # Combinar análisis dimensional de todos los archivos
        combined_dimensional_analysis = self._combine_dimensional_analysis(dimensional_data)

        # Combinar información técnica avanzada
        combined_technical_info = self._combine_technical_info(technical_info_data)

        # Crear prompt inteligente para análisis completo de planos con datos avanzados
        intelligent_planos_prompt = f"""
        {BASICO_GROQ_BASE}

        ANÁLISIS INTELIGENTE AVANZADO DE PLANOS CON OCR MEJORADO Y EXTRACCIÓN TÉCNICA

        DOCUMENTACIÓN GRÁFICA COMPLETA:
        {combined_planos[:10000]}

        ANÁLISIS DIMENSIONAL EXTRAÍDO POR OCR:
        {json.dumps(combined_dimensional_analysis, indent=2)[:2000]}

        INFORMACIÓN TÉCNICA AVANZADA EXTRAÍDA:
        {json.dumps(combined_technical_info, indent=2)[:3000]}
        
        INSTRUCCIONES PARA ANÁLISIS INTELIGENTE DE PLANOS:
        
        Analiza TODA la documentación gráfica y extrae CUALQUIER información técnica que pueda ser relevante para la verificación normativa. Usa los datos dimensionales extraídos por OCR como base para tu análisis. Busca información en:
        
        1. **DIMENSIONES Y MEDIDAS (usando datos OCR):**
           - Superficies totales y por planta (usar áreas extraídas)
           - Alturas totales y por planta (usar alturas extraídas)
           - Dimensiones de espacios, habitaciones, pasillos (usar dimensiones extraídas)
           - Cotas, escalas, medidas en planos (usar análisis estadístico)
           - Volúmenes construidos (calcular a partir de dimensiones)
        
        2. **ELEMENTOS CONSTRUCTIVOS:**
           - Tipos de estructura (pilares, vigas, muros)
           - Sistemas de cimentación
           - Tipos de forjados y cubiertas
           - Materiales constructivos indicados
           - Espesores de muros y elementos
        
        3. **INSTALACIONES TÉCNICAS:**
           - Redes eléctricas y puntos de luz
           - Instalaciones de fontanería
           - Sistemas de climatización
           - Instalaciones de gas
           - Telecomunicaciones y datos
           - Sistemas de seguridad
        
        4. **ACCESIBILIDAD:**
           - Rampas y sus pendientes
           - Ascensores y plataformas
           - Anchos de paso y puertas
           - Aseos adaptados
           - Señalización táctil y visual
        
        5. **SEGURIDAD CONTRA INCENDIOS:**
           - Compartimentación horizontal y vertical
           - Salidas de emergencia y recorridos
           - Sistemas de detección
           - Extintores y bocas de incendio
           - Materiales ignífugos
        
        6. **EFICIENCIA ENERGÉTICA:**
           - Aislamiento térmico en secciones
           - Sistemas de ventilación
           - Orientación y soleamiento
           - Sistemas de energías renovables
        
        7. **PARÁMETROS URBANÍSTICOS:**
           - Ocupación del suelo
           - Retranqueos y distancias
           - Alturas máximas
           - Usos por planta
        
        8. **INFORMACIÓN ADICIONAL:**
           - Condicionantes del terreno
           - Servidumbres y limitaciones
           - Accesos y aparcamientos
           - Zonas verdes y ajardinamiento
        
        Devuelve un JSON con la siguiente estructura:
        {{
            "dimensiones_extraidas": {{
                "superficie_total": "valor en m² (usar datos OCR)",
                "superficie_util": "valor en m² (usar datos OCR)",
                "superficie_construida": "valor en m² (usar datos OCR)",
                "altura_total": "valor en m (usar datos OCR)",
                "plantas": "número de plantas",
                "dimensiones_por_planta": {{
                    "planta_baja": "superficie en m²",
                    "planta_primera": "superficie en m²",
                    "planta_segunda": "superficie en m²"
                }},
                "alturas_por_planta": {{
                    "planta_baja": "altura en m",
                    "planta_primera": "altura en m",
                    "planta_segunda": "altura en m"
                }},
                "dimensiones_espacios": {{
                    "habitaciones": "dimensiones típicas",
                    "pasillos": "anchos mínimos",
                    "escaleras": "dimensiones"
                }},
                "datos_ocr_utilizados": {{
                    "total_dimensiones": "número de dimensiones extraídas",
                    "total_areas": "número de áreas extraídas",
                    "total_alturas": "número de alturas extraídas",
                    "rango_mas_comun": "rango más común de valores",
                    "valores_atipicos": "valores atípicos detectados"
                }}
            }},
            "elementos_constructivos": {{
                "estructura": "tipo de estructura detectada",
                "cimentacion": "tipo de cimentación",
                "muros": "tipo y espesor de muros",
                "forjados": "tipo de forjados",
                "cubierta": "tipo de cubierta",
                "materiales_principales": ["lista de materiales"]
            }},
            "instalaciones_detectadas": {{
                "electricas": {{
                    "distribucion": "descripción de la red",
                    "puntos_luz": "número y ubicación",
                    "cuadros_electricos": "ubicación y potencia"
                }},
                "fontaneria": {{
                    "abastecimiento": "descripción",
                    "saneamiento": "descripción",
                    "instalaciones_sanitarias": "número y ubicación"
                }},
                "climatizacion": {{
                    "calefaccion": "sistema detectado",
                    "refrigeracion": "sistema detectado",
                    "ventilacion": "sistema detectado"
                }},
                "gas": "sistema detectado",
                "telecomunicaciones": "sistema detectado"
            }},
            "accesibilidad": {{
                "rampas": {{
                    "pendiente": "valor detectado",
                    "ancho": "valor detectado",
                    "ubicacion": "descripción"
                }},
                "ascensores": {{
                    "numero": "número detectado",
                    "capacidad": "capacidad detectada",
                    "ubicacion": "descripción"
                }},
                "anchos_paso": {{
                    "pasillos": "ancho mínimo detectado",
                    "puertas": "ancho mínimo detectado"
                }},
                "aseos_adaptados": "descripción",
                "señalizacion": "descripción"
            }},
            "seguridad_incendios": {{
                "compartimentacion": "descripción",
                "salidas_emergencia": {{
                    "numero": "número detectado",
                    "ubicacion": "descripción",
                    "ancho": "ancho detectado"
                }},
                "sistemas_deteccion": "sistema detectado",
                "extintores": "ubicación y tipo",
                "bocas_incendio": "ubicación"
            }},
            "eficiencia_energetica": {{
                "aislamiento_termico": "detectado en secciones",
                "ventilacion_natural": "sistema detectado",
                "orientacion": "orientación detectada",
                "soleamiento": "análisis de soleamiento"
            }},
            "parametros_urbanisticos": {{
                "ocupacion_suelo": "valor en m²",
                "retranqueos": "valores detectados",
                "alturas_maximas": "valores detectados",
                "usos_por_planta": "distribución de usos"
            }},
            "informacion_adicional": {{
                "accesos": "descripción",
                "aparcamientos": "número y ubicación",
                "zonas_verdes": "superficie y ubicación",
                "servidumbres": "limitaciones detectadas"
            }},
            "observaciones_tecnicas": [
                "lista de observaciones importantes"
            ],
            "coherencia_con_memoria": {{
                "dimensiones_consistentes": "verificación",
                "usos_consistentes": "verificación",
                "inconsistencias": ["lista de inconsistencias"]
            }},
            "calidad_ocr": {{
                "metodo_extraccion": "método principal usado",
                "confianza_promedio": "confianza promedio del OCR",
                "dimensiones_extraidas": "número de dimensiones extraídas",
                "calidad_datos": "evaluación de la calidad de los datos extraídos"
            }}
        }}
        """
        
        response = await self.ai_client.generate_response(intelligent_planos_prompt, max_tokens=2500)
        
        return self._parse_ai_json_response(response)
    
    async def _check_coherence_with_ai(self, ai_analysis: Dict[str, Any], config: Dict[str, Any], planos_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación inteligente de coherencia entre memoria, configuración y planos"""
        
        # Extraer datos clave de la información extraída
        memoria_data = ai_analysis.get("datos_proyecto", {})
        memoria_tecnico = ai_analysis.get("analisis_tecnico", {})
        memoria_coherencia = ai_analysis.get("coherencia_configuracion", {})
        
        user_config = config
        planos_data = planos_analysis.get("dimensiones_extraidas", {})
        planos_coherencia = planos_analysis.get("coherencia_con_memoria", {})
        
        # Crear prompt para verificación inteligente de coherencia
        coherence_prompt = f"""
        {BASICO_GROQ_BASE}
        
        VERIFICACIÓN INTELIGENTE DE COHERENCIA ENTRE DOCUMENTACIÓN
        
        CONFIGURACIÓN DEL USUARIO:
        {json.dumps(user_config, indent=2)}
        
        DATOS EXTRAÍDOS DE LA MEMORIA:
        {json.dumps(memoria_data, indent=2)}
        
        ANÁLISIS TÉCNICO DE LA MEMORIA:
        {json.dumps(memoria_tecnico, indent=2)}
        
        DIMENSIONES EXTRAÍDAS DE LOS PLANOS:
        {json.dumps(planos_data, indent=2)}
        
        COHERENCIA DETECTADA EN MEMORIA:
        {json.dumps(memoria_coherencia, indent=2)}
        
        COHERENCIA DETECTADA EN PLANOS:
        {json.dumps(planos_coherencia, indent=2)}
        
        INSTRUCCIONES PARA VERIFICACIÓN DE COHERENCIA:
        
        Analiza la coherencia entre:
        1. Configuración del usuario vs datos extraídos de la memoria
        2. Datos de la memoria vs dimensiones de los planos
        3. Análisis técnico vs información gráfica
        4. Consistencia interna de cada documento
        
        Verifica específicamente:
        - Uso principal y usos secundarios
        - Superficies y dimensiones
        - Número de plantas y alturas
        - Sistemas constructivos
        - Instalaciones técnicas
        - Parámetros urbanísticos
        - Normativas mencionadas
        
        Devuelve un JSON con la siguiente estructura:
        {{
            "coherence_score": "puntuación de 0 a 100",
            "issues": [
                {{
                    "tipo": "tipo de inconsistencia",
                    "descripcion": "descripción detallada",
                    "severidad": "low/medium/high",
                    "fuente": "memoria/planos/config",
                    "valor_esperado": "valor esperado",
                    "valor_encontrado": "valor encontrado",
                    "recomendacion": "recomendación para corregir"
                }}
            ],
            "summary": "resumen de la coherencia",
            "recomendaciones": [
                "lista de recomendaciones generales"
            ],
            "datos_consistentes": {{
                "uso_principal": "verificación",
                "superficies": "verificación",
                "dimensiones": "verificación",
                "sistemas_constructivos": "verificación",
                "instalaciones": "verificación"
            }},
            "confianza_analisis": {{
                "memoria": "nivel de confianza en datos de memoria",
                "planos": "nivel de confianza en datos de planos",
                "configuracion": "nivel de confianza en configuración"
            }}
        }}
        """
        
        response = await self.ai_client.generate_response(coherence_prompt, max_tokens=2000)
        
        return self._parse_ai_json_response(response)
    
    def _combine_dimensional_analysis(self, dimensional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combinar análisis dimensional de múltiples archivos"""
        
        try:
            combined = {
                'total_files_analyzed': len(dimensional_data),
                'total_dimensions': 0,
                'total_areas': 0,
                'total_heights': 0,
                'dimension_summary': {},
                'area_summary': {},
                'height_summary': {},
                'statistical_analysis': {},
                'file_analysis': {}
            }
            
            all_dimensions = []
            all_areas = []
            all_heights = []
            
            for filename, analysis in dimensional_data.items():
                if not analysis or 'error' in analysis:
                    continue
                
                combined['file_analysis'][filename] = {
                    'dimensions': analysis.get('total_dimensions', 0),
                    'areas': analysis.get('total_areas', 0),
                    'heights': analysis.get('total_heights', 0)
                }
                
                combined['total_dimensions'] += analysis.get('total_dimensions', 0)
                combined['total_areas'] += analysis.get('total_areas', 0)
                combined['total_heights'] += analysis.get('total_heights', 0)
                
                # Acumular valores para análisis estadístico
                if 'dimension_summary' in analysis and 'values' in analysis['dimension_summary']:
                    all_dimensions.extend(analysis['dimension_summary']['values'])
                
                if 'area_summary' in analysis and 'values' in analysis['area_summary']:
                    all_areas.extend(analysis['area_summary']['values'])
                
                if 'height_summary' in analysis and 'values' in analysis['height_summary']:
                    all_heights.extend(analysis['height_summary']['values'])
            
            # Análisis estadístico combinado
            if all_dimensions:
                combined['dimension_summary'] = {
                    'count': len(all_dimensions),
                    'min': min(all_dimensions),
                    'max': max(all_dimensions),
                    'avg': sum(all_dimensions) / len(all_dimensions),
                    'values': all_dimensions
                }
            
            if all_areas:
                combined['area_summary'] = {
                    'count': len(all_areas),
                    'min': min(all_areas),
                    'max': max(all_areas),
                    'avg': sum(all_areas) / len(all_areas),
                    'values': all_areas
                }
            
            if all_heights:
                combined['height_summary'] = {
                    'count': len(all_heights),
                    'min': min(all_heights),
                    'max': max(all_heights),
                    'avg': sum(all_heights) / len(all_heights),
                    'values': all_heights
                }
            
            # Análisis estadístico general
            all_values = all_dimensions + all_areas + all_heights
            if all_values:
                combined['statistical_analysis'] = {
                    'total_measurements': len(all_values),
                    'range': max(all_values) - min(all_values),
                    'most_common_range': self._find_most_common_range(all_values),
                    'outliers': self._find_outliers(all_values)
                }
            
            return combined

        except Exception as e:
            logger.error(f"❌ Error combinando análisis dimensional: {str(e)}")
            return {
                'total_files_analyzed': 0,
                'total_dimensions': 0,
                'total_areas': 0,
                'total_heights': 0,
                'error': str(e)
            }

    def _combine_technical_info(self, technical_info_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combinar información técnica avanzada de múltiples archivos"""

        try:
            combined = {
                'total_files_analyzed': len(technical_info_data),
                'scales': [],
                'dimensions': [],
                'areas': [],
                'materials': [],
                'installations': [],
                'structural_elements': [],
                'accessibility_features': [],
                'fire_safety_elements': [],
                'energy_efficiency_data': [],
                'urban_parameters': [],
                'file_analysis': {}
            }

            for filename, tech_info in technical_info_data.items():
                if not tech_info:
                    continue

                # Registrar análisis por archivo
                combined['file_analysis'][filename] = {
                    'scales_found': len(tech_info.get('scales', [])),
                    'dimensions_found': len(tech_info.get('dimensions', [])),
                    'areas_found': len(tech_info.get('areas', [])),
                    'materials_found': len(tech_info.get('materials', [])),
                    'installations_found': len(tech_info.get('installations', [])),
                    'structural_elements_found': len(tech_info.get('structural_elements', []))
                }

                # Combinar todas las categorías
                for category in combined.keys():
                    if category in ['total_files_analyzed', 'file_analysis']:
                        continue

                    if category in tech_info:
                        combined[category].extend(tech_info[category])

            # Análisis de escalas detectadas
            if combined['scales']:
                scale_counts = {}
                for scale_info in combined['scales']:
                    scale = scale_info.get('scale', 'unknown')
                    scale_counts[scale] = scale_counts.get(scale, 0) + 1

                combined['scale_analysis'] = {
                    'total_scale_references': len(combined['scales']),
                    'unique_scales': list(scale_counts.keys()),
                    'most_common_scale': max(scale_counts.items(), key=lambda x: x[1])[0] if scale_counts else None,
                    'scale_distribution': scale_counts
                }

            # Análisis de materiales
            if combined['materials']:
                material_types = {}
                for material in combined['materials']:
                    mat_type = material.get('type', 'unknown')
                    material_types[mat_type] = material_types.get(mat_type, 0) + 1

                combined['material_analysis'] = {
                    'total_materials': len(combined['materials']),
                    'material_distribution': material_types
                }

            # Análisis estructural
            if combined['structural_elements']:
                structural_types = {}
                for element in combined['structural_elements']:
                    elem_type = element.get('type', 'unknown')
                    structural_types[elem_type] = structural_types.get(elem_type, 0) + 1

                combined['structural_analysis'] = {
                    'total_elements': len(combined['structural_elements']),
                    'element_distribution': structural_types
                }

            logger.info(f"📊 Información técnica combinada: {len(combined['scales'])} escalas, "
                       f"{len(combined['materials'])} materiales, {len(combined['structural_elements'])} elementos estructurales")

            return combined

        except Exception as e:
            logger.error(f"❌ Error combinando información técnica: {str(e)}")
            return {
                'total_files_analyzed': 0,
                'error': str(e)
            }
    
    def _find_most_common_range(self, values: List[float]) -> Dict[str, Any]:
        """Encontrar el rango más común de valores"""
        
        try:
            if not values:
                return {}
            
            # Agrupar valores en rangos
            ranges = {}
            for value in values:
                # Redondear a rangos de 0.5
                range_key = round(value * 2) / 2
                if range_key not in ranges:
                    ranges[range_key] = 0
                ranges[range_key] += 1
            
            # Encontrar el rango más común
            most_common = max(ranges.items(), key=lambda x: x[1])
            
            return {
                'range': most_common[0],
                'count': most_common[1],
                'percentage': (most_common[1] / len(values)) * 100
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error encontrando rango común: {str(e)}")
            return {}
    
    def _find_outliers(self, values: List[float]) -> List[float]:
        """Encontrar valores atípicos usando el método IQR"""
        
        try:
            if len(values) < 4:
                return []
            
            sorted_values = sorted(values)
            q1 = sorted_values[len(sorted_values) // 4]
            q3 = sorted_values[3 * len(sorted_values) // 4]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [v for v in values if v < lower_bound or v > upper_bound]
            
            return outliers
            
        except Exception as e:
            logger.warning(f"⚠️ Error encontrando outliers: {str(e)}")
            return []
    
    def _prepare_project_text(self, session_data: Dict[str, Any]) -> str:
        """Preparar texto del proyecto para análisis normativo"""
        all_texts = self._extract_all_texts(session_data)
        return self._combine_texts(all_texts)
    
    async def _verify_normative_with_ai(self, project_text: str, user_config: Dict[str, Any], enriched_context: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación normativa contextual con IA - FASE 3 MEJORADA CON CARGA SELECTIVA"""
        
        # Extraer información contextual de Fase 2
        datos_proyecto = enriched_context.get('datos_proyecto', {})
        analisis_tecnico = enriched_context.get('analisis_tecnico', {})
        planos_analysis = enriched_context.get('planos_analysis', {})
        
        # Crear contexto enriquecido para la IA (configuración del usuario tiene prioridad)
        contexto_proyecto = {
            "uso_principal": user_config.get("uso_principal", datos_proyecto.get("uso_principal", "")),
            "norma_zonal": user_config.get("norma_zonal", datos_proyecto.get("norma_zonal", "")),
            "grado": user_config.get("grado", datos_proyecto.get("grado", "")),
            "superficie_construida": datos_proyecto.get("superficie_construida", 0),
            "plantas": datos_proyecto.get("plantas", 0),
            "altura_edificio": datos_proyecto.get("altura_total", datos_proyecto.get("altura_edificio", 0)),
            "sistemas_estructurales": analisis_tecnico.get("sistema_estructural", "no_especificado"),
            "sistemas_ambientales": analisis_tecnico.get("sistemas_ambientales", {}),
            "requisitos_cte": analisis_tecnico.get("requisitos_cte", {}),
            "instalaciones_detectadas": analisis_tecnico.get("instalaciones_detectadas", {}),
            "materiales_principales": analisis_tecnico.get("materiales_principales", []),
            "planos_dimensiones": planos_analysis.get("dimensiones_extraidas", {})
        }
        
        # PASO 1: Determinar normativas aplicables específicamente para este proyecto
        applicable_normatives = self.normative_loader.get_applicable_normatives(contexto_proyecto)
        
        # PASO 2: Cargar contenido con selección inteligente de secciones
        normative_contents = []
        for normative in applicable_normatives[:5]:  # Limitar a 5 normativas principales
            # Usar selección inteligente de secciones
            content = await self.normative_loader.get_intelligent_sections(
                normative, contexto_proyecto, self.ai_client
            )
            if not content.get("error"):
                normative_contents.append({
                    "name": content["name"],
                    "justification": content["justification"],
                    "selection_method": content.get("selection_method", "unknown"),
                    "sections_selected": content.get("total_sections_found", 0),
                    "relevant_content": content["content"][:3000]  # Más contenido con secciones seleccionadas
                })
        
        # PASO 3: Crear prompt contextual específico con información de selección inteligente
        normatives_text = "\n\n".join([
            f"NORMATIVA: {norm['name']}\n"
            f"JUSTIFICACIÓN: {norm['justification']}\n"
            f"MÉTODO DE SELECCIÓN: {norm['selection_method']}\n"
            f"SECCIONES SELECCIONADAS: {norm['sections_selected']}\n"
            f"CONTENIDO RELEVANTE (secciones seleccionadas por IA):\n{norm['relevant_content']}"
            for norm in normative_contents
        ])
        
        prompt = f"""
        {BASICO_GROQ_BASE}
        
        FASE 3: VERIFICACIÓN NORMATIVA CON SELECCIÓN INTELIGENTE DE SECCIONES
        
        Analiza el proyecto aplicando ÚNICAMENTE las secciones normativas que han sido seleccionadas inteligentemente para este proyecto específico.
        
        CONTEXTO DEL PROYECTO (Fase 2):
        {json.dumps(contexto_proyecto, indent=2)}
        
        NORMATIVAS CON SECCIONES SELECCIONADAS (solo estas secciones son relevantes):
        {normatives_text[:10000]}
        
        TEXTO DEL PROYECTO:
        {project_text[:8000]}
        
        INSTRUCCIONES CRÍTICAS:
        1. SOLO verifica contra las secciones normativas proporcionadas arriba
        2. NO inventes normativas, artículos o secciones no mencionadas
        3. Si un artículo no está en el contenido cargado, NO lo menciones
        4. Cada incumplimiento debe citar específicamente el texto normativo proporcionado
        5. Justifica por qué cada sección normativa es aplicable a ESTE proyecto específico
        6. Considera que las secciones han sido pre-seleccionadas por IA para ser relevantes
        
        Responde en formato JSON:
        {{
          "normativas_verificadas": [
            {{
              "normativa": "nombre exacto de la normativa cargada",
              "secciones_seleccionadas": "número de secciones seleccionadas por IA",
              "metodo_seleccion": "método usado para seleccionar secciones",
              "articulos_verificados": ["artículos encontrados en secciones cargadas"],
              "aplicable_justificacion": "por qué es aplicable a este proyecto"
            }}
          ],
          "incumplimientos_detectados": [
            {{
              "normativa": "nombre_normativa_cargada",
              "seccion_aplicable": "sección específica seleccionada por IA",
              "articulo_especifico": "artículo exacto del contenido cargado",
              "texto_normativo": "texto exacto de la normativa",
              "descripcion_incumplimiento": "qué no cumple el proyecto",
              "ubicacion_en_proyecto": "dónde se detectó en el proyecto",
              "severidad": "low/medium/high",
              "evidencia_textual": "cita textual del proyecto que evidencia el incumplimiento",
              "relevancia_seleccion": "por qué esta sección fue seleccionada como relevante"
            }}
          ],
          "elementos_faltantes_verificados": [
            {{
              "elemento": "elemento específico mencionado en sección normativa cargada",
              "normativa_origen": "normativa cargada que lo requiere",
              "seccion_origen": "sección específica que lo requiere",
              "texto_normativo_origen": "texto exacto que lo requiere",
              "ubicacion_esperada": "dónde debería estar en el proyecto"
            }}
          ],
          "observaciones_especificas": [
            "observaciones sobre aplicabilidad de secciones normativas específicas"
          ],
          "puntuacion_cumplimiento": "porcentaje de cumplimiento basado en secciones cargadas",
          "resumen_seleccion_inteligente": {{
            "total_normativas_cargadas": "número de normativas procesadas",
            "total_secciones_seleccionadas": "número total de secciones seleccionadas",
            "criterios_aplicados": ["criterios usados para selección de secciones"],
            "eficiencia_seleccion": "evaluación de la precisión de la selección"
          }}
        }}
        """
        
        response = await self.ai_client.generate_response(prompt, max_tokens=3000)
        
        result = self._parse_ai_json_response(response)
        if "error" not in result:
            # Añadir metadatos sobre las normativas aplicadas
            result["metadata"] = {
                "normativas_consideradas": len(applicable_normatives),
                "normativas_cargadas": len(normative_contents),
                "contexto_aplicado": contexto_proyecto
            }
        return result
    
    async def _verify_cte_with_ai(self, project_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación CTE específica"""
        prompt = BASICO_VERIFICACION_CTE.format(
            texto_proyecto=project_text[:8000],
            config_proyecto=json.dumps(config, indent=2)
        )
        
        response = await self.ai_client.generate_response(prompt)
        
        return self._parse_ai_json_response(response)
    
    async def _verify_pgoum_with_ai(self, project_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación PGOUM específica"""
        prompt = BASICO_VERIFICACION_PGOUM.format(
            texto_proyecto=project_text[:8000],
            config_proyecto=json.dumps(config, indent=2)
        )
        
        response = await self.ai_client.generate_response(prompt)
        
        return self._parse_ai_json_response(response)
    
    def _calculate_final_score(self, normative_verification: Dict[str, Any], cte_verification: Dict[str, Any], pgoum_verification: Dict[str, Any]) -> float:
        """Calcular puntuación final de cumplimiento"""
        
        # Pesos para cada tipo de verificación
        normative_weight = 0.5
        cte_weight = 0.3
        pgoum_weight = 0.2
        
        # Obtener puntuaciones individuales
        normative_score = normative_verification.get("puntuacion_cumplimiento", 0)
        cte_score = cte_verification.get("puntuacion_cte", 0)
        pgoum_score = pgoum_verification.get("puntuacion_pgoum", 0)
        
        # Calcular promedio ponderado
        final_score = (
            normative_score * normative_weight +
            cte_score * cte_weight +
            pgoum_score * pgoum_weight
        )
        
        return round(final_score, 2)
    
    def _generate_coherence_recommendations(self, coherence_issues: List[Dict[str, Any]]) -> List[str]:
        """Generar recomendaciones basadas en problemas de coherencia"""
        recommendations = []
        
        for issue in coherence_issues:
            if issue["tipo"] == "uso_principal":
                recommendations.append(
                    f"Revisar coherencia en uso principal: memoria indica '{issue['memoria']}' pero configuración indica '{issue['config']}'"
                )
            elif issue["tipo"] == "superficie":
                recommendations.append(
                    f"Verificar superficies: diferencia del {issue['diferencia_porcentaje']:.1f}% entre memoria y planos"
                )
        
        if not recommendations:
            recommendations.append("No se detectaron problemas de coherencia significativos")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Obtener timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _parse_ai_json_response(self, response: str) -> Dict[str, Any]:
        """Parse AI JSON response, handling markdown code blocks"""
        try:
            # First try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            
            # Look for JSON in code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Look for JSON without code blocks
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, return error
            return {"error": "Error parsing AI response", "raw_response": response}

