#!/usr/bin/env python3
import requests
import json

# Test server URL
BASE_URL = "http://localhost:8000"

# Test text with various PII entities
test_text = "John Smith's email is john.smith@example.com and his phone is 555-123-4567."

print("Testing PII Scrubber API Modes\n")
print("=" * 50)
print(f"Test text: {test_text}")
print("=" * 50)

# Test 1: Detect mode - only identify entities without masking
print("\n1. Testing DETECT mode (entity identification only):")
detect_response = requests.post(
    f"{BASE_URL}/mask",
    json={
        "text": test_text,
        "mode": "detect"
    }
)

if detect_response.status_code == 200:
    result = detect_response.json()
    print(f"   Original text returned: {result['masked_text']}")
    print(f"   Entities found: {len(result['entities_found'])}")
    for entity in result['entities_found']:
        print(f"     - {entity['entity_type']} at position {entity['start']}-{entity['end']}, score: {entity['score']}")
else:
    print(f"   Error: {detect_response.status_code} - {detect_response.text}")

# Test 2: Mask mode with replace
print("\n2. Testing MASK mode with REPLACE:")
mask_response = requests.post(
    f"{BASE_URL}/mask",
    json={
        "text": test_text,
        "mode": "mask",
        "masking_mode": "replace"
    }
)

if mask_response.status_code == 200:
    result = mask_response.json()
    print(f"   Masked text: {result['masked_text']}")
    print(f"   Entities found: {len(result['entities_found'])}")
else:
    print(f"   Error: {mask_response.status_code} - {mask_response.text}")

# Test 3: Mask mode with redact
print("\n3. Testing MASK mode with REDACT:")
redact_response = requests.post(
    f"{BASE_URL}/mask",
    json={
        "text": test_text,
        "mode": "mask",
        "masking_mode": "redact"
    }
)

if redact_response.status_code == 200:
    result = redact_response.json()
    print(f"   Masked text: {result['masked_text']}")
else:
    print(f"   Error: {redact_response.status_code} - {redact_response.text}")

# Test 4: Mask mode with hash
print("\n4. Testing MASK mode with HASH:")
hash_response = requests.post(
    f"{BASE_URL}/mask",
    json={
        "text": test_text,
        "mode": "mask",
        "masking_mode": "hash"
    }
)

if hash_response.status_code == 200:
    result = hash_response.json()
    print(f"   Masked text: {result['masked_text']}")
else:
    print(f"   Error: {hash_response.status_code} - {hash_response.text}")

# Test 5: Default behavior (should be mask mode)
print("\n5. Testing DEFAULT behavior (no mode specified):")
default_response = requests.post(
    f"{BASE_URL}/mask",
    json={
        "text": test_text
    }
)

if default_response.status_code == 200:
    result = default_response.json()
    print(f"   Masked text: {result['masked_text']}")
    print(f"   (Should be masked by default)")
else:
    print(f"   Error: {default_response.status_code} - {default_response.text}")

print("\n" + "=" * 50)
print("Testing complete!")