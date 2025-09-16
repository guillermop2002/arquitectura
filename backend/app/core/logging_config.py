"""
Configuración de logging para la aplicación.
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any

# Configurar el path del proyecto
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def get_logger(name: str = "verificacion_app") -> logging.Logger:
    """
    Obtener un logger configurado.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

def initialize_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Inicializar el sistema de logging.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo de log (opcional)
        max_file_size: Tamaño máximo del archivo de log
        backup_count: Número de archivos de respaldo
    """
    # Crear directorio de logs si no existe
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configurar nivel de logging
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Configurar handler para archivo si se especifica
    file_handler = None
    if log_file:
        log_path = log_dir / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Agregar handlers
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Log de inicialización
    logger = get_logger("logging_config")
    logger.info(f"Logging inicializado - Nivel: {log_level}")
    if log_file:
        logger.info(f"Logs guardados en: {log_path}")

def setup_application_logging() -> logging.Logger:
    """
    Configurar logging específico para la aplicación.
    
    Returns:
        Logger de la aplicación
    """
    # Obtener configuración desde variables de entorno
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "verificacion_app.log")
    
    # Inicializar logging
    initialize_logging(
        log_level=log_level,
        log_file=log_file
    )
    
    # Retornar logger de la aplicación
    return get_logger("verificacion_app")

def log_performance(operation: str, duration: float, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Registrar métricas de rendimiento.
    
    Args:
        operation: Nombre de la operación
        duration: Duración en segundos
        details: Detalles adicionales
    """
    logger = get_logger("performance")
    message = f"Performance: {operation} took {duration:.3f}s"
    if details:
        message += f" - Details: {details}"
    logger.info(message)

def log_api_call(api_name: str, endpoint: str, method: str, status_code: int, 
                duration: float, response_size: Optional[int] = None) -> None:
    """
    Registrar llamadas a API.
    
    Args:
        api_name: Nombre de la API
        endpoint: Endpoint llamado
        method: Método HTTP
        status_code: Código de estado
        duration: Duración en segundos
        response_size: Tamaño de la respuesta en bytes
    """
    logger = get_logger("api_calls")
    message = f"API Call: {api_name} {method} {endpoint} - Status: {status_code} - Duration: {duration:.3f}s"
    if response_size:
        message += f" - Size: {response_size} bytes"
    logger.info(message)
