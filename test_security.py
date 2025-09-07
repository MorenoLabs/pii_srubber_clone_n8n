#!/usr/bin/env python3
"""
Comprehensive security test suite for PII Scrubber API.
Tests rate limiting, DoS protection, authentication, and CORS.
"""

import requests
import time
import sys
import threading
from requests.auth import HTTPBasicAuth

API_BASE = "http://localhost:8000"

def test_rate_limiting():
    """Test rate limiting by making many rapid requests."""
    print("\n=== Testing Rate Limiting ===")
    
    # Make rapid requests to trigger rate limiting
    start_time = time.time()
    success_count = 0
    rate_limited_count = 0
    
    for i in range(35):  # Exceed the default 30/minute limit
        try:
            response = requests.post(
                f"{API_BASE}/mask",
                json={"text": f"test request {i}", "mode": "detect"},
                timeout=2
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_count += 1
                print(f"  ✓ Rate limit triggered at request {i+1}")
            else:
                print(f"  ? Unexpected status {response.status_code} at request {i+1}")
                
        except requests.RequestException as e:
            print(f"  ✗ Request {i+1} failed: {e}")
    
    elapsed = time.time() - start_time
    print(f"  Sent 35 requests in {elapsed:.2f}s")
    print(f"  Success: {success_count}, Rate limited: {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("  ✅ Rate limiting is working")
    else:
        print("  ❌ Rate limiting may not be configured")

def test_dos_protection():
    """Test DoS protection with large payloads and timeouts."""
    print("\n=== Testing DoS Protection ===")
    
    # Test 1: Large text payload
    print("Testing large text payload...")
    large_text = "A" * 60000  # Exceeds 50KB default limit
    
    try:
        response = requests.post(
            f"{API_BASE}/mask",
            json={"text": large_text, "mode": "detect"},
            timeout=5
        )
        
        if response.status_code == 413:
            print("  ✅ Large payload correctly rejected (413)")
        else:
            print(f"  ❌ Large payload not rejected (status: {response.status_code})")
            
    except requests.RequestException as e:
        print(f"  ✗ Large payload test failed: {e}")
    
    # Test 2: Very large request size (bytes)
    print("Testing request size limits...")
    mega_text = "X" * 1200000  # Exceeds 1MB limit
    
    try:
        response = requests.post(
            f"{API_BASE}/mask",
            json={"text": mega_text, "mode": "detect"},
            timeout=5
        )
        
        if response.status_code == 413:
            print("  ✅ Mega payload correctly rejected (413)")
        else:
            print(f"  ❌ Mega payload not rejected (status: {response.status_code})")
            
    except requests.RequestException as e:
        print(f"  ✗ Mega payload test failed: {e}")

def test_authentication_security():
    """Test authentication with various scenarios."""
    print("\n=== Testing Authentication Security ===")
    
    # Test 1: No credentials
    print("Testing without credentials...")
    try:
        response = requests.post(
            f"{API_BASE}/mask",
            json={"text": "test", "mode": "detect"},
            timeout=5
        )
        
        if response.status_code == 401:
            print("  ✅ Authentication required (401)")
        elif response.status_code == 200:
            print("  ℹ  Authentication disabled - request succeeded")
        else:
            print(f"  ? Unexpected status: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"  ✗ No credentials test failed: {e}")
    
    # Test 2: Wrong credentials
    print("Testing with wrong credentials...")
    try:
        response = requests.post(
            f"{API_BASE}/mask",
            json={"text": "test", "mode": "detect"},
            auth=HTTPBasicAuth("hacker", "wrong_password"),
            timeout=5
        )
        
        if response.status_code == 401:
            print("  ✅ Wrong credentials rejected (401)")
        elif response.status_code == 200:
            print("  ℹ  Authentication disabled - wrong credentials succeeded")
        else:
            print(f"  ? Unexpected status: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"  ✗ Wrong credentials test failed: {e}")
    
    # Test 3: Correct credentials (if auth enabled)
    print("Testing with correct credentials...")
    try:
        response = requests.post(
            f"{API_BASE}/mask",
            json={"text": "John Doe", "mode": "detect"},
            auth=HTTPBasicAuth("admin", "change_me_to_secure_password_123"),
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Correct credentials accepted - found {len(result.get('entities_found', []))} entities")
        elif response.status_code == 401:
            print("  ❌ Correct credentials rejected - check configuration")
        else:
            print(f"  ? Unexpected status: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"  ✗ Correct credentials test failed: {e}")

def test_cors_headers():
    """Test CORS configuration."""
    print("\n=== Testing CORS Configuration ===")
    
    # Test preflight request
    try:
        response = requests.options(
            f"{API_BASE}/mask",
            headers={
                "Origin": "https://evil-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=5
        )
        
        cors_origin = response.headers.get("Access-Control-Allow-Origin", "")
        
        if "evil-site.com" not in cors_origin:
            print("  ✅ CORS properly restricts origins")
        else:
            print("  ❌ CORS allows unauthorized origins")
            
        print(f"  Allowed origins: {cors_origin}")
        print(f"  Allowed methods: {response.headers.get('Access-Control-Allow-Methods', 'N/A')}")
        
    except requests.RequestException as e:
        print(f"  ✗ CORS test failed: {e}")

def test_concurrent_requests():
    """Test behavior under concurrent load."""
    print("\n=== Testing Concurrent Request Handling ===")
    
    results = []
    
    def make_request(request_id):
        try:
            start = time.time()
            response = requests.post(
                f"{API_BASE}/mask",
                json={"text": f"Test user {request_id}", "mode": "detect"},
                timeout=10
            )
            elapsed = time.time() - start
            results.append((request_id, response.status_code, elapsed))
        except requests.RequestException as e:
            results.append((request_id, f"ERROR: {e}", 0))
    
    # Launch concurrent requests
    threads = []
    for i in range(10):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    # Analyze results
    success_count = sum(1 for _, status, _ in results if status == 200)
    avg_time = sum(elapsed for _, status, elapsed in results if status == 200) / max(success_count, 1)
    
    print(f"  Concurrent requests: 10")
    print(f"  Successful: {success_count}")
    print(f"  Average response time: {avg_time:.3f}s")
    
    if success_count >= 8:  # Allow for some rate limiting
        print("  ✅ Handles concurrent requests well")
    else:
        print("  ⚠️  May have issues with concurrent requests")

def test_health_endpoint():
    """Test health endpoint accessibility."""
    print("\n=== Testing Health Endpoint ===")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"  ✅ Health endpoint accessible: {health_data}")
        else:
            print(f"  ❌ Health endpoint returned {response.status_code}")
            
    except requests.RequestException as e:
        print(f"  ✗ Health endpoint test failed: {e}")

def main():
    """Run all security tests."""
    print("🔒 PII Scrubber API Security Test Suite")
    print("=" * 50)
    
    # Check server availability
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding properly. Status: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server at {API_BASE}")
        print("Please ensure the server is running: uvicorn app:app --reload")
        sys.exit(1)
    
    print(f"✅ Server is accessible at {API_BASE}")
    
    # Run all tests
    test_health_endpoint()
    test_authentication_security()
    test_rate_limiting()
    test_dos_protection()
    test_cors_headers()
    test_concurrent_requests()
    
    print("\n" + "=" * 50)
    print("🔒 Security testing complete!")
    print("\nℹ️  Notes:")
    print("- Some tests may show 'Authentication disabled' if ENABLE_AUTH=false in .env")
    print("- Rate limiting may take time to reset between test runs")
    print("- DoS protection limits are configurable in config.py")
    print("- For production, enable all security features and use HTTPS")

if __name__ == "__main__":
    main()