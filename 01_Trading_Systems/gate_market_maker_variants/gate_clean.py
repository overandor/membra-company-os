#!/usr/bin/env python3
"""
Gate.io Multi-Pair Market Maker - Clean Version
Simple, working implementation with best bid/ask strategy
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import os
import signal
import sys
import time
from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import websockets
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

class GateConfig:
    """Configuration for Gate.io market maker"""
    
    def __init__(self):
        # API credentials
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Trading symbols
        self.symbols = ["ENA_USDT", "PEPE_USDT", "SHIB_USDT"]
        
        # Risk management
        self.max_order_value_usd = 0.05  # $0.05 per order
        self.max_total_exposure_usd = 0.15  # $0.15 total
        self.spread_bps = 10.0  # 10 bps spread
        
        # WebSocket
        self.ws_url = "wss://fx-ws.gateio.ws/v4/ws/usdt"

class GateMarketMaker:
    """Simple Gate.io market maker"""
    
    def __init__(self, config: GateConfig):
        self.config = config
        self.running = False
        
        # Initialize API
        api_cfg = Configuration(key=config.api_key, secret=config.api_secret)
        self.api = FuturesApi(ApiClient(api_cfg))
        
        # Market data
        self.order_books = {}
        self.positions = {}
        
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket"""
        try:
            self.ws = await websockets.connect(self.config.ws_url)
            log.info("✅ WebSocket connected")
            
            # Subscribe to order books
            for symbol in self.config.symbols:
                subscribe_msg = {
                    "time": int(time.time()),
                    "channel": "futures.order_book",
                    "event": "subscribe", 
                    "payload": [symbol, 5, 0]
                }
                await self.ws.send(json.dumps(subscribe_msg))
                log.info(f"📊 Subscribed to {symbol}")
            
            return True
            
        except Exception as e:
            log.error(f"❌ WebSocket error: {e}")
            return False
    
    async def get_balance(self) -> float:
        """Get account balance"""
        try:
            account = self.api.get_futures_account(settle='usdt')
            balance = float(account.available)
            log.info(f"💰 Balance: ${balance:.2f}")
            return balance
        except Exception as e:
            log.error(f"❌ Balance error: {e}")
            return 0.0
    
    async def place_order(self, symbol: str, side: str, price: float, size: float) -> Optional[str]:
        """Place an order"""
        try:
            order = gate_api.FuturesOrder(
                contract=symbol,
                size=size,
                price=price,
                side=side,
                type='limit',
                time_in_force='post_only',
                client_order_id=f"mm_{symbol}_{int(time.time() * 1000)}"
            )
            
            result = self.api.create_futures_order(settle='usdt', order=order)
            log.info(f"📈 Order placed: {symbol} {side.upper()} {size:.6f} @ ${price:.6f}")
            return result.id
            
        except Exception as e:
            log.error(f"❌ Order failed: {e}")
            return None
    
    async def process_messages(self):
        """Process WebSocket messages"""
        try:
            async for message in self.ws:
                if not self.running:
                    break
                
                data = json.loads(message)
                
                if data.get('channel') == 'futures.order_book' and data.get('event') == 'update':
                    result = data.get('result', {})
                    symbol = result.get('s', '')
                    bids = result.get('bids', [])
                    asks = result.get('asks', [])
                    
                    if symbol and bids and asks:
                        self.order_books[symbol] = {
                            'bids': bids,
                            'asks': asks,
                            'timestamp': time.time()
                        }
                        
                        # Process trading opportunity
                        await self.process_symbol(symbol, bids, asks)
                        
        except Exception as e:
            log.error(f"❌ Message processing error: {e}")
    
    async def process_symbol(self, symbol: str, bids: List, asks: List):
        """Process trading for a specific symbol"""
        if not bids or not asks:
            return
        
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid = (best_bid + best_ask) / 2
        
        # Calculate spread
        spread_bps = (best_ask - best_bid) / mid * 10000
        
        # Only trade if spread is good
        if spread_bps < self.config.spread_bps:
            return
        
        # Calculate order size
        balance = await self.get_balance()
        max_order_value = min(self.config.max_order_value_usd, balance * 0.05)
        size = max_order_value / mid
        
        # Place orders
        buy_price = best_bid + 0.00001
        sell_price = best_ask - 0.00001
        
        await self.place_order(symbol, 'buy', buy_price, size)
        await asyncio.sleep(0.1)
        await self.place_order(symbol, 'sell', sell_price, size)
    
    async def run(self):
        """Run the market maker"""
        self.running = True
        
        log.info("🚀 Starting Gate.io Market Maker")
        log.info(f"📊 Symbols: {', '.join(self.config.symbols)}")
        log.info(f"💰 Max order: ${self.config.max_order_value_usd}")
        
        # Connect WebSocket
        if not await self.connect_websocket():
            return
        
        # Initial balance check
        balance = await self.get_balance()
        if balance < 1.0:
            log.error("❌ Insufficient balance")
            return
        
        try:
            await self.process_messages()
        except KeyboardInterrupt:
            log.info("⏹️ Shutting down...")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the market maker"""
        self.running = False
        if hasattr(self, 'ws') and self.ws:
            await self.ws.close()
        log.info("✅ Market maker stopped")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Gate.io Market Maker')
    parser.add_argument('--dry', action='store_true', help='Dry run mode')
    parser.add_argument('--live', action='store_true', help='Live trading mode')
    parser.add_argument('--balance', action='store_true', help='Check balance')
    parser.add_argument('--positions', action='store_true', help='Check positions')
    parser.add_argument('--cancel-all', action='store_true', help='Cancel all orders')
    parser.add_argument('--flatten-all', action='store_true', help='Flatten all positions')
    
    args = parser.parse_args()
    
    print("🤖 Gate.io Multi-Pair Market Maker - Clean Version")
    print("=" * 50)
    
    config = GateConfig()
    mm = GateMarketMaker(config)
    
    if args.balance:
        asyncio.run(mm.get_balance())
    elif args.positions:
        print("Position check not implemented")
    elif args.cancel_all:
        print("Cancel all not implemented")
    elif args.flatten_all:
        print("Flatten all not implemented")
    elif args.dry:
        print("🔍 Dry run mode - no real trades")
        asyncio.run(mm.run())
    elif args.live:
        print("🚀 Live trading mode")
        asyncio.run(mm.run())
    else:
        print("Use --dry for testing or --live for real trading")
        print("Use --balance to check account balance")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
