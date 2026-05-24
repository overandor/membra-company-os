#!/usr/bin/env python3
"""
Test Gate.io Futures Order Placement
Places a small test order and cancels it
"""

import os
import time

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
    
    print("=" * 60)
    print("🧪 GATE.IO FUTURES ORDER PLACEMENT TEST")
    print("=" * 60)
    
    # Test with a high-volume micro contract
    test_symbol = "PEPE_USDT"  # High volume, small notional
    
    print(f"\n📊 Testing with: {test_symbol}")
    
    try:
        # Get ticker
        tickers = list(client.list_futures_tickers(SETTLE))
        ticker = None
        for t in tickers:
            if getattr(t, "contract", "") == test_symbol:
                ticker = t
                break
        
        if not ticker:
            print(f"❌ Could not find ticker for {test_symbol}")
            return
        
        last_price = float(getattr(ticker, "last", 0))
        volume = float(getattr(ticker, "volume_24h_quote", 0))
        
        print(f"   Price: ${last_price:.6f}")
        print(f"   Volume: ${volume:,.0f}")
        
        # Calculate a very small order size
        # For PEPE at ~$0.000004, 1 contract = $0.000004
        # Let's try 1000 contracts = $0.004
        order_size = 1000
        order_value = order_size * last_price
        
        print(f"\n📝 Order Details:")
        print(f"   Size: {order_size} contracts")
        print(f"   Value: ${order_value:.6f}")
        
        # Place a limit order far from current price (won't fill)
        # Buy order at 50% of current price
        limit_price = last_price * 0.5
        
        print(f"   Limit Price: ${limit_price:.6f}")
        print(f"   Side: BUY")
        
        print(f"\n⏳ Placing order...")
        
        try:
            # Create order - note: need to use correct parameters
            # The gate_api SDK has specific parameter names
            order = gate_api.Order(
                amount=str(order_size),
                price=str(limit_price),
                side='buy',
                contract=test_symbol,
                tif='gtc'
            )
            
            result = client.create_order(order, settle=SETTLE)
            
            order_id = result.id
            print(f"✅ Order placed successfully!")
            print(f"   Order ID: {order_id}")
            
            # Wait a moment
            time.sleep(2)
            
            # Cancel the order
            print(f"\n⏳ Cancelling order...")
            client.cancel_order(order_id, settle=SETTLE, contract=test_symbol)
            print(f"✅ Order cancelled successfully!")
            
            print(f"\n✅ TEST PASSED: Order placement and cancellation working")
            
        except Exception as e:
            print(f"❌ Order placement failed: {e}")
            print(f"\n⚠️  Note: This may be due to SDK parameter mismatch")
            print(f"   The gate_api SDK has inconsistent method names")
            print(f"   Consider using CCXT for more reliable order placement")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
