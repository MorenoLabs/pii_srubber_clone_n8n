#!/usr/bin/env python3
import requests
import base64

# Test server URL
BASE_URL = "http://localhost:8000"

# Test text
test_text = "John Smith's email is john.smith@example.com"

print("Testing Authentication on PII Scrubber API")
print("=" * 50)

# Test 1: Without authentication (should work if auth is disabled)
print("\n1. Testing without authentication:")
try:
    response = requests.post(
        f"{BASE_URL}/mask",
        json={"text": test_text, "mode": "detect"}
    )
    if response.status_code == 200:
        print("   ✓ Success - Authentication is disabled or not required")
    elif response.status_code == 401:
        print("   ✗ Failed - Authentication is required")
    else:
        print(f"   ✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ✗ Connection error: {e}")

# Test 2: With incorrect credentials
print("\n2. Testing with incorrect credentials:")
try:
    response = requests.post(
        f"{BASE_URL}/mask",
        json={"text": test_text, "mode": "detect"},
        auth=("wrong_user", "wrong_pass")
    )
    if response.status_code == 200:
        print("   ✓ Success - Authentication is disabled")
    elif response.status_code == 401:
        print("   ✓ Correctly rejected invalid credentials")
    else:
        print(f"   ✗ Unexpected response: {response.status_code}")
except Exception as e:
    print(f"   ✗ Connection error: {e}")

# Test 3: With correct credentials (update these based on your .env)
print("\n3. Testing with correct credentials (admin/secure_password_here):")
try:
    response = requests.post(
        f"{BASE_URL}/mask",
        json={"text": test_text, "mode": "detect"},
        auth=("admin", "secure_password_here")
    )
    if response.status_code == 200:
        result = response.json()
        print("   ✓ Authentication successful")
        print(f"   Entities found: {len(result['entities_found'])}")
    elif response.status_code == 401:
        print("   ✗ Authentication failed - check credentials")
    else:
        print(f"   ✗ Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"   ✗ Connection error: {e}")

# Test 4: Health endpoint (usually no auth required)
print("\n4. Testing health endpoint:")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print(f"   ✓ Health check passed: {response.json()}")
    else:
        print(f"   ✗ Error: {response.status_code}")
except Exception as e:
    print(f"   ✗ Connection error: {e}")

print("\n" + "=" * 50)
print("Testing complete!")
print("\nTo enable authentication:")
print("1. Create a .env file based on .env.example")
print("2. Set ENABLE_AUTH=true")
print("3. Set API_USERNAME and API_PASSWORD")
print("4. Restart the server")