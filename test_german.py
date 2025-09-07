#!/usr/bin/env python3
"""
Test script for German language PII detection
Run this after starting the API server
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

def test_german_auto_detection():
    """Test automatic German language detection"""
    print("Testing German auto-detection...")
    
    response = requests.post(
        f"{BASE_URL}/mask",
        json={
            "text": "Mein Name ist Hans Müller und meine E-Mail ist hans@beispiel.de",
            "masking_mode": "replace"
        }
    )
    
    data = response.json()
    print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
    
    assert response.status_code == 200
    assert data["detected_language"] == "de"
    assert "<PERSON>" in data["masked_text"]
    assert "<EMAIL_ADDRESS>" in data["masked_text"] or "<EMAIL>" in data["masked_text"]
    print("✓ German auto-detection test passed\n")

def test_german_explicit():
    """Test explicit German language specification"""
    print("Testing explicit German language...")
    
    response = requests.post(
        f"{BASE_URL}/mask",
        json={
            "text": "Der Kunde Max Schmidt wohnt in der Hauptstraße 123, 10115 Berlin. Seine Telefonnummer ist +49 30 12345678.",
            "masking_mode": "replace",
            "language": "de"
        }
    )
    
    data = response.json()
    print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
    
    assert response.status_code == 200
    assert data["detected_language"] == "de"
    assert "<PERSON>" in data["masked_text"]
    assert "<LOCATION>" in data["masked_text"]
    print("✓ Explicit German language test passed\n")

def test_german_with_phone_and_address():
    """Test German text with phone numbers and addresses"""
    print("Testing German with complex PII...")
    
    response = requests.post(
        f"{BASE_URL}/mask",
        json={
            "text": "Frau Anna Weber erreichen Sie unter anna.weber@firma.de oder telefonisch unter 030-12345678. Sie arbeitet in der Friedrichstraße 50, 10117 Berlin.",
            "masking_mode": "redact",
            "language": "de"
        }
    )
    
    data = response.json()
    print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
    
    assert response.status_code == 200
    assert "██████" in data["masked_text"]  # Redacted content
    print("✓ German complex PII test passed\n")

def test_german_credit_card():
    """Test German text with credit card number"""
    print("Testing German with credit card...")
    
    response = requests.post(
        f"{BASE_URL}/mask",
        json={
            "text": "Die Kreditkartennummer ist 4532-1234-5678-9012 und gehört zu Herrn Peter Meier.",
            "masking_mode": "hash",
            "language": "de"
        }
    )
    
    data = response.json()
    print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
    
    assert response.status_code == 200
    assert "<HASH:" in data["masked_text"]  # Hash mode
    print("✓ German credit card test passed\n")

def test_mixed_english_german():
    """Test mixed English and German text"""
    print("Testing mixed English/German text...")
    
    response = requests.post(
        f"{BASE_URL}/mask",
        json={
            "text": "Hello, my name is John Smith. Ich wohne in München und meine E-Mail ist john@example.com",
            "masking_mode": "replace"
        }
    )
    
    data = response.json()
    print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
    
    assert response.status_code == 200
    assert "<PERSON>" in data["masked_text"]
    assert "<EMAIL_ADDRESS>" in data["masked_text"] or "<EMAIL>" in data["masked_text"]
    print("✓ Mixed language test passed\n")

def test_detect_mode_german():
    """Test detect mode with German text"""
    print("Testing detect mode with German...")
    
    response = requests.post(
        f"{BASE_URL}/mask",
        json={
            "text": "Kontaktieren Sie Frau Dr. Schmidt unter der Nummer 0171-1234567.",
            "mode": "detect",
            "language": "de"
        }
    )
    
    data = response.json()
    print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
    
    assert response.status_code == 200
    assert data["masked_text"] == "Kontaktieren Sie Frau Dr. Schmidt unter der Nummer 0171-1234567."
    assert len(data["entities_found"]) > 0
    print("✓ Detect mode German test passed\n")

def main():
    """Run all German language tests"""
    print("=" * 50)
    print("Running German Language PII Detection Tests")
    print("=" * 50 + "\n")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Error: API server is not running!")
            print("Please start the server with: uvicorn app:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server!")
        print("Please start the server with: uvicorn app:app --reload")
        return
    
    # Run tests
    tests = [
        test_german_auto_detection,
        test_german_explicit,
        test_german_with_phone_and_address,
        test_german_credit_card,
        test_mixed_english_german,
        test_detect_mode_german
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test {test.__name__} failed: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} error: {e}\n")
            failed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)

if __name__ == "__main__":
    main()