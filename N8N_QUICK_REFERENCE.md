# PII Scrubber API Demo (EN/DE) - N8N Quick Reference
using [Presidio](https://microsoft.github.io/presidio/) and [Spacy](https://spacy.io/)

## API Endpoint
```
http://your-server:8000/mask
```

## Basic Usage (HTTP Request Node)

### 1. Detect Only (Find PII without masking)
```json
{
  "text": "{{ $json.text }}",
  "mode": "detect"
}
```
Returns original text + entity locations

### 2. Mask PII (Default: Redact with █████)
```json
{
  "text": "{{ $json.text }}",
  "mode": "mask"
}
```

### 3. Replace with Entity Tags
```json
{
  "text": "{{ $json.text }}",
  "mode": "mask",
  "masking_mode": "replace"
}
```
Example: "John Smith" → "<PERSON>"

### 4. Hash PII Values
```json
{
  "text": "{{ $json.text }}",
  "mode": "mask",
  "masking_mode": "hash"
}
```

## Multi-Language Support 🌍

### Auto-Detect Language (Default)
```json
{
  "text": "{{ $json.text }}",
  "mode": "mask"
}
```
Automatically detects English or German

### Specify Language Explicitly
```json
{
  "text": "{{ $json.text }}",
  "mode": "mask",
  "language": "de"
}
```
- `"en"` - English
- `"de"` - German (Deutsch)

### German Example
```json
{
  "text": "Liebe Frau Schmidt, Ihre E-Mail anna@firma.de wurde erhalten.",
  "mode": "mask",
  "masking_mode": "replace",
  "language": "de"
}
```
Result: `"Liebe <PERSON>, Ihre E-Mail <EMAIL_ADDRESS> wurde erhalten."`

## Text Preprocessing ⚡

### Enable/Disable Preprocessing
```json
{
  "text": "{{ $json.text }}",
  "enable_preprocessing": true
}
```
- `true` - Clean escape sequences (\n, \t), normalize whitespace (recommended)
- `false` - Use raw text as-is
- `null` - Use server default (true)

**💡 Tip:** Preprocessing significantly improves PII detection accuracy, especially for JSON-encoded text!

## Filter Entity Types

### Only Detect Specific Entities
```json
{
  "text": "{{ $json.text }}",
  "entities": ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
}
```

### Skip Certain Entities
```json
{
  "text": "{{ $json.text }}",
  "skip_entities": ["DATE_TIME", "URL"]
}
```

## Response Structure
```json
{
  "masked_text": "processed text here",
  "entities_found": [
    {
      "entity_type": "PERSON",
      "start": 0,
      "end": 8,
      "score": 0.95
    }
  ],
  "processing_time_ms": 52.11,
  "detected_language": "de"
}
```

## Common Entity Types
- `PERSON` - Names (Hans Müller, John Smith)
- `EMAIL_ADDRESS` - Emails
- `PHONE_NUMBER` - Phone numbers (+49 30 12345678)
- `LOCATION` - Addresses, cities (Berlin, München)
- `CREDIT_CARD` - Card numbers
- `IP_ADDRESS` - IP addresses
- `DATE_TIME` - Dates/times
- `URL` - Web URLs
- `IBAN_CODE` - Bank account numbers
- `NRP` - National registration plates

## N8N Workflow Examples

### 1. Basic HTTP Request Node Settings:
- **Method:** `POST`
- **URL:** `http://your-server:8000/mask`
- **Body Content Type:** `JSON`
- **Body:** See examples above

### 2. Extract Results:
- **Cleaned text:** `{{ $json.masked_text }}`
- **Entity list:** `{{ $json.entities_found }}`
- **Detected language:** `{{ $json.detected_language }}`
- **Processing time:** `{{ $json.processing_time_ms }}`

### 3. Multi-Language Processing:
```json
{
  "text": "{{ $json.message }}",
  "masking_mode": "replace",
  "language": "{{ $json.detected_lang || 'auto' }}"
}
```

### 4. Conditional Processing Based on Language:
Use IF node with: `{{ $json.detected_language === 'de' }}`

## Advanced Patterns

### Chain Multiple Strategies
1. First call: `"mode": "detect"` to analyze
2. Second call: Apply different masking based on entity types found

### Batch Processing
- Use **Split In Batches** node for multiple texts
- Process arrays of messages/documents

### Smart Routing
- Use **IF** node: `{{ $json.entities_found.length > 0 }}`
- Route texts with/without PII differently

## Authentication (if enabled)
Add credentials in HTTP Request node:
- **Authentication:** `Basic Auth`
- **Username:** `your_username`
- **Password:** `your_password`

## Performance Tips ⚡
- First request loads models (~500ms), subsequent requests <50ms
- Enable preprocessing for better accuracy
- Specify language explicitly if known
- Use "detect" mode first for analysis workflows
- Process smaller text chunks for optimal performance

## Error Handling
Common HTTP status codes:
- `200` - Success
- `400` - Invalid parameters
- `413` - Text too large (>50KB default)
- `500` - Processing error

## Quick Test
```bash
curl -X POST http://your-server:8000/mask \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact John at john@test.com", "masking_mode": "replace"}'
```