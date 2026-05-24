#!/usr/bin/env python3
"""
Check Gate.io Futures Balance
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
    
    print("=" * 60)
    print("📊 GATE.IO FUTURES BALANCE")
    print("=" * 60)
    
    try:
        # Get account
        account = client.list_futures_accounts(SETTLE)
        
        print(f"\n💰 Account Summary:")
        print(f"   Total Balance:     ${float(account.total):.2f}")
        print(f"   Available:         ${float(account.available):.2f}")
        print(f"   Unrealized PnL:    ${float(account.unrealised_pnl):.2f}")
        
        print(f"\n📈 Position Details:")
        print(f"   Position Margin:   ${float(account.position_margin):.2f}")
        print(f"   Order Margin:      ${float(account.order_margin):.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Get positions
    try:
        positions = client.list_positions(SETTLE, limit=100)
        open_positions = [p for p in positions if float(p.size) != 0]
        
        print(f"\n📊 Open Positions: {len(open_positions)}")
        
        if open_positions:
            for pos in open_positions[:10]:
                size = float(pos.size)
                entry_price = float(pos.entry_price)
                mark_price = float(pos.mark_price)
                pnl = float(pos.unrealised_pnl)
                
                side = "LONG" if size > 0 else "SHORT"
                symbol = getattr(pos, "contract", "N/A")
                
                print(f"\n   {symbol} ({side})")
                print(f"   Size: {size}")
                print(f"   Entry: ${entry_price:.6f}")
                print(f"   Mark:  ${mark_price:.6f}")
                print(f"   PnL:   ${pnl:+.2f}")
        else:
            print("   No open positions")
            
    except Exception as e:
        print(f"❌ Error getting positions: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
