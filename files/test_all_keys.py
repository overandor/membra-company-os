"""
Test all Gate.io API keys
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import aiohttp

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv("/Users/alep/Downloads/05_Config_Files/.env", override=True)

# All keys to test
all_keys = [
    ("Key 1 (abcd)", "abcd9ea5956f5819386efaaa90fa0e41", "ed43f2696c3767685e8470c4ba98ea0f7ea85e9adeb9c3d098182889756d79d9"),
    ("Key 2 (cbdf)", "cbdf439fddf1d99b13113054eb3295e6", "e0d1e5d4411a250f8aaf7a540c4b395ffc08667d93f2ad9039d08342f7964937"),
    ("Key 3 (eb55)", "eb55dca15fca01bfd6ebcc67f22e7bc8", "d83ed484c5da96147061d8452c4448d2577a347308c1ef4e76f96f88709620a4"),
    ("Key 4 (gate_api)", "2b29d118d4fe92628f33a8f298416548", "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"),
]

async def test_key(label, api_key, api_secret):
    """Test a single API key"""
    print(f"\nTesting {label}...")
    print(f"  API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"  API Secret: {api_secret[:8]}...{api_secret[-4:]}")
    
    # Use the actual auth module
    from app.connectors.auth import sign_rest
    
    url = "https://api.gateio.ws/api/v4/futures/usdt/positions"
    headers = sign_rest("GET", "/futures/usdt/positions", None, None, api_key, api_secret)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                print(f"  Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"  ✅ SUCCESS! Found {len(data)} positions")
                    return True, label
                else:
                    error = await resp.text()
                    print(f"  ❌ Failed: {error[:100]}")
                    return False, label
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        return False, label

async def main():
    print("=" * 60)
    print("TESTING ALL GATE.IO API KEYS")
    print("=" * 60)
    
    results = []
    
    for label, api_key, api_secret in all_keys:
        success, key_label = await test_key(label, api_key, api_secret)
        results.append((key_label, success))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for label, success in results:
        status = "✅ WORKS" if success else "❌ FAILS"
        print(f"{label}: {status}")
    
    working_keys = [label for label, success in results if success]
    
    if working_keys:
        print(f"\n✅ Found {len(working_keys)} working key(s): {', '.join(working_keys)}")
    else:
        print("\n❌ No working keys found - all API keys are invalid or expired")

if __name__ == "__main__":
    asyncio.run(main())
