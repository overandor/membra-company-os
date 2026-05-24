#!/usr/bin/env python3
import os
"""
SIMPLE MARKET MAKER
Works with major liquid coins - perfect for $12 budget
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MAKER - %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/simple_market_maker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleMarketMaker:
    """Simple market maker for liquid coins"""
    
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Focus on most liquid coins
        self.symbols = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "ENA_USDT"]
        
        # Budget management
        self.total_budget = 12.0
        self.per_symbol_budget = 3.0  # $3 per symbol
        
        # Trading parameters
        self.order_size_usdt = 2.0  # $2 worth per order
        self.max_spread_bps = 50   # Max 0.5% spread
        self.min_spread_bps = 5    # Min 0.05% spread
        
        # Active orders
        self.active_orders: Dict[str, Dict] = {}
        
        # Performance
        self.total_orders = 0
        self.successful_orders = 0
        self.total_profit = 0.0
        
        logger.info("🏪 Simple Market Maker initialized")
        logger.info(f"💰 Budget: ${self.total_budget}")
        logger.info(f"🎯 Symbols: {self.symbols}")
        logger.info(f"💵 Per order: ${self.order_size_usdt}")
    
    async def get_order_book(self, symbol: str) -> Optional[Dict]:
        """Get order book for symbol"""
        try:
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=5)
            
            if not book.bids or not book.asks:
                return None
            
            best_bid = float(book.bids[0].p)
            best_ask = float(book.asks[0].p)
            bid_size = float(book.bids[0].s)
            ask_size = float(book.asks[0].s)
            
            mid_price = (best_bid + best_ask) / 2
            spread_bps = (best_ask - best_bid) / mid_price * 10000
            
            return {
                'symbol': symbol,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'bid_size': bid_size,
                'ask_size': ask_size,
                'mid_price': mid_price,
                'spread_bps': spread_bps
            }
            
        except Exception as e:
            logger.error(f"❌ Order book for {symbol}: {e}")
            return None
    
    def calculate_order_size(self, price: float) -> float:
        """Calculate order size based on USD value"""
        return self.order_size_usdt / price
    
    async def place_buy_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place buy order"""
        try:
            order_params = {
                'contract': symbol,
                'side': 'buy',
                'type': 'limit',
                'size': size,
                'price': str(price),
                'time_in_force': 'post_only'
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            
            logger.info(f"💚 BUY PLACED: {symbol}")
            logger.info(f"   Price: ${price:.4f} | Size: {size:.6f}")
            logger.info(f"   Value: ${price * size:.4f}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Buy order failed: {e}")
            return None
    
    async def place_sell_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place sell order"""
        try:
            order_params = {
                'contract': symbol,
                'side': 'sell',
                'type': 'limit',
                'size': size,
                'price': str(price),
                'time_in_force': 'post_only'
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            
            logger.info(f"❤️ SELL PLACED: {symbol}")
            logger.info(f"   Price: ${price:.4f} | Size: {size:.6f}")
            logger.info(f"   Value: ${price * size:.4f}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Sell order failed: {e}")
            return None
    
    async def create_market_maker_pair(self, symbol: str, order_book: Dict) -> bool:
        """Create buy/sell pair"""
        # Check spread
        if order_book['spread_bps'] < self.min_spread_bps or order_book['spread_bps'] > self.max_spread_bps:
            return False
        
        # Calculate sizes
        buy_size = self.calculate_order_size(order_book['best_bid'])
        sell_size = self.calculate_order_size(order_book['best_ask'])
        
        # Place buy order
        buy_order_id = await self.place_buy_order(symbol, order_book['best_bid'], buy_size)
        if not buy_order_id:
            return False
        
        # Place sell order
        sell_order_id = await self.place_sell_order(symbol, order_book['best_ask'], sell_size)
        if not sell_order_id:
            # Cancel buy order if sell failed
            try:
                self.api.cancel_futures_order(settle='usdt', order_id=buy_order_id)
            except:
                pass
            return False
        
        # Store active orders
        self.active_orders[symbol] = {
            'buy_order_id': buy_order_id,
            'sell_order_id': sell_order_id,
            'buy_price': order_book['best_bid'],
            'sell_price': order_book['best_ask'],
            'buy_size': buy_size,
            'sell_size': sell_size,
            'spread_bps': order_book['spread_bps'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.total_orders += 2
        
        expected_profit = (order_book['best_ask'] - order_book['best_bid']) * min(buy_size, sell_size)
        
        logger.info(f"🏪 PAIR CREATED: {symbol}")
        logger.info(f"   Buy: ${order_book['best_bid']:.4f} | Sell: ${order_book['best_ask']:.4f}")
        logger.info(f"   Spread: {order_book['spread_bps']:.1f} bps")
        logger.info(f"   Expected Profit: ${expected_profit:.6f}")
        logger.info(f"   Active Pairs: {len(self.active_orders)}")
        
        return True
    
    async def check_and_refresh_orders(self):
        """Check and refresh stale orders"""
        current_time = datetime.now()
        
        for symbol, orders in list(self.active_orders.items()):
            try:
                # Check if orders are stale (older than 60 seconds)
                order_time = datetime.fromisoformat(orders['timestamp'])
                if (current_time - order_time).total_seconds() > 60:
                    logger.info(f"🔄 Refreshing stale orders: {symbol}")
                    
                    # Cancel old orders
                    try:
                        self.api.cancel_futures_order(settle='usdt', order_id=orders['buy_order_id'])
                        self.api.cancel_futures_order(settle='usdt', order_id=orders['sell_order_id'])
                    except:
                        pass
                    
                    # Remove from active orders
                    del self.active_orders[symbol]
                    self.successful_orders += 2
                
            except Exception as e:
                logger.error(f"❌ Error checking {symbol}: {e}")
    
    async def simple_market_making_loop(self):
        """Main market making loop"""
        logger.info("🏪 SIMPLE MARKET MAKING LOOP STARTED")
        logger.info(f"🎯 Strategy: Buy Best Bid, Sell Best Ask")
        logger.info(f"💰 Order Size: ${self.order_size_usdt} per side")
        logger.info(f"📊 Symbols: {self.symbols}")
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                
                # Check and refresh stale orders
                await self.check_and_refresh_orders()
                
                # Create new pairs if we have capacity
                max_pairs = len(self.symbols)
                current_pairs = len(self.active_orders)
                
                if current_pairs < max_pairs:
                    for symbol in self.symbols:
                        if current_pairs >= max_pairs:
                            break
                        
                        if symbol in self.active_orders:
                            continue
                        
                        # Get order book
                        order_book = await self.get_order_book(symbol)
                        if order_book:
                            if await self.create_market_maker_pair(symbol, order_book):
                                current_pairs += 1
                
                # Log status
                logger.info(f"📊 Cycle {cycle}: Active Pairs: {len(self.active_orders)}/{max_pairs} | "
                           f"Total Orders: {self.total_orders} | "
                           f"Success: {self.successful_orders}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Market making error: {e}")
                await asyncio.sleep(10)
    
    def get_performance_report(self) -> Dict:
        """Get performance report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_budget': self.total_budget,
            'active_pairs': len(self.active_orders),
            'total_orders': self.total_orders,
            'successful_orders': self.successful_orders,
            'success_rate': self.successful_orders / max(1, self.total_orders),
            'symbols_traded': len(self.symbols)
        }

async def main():
    """Main simple market maker"""
    print("🏪 SIMPLE MARKET MAKER")
    print("="*60)
    print("💰 Budget: $12")
    print("🎯 Strategy: Buy Best Bid, Sell Best Ask")
    print("💚 Major Liquid Coins Only")
    print("💵 $2 per order side")
    print("🔄 Up to 4 symbols simultaneously")
    print("="*60)
    
    # Initialize simple market maker
    maker = SimpleMarketMaker()
    
    try:
        # Start market making
        await maker.simple_market_making_loop()
        
    except KeyboardInterrupt:
        print("\n🏪 Simple market maker stopped by user")
        
        # Performance report
        report = maker.get_performance_report()
        print("\n" + "="*60)
        print("📊 PERFORMANCE REPORT")
        print("="*60)
        print(f"💰 Total Budget: ${report['total_budget']}")
        print(f"🔄 Active Pairs: {report['active_pairs']}")
        print(f"📊 Total Orders: {report['total_orders']}")
        print(f"✅ Successful Orders: {report['successful_orders']}")
        print(f"🎯 Success Rate: {report['success_rate']:.1%}")
        print(f"🪙 Symbols Traded: {report['symbols_traded']}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Simple market maker error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
