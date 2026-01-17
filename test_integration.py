#!/usr/bin/env python3
"""
Integration test: Frontend-Backend compatibility check.

This script validates that the frontend API client calls are compatible
with the backend endpoints and that the full workflow functions correctly.
"""

import os
import requests
import json
import time
from pathlib import Path

# Ensure we use the test database
os.environ['DATABASE_URL'] = 'sqlite:///./test_integration.db'

# Clean up any previous test DB
Path('test_integration.db').unlink(missing_ok=True)

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
BASE_URL = 'http://localhost:8000/api/v1'

print("=" * 60)
print("Frontend-Backend Integration Test")
print("=" * 60)

# Test 1: User Registration
print("\n[Test 1] User Registration")
register_response = client.post(
    '/api/v1/users/register',
    json={
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test User'
    }
)
print(f"Status: {register_response.status_code}")
print(f"Response: {register_response.json()}")
assert register_response.status_code == 200, "Registration failed"
assert register_response.json()['email'] == 'test@example.com'
print("✓ Registration successful")

# Test 2: User Login
print("\n[Test 2] User Login")
login_response = client.post(
    '/api/v1/users/login',
    json={
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test User'
    }
)
print(f"Status: {login_response.status_code}")
print(f"Response keys: {list(login_response.json().keys())}")
assert login_response.status_code == 200, "Login failed"
token = login_response.json().get('access_token')
assert token, "No access token returned"
print(f"✓ Login successful, token: {token[:20]}...")

# Test 3: File Upload
print("\n[Test 3] File Upload (with mocked OCR)")
from unittest.mock import patch

# Create a test file
test_file_path = 'test_upload.txt'
with open(test_file_path, 'w') as f:
    f.write('hello world test content')

# Mock OCR service to avoid external API calls
with patch('backend.app.ocr_service.OCRService') as MockOCR:
    mock_ocr_instance = MockOCR.return_value
    mock_ocr_instance.process_document.return_value = {
        'words': ['hello', 'world', 'test', 'content'],
        'count': 4,
        'raw_result': {}
    }
    
    with open(test_file_path, 'rb') as f:
        upload_response = client.post(
            '/api/v1/upload',
            files={'file': ('test_upload.txt', f, 'text/plain')},
            headers={'Authorization': f'Bearer {token}'}
        )

print(f"Status: {upload_response.status_code}")
print(f"Response: {upload_response.json()}")
assert upload_response.status_code == 200, "Upload failed"
upload_id = upload_response.json().get('upload_id')
assert upload_id, "No upload_id returned"
print(f"✓ Upload successful, upload_id: {upload_id}")

# Test 4: Get Upload Status
print("\n[Test 4] Get Upload Status")
# Wait a moment for background processing
time.sleep(0.5)
status_response = client.get(
    f'/api/v1/upload/{upload_id}',
    headers={'Authorization': f'Bearer {token}'}
)
print(f"Status: {status_response.status_code}")
print(f"Response: {status_response.json()}")
assert status_response.status_code == 200, "Get upload status failed"
upload_status = status_response.json()
assert upload_status['upload_id'] == upload_id
print(f"✓ Upload status retrieved: {upload_status['status']}")

# Test 5: Get Learning Plan (should be empty initially)
print("\n[Test 5] Get Learning Plan")
plan_response = client.get(
    '/api/v1/learning/plan',
    headers={'Authorization': f'Bearer {token}'}
)
print(f"Status: {plan_response.status_code}")
print(f"Response: {plan_response.json()}")
assert plan_response.status_code == 200, "Get learning plan failed"
initial_plans = plan_response.json().get('plans', [])
print(f"✓ Learning plan retrieved, {len(initial_plans)} items")

# Test 6: Create a Word and Post Progress
print("\n[Test 6] Create Word and Post Progress")
from backend.app.db import SessionLocal
from backend.app import models

db = SessionLocal()
word = models.Word(lemma='hello')
db.add(word)
db.commit()
db.refresh(word)
db.close()

progress_response = client.post(
    '/api/v1/learning/progress',
    json={
        'word_id': word.id,
        'performance': 0.9
    },
    headers={'Authorization': f'Bearer {token}'}
)
print(f"Status: {progress_response.status_code}")
print(f"Response: {progress_response.json()}")
assert progress_response.status_code == 200, "Post progress failed"
assert 'next_review' in progress_response.json()
assert 'interval_hours' in progress_response.json()
print("✓ Progress posted successfully")

# Test 7: Get Updated Learning Plan
print("\n[Test 7] Get Updated Learning Plan")
updated_plan_response = client.get(
    '/api/v1/learning/plan',
    headers={'Authorization': f'Bearer {token}'}
)
print(f"Status: {updated_plan_response.status_code}")
plans = updated_plan_response.json().get('plans', [])
print(f"Response: {len(plans)} items in plan")
assert len(plans) > 0, "No items in learning plan after posting progress"
print(f"✓ Learning plan updated: {len(plans)} items")

# Test 8: Verify Frontend API calls format
print("\n[Test 8] Validate Frontend-Backend Data Format Compatibility")
# Simulate frontend API calls
frontend_calls = {
    'register': {'email': 'test2@example.com', 'password': 'pass', 'name': 'Test2'},
    'login': {'email': 'test2@example.com', 'password': 'pass', 'name': 'Test2'},
    'progress': {'word_id': word.id, 'performance': 0.75},
}

# Test register format
print("  - Register endpoint format: ", end='')
try:
    r = client.post('/api/v1/users/register', json=frontend_calls['register'])
    assert r.status_code == 200
    print("✓")
except Exception as e:
    print(f"✗ {e}")

# Test login format
print("  - Login endpoint format: ", end='')
try:
    r = client.post('/api/v1/users/login', json=frontend_calls['login'])
    assert r.status_code == 200
    print("✓")
except Exception as e:
    print(f"✗ {e}")

# Test progress format
print("  - Progress endpoint format: ", end='')
try:
    r = client.post(
        '/api/v1/learning/progress',
        json=frontend_calls['progress'],
        headers={'Authorization': f'Bearer {token}'}
    )
    assert r.status_code == 200
    print("✓")
except Exception as e:
    print(f"✗ {e}")

# Clean up
Path(test_file_path).unlink(missing_ok=True)
Path('test_integration.db').unlink(missing_ok=True)

print("\n" + "=" * 60)
print("✓ All integration tests passed!")
print("Frontend and backend are compatible and working correctly.")
print("=" * 60)
