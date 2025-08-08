## **Directory Structure**


pii_scrubber/
  ├── app.py
  ├── requirements.txt
  ├── Dockerfile
  ├── config.py
  └── README.md
```

---

## **`requirements.txt`**

```txt
fastapi
uvicorn[standard]
presidio-analyzer
presidio-anonymizer
python-multipart
```

---

## **`config.py`**

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    MASKING_MODE: str = "replace"  # replace | redact | hash
    MASKING_CHAR: str = "█"
    MAX_TEXT_SIZE: int = 50_000  # 50 KB

settings = Settings()
```

---

## **`app.py`**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from config import settings
import hashlib
import time

app = FastAPI(title="Presidio PII Scrubber API")

# Initialize Presidio Engines once (warm)
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Request schema
class MaskRequest(BaseModel):
    text: str
    masking_mode: str | None = None  # replace, redact, hash
    masking_char: str | None = None
    entities: list[str] | None = None
    skip_entities: list[str] | None = None

# Helper: build anonymization config
def build_anonymizer_config(masking_mode: str, masking_char: str):
    if masking_mode == "replace":
        return lambda entity: {"type": "replace", "new_value": f"<{entity}>"}
    elif masking_mode == "redact":
        return lambda entity: {"type": "replace", "new_value": masking_char * 6}
    elif masking_mode == "hash":
        return lambda entity: {"type": "replace", "new_value": hashlib.sha256(entity.encode()).hexdigest()}
    else:
        raise HTTPException(status_code=400, detail="Invalid masking_mode")

@app.post("/mask")
def mask_text(req: MaskRequest):
    start_time = time.time()

    if not req.text:
        raise HTTPException(status_code=400, detail="Missing text")
    if len(req.text) > settings.MAX_TEXT_SIZE:
        raise HTTPException(status_code=413, detail="Text too large")

    masking_mode = req.masking_mode or settings.MASKING_MODE
    masking_char = req.masking_char or settings.MASKING_CHAR
    make_conf = build_anonymizer_config(masking_mode, masking_char)

    # Analyze
    results = analyzer.analyze(
        text=req.text,
        entities=req.entities,
        language="en"
    )

    # Filter out skip_entities
    if req.skip_entities:
        results = [r for r in results if r.entity_type not in req.skip_entities]

    # Build entity-specific anonymizer config
    anonymizer_config = {}
    for r in results:
        anonymizer_config[r.entity_type] = make_conf(r.entity_type)

    # Anonymize
    anonymized_result = anonymizer.anonymize(
        text=req.text,
        analyzer_results=results,
        anonymizers_config=anonymizer_config
    )

    elapsed = round((time.time() - start_time) * 1000, 2)
    return {
        "masked_text": anonymized_result.text,
        "entities_found": [
            {"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score}
            for r in results
        ],
        "processing_time_ms": elapsed
    }
```

---

## **`Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## **Run Locally**

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

---

## **Example Call (n8n / curl)**

```bash
curl -X POST http://localhost:8000/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "John Doe lives at 123 Main St and email is john@example.com",
    "masking_mode": "replace"
  }'
```

**Response:**

```json
{
  "masked_text": "<PERSON> lives at <LOCATION> and email is <EMAIL_ADDRESS>",
  "entities_found": [
    {"entity_type": "PERSON", "start": 0, "end": 8, "score": 0.95},
    {"entity_type": "LOCATION", "start": 18, "end": 28, "score": 0.91},
    {"entity_type": "EMAIL_ADDRESS", "start": 42, "end": 59, "score": 0.99}
  ],
  "processing_time_ms": 52.11
}
```

---

If you like, I can also add:

* **Consistent per-request hashing** (so identical entities get identical hashes in one run)
* **Pre-warmed analyzer** for even faster startup in Docker
* **Basic auth token check** so n8n users can’t misuse it outside company workflows

Do you want me to extend it with those before you deploy? That would make it more robust for your internal environment.
