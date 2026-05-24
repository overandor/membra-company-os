#!/usr/bin/env python3
import os
"""
BRUTALIST MARKET MAKER - FIXED VERSION
Clean, working implementation
"""

import asyncio
import websockets
import json
import time
import math
import logging
from typing import Dict, List, Optional, Tuple
from collections import deque
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class MarketMakerConfig:
    """Configuration for market maker"""
    
    def __init__(self):
        # API
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        self.symbol = "ENA_USDT"
        
        # Trading
        self.order_size_usd = 0.05  # Tiny order size for safety
        self.spread_bps = 10.0  # 10 bps spread
        self.max_position = 2.0  # Max 2 tokens
        
        # Risk
        self.max_balance_usage = 0.1  # Use 10% of balance
        self.stop_loss_bps = 50.0  # 50 bps stop loss

class BrutalistMarketMaker:
    """Simplified market maker"""
    
    def __init__(self, config: MarketMakerConfig):
        self.config = config
        self.running = False
        self.position = 0.0
        self.last_mid = 0.0
        self.orders = {}
        
        # Initialize API
        cfg = Configuration(key=config.api_key, secret=config.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # WebSocket
        self.ws = None
        
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket"""
        try:
            self.ws = await websockets.connect("wss://fx-ws.gateio.ws/v4/ws/usdt")
            log.info("✅ WebSocket connected")
            
            # Subscribe to order book
            subscribe_msg = {
                "time": int(time.time()),
                "channel": "futures.order_book",
                "event": "subscribe",
                "payload": [self.config.symbol, 5, 0]
            }
            await self.ws.send(json.dumps(subscribe_msg))
            log.info(f"📊 Subscribed to {self.config.symbol}")
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
    
    async def place_order(self, side: str, price: float, size: float) -> Optional[str]:
        """Place an order"""
        try:
            order = gate_api.FuturesOrder(
                contract=self.config.symbol,
                size=size,
                price=price,
                side=side,
                type='limit',
                time_in_force='post_only',
                client_order_id=f"mm_{int(time.time() * 1000)}"
            )
            
            result = self.api.create_futures_order(settle='usdt', order=order)
            log.info(f"📈 Order placed: {side.upper()} {size:.6f} @ ${price:.6f}")
            return result.id
            
        except Exception as e:
            log.error(f"❌ Order failed: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.api.cancel_futures_order(settle='usdt', order_id=order_id)
            log.info(f"❌ Order cancelled: {order_id}")
            return True
        except Exception as e:
            log.error(f"❌ Cancel failed: {e}")
            return False
    
    async def manage_orders(self, bids: List, asks: List):
        """Manage orders based on market data"""
        if not bids or not asks:
            return
        
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid = (best_bid + best_ask) / 2
        
        # Cancel existing orders
        for order_id in list(self.orders.keys()):
            await self.cancel_order(order_id)
            del self.orders[order_id]
        
        # Calculate order size
        balance = await self.get_balance()
        max_order_value = balance * self.config.max_balance_usage
        size = min(max_order_value / mid, self.config.order_size_usd / mid)
        
        # Position limits
        if abs(self.position) >= self.config.max_position:
            log.info(f"⚠️ Position limit reached: {self.position:.6f}")
            return
        
        # Place new orders
        if self.position <= 0:  # Can buy
            buy_price = best_bid + 0.00001
            order_id = await self.place_order('buy', buy_price, size)
            if order_id:
                self.orders[order_id] = {'side': 'buy', 'price': buy_price, 'size': size}
        
        if self.position >= 0:  # Can sell
            sell_price = best_ask - 0.00001
            order_id = await self.place_order('sell', sell_price, size)
            if order_id:
                self.orders[order_id] = {'side': 'sell', 'price': sell_price, 'size': size}
    
    async def process_messages(self):
        """Process WebSocket messages"""
        try:
            async for message in self.ws:
                if not self.running:
                    break
                
                data = json.loads(message)
                
                if data.get('channel') == 'futures.order_book' and data.get('event') == 'update':
                    bids = data.get('result', {}).get('bids', [])
                    asks = data.get('result', {}).get('asks', [])
                    
                    if bids and asks:
                        await self.manage_orders(bids, asks)
                        
        except Exception as e:
            log.error(f"❌ Message processing error: {e}")
    
    async def run(self):
        """Run the market maker"""
        self.running = True
        
        # Connect WebSocket
        if not await self.connect_websocket():
            return
        
        # Initial balance check
        balance = await self.get_balance()
        if balance < 1.0:
            log.error("❌ Insufficient balance")
            return
        
        log.info(f"🚀 Starting market maker for {self.config.symbol}")
        log.info(f"💰 Order size: ${self.config.order_size_usd}")
        log.info(f"📊 Spread: {self.config.spread_bps} bps")
        
        try:
            await self.process_messages()
        except KeyboardInterrupt:
            log.info("⏹️ Shutting down...")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the market maker"""
        self.running = False
        
        # Cancel all orders
        for order_id in list(self.orders.keys()):
            await self.cancel_order(order_id)
        
        if self.ws:
            await self.ws.close()
        
        log.info("✅ Market maker stopped")

async def main():
    """Main entry point"""
    print("🤖 BRUTALIST MARKET MAKER - FIXED VERSION")
    print("📊 Simple, clean, working implementation")
    print("=" * 50)
    
    config = MarketMakerConfig()
    mm = BrutalistMarketMaker(config)
    
    try:
        await mm.run()
    except Exception as e:
        log.error(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
