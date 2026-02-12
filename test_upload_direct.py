#!/usr/bin/env python3
"""Test script to upload a file and debug issues"""
import requests
import time
import os

# Wait for server to start
time.sleep(3)

# Create a test file
test_file_path = "test_document.txt"
with open(test_file_path, "w") as f:
    f.write("This is a test document for upload testing.\nLine 2.\nLine 3.")

print(f"Test file created: {test_file_path}")
print(f"File size: {os.path.getsize(test_file_path)} bytes")

# Test health endpoint first
try:
    r = requests.get("http://localhost:5001/health", timeout=5)
    print(f"\n✓ Health check: {r.status_code}")
    print(f"  Response: {r.json()}")
except Exception as e:
    print(f"\n✗ Health check failed: {e}")
    exit(1)

# Test upload endpoint
print("\nAttempting file upload...")
try:
    with open(test_file_path, "rb") as f:
        files = {"file": (test_file_path, f)}
        r = requests.post(
            "http://localhost:5001/upload-doc",
            files=files,
            timeout=30
        )
    
    print(f"✓ Upload response: {r.status_code}")
    print(f"  Headers: {dict(r.headers)}")
    print(f"  Response body: {r.text}")
    
    try:
        data = r.json()
        print(f"  JSON: {data}")
    except:
        print(f"  (Not JSON)")
    
except Exception as e:
    print(f"✗ Upload failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Clean up
os.remove(test_file_path)
print(f"\nTest file cleaned up")
