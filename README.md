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
API_PASSWORD=your_secure_password_min_12_chars
MIN_PASSWORD_LENGTH=12
```

3. Restart the server to apply changes

### Security Features
- **Password strength validation**: Minimum password length enforcement (default: 12 characters)
- **Failed attempt logging**: Authentication failures are logged for monitoring
- **Constant-time comparison**: Secure credential validation using `secrets.compare_digest()`
- **Configurable authentication**: Can be enabled/disabled via environment variables

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

The PII Scrubber API implements comprehensive security measures for production deployment:

### Built-in Security Features

#### 1. **Authentication & Authorization**
- **HTTP Basic Authentication** with configurable credentials
- **Constant-time credential comparison** preventing timing attacks
- **Password strength validation** (minimum 12 characters)
- **Failed authentication logging** for monitoring
- **Environment-based configuration** for secure credential management

#### 2. **Rate Limiting & Brute Force Protection**
- **Per-IP rate limiting** (default: 30 requests/minute)
- **Configurable burst limits** to handle legitimate traffic spikes
- **Automatic blocking** of excessive requests
- **Rate limit headers** provided in responses

#### 3. **CORS (Cross-Origin Resource Sharing) Protection**
- **Restricted origins** - only specific domains allowed (configurable)
- **Limited HTTP methods** - only GET and POST allowed
- **Controlled headers** - only necessary headers permitted
- **Credentials handling** - configurable credential allowance

#### 4. **DoS (Denial of Service) Protection**
- **Request size limits** (1MB default) to prevent memory exhaustion
- **Processing timeouts** (30s default) to prevent resource starvation
- **Entity count limits** (100 entities max) to prevent excessive processing
- **Text size validation** (50KB default) for performance optimization

#### 5. **Input Validation & Sanitization**
- **Subprocess security** - whitelisted spaCy models only
- **Regex validation** for model names preventing injection attacks
- **Request size validation** at multiple levels
- **Parameter validation** with strict type checking

#### 6. **Secure Coding Practices**
- **No sensitive data logging** - only metadata is recorded
- **Memory-only processing** - no data persistence
- **Constant-time operations** for security-sensitive comparisons
- **Proper error handling** preventing information leakage
- **Secure defaults** in all configuration options

### Production Deployment Recommendations

#### Infrastructure Security
- **Internal network deployment** - avoid public internet exposure
- **HTTPS termination** via reverse proxy (nginx/Apache)
- **Web Application Firewall (WAF)** for additional protection
- **Network segmentation** to isolate the API service
- **Resource monitoring** to detect anomalous usage patterns

#### Configuration Security
```bash
# Essential production settings in .env
ENABLE_AUTH=true
API_USERNAME=secure_admin_user
API_PASSWORD=very_strong_password_min_12_chars
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
RATE_LIMIT_PER_MINUTE=10  # Stricter limits for production
MAX_PROCESSING_TIME=15    # Lower timeout for production
ENABLE_LOGGING=true       # Enable security monitoring
```

#### Monitoring & Alerting
- **Failed authentication attempts** - monitor logs for brute force attacks
- **Rate limit violations** - track IPs hitting limits frequently
- **Processing timeouts** - monitor for potential DoS attempts
- **Resource usage** - CPU and memory consumption patterns
- **Error rates** - unusual error patterns may indicate attacks

#### Additional Security Layers
Consider implementing these additional security measures:

1. **API Gateway** (AWS API Gateway, Kong, etc.)
   - Additional rate limiting and throttling
   - API key management
   - Request/response transformation
   - Advanced analytics and monitoring

2. **Container Security** (if using Docker)
   - Non-root user execution
   - Read-only filesystem
   - Minimal base image
   - Security scanning of images

3. **Network Security**
   - VPC/private subnet deployment
   - Security groups with minimal access
   - Load balancer with SSL termination
   - DDoS protection services

4. **Compliance & Auditing**
   - Regular security assessments
   - Dependency vulnerability scanning
   - Access log retention and analysis
   - Incident response procedures

### Security Testing
The API includes security testing capabilities:

```bash
# Test authentication security
python3 test_auth.py

# Test rate limiting (run multiple times quickly)
for i in {1..50}; do curl -X POST http://localhost:8000/mask -H "Content-Type: application/json" -d '{"text":"test"}' & done

# Test DoS protection with large payloads
curl -X POST http://localhost:8000/mask -H "Content-Type: application/json" -d '{"text":"'$(head -c 100000 </dev/zero | tr '\0' 'A')'"}' 
```

### Security Incident Response
In case of security incidents:

1. **Immediate Response**
   - Block suspicious IP addresses at firewall/WAF level
   - Temporarily disable API if under severe attack
   - Increase logging verbosity for investigation

2. **Investigation**
   - Review authentication logs for failed attempts
   - Check rate limiting logs for patterns
   - Monitor resource usage for anomalies
   - Examine error logs for attack vectors

3. **Recovery**
   - Update credentials if compromised
   - Implement additional rate limiting if needed
   - Apply security patches promptly
   - Review and update security configurations

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