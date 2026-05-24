#!/usr/bin/env python3
"""
Check available futures contracts and their notional values
"""

import os

os.environ["GATE_API_KEY"] = os.environ.get("GATE_API_KEY", "")
os.environ["GATE_API_SECRET"] = os.environ.get("GATE_API_SECRET", "")

try:
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "gate-api"], check=True)
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi

def main():
    configuration = Configuration(key=os.environ["GATE_API_KEY"], secret=os.environ["GATE_API_SECRET"])
    configuration.host = "https://api.gateio.ws"
    
    api_client = ApiClient(configuration)
    futures_api = FuturesApi(api_client)
    
    print("Fetching futures contracts...")
    try:
        contracts = list(futures_api.list_futures_contracts("usdt"))
        print(f"Found {len(contracts)} contracts\n")
        
        print("Top 20 contracts by name:")
        for c in contracts[:20]:
            name = getattr(c, "name", "N/A")
            contract_size = getattr(c, "contract_size", "N/A")
            print(f"  {name:20} Size: {contract_size}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
