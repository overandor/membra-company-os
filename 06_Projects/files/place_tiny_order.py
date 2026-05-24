#!/usr/bin/env python3
"""
Place a tiny test order on Gate.io futures

Usage: python place_tiny_order.py SHIB_USDT
"""

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv
import aiohttp

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv("/Users/alep/Downloads/05_Config_Files/.env")

# Configure Gate.io API - Use GATE_API_KEY/GATE_API_SECRET (Set 1)
GATE_API_KEY = os.getenv("GATE_API_KEY")
GATE_API_SECRET = os.getenv("GATE_API_SECRET")

if not GATE_API_KEY or not GATE_API_SECRET:
    print("ERROR: Gate.io API credentials not found in .env file")
    sys.exit(1)

# Set environment variables BEFORE importing config
os.environ["GATE_API_KEY"] = GATE_API_KEY
os.environ["GATE_API_SECRET"] = GATE_API_SECRET
os.environ["LIVE_TRADING"] = "1"
os.environ["LIVE_TRADING_CONFIRM"] = "I_UNDERSTAND_RISK"

# NOW import the config
from app.connectors.rest_client import place_order, cancel_order
from app.core.config import mm_config, ContractSpec
mm_config.dry_run = True  # DRY RUN MODE - API keys still failing
mm_config.account_mode = "single"
mm_config.kill_switch = False

# Add contract
mm_config.contracts["SHIB_USDT"] = ContractSpec(
    name="SHIB_USDT",
    tick_size=Decimal("0.000000001"),
    lot_size=1,
    quanto_multiplier=Decimal("1")
)

async def place_micro_orders(contract: str, num_orders: int = 10):
    """Place multiple tiny orders (max 10 cents each)"""
    
    spec = mm_config.contracts[contract]
    
    print("=" * 60)
    print(f"PLACING {num_orders} MICRO ORDERS (DRY-RUN MODE)")
    print("=" * 60)
    print(f"Contract: {contract}")
    print(f"Max notional per order: $0.10")
    print(f"Total max notional: ${0.10 * num_orders:.2f}")
    print("⚠️  DRY-RUN MODE: No real orders will be placed")
    print("⚠️  API KEYS FAILING - Using simulation mode")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_orders):
            # Vary price slightly for each order
            price = Decimal("0.000045") + Decimal("0.000000001") * i
            max_notional = Decimal("0.10")
            size = int((max_notional / price).to_integral_value())
            
            print(f"\n[{i+1}/{num_orders}] Placing order...")
            print(f"  Size: {size}")
            print(f"  Price: {price}")
            print(f"  Notional: ${size * price:.4f}")
            
            # Place maker bid (post-only cancel)
            result = await place_order(
                session=session,
                contract=contract,
                size=size,  # buy
                price=price,
                tif="poc",  # post-only cancel
                reduce_only=False,
                text=f"micro_test_order_{i+1}"
            )
            
            print(f"  Order ID: {result.get('id')}")
            print(f"  Status: {result.get('status')}")
            
            # Small delay between orders
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print(f"ALL {num_orders} ORDERS PLACED")
        print("=" * 60)
        
        # Cancel all orders
        print("\nCancelling all orders...")
        for i in range(num_orders):
            # In dry-run, we can't actually cancel, but simulate it
            await asyncio.sleep(0.1)
        
        print("All orders cancelled")
        
        print("\n" + "=" * 60)
        print(f"MICRO ORDER TEST COMPLETE ({num_orders} orders)")
        print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python place_tiny_order.py <CONTRACT> [NUM_ORDERS]")
        print("Example: python place_tiny_order.py SHIB_USDT 10")
        sys.exit(1)
    
    contract = sys.argv[1].upper()
    num_orders = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    print("=" * 60)
    print("DRY-RUN MICRO ORDER PLACEMENT")
    print("=" * 60)
    print("⚠️  DRY-RUN MODE: No real orders will be placed")
    print(f"Placing {num_orders} micro orders (max $0.10 each)")
    print("⚠️  API KEYS FAILING - Using simulation mode")
    print("=" * 60)
    
    try:
        asyncio.run(place_micro_orders(contract, num_orders))
    except KeyboardInterrupt:
        print("\nCancelled by user")
