#!/usr/bin/env python3
"""
Test script to verify all endpoints are working
"""
import requests
import json
import time
from pathlib import Path

# Wait a bit for server
time.sleep(2)

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint"""
    print("="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_list_docs():
    """Test list documents endpoint"""
    print("\n" + "="*60)
    print("TEST 2: List Documents")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/list-docs")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_upload():
    """Test upload document endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Upload Document")
    print("="*60)
    
    # Create a test file
    test_content = """
    This is a test document.
    It contains some text to test the upload functionality.
    The system should be able to index this content.
    """
    test_file_path = "test_doc.txt"
    
    try:
        # Write test file
        with open(test_file_path, "w") as f:
            f.write(test_content)
        
        # Upload it
        with open(test_file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/upload-doc", files=files)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Clean up
        Path(test_file_path).unlink(missing_ok=True)
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat():
    """Test chat endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Chat")
    print("="*60)
    try:
        chat_data = {
            "question": "What is in the uploaded document?",
            "model": "gemini-2.5-flash",
            "session_id": "test-session-123"
        }
        response = requests.post(f"{BASE_URL}/chat", json=chat_data)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting endpoint tests...\n")
    
    results = {}
    results["Health Check"] = test_health()
    results["List Documents"] = test_list_docs()
    results["Upload Document"] = test_upload()
    results["Chat"] = test_chat()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED ✓' if all_passed else 'SOME TESTS FAILED ✗'}")
