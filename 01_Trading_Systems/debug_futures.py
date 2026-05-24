#!/usr/bin/env python3
"""
Debug futures contracts to see what data is available
"""

import os

GATE_API_KEY = "2b29d118d4fe92628f33a8f298416548"
GATE_API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

try:
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "gate-api"], check=True)
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def main():
    cfg = Configuration(key=GATE_API_KEY, secret=GATE_API_SECRET)
    client = FuturesApi(ApiClient(cfg))
    
    SETTLE = "usdt"
    
    print("Fetching futures contracts...")
    try:
        contracts = list(client.list_contracts())
        print(f"Found {len(contracts)} contracts\n")
        
        print("First 10 contracts with their attributes:")
        for i, c in enumerate(contracts[:10]):
            print(f"\nContract {i+1}:")
            print(f"  name: {getattr(c, 'name', 'N/A')}")
            print(f"  last_price: {getattr(c, 'last_price', 'N/A')}")
            print(f"  quanto_multiplier: {getattr(c, 'quanto_multiplier', 'N/A')}")
            print(f"  volume_24h_quote: {getattr(c, 'volume_24h_quote', 'N/A')}")
            print(f"  order_size_min: {getattr(c, 'order_size_min', 'N/A')}")
            
            # Calculate notional
            price = safe_float(getattr(c, 'last_price', 0))
            mult = safe_float(getattr(c, 'quanto_multiplier', 1.0), 1.0)
            notional = price * mult
            print(f"  calculated notional: ${notional}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
