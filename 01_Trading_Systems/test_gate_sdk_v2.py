#!/usr/bin/env python3
"""
Test Gate.io API using official SDK v2
"""

import gate_api
from gate_api.exceptions import GateApiException
import os

API_KEY = "2b29d118d4fe92628f33a8f298416548"
API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

def test_spot_api():
    """Test spot trading API"""
    configuration = gate_api.Configuration()
    configuration.host = "https://api.gateio.ws"
    
    api_client = gate_api.ApiClient(configuration)
    api_client.set_default_header(gate_api.Configuration.api_key['KEY'], API_KEY)
    api_client.set_default_header(gate_api.Configuration.api_key['SECRET'], API_SECRET)
    
    spot_api = gate_api.SpotApi(api_client)
    
    try:
        accounts = spot_api.list_spot_accounts()
        print("✅ Spot API works!")
        print(f"Accounts: {len(accounts)}")
        for acc in accounts[:5]:
            print(f"  {acc.currency}: {acc.available}")
        return True
    except GateApiException as e:
        print(f"❌ Spot API failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_futures_api():
    """Test futures trading API"""
    configuration = gate_api.Configuration()
    configuration.host = "https://api.gateio.ws"
    
    api_client = gate_api.ApiClient(configuration)
    api_client.set_default_header(gate_api.Configuration.api_key['KEY'], API_KEY)
    api_client.set_default_header(gate_api.Configuration.api_key['SECRET'], API_SECRET)
    
    futures_api = gate_api.FuturesApi(api_client)
    
    try:
        # Test USDT futures
        positions = futures_api.list_positions("usdt", limit=10)
        print("✅ Futures API works!")
        print(f"Positions: {len(positions)}")
        return True
    except GateApiException as e:
        print(f"❌ Futures API failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Gate.io API with Official SDK...")
    print(f"API Key: {API_KEY}")
    print("=" * 60)
    
    print("\n1. Testing Spot API...")
    spot_ok = test_spot_api()
    
    print("\n2. Testing Futures API...")
    futures_ok = test_futures_api()
    
    print("\n" + "=" * 60)
    if spot_ok or futures_ok:
        print("✅ API credentials work with official SDK!")
    else:
        print("❌ API credentials invalid or need different permissions")
