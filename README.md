# PII Scrubber API

A lightweight REST API for detecting and masking personally identifiable information (PII) in text using Microsoft Presidio. Designed for easy integration with N8N workflows and internal automation tools.

## Features

- **PII Detection**: Detects names, emails, phone numbers, addresses, credit cards, and more
- **Multi-Language Support**: 
  - English (en) - Full support
  - German (de) - Full support
  - Automatic language detection or explicit language specification
- **Smart Text Preprocessing**: Automatically cleans escape sequences (`\n`, `\t`) and normalizes whitespace to improve PII recognition accuracy - especially useful for JSON-encoded text or text with formatting issues
- **Dual Modes**:
  - `detect`: Only identify PII entities without masking (returns original text with entity locations)
  - `mask`: Apply masking to identified PII entities
- **Multiple Masking Modes**: 
  - `redact`: Replaces with masking characters (e.g., "John" → "████") - **Default**
  - `replace`: Replaces PII with entity type tags (e.g., "John" → "<PERSON>")
  - `hash`: Replaces with hash values for irreversible masking
- **Basic Authentication**: Optional HTTP Basic Auth for secure deployments
- **Configurable**: Specify which entities to detect or skip
- **Fast**: Pre-warmed analyzers for low latency (<300ms for typical payloads)
- **Privacy-First**: No data persistence, minimal logging

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. **Language models are automatically installed** on first startup
   - The API will automatically download required spaCy models:
     - `en_core_web_lg` (English)  
     - `de_core_news_lg` (German)
   - This happens automatically when the server starts for the first time
   - Manual installation (optional): 
     ```bash
     python -m spacy download en_core_web_lg
     python -m spacy download de_core_news_lg
     ```

## Running the API

### Development Mode
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Python directly
```bash
python app.py
```

## API Endpoints

### Health Check
```
GET /health
```

### Mask Text
```
POST /mask
```

#### Request Body
```json
{
  "text": "John Doe lives at 123 Main St and email is john@example.com",
  "mode": "mask",
  "masking_mode": "replace",
  "masking_char": "█",
  "entities": ["PERSON", "EMAIL_ADDRESS", "LOCATION"],
  "skip_entities": ["DATE_TIME"],
  "language": "en"
}
```

#### Parameters
- `text` (required): Text to process
- `mode` (optional): "detect" | "mask" (default: "mask")
  - `detect`: Only identify entities without masking
  - `mask`: Apply masking to identified entities
- `masking_mode` (optional): "replace" | "redact" | "hash" (default: "redact")
- `masking_char` (optional): Character for redaction mode (default: "█")
- `entities` (optional): List of entity types to detect (default: all)
- `skip_entities` (optional): List of entity types to ignore
- `language` (optional): "en" | "de" | null (default: auto-detect)
  - `en`: English
  - `de`: German
  - `null`: Auto-detect language
- `enable_preprocessing` (optional): true | false | null (default: server setting)
  - `true`: Enable text preprocessing (clean escape sequences, normalize whitespace)
  - `false`: Disable preprocessing (use raw text)
  - `null`: Use server default setting

#### Response
```json
{
  "masked_text": "<PERSON> lives at <LOCATION> and email is <EMAIL_ADDRESS>",
  "entities_found": [
    {"entity_type": "PERSON", "start": 0, "end": 8, "score": 0.95},
    {"entity_type": "LOCATION", "start": 18, "end": 28, "score": 0.91},
    {"entity_type": "EMAIL_ADDRESS", "start": 42, "end": 59, "score": 0.99}
  ],
  "processing_time_ms": 52.11,
  "detected_language": "en"
}
```

## Authentication

The API supports optional HTTP Basic Authentication for secure deployments.

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and set authentication parameters:
```
ENABLE_AUTH=true
API_USERNAME=your_username
API_PASSWORD=your_secure_password
```

3. Restart the server to apply changes

### Using Authentication

When authentication is enabled, include credentials in your requests:

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    "http://your-server:8000/mask",
    json={"text": "sample text", "mode": "detect"},
    auth=HTTPBasicAuth("your_username", "your_secure_password")
)
```

## N8N Integration

### HTTP Request Node Configuration

1. **Method**: POST
2. **URL**: `http://your-server:8000/mask`
3. **Authentication**: 
   - Type: Basic Auth (if enabled)
   - Username: Your API username
   - Password: Your API password
4. **Body Content Type**: JSON
5. **Body**:
```json
{
  "text": "{{ $json.message }}",
  "mode": "mask",
  "masking_mode": "replace"
}
```

### Example N8N Workflow

1. **Trigger**: Webhook or any data source
2. **HTTP Request**: Call PII Scrubber API
3. **Set**: Extract `masked_text` from response
4. **Continue**: Use sanitized text in subsequent nodes

### Using Function Node (Alternative)
```javascript
const response = await $http.request({
  method: 'POST',
  url: 'http://your-server:8000/mask',
  body: {
    text: items[0].json.text,
    masking_mode: 'replace',
    entities: ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER']
  },
  returnFullResponse: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

return [{
  json: {
    original: items[0].json.text,
    masked: response.body.masked_text,
    entities: response.body.entities_found
  }
}];
```

## Supported Entity Types

- `PERSON`: Names
- `EMAIL_ADDRESS`: Email addresses
- `PHONE_NUMBER`: Phone numbers
- `LOCATION`: Addresses and locations
- `CREDIT_CARD`: Credit card numbers
- `IBAN_CODE`: International bank account numbers
- `IP_ADDRESS`: IP addresses
- `DATE_TIME`: Dates and times
- `NRP`: National identification numbers
- `MEDICAL_LICENSE`: Medical license numbers
- `URL`: Web URLs

## Language Support

### Automatic Language Detection
The API automatically detects the language of input text and applies the appropriate analyzer:

```bash
# English text - automatically detected
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Contact John Doe at john@example.com",
    "masking_mode": "replace"
  }'

# German text - automatically detected
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Kontaktieren Sie Hans Müller unter hans@beispiel.de",
    "masking_mode": "replace"
  }'
```

### Explicit Language Specification
You can also explicitly specify the language:

```bash
# Explicitly specify German
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Frau Schmidt wohnt in Berlin, Hauptstraße 123",
    "language": "de",
    "masking_mode": "replace"
  }'
```

## Testing

### Running Test Suite

The API includes several test scripts to validate functionality:

```bash
# Start the API server first
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Run core API functionality tests
python test_api.py

# Test authentication features
python test_auth.py

# Test different masking modes
python test_modes.py

# Test German language support
python test_german.py
```

### Testing with cURL

```bash
# Basic test (English)
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Contact John Doe at john@example.com or 555-0123",
    "masking_mode": "replace"
  }'

# With specific entities
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Doe, SSN 123-45-6789, lives at 123 Main St",
    "masking_mode": "redact",
    "entities": ["PERSON", "US_SSN"]
  }'

# Hash mode for consistent masking
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Email john@example.com twice: john@example.com",
    "masking_mode": "hash"
  }'

# German text example
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Herr Müller, geboren am 15.01.1990, E-Mail: mueller@firma.de",
    "language": "de",
    "masking_mode": "replace"
  }'
```

## Configuration

Environment variables can be set to override defaults:

- `MASKING_MODE`: Default masking mode (replace/redact/hash)
- `MASKING_CHAR`: Default character for redaction
- `MAX_TEXT_SIZE`: Maximum text size in characters (default: 50000)
- `ENABLE_LOGGING`: Enable request logging (default: false)
- `HOST`: API host (default: 0.0.0.0)
- `PORT`: API port (default: 8000)
- `SUPPORTED_LANGUAGES`: Comma-separated list of supported languages (default: en,de)
- `DEFAULT_LANGUAGE`: Default language when detection fails (default: en)
- `AUTO_DETECT_LANGUAGE`: Enable automatic language detection (default: true)
- `ENABLE_PREPROCESSING`: Enable text preprocessing to improve PII detection (default: true)

Example:
```bash
export MASKING_MODE=redact
export MAX_TEXT_SIZE=100000
uvicorn app:app
```

## Performance Tips

1. **Pre-warm on startup**: The analyzer is initialized on startup for faster first requests
2. **Keep payloads small**: Best performance with text under 5KB
3. **Use specific entities**: Specifying entities reduces processing time
4. **Run multiple workers**: Use `--workers` flag for production

## Security Considerations

- Run on internal network only
- Use HTTPS in production (via reverse proxy)
- No sensitive data is logged
- All processing is in-memory
- Consider API authentication for production use

## Troubleshooting

### Slow first request
The first request loads NLP models. Subsequent requests will be faster.

### Missing entities
Ensure Presidio language models are downloaded for all supported languages:
```bash
# English model
python -m spacy download en_core_web_lg

# German model
python -m spacy download de_core_news_lg
```

### High memory usage
Reduce worker count or implement request queuing for high-volume scenarios.

## License

Internal use only. Based on Microsoft Presidio (MIT License).