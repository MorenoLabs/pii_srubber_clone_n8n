# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based REST API for detecting and masking personally identifiable information (PII) using Microsoft Presidio. The API is designed for integration with N8N workflows and internal automation tools.

## Key Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Download Presidio language models (required on first setup)
python -m spacy download en_core_web_lg  # English
python -m spacy download de_core_news_lg  # German

# Run in development mode with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Run directly with Python
python app.py
```

### Production
```bash
# Run with multiple workers
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing
```bash
# Run basic API tests (requires running server)
python test_api.py

# Test authentication functionality
python test_auth.py

# Test different masking modes
python test_modes.py

# Test German language support
python test_german.py
```

## Architecture

### Core Components

1. **app.py**: Main FastAPI application containing:
   - `/health` endpoint for monitoring
   - `/mask` endpoint for PII detection and masking
   - Authentication middleware using HTTPBasic
   - Multi-language Presidio analyzers (English, German) pre-warmed
   - Automatic language detection using langdetect library
   - Built-in text preprocessing to improve PII recognition accuracy
   - Support for multiple masking modes (redact, replace, hash)

2. **config.py**: Pydantic settings management using environment variables
   - Configurable masking defaults
   - Language settings (supported languages, auto-detection)
   - Text preprocessing settings
   - Optional authentication settings
   - Server configuration (host, port)

3. **Testing Suite**: Standalone Python scripts that test API endpoints
   - No pytest/unittest framework - direct HTTP requests
   - Tests cover authentication, masking modes, entity detection, and language support
   - test_german.py specifically tests German language PII detection

### Request Flow

1. Request arrives at `/mask` endpoint with text and configuration
2. Optional authentication check (if enabled via ENABLE_AUTH)
3. Text validation (size limits, required fields)
4. Apply text preprocessing (if enabled) to clean escape sequences and normalize whitespace
5. Language detection (auto-detect or use specified language)
6. Select appropriate Presidio Analyzer for detected language
7. Presidio Analyzer detects PII entities in the processed text
8. Based on mode ("detect" or "mask"):
   - detect: Returns entity locations without modification
   - mask: Applies anonymization based on masking_mode
9. Returns masked text with entity metadata, processing time, and detected language

### Key Design Decisions

- **Pre-warmed engines**: Presidio analyzers for each language initialized on startup for faster responses
- **Multi-language support**: Separate analyzers for English and German with automatic detection
- **Stateless processing**: No data persistence, all processing in-memory
- **Minimal logging**: Privacy-first approach with optional logging
- **Flexible masking**: Support for redact, replace, and hash modes
- **Authentication**: Optional HTTP Basic Auth for production deployments

## Entity Types Supported

Main entities handled by the API:
- PERSON, EMAIL_ADDRESS, PHONE_NUMBER
- LOCATION, CREDIT_CARD, IBAN_CODE
- IP_ADDRESS, DATE_TIME, URL
- NRP, MEDICAL_LICENSE, US_SSN

## Configuration

Environment variables (set in .env file or system):
- `ENABLE_AUTH`: Enable/disable authentication
- `API_USERNAME` / `API_PASSWORD`: Authentication credentials
- `MASKING_MODE`: Default mode (redact/replace/hash)
- `MASKING_CHAR`: Character for redaction
- `MAX_TEXT_SIZE`: Maximum text size limit
- `ENABLE_LOGGING`: Enable request logging
- `SUPPORTED_LANGUAGES`: List of supported languages (default: ["en", "de"])
- `DEFAULT_LANGUAGE`: Fallback language when detection fails (default: "en")
- `AUTO_DETECT_LANGUAGE`: Enable automatic language detection (default: true)
- `ENABLE_PREPROCESSING`: Enable text preprocessing to improve PII detection (default: true)
