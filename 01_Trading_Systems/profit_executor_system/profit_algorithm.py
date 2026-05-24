#!/usr/bin/env python3
import os
"""
PROFIT-OPTIMIZED UNIVERSAL TRADING ALGORITHM
Self-Developing System Focused Solely on Profit Generation
"""

import asyncio
import json
import time
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi
import requests
import hashlib

# Setup logging for profit tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PROFIT - %(message)s',
    handlers=[
        logging.FileHandler('/Users/alep/Downloads/profit_algorithm.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProfitMetrics:
    """Real-time profit tracking"""
    total_profit: float = 0.0
    daily_profit: float = 0.0
    hourly_profit: float = 0.0
    trade_count: int = 0
    win_rate: float = 0.0
    avg_profit_per_trade: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    sharpe_ratio: float = 0.0
    profit_rate_per_hour: float = 0.0
    connected_time: float = 0.0
    disconnected_time: float = 0.0
    last_connection_status: str = "disconnected"

@dataclass
class CoinOpportunity:
    """Profit opportunity for a specific coin"""
    symbol: str
    profit_potential: float
    confidence: float
    action: str  # buy, sell, hedge
    entry_price: float
    target_price: float
    stop_loss: float
    position_size: float
    risk_reward_ratio: float
    market_condition: str
    timestamp: str

class UniversalProfitEngine:
    """Universal profit engine for all coins"""
    
    def __init__(self):
        # API Configuration
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Profit tracking
        self.profit_metrics = ProfitMetrics()
        self.trade_history: List[Dict] = []
        self.profit_history: List[float] = []
        
        # Universal coin coverage
        self.all_symbols: List[str] = []
        self.active_trades: Dict[str, Dict] = {}
        self.coin_performance: Dict[str, float] = {}
        
        # Self-development parameters
        self.learning_rate = 0.01
        self.adaptation_threshold = 0.001
        self.profit_target_multiplier = 1.5
        self.risk_tolerance = 0.02
        
        # Connection tracking
        self.connection_start_time = None
        self.is_connected = False
        self.last_ping = datetime.now()
        
        # Budget management
        self.total_budget = 12.0
        self.available_capital = 12.0
        self.allocated_capital = 0.0
        self.capital_efficiency = 0.0
        
        logger.info("💰 Universal Profit Engine initialized")
        logger.info(f"💵 Budget: ${self.total_budget}")
        logger.info(f"🎯 Sole Purpose: Profit Generation")
    
    async def discover_all_tradable_coins(self) -> List[str]:
        """Discover all tradable coins on Gate.io futures"""
        try:
            contracts = self.api.list_futures_contracts(settle='usdt')
            
            # Filter for active contracts with good volume
            tradable_coins = []
            for contract in contracts:
                if (contract.status == 'open' and 
                    contract.quanto_multiplier == 1 and  # Standard contracts
                    float(contract.order_price_round) > 0):
                    
                    symbol = contract.name
                    tradable_coins.append(symbol)
            
            # Sort by liquidity (simplified - would use volume data)
            tradable_coins.sort()
            
            self.all_symbols = tradable_coins[:50]  # Top 50 most liquid
            
            logger.info(f"🔍 Discovered {len(self.all_symbols)} tradable coins")
            logger.info(f"📊 Top coins: {self.all_symbols[:10]}")
            
            return self.all_symbols
            
        except Exception as e:
            logger.error(f"❌ Coin discovery failed: {e}")
            return ["BTC_USDT", "ETH_USDT", "SOL_USDT", "ENA_USDT"]  # Fallback
    
    async def get_account_balance(self) -> Dict:
        """Get real-time account balance"""
        try:
            accounts = self.api.list_futures_accounts(settle='usdt')
            if accounts:
                account = accounts[0]
                balance = {
                    'total': float(account.total),
                    'available': float(account.available),
                    'unrealized_pnl': float(account.unrealised_pnl),
                    'margin': float(account.margin),
                    'maintenance_margin': float(account.maintenance_margin)
                }
                
                self.available_capital = balance['available']
                self.capital_efficiency = (balance['total'] - self.total_budget) / self.total_budget * 100
                
                return balance
        except Exception as e:
            logger.error(f"❌ Balance check failed: {e}")
        return {}
    
    async def get_market_data(self, symbol: str) -> Dict:
        """Get comprehensive market data for profit analysis"""
        try:
            # Get order book
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=10)
            
            if not book.bids or not book.asks:
                return {}
            
            # Process order book
            bids = [[float(b.p), float(b.s)] for b in book.bids]
            asks = [[float(a.p), float(a.s)] for a in book.asks]
            
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            mid_price = (best_bid + best_ask) / 2
            spread_bps = (best_ask - best_bid) / mid_price * 10000
            
            # Calculate market depth
            bid_depth = sum(b[1] for b in bids[:5])
            ask_depth = sum(a[1] for a in asks[:5])
            depth_imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
            
            # Get 24h stats (would need additional API call)
            volume_24h = 1000000  # Placeholder
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': mid_price,
                'spread_bps': spread_bps,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'depth_imbalance': depth_imbalance,
                'volume_24h': volume_24h,
                'liquidity_score': min(bid_depth, ask_depth) / max(bid_depth, ask_depth),
                'volatility_estimate': spread_bps / 100,  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"❌ Market data for {symbol}: {e}")
            return {}
    
    def calculate_profit_opportunity(self, market_data: Dict, historical_data: Dict = None) -> Optional[CoinOpportunity]:
        """Calculate profit opportunity for a coin"""
        if not market_data:
            return None
        
        symbol = market_data['symbol']
        mid_price = market_data['mid_price']
        spread_bps = market_data['spread_bps']
        depth_imbalance = market_data['depth_imbalance']
        liquidity_score = market_data['liquidity_score']
        volatility = market_data['volatility_estimate']
        
        # Skip if spread is too wide
        if spread_bps > 20:
            return None
        
        # Calculate profit potential based on multiple factors
        base_potential = 0.001  # 0.1% base
        
        # Adjust for market conditions
        if abs(depth_imbalance) > 0.3:  # Strong imbalance
            base_potential += 0.002
        
        if liquidity_score > 0.8:  # High liquidity
            base_potential += 0.001
        
        if volatility > 0.01:  # Volatile market
            base_potential += 0.002
        
        # Determine action based on imbalance
        if depth_imbalance > 0.2:  # More bids - bullish
            action = 'buy'
            entry_price = market_data['best_bid']
            target_price = mid_price * (1 + base_potential * self.profit_target_multiplier)
            stop_loss = entry_price * (1 - self.risk_tolerance)
        elif depth_imbalance < -0.2:  # More asks - bearish
            action = 'sell'
            entry_price = market_data['best_ask']
            target_price = mid_price * (1 - base_potential * self.profit_target_multiplier)
            stop_loss = entry_price * (1 + self.risk_tolerance)
        else:
            # Balanced market - hedge opportunity
            action = 'hedge'
            entry_price = mid_price
            target_price = mid_price * (1 + base_potential)
            stop_loss = mid_price * (1 - self.risk_tolerance)
        
        # Calculate position size based on confidence and available capital
        confidence = min(0.9, base_potential * 100)  # Convert to confidence score
        max_position_value = self.available_capital * 0.1  # 10% per position
        position_size = min(max_position_value / entry_price, 100.0)
        
        # Risk-reward ratio
        potential_profit = abs(target_price - entry_price) * position_size
        potential_loss = abs(entry_price - stop_loss) * position_size
        risk_reward_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # Skip if risk-reward is poor
        if risk_reward_ratio < 1.5:
            return None
        
        return CoinOpportunity(
            symbol=symbol,
            profit_potential=base_potential,
            confidence=confidence,
            action=action,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            position_size=position_size,
            risk_reward_ratio=risk_reward_ratio,
            market_condition='bullish' if depth_imbalance > 0 else 'bearish' if depth_imbalance < 0 else 'neutral',
            timestamp=datetime.now().isoformat()
        )
    
    async def execute_profit_trade(self, opportunity: CoinOpportunity) -> bool:
        """Execute a profit-generating trade"""
        try:
            # Calculate order parameters
            order_params = {
                'contract': opportunity.symbol,
                'size': opportunity.position_size,
                'type': 'limit',
                'time_in_force': 'post_only'
            }
            
            if opportunity.action == 'buy':
                order_params['side'] = 'buy'
                order_params['price'] = str(opportunity.entry_price)
            elif opportunity.action == 'sell':
                order_params['side'] = 'sell'
                order_params['price'] = str(opportunity.entry_price)
            elif opportunity.action == 'hedge':
                # For hedge, place both buy and sell orders
                buy_params = order_params.copy()
                buy_params['side'] = 'buy'
                buy_params['price'] = str(opportunity.entry_price * 0.999)
                
                sell_params = order_params.copy()
                sell_params['side'] = 'sell'
                sell_params['price'] = str(opportunity.entry_price * 1.001)
                
                # Execute hedge
                buy_order = self.api.create_futures_order(settle='usdt', **buy_params)
                sell_order = self.api.create_futures_order(settle='usdt', **sell_params)
                
                logger.info(f"💰 HEDGE EXECUTED: {opportunity.symbol}")
                logger.info(f"   BUY: {buy_params['size']} @ {buy_params['price']}")
                logger.info(f"   SELL: {sell_params['size']} @ {sell_params['price']}")
                logger.info(f"   Expected Profit: ${opportunity.profit_potential * opportunity.position_size:.4f}")
                
                return True
            
            # Execute single direction trade
            result = self.api.create_futures_order(settle='usdt', **order_params)
            
            # Track the trade
            self.active_trades[opportunity.symbol] = {
                'opportunity': opportunity,
                'entry_time': datetime.now().isoformat(),
                'order_id': result.id,
                'status': 'active'
            }
            
            # Update metrics
            self.profit_metrics.trade_count += 1
            self.allocated_capital += opportunity.position_size * opportunity.entry_price
            
            logger.info(f"💰 TRADE EXECUTED: {opportunity.action.upper()} {opportunity.symbol}")
            logger.info(f"   Size: {opportunity.position_size:.3f} @ ${opportunity.entry_price:.4f}")
            logger.info(f"   Target: ${opportunity.target_price:.4f} | Stop: ${opportunity.stop_loss:.4f}")
            logger.info(f"   Risk/Reward: {opportunity.risk_reward_ratio:.2f}")
            logger.info(f"   Expected Profit: ${opportunity.profit_potential * opportunity.position_size:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")
            return False
    
    async def scan_all_coins_for_profit(self) -> List[CoinOpportunity]:
        """Scan all coins for profit opportunities"""
        opportunities = []
        
        # Get all tradable coins if not already done
        if not self.all_symbols:
            await self.discover_all_tradable_coins()
        
        # Scan each coin
        for symbol in self.all_symbols:
            try:
                market_data = await self.get_market_data(symbol)
                if market_data:
                    opportunity = self.calculate_profit_opportunity(market_data)
                    if opportunity and opportunity.confidence > 0.6:
                        opportunities.append(opportunity)
                
                # Small delay to avoid API rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error scanning {symbol}: {e}")
                continue
        
        # Sort by profit potential
        opportunities.sort(key=lambda x: x.profit_potential * x.confidence, reverse=True)
        
        return opportunities
    
    async def manage_active_trades(self):
        """Manage and close profitable trades"""
        current_time = datetime.now()
        
        for symbol, trade_info in list(self.active_trades.items()):
            try:
                opportunity = trade_info['opportunity']
                
                # Get current market data
                market_data = await self.get_market_data(symbol)
                if not market_data:
                    continue
                
                current_price = market_data['mid_price']
                
                # Check if target reached
                if opportunity.action == 'buy' and current_price >= opportunity.target_price:
                    # Take profit
                    await self.close_trade(symbol, current_price, 'profit')
                elif opportunity.action == 'sell' and current_price <= opportunity.target_price:
                    # Take profit
                    await self.close_trade(symbol, current_price, 'profit')
                elif current_price <= opportunity.stop_loss or current_price >= opportunity.stop_loss:
                    # Stop loss
                    await self.close_trade(symbol, current_price, 'loss')
                
                # Time-based exit (if held too long)
                entry_time = datetime.fromisoformat(trade_info['entry_time'])
                if (current_time - entry_time).total_seconds() > 300:  # 5 minutes
                    await self.close_trade(symbol, current_price, 'timeout')
                
            except Exception as e:
                logger.error(f"❌ Error managing {symbol} trade: {e}")
    
    async def close_trade(self, symbol: str, exit_price: float, reason: str):
        """Close a trade and calculate profit"""
        if symbol not in self.active_trades:
            return
        
        trade_info = self.active_trades[symbol]
        opportunity = trade_info['opportunity']
        
        # Calculate profit/loss
        if opportunity.action == 'buy':
            profit = (exit_price - opportunity.entry_price) * opportunity.position_size
        else:
            profit = (opportunity.entry_price - exit_price) * opportunity.position_size
        
        # Update profit metrics
        self.profit_metrics.total_profit += profit
        self.profit_metrics.daily_profit += profit
        self.profit_metrics.hourly_profit += profit
        
        if profit > 0:
            self.profit_metrics.max_profit = max(self.profit_metrics.max_profit, profit)
        else:
            self.profit_metrics.max_loss = min(self.profit_metrics.max_loss, profit)
        
        # Update win rate
        if reason == 'profit':
            wins = sum(1 for t in self.trade_history if t.get('profit', 0) > 0)
            self.profit_metrics.win_rate = wins / len(self.trade_history) if self.trade_history else 0
        
        # Record trade
        trade_record = {
            'symbol': symbol,
            'action': opportunity.action,
            'entry_price': opportunity.entry_price,
            'exit_price': exit_price,
            'size': opportunity.position_size,
            'profit': profit,
            'reason': reason,
            'duration': (datetime.now() - datetime.fromisoformat(trade_info['entry_time'])).total_seconds(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.trade_history.append(trade_record)
        self.profit_history.append(profit)
        
        # Update allocated capital
        self.allocated_capital -= opportunity.position_size * opportunity.entry_price
        
        # Remove from active trades
        del self.active_trades[symbol]
        
        # Log profit
        profit_emoji = "💰" if profit > 0 else "📉"
        logger.info(f"{profit_emoji} TRADE CLOSED: {symbol}")
        logger.info(f"   Profit: ${profit:+.4f}")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Total Profit: ${self.profit_metrics.total_profit:+.4f}")
        
        # Update coin performance
        if symbol not in self.coin_performance:
            self.coin_performance[symbol] = 0
        self.coin_performance[symbol] += profit
    
    def track_connection_status(self):
        """Track connection and disconnection time"""
        current_time = datetime.now()
        
        if self.is_connected:
            if not self.connection_start_time:
                self.connection_start_time = current_time
            
            connected_duration = (current_time - self.connection_start_time).total_seconds()
            self.profit_metrics.connected_time = connected_duration
        else:
            if self.connection_start_time:
                disconnected_duration = (current_time - self.connection_start_time).total_seconds()
                self.profit_metrics.disconnected_time += disconnected_duration
                self.connection_start_time = None
    
    def calculate_profit_efficiency(self):
        """Calculate profit efficiency metrics"""
        if self.profit_metrics.connected_time > 0:
            self.profit_metrics.profit_rate_per_hour = (
                self.profit_metrics.total_profit / (self.profit_metrics.connected_time / 3600)
            )
        
        if len(self.profit_history) > 1:
            returns = np.array(self.profit_history)
            if np.std(returns) > 0:
                self.profit_metrics.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(24)
        
        if self.profit_metrics.trade_count > 0:
            self.profit_metrics.avg_profit_per_trade = (
                self.profit_metrics.total_profit / self.profit_metrics.trade_count
            )
    
    async def profit_generation_loop(self):
        """Main profit generation loop"""
        logger.info("💰 PROFIT GENERATION LOOP STARTED")
        logger.info(f"🎯 Focus: Pure Profit Generation")
        logger.info(f"💵 Budget: ${self.total_budget}")
        logger.info(f"📊 Scanning {len(self.all_symbols)} coins")
        
        while True:
            try:
                # Update connection status
                self.is_connected = True  # Simplified - would check actual connection
                self.track_connection_status()
                
                # Get current balance
                balance = await self.get_account_balance()
                if balance:
                    logger.info(f"💰 Balance: ${balance['available']:.2f} | PnL: ${balance['unrealized_pnl']:+.4f}")
                
                # Scan for profit opportunities
                opportunities = await self.scan_all_coins_for_profit()
                
                if opportunities:
                    logger.info(f"🎯 Found {len(opportunities)} profit opportunities")
                    
                    # Execute best opportunities
                    for i, opp in enumerate(opportunities[:3]):  # Top 3
                        if self.allocated_capital < self.available_capital * 0.8:  # Don't over-allocate
                            success = await self.execute_profit_trade(opp)
                            if success:
                                logger.info(f"✅ Executed #{i+1}: {opp.symbol} ({opp.action})")
                        else:
                            logger.warning(f"⚠️ Capital limit reached - skipping {opp.symbol}")
                
                # Manage active trades
                await self.manage_active_trades()
                
                # Calculate efficiency metrics
                self.calculate_profit_efficiency()
                
                # Log profit status
                logger.info(f"📊 Profit Status: ${self.profit_metrics.total_profit:+.4f} | "
                           f"Trades: {self.profit_metrics.trade_count} | "
                           f"Win Rate: {self.profit_metrics.win_rate:.1%} | "
                           f"Efficiency: ${self.profit_metrics.profit_rate_per_hour:.2f}/hr")
                
                # Adapt parameters based on performance
                if self.profit_metrics.win_rate < 0.4:
                    self.risk_tolerance *= 0.95  # Reduce risk
                elif self.profit_metrics.win_rate > 0.7:
                    self.risk_tolerance = min(self.risk_tolerance * 1.02, 0.05)  # Increase risk
                
                await asyncio.sleep(5)  # Scan every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Profit loop error: {e}")
                await asyncio.sleep(10)
    
    def get_profit_report(self) -> Dict:
        """Generate comprehensive profit report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_profit': self.profit_metrics.total_profit,
            'daily_profit': self.profit_metrics.daily_profit,
            'hourly_profit': self.profit_metrics.hourly_profit,
            'trade_count': self.profit_metrics.trade_count,
            'win_rate': self.profit_metrics.win_rate,
            'avg_profit_per_trade': self.profit_metrics.avg_profit_per_trade,
            'sharpe_ratio': self.profit_metrics.sharpe_ratio,
            'profit_rate_per_hour': self.profit_metrics.profit_rate_per_hour,
            'connected_time': self.profit_metrics.connected_time,
            'disconnected_time': self.profit_metrics.disconnected_time,
            'capital_efficiency': self.capital_efficiency,
            'active_trades': len(self.active_trades),
            'budget_utilization': self.allocated_capital / self.total_budget * 100,
            'top_performing_coins': sorted(self.coin_performance.items(), key=lambda x: x[1], reverse=True)[:5]
        }

async def main():
    """Main profit algorithm"""
    print("💰 PROFIT-OPTIMIZED UNIVERSAL TRADING ALGORITHM")
    print("="*70)
    print("🎯 SOLE PURPOSE: AUTOMATIC PROFIT GENERATION")
    print("🤖 SELF-DEVELOPING: NO HUMAN GOVERNANCE NEEDED")
    print("🌍 UNIVERSAL: ALL COINS, ALL OPPORTUNITIES")
    print("💵 BUDGET: $12 - FULL CAPITAL UTILIZATION")
    print("="*70)
    
    # Initialize profit engine
    profit_engine = UniversalProfitEngine()
    
    # Discover all tradable coins
    await profit_engine.discover_all_tradable_coins()
    
    try:
        # Start profit generation
        await profit_engine.profit_generation_loop()
        
    except KeyboardInterrupt:
        print("\n💰 Profit algorithm stopped by user")
        
        # Final profit report
        report = profit_engine.get_profit_report()
        print("\n" + "="*70)
        print("📊 FINAL PROFIT REPORT")
        print("="*70)
        print(f"💰 Total Profit: ${report['total_profit']:+.4f}")
        print(f"📈 Daily Profit: ${report['daily_profit']:+.4f}")
        print(f"🔄 Total Trades: {report['trade_count']}")
        print(f"🎯 Win Rate: {report['win_rate']:.1%}")
        print(f"⚡ Profit Rate: ${report['profit_rate_per_hour']:.2f}/hour")
        print(f"⏱️ Connected: {report['connected_time']:.0f}s | Disconnected: {report['disconnected_time']:.0f}s")
        print(f"💵 Capital Efficiency: {report['capital_efficiency']:.1f}%")
        
        if report['top_performing_coins']:
            print(f"\n🏆 Top Performing Coins:")
            for coin, profit in report['top_performing_coins']:
                print(f"   {coin}: ${profit:+.4f}")
        
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Profit algorithm error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
