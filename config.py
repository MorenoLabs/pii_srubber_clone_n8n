from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
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
    ENABLE_AUTH: bool = False
    API_USERNAME: Optional[str] = None
    API_PASSWORD: Optional[str] = None

settings = Settings()