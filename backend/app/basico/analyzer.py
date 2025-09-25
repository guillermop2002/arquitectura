import json
from typing import Dict, Any, List
from pathlib import Path
from .anexo_verifier import BasicoAnexoVerifier
from .ocr_processor import BasicoOCRProcessor
from .ai_client import BasicoAIClient
from .basico_prompts import *

class BasicoAnalyzer:
    def __init__(self):
        self.anexo_verifier = BasicoAnexoVerifier()
        self.ocr_processor = BasicoOCRProcessor()
        self.ai_client = BasicoAIClient()
    
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
    
    def _get_timestamp(self) -> str:
        """Obtener timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()

