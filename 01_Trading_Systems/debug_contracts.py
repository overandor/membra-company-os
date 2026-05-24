#!/usr/bin/env python3
"""
Debug script to see available contracts
"""

GATE_API_KEY = "2b29d118d4fe92628f33a8f298416548"
GATE_API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

try:
    import ccxt
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "ccxt"], check=True)
    import ccxt

def main():
    exchange = ccxt.gateio({
        'apiKey': GATE_API_KEY,
        'secret': GATE_API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
            'defaultSettle': 'usdt',
        }
    })
    
    print("Loading markets...")
    exchange.load_markets()
    
    print(f"Total markets: {len(exchange.markets)}")
    
    # Show first 20 USDT futures
    count = 0
    for symbol, market in exchange.markets.items():
        if market.get('type') == 'swap' and market.get('settle') == 'usdt':
            if count < 20:
                print(f"{symbol}: active={market.get('active')}, contractSize={market.get('contractSize')}")
                count += 1
    
    # Try to get some tickers
    print("\nFetching tickers for first 10...")
    count = 0
    for symbol, market in exchange.markets.items():
        if market.get('type') == 'swap' and market.get('settle') == 'usdt' and market.get('active'):
            try:
                ticker = exchange.fetch_ticker(symbol)
                price = ticker['last']
                volume = ticker.get('quoteVolume', 0)
                print(f"{symbol}: ${price:.6f} | Vol: ${volume:,.0f}")
                count += 1
                if count >= 10:
                    break
            except Exception as e:
                print(f"{symbol}: Error - {e}")

if __name__ == "__main__":
    main()
