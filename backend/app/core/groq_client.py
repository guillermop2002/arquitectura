"""
Cliente Groq con rotación automática de claves y manejo de rate limits.
Optimizado para Oracle Cloud ARM64 con 4 claves de free tier.
"""

import os
import sys
import logging
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import AIConfig

logger = logging.getLogger(__name__)

class GroqClient:
    """Cliente Groq con rotación automática de claves y manejo de rate limits."""
    
    def __init__(self, config: AIConfig):
        """Inicializar cliente Groq."""
        self.config = config
        self.base_url = "https://api.groq.com/openai/v1"
        self.session = None
        self.rate_limit_delay = config.rate_limit_delay
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        
        # Estadísticas de uso
        self.request_count = 0
        self.error_count = 0
        self.last_request_time = None
        self.key_errors = {key: 0 for key in config.groq_api_keys}
        
        logger.info(f"GroqClient initialized with {len(config.groq_api_keys)} keys")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "BuildingVerificationSystem/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_headers(self, api_key: str) -> Dict[str, str]:
        """Obtener headers para la petición."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BuildingVerificationSystem/1.0"
        }
    
    async def _make_request(self, 
                          endpoint: str, 
                          payload: Dict[str, Any], 
                          api_key: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Realizar petición HTTP a Groq API."""
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = self._get_headers(api_key)
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                self.request_count += 1
                self.last_request_time = datetime.now()
                
                # Registrar uso de la clave
                self.config.record_key_usage(api_key)
                
                if response.status == 200:
                    data = await response.json()
                    return True, data, None
                elif response.status == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 1))
                    error_msg = f"Rate limit exceeded. Retry after {retry_after} seconds"
                    logger.warning(f"Rate limit for key {api_key[:10]}...: {error_msg}")
                    return False, {}, error_msg
                elif response.status == 401:  # Unauthorized
                    error_msg = f"Invalid API key: {api_key[:10]}..."
                    logger.error(error_msg)
                    self.key_errors[api_key] += 1
                    return False, {}, error_msg
                else:
                    error_text = await response.text()
                    error_msg = f"HTTP {response.status}: {error_text}"
                    logger.error(f"API error: {error_msg}")
                    return False, {}, error_msg
                    
        except asyncio.TimeoutError:
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    async def _try_with_key_rotation(self, 
                                   endpoint: str, 
                                   payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Intentar petición con rotación de claves."""
        last_error = None
        
        for attempt in range(self.max_retries):
            # Obtener clave actual
            current_key = self.config.get_current_key()
            
            # Realizar petición
            success, data, error = await self._make_request(endpoint, payload, current_key)
            
            if success:
                return True, data, None
            
            # Si es error de rate limit, esperar antes de rotar
            if "Rate limit" in str(error):
                retry_after = 1
                if "Retry after" in str(error):
                    try:
                        retry_after = int(str(error).split("Retry after ")[1].split(" ")[0])
                    except:
                        retry_after = 1
                
                logger.info(f"Waiting {retry_after} seconds before retry...")
                await asyncio.sleep(retry_after)
            
            # Rotar clave para el siguiente intento
            if attempt < self.max_retries - 1:
                next_key = self.config.rotate_key()
                logger.info(f"Rotating to next key: {next_key[:10]}...")
                
                # Pequeña pausa entre intentos
                await asyncio.sleep(self.rate_limit_delay)
            
            last_error = error
        
        # Si llegamos aquí, todos los intentos fallaron
        self.error_count += 1
        return False, {}, f"All attempts failed. Last error: {last_error}"
    
    async def generate_completion(self, 
                                prompt: str, 
                                model: Optional[str] = None,
                                max_tokens: Optional[int] = None,
                                temperature: Optional[float] = None) -> Dict[str, Any]:
        """Generar completación usando Groq API."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Usar configuración por defecto si no se especifica
        model = model or self.config.groq_model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        logger.info(f"Generating completion with model {model}, max_tokens {max_tokens}")
        
        success, data, error = await self._try_with_key_rotation("chat/completions", payload)
        
        if success:
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "usage": data.get("usage", {}),
                "model": data.get("model", model),
                "key_used": self.config.get_current_key()[:10] + "..."
            }
        else:
            return {
                "success": False,
                "error": error,
                "response": "",
                "usage": {},
                "model": model
            }
    
    async def generate_structured_completion(self, 
                                           prompt: str, 
                                           model: Optional[str] = None,
                                           max_tokens: Optional[int] = None,
                                           temperature: Optional[float] = None) -> Dict[str, Any]:
        """Generar completación estructurada (JSON) usando Groq API."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Usar configuración por defecto si no se especifica
        model = model or self.config.groq_model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        # Añadir instrucciones para JSON
        json_prompt = f"{prompt}\n\nResponde ÚNICAMENTE en formato JSON válido, sin texto adicional."
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": json_prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "response_format": {"type": "json_object"}
        }
        
        logger.info(f"Generating structured completion with model {model}")
        
        success, data, error = await self._try_with_key_rotation("chat/completions", payload)
        
        if success:
            response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Intentar parsear JSON
            try:
                json_response = json.loads(response_text)
                return {
                    "success": True,
                    "response": json_response,
                    "raw_response": response_text,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", model),
                    "key_used": self.config.get_current_key()[:10] + "..."
                }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {str(e)}",
                    "raw_response": response_text,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", model)
                }
        else:
            return {
                "success": False,
                "error": error,
                "response": {},
                "raw_response": "",
                "usage": {},
                "model": model
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso del cliente."""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "key_errors": self.key_errors.copy(),
            "key_usage_stats": self.config.get_key_usage_stats(),
            "current_key": self.config.get_current_key()[:10] + "...",
            "total_keys": len(self.config.groq_api_keys)
        }
    
    def reset_stats(self):
        """Resetear estadísticas de uso."""
        self.request_count = 0
        self.error_count = 0
        self.last_request_time = None
        self.key_errors = {key: 0 for key in self.config.groq_api_keys}
        self.config.key_usage_count = {key: 0 for key in self.config.groq_api_keys}
        logger.info("Usage statistics reset")
