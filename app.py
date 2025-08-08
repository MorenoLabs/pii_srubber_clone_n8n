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
from typing import Optional, List, Dict, Any

# Configure minimal logging
if settings.ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
else:
    logger = None

app = FastAPI(
    title="Presidio PII Scrubber API",
    description="Lightweight API for PII detection and masking using Microsoft Presidio",
    version="1.0.0"
)

# Initialize Presidio Engines once (warm start)
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

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

# Response schema
class MaskResponse(BaseModel):
    masked_text: str
    entities_found: List[Dict[str, Any]]
    processing_time_ms: float

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
    
    try:
        # Analyze text for PII
        analysis_results = analyzer.analyze(
            text=req.text,
            entities=req.entities,
            language="en"
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
                logger.info(f"Processed text (detect mode): size={len(req.text)}, entities_found={len(analysis_results)}, time={elapsed_ms}ms")
            
            # Prepare response with original text
            response = MaskResponse(
                masked_text=req.text,  # Return original text in detect mode
                entities_found=[
                    {
                        "entity_type": r.entity_type,
                        "start": r.start,
                        "end": r.end,
                        "score": round(r.score, 3)
                    }
                    for r in analysis_results
                ],
                processing_time_ms=elapsed_ms
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
                        {"new_value": f"<HASH:{hashlib.sha256(req.text[result.start:result.end].encode()).hexdigest()[:8]}>"}
                    )
            else:
                operators = build_anonymizer_config(masking_mode, masking_char, analysis_results)
            
            # Anonymize the text
            anonymized_result = anonymizer.anonymize(
                text=req.text,
                analyzer_results=analysis_results,
                operators=operators if operators else None
            )
            
            # Calculate processing time
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log metadata only (no sensitive data)
            if logger:
                logger.info(f"Processed text (mask mode): size={len(req.text)}, entities_found={len(analysis_results)}, time={elapsed_ms}ms")
            
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
                processing_time_ms=elapsed_ms
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