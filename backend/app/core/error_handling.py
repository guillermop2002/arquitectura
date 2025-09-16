"""
Sistema de manejo de errores para la aplicación.
"""
import logging
import traceback
from typing import Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Códigos de error del sistema."""
    
    # Errores generales
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Errores de IA
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    AI_RATE_LIMIT = "AI_RATE_LIMIT"
    AI_TIMEOUT = "AI_TIMEOUT"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    
    # Errores de base de datos
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DATABASE_TRANSACTION_ERROR = "DATABASE_TRANSACTION_ERROR"
    
    # Errores de archivos
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_READ_ERROR = "FILE_READ_ERROR"
    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    FILE_PERMISSION_ERROR = "FILE_PERMISSION_ERROR"
    
    # Errores de procesamiento
    PDF_PROCESSING_ERROR = "PDF_PROCESSING_ERROR"
    OCR_PROCESSING_ERROR = "OCR_PROCESSING_ERROR"
    IMAGE_PROCESSING_ERROR = "IMAGE_PROCESSING_ERROR"
    
    # Errores de validación
    ANEXO1_VALIDATION_ERROR = "ANEXO1_VALIDATION_ERROR"
    PROJECT_VALIDATION_ERROR = "PROJECT_VALIDATION_ERROR"
    DOCUMENT_VALIDATION_ERROR = "DOCUMENT_VALIDATION_ERROR"
    
    # Errores de red
    NETWORK_ERROR = "NETWORK_ERROR"
    API_ERROR = "API_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"

class AIProcessingError(Exception):
    """Error específico para procesamiento de IA."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.AI_SERVICE_ERROR, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir error a diccionario."""
        return {
            "error_type": "AIProcessingError",
            "message": self.message,
            "error_code": self.error_code.value,
            "details": self.details,
            "timestamp": self.timestamp
        }

class ValidationError(Exception):
    """Error de validación."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 error_code: ErrorCode = ErrorCode.VALIDATION_ERROR):
        super().__init__(message)
        self.message = message
        self.field = field
        self.error_code = error_code
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir error a diccionario."""
        return {
            "error_type": "ValidationError",
            "message": self.message,
            "field": self.field,
            "error_code": self.error_code.value,
            "timestamp": self.timestamp
        }

class DatabaseError(Exception):
    """Error de base de datos."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DATABASE_CONNECTION_ERROR,
                 query: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.query = query
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir error a diccionario."""
        return {
            "error_type": "DatabaseError",
            "message": self.message,
            "error_code": self.error_code.value,
            "query": self.query,
            "timestamp": self.timestamp
        }

class FileProcessingError(Exception):
    """Error de procesamiento de archivos."""
    
    def __init__(self, message: str, file_path: Optional[str] = None,
                 error_code: ErrorCode = ErrorCode.FILE_READ_ERROR):
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.error_code = error_code
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir error a diccionario."""
        return {
            "error_type": "FileProcessingError",
            "message": self.message,
            "file_path": self.file_path,
            "error_code": self.error_code.value,
            "timestamp": self.timestamp
        }

def handle_exception(e: Exception, context: str = "Unknown") -> Dict[str, Any]:
    """
    Manejar excepción y devolver información estructurada.
    
    Args:
        e: Excepción a manejar
        context: Contexto donde ocurrió la excepción
        
    Returns:
        Diccionario con información del error
    """
    try:
        # Log del error
        logger.error(f"Error en {context}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Si es un error personalizado, usar su método to_dict
        if hasattr(e, 'to_dict'):
            error_info = e.to_dict()
            error_info["context"] = context
            return error_info
        
        # Error genérico
        return {
            "error_type": type(e).__name__,
            "message": str(e),
            "error_code": ErrorCode.UNKNOWN_ERROR.value,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc()
        }
        
    except Exception as handling_error:
        logger.critical(f"Error al manejar excepción: {handling_error}")
        return {
            "error_type": "ErrorHandlingError",
            "message": f"Error al manejar excepción: {str(handling_error)}",
            "original_error": str(e),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

def create_error_response(error_info: Dict[str, Any], status_code: int = 500) -> Dict[str, Any]:
    """
    Crear respuesta de error estructurada.
    
    Args:
        error_info: Información del error
        status_code: Código de estado HTTP
        
    Returns:
        Respuesta de error estructurada
    """
    return {
        "success": False,
        "error": error_info,
        "status_code": status_code,
        "timestamp": datetime.now().isoformat()
    }

def log_error(error_info: Dict[str, Any], level: str = "ERROR") -> None:
    """
    Registrar error en logs.
    
    Args:
        error_info: Información del error
        level: Nivel de log
    """
    try:
        log_message = f"Error {error_info.get('error_type', 'Unknown')}: {error_info.get('message', 'No message')}"
        
        if level.upper() == "CRITICAL":
            logger.critical(log_message)
        elif level.upper() == "ERROR":
            logger.error(log_message)
        elif level.upper() == "WARNING":
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        # Log de detalles si están disponibles
        if error_info.get('details'):
            logger.debug(f"Error details: {error_info['details']}")
            
    except Exception as e:
        logger.critical(f"Error al registrar error: {e}")

def is_retryable_error(error_info: Dict[str, Any]) -> bool:
    """
    Determinar si un error es recuperable.
    
    Args:
        error_info: Información del error
        
    Returns:
        True si el error es recuperable
    """
    retryable_codes = [
        ErrorCode.AI_RATE_LIMIT.value,
        ErrorCode.AI_TIMEOUT.value,
        ErrorCode.NETWORK_ERROR.value,
        ErrorCode.TIMEOUT_ERROR.value,
        ErrorCode.DATABASE_CONNECTION_ERROR.value
    ]
    
    return error_info.get('error_code') in retryable_codes

def get_error_severity(error_info: Dict[str, Any]) -> str:
    """
    Obtener severidad del error.
    
    Args:
        error_info: Información del error
        
    Returns:
        Severidad del error (LOW, MEDIUM, HIGH, CRITICAL)
    """
    error_code = error_info.get('error_code', '')
    
    if error_code in [ErrorCode.AI_RATE_LIMIT.value, ErrorCode.VALIDATION_ERROR.value]:
        return "LOW"
    elif error_code in [ErrorCode.AI_SERVICE_ERROR.value, ErrorCode.DATABASE_QUERY_ERROR.value]:
        return "MEDIUM"
    elif error_code in [ErrorCode.DATABASE_CONNECTION_ERROR.value, ErrorCode.FILE_READ_ERROR.value]:
        return "HIGH"
    else:
        return "CRITICAL"

def format_error_for_user(error_info: Dict[str, Any]) -> str:
    """
    Formatear error para mostrar al usuario.
    
    Args:
        error_info: Información del error
        
    Returns:
        Mensaje de error formateado para el usuario
    """
    error_type = error_info.get('error_type', 'Error')
    message = error_info.get('message', 'Error desconocido')
    
    # Mensajes amigables para el usuario
    user_messages = {
        'AIProcessingError': 'Error en el procesamiento de IA. Inténtalo de nuevo.',
        'ValidationError': 'Error de validación en los datos proporcionados.',
        'DatabaseError': 'Error de conexión a la base de datos.',
        'FileProcessingError': 'Error al procesar el archivo.',
        'AIProcessingError': 'Error en el servicio de IA. Inténtalo más tarde.'
    }
    
    return user_messages.get(error_type, f"Error: {message}")
