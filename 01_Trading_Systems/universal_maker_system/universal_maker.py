#!/usr/bin/env python3
import os
"""
UNIVERSAL MARKET MAKER
Adapts strategy to any coin price - perfect for $12 budget
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
    format='%(asctime)s - UNIVERSAL - %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/universal_maker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradableCoin:
    """Universal coin information"""
    symbol: str
    price: float
    volume_24h: float
    spread_bps: float
    liquidity_score: float
    category: str  # micro, low, mid, high
    recommended_size: float
    profit_potential: float

@dataclass
class UniversalOrderPair:
    """Universal order pair"""
    symbol: str
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    buy_price: float = 0.0
    sell_price: float = 0.0
    size: float = 0.0
    spread_profit: float = 0.0
    category: str = ""
    status: str = "placing"

class UniversalMarketMaker:
    """Universal market maker for all coin price ranges"""
    
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Universal budget management
        self.total_budget = 12.0
        self.max_positions = 20  # Trade up to 20 coins
        self.reserve_ratio = 0.2  # Keep 20% as reserve
        
        # Price categories and strategies
        self.price_categories = {
            'micro': {'max_price': 0.1, 'budget_per_coin': 0.10, 'size_factor': 2000},
            'low': {'max_price': 1.0, 'budget_per_coin': 0.15, 'size_factor': 500},
            'mid': {'max_price': 10.0, 'budget_per_coin': 0.25, 'size_factor': 50},
            'high': {'max_price': 1000.0, 'budget_per_coin': 0.30, 'size_factor': 5}
        }
        
        # Universal parameters
        self.min_volume = 10000
        self.max_spread_bps = 300  # More flexible for all coins
        self.min_spread_bps = 3    # Lower minimum for more opportunities
        
        # Active trading
        self.tradable_coins: List[TradableCoin] = []
        self.active_pairs: Dict[str, UniversalOrderPair] = {}
        self.blacklisted_symbols = set()
        
        # Performance metrics
        self.total_cycles = 0
        self.successful_cycles = 0
        self.total_profit = 0.0
        self.category_performance: Dict[str, float] = {}
        
        logger.info("🌍 Universal Market Maker initialized")
        logger.info(f"💰 Total Budget: ${self.total_budget}")
        logger.info(f"📊 Max Positions: {self.max_positions}")
        logger.info(f"🎯 Strategy: Adapts to any price range")
    
    def categorize_coin(self, price: float) -> str:
        """Categorize coin by price"""
        if price <= 0.1:
            return 'micro'
        elif price <= 1.0:
            return 'low'
        elif price <= 10.0:
            return 'mid'
        else:
            return 'high'
    
    def calculate_position_size(self, symbol: str, price: float, category: str) -> float:
        """Calculate optimal position size based on category"""
        config = self.price_categories[category]
        budget_per_coin = config['budget_per_coin']
        size_factor = config['size_factor']
        
        # Adjust based on available budget
        used_budget = len(self.active_pairs) * budget_per_coin
        available_budget = self.total_budget * (1 - self.reserve_ratio) - used_budget
        
        if available_budget < budget_per_coin * 0.5:
            return 0  # Not enough budget
        
        # Calculate size
        size_by_budget = budget_per_coin / price
        size_by_factor = size_factor
        
        # Take minimum but ensure minimum viability
        size = min(size_by_budget, size_by_factor)
        min_value = 0.05  # $0.05 minimum trade value
        min_size = min_value / price
        
        return max(size, min_size)
    
    async def discover_tradable_coins(self) -> List[TradableCoin]:
        """Discover all tradable coins with universal strategy"""
        logger.info("🌍 DISCOVERING UNIVERSAL TRADABLE COINS...")
        
        try:
            contracts = self.api.list_futures_contracts(settle='usdt')
            
            tradable_coins = []
            total_checked = 0
            
            for contract in contracts:
                total_checked += 1
                
                if contract.status != 'open':
                    continue
                
                symbol = contract.name
                
                if symbol in self.blacklisted_symbols:
                    continue
                
                try:
                    # Get order book
                    book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=5)
                    
                    if not book.bids or not book.asks:
                        continue
                    
                    best_bid = float(book.bids[0].p)
                    best_ask = float(book.asks[0].p)
                    mid_price = (best_bid + best_ask) / 2
                    
                    # Calculate spread
                    spread_bps = (best_ask - best_bid) / mid_price * 10000
                    
                    # Skip if spread too wide
                    if spread_bps > self.max_spread_bps:
                        continue
                    
                    # Calculate liquidity
                    bid_size = sum(float(b.s) for b in book.bids[:3])
                    ask_size = sum(float(a.s) for a in book.asks[:3])
                    liquidity_score = min(bid_size, ask_size) / max(bid_size, ask_size)
                    
                    # Estimate volume
                    volume_24h = liquidity_score * 500000  # Conservative estimate
                    
                    # Skip if insufficient volume
                    if volume_24h < self.min_volume:
                        continue
                    
                    # Categorize coin
                    category = self.categorize_coin(mid_price)
                    
                    # Calculate recommended position size
                    recommended_size = self.calculate_position_size(symbol, mid_price, category)
                    
                    if recommended_size == 0:
                        continue
                    
                    # Calculate profit potential
                    profit_potential = spread_bps * 0.7  # Conservative estimate
                    
                    tradable_coin = TradableCoin(
                        symbol=symbol,
                        price=mid_price,
                        volume_24h=volume_24h,
                        spread_bps=spread_bps,
                        liquidity_score=liquidity_score,
                        category=category,
                        recommended_size=recommended_size,
                        profit_potential=profit_potential
                    )
                    
                    tradable_coins.append(tradable_coin)
                    
                    if len(tradable_coins) % 25 == 0:
                        logger.info(f"🔍 Found {len(tradable_coins)} tradable coins...")
                
                except Exception as e:
                    self.blacklisted_symbols.add(symbol)
                    continue
            
            # Sort by profit potential
            tradable_coins.sort(key=lambda x: x.profit_potential, reverse=True)
            
            # Take top coins
            self.tradable_coins = tradable_coins[:self.max_positions * 2]  # Get more than needed
            
            logger.info(f"✅ DISCOVERY COMPLETE!")
            logger.info(f"📊 Checked {total_checked} contracts")
            logger.info(f"🌍 Found {len(self.tradable_coins)} tradable coins")
            
            # Show category breakdown
            category_counts = {}
            for coin in self.tradable_coins:
                category_counts[coin.category] = category_counts.get(coin.category, 0) + 1
            
            logger.info(f"📈 Category Breakdown:")
            for category, count in category_counts.items():
                price_range = self.price_categories[category]['max_price']
                logger.info(f"   {category.title()} (<${price_range}): {count} coins")
            
            # Show top 10 coins
            logger.info(f"🏆 TOP 10 COINS:")
            for i, coin in enumerate(self.tradable_coins[:10]):
                logger.info(f"   {i+1}. {coin.symbol}: ${coin.price:.6f} ({coin.category}) | {coin.spread_bps:.1f}bps")
            
            return self.tradable_coins
            
        except Exception as e:
            logger.error(f"❌ Coin discovery failed: {e}")
            return []
    
    async def get_order_book(self, symbol: str) -> Optional[Dict]:
        """Get current order book"""
        try:
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=5)
            
            if not book.bids or not book.asks:
                return None
            
            best_bid = float(book.bids[0].p)
            best_ask = float(book.asks[0].p)
            mid_price = (best_bid + best_ask) / 2
            spread_bps = (best_ask - best_bid) / mid_price * 10000
            
            return {
                'symbol': symbol,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': mid_price,
                'spread_bps': spread_bps,
                'spread_profit': (best_ask - best_bid)
            }
            
        except Exception as e:
            return None
    
    async def place_buy_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place universal buy order"""
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
            logger.info(f"💚 BUY: {symbol}")
            logger.info(f"   Price: ${price:.6f} | Size: {size:.1f}")
            logger.info(f"   Value: ${position_value:.4f}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Buy failed for {symbol}: {e}")
            return None
    
    async def place_sell_order(self, symbol: str, price: float, size: float) -> Optional[str]:
        """Place universal sell order"""
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
            logger.info(f"❤️ SELL: {symbol}")
            logger.info(f"   Price: ${price:.6f} | Size: {size:.1f}")
            logger.info(f"   Value: ${position_value:.4f}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Sell failed for {symbol}: {e}")
            return None
    
    async def create_universal_pair(self, coin: TradableCoin, order_book: Dict) -> bool:
        """Create trading pair for any coin"""
        if coin.symbol in self.active_pairs:
            return False
        
        if order_book['spread_bps'] < self.min_spread_bps:
            return False
        
        # Calculate current position size
        current_size = self.calculate_position_size(coin.symbol, order_book['mid_price'], coin.category)
        
        if current_size == 0:
            return False
        
        # Place orders
        buy_order_id = await self.place_buy_order(coin.symbol, order_book['best_bid'], current_size)
        if not buy_order_id:
            return False
        
        sell_order_id = await self.place_sell_order(coin.symbol, order_book['best_ask'], current_size)
        if not sell_order_id:
            try:
                self.api.cancel_futures_order(settle='usdt', order_id=buy_order_id)
            except:
                pass
            return False
        
        # Create order pair
        order_pair = UniversalOrderPair(
            symbol=coin.symbol,
            buy_order_id=buy_order_id,
            sell_order_id=sell_order_id,
            buy_price=order_book['best_bid'],
            sell_price=order_book['best_ask'],
            size=current_size,
            spread_profit=order_book['spread_profit'] * current_size,
            category=coin.category,
            status="active"
        )
        
        self.active_pairs[coin.symbol] = order_pair
        self.total_cycles += 1
        
        logger.info(f"🌍 UNIVERSAL PAIR: {coin.symbol} ({coin.category})")
        logger.info(f"   Buy: ${order_book['best_bid']:.6f} | Sell: ${order_book['best_ask']:.6f}")
        logger.info(f"   Spread: {order_book['spread_bps']:.1f} bps")
        logger.info(f"   Size: {current_size:.1f} | Value: ${order_book['mid_price']*current_size:.4f}")
        logger.info(f"   Expected Profit: ${order_pair.spread_profit:.6f}")
        logger.info(f"   Active: {len(self.active_pairs)}/{self.max_positions}")
        
        return True
    
    async def universal_trading_loop(self):
        """Main universal trading loop"""
        logger.info("🌍 UNIVERSAL TRADING LOOP STARTED")
        logger.info(f"💰 Budget: ${self.total_budget} (Reserve: {self.reserve_ratio*100:.0f}%)")
        logger.info(f"📊 Max Positions: {self.max_positions}")
        logger.info(f"🎯 Strategy: Adapts to any coin price")
        
        # Discover tradable coins
        await self.discover_tradable_coins()
        
        if not self.tradable_coins:
            logger.error("❌ No tradable coins found")
            return
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                
                # Create new pairs if we have capacity
                if len(self.active_pairs) < self.max_positions:
                    opportunities_created = 0
                    
                    for coin in self.tradable_coins:
                        if len(self.active_pairs) >= self.max_positions:
                            break
                        
                        if coin.symbol in self.active_pairs:
                            continue
                        
                        # Get current order book
                        order_book = await self.get_order_book(coin.symbol)
                        if order_book:
                            if await self.create_universal_pair(coin, order_book):
                                opportunities_created += 1
                        
                        await asyncio.sleep(0.05)  # Small delay
                    
                    if opportunities_created > 0:
                        logger.info(f"🎯 Created {opportunities_created} new pairs")
                
                # Monitor and refresh pairs (simplified)
                if cycle_count % 20 == 0:  # Every minute
                    logger.info("🔄 Refreshing market opportunities...")
                    await self.discover_tradable_coins()
                
                # Calculate budget utilization
                used_budget = sum(pair.spread_profit * 50 for pair in self.active_pairs.values())  # Rough estimate
                budget_utilization = used_budget / self.total_budget * 100
                
                # Log status
                logger.info(f"📊 Cycle {cycle_count}: Active: {len(self.active_pairs)}/{self.max_positions} | "
                           f"Budget: {budget_utilization:.1f}% | "
                           f"Total Cycles: {self.total_cycles}")
                
                await asyncio.sleep(3)  # Scan every 3 seconds
                
            except Exception as e:
                logger.error(f"❌ Trading loop error: {e}")
                await asyncio.sleep(5)
    
    def get_performance_report(self) -> Dict:
        """Get universal performance report"""
        category_stats = {}
        for coin in self.tradable_coins:
            if coin.category not in category_stats:
                category_stats[coin.category] = {'count': 0, 'avg_price': 0, 'avg_spread': 0}
            category_stats[coin.category]['count'] += 1
            category_stats[coin.category]['avg_price'] += coin.price
            category_stats[coin.category]['avg_spread'] += coin.spread_bps
        
        for category in category_stats:
            count = category_stats[category]['count']
            category_stats[category]['avg_price'] /= count
            category_stats[category]['avg_spread'] /= count
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_budget': self.total_budget,
            'tradable_coins': len(self.tradable_coins),
            'active_pairs': len(self.active_pairs),
            'total_cycles': self.total_cycles,
            'category_breakdown': category_stats,
            'price_categories': self.price_categories
        }

async def main():
    """Main universal market maker"""
    print("🌍 UNIVERSAL MARKET MAKER")
    print("="*70)
    print("💰 Budget: $12")
    print("🎯 Strategy: Adapts to ANY coin price")
    print("💚 Buy Best Bid | ❤️ Sell Best Ask")
    print("📊 Micro (<$0.1) | Low (<$1) | Mid (<$10) | High ($10+)")
    print("🔄 Up to 20 positions simultaneously")
    print("="*70)
    
    # Initialize universal market maker
    universal_maker = UniversalMarketMaker()
    
    try:
        # Start universal trading
        await universal_maker.universal_trading_loop()
        
    except KeyboardInterrupt:
        print("\n🌍 Universal market maker stopped by user")
        
        # Final performance report
        report = universal_maker.get_performance_report()
        print("\n" + "="*70)
        print("📊 UNIVERSAL PERFORMANCE REPORT")
        print("="*70)
        print(f"🌍 Tradable Coins: {report['tradable_coins']}")
        print(f"🔄 Active Pairs: {report['active_pairs']}")
        print(f"💰 Total Cycles: {report['total_cycles']}")
        
        print(f"\n📈 Category Performance:")
        for category, stats in report['category_breakdown'].items():
            print(f"   {category.title()}: {stats['count']} coins | "
                  f"Avg Price: ${stats['avg_price']:.6f} | "
                  f"Avg Spread: {stats['avg_spread']:.1f}bps")
        
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Universal market maker error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
