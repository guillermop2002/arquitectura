"""
Configuration management for the building verification system.
Handles environment variables, default values, and configuration validation.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: Optional[str] = None
    host: str = "localhost"
    port: int = 5432
    name: str = "building_verification"
    user: str = "postgres"
    password: str = ""
    ssl_mode: str = "prefer"
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create database config from environment variables."""
        return cls(
            url=os.getenv('DATABASE_URL'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            name=os.getenv('DB_NAME', 'building_verification'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            ssl_mode=os.getenv('DB_SSL_MODE', 'prefer')
        )


@dataclass
class RedisConfig:
    """Redis configuration."""
    url: Optional[str] = None
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False

@dataclass
class Neo4jConfig:
    """Neo4j configuration."""
    uri: str = "neo4j://localhost:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    
    @classmethod
    def from_env(cls) -> 'Neo4jConfig':
        """Create Neo4j config from environment variables."""
        return cls(
            uri=os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
            username=os.getenv('NEO4J_USERNAME', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD', 'password'),
            database=os.getenv('NEO4J_DATABASE', 'neo4j')
        )

@dataclass
class RedisConfig:
    """Redis configuration."""
    url: Optional[str] = None
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """Create Redis config from environment variables."""
        return cls(
            url=os.getenv('REDIS_URL'),
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true'
        )


@dataclass
class AIConfig:
    """AI service configuration with key rotation support."""
    groq_api_keys: List[str] = None
    openai_api_key: Optional[str] = None  # Para compatibilidad
    groq_model: str = "llama-3.3-70b-versatile"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.1
    use_key_rotation: bool = True
    current_key_index: int = 0
    key_usage_count: Dict[str, int] = None
    
    def __post_init__(self):
        if self.groq_api_keys is None:
            # Las claves se cargarán desde variables de entorno
            self.groq_api_keys = []
        if self.key_usage_count is None:
            self.key_usage_count = {}
    
    @classmethod
    def from_env(cls) -> 'AIConfig':
        """Create AI config from environment variables."""
        # Obtener claves de Groq (múltiples)
        groq_keys = []
        for i in range(1, 5):  # 4 claves
            key = os.getenv(f'GROQ_API_KEY_{i}')
            if key:
                groq_keys.append(key)
        
        # Si no hay claves en env, mostrar error
        if not groq_keys:
            raise ValueError("No se encontraron claves de Groq en las variables de entorno. Configura GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3, GROQ_API_KEY_4")
        
        return cls(
            groq_api_keys=groq_keys,
            openai_api_key=os.getenv('OPENAI_API_KEY'),  # Para compatibilidad
            groq_model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            max_tokens=int(os.getenv('AI_MAX_TOKENS', '4096')),
            temperature=float(os.getenv('AI_TEMPERATURE', '0.1')),
            timeout=int(os.getenv('AI_TIMEOUT', '30')),
            max_retries=int(os.getenv('AI_MAX_RETRIES', '3')),
            rate_limit_delay=float(os.getenv('AI_RATE_LIMIT_DELAY', '0.1')),
            use_key_rotation=os.getenv('USE_KEY_ROTATION', 'true').lower() == 'true'
        )
    
    def get_current_key(self) -> str:
        """Obtener la clave actual para usar."""
        if not self.groq_api_keys:
            raise ValueError("No Groq API keys configured")
        
        if not self.use_key_rotation:
            return self.groq_api_keys[0]
        
        return self.groq_api_keys[self.current_key_index]
    
    def rotate_key(self) -> str:
        """Rotar a la siguiente clave disponible."""
        if not self.groq_api_keys:
            raise ValueError("No Groq API keys configured")
        
        if not self.use_key_rotation:
            return self.groq_api_keys[0]
        
        # Rotar al siguiente índice
        self.current_key_index = (self.current_key_index + 1) % len(self.groq_api_keys)
        return self.groq_api_keys[self.current_key_index]
    
    def record_key_usage(self, key: str):
        """Registrar uso de una clave."""
        if key in self.key_usage_count:
            self.key_usage_count[key] += 1
    
    def get_key_usage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso de claves."""
        if not self.groq_api_keys:
            return {}
        
        total_usage = sum(self.key_usage_count.values())
        return {
            "total_keys": len(self.groq_api_keys),
            "current_key_index": self.current_key_index,
            "current_key": self.groq_api_keys[self.current_key_index],
            "key_usage": self.key_usage_count.copy(),
            "total_usage": total_usage,
            "average_usage_per_key": total_usage / len(self.groq_api_keys) if self.groq_api_keys else 0
        }

@dataclass
class RasaConfig:
    """Rasa microservice configuration."""
    url: str = "http://rasa:5005"
    timeout: int = 30
    max_retries: int = 3
    enabled: bool = True
    
    @classmethod
    def from_env(cls) -> 'RasaConfig':
        """Create Rasa config from environment variables."""
        return cls(
            url=os.getenv('RASA_URL', 'http://rasa:5005'),
            timeout=int(os.getenv('RASA_TIMEOUT', '30')),
            max_retries=int(os.getenv('RASA_MAX_RETRIES', '3')),
            enabled=os.getenv('RASA_ENABLED', 'true').lower() == 'true'
        )


@dataclass
class FileConfig:
    """File processing configuration."""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_files: int = 20
    allowed_extensions: List[str] = None
    upload_folder: str = "uploads"
    temp_folder: str = "temp"
    cleanup_after_hours: int = 24
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.pdf']
    
    @classmethod
    def from_env(cls) -> 'FileConfig':
        """Create file config from environment variables."""
        return cls(
            max_file_size=int(os.getenv('MAX_FILE_SIZE', str(100 * 1024 * 1024))),
            max_files=int(os.getenv('MAX_FILES', '20')),
            allowed_extensions=os.getenv('ALLOWED_EXTENSIONS', '.pdf').split(','),
            upload_folder=os.getenv('UPLOAD_FOLDER', 'uploads'),
            temp_folder=os.getenv('TEMP_FOLDER', 'temp'),
            cleanup_after_hours=int(os.getenv('CLEANUP_AFTER_HOURS', '24'))
        )


@dataclass
class OCRConfig:
    """OCR processing configuration."""
    tesseract_path: Optional[str] = None
    tesseract_config: str = "--oem 3 --psm 6"
    language: str = "spa"
    dpi: int = 200
    max_image_size: int = 4096
    enable_preprocessing: bool = True
    
    @classmethod
    def from_env(cls) -> 'OCRConfig':
        """Create OCR config from environment variables."""
        return cls(
            tesseract_path=os.getenv('TESSERACT_PATH'),
            tesseract_config=os.getenv('TESSERACT_CONFIG', '--oem 3 --psm 6'),
            language=os.getenv('OCR_LANGUAGE', 'spa'),
            dpi=int(os.getenv('OCR_DPI', '200')),
            max_image_size=int(os.getenv('OCR_MAX_IMAGE_SIZE', '4096')),
            enable_preprocessing=os.getenv('OCR_ENABLE_PREPROCESSING', 'true').lower() == 'true'
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_structured: bool = True
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create logging config from environment variables."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            file_path=os.getenv('LOG_FILE'),
            max_file_size=int(os.getenv('LOG_MAX_FILE_SIZE', str(10 * 1024 * 1024))),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5')),
            enable_console=os.getenv('LOG_ENABLE_CONSOLE', 'true').lower() == 'true',
            enable_structured=os.getenv('LOG_ENABLE_STRUCTURED', 'true').lower() == 'true'
        )


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = "dev-secret-key-change-in-production"
    session_timeout: int = 3600  # 1 hour
    max_session_size: int = 1024 * 1024  # 1MB
    enable_csrf: bool = True
    allowed_origins: List[str] = None
    
    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ['*']
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Create security config from environment variables."""
        return cls(
            secret_key=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            session_timeout=int(os.getenv('SESSION_TIMEOUT', '3600')),
            max_session_size=int(os.getenv('MAX_SESSION_SIZE', str(1024 * 1024))),
            enable_csrf=os.getenv('ENABLE_CSRF', 'true').lower() == 'true',
            allowed_origins=os.getenv('ALLOWED_ORIGINS', '*').split(',')
        )


@dataclass
class AppConfig:
    """Main application configuration."""
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5000
    environment: str = "development"
    version: str = "1.0.0"
    
    # Sub-configurations
    database: DatabaseConfig = None
    redis: RedisConfig = None
    neo4j: Neo4jConfig = None
    ai: AIConfig = None
    rasa: RasaConfig = None
    file: FileConfig = None
    ocr: OCRConfig = None
    logging: LoggingConfig = None
    security: SecurityConfig = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig.from_env()
        if self.redis is None:
            self.redis = RedisConfig.from_env()
        if self.neo4j is None:
            self.neo4j = Neo4jConfig.from_env()
        if self.ai is None:
            self.ai = AIConfig.from_env()
        if self.rasa is None:
            self.rasa = RasaConfig.from_env()
        if self.file is None:
            self.file = FileConfig.from_env()
        if self.ocr is None:
            self.ocr = OCRConfig.from_env()
        if self.logging is None:
            self.logging = LoggingConfig.from_env()
        if self.security is None:
            self.security = SecurityConfig.from_env()
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create app config from environment variables."""
        return cls(
            debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5000')),
            environment=os.getenv('FLASK_ENV', 'development'),
            version=os.getenv('APP_VERSION', '1.0.0')
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate required settings
        if not self.security.secret_key or self.security.secret_key == "dev-secret-key-change-in-production":
            if self.environment == "production":
                issues.append("SECRET_KEY must be set in production")
        
        if not self.ai.groq_api_key:
            issues.append("GROQ_API_KEY is required for AI functionality")
        
        # Validate file paths
        if not os.path.exists(self.file.upload_folder):
            try:
                os.makedirs(self.file.upload_folder, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create upload folder: {e}")
        
        if not os.path.exists(self.file.temp_folder):
            try:
                os.makedirs(self.file.temp_folder, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create temp folder: {e}")
        
        # Validate OCR configuration
        if self.ocr.tesseract_path and not os.path.exists(self.ocr.tesseract_path):
            issues.append(f"Tesseract path does not exist: {self.ocr.tesseract_path}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'debug': self.debug,
            'host': self.host,
            'port': self.port,
            'environment': self.environment,
            'version': self.version,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'name': self.database.name,
                'user': self.database.user,
                'ssl_mode': self.database.ssl_mode
            },
            'redis': {
                'host': self.redis.host,
                'port': self.redis.port,
                'db': self.redis.db,
                'ssl': self.redis.ssl
            },
            'ai': {
                'model': self.ai.groq_model,
                'max_tokens': self.ai.max_tokens,
                'temperature': self.ai.temperature,
                'timeout': self.ai.timeout,
                'max_retries': self.ai.max_retries
            },
            'file': {
                'max_file_size': self.file.max_file_size,
                'max_files': self.file.max_files,
                'allowed_extensions': self.file.allowed_extensions,
                'upload_folder': self.file.upload_folder,
                'temp_folder': self.file.temp_folder
            },
            'ocr': {
                'language': self.ocr.language,
                'dpi': self.ocr.dpi,
                'max_image_size': self.ocr.max_image_size,
                'enable_preprocessing': self.ocr.enable_preprocessing
            },
            'logging': {
                'level': self.logging.level,
                'file_path': self.logging.file_path,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count,
                'enable_console': self.logging.enable_console
            },
            'security': {
                'session_timeout': self.security.session_timeout,
                'max_session_size': self.security.max_session_size,
                'enable_csrf': self.security.enable_csrf,
                'allowed_origins': self.security.allowed_origins
            }
        }


# Global configuration instance
config = AppConfig.from_env()

# Validate configuration on import
config_issues = config.validate()
if config_issues:
    logger = logging.getLogger(__name__)
    for issue in config_issues:
        logger.warning(f"Configuration issue: {issue}")
    
    if config.environment == "production":
        raise RuntimeError(f"Configuration validation failed: {config_issues}")


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config


def reload_config():
    """Reload configuration from environment variables."""
    global config
    config = AppConfig.from_env()
    config_issues = config.validate()
    
    if config_issues:
        logger = logging.getLogger(__name__)
        for issue in config_issues:
            logger.warning(f"Configuration issue: {issue}")
    
    return config
