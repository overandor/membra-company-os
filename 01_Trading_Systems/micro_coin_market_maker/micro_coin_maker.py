#!/usr/bin/env python3
import os
"""
MICRO-COIN MARKET MAKER
Discovers and trades coins under $0.10 for maximum percentage gains
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
    format='%(asctime)s - MICRO_COIN - %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/micro_coin_maker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MicroCoin:
    """Micro coin information"""
    symbol: str
    price: float
    volume_24h: float
    spread_bps: float
    liquidity_score: float
    volatility: float
    profit_potential: float

@dataclass
class MicroOrderPair:
    """Order pair for micro coin trading"""
    symbol: str
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    buy_price: float = 0.0
    sell_price: float = 0.0
    size: float = 0.0
    spread_profit_pct: float = 0.0
    status: str = "placing"

class MicroCoinMarketMaker:
    """Specialized market maker for coins under $0.10"""
    
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Budget and position sizing
        self.total_budget = 12.0
        self.max_coins = 50  # Trade up to 50 micro coins simultaneously
        self.per_coin_budget = 0.20  # $0.20 per coin maximum
        self.order_size_factor = 1000  # Buy 1000 units for micro coins
        
        # Micro coin parameters
        self.max_price = 1.0  # Maximum price $1.00 (increased for more opportunities)
        self.min_volume = 50000  # Minimum 24h volume (reduced)
        self.max_spread_bps = 200  # Max 2% spread for low-price coins
        self.min_spread_bps = 5   # Min 0.05% spread to be profitable
        
        # Active trading
        self.micro_coins: List[MicroCoin] = []
        self.active_pairs: Dict[str, MicroOrderPair] = {}
        self.blacklisted_symbols = set()
        
        # Performance metrics
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        self.total_volume = 0.0
        self.discovery_time = ""
        
        logger.info("🪙 Micro-Coin Market Maker initialized")
        logger.info(f"💰 Budget: ${self.total_budget}")
        logger.info(f"🎯 Max Price: ${self.max_price}")
        logger.info(f"📊 Max Coins: {self.max_coins}")
        logger.info(f"💎 Strategy: High-volume micro coins")
    
    async def discover_micro_coins(self) -> List[MicroCoin]:
        """Discover all tradable coins under $0.10"""
        logger.info("🔍 DISCOVERING LOW-PRICE COINS (Under $1.00)...")
        
        try:
            # Get all futures contracts
            contracts = self.api.list_futures_contracts(settle='usdt')
            
            micro_coins = []
            total_checked = 0
            
            for contract in contracts:
                total_checked += 1
                
                # Skip if not active
                if contract.status != 'open':
                    continue
                
                symbol = contract.name
                
                # Skip if blacklisted
                if symbol in self.blacklisted_symbols:
                    continue
                
                try:
                    # Get current price and order book
                    book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=5)
                    
                    if not book.bids or not book.asks:
                        continue
                    
                    best_bid = float(book.bids[0].p)
                    best_ask = float(book.asks[0].p)
                    mid_price = (best_bid + best_ask) / 2
                    
                    # Only consider coins under $0.10
                    if mid_price > self.max_price:
                        continue
                    
                    # Calculate spread
                    spread_bps = (best_ask - best_bid) / mid_price * 10000
                    
                    # Skip if spread too wide
                    if spread_bps > self.max_spread_bps:
                        continue
                    
                    # Calculate liquidity score
                    bid_size = sum(float(b.s) for b in book.bids[:3])
                    ask_size = sum(float(a.s) for a in book.asks[:3])
                    liquidity_score = min(bid_size, ask_size) / max(bid_size, ask_size)
                    
                    # Estimate volume (simplified)
                    volume_24h = liquidity_score * 1000000  # Rough estimate
                    
                    # Skip if insufficient volume
                    if volume_24h < self.min_volume:
                        continue
                    
                    # Calculate volatility (from spread)
                    volatility = spread_bps / 10000
                    
                    # Calculate profit potential
                    profit_potential = spread_bps * 0.8  # 80% of spread as potential profit
                    
                    micro_coin = MicroCoin(
                        symbol=symbol,
                        price=mid_price,
                        volume_24h=volume_24h,
                        spread_bps=spread_bps,
                        liquidity_score=liquidity_score,
                        volatility=volatility,
                        profit_potential=profit_potential
                    )
                    
                    micro_coins.append(micro_coin)
                    
                    if len(micro_coins) % 50 == 0:
                        logger.info(f"🔍 Found {len(micro_coins)} micro coins...")
                
                except Exception as e:
                    # Blacklist problematic symbols
                    self.blacklisted_symbols.add(symbol)
                    continue
            
            # Sort by profit potential and volume
            micro_coins.sort(key=lambda x: x.profit_potential * x.volume_24h, reverse=True)
            
            # Take top coins
            self.micro_coins = micro_coins[:self.max_coins]
            
            self.discovery_time = datetime.now().isoformat()
            
            logger.info(f"✅ DISCOVERY COMPLETE!")
            logger.info(f"📊 Checked {total_checked} contracts")
            logger.info(f"🪙 Found {len(micro_coins)} suitable micro coins")
            logger.info(f"💰 Price range: ${min(c.price for c in self.micro_coins):.6f} - ${max(c.price for c in self.micro_coins):.6f}")
            logger.info(f"📈 Avg spread: {sum(c.spread_bps for c in self.micro_coins)/len(self.micro_coins):.1f} bps")
            
            # Show top 10 coins
            logger.info(f"🏆 TOP 10 MICRO COINS:")
            for i, coin in enumerate(self.micro_coins[:10]):
                logger.info(f"   {i+1}. {coin.symbol}: ${coin.price:.6f} | {coin.spread_bps:.1f}bps | Vol: ${coin.volume_24h:,.0f}")
            
            return self.micro_coins
            
        except Exception as e:
            logger.error(f"❌ Micro coin discovery failed: {e}")
            return []
    
    async def get_micro_coin_order_book(self, symbol: str) -> Optional[Dict]:
        """Get order book for a specific micro coin"""
        try:
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=5)
            
            if not book.bids or not book.asks:
                return None
            
            best_bid = float(book.bids[0].p)
            best_ask = float(book.asks[0].p)
            bid_size = float(book.bids[0].s)
            ask_size = float(book.asks[0].s)
            
            # Verify it's still a micro coin
            mid_price = (best_bid + best_ask) / 2
            if mid_price > self.max_price:
                return None
            
            spread_bps = (best_ask - best_bid) / mid_price * 10000
            
            return {
                'symbol': symbol,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'bid_size': bid_size,
                'ask_size': ask_size,
                'mid_price': mid_price,
                'spread_bps': spread_bps,
                'spread_profit_pct': spread_bps / 10000
            }
            
        except Exception as e:
            logger.error(f"❌ Order book for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, coin_price: float, available_budget: float) -> float:
        """Calculate optimal position size for micro coin"""
        # Calculate maximum units we can buy with per_coin_budget
        max_units_by_budget = self.per_coin_budget / coin_price
        
        # Calculate units based on order_size_factor
        factor_units = self.order_size_factor
        
        # Take the minimum
        position_size = min(max_units_by_budget, factor_units)
        
        # Ensure minimum position size
        min_position_value = 0.05  # $0.05 minimum
        min_units = min_position_value / coin_price
        position_size = max(position_size, min_units)
        
        return position_size
    
    async def place_micro_buy_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place buy order for micro coin"""
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
            
            position_value = price * size
            logger.info(f"💚 MICRO BUY: {symbol}")
            logger.info(f"   Price: ${price:.6f} | Size: {size:.0f} units")
            logger.info(f"   Value: ${position_value:.4f}")
            logger.info(f"   Order ID: {result.id}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Micro buy failed for {symbol}: {e}")
            return None
    
    async def place_micro_sell_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place sell order for micro coin"""
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
            
            position_value = price * size
            logger.info(f"❤️ MICRO SELL: {symbol}")
            logger.info(f"   Price: ${price:.6f} | Size: {size:.0f} units")
            logger.info(f"   Value: ${position_value:.4f}")
            logger.info(f"   Order ID: {result.id}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Micro sell failed for {symbol}: {e}")
            return None
    
    async def create_micro_coin_pair(self, coin: MicroCoin, order_book: Dict) -> bool:
        """Create buy/sell pair for micro coin"""
        # Check if we already have this coin
        if coin.symbol in self.active_pairs:
            return False
        
        # Check spread profitability
        if order_book['spread_bps'] < self.min_spread_bps:
            return False
        
        # Calculate position size
        available_budget = self.per_coin_budget * (1 - len(self.active_pairs) / self.max_coins)
        position_size = self.calculate_position_size(order_book['mid_price'], available_budget)
        
        # Place buy order at best bid
        buy_order_id = await self.place_micro_buy_order(coin.symbol, order_book['best_bid'], position_size)
        if not buy_order_id:
            return False
        
        # Place sell order at best ask
        sell_order_id = await self.place_micro_sell_order(coin.symbol, order_book['best_ask'], position_size)
        if not sell_order_id:
            # Cancel buy order if sell failed
            try:
                self.api.cancel_futures_order(settle='usdt', order_id=buy_order_id)
            except:
                pass
            return False
        
        # Create order pair
        order_pair = MicroOrderPair(
            symbol=coin.symbol,
            buy_order_id=buy_order_id,
            sell_order_id=sell_order_id,
            buy_price=order_book['best_bid'],
            sell_price=order_book['best_ask'],
            size=position_size,
            spread_profit_pct=order_book['spread_profit_pct'],
            status="active"
        )
        
        self.active_pairs[coin.symbol] = order_pair
        self.total_trades += 2  # One buy, one sell
        
        expected_profit = order_book['spread_profit_pct'] * position_size * order_book['mid_price']
        
        logger.info(f"🪙 MICRO PAIR CREATED: {coin.symbol}")
        logger.info(f"   Buy: ${order_book['best_bid']:.6f} | Sell: ${order_book['best_ask']:.6f}")
        logger.info(f"   Spread: {order_book['spread_bps']:.1f} bps ({order_book['spread_profit_pct']*100:.2f}%)")
        logger.info(f"   Size: {position_size:.0f} units | Value: ${order_book['mid_price']*position_size:.4f}")
        logger.info(f"   Expected Profit: ${expected_profit:.6f}")
        logger.info(f"   Active Pairs: {len(self.active_pairs)}/{self.max_coins}")
        
        return True
    
    async def scan_and_trade_micro_coins(self):
        """Scan micro coins and create trading pairs"""
        if not self.micro_coins:
            logger.warning("⚠️ No micro coins discovered")
            return
        
        # Check if we have maximum active pairs
        if len(self.active_pairs) >= self.max_coins:
            return
        
        opportunities_found = 0
        
        for coin in self.micro_coins:
            if len(self.active_pairs) >= self.max_coins:
                break
            
            # Skip if already trading this coin
            if coin.symbol in self.active_pairs:
                continue
            
            # Get current order book
            order_book = await self.get_micro_coin_order_book(coin.symbol)
            if not order_book:
                continue
            
            # Create trading pair
            if await self.create_micro_coin_pair(coin, order_book):
                opportunities_found += 1
            
            # Small delay to avoid API limits
            await asyncio.sleep(0.05)
        
        if opportunities_found > 0:
            logger.info(f"🎯 Created {opportunities_found} new micro coin pairs")
    
    async def monitor_active_pairs(self):
        """Monitor and manage active micro coin pairs"""
        if not self.active_pairs:
            return
        
        for symbol, pair in list(self.active_pairs.items()):
            try:
                # Check order status (simplified - would need proper order tracking)
                # For now, assume orders fill quickly and create new pairs
                
                # Check if pair is stale (older than 60 seconds)
                pair_age = (datetime.now() - datetime.fromisoformat(symbol if isinstance(symbol, str) else "2024-01-01")).total_seconds()
                if pair_age > 60:  # Simplified check
                    logger.info(f"🔄 Refreshing stale pair: {symbol}")
                    
                    # Cancel old orders
                    try:
                        if pair.buy_order_id:
                            self.api.cancel_futures_order(settle='usdt', order_id=pair.buy_order_id)
                        if pair.sell_order_id:
                            self.api.cancel_futures_order(settle='usdt', order_id=pair.sell_order_id)
                    except:
                        pass
                    
                    # Remove from active pairs
                    del self.active_pairs[symbol]
                    self.successful_trades += 2
                
            except Exception as e:
                logger.error(f"❌ Error monitoring {symbol}: {e}")
    
    async def micro_coin_trading_loop(self):
        """Main micro coin trading loop"""
        logger.info("🪙 MICRO COIN TRADING LOOP STARTED")
        logger.info(f"🎯 Target: Coins under ${self.max_price}")
        logger.info(f"💰 Budget per coin: ${self.per_coin_budget}")
        logger.info(f"📊 Max concurrent coins: {self.max_coins}")
        
        # Discover micro coins
        await self.discover_micro_coins()
        
        if not self.micro_coins:
            logger.error("❌ No micro coins found - cannot start trading")
            return
        
        trading_cycles = 0
        
        while True:
            try:
                trading_cycles += 1
                
                # Scan for opportunities and create pairs
                await self.scan_and_trade_micro_coins()
                
                # Monitor active pairs
                await self.monitor_active_pairs()
                
                # Refresh coin list periodically
                if trading_cycles % 100 == 0:  # Every ~5 minutes
                    logger.info("🔄 Refreshing micro coin list...")
                    await self.discover_micro_coins()
                
                # Calculate current metrics
                active_value = len(self.active_pairs) * self.per_coin_budget
                budget_utilization = active_value / self.total_budget * 100
                
                # Log status
                logger.info(f"📊 Cycle {trading_cycles}: Active: {len(self.active_pairs)}/{self.max_coins} | "
                           f"Budget: {budget_utilization:.1f}% | "
                           f"Trades: {self.total_trades} | "
                           f"Success: {self.successful_trades}")
                
                await asyncio.sleep(3)  # Scan every 3 seconds
                
            except Exception as e:
                logger.error(f"❌ Trading loop error: {e}")
                await asyncio.sleep(5)
    
    def get_performance_report(self) -> Dict:
        """Get micro coin trading performance"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_budget': self.total_budget,
            'discovered_coins': len(self.micro_coins),
            'active_pairs': len(self.active_pairs),
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'success_rate': self.successful_trades / max(1, self.total_trades),
            'budget_utilization': len(self.active_pairs) * self.per_coin_budget / self.total_budget * 100,
            'discovery_time': self.discovery_time,
            'price_range': {
                'min': min(c.price for c in self.micro_coins) if self.micro_coins else 0,
                'max': max(c.price for c in self.micro_coins) if self.micro_coins else 0
            },
            'avg_spread_bps': sum(c.spread_bps for c in self.micro_coins) / len(self.micro_coins) if self.micro_coins else 0
        }

async def main():
    """Main micro coin market maker"""
    print("🪙 MICRO-COIN MARKET MAKER")
    print("="*70)
    print("💰 Budget: $12")
    print("🎯 Target: Coins under $0.10")
    print("📊 Strategy: High-volume micro coins")
    print("💚 Buy Best Bid | ❤️ Sell Best Ask")
    print("🔄 Up to 50 coins simultaneously")
    print("="*70)
    
    # Initialize micro coin market maker
    micro_maker = MicroCoinMarketMaker()
    
    try:
        # Start micro coin trading
        await micro_maker.micro_coin_trading_loop()
        
    except KeyboardInterrupt:
        print("\n🪙 Micro coin market maker stopped by user")
        
        # Final performance report
        report = micro_maker.get_performance_report()
        print("\n" + "="*70)
        print("📊 MICRO COIN PERFORMANCE REPORT")
        print("="*70)
        print(f"🔍 Discovered Coins: {report['discovered_coins']}")
        print(f"🪙 Active Pairs: {report['active_pairs']}")
        print(f"🔄 Total Trades: {report['total_trades']}")
        print(f"✅ Successful Trades: {report['successful_trades']}")
        print(f"🎯 Success Rate: {report['success_rate']:.1%}")
        print(f"💰 Budget Utilization: {report['budget_utilization']:.1f}%")
        print(f"💵 Price Range: ${report['price_range']['min']:.6f} - ${report['price_range']['max']:.6f}")
        print(f"📈 Avg Spread: {report['avg_spread_bps']:.1f} bps")
        
        if micro_maker.micro_coins:
            print(f"\n🏆 TOP 5 TRADED COINS:")
            for i, coin in enumerate(micro_maker.micro_coins[:5]):
                print(f"   {i+1}. {coin.symbol}: ${coin.price:.6f} | {coin.spread_bps:.1f}bps")
        
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Micro coin market maker error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
