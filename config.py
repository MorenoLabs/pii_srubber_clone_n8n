from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    MASKING_MODE: str = "redact"  # replace | redact | hash
    MASKING_CHAR: str = "█"
    MAX_TEXT_SIZE: int = 50_000  # 50 KB
    ENABLE_LOGGING: bool = False  # Minimal logging for privacy
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Language settings
    SUPPORTED_LANGUAGES: List[str] = ["en", "de"]  # English and German
    DEFAULT_LANGUAGE: str = "en"  # Default to English if detection fails
    AUTO_DETECT_LANGUAGE: bool = True  # Enable automatic language detection
    
    # Text preprocessing settings
    ENABLE_PREPROCESSING: bool = True  # Enable text preprocessing to improve PII detection
    
    # Basic Authentication (disabled by default)
    ENABLE_AUTH: bool = True
    API_USERNAME: Optional[str] = None
    API_PASSWORD: Optional[str] = None
    
    # Security settings
    MIN_PASSWORD_LENGTH: int = 12  # Minimum password length when auth is enabled
    
    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = 30  # Max requests per minute per IP
    RATE_LIMIT_BURST: int = 10  # Max burst requests before rate limiting kicks in
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]  # Allowed origins
    CORS_ALLOW_CREDENTIALS: bool = False
    
    # DoS Protection settings
    MAX_PROCESSING_TIME: int = 30  # Maximum processing time in seconds
    MAX_ENTITIES_PER_REQUEST: int = 100  # Maximum number of entities to process
    MAX_REQUEST_SIZE: int = 1_000_000  # 1MB max request size in bytes

settings = Settings()