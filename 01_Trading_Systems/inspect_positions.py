#!/usr/bin/env python3
"""
Inspect existing Gate.io futures positions in detail
"""

import os

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
    print("🔍 GATE.IO FUTURES POSITION INSPECTION")
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
    
    try:
        exchange.load_markets()
    except Exception as e:
        print(f"❌ Error loading markets: {e}")
        return
    
    # Target positions
    target_symbols = [
        "ENA/USDT:USDT",
        "SHIB/USDT:USDT"
    ]
    
    for symbol in target_symbols:
        print(f"\n{'=' * 70}")
        print(f"📊 {symbol}")
        print(f"{'=' * 70}")
        
        try:
            # Fetch positions
            positions = exchange.fetch_positions([symbol])
            
            for pos in positions:
                size = float(pos.get('contracts', 0))
                
                if size == 0:
                    continue
                
                side = pos.get('side', 'unknown')
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                notional = float(pos.get('notional', 0))
                
                # Additional details
                margin_mode = pos.get('marginMode', 'unknown')
                leverage = pos.get('leverage', 1)
                liquidation_price = pos.get('liquidationPrice', 'N/A')
                percentage = pos.get('percentage', 'N/A')
                
                # Calculate contract value
                contract_value = mark_price * size
                
                print(f"\n📍 Position Details:")
                print(f"   Side:           {side.upper()}")
                print(f"   Size:           {size:.2f} contracts")
                print(f"   Entry Price:    ${entry_price:.6f}")
                print(f"   Mark Price:     ${mark_price:.6f}")
                print(f"   Unrealized PnL: ${unrealized_pnl:+.4f}")
                print(f"   Notional:       ${notional:.4f}")
                print(f"   Contract Value: ${contract_value:.6f}")
                
                print(f"\n⚙️  Risk Parameters:")
                print(f"   Margin Mode:    {margin_mode}")
                print(f"   Leverage:       {leverage}x")
                print(f"   Liquidation:    ${liquidation_price if liquidation_price != 'N/A' else 'N/A'}")
                print(f"   ROE:            {percentage if percentage != 'N/A' else 'N/A'}%")
                
                # Get market info
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    volume_24h = ticker.get('quoteVolume', 0)
                    change_24h = ticker.get('percentage', 0)
                    
                    print(f"\n📈 Market Info:")
                    print(f"   24h Volume:     ${volume_24h:,.0f}")
                    print(f"   24h Change:     {change_24h:+.2f}%")
                except Exception as e:
                    print(f"\n⚠️  Could not fetch market info: {e}")
                
        except Exception as e:
            print(f"❌ Error inspecting {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    # Account summary
    print(f"\n{'=' * 70}")
    print("💰 ACCOUNT SUMMARY")
    print(f"{'=' * 70}")
    
    try:
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {})
        
        total = float(usdt_balance.get('total', 0))
        free = float(usdt_balance.get('free', 0))
        used = float(usdt_balance.get('used', 0))
        
        print(f"\nUSDT Balance:")
        print(f"   Total:    ${total:.2f}")
        print(f"   Free:     ${free:.2f}")
        print(f"   Used:     ${used:.2f}")
        
    except Exception as e:
        print(f"❌ Error fetching balance: {e}")
    
    print(f"\n{'=' * 70}")

if __name__ == "__main__":
    main()
