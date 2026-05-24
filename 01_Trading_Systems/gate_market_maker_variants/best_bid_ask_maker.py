#!/usr/bin/env python3
import os
"""
BEST BID/ASK MARKET MAKER
Pure Market Making Strategy - Buy at Best Bid, Sell at Best Ask
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MARKET_MAKER - %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/best_bid_ask_maker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class OrderPair:
    """Buy/Sell order pair for market making"""
    symbol: str
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    buy_price: float = 0.0
    sell_price: float = 0.0
    size: float = 0.0
    spread_profit: float = 0.0
    status: str = "placing"  # placing, active, partial, completed
    buy_filled: float = 0.0
    sell_filled: float = 0.0
    timestamp: str = ""

@dataclass
class MarketMakerMetrics:
    """Market making performance metrics"""
    total_cycles: int = 0
    successful_cycles: int = 0
    total_spread_profit: float = 0.0
    avg_spread_bps: float = 0.0
    total_volume: float = 0.0
    active_pairs: int = 0
    profit_per_hour: float = 0.0
    start_time: str = ""

class BestBidAskMarketMaker:
    """Pure market maker - buy best bid, sell best ask"""
    
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Market making parameters
        self.symbols = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "ENA_USDT", "DOGE_USDT", "SHIB_USDT"]
        self.order_size = 10.0  # Base order size
        self.max_spread_bps = 50  # Max spread to trade (50 bps = 0.5%)
        self.min_spread_bps = 5   # Min spread to be profitable
        self.max_position_per_symbol = 50.0
        self.max_total_exposure = 200.0
        
        # Active order pairs
        self.active_pairs: Dict[str, OrderPair] = {}
        
        # Performance tracking
        self.metrics = MarketMakerMetrics(start_time=datetime.now().isoformat())
        
        # Risk management
        self.total_exposure = 0.0
        self.daily_loss_limit = 10.0
        self.daily_pnl = 0.0
        
        logger.info("🏪 Best Bid/Ask Market Maker initialized")
        logger.info(f"📊 Symbols: {self.symbols}")
        logger.info(f"💰 Order Size: {self.order_size}")
        logger.info(f"📈 Max Spread: {self.max_spread_bps} bps")
        logger.info(f"🎯 Strategy: Buy Best Bid, Sell Best Ask")
    
    async def get_order_book(self, symbol: str) -> Dict:
        """Get current order book for a symbol"""
        try:
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=5)
            
            if not book.bids or not book.asks:
                return {}
            
            best_bid = float(book.bids[0].p)
            best_ask = float(book.asks[0].p)
            bid_size = float(book.bids[0].s)
            ask_size = float(book.asks[0].s)
            
            mid_price = (best_bid + best_ask) / 2
            spread_bps = (best_ask - best_bid) / mid_price * 10000
            spread_profit = (best_ask - best_bid) * self.order_size
            
            return {
                'symbol': symbol,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'bid_size': bid_size,
                'ask_size': ask_size,
                'mid_price': mid_price,
                'spread_bps': spread_bps,
                'spread_profit': spread_profit,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Order book error for {symbol}: {e}")
            return {}
    
    async def get_positions(self) -> Dict[str, float]:
        """Get current positions"""
        try:
            positions = self.api.list_positions(settle='usdt')
            current_positions = {}
            
            for pos in positions:
                if float(pos.size) != 0:
                    current_positions[pos.contract] = float(pos.size)
            
            return current_positions
            
        except Exception as e:
            logger.error(f"❌ Positions error: {e}")
            return {}
    
    async def place_buy_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place buy order at best bid price"""
        try:
            order_params = {
                'contract': symbol,
                'side': 'buy',
                'type': 'limit',
                'size': size,
                'price': str(price),
                'time_in_force': 'post_only'  # Only maker orders
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            logger.info(f"💚 BUY ORDER PLACED: {symbol}")
            logger.info(f"   Price: ${price:.6f} | Size: {size}")
            logger.info(f"   Order ID: {result.id}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Buy order failed for {symbol}: {e}")
            return None
    
    async def place_sell_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place sell order at best ask price"""
        try:
            order_params = {
                'contract': symbol,
                'side': 'sell',
                'type': 'limit',
                'size': size,
                'price': str(price),
                'time_in_force': 'post_only'  # Only maker orders
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            logger.info(f"❤️ SELL ORDER PLACED: {symbol}")
            logger.info(f"   Price: ${price:.6f} | Size: {size}")
            logger.info(f"   Order ID: {result.id}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Sell order failed for {symbol}: {e}")
            return None
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.api.cancel_futures_order(settle='usdt', order_id=order_id)
            logger.info(f"🚫 ORDER CANCELLED: {order_id} ({symbol})")
            return True
        except Exception as e:
            logger.error(f"❌ Cancel failed for {order_id}: {e}")
            return False
    
    async def check_order_status(self, symbol: str, order_id: str) -> Dict:
        """Check order fill status"""
        try:
            orders = self.api.list_futures_orders(settle='usdt', status='finished')
            
            for order in orders:
                if order.id == order_id:
                    return {
                        'status': 'filled',
                        'filled_size': float(order.size),
                        'avg_price': float(order.fill_price) if order.fill_price else 0.0
                    }
            
            # Check if still open
            open_orders = self.api.list_futures_orders(settle='usdt', status='open')
            for order in open_orders:
                if order.id == order_id:
                    return {
                        'status': 'open',
                        'filled_size': float(order.filled_size) if order.filled_size else 0.0,
                        'avg_price': float(order.fill_price) if order.fill_price else 0.0
                    }
            
            return {'status': 'not_found', 'filled_size': 0.0, 'avg_price': 0.0}
            
        except Exception as e:
            logger.error(f"❌ Order status check failed: {e}")
            return {'status': 'error', 'filled_size': 0.0, 'avg_price': 0.0}
    
    async def create_market_maker_pair(self, symbol: str, order_book: Dict) -> bool:
        """Create buy/sell pair at best bid/ask"""
        if not order_book:
            return False
        
        # Check if spread is profitable
        spread_bps = order_book['spread_bps']
        if spread_bps < self.min_spread_bps or spread_bps > self.max_spread_bps:
            logger.debug(f"📊 {symbol}: Spread {spread_bps:.1f} bps - not suitable")
            return False
        
        # Check position limits
        positions = await self.get_positions()
        current_position = positions.get(symbol, 0.0)
        
        if abs(current_position) >= self.max_position_per_symbol:
            logger.warning(f"⚠️ {symbol}: Position limit reached ({current_position:.1f})")
            return False
        
        # Check total exposure
        if self.total_exposure >= self.max_total_exposure:
            logger.warning(f"⚠️ Total exposure limit reached ({self.total_exposure:.1f})")
            return False
        
        # Create order pair
        buy_price = order_book['best_bid']
        sell_price = order_book['best_ask']
        spread_profit = order_book['spread_profit']
        
        # Place buy order at best bid
        buy_order_id = await self.place_buy_order(symbol, buy_price, self.order_size)
        if not buy_order_id:
            return False
        
        # Place sell order at best ask
        sell_order_id = await self.place_sell_order(symbol, sell_price, self.order_size)
        if not sell_order_id:
            # Cancel buy order if sell failed
            await self.cancel_order(symbol, buy_order_id)
            return False
        
        # Create order pair
        order_pair = OrderPair(
            symbol=symbol,
            buy_order_id=buy_order_id,
            sell_order_id=sell_order_id,
            buy_price=buy_price,
            sell_price=sell_price,
            size=self.order_size,
            spread_profit=spread_profit,
            status="active",
            timestamp=datetime.now().isoformat()
        )
        
        self.active_pairs[symbol] = order_pair
        self.total_exposure += self.order_size * 2  # Both sides
        
        logger.info(f"🏪 MARKET MAKER PAIR CREATED: {symbol}")
        logger.info(f"   Buy: ${buy_price:.6f} | Sell: ${sell_price:.6f}")
        logger.info(f"   Spread: {spread_bps:.1f} bps | Profit: ${spread_profit:.4f}")
        logger.info(f"   Total Exposure: ${self.total_exposure:.1f}")
        
        return True
    
    async def manage_active_pairs(self):
        """Manage and monitor active order pairs"""
        if not self.active_pairs:
            return
        
        for symbol, pair in list(self.active_pairs.items()):
            try:
                # Check order statuses
                buy_status = await self.check_order_status(symbol, pair.buy_order_id)
                sell_status = await self.check_order_status(symbol, pair.sell_order_id)
                
                # Update fill amounts
                pair.buy_filled = buy_status['filled_size']
                pair.sell_filled = sell_status['filled_size']
                
                # Check if both orders are filled (cycle complete)
                if buy_status['status'] == 'filled' and sell_status['status'] == 'filled':
                    await self.complete_market_maker_cycle(symbol, pair)
                
                # Check if one order filled and other needs adjustment
                elif buy_status['status'] == 'filled' and sell_status['status'] == 'open':
                    await self.handle_partial_fill(symbol, pair, 'buy_filled')
                elif sell_status['status'] == 'filled' and buy_status['status'] == 'open':
                    await self.handle_partial_fill(symbol, pair, 'sell_filled')
                
                # Check if orders are stale (cancel and replace)
                elif buy_status['status'] == 'open' and sell_status['status'] == 'open':
                    await self.check_and_replace_stale_orders(symbol, pair)
                
            except Exception as e:
                logger.error(f"❌ Error managing {symbol} pair: {e}")
    
    async def complete_market_maker_cycle(self, symbol: str, pair: OrderPair):
        """Complete a successful market maker cycle"""
        # Calculate actual profit
        actual_profit = (pair.sell_price - pair.buy_price) * min(pair.buy_filled, pair.sell_filled)
        
        # Update metrics
        self.metrics.total_cycles += 1
        self.metrics.successful_cycles += 1
        self.metrics.total_spread_profit += actual_profit
        self.metrics.total_volume += pair.buy_filled + pair.sell_filled
        
        # Update daily PnL
        self.daily_pnl += actual_profit
        
        # Update exposure
        self.total_exposure -= pair.size * 2
        
        # Remove from active pairs
        del self.active_pairs[symbol]
        
        logger.info(f"✅ MARKET MAKER CYCLE COMPLETED: {symbol}")
        logger.info(f"   Profit: ${actual_profit:.4f}")
        logger.info(f"   Volume: {pair.buy_filled + pair.sell_filled:.1f}")
        logger.info(f"   Total Cycles: {self.metrics.total_cycles}")
        logger.info(f"   Success Rate: {self.metrics.successful_cycles/self.metrics.total_cycles:.1%}")
        logger.info(f"   Total Profit: ${self.metrics.total_spread_profit:.4f}")
    
    async def handle_partial_fill(self, symbol: str, pair: OrderPair, filled_side: str):
        """Handle partial fills - place counter order"""
        logger.info(f"⚠️ PARTIAL FILL: {symbol} - {filled_side}")
        
        if filled_side == 'buy_filled':
            # Buy order filled, need to sell at current best ask
            order_book = await self.get_order_book(symbol)
            if order_book:
                new_sell_order_id = await self.place_sell_order(symbol, order_book['best_ask'], pair.buy_filled)
                if new_sell_order_id:
                    pair.sell_order_id = new_sell_order_id
                    pair.status = "partial"
        
        elif filled_side == 'sell_filled':
            # Sell order filled, need to buy at current best bid
            order_book = await self.get_order_book(symbol)
            if order_book:
                new_buy_order_id = await self.place_buy_order(symbol, order_book['best_bid'], pair.sell_filled)
                if new_buy_order_id:
                    pair.buy_order_id = new_buy_order_id
                    pair.status = "partial"
    
    async def check_and_replace_stale_orders(self, symbol: str, pair: OrderPair):
        """Check and replace stale orders with current best prices"""
        # Check if orders are stale (older than 30 seconds)
        order_time = datetime.fromisoformat(pair.timestamp)
        if (datetime.now() - order_time).total_seconds() < 30:
            return
        
        # Get current order book
        order_book = await self.get_order_book(symbol)
        if not order_book:
            return
        
        # Check if prices moved significantly
        current_bid = order_book['best_bid']
        current_ask = order_book['best_ask']
        
        bid_moved = abs(current_bid - pair.buy_price) / pair.buy_price > 0.001  # 0.1%
        ask_moved = abs(current_ask - pair.sell_price) / pair.sell_price > 0.001
        
        if bid_moved or ask_moved:
            logger.info(f"🔄 REPLACING STALE ORDERS: {symbol}")
            
            # Cancel old orders
            await self.cancel_order(symbol, pair.buy_order_id)
            await self.cancel_order(symbol, pair.sell_order_id)
            
            # Place new orders at current prices
            await self.create_market_maker_pair(symbol, order_book)
    
    async def market_making_loop(self):
        """Main market making loop"""
        logger.info("🏪 MARKET MAKING LOOP STARTED")
        logger.info(f"🎯 Strategy: Buy Best Bid, Sell Best Ask")
        logger.info(f"📊 Monitoring {len(self.symbols)} symbols")
        
        while True:
            try:
                # Check daily loss limit
                if self.daily_pnl < -self.daily_loss_limit:
                    logger.critical(f"🚨 DAILY LOSS LIMIT REACHED: ${self.daily_pnl:.2f}")
                    await self.emergency_shutdown()
                    break
                
                # Scan all symbols for opportunities
                for symbol in self.symbols:
                    try:
                        # Skip if already have active pair
                        if symbol in self.active_pairs:
                            continue
                        
                        # Get order book
                        order_book = await self.get_order_book(symbol)
                        if order_book:
                            # Create market maker pair if conditions are good
                            await self.create_market_maker_pair(symbol, order_book)
                        
                        # Small delay to avoid API limits
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing {symbol}: {e}")
                        continue
                
                # Manage active pairs
                await self.manage_active_pairs()
                
                # Update metrics
                self.update_metrics()
                
                # Log status
                logger.info(f"📊 Status: Active Pairs: {len(self.active_pairs)} | "
                           f"Exposure: ${self.total_exposure:.1f} | "
                           f"Profit: ${self.metrics.total_spread_profit:+.4f} | "
                           f"Success Rate: {self.metrics.successful_cycles/max(1,self.metrics.total_cycles):.1%}")
                
                await asyncio.sleep(2)  # Scan every 2 seconds
                
            except Exception as e:
                logger.error(f"❌ Market making loop error: {e}")
                await asyncio.sleep(5)
    
    def update_metrics(self):
        """Update performance metrics"""
        if self.metrics.total_cycles > 0:
            self.metrics.successful_cycles = len([p for p in self.active_pairs.values() if p.status == 'completed'])
        
        # Calculate profit per hour
        start_time = datetime.fromisoformat(self.metrics.start_time)
        hours_running = (datetime.now() - start_time).total_seconds() / 3600
        if hours_running > 0:
            self.metrics.profit_per_hour = self.metrics.total_spread_profit / hours_running
        
        # Update active pairs count
        self.metrics.active_pairs = len(self.active_pairs)
    
    async def emergency_shutdown(self):
        """Emergency shutdown - cancel all orders"""
        logger.critical("🚨 EMERGENCY SHUTDOWN - CANCELLING ALL ORDERS")
        
        for symbol, pair in self.active_pairs.items():
            if pair.buy_order_id:
                await self.cancel_order(symbol, pair.buy_order_id)
            if pair.sell_order_id:
                await self.cancel_order(symbol, pair.sell_order_id)
        
        self.active_pairs.clear()
        self.total_exposure = 0.0
        
        logger.critical("🚨 EMERGENCY SHUTDOWN COMPLETE")
    
    def get_performance_report(self) -> Dict:
        """Get performance report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_cycles': self.metrics.total_cycles,
            'successful_cycles': self.metrics.successful_cycles,
            'success_rate': self.metrics.successful_cycles / max(1, self.metrics.total_cycles),
            'total_spread_profit': self.metrics.total_spread_profit,
            'total_volume': self.metrics.total_volume,
            'avg_spread_bps': self.metrics.avg_spread_bps,
            'profit_per_hour': self.metrics.profit_per_hour,
            'active_pairs': len(self.active_pairs),
            'total_exposure': self.total_exposure,
            'daily_pnl': self.daily_pnl,
            'start_time': self.metrics.start_time
        }

async def main():
    """Main market maker"""
    print("🏪 BEST BID/ASK MARKET MAKER")
    print("="*60)
    print("💚 BUY at BEST BID")
    print("❤️ SELL at BEST ASK")
    print("💰 Capture SPREAD PROFIT")
    print("🔄 CONTINUOUS MARKET MAKING")
    print("="*60)
    
    # Initialize market maker
    market_maker = BestBidAskMarketMaker()
    
    try:
        # Start market making
        await market_maker.market_making_loop()
        
    except KeyboardInterrupt:
        print("\n🏪 Market maker stopped by user")
        
        # Final performance report
        report = market_maker.get_performance_report()
        print("\n" + "="*60)
        print("📊 PERFORMANCE REPORT")
        print("="*60)
        print(f"🔄 Total Cycles: {report['total_cycles']}")
        print(f"✅ Successful Cycles: {report['successful_cycles']}")
        print(f"🎯 Success Rate: {report['success_rate']:.1%}")
        print(f"💰 Total Spread Profit: ${report['total_spread_profit']:+.4f}")
        print(f"📊 Total Volume: {report['total_volume']:.1f}")
        print(f"⚡ Profit per Hour: ${report['profit_per_hour']:.2f}")
        print(f"💵 Total Exposure: ${report['total_exposure']:.1f}")
        print(f"📈 Daily P&L: ${report['daily_pnl']:+.4f}")
        print("="*60)
        
        # Emergency shutdown
        await market_maker.emergency_shutdown()
        
    except Exception as e:
        print(f"\n❌ Market maker error: {e}")
        await market_maker.emergency_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
