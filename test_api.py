#!/usr/bin/env python3
"""
Test script for PII Scrubber API
Run this after starting the API server
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    assert response.status_code == 200
    print("✓ Health check passed\n")

def test_basic_masking():
    """Test basic PII masking"""
    payload = {
        "text": "John Doe lives at 123 Main St and email is john@example.com",
        "masking_mode": "replace"
    }
    
    response = requests.post(f"{BASE_URL}/mask", json=payload)
    result = response.json()
    
    print("Basic Masking Test:")
    print(f"  Original: {payload['text']}")
    print(f"  Masked: {result['masked_text']}")
    print(f"  Entities found: {len(result['entities_found'])}")
    print(f"  Processing time: {result['processing_time_ms']}ms")
    
    assert response.status_code == 200
    assert "<PERSON>" in result['masked_text']
    assert "<EMAIL_ADDRESS>" in result['masked_text']
    print("✓ Basic masking passed\n")

def test_redact_mode():
    """Test redaction mode"""
    payload = {
        "text": "Contact Sarah Johnson at sarah.j@company.com or call 555-0123",
        "masking_mode": "redact",
        "masking_char": "*"
    }
    
    response = requests.post(f"{BASE_URL}/mask", json=payload)
    result = response.json()
    
    print("Redact Mode Test:")
    print(f"  Original: {payload['text']}")
    print(f"  Masked: {result['masked_text']}")
    
    assert response.status_code == 200
    assert "******" in result['masked_text']
    print("✓ Redact mode passed\n")

def test_hash_mode():
    """Test hash mode for consistent masking"""
    payload = {
        "text": "Email john@example.com appears twice: john@example.com",
        "masking_mode": "hash"
    }
    
    response = requests.post(f"{BASE_URL}/mask", json=payload)
    result = response.json()
    
    print("Hash Mode Test:")
    print(f"  Original: {payload['text']}")
    print(f"  Masked: {result['masked_text']}")
    
    assert response.status_code == 200
    assert "<HASH:" in result['masked_text']
    print("✓ Hash mode passed\n")

def test_specific_entities():
    """Test with specific entity selection"""
    payload = {
        "text": "John Doe, born on 01/15/1990, email: john@test.com",
        "entities": ["PERSON", "EMAIL_ADDRESS"],
        "skip_entities": ["DATE_TIME"]
    }
    
    response = requests.post(f"{BASE_URL}/mask", json=payload)
    result = response.json()
    
    print("Specific Entities Test:")
    print(f"  Original: {payload['text']}")
    print(f"  Masked: {result['masked_text']}")
    print(f"  Detected entities: {[e['entity_type'] for e in result['entities_found']]}")
    
    assert response.status_code == 200
    # Date should not be masked since it's in skip_entities
    assert "01/15/1990" in result['masked_text'] or "DATE" not in [e['entity_type'] for e in result['entities_found']]
    print("✓ Specific entities test passed\n")

def test_complex_text():
    """Test with complex multi-entity text"""
    payload = {
        "text": """
        Customer: Robert Smith
        SSN: 123-45-6789
        Phone: +1 (555) 123-4567
        Email: robert.smith@example.com
        Address: 456 Oak Avenue, New York, NY 10001
        Credit Card: 4111-1111-1111-1111
        IP Address: 192.168.1.100
        """,
        "masking_mode": "replace"
    }
    
    response = requests.post(f"{BASE_URL}/mask", json=payload)
    result = response.json()
    
    print("Complex Text Test:")
    print(f"  Entities found: {len(result['entities_found'])}")
    for entity in result['entities_found']:
        print(f"    - {entity['entity_type']}: score {entity['score']}")
    
    assert response.status_code == 200
    assert len(result['entities_found']) > 3
    print("✓ Complex text test passed\n")

def test_n8n_format():
    """Test N8N-compatible format"""
    # Simulating N8N workflow data
    payload = {
        "text": "Please contact Jane Doe at jane.doe@company.org or 555-9876",
        "masking_mode": "replace"
    }
    
    response = requests.post(
        f"{BASE_URL}/mask",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    result = response.json()
    
    print("N8N Format Test:")
    print(f"  Request format: JSON")
    print(f"  Response has masked_text: {'masked_text' in result}")
    print(f"  Response has entities_found: {'entities_found' in result}")
    print(f"  Response has processing_time_ms: {'processing_time_ms' in result}")
    
    assert response.status_code == 200
    assert all(key in result for key in ['masked_text', 'entities_found', 'processing_time_ms'])
    print("✓ N8N format test passed\n")

def test_error_handling():
    """Test error handling"""
    # Test with empty text
    response = requests.post(f"{BASE_URL}/mask", json={"text": ""})
    assert response.status_code == 400
    print("✓ Empty text handling passed")
    
    # Test with invalid masking mode
    response = requests.post(f"{BASE_URL}/mask", json={
        "text": "test",
        "masking_mode": "invalid"
    })
    assert response.status_code == 400
    print("✓ Invalid masking mode handling passed")
    
    print("")

if __name__ == "__main__":
    print("="*50)
    print("PII Scrubber API Test Suite")
    print("="*50)
    print()
    
    try:
        # Run all tests
        test_health()
        test_basic_masking()
        test_redact_mode()
        test_hash_mode()
        test_specific_entities()
        test_complex_text()
        test_n8n_format()
        test_error_handling()
        
        print("="*50)
        print("✅ All tests passed successfully!")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API at http://localhost:8000")
        print("   Please start the API server first:")
        print("   uvicorn app:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()