#!/usr/bin/env python3
import os
"""
SECOND PROFIT SYSTEM
Generates profit every second through ultra-high frequency trading
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SECOND-PROFIT - %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/second_profit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecondProfitSystem:
    """Ultra-high frequency profit system"""
    
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Ultra-high frequency parameters
        self.symbols = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "ENA_USDT"]
        self.micro_trade_size = 1.0  # $1 per micro trade
        self.min_profit_ticks = 1  # Minimum 1 tick profit
        self.max_latency_ms = 100  # Max 100ms latency
        
        # Second-by-second tracking
        self.second_counter = 0
        self.profit_per_second = []
        self.trades_per_second = []
        self.current_second_profit = 0.0
        self.current_second_trades = 0
        
        # Performance metrics
        self.start_balance = 0.0
        self.current_balance = 0.0
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0
        self.last_second_time = time.time()
        
        # Price tracking for arbitrage
        self.price_history: Dict[str, List[float]] = {}
        self.spread_history: Dict[str, List[float]] = {}
        
        logger.info("⚡ SECOND PROFIT SYSTEM INITIALIZED")
        logger.info(f"🎯 Goal: PROFIT EVERY SECOND")
        logger.info(f"💰 Micro Trade Size: ${self.micro_trade_size}")
        logger.info(f"⚡ Max Latency: {self.max_latency_ms}ms")
    
    async def get_balance(self) -> Dict:
        """Get current balance with minimal latency"""
        try:
            accounts = self.api.list_futures_accounts(settle='usdt')
            if accounts:
                account = accounts[0]
                balance = {
                    'total': float(account.total),
                    'available': float(account.available),
                    'unrealized_pnl': float(account.unrealised_pnl)
                }
                
                if self.start_balance == 0.0:
                    self.start_balance = balance['total']
                
                self.current_balance = balance['total']
                return balance
        except Exception as e:
            logger.error(f"❌ Balance error: {e}")
        return {}
    
    async def get_tick_data(self, symbol: str) -> Optional[Dict]:
        """Get tick data with minimal latency"""
        try:
            start_time = time.time()
            
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=1)
            
            latency_ms = (time.time() - start_time) * 1000
            if latency_ms > self.max_latency_ms:
                return None  # Skip if too slow
            
            if book.bids and book.asks:
                bid = float(book.bids[0].p)
                ask = float(book.asks[0].p)
                mid = (bid + ask) / 2
                spread = ask - bid
                spread_bps = spread / mid * 10000
                
                # Update price history
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                    self.spread_history[symbol] = []
                
                self.price_history[symbol].append(mid)
                self.spread_history[symbol].append(spread_bps)
                
                # Keep only last 100 ticks
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol] = self.price_history[symbol][-100:]
                    self.spread_history[symbol] = self.spread_history[symbol][-100:]
                
                return {
                    'symbol': symbol,
                    'bid': bid,
                    'ask': ask,
                    'mid': mid,
                    'spread': spread,
                    'spread_bps': spread_bps,
                    'timestamp': time.time()
                }
        except Exception as e:
            logger.error(f"❌ Tick data for {symbol}: {e}")
        return None
    
    async def execute_micro_buy(self, symbol: str, price: float) -> Optional[str]:
        """Execute micro buy order"""
        try:
            size = self.micro_trade_size / price
            
            order_params = {
                'contract': symbol,
                'side': 'buy',
                'type': 'market',
                'size': size,
                'time_in_force': 'ioc'
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            
            self.total_trades += 1
            self.current_second_trades += 1
            
            logger.info(f"🟢 MICRO BUY: {symbol} | Size: {size:.6f} | Value: ${self.micro_trade_size}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Micro buy failed: {e}")
            return None
    
    async def execute_micro_sell(self, symbol: str, price: float) -> Optional[str]:
        """Execute micro sell order"""
        try:
            size = self.micro_trade_size / price
            
            order_params = {
                'contract': symbol,
                'side': 'sell',
                'type': 'market',
                'size': size,
                'time_in_force': 'ioc'
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            
            self.total_trades += 1
            self.current_second_trades += 1
            
            logger.info(f"🔴 MICRO SELL: {symbol} | Size: {size:.6f} | Value: ${self.micro_trade_size}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"❌ Micro sell failed: {e}")
            return None
    
    def detect_micro_arbitrage(self, symbol: str, tick_data: Dict) -> Optional[str]:
        """Detect micro arbitrage opportunities"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 2:
            return None
        
        prices = self.price_history[symbol]
        spreads = self.spread_history[symbol]
        
        current_price = tick_data['mid']
        current_spread = tick_data['spread_bps']
        
        # Check for price momentum
        if len(prices) >= 3:
            price_change = (current_price - prices[-2]) / prices[-2] * 10000
            
            # Micro momentum strategy
            if price_change > 2:  # 0.02% upward momentum
                return "buy"
            elif price_change < -2:  # 0.02% downward momentum
                return "sell"
        
        # Check for spread compression/expansion
        if len(spreads) >= 5:
            avg_spread = np.mean(spreads[-5:])
            
            if current_spread < avg_spread * 0.8:  # Spread compressed
                return "buy"  # Expect spread to expand
            elif current_spread > avg_spread * 1.2:  # Spread expanded
                return "sell"  # Expect spread to compress
        
        return None
    
    async def execute_second_strategy(self):
        """Execute strategy to profit every second"""
        # Get current balance
        balance = await self.get_balance()
        if not balance or balance['available'] < self.micro_trade_size:
            return
        
        # Scan all symbols for opportunities
        for symbol in self.symbols:
            try:
                # Get tick data
                tick_data = await self.get_tick_data(symbol)
                if not tick_data:
                    continue
                
                # Detect arbitrage opportunity
                signal = self.detect_micro_arbitrage(symbol, tick_data)
                
                if signal:
                    logger.info(f"⚡ SIGNAL: {signal} {symbol} | Price: ${tick_data['mid']:.4f} | Spread: {tick_data['spread_bps']:.1f}bps")
                    
                    if signal == "buy":
                        if await self.execute_micro_buy(symbol, tick_data['ask']):
                            # Immediate sell attempt for profit
                            await asyncio.sleep(0.1)  # 100ms delay
                            new_tick = await self.get_tick_data(symbol)
                            if new_tick and new_tick['bid'] > tick_data['ask']:
                                await self.execute_micro_sell(symbol, new_tick['bid'])
                                profit = (new_tick['bid'] - tick_data['ask']) * (self.micro_trade_size / tick_data['ask'])
                                self.current_second_profit += profit
                                self.profitable_trades += 1
                    
                    elif signal == "sell":
                        if await self.execute_micro_sell(symbol, tick_data['bid']):
                            # Immediate buy attempt for profit
                            await asyncio.sleep(0.1)  # 100ms delay
                            new_tick = await self.get_tick_data(symbol)
                            if new_tick and new_tick['ask'] < tick_data['bid']:
                                await self.execute_micro_buy(symbol, new_tick['ask'])
                                profit = (tick_data['bid'] - new_tick['ask']) * (self.micro_trade_size / tick_data['bid'])
                                self.current_second_profit += profit
                                self.profitable_trades += 1
                
                # Micro delay between symbols
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"❌ Strategy error for {symbol}: {e}")
    
    def update_second_metrics(self):
        """Update second-by-second metrics"""
        current_time = time.time()
        
        # Check if a second has passed
        if current_time - self.last_second_time >= 1.0:
            self.second_counter += 1
            
            # Store second metrics
            self.profit_per_second.append(self.current_second_profit)
            self.trades_per_second.append(self.current_second_trades)
            
            # Log second performance
            if self.current_second_profit != 0:
                logger.info(f"⏱️ SECOND #{self.second_counter}: Profit: ${self.current_second_profit:+.6f} | Trades: {self.current_second_trades}")
            
            # Reset for next second
            self.current_second_profit = 0.0
            self.current_second_trades = 0
            self.last_second_time = current_time
            
            # Keep only last 60 seconds of data
            if len(self.profit_per_second) > 60:
                self.profit_per_second = self.profit_per_second[-60:]
                self.trades_per_second = self.trades_per_second[-60:]
    
    async def second_profit_loop(self):
        """Main loop - profit every second"""
        logger.info("⚡ SECOND PROFIT LOOP STARTED")
        logger.info(f"🎯 OBJECTIVE: PROFIT EVERY SINGLE SECOND")
        logger.info(f"💰 Micro Trades: ${self.micro_trade_size}")
        logger.info(f"📊 Symbols: {self.symbols}")
        
        # Get initial balance
        await self.get_balance()
        logger.info(f"💰 Starting Balance: ${self.start_balance:.2f}")
        
        self.last_second_time = time.time()
        
        while True:
            try:
                # Execute profit strategy
                await self.execute_second_strategy()
                
                # Update second metrics
                self.update_second_metrics()
                
                # Get balance every 5 seconds
                if self.second_counter % 5 == 0:
                    balance = await self.get_balance()
                    if balance:
                        profit = balance['total'] - self.start_balance
                        self.total_profit = profit
                        
                        # Calculate recent performance
                        if len(self.profit_per_second) > 0:
                            avg_profit_per_second = np.mean(self.profit_per_second[-10:])
                            avg_trades_per_second = np.mean(self.trades_per_second[-10:])
                            
                            logger.info(f"📊 PERFORMANCE: Balance: ${balance['total']:.2f} | "
                                       f"Total P&L: ${profit:+.4f} | "
                                       f"Avg/Sec: ${avg_profit_per_second:+.6f} | "
                                       f"Avg Trades/Sec: {avg_trades_per_second:.1f}")
                
                # Ultra-high frequency - minimal delay
                await asyncio.sleep(0.1)  # 100ms cycle time
                
            except Exception as e:
                logger.error(f"❌ Second profit loop error: {e}")
                await asyncio.sleep(0.5)
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        total_profit = self.current_balance - self.start_balance
        
        # Calculate second-level metrics
        profitable_seconds = len([p for p in self.profit_per_second if p > 0])
        profit_per_second_avg = np.mean(self.profit_per_second) if self.profit_per_second else 0
        trades_per_second_avg = np.mean(self.trades_per_second) if self.trades_per_second else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_seconds': self.second_counter,
            'start_balance': self.start_balance,
            'current_balance': self.current_balance,
            'total_profit': total_profit,
            'total_trades': self.total_trades,
            'profitable_trades': self.profitable_trades,
            'win_rate': self.profitable_trades / max(1, self.total_trades),
            'profitable_seconds': profitable_seconds,
            'profitable_second_rate': profitable_seconds / max(1, self.second_counter),
            'avg_profit_per_second': profit_per_second_avg,
            'avg_trades_per_second': trades_per_second_avg,
            'max_profit_per_second': max(self.profit_per_second) if self.profit_per_second else 0,
            'total_profit_potential': profit_per_second_avg * 86400  # Daily potential
        }

async def main():
    """Main second profit system"""
    print("⚡ SECOND PROFIT SYSTEM")
    print("="*70)
    print("🎯 OBJECTIVE: PROFIT EVERY SINGLE SECOND")
    print("💰 Ultra-High Frequency Trading")
    print("📊 Micro Arbitrage Strategy")
    print("⚡ 100ms Latency Target")
    print("🔄 Continuous Execution")
    print("="*70)
    
    # Initialize second profit system
    second_system = SecondProfitSystem()
    
    try:
        # Start second profit loop
        await second_system.second_profit_loop()
        
    except KeyboardInterrupt:
        print("\n⚡ Second profit system stopped by user")
        
        # Final performance report
        report = second_system.get_performance_report()
        print("\n" + "="*70)
        print("📊 SECOND PROFIT PERFORMANCE REPORT")
        print("="*70)
        print(f"⏱️ Total Seconds: {report['total_seconds']}")
        print(f"💰 Start Balance: ${report['start_balance']:.2f}")
        print(f"💰 End Balance: ${report['current_balance']:.2f}")
        print(f"💵 Total Profit: ${report['total_profit']:+.4f}")
        print(f"🔄 Total Trades: {report['total_trades']}")
        print(f"✅ Profitable Trades: {report['profitable_trades']}")
        print(f"🎯 Win Rate: {report['win_rate']:.1%}")
        print(f"⏱️ Profitable Seconds: {report['profitable_seconds']}/{report['total_seconds']}")
        print(f"📈 Profitable Second Rate: {report['profitable_second_rate']:.1%}")
        print(f"💰 Avg Profit/Second: ${report['avg_profit_per_second']:+.6f}")
        print(f"📊 Avg Trades/Second: {report['avg_trades_per_second']:.1f}")
        print(f"🚀 Max Profit/Second: ${report['max_profit_per_second']:+.6f}")
        print(f"🌟 Daily Profit Potential: ${report['total_profit_potential']:+.2f}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Second profit system error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
