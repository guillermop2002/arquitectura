import os
import json
from typing import Dict, Any, Optional
from groq import Groq

class BasicoAIClient:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.client = None
        self.model = "llama-3.1-70b-versatile"
        
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Error inicializando cliente Groq: {e}")
    
    async def generate_response(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generar respuesta usando Groq"""
        
        if not self.client:
            return json.dumps({
                "error": "Cliente Groq no disponible",
                "message": "Verificar GROQ_API_KEY"
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en normativa arquitectónica española. Responde siempre en formato JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return json.dumps({
                "error": f"Error en API Groq: {str(e)}",
                "fallback_analysis": "Análisis no disponible por error en IA"
            })
    
    def is_available(self) -> bool:
        """Verificar si el cliente está disponible"""
        return self.client is not None
    
    def get_client_info(self) -> Dict[str, Any]:
        """Obtener información del cliente"""
        return {
            "api_key_configured": bool(self.api_key),
            "client_available": self.is_available(),
            "model": self.model
        }