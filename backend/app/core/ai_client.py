"""
AI client for Groq API integration with enhanced error handling and rate limiting.
"""

import os
import logging
import time
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from openai import OpenAI
except ImportError:
    # Fallback for environments without openai package
    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass

from .config import get_config
from .error_handling import AIProcessingError, ErrorCode, handle_exception
from .logging_config import log_performance, log_api_call

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structured AI response."""
    content: str
    success: bool
    tokens_used: int = 0
    processing_time: float = 0.0
    confidence: float = 0.0
    error: Optional[str] = None


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_requests_per_minute: int = 60, max_requests_per_hour: int = 1000):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_hour = max_requests_per_hour
        self.requests_minute = []
        self.requests_hour = []
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limits."""
        now = time.time()
        
        # Clean old requests
        self.requests_minute = [req_time for req_time in self.requests_minute if now - req_time < 60]
        self.requests_hour = [req_time for req_time in self.requests_hour if now - req_time < 3600]
        
        # Check limits
        if len(self.requests_minute) >= self.max_requests_per_minute:
            return False
        if len(self.requests_hour) >= self.max_requests_per_hour:
            return False
        
        return True
    
    def record_request(self):
        """Record a request timestamp."""
        now = time.time()
        self.requests_minute.append(now)
        self.requests_hour.append(now)
    
    def get_wait_time(self) -> float:
        """Get time to wait before next request can be made."""
        now = time.time()
        
        # Check minute limit
        if len(self.requests_minute) >= self.max_requests_per_minute:
            oldest_minute = min(self.requests_minute)
            return max(0, 60 - (now - oldest_minute))
        
        # Check hour limit
        if len(self.requests_hour) >= self.max_requests_per_hour:
            oldest_hour = min(self.requests_hour)
            return max(0, 3600 - (now - oldest_hour))
        
        return 0.0


class AIClient:
    """Enhanced AI client with error handling and rate limiting."""
    
    def __init__(self):
        """Initialize AI client with configuration."""
        self.config = get_config()
        self.ai_config = self.config.ai
        
        # Initialize Groq client (primary) with OpenAI fallback
        self.client = None
        self.client_type = None
        
        if self.ai_config.groq_api_key:
            try:
                self.client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=self.ai_config.groq_api_key
                )
                self.client_type = "groq"
                logger.info("Groq API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            logger.warning("GROQ_API_KEY not provided, AI functionality disabled")
        
        # Fallback to OpenAI if available (for compatibility)
        if not self.client and self.ai_config.openai_api_key:
            try:
                self.client = OpenAI(api_key=self.ai_config.openai_api_key)
                self.client_type = "openai"
                logger.info("OpenAI fallback client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI fallback: {e}")
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=60,  # Conservative limit
            max_requests_per_hour=1000
        )
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_processing_time': 0.0,
            'rate_limited_requests': 0
        }
    
    def is_available(self) -> bool:
        """Check if AI client is available."""
        return self.client is not None
    
    @log_performance
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None
    ) -> AIResponse:
        """
        Make a chat completion request with enhanced error handling.
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            
        Returns:
            AIResponse object
        """
        if not self.is_available():
            return AIResponse(
                content="",
                success=False,
                error="AI client not available"
            )
        
        # Use configured defaults if not provided
        model = model or self.ai_config.groq_model
        max_tokens = max_tokens or self.ai_config.max_tokens
        temperature = temperature or self.ai_config.temperature
        timeout = timeout or self.ai_config.timeout
        
        # Check rate limits
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            self.stats['rate_limited_requests'] += 1
            return AIResponse(
                content="",
                success=False,
                error=f"Rate limit exceeded. Wait {wait_time:.1f} seconds"
            )
        
        # Record request
        self.rate_limiter.record_request()
        self.stats['total_requests'] += 1
        
        start_time = time.time()
        
        try:
            # Make API request with retries
            for attempt in range(self.ai_config.max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=timeout
                    )
                    
                    # Extract response data
                    content = response.choices[0].message.content
                    tokens_used = response.usage.total_tokens if response.usage else 0
                    processing_time = time.time() - start_time
                    
                    # Calculate confidence based on response quality
                    confidence = self._calculate_confidence(content, tokens_used)
                    
                    # Update stats
                    self.stats['successful_requests'] += 1
                    self.stats['total_tokens'] += tokens_used
                    self.stats['total_processing_time'] += processing_time
                    
                    # Log API call
                    log_api_call("Groq API", "chat completion", "POST", 200, processing_time, len(content))
                    
                    return AIResponse(
                        content=content,
                        success=True,
                        tokens_used=tokens_used,
                        processing_time=processing_time,
                        confidence=confidence
                    )
                    
                except Exception as e:
                    if attempt < self.ai_config.max_retries - 1:
                        wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                        logger.warning(f"API request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        raise
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats['failed_requests'] += 1
            
            error_msg = f"AI API request failed: {str(e)}"
            logger.error(error_msg)
            
            # Log API call error
            log_api_call("Groq API", "chat completion", "POST", 500, processing_time)
            
            return AIResponse(
                content="",
                success=False,
                processing_time=processing_time,
                error=error_msg
            )
    
    def extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from AI response content."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Try to parse the entire content as JSON
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
            return None
    
    def _calculate_confidence(self, content: str, tokens_used: int) -> float:
        """Calculate confidence score for AI response."""
        if not content:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Length factor
        if len(content) > 500:
            confidence += 0.2
        elif len(content) > 200:
            confidence += 0.1
        
        # Token efficiency factor
        if tokens_used > 0:
            efficiency = len(content) / tokens_used
            if efficiency > 0.5:
                confidence += 0.2
            elif efficiency > 0.3:
                confidence += 0.1
        
        # Content quality indicators
        if any(indicator in content.lower() for indicator in ['error', 'failed', 'unable']):
            confidence -= 0.2
        
        if any(indicator in content.lower() for indicator in ['success', 'completed', 'found']):
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_requests = self.stats['total_requests']
        if total_requests == 0:
            success_rate = 0.0
            avg_processing_time = 0.0
            avg_tokens = 0.0
        else:
            success_rate = self.stats['successful_requests'] / total_requests
            avg_processing_time = self.stats['total_processing_time'] / total_requests
            avg_tokens = self.stats['total_tokens'] / total_requests
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'avg_tokens_per_request': avg_tokens,
            'rate_limit_usage': self.rate_limiter.requests_minute.__len__() / 60.0
        }
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_processing_time': 0.0,
            'rate_limited_requests': 0
        }


# Global AI client instance
ai_client = AIClient()


def get_ai_client() -> AIClient:
    """Get the global AI client instance."""
    return ai_client
