import json
from typing import Dict, Any, List
from pathlib import Path
from .anexo_verifier import BasicoAnexoVerifier
from .ocr_processor import BasicoOCRProcessor
from .ai_client import BasicoAIClient
from .normative_loader import BasicoNormativeLoader
from .basico_prompts import *

class BasicoAnalyzer:
    def __init__(self):
        self.anexo_verifier = BasicoAnexoVerifier()
        self.ocr_processor = BasicoOCRProcessor()
        self.ai_client = BasicoAIClient()
        self.normative_loader = BasicoNormativeLoader()
    
    async def fase1_verificar_documentacion(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """FASE 1: Verificar presencia de elementos según anexo1.json con IA"""
        
        # 1. Extraer texto de todos los documentos
        all_texts = self._extract_all_texts(session_data)
        combined_text = self._combine_texts(all_texts)
        
        # 2. Verificación con IA usando Groq
        ai_verification = await self._verify_with_ai(combined_text)
        
        # 3. Verificación tradicional con anexo
        traditional_verification = self.anexo_verifier.verify_session_documents(session_data)
        
        # 4. Combinar resultados
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
        
        # 1. Extraer texto de memoria específicamente
        memoria_texts = self._extract_memoria_texts(session_data)
        
        # 2. Análisis con IA
        ai_analysis = await self._analyze_memoria_with_ai(memoria_texts, config)
        
        # 3. Análisis de planos (si existen)
        planos_analysis = await self._analyze_planos_with_ai(session_data)
        
        # 4. Verificación de coherencia
        coherence_check = await self._check_coherence_with_ai(ai_analysis, config, planos_analysis)
        
        return {
            "fase": 2,
            "tipo": "analisis_memoria",
            "datos_proyecto": ai_analysis.get("datos_proyecto", {}),
            "analisis_tecnico": ai_analysis.get("analisis_tecnico", {}),
            "planos_analysis": planos_analysis,
            "coherencia_config": coherence_check,
            "coherence_score": coherence_check.get("coherence_score", 0),
            "next_phase_ready": coherence_check.get("coherence_score", 0) > 70,
            "timestamp": self._get_timestamp()
        }
    
    async def fase3_verificar_normativa(self, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """FASE 3: Verificación normativa con IA"""
        
        # 1. Preparar datos para análisis normativo
        project_text = self._prepare_project_text(session_data)
        fase2_result = context.get('fase2', {})
        config = fase2_result.get('datos_proyecto', {})
        
        # 2. Verificación normativa con IA
        normative_verification = await self._verify_normative_with_ai(project_text, config, fase2_result)
        
        # 3. Verificación CTE específica
        cte_verification = await self._verify_cte_with_ai(project_text, config)
        
        # 4. Verificación PGOUM (si aplica)
        pgoum_verification = await self._verify_pgoum_with_ai(project_text, config)
        
        # 5. Calcular puntuación final
        final_score = self._calculate_final_score(normative_verification, cte_verification, pgoum_verification)
        
        return {
            "fase": 3,
            "tipo": "verificacion_normativa",
            "normative_verification": normative_verification,
            "cte_verification": cte_verification,
            "pgoum_verification": pgoum_verification,
            "final_compliance_score": final_score,
            "production_ready": final_score > 75,
            "timestamp": self._get_timestamp()
        }
    
    def _extract_all_texts(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer texto de todos los archivos de la sesión"""
        all_texts = {}
        
        for file_info in session_data.get("files", []):
            file_path = file_info["path"]
            if file_path.lower().endswith('.pdf'):
                text_data = self.ocr_processor.extract_text_from_pdf(file_path)
                all_texts[file_info["filename"]] = text_data
        
        return all_texts
    
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
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Error parsing AI response", "raw_response": response}
    
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
        """Extraer textos específicamente de archivos de memoria"""
        memoria_texts = {}
        
        for file_info in session_data.get("files", []):
            filename = file_info["filename"].lower()
            # Identificar archivos de memoria
            if any(keyword in filename for keyword in ["memoria", "memory", "descriptiva"]):
                file_path = file_info["path"]
                if file_path.lower().endswith('.pdf'):
                    text_data = self.ocr_processor.extract_text_from_pdf(file_path)
                    memoria_texts[file_info["filename"]] = text_data
        
        return memoria_texts
    
    async def _analyze_memoria_with_ai(self, memoria_texts: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de memoria con IA"""
        combined_memoria = self._combine_texts(memoria_texts)
        
        prompt = BASICO_ANALISIS_MEMORIA.format(
            memoria_texto=combined_memoria[:10000],  # Limitar texto
            config_proyecto=json.dumps(config, indent=2)
        )
        
        response = await self.ai_client.generate_response(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Error parsing AI response", "raw_response": response}
    
    async def _analyze_planos_with_ai(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de planos con IA"""
        planos_texts = {}
        
        for file_info in session_data.get("files", []):
            filename = file_info["filename"].lower()
            # Identificar archivos de planos
            if any(keyword in filename for keyword in ["plano", "plan", "dwg", "autocad"]):
                file_path = file_info["path"]
                if file_path.lower().endswith('.pdf'):
                    text_data = self.ocr_processor.extract_text_from_pdf(file_path)
                    planos_texts[file_info["filename"]] = text_data
        
        if not planos_texts:
            return {"message": "No se encontraron planos para analizar"}
        
        combined_planos = self._combine_texts(planos_texts)
        
        prompt = BASICO_ANALISIS_PLANOS.format(
            plans_text=combined_planos[:8000],
            memory_data="{}"  # Se completará con datos de memoria
        )
        
        response = await self.ai_client.generate_response(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Error parsing AI response", "raw_response": response}
    
    async def _check_coherence_with_ai(self, ai_analysis: Dict[str, Any], config: Dict[str, Any], planos_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Verificar coherencia entre memoria, configuración y planos"""
        
        # Extraer datos clave
        memoria_data = ai_analysis.get("datos_proyecto", {})
        user_config = config
        planos_data = planos_analysis.get("dimensiones_extraidas", {})
        
        # Verificar coherencia
        coherence_issues = []
        coherence_score = 100
        
        # Verificar uso principal
        memoria_uso = memoria_data.get("uso_principal", "").lower()
        config_uso = user_config.get("uso_principal", "").lower()
        if memoria_uso and config_uso and memoria_uso != config_uso:
            coherence_issues.append({
                "tipo": "uso_principal",
                "memoria": memoria_uso,
                "config": config_uso,
                "severidad": "high"
            })
            coherence_score -= 20
        
        # Verificar superficie
        memoria_superficie = memoria_data.get("superficie_construida", 0)
        planos_superficie = planos_data.get("superficie_planos", 0)
        if memoria_superficie > 0 and planos_superficie > 0:
            diferencia = abs(memoria_superficie - planos_superficie) / memoria_superficie
            if diferencia > 0.1:  # Más del 10% de diferencia
                coherence_issues.append({
                    "tipo": "superficie",
                    "memoria": memoria_superficie,
                    "planos": planos_superficie,
                    "diferencia_porcentaje": diferencia * 100,
                    "severidad": "medium"
                })
                coherence_score -= 15
        
        return {
            "coherence_score": max(0, coherence_score),
            "issues": coherence_issues,
            "total_issues": len(coherence_issues),
            "high_severity_issues": len([i for i in coherence_issues if i.get("severidad") == "high"]),
            "recommendations": self._generate_coherence_recommendations(coherence_issues)
        }
    
    def _prepare_project_text(self, session_data: Dict[str, Any]) -> str:
        """Preparar texto del proyecto para análisis normativo"""
        all_texts = self._extract_all_texts(session_data)
        return self._combine_texts(all_texts)
    
    async def _verify_normative_with_ai(self, project_text: str, config: Dict[str, Any], fase2_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación normativa contextual con IA - FASE 3 MEJORADA CON CARGA SELECTIVA"""
        
        # Extraer información contextual de Fase 2
        datos_proyecto = fase2_result.get('datos_proyecto', {})
        analisis_tecnico = fase2_result.get('analisis_tecnico', {})
        
        # Crear contexto enriquecido para la IA
        contexto_proyecto = {
            "uso_principal": config.get("uso_principal", datos_proyecto.get("uso_principal", "")),
            "norma_zonal": config.get("norma_zonal", datos_proyecto.get("norma_zonal", "")),
            "grado": config.get("grado", datos_proyecto.get("grado", "")),
            "superficie_construida": datos_proyecto.get("superficie_construida", 0),
            "plantas": datos_proyecto.get("plantas", 0),
            "altura_edificio": datos_proyecto.get("altura_edificio", 0),
            "sistemas_estructurales": analisis_tecnico.get("sistemas_estructurales", {}),
            "sistemas_ambientales": analisis_tecnico.get("sistemas_ambientales", {}),
            "requisitos_cte": analisis_tecnico.get("requisitos_cte", {})
        }
        
        # PASO 1: Determinar normativas aplicables específicamente para este proyecto
        applicable_normatives = self.normative_loader.get_applicable_normatives(contexto_proyecto)
        
        # PASO 2: Cargar solo el contenido relevante de cada normativa
        normative_contents = []
        for normative in applicable_normatives[:5]:  # Limitar a 5 normativas principales
            content = self.normative_loader.load_normative_content(normative)
            if not content.get("error"):
                normative_contents.append({
                    "name": content["name"],
                    "justification": content["justification"],
                    "relevant_content": content["content"][:2000]  # Limitar contenido
                })
        
        # PASO 3: Crear prompt contextual específico
        normatives_text = "\n\n".join([
            f"NORMATIVA: {norm['name']}\nJUSTIFICACIÓN: {norm['justification']}\nCONTENIDO RELEVANTE:\n{norm['relevant_content']}"
            for norm in normative_contents
        ])
        
        prompt = f"""
        {BASICO_GROQ_BASE}
        
        FASE 3: VERIFICACIÓN NORMATIVA CONTEXTUAL ESPECÍFICA
        
        Analiza el proyecto aplicando ÚNICAMENTE las normativas cargadas que son específicamente relevantes para este proyecto.
        
        CONTEXTO DEL PROYECTO (Fase 2):
        {json.dumps(contexto_proyecto, indent=2)}
        
        NORMATIVAS APLICABLES (solo estas):
        {normatives_text[:8000]}
        
        TEXTO DEL PROYECTO:
        {project_text[:8000]}
        
        INSTRUCCIONES CRÍTICAS:
        1. SOLO verifica contra las normativas proporcionadas arriba
        2. NO inventes normativas o artículos no mencionados
        3. Si un artículo no está en el contenido cargado, NO lo menciones
        4. Cada incumplimiento debe citar específicamente el texto normativo proporcionado
        5. Justifica por qué cada normativa/artículo es aplicable a ESTE proyecto específico
        
        Responde en formato JSON:
        {{
          "normativas_verificadas": [
            {{
              "normativa": "nombre exacto de la normativa cargada",
              "articulos_verificados": ["artículos encontrados en contenido cargado"],
              "aplicable_justificacion": "por qué es aplicable a este proyecto"
            }}
          ],
          "incumplimientos_detectados": [
            {{
              "normativa": "nombre_normativa_cargada",
              "articulo_especifico": "artículo exacto del contenido cargado",
              "texto_normativo": "texto exacto de la normativa",
              "descripcion_incumplimiento": "qué no cumple el proyecto",
              "ubicacion_en_proyecto": "dónde se detectó en el proyecto",
              "severidad": "low/medium/high",
              "evidencia_textual": "cita textual del proyecto que evidencia el incumplimiento"
            }}
          ],
          "elementos_faltantes_verificados": [
            {{
              "elemento": "elemento específico mencionado en normativa cargada",
              "normativa_origen": "normativa cargada que lo requiere",
              "texto_normativo_origen": "texto exacto que lo requiere",
              "obligatorio_justificacion": "por qué es obligatorio según el contexto"
            }}
          ],
          "puntuacion_cumplimiento": 0-100,
          "observaciones_especificas": [
            "observaciones basadas únicamente en normativas cargadas y proyecto analizado"
          ]
        }}
        """
        
        response = await self.ai_client.generate_response(prompt, max_tokens=3000)
        
        try:
            result = json.loads(response)
            # Añadir metadatos sobre las normativas aplicadas
            result["metadata"] = {
                "normativas_consideradas": len(applicable_normatives),
                "normativas_cargadas": len(normative_contents),
                "contexto_aplicado": contexto_proyecto
            }
            return result
        except json.JSONDecodeError:
            return {"error": "Error parsing AI response", "raw_response": response}
    
    async def _verify_cte_with_ai(self, project_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación CTE específica"""
        prompt = BASICO_VERIFICACION_CTE.format(
            texto_proyecto=project_text[:8000],
            config_proyecto=json.dumps(config, indent=2)
        )
        
        response = await self.ai_client.generate_response(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Error parsing AI response", "raw_response": response}
    
    async def _verify_pgoum_with_ai(self, project_text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verificación PGOUM específica"""
        prompt = BASICO_VERIFICACION_PGOUM.format(
            texto_proyecto=project_text[:8000],
            config_proyecto=json.dumps(config, indent=2)
        )
        
        response = await self.ai_client.generate_response(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Error parsing AI response", "raw_response": response}
    
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

