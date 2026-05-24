#!/usr/bin/env python3
"""
Check futures using the exact pattern from gatefutures.py
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

def main():
    cfg = Configuration(key=GATE_API_KEY, secret=GATE_API_SECRET)
    client = FuturesApi(ApiClient(cfg))
    
    SETTLE = "usdt"
    
    print("Fetching futures tickers...")
    try:
        tickers = list(client.list_futures_tickers(SETTLE))
        print(f"Found {len(tickers)} tickers\n")
        
        print("Top 30 by volume:")
        for t in tickers[:30]:
            name = getattr(t, "contract", "N/A")
            last = getattr(t, "last", "0")
            volume = getattr(t, "volume_24h", "0")
            quote_volume = getattr(t, "volume_24h_quote", "0")
            
            price = float(last) if last else 0
            vol = float(quote_volume) if quote_volume else 0
            
            print(f"  {name:20} ${price:10.2f}  Vol: ${vol:15,.0f}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
