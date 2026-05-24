#!/usr/bin/env python3
import os
"""
PROFIT EXECUTOR SYSTEM
Actually executes trades and changes your balance
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
    format='%(asctime)s - EXECUTOR - %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/profit_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProfitExecutor:
    """Actually executes profitable trades"""
    
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Trading parameters
        self.symbols = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "ENA_USDT"]
        self.trade_size_usdt = 5.0  # $5 per trade (aggressive for small budget)
        self.min_profit_bps = 10  # 0.1% minimum profit
        
        # Execution tracking
        self.start_balance = 0.0
        self.current_balance = 0.0
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0
        
        logger.info("💰 Profit Executor initialized")
        logger.info(f"💵 Trade Size: ${self.trade_size_usdt}")
        logger.info(f"🎯 Min Profit: {self.min_profit_bps} bps")
    
    async def get_balance(self) -> Dict:
        """Get current account balance"""
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
            logger.error(f"❌ Balance check failed: {e}")
        return {}
    
    async def get_positions(self) -> Dict:
        """Get current positions"""
        try:
            positions = self.api.list_positions(settle='usdt')
            active_positions = {}
            
            for pos in positions:
                if float(pos.size) != 0:
                    active_positions[pos.contract] = {
                        'size': float(pos.size),
                        'entry_price': float(pos.entry_price),
                        'mark_price': float(pos.mark_price),
                        'unrealized_pnl': float(pos.unrealised_pnl)
                    }
            
            return active_positions
        except Exception as e:
            logger.error(f"❌ Positions check failed: {e}")
        return {}
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker price"""
        try:
            # Use order book to get current price
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=1)
            
            if book.bids and book.asks:
                best_bid = float(book.bids[0].p)
                best_ask = float(book.asks[0].p)
                mid_price = (best_bid + best_ask) / 2
                
                return {
                    'symbol': symbol,
                    'bid': best_bid,
                    'ask': best_ask,
                    'mid': mid_price,
                    'spread_bps': (best_ask - best_bid) / mid_price * 10000
                }
        except Exception as e:
            logger.error(f"❌ Ticker for {symbol}: {e}")
        return None
    
    async def execute_market_buy(self, symbol: str, usdt_amount: float) -> bool:
        """Execute market buy order"""
        try:
            ticker = await self.get_ticker(symbol)
            if not ticker:
                return False
            
            # Calculate size from USDT amount
            size = usdt_amount / ticker['ask']
            
            order_params = {
                'contract': symbol,
                'side': 'buy',
                'type': 'market',
                'size': size,
                'time_in_force': 'ioc'
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            
            logger.info(f"🟢 MARKET BUY EXECUTED: {symbol}")
            logger.info(f"   Size: {size:.6f} | Value: ${usdt_amount:.2f}")
            logger.info(f"   Price: ~${ticker['ask']:.4f}")
            logger.info(f"   Order ID: {result.id}")
            
            self.total_trades += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Market buy failed: {e}")
            return False
    
    async def execute_market_sell(self, symbol: str, usdt_amount: float) -> bool:
        """Execute market sell order"""
        try:
            ticker = await self.get_ticker(symbol)
            if not ticker:
                return False
            
            # Calculate size from USDT amount
            size = usdt_amount / ticker['bid']
            
            order_params = {
                'contract': symbol,
                'side': 'sell',
                'type': 'market',
                'size': size,
                'time_in_force': 'ioc'
            }
            
            result = self.api.create_futures_order(settle='usdt', **order_params)
            
            logger.info(f"🔴 MARKET SELL EXECUTED: {symbol}")
            logger.info(f"   Size: {size:.6f} | Value: ${usdt_amount:.2f}")
            logger.info(f"   Price: ~${ticker['bid']:.4f}")
            logger.info(f"   Order ID: {result.id}")
            
            self.total_trades += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Market sell failed: {e}")
            return False
    
    async def close_position_for_profit(self, symbol: str, position: Dict) -> bool:
        """Close position if profitable"""
        try:
            size = abs(position['size'])
            entry_price = position['entry_price']
            mark_price = position['mark_price']
            
            if position['size'] > 0:  # Long position
                profit_pct = (mark_price - entry_price) / entry_price * 10000  # bps
                if profit_pct > self.min_profit_bps:
                    logger.info(f"💰 Closing profitable LONG {symbol}")
                    logger.info(f"   Entry: ${entry_price:.4f} | Current: ${mark_price:.4f}")
                    logger.info(f"   Profit: {profit_pct:.1f} bps")
                    
                    return await self.execute_market_sell(symbol, size * mark_price)
            
            else:  # Short position
                profit_pct = (entry_price - mark_price) / entry_price * 10000  # bps
                if profit_pct > self.min_profit_bps:
                    logger.info(f"💰 Closing profitable SHORT {symbol}")
                    logger.info(f"   Entry: ${entry_price:.4f} | Current: ${mark_price:.4f}")
                    logger.info(f"   Profit: {profit_pct:.1f} bps")
                    
                    return await self.execute_market_buy(symbol, size * mark_price)
        
        except Exception as e:
            logger.error(f"❌ Error closing {symbol}: {e}")
        
        return False
    
    async def scalp_quick_profits(self):
        """Execute quick scalp trades"""
        for symbol in self.symbols:
            try:
                ticker = await self.get_ticker(symbol)
                if not ticker:
                    continue
                
                # Check if spread is tight enough for scalping
                if ticker['spread_bps'] > 20:  # Skip if spread too wide
                    continue
                
                # Quick scalp: Buy and immediately sell if price moves
                current_balance = await self.get_balance()
                if not current_balance or current_balance['available'] < self.trade_size_usdt:
                    continue
                
                # Execute quick buy
                logger.info(f"⚡ Quick scalp attempt: {symbol}")
                
                if await self.execute_market_buy(symbol, self.trade_size_usdt):
                    # Wait a moment for price movement
                    await asyncio.sleep(2)
                    
                    # Check new price and sell if profitable
                    new_ticker = await self.get_ticker(symbol)
                    if new_ticker:
                        price_change = (new_ticker['mid'] - ticker['mid']) / ticker['mid'] * 10000
                        
                        if price_change > self.min_profit_bps:
                            logger.info(f"🚀 Quick profit detected: {price_change:.1f} bps")
                            await self.execute_market_sell(symbol, self.trade_size_usdt)
                            self.profitable_trades += 1
                        else:
                            # Cut losses quickly
                            logger.info(f"⚡ No profit, cutting loss: {price_change:.1f} bps")
                            await self.execute_market_sell(symbol, self.trade_size_usdt)
                
                # Small delay between symbols
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Scalp error for {symbol}: {e}")
    
    async def profit_execution_loop(self):
        """Main profit execution loop"""
        logger.info("💰 PROFIT EXECUTION LOOP STARTED")
        logger.info(f"🎯 Strategy: Quick scalp trades + profit taking")
        logger.info(f"💵 Trade size: ${self.trade_size_usdt}")
        logger.info(f"⚡ High frequency execution")
        
        # Get initial balance
        await self.get_balance()
        logger.info(f"💰 Starting balance: ${self.start_balance:.2f}")
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                
                # Get current balance
                balance = await self.get_balance()
                if balance:
                    profit = balance['total'] - self.start_balance
                    logger.info(f"💰 Balance: ${balance['total']:.2f} | P&L: ${profit:+.4f}")
                
                # Check positions for profit taking
                positions = await self.get_positions()
                if positions:
                    logger.info(f"📊 Active positions: {len(positions)}")
                    
                    for symbol, position in positions.items():
                        await self.close_position_for_profit(symbol, position)
                
                # Execute quick scalp trades
                if balance and balance['available'] >= self.trade_size_usdt:
                    await self.scalp_quick_profits()
                
                # Log performance
                if self.total_trades > 0:
                    profit_rate = self.profitable_trades / self.total_trades
                    logger.info(f"📊 Cycle {cycle}: Trades: {self.total_trades} | "
                               f"Win Rate: {profit_rate:.1%} | "
                               f"Profitable: {self.profitable_trades}")
                
                await asyncio.sleep(10)  # Execute every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Execution loop error: {e}")
                await asyncio.sleep(5)
    
    def get_performance_report(self) -> Dict:
        """Get execution performance"""
        total_profit = self.current_balance - self.start_balance
        return {
            'timestamp': datetime.now().isoformat(),
            'start_balance': self.start_balance,
            'current_balance': self.current_balance,
            'total_profit': total_profit,
            'total_trades': self.total_trades,
            'profitable_trades': self.profitable_trades,
            'win_rate': self.profitable_trades / max(1, self.total_trades),
            'profit_per_trade': total_profit / max(1, self.total_trades)
        }

async def main():
    """Main profit executor"""
    print("💰 PROFIT EXECUTOR SYSTEM")
    print("="*60)
    print("🎯 ACTUALLY EXECUTES TRADES")
    print("⚡ Quick Scalp Trading")
    print("💵 Market Orders for Fast Execution")
    print("🔄 Real Balance Changes")
    print("="*60)
    
    # Initialize profit executor
    executor = ProfitExecutor()
    
    try:
        # Start profit execution
        await executor.profit_execution_loop()
        
    except KeyboardInterrupt:
        print("\n💰 Profit executor stopped by user")
        
        # Final performance report
        report = executor.get_performance_report()
        print("\n" + "="*60)
        print("📊 EXECUTION PERFORMANCE")
        print("="*60)
        print(f"💰 Start Balance: ${report['start_balance']:.2f}")
        print(f"💰 End Balance: ${report['current_balance']:.2f}")
        print(f"💵 Total Profit: ${report['total_profit']:+.4f}")
        print(f"🔄 Total Trades: {report['total_trades']}")
        print(f"✅ Profitable Trades: {report['profitable_trades']}")
        print(f"🎯 Win Rate: {report['win_rate']:.1%}")
        print(f"💰 Profit per Trade: ${report['profit_per_trade']:+.4f}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Profit executor error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
