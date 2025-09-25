import os
import json
import random
from typing import Dict, Any, Optional
from groq import Groq

class BasicoAIClient:
    def __init__(self):
        # Configurar rotación de claves API
        self.api_keys = [
            os.getenv('GROQ_API_KEY_1'),
            os.getenv('GROQ_API_KEY_2'),
            os.getenv('GROQ_API_KEY_3'),
            os.getenv('GROQ_API_KEY_4')
        ]
        self.api_keys = [key for key in self.api_keys if key]  # Filtrar claves vacías
        
        self.current_key_index = 0
        self.client = None
        self.model = "llama-3.3-70b-versatile"
        
        if self.api_keys:
            self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar cliente Groq con la clave actual"""
        if self.api_keys:
            try:
                current_key = self.api_keys[self.current_key_index]
                self.client = Groq(api_key=current_key)
            except Exception as e:
                print(f"Error inicializando cliente Groq: {e}")
                self.client = None
    
    def _rotate_key(self):
        """Rotar a la siguiente clave API"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._initialize_client()
    
    async def generate_response(self, prompt: str, max_tokens: int = 2000, retry_count: int = 0) -> str:
        """Generar respuesta usando Groq con rotación de claves"""
        
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
            # Si hay error y tenemos más claves, intentar con la siguiente
            if retry_count < len(self.api_keys) - 1:
                self._rotate_key()
                return await self.generate_response(prompt, max_tokens, retry_count + 1)
            
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
            "api_keys_configured": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "client_available": self.is_available(),
            "model": self.model
        }