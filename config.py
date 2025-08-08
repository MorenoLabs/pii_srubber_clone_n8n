from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MASKING_MODE: str = "redact"  # replace | redact | hash
    MASKING_CHAR: str = "█"
    MAX_TEXT_SIZE: int = 50_000  # 50 KB
    ENABLE_LOGGING: bool = False  # Minimal logging for privacy
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Basic Authentication (disabled by default)
    ENABLE_AUTH: bool = False
    API_USERNAME: Optional[str] = None
    API_PASSWORD: Optional[str] = None

settings = Settings()