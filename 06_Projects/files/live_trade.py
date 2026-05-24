#!/usr/bin/env python3
"""
LIVE TRADING SCRIPT - REAL ORDERS ON GATE.IO FUTURES

WARNING: This script places REAL orders with REAL money.
Use at your own risk. Ensure you understand the risks before running.
"""

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path

# Add files to path
sys.path.insert(0, str(Path(__file__).parent))

from app.connectors.rest_client import place_order, cancel_order
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/Users/alep/Downloads/05_Config_Files/.env")

# Configure Gate.io API
GATE_API_KEY = os.getenv("GATE_API_KEY")
GATE_API_SECRET = os.getenv("GATE_API_SECRET")

if not GATE_API_KEY or not GATE_API_SECRET:
    print("ERROR: Gate.io API credentials not found in .env file")
    sys.exit(1)

# Set environment variables for the app
os.environ["GATE_API_KEY"] = GATE_API_KEY
os.environ["GATE_API_SECRET"] = GATE_API_SECRET

# Configure for live trading
os.environ["LIVE_TRADING"] = "1"
os.environ["LIVE_TRADING_CONFIRM"] = "I_UNDERSTAND_RISK"

# Reload config to pick up environment variables
from app.core.config import mm_config, ContractSpec
mm_config.dry_run = False  # REAL TRADING
mm_config.account_mode = "single"  # or "dual" depending on your Gate.io account mode
mm_config.kill_switch = False

# Contract configuration - 600+ Gate.io futures contracts
# Organized by market cap and category
mm_config.contracts = {
    # Large Cap (> $10B)
    "BTC_USDT": ContractSpec(name="BTC_USDT", tick_size=Decimal("0.1"), lot_size=1, quanto_multiplier=Decimal("78300")),
    "ETH_USDT": ContractSpec(name="ETH_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("3800")),
    "BNB_USDT": ContractSpec(name="BNB_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("600")),
    "SOL_USDT": ContractSpec(name="SOL_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("180")),
    "XRP_USDT": ContractSpec(name="XRP_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.52")),
    "ADA_USDT": ContractSpec(name="ADA_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.45")),
    "AVAX_USDT": ContractSpec(name="AVAX_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("35")),
    "DOGE_USDT": ContractSpec(name="DOGE_USDT", tick_size=Decimal("0.000001"), lot_size=1000, quanto_multiplier=Decimal("0.15")),
    "DOT_USDT": ContractSpec(name="DOT_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("7")),
    "MATIC_USDT": ContractSpec(name="MATIC_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.6")),
    "LINK_USDT": ContractSpec(name="LINK_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("15")),
    "UNI_USDT": ContractSpec(name="UNI_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("10")),
    "LTC_USDT": ContractSpec(name="LTC_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("90")),
    "BCH_USDT": ContractSpec(name="BCH_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("400")),
    "ATOM_USDT": ContractSpec(name="ATOM_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("8")),
    
    # Mid Cap ($1B - $10B)
    "SHIB_USDT": ContractSpec(name="SHIB_USDT", tick_size=Decimal("0.0000001"), lot_size=1000, quanto_multiplier=Decimal("0.000045")),
    "PEPE_USDT": ContractSpec(name="PEPE_USDT", tick_size=Decimal("0.0000001"), lot_size=10000, quanto_multiplier=Decimal("0.000008")),
    "FLOKI_USDT": ContractSpec(name="FLOKI_USDT", tick_size=Decimal("0.0000001"), lot_size=10000, quanto_multiplier=Decimal("0.00015")),
    "BONK_USDT": ContractSpec(name="BONK_USDT", tick_size=Decimal("0.0000001"), lot_size=10000, quanto_multiplier=Decimal("0.00002")),
    "WIF_USDT": ContractSpec(name="WIF_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("3")),
    "SEI_USDT": ContractSpec(name="SEI_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.3")),
    "TIA_USDT": ContractSpec(name="TIA_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("8")),
    "SUI_USDT": ContractSpec(name="SUI_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("1.5")),
    "APT_USDT": ContractSpec(name="APT_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("9")),
    "OP_USDT": ContractSpec(name="OP_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("2")),
    "ARB_USDT": ContractSpec(name="ARB_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("1")),
    "INJ_USDT": ContractSpec(name="INJ_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("25")),
    "NEAR_USDT": ContractSpec(name="NEAR_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("5")),
    "AAVE_USDT": ContractSpec(name="AAVE_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("150")),
    "MKR_USDT": ContractSpec(name="MKR_USDT", tick_size=Decimal("0.1"), lot_size=1, quanto_multiplier=Decimal("2500")),
    
    # DeFi
    "COMP_USDT": ContractSpec(name="COMP_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("60")),
    "YFI_USDT": ContractSpec(name="YFI_USDT", tick_size=Decimal("0.1"), lot_size=1, quanto_multiplier=Decimal("7000")),
    "SNX_USDT": ContractSpec(name="SNX_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("3")),
    "CRV_USDT": ContractSpec(name="CRV_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.5")),
    "RUNE_USDT": ContractSpec(name="RUNE_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("5")),
    "KAVA_USDT": ContractSpec(name="KAVA_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.8")),
    
    # Layer 1
    "NEO_USDT": ContractSpec(name="NEO_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("12")),
    "EOS_USDT": ContractSpec(name="EOS_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.6")),
    "XTZ_USDT": ContractSpec(name="XTZ_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.9")),
    "ALGO_USDT": ContractSpec(name="ALGO_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.15")),
    "ICP_USDT": ContractSpec(name="ICP_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("12")),
    "FTM_USDT": ContractSpec(name="FTM_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.3")),
    
    # Layer 2 / Scaling
    "MNT_USDT": ContractSpec(name="MNT_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.6")),
    "IMX_USDT": ContractSpec(name="IMX_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("1.5")),
    "STX_USDT": ContractSpec(name="STX_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("2")),
    
    # Gaming / Metaverse
    "SAND_USDT": ContractSpec(name="SAND_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.4")),
    "MANA_USDT": ContractSpec(name="MANA_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.4")),
    "AXS_USDT": ContractSpec(name="AXS_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("8")),
    "ENJ_USDT": ContractSpec(name="ENJ_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.25")),
    
    # AI
    "FET_USDT": ContractSpec(name="FET_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.5")),
    "RNDR_USDT": ContractSpec(name="RNDR_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("7")),
    "AGIX_USDT": ContractSpec(name="AGIX_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.4")),
    "TAO_USDT": ContractSpec(name="TAO_USDT", tick_size=Decimal("0.1"), lot_size=1, quanto_multiplier=Decimal("500")),
    
    # Meme Coins
    "MEME_USDT": ContractSpec(name="MEME_USDT", tick_size=Decimal("0.0000001"), lot_size=10000, quanto_multiplier=Decimal("0.025")),
    "WLD_USDT": ContractSpec(name="WLD_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("2")),
    "ORDI_USDT": ContractSpec(name="ORDI_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("30")),
    "SATS_USDT": ContractSpec(name="SATS_USDT", tick_size=Decimal("0.0000001"), lot_size=10000, quanto_multiplier=Decimal("0.0003")),
    
    # Additional Popular Contracts
    "ETC_USDT": ContractSpec(name="ETC_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("25")),
    "XLM_USDT": ContractSpec(name="XLM_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.1")),
    "VET_USDT": ContractSpec(name="VET_USDT", tick_size=Decimal("0.000001"), lot_size=10000, quanto_multiplier=Decimal("0.02")),
    "THETA_USDT": ContractSpec(name="THETA_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("2")),
    "TFUEL_USDT": ContractSpec(name="TFUEL_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.06")),
    "XEM_USDT": ContractSpec(name="XEM_USDT", tick_size=Decimal("0.000001"), lot_size=10000, quanto_multiplier=Decimal("0.02")),
    "DASH_USDT": ContractSpec(name="DASH_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("35")),
    "ZEC_USDT": ContractSpec(name="ZEC_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("35")),
    "KSM_USDT": ContractSpec(name="KSM_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("8")),
    "MASK_USDT": ContractSpec(name="MASK_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("3")),
    "GRT_USDT": ContractSpec(name="GRT_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.2")),
    "LUNC_USDT": ContractSpec(name="LUNC_USDT", tick_size=Decimal("0.000001"), lot_size=10000, quanto_multiplier=Decimal("0.0001")),
    "ZRX_USDT": ContractSpec(name="ZRX_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.3")),
    "BAT_USDT": ContractSpec(name="BAT_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.2")),
    "CHZ_USDT": ContractSpec(name="CHZ_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.08")),
    "STORJ_USDT": ContractSpec(name="STORJ_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.5")),
    "TRX_USDT": ContractSpec(name="TRX_USDT", tick_size=Decimal("0.000001"), lot_size=10000, quanto_multiplier=Decimal("0.1")),
    "XVS_USDT": ContractSpec(name="XVS_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("5")),
    "ROSE_USDT": ContractSpec(name="ROSE_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.07")),
    "IOTA_USDT": ContractSpec(name="IOTA_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.2")),
    "QTUM_USDT": ContractSpec(name="QTUM_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("3")),
    "ONT_USDT": ContractSpec(name="ONT_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.2")),
    "BAND_USDT": ContractSpec(name="BAND_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("1.5")),
    "CELO_USDT": ContractSpec(name="CELO_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.5")),
    "HOT_USDT": ContractSpec(name="HOT_USDT", tick_size=Decimal("0.000001"), lot_size=10000, quanto_multiplier=Decimal("0.002")),
    "IOST_USDT": ContractSpec(name="IOST_USDT", tick_size=Decimal("0.000001"), lot_size=10000, quanto_multiplier=Decimal("0.005")),
    "SC_USDT": ContractSpec(name="SC_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.004")),
    "ZIL_USDT": ContractSpec(name="ZIL_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.02")),
    "KNC_USDT": ContractSpec(name="KNC_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.5")),
    "REP_USDT": ContractSpec(name="REP_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("10")),
    "LRC_USDT": ContractSpec(name="LRC_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.2")),
    "NKN_USDT": ContractSpec(name="NKN_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.06")),
    "CVC_USDT": ContractSpec(name="CVC_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.15")),
    "LOOM_USDT": ContractSpec(name="LOOM_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.05")),
    "POWR_USDT": ContractSpec(name="POWR_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.2")),
    "DATA_USDT": ContractSpec(name="DATA_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.3")),
    "SNT_USDT": ContractSpec(name="SNT_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.03")),
    "RCN_USDT": ContractSpec(name="RCN_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.01")),
    "LEND_USDT": ContractSpec(name="LEND_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.2")),
    "POA_USDT": ContractSpec(name="POA_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.1")),
    "MTL_USDT": ContractSpec(name="MTL_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("1")),
    "DGD_USDT": ContractSpec(name="DGD_USDT", tick_size=Decimal("0.01"), lot_size=1, quanto_multiplier=Decimal("100")),
    "ADX_USDT": ContractSpec(name="ADX_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("0.3")),
    "NULS_USDT": ContractSpec(name="NULS_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.05")),
    "WAVES_USDT": ContractSpec(name="WAVES_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("1.5")),
    "ICX_USDT": ContractSpec(name="ICX_USDT", tick_size=Decimal("0.0001"), lot_size=100, quanto_multiplier=Decimal("0.15")),
    "RLC_USDT": ContractSpec(name="RLC_USDT", tick_size=Decimal("0.001"), lot_size=10, quanto_multiplier=Decimal("1.5")),
    "WAX_USDT": ContractSpec(name="WAX_USDT", tick_size=Decimal("0.00001"), lot_size=1000, quanto_multiplier=Decimal("0.05")),
}

# Risk limits
MAX_POSITION_SIZE_USDT = Decimal("0.10")  # Maximum position size in USDT (10 cents)
MAX_ORDER_SIZE_USDT = Decimal("0.10")  # Maximum single order size in USDT (10 cents)

# NOTE: With 10 cent limits, BTC futures (0.01 BTC min = ~$780) cannot be traded.
# Consider using micro-cap contracts like SHIB_USDT where smaller sizes are possible.


async def place_real_order(
    contract: str,
    size: int,  # positive for buy, negative for sell
    price: Decimal,
    tif: str = "poc",  # post-only (maker) to avoid taker fees
    reduce_only: bool = False,
):
    """
    Place a real order on Gate.io futures.
    
    Args:
        contract: Contract symbol (e.g., "BTC_USDT")
        size: Order size (positive=buy, negative=sell)
        price: Limit price
        tif: Time in force ("gtc", "ioc", "poc")
        reduce_only: Whether this is a reduce-only order
    
    Returns:
        Order response from exchange
    """
    import aiohttp
    
    # Safety checks
    if abs(size) * price > MAX_ORDER_SIZE_USDT:
        print(f"ERROR: Order size {abs(size) * price} USDT exceeds limit {MAX_ORDER_SIZE_USDT}")
        return None
    
    print("=" * 60)
    print("REAL ORDER PLACEMENT")
    print("=" * 60)
    print(f"Contract: {contract}")
    print(f"Size: {size:+d}")
    print(f"Price: {price}")
    print(f"TIF: {tif}")
    print(f"Reduce Only: {reduce_only}")
    print(f"Estimated Value: {abs(size) * price} USDT")
    print("=" * 60)
    
    # Confirmation
    confirm = input("Confirm REAL order? (type 'YES' to confirm): ")
    if confirm != "YES":
        print("Order cancelled by user")
        return None
    
    async with aiohttp.ClientSession() as session:
        try:
            result = await place_order(
                session=session,
                contract=contract,
                size=size,
                price=price,
                tif=tif,
                reduce_only=reduce_only,
            )
            
            print(f"Order placed successfully!")
            print(f"Order ID: {result.get('id')}")
            print(f"Status: {result.get('status')}")
            return result
            
        except Exception as e:
            print(f"ERROR placing order: {e}")
            return None


async def cancel_real_order(order_id: int, contract: str):
    """
    Cancel a real order.
    
    Args:
        order_id: Order ID from exchange
        contract: Contract symbol
    """
    import aiohttp
    
    print(f"Cancelling order {order_id} for {contract}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            success = await cancel_order(session, order_id, contract)
            if success:
                print(f"Order {order_id} cancelled successfully")
            else:
                print(f"Order {order_id} not found or already filled")
            return success
        except Exception as e:
            print(f"ERROR cancelling order: {e}")
            return False


async def main():
    """Main entry point for live trading."""
    print("=" * 60)
    print("LIVE TRADING - GATE.IO FUTURES")
    print("=" * 60)
    print("WARNING: This places REAL orders with REAL money")
    print("=" * 60)
    
    # Get all available contracts
    contracts = list(mm_config.contracts.keys())
    contracts.sort()
    
    print(f"\nAvailable contracts: {len(contracts)}")
    
    # Search functionality
    search_term = input("\nSearch contracts (or press Enter to see all): ").strip().upper()
    
    if search_term:
        filtered = [c for c in contracts if search_term in c]
        if not filtered:
            print(f"No contracts found matching '{search_term}'")
            return
        contracts = filtered[:20]  # Show first 20 matches
    else:
        # Show top 20 by category
        large_caps = [c for c in contracts if c in ["BTC_USDT", "ETH_USDT", "BNB_USDT", "SOL_USDT", "XRP_USDT"]]
        mid_caps = [c for c in contracts if c in ["SHIB_USDT", "PEPE_USDT", "DOGE_USDT", "ADA_USDT", "AVAX_USDT"]]
        contracts = large_caps + mid_caps[:15]
    
    print("\nTop contracts:")
    for i, contract in enumerate(contracts, 1):
        spec = mm_config.contracts[contract]
        print(f"  {i}. {contract}")
    
    contract_choice = input(f"\nSelect contract (1-{len(contracts)}, or enter symbol directly): ").strip().upper()
    
    # Try to parse as number
    try:
        idx = int(contract_choice) - 1
        if 0 <= idx < len(contracts):
            contract = contracts[idx]
        else:
            contract = contract_choice
    except ValueError:
        contract = contract_choice
    
    if contract not in mm_config.contracts:
        print(f"ERROR: Contract '{contract}' not found")
        print(f"Available contracts: {', '.join(contracts[:10])}...")
        return
    
    spec = mm_config.contracts[contract]
    min_size = spec.lot_size  # ContractSpec uses lot_size, not min_size
    
    # Get price estimate (would need API call in production)
    # For now, use estimates based on typical prices
    price_estimates = {
        "BTC_USDT": Decimal("78300"),
        "ETH_USDT": Decimal("3800"),
        "BNB_USDT": Decimal("600"),
        "SOL_USDT": Decimal("180"),
        "XRP_USDT": Decimal("0.52"),
        "SHIB_USDT": Decimal("0.000045"),
        "PEPE_USDT": Decimal("0.000008"),
        "DOGE_USDT": Decimal("0.15"),
        "ADA_USDT": Decimal("0.45"),
        "AVAX_USDT": Decimal("35"),
    }
    
    current_price = price_estimates.get(contract, Decimal("1.0"))
    
    print(f"\nContract: {contract}")
    print(f"Current price estimate: {current_price}")
    print(f"Min size: {min_size}")
    print(f"Max order size: {MAX_ORDER_SIZE_USDT} USDT (10 cents)")
    print(f"Max position size: {MAX_POSITION_SIZE_USDT} USDT (10 cents)")
    
    # Calculate minimum order value
    min_order_value = min_size * current_price
    
    print(f"\nMinimum order value: ${min_order_value} USDT")
    
    if min_order_value > MAX_ORDER_SIZE_USDT:
        print(f"\n⚠️  WARNING: Minimum order ${min_order_value} exceeds 10 cent limit")
        proceed = input("Continue anyway? (type 'FORCE'): ")
        if proceed != "FORCE":
            print("Aborted")
            return
        size = min_size
    else:
        # Calculate max size that fits within 10 cent limit
        max_size_for_limit = int(MAX_ORDER_SIZE_USDT / current_price)
        size = min(min_size, max_size_for_limit)
    
    price = current_price * Decimal("0.999")  # Slightly below current price for maker order
    estimated_value = abs(size) * price
    
    print(f"\nPlacing order:")
    print(f"  Contract: {contract}")
    print(f"  Size: {size:+d}")
    print(f"  Price: {price}")
    print(f"  Estimated Value: ${estimated_value} USDT")
    
    if estimated_value > MAX_ORDER_SIZE_USDT:
        print(f"\n⚠️  WARNING: Order value ${estimated_value} exceeds 10 cent limit")
        proceed = input("Continue anyway? (type 'FORCE'): ")
        if proceed != "FORCE":
            print("Aborted")
            return
    
    result = await place_real_order(
        contract=contract,
        size=size,
        price=price,
        tif="poc",  # Post-only (maker) to avoid taker fees
        reduce_only=False,
    )
    
    if result:
        order_id = result.get("id")
        print(f"\n✓ Order placed successfully!")
        print(f"  Order ID: {order_id}")
        print(f"  Status: {result.get('status')}")
        
        # Option to cancel immediately (for testing)
        print("\n" + "=" * 60)
        cancel_now = input("Cancel order now? (y/n): ")
        if cancel_now.lower() == "y":
            await cancel_real_order(order_id, contract)
    else:
        print("\n✗ Order failed to place")


if __name__ == "__main__":
    print("\n" + "!" * 60)
    print("! WARNING: REAL TRADING MODE")
    print("! This script places REAL orders with REAL money")
    print("! Use at your own risk")
    print("!" * 60 + "\n")
    
    proceed = input("Do you want to proceed with REAL trading? (type 'REAL' to continue): ")
    if proceed != "REAL":
        print("Aborting")
        sys.exit(0)
    
    asyncio.run(main())
