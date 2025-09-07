from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from config import settings
import hashlib
import time
import logging
import secrets
import re
import subprocess
import sys
from typing import Optional, List, Dict, Any
from langdetect import detect, detect_langs, LangDetectException

# Configure minimal logging
if settings.ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
else:
    logger = None

# Helper: Check if spaCy model is installed
def is_spacy_model_installed(model_name: str) -> bool:
    """Check if a spaCy model is installed."""
    try:
        import spacy
        spacy.load(model_name)
        return True
    except OSError:
        return False

# Helper: Install spaCy model
def install_spacy_model(model_name: str) -> bool:
    """Install a spaCy model using subprocess."""
    try:
        print(f"Installing spaCy model: {model_name}")
        result = subprocess.run([
            sys.executable, "-m", "spacy", "download", model_name
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print(f"✓ Successfully installed {model_name}")
            return True
        else:
            print(f"✗ Failed to install {model_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout installing {model_name}")
        return False
    except Exception as e:
        print(f"✗ Error installing {model_name}: {str(e)}")
        return False

# Helper: Ensure required spaCy models are installed
def ensure_spacy_models():
    """Ensure all required spaCy models are installed."""
    required_models = {
        "en": "en_core_web_lg",
        "de": "de_core_news_lg"
    }
    
    print("Checking required spaCy models...")
    
    for lang, model_name in required_models.items():
        if not is_spacy_model_installed(model_name):
            print(f"Model {model_name} not found. Installing...")
            if not install_spacy_model(model_name):
                print(f"WARNING: Failed to install {model_name}. {lang} language support may not work properly.")
        else:
            print(f"✓ Model {model_name} is already installed")
    
    print("spaCy model check completed.")

app = FastAPI(
    title="Presidio PII Scrubber API",
    description="Lightweight API for PII detection and masking using Microsoft Presidio",
    version="1.0.0"
)

# Ensure required spaCy models are installed before initializing engines
ensure_spacy_models()

# Initialize Presidio Engines for supported languages (warm start)
# For German, we need to configure with the proper nlp model
from presidio_analyzer.nlp_engine import NlpEngineProvider

# Configure NLP engine provider for German
configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_lg"},
        {"lang_code": "de", "model_name": "de_core_news_lg"}
    ]
}

# Create NLP engine provider
provider = NlpEngineProvider(nlp_configuration=configuration)

# Initialize analyzers with the provider
analyzers = {
    "en": AnalyzerEngine(nlp_engine=provider.create_engine()),
    "de": AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["de"])
}
anonymizer = AnonymizerEngine()

# Language code mapping for detection
LANGUAGE_MAP = {
    "en": "en",
    "de": "de",
    "eng": "en",
    "deu": "de",
    "ger": "de"
}

# Initialize Basic Auth
security = HTTPBasic(auto_error=False)

def get_current_user(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    """Verify basic authentication credentials if auth is enabled."""
    if not settings.ENABLE_AUTH:
        return "anonymous"
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not settings.API_USERNAME or not settings.API_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is enabled but credentials are not configured"
        )
    
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        settings.API_USERNAME.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        settings.API_PASSWORD.encode("utf8")
    )
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

# Request schema
class MaskRequest(BaseModel):
    text: str
    mode: Optional[str] = "mask"  # "detect" for entity names only, "mask" for actual masking
    masking_mode: Optional[str] = None  # replace, redact, hash
    masking_char: Optional[str] = None
    entities: Optional[List[str]] = None
    skip_entities: Optional[List[str]] = None
    language: Optional[str] = None  # Explicitly specify language (en, de) or auto-detect if None
    enable_preprocessing: Optional[bool] = None  # Override default preprocessing setting

# Response schema
class MaskResponse(BaseModel):
    masked_text: str
    entities_found: List[Dict[str, Any]]
    processing_time_ms: float
    detected_language: Optional[str] = None

# Helper: preprocess text to improve PII recognition
def preprocess_text(text: str) -> str:
    """
    Clean and preprocess text to improve PII entity recognition.
    
    This function:
    - Converts escape sequences (\\n, \\t) to actual whitespace
    - Normalizes multiple consecutive whitespace characters to single spaces
    - Removes or normalizes other problematic characters that interfere with NLP models
    - Preserves the overall structure and meaning of the text
    
    Args:
        text (str): Raw input text that may contain escape sequences
        
    Returns:
        str: Cleaned text optimized for PII detection
    """
    if not text:
        return text
    
    # Convert escape sequences to actual characters
    processed = text.replace('\\n', ' ').replace('\\t', ' ')
    
    # Normalize multiple whitespace characters to single spaces
    processed = re.sub(r'\s+', ' ', processed)
    
    # Remove leading/trailing whitespace
    processed = processed.strip()
    
    return processed

# Helper: detect language of text
def detect_text_language(text: str, fallback: str = "en") -> str:
    """
    Detect the language of the input text.
    Returns ISO 639-1 language code (en, de).
    """
    try:
        # Try to detect language
        detected = detect(text)
        
        # Map detected language to supported languages
        if detected in LANGUAGE_MAP:
            lang = LANGUAGE_MAP[detected]
            if lang in settings.SUPPORTED_LANGUAGES:
                return lang
        
        # If detected language is not supported, return fallback
        return fallback
    except LangDetectException:
        # If detection fails, return fallback
        return fallback

# Helper: build anonymization config
def build_anonymizer_config(masking_mode: str, masking_char: str, results):
    """
    Build anonymizer configuration based on masking mode.
    For consistent hashing within a request, we'll use entity value as salt.
    """
    operators = {}
    
    for result in results:
        entity_type = result.entity_type
        
        if masking_mode == "replace":
            operators[entity_type] = OperatorConfig(
                "replace",
                {"new_value": f"<{entity_type}>"}
            )
        elif masking_mode == "redact":
            operators[entity_type] = OperatorConfig(
                "replace",
                {"new_value": masking_char * 6}
            )
        elif masking_mode == "hash":
            # For consistent hashing, we use SHA256
            operators[entity_type] = OperatorConfig(
                "custom",
                {"lambda": lambda x: hashlib.sha256(x.encode()).hexdigest()[:12]}
            )
    
    return operators

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "pii-scrubber"}

@app.post("/mask", response_model=MaskResponse)
async def mask_text(
    req: MaskRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Main endpoint for PII detection and masking.
    
    Accepts text and masking configuration, returns masked text
    with metadata about detected entities.
    """
    start_time = time.time()
    
    # Validate input
    if not req.text:
        raise HTTPException(status_code=400, detail="Missing text in request body")
    
    if len(req.text) > settings.MAX_TEXT_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"Text too large. Maximum size is {settings.MAX_TEXT_SIZE} characters"
        )
    
    # Apply text preprocessing if enabled
    original_text = req.text
    preprocessing_enabled = req.enable_preprocessing if req.enable_preprocessing is not None else settings.ENABLE_PREPROCESSING
    
    if preprocessing_enabled:
        processed_text = preprocess_text(req.text)
        if logger:
            logger.info(f"Text preprocessing applied: original_length={len(original_text)}, processed_length={len(processed_text)}")
    else:
        processed_text = req.text
    
    # Validate mode
    if req.mode not in ["detect", "mask"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode. Must be: detect or mask"
        )
    
    # Get masking configuration
    masking_mode = req.masking_mode or settings.MASKING_MODE
    masking_char = req.masking_char or settings.MASKING_CHAR
    
    # Validate masking mode (only if in mask mode)
    if req.mode == "mask" and masking_mode not in ["replace", "redact", "hash"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid masking_mode. Must be: replace, redact, or hash"
        )
    
    # Determine language to use
    if req.language:
        # Use explicitly specified language
        if req.language not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {req.language}. Supported languages: {', '.join(settings.SUPPORTED_LANGUAGES)}"
            )
        detected_language = req.language
    elif settings.AUTO_DETECT_LANGUAGE:
        # Auto-detect language using processed text for better accuracy
        detected_language = detect_text_language(processed_text, settings.DEFAULT_LANGUAGE)
    else:
        # Use default language
        detected_language = settings.DEFAULT_LANGUAGE
    
    # Get the appropriate analyzer for the detected language
    if detected_language not in analyzers:
        raise HTTPException(
            status_code=500,
            detail=f"Analyzer not configured for language: {detected_language}"
        )
    
    analyzer = analyzers[detected_language]
    
    try:
        # Analyze processed text for PII
        analysis_results = analyzer.analyze(
            text=processed_text,
            entities=req.entities,
            language=detected_language
        )
        
        # Filter out skip_entities if provided
        if req.skip_entities:
            analysis_results = [
                r for r in analysis_results 
                if r.entity_type not in req.skip_entities
            ]
        
        # If mode is "detect", just return entity information without masking
        if req.mode == "detect":
            # Calculate processing time
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log metadata only (no sensitive data)
            if logger:
                logger.info(f"Processed text (detect mode): size={len(original_text)}, entities_found={len(analysis_results)}, time={elapsed_ms}ms")
            
            # Prepare response with original text
            response = MaskResponse(
                masked_text=original_text,  # Return original text in detect mode
                entities_found=[
                    {
                        "entity_type": r.entity_type,
                        "start": r.start,
                        "end": r.end,
                        "score": round(r.score, 3)
                    }
                    for r in analysis_results
                ],
                processing_time_ms=elapsed_ms,
                detected_language=detected_language
            )
        else:
            # Mode is "mask" - perform actual masking
            # Build anonymizer configuration
            if masking_mode == "hash":
                # For hash mode, use custom operators
                operators = {}
                for result in analysis_results:
                    entity_type = result.entity_type
                    operators[entity_type] = OperatorConfig(
                        "replace",
                        {"new_value": f"<HASH:{hashlib.sha256(processed_text[result.start:result.end].encode()).hexdigest()[:8]}>"}
                    )
            else:
                operators = build_anonymizer_config(masking_mode, masking_char, analysis_results)
            
            # Anonymize the processed text
            anonymized_result = anonymizer.anonymize(
                text=processed_text,
                analyzer_results=analysis_results,
                operators=operators if operators else None
            )
            
            # Calculate processing time
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log metadata only (no sensitive data)
            if logger:
                logger.info(f"Processed text (mask mode): size={len(original_text)}, entities_found={len(analysis_results)}, time={elapsed_ms}ms")
            
            # Prepare response
            response = MaskResponse(
                masked_text=anonymized_result.text,
                entities_found=[
                    {
                        "entity_type": r.entity_type,
                        "start": r.start,
                        "end": r.end,
                        "score": round(r.score, 3)
                    }
                    for r in analysis_results
                ],
                processing_time_ms=elapsed_ms,
                detected_language=detected_language
            )
        
        return response
        
    except Exception as e:
        if logger:
            logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler to prevent sensitive data leakage."""
    if logger:
        logger.error(f"Unhandled exception: {type(exc).__name__}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )