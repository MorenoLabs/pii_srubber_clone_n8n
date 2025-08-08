
# **Product Requirements Document (PRD)**

**Project:** Presidio-Based PII Scrubber / Masker API
**Author:** Buddy
**Date:** 2025-08-08
**Status:** Draft

---

## **1. Overview**

The Presidio-Based PII Scrubber / Masker API is a lightweight internal service that detects and obfuscates personally identifiable information (PII) in text payloads. It will be hosted on the company’s internal network and accessible to **n8n workflow modules** via simple REST calls.

This allows automation workflows to preprocess sensitive data before storage, transmission, or AI processing, ensuring compliance with data protection policies (e.g., GDPR).

---

## **2. Goals & Objectives**

**Goals:**

* Provide a **production-grade but lightweight** REST API for PII detection and masking.
* Integrate with **Microsoft Presidio** for entity recognition and masking.
* Allow **configurable masking strategies** per request (e.g., `replace`, `redact`, `hash`).
* Be **easy to call from n8n** with minimal configuration.

**Objectives:**

* Support JSON input and output.
* Ensure high availability and low latency (<300ms for average payloads).
* Maintain consistent masking patterns for identical entities within a request.
* Avoid storing any payloads to disk or logs (privacy by design).

---

## **3. Key Features**

| Feature                           | Description                                                                                                                                         | Priority |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| **PII Detection**                 | Detect common PII types (Names, Emails, Phone numbers, Addresses, Credit Cards, IBAN, Passport Numbers, National IDs, Dates) via Presidio Analyzer. | High     |
| **Masking Modes**                 | `replace` (e.g., "John Doe" → "<NAME>"), `redact` (e.g., "John Doe" → "██████"), `hash` (e.g., SHA256 for irreversible replacement).                | High     |
| **Entity Whitelisting**           | Allow skipping masking for selected entity types (e.g., dates).                                                                                     | Medium   |
| **Multi-Entity Mask Consistency** | Identical values replaced with identical masks within a single request.                                                                             | High     |
| **Stateless Operation**           | No persistence; data processed in-memory only.                                                                                                      | High     |
| **Simple REST API**               | `/mask` endpoint accepting POST with JSON payload.                                                                                                  | High     |
| **n8n Ready**                     | Endpoint accepts `application/json` with `text` key so n8n HTTP Request node can pass variables directly.                                           | High     |
| **Logging Controls**              | Only minimal request metadata logged (timestamp, request size, processing time).                                                                    | High     |

---

## **4. Non-Goals**

* No front-end UI.
* No batch file processing (text only).
* No external API exposure — internal network only.

---

## **5. API Specification**

**Endpoint:**

```
POST /mask
```

**Request Body (JSON):**

```json
{
  "text": "John Doe's email is john.doe@example.com and phone is +49 170 1234567",
  "masking_mode": "replace",  
  "masking_char": "*",         
  "entities": ["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON"],  
  "skip_entities": ["DATE_TIME"]
}
```

**Parameters:**

* `text` *(string, required)* – Text to process.
* `masking_mode` *(string, optional)* – `"replace" | "redact" | "hash"`, default `"replace"`.
* `masking_char` *(string, optional)* – Character for redaction (default `"█"`).
* `entities` *(array, optional)* – Explicitly define which PII entity types to detect; default: all Presidio-supported.
* `skip_entities` *(array, optional)* – List of entity types to ignore.

**Response Example:**

```json
{
  "masked_text": "<PERSON>'s email is <EMAIL_ADDRESS> and phone is <PHONE_NUMBER>",
  "entities_found": [
    {"entity_type": "PERSON", "start": 0, "end": 8, "score": 0.95},
    {"entity_type": "EMAIL_ADDRESS", "start": 21, "end": 42, "score": 0.99},
    {"entity_type": "PHONE_NUMBER", "start": 56, "end": 71, "score": 0.92}
  ]
}
```

**Error Responses:**

* `400 Bad Request` – Missing `text` or invalid JSON.
* `500 Internal Server Error` – Unexpected processing error.

---

## **6. Performance & Scalability**

* Target: <300ms for text ≤5KB.
* Horizontal scaling possible via container orchestration (K8s/Docker Swarm).
* Limit: Max payload size 50KB per request.

---

## **7. Security & Compliance**

* API available **only on internal VLAN**.
* HTTPS enforced.
* No sensitive data persisted (memory-only).
* Minimal logs (no raw text logged).

---

## **8. Tech Stack**

* **Language:** Python 3.12
* **Framework:** FastAPI
* **PII Engine:** Microsoft Presidio (`presidio-analyzer`, `presidio-anonymizer`)
* **Logging:** Python `logging` + centralized ELK (metadata only)

---

## **9. Example n8n Usage**

**HTTP Request Node:**

* Method: POST
* URL: `http://pii-scrubber.internal/mask`
* Body: JSON with `{{ $json["message"] }}` as `text`
* Response: Use `masked_text` in subsequent nodes.
