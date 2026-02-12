#!/usr/bin/env python3
"""Test document upload functionality"""

import requests
import time

# Give server a moment to be ready
time.sleep(2)

BASE_URL = "http://127.0.0.1:5001"

# Test 1: Check health endpoint
print("=" * 50)
print("Test 1: Health Check")
print("=" * 50)
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Create a test file and upload it
print("\n" + "=" * 50)
print("Test 2: Document Upload")
print("=" * 50)

# Create a simple test PDF-like text file
test_content = """
This is a sample document for testing RAG indexing.
It contains information about Python, FastAPI, and machine learning.

Python is a high-level programming language known for its simplicity.
FastAPI is a modern web framework for building APIs.
Machine learning is a subset of artificial intelligence.
"""

test_filename = "test_document.txt"
with open(test_filename, "w") as f:
    f.write(test_content)

try:
    with open(test_filename, "rb") as f:
        files = {"file": (test_filename, f)}
        response = requests.post(f"{BASE_URL}/upload-doc", files=files)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e).__name__}")

# Test 3: List documents
print("\n" + "=" * 50)
print("Test 3: List Documents")
print("=" * 50)
try:
    response = requests.get(f"{BASE_URL}/list-docs")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Cleanup
import os
if os.path.exists(test_filename):
    os.remove(test_filename)

print("\n✓ Tests completed!")
