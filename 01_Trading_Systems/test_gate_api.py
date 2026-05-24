#!/usr/bin/env python3
"""
Test Gate.io API connection with current credentials
"""

import requests
import hmac
import hashlib
import time
import os

API_KEY = os.getenv("GATE_API_KEY", "2b29d118d4fe92628f33a8f298416548")
API_SECRET = os.getenv("GATE_API_SECRET", "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35")

def generate_signature(method, url, query_params="", body="", timestamp=None):
    """Generate Gate.io API signature"""
    if timestamp is None:
        timestamp = str(int(time.time()))
    
    message = f"{method}\n{url}\n{query_params}\n{body}\n{timestamp}"
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    return signature, timestamp

def test_spot_api():
    """Test spot trading API"""
    BASE_URL = "https://api.gateio.ws"
    ENDPOINT = "/api/v4/spot/accounts"
    METHOD = "GET"
    
    timestamp = str(int(time.time()))
    signature, _ = generate_signature(METHOD, ENDPOINT, "", "", timestamp)
    
    headers = {
        "KEY": API_KEY,
        "SIGN": signature,
        "Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}{ENDPOINT}", headers=headers, timeout=10)
        print(f"Spot API Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Spot API Error: {e}")
        return False

def test_futures_api():
    """Test futures trading API"""
    BASE_URL = "https://api.gateio.ws"
    ENDPOINT = "/api/v4/futures/usdt/accounts"
    METHOD = "GET"
    
    timestamp = str(int(time.time()))
    signature, _ = generate_signature(METHOD, ENDPOINT, "", "", timestamp)
    
    headers = {
        "KEY": API_KEY,
        "SIGN": signature,
        "Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}{ENDPOINT}", headers=headers, timeout=10)
        print(f"Futures API Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Futures API Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Gate.io API Credentials...")
    print(f"API Key: {API_KEY}")
    print("=" * 60)
    
    print("\n1. Testing Spot API...")
    spot_ok = test_spot_api()
    
    print("\n2. Testing Futures API...")
    futures_ok = test_futures_api()
    
    print("\n" + "=" * 60)
    if spot_ok or futures_ok:
        print("✅ API credentials work!")
    else:
        print("❌ API credentials invalid or insufficient permissions")
