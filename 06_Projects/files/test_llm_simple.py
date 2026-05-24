"""
Simple LLM prediction test - no order placement
"""

import requests
import json

print("=" * 60)
print("TESTING OLLAMA CONNECTION")
print("=" * 60)

# Test Ollama connection
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    print(f"✅ Ollama is running")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ Ollama connection failed: {e}")
    exit(1)

# Test LLM generation
print("\nTesting LLM generation...")
prompt = "What is 2+2?"
payload = {
    "model": "llama2:7b",
    "prompt": prompt,
    "stream": False,
}

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=30
    )
    result = response.json()
    print(f"✅ LLM generation successful")
    print(f"   Response: {result.get('response', '')}")
except Exception as e:
    print(f"❌ LLM generation failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("OLLAMA TEST COMPLETE ✅")
print("=" * 60)
