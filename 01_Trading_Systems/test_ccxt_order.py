#!/usr/bin/env python3
"""
Test Gate.io Futures Order Placement using CCXT
Places a small test order and cancels it
"""

import os
import time

GATE_API_KEY = "2b29d118d4fe92628f33a8f298416548"
GATE_API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

try:
    import ccxt
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "ccxt"], check=True)
    import ccxt

def main():
    print("=" * 60)
    print("🧪 GATE.IO FUTURES ORDER PLACEMENT TEST (CCXT)")
    print("=" * 60)
    
    # Initialize CCXT for Gate.io futures
    exchange = ccxt.gateio({
        'apiKey': GATE_API_KEY,
        'secret': GATE_API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
            'defaultSettle': 'usdt',
        }
    })
    
    # Test closing an existing position instead of opening new
    test_symbol = "ENA/USDT:USDT"  # Has existing positions
    
    print(f"\n📊 Testing with: {test_symbol}")
    print(f"   (Will close existing LONG position)")
    
    try:
        # Load markets
        exchange.load_markets()
        
        # Get current positions
        positions = exchange.fetch_positions([test_symbol])
        
        long_pos = None
        for pos in positions:
            if pos['side'] == 'long' and float(pos['contracts']) > 0:
                long_pos = pos
                break
        
        if not long_pos:
            print(f"❌ No LONG position found for {test_symbol}")
            return
        
        size = float(long_pos['contracts'])
        entry_price = float(long_pos['entryPrice'])
        
        print(f"   Current Position Size: {size}")
        print(f"   Entry Price: ${entry_price:.6f}")
        
        # Get current ticker
        ticker = exchange.fetch_ticker(test_symbol)
        last_price = ticker['last']
        
        print(f"   Current Price: ${last_price:.6f}")
        
        # Place a sell order at current price to close
        limit_price = last_price * 0.99  # Slightly below to ensure fill
        
        print(f"\n📝 Order Details:")
        print(f"   Size: {size} contracts")
        print(f"   Limit Price: ${limit_price:.6f}")
        print(f"   Side: SELL (close LONG)")
        
        print(f"\n⏳ Placing order...")
        
        # Set leverage first
        try:
            exchange.set_leverage(5, test_symbol)
            print(f"✅ Leverage set to 5x")
        except Exception as e:
            print(f"⚠️  Could not set leverage: {e}")
        
        # Place limit order (reduceOnly to close position)
        order = exchange.create_limit_sell_order(
            symbol=test_symbol,
            amount=size,
            price=limit_price,
            params={
                'marginMode': 'cross',
                'type': 'swap',
                'reduceOnly': True
            }
        )
        
        order_id = order['id']
        print(f"✅ Order placed successfully!")
        print(f"   Order ID: {order_id}")
        print(f"   Status: {order['status']}")
        print(f"   (This will close the LONG position)")
        
        # Wait for fill
        print(f"\n⏳ Waiting for fill...")
        time.sleep(5)
        
        # Check if filled
        updated_order = exchange.fetch_order(order_id, test_symbol)
        print(f"   Updated Status: {updated_order['status']}")
        
        if updated_order['status'] == 'closed':
            print(f"✅ Position closed successfully!")
            print(f"\n✅ TEST PASSED: Order placement and fill working")
        else:
            print(f"⚠️  Order not filled, cancelling...")
            exchange.cancel_order(order_id, test_symbol)
            print(f"✅ Order cancelled")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
