#!/usr/bin/env python3
"""
Close SHIB hedge positions using reduce-only orders
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
    print("=" * 70)
    print("🔒 CLOSING SHIB HEDGE POSITIONS")
    print("=" * 70)
    
    # Initialize CCXT
    exchange = ccxt.gateio({
        'apiKey': GATE_API_KEY,
        'secret': GATE_API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
            'defaultSettle': 'usdt',
        }
    })
    
    symbol = "SHIB/USDT:USDT"
    
    try:
        exchange.load_markets()
    except Exception as e:
        print(f"❌ Error loading markets: {e}")
        return
    
    # Get current positions
    print(f"\n📊 Fetching positions for {symbol}...")
    positions = exchange.fetch_positions([symbol])
    
    for pos in positions:
        size = float(pos.get('contracts', 0))
        
        if size == 0:
            continue
        
        side = pos.get('side', 'unknown')
        print(f"\n📍 Found {side.upper()} position: {size} contracts")
        
        # Get current price
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Calculate close price (slightly aggressive to ensure fill)
        if side == 'long':
            close_side = 'sell'
            close_price = current_price * 0.99  # Sell below current
        else:  # short
            close_side = 'buy'
            close_price = current_price * 1.01  # Buy above current
        
        print(f"   Closing with {close_side.upper()} @ ${close_price:.6f}")
        
        try:
            # Place reduce-only order
            order = exchange.create_order(
                symbol=symbol,
                type='limit',
                side=close_side,
                amount=abs(size),
                price=close_price,
                params={
                    'marginMode': 'isolated',
                    'type': 'swap',
                    'reduceOnly': True
                }
            )
            
            order_id = order['id']
            print(f"✅ Order placed: {order_id}")
            
            # Wait for fill
            time.sleep(3)
            
            # Check status
            updated_order = exchange.fetch_order(order_id, symbol)
            print(f"   Status: {updated_order['status']}")
            
            if updated_order['status'] == 'closed':
                print(f"✅ Position closed successfully!")
            else:
                print(f"⚠️  Order not filled, cancelling...")
                exchange.cancel_order(order_id, symbol)
                
        except Exception as e:
            print(f"❌ Error closing position: {e}")
    
    print(f"\n{'=' * 70}")
    print("✅ SHIB positions closed")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
