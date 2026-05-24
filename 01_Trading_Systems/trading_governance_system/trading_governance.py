#!/usr/bin/env python3
import os
"""
TRADING GOVERNANCE SYSTEM
24/7 Trading Operations Management & Robot Development Oversight
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    timestamp: str
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_profit: float
    total_fees: float
    current_positions: Dict[str, float]
    account_balance: float
    unrealized_pnl: float
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0

@dataclass
class RiskLimits:
    """Risk management limits"""
    max_position_size: float = 100.0  # Max ENA per position
    max_daily_loss: float = 50.0  # Max daily loss in USD
    max_positions: int = 5  # Max concurrent positions
    min_profit_margin: float = 0.002  # 0.2% minimum profit
    max_drawdown_percent: float = 10.0  # Max 10% drawdown

@dataclass
class GovernanceConfig:
    """Governance system configuration"""
    api_key: str = os.environ.get("GATE_API_KEY", "")
    api_secret: str = os.environ.get("GATE_API_SECRET", "")
    monitoring_interval: int = 60  # seconds
    report_interval: int = 3600  # 1 hour
    emergency_stop: bool = False
    auto_restart: bool = True
    backup_frequency: int = 1800  # 30 minutes

class TradingGovernance:
    """Main trading governance system"""
    
    def __init__(self):
        self.config = GovernanceConfig()
        self.risk_limits = RiskLimits()
        self.metrics_history: List[TradingMetrics] = []
        self.current_metrics: Optional[TradingMetrics] = None
        self.start_time = datetime.now()
        self.daily_pnl = 0.0
        self.daily_trades = 0
        
        # Initialize API
        cfg = Configuration(key=self.config.api_key, secret=self.config.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # Governance state
        self.system_health = "HEALTHY"
        self.last_check = datetime.now()
        self.alerts: List[str] = []
        
    async def get_account_status(self) -> Dict:
        """Get current account status"""
        try:
            accounts = self.api.list_futures_accounts(settle='usdt')
            if accounts:
                account = accounts[0]
                return {
                    'balance': float(account.total),
                    'available': float(account.available),
                    'unrealized_pnl': float(account.unrealised_pnl),
                    'margin': float(account.margin),
                    'maintenance_margin': float(account.maintenance_margin)
                }
        except Exception as e:
            logger.error(f"Account status error: {e}")
        return {}
    
    async def get_positions(self) -> Dict[str, Dict]:
        """Get all current positions"""
        try:
            positions = self.api.list_positions(settle='usdt')
            active_positions = {}
            
            for pos in positions:
                if float(pos.size) != 0:
                    active_positions[pos.contract] = {
                        'size': float(pos.size),
                        'entry_price': float(pos.entry_price),
                        'mark_price': float(pos.mark_price),
                        'unrealized_pnl': float(pos.unrealised_pnl),
                        'percentage_pnl': (float(pos.mark_price) - float(pos.entry_price)) / float(pos.entry_price) * 100
                    }
            
            return active_positions
        except Exception as e:
            logger.error(f"Positions error: {e}")
        return {}
    
    async def check_risk_limits(self, positions: Dict, account: Dict) -> List[str]:
        """Check if current positions violate risk limits"""
        violations = []
        
        # Check position sizes
        for symbol, pos in positions.items():
            if abs(pos['size']) > self.risk_limits.max_position_size:
                violations.append(f"Position size exceeded for {symbol}: {abs(pos['size'])} > {self.risk_limits.max_position_size}")
        
        # Check number of positions
        if len(positions) > self.risk_limits.max_positions:
            violations.append(f"Too many positions: {len(positions)} > {self.risk_limits.max_positions}")
        
        # Check daily loss
        if self.daily_pnl < -self.risk_limits.max_daily_loss:
            violations.append(f"Daily loss exceeded: ${self.daily_pnl:.2f} < -${self.risk_limits.max_daily_loss}")
        
        # Check drawdown
        if account.get('unrealized_pnl', 0) < -account.get('balance', 0) * (self.risk_limits.max_drawdown_percent / 100):
            violations.append(f"Max drawdown exceeded: ${account.get('unrealized_pnl', 0):.2f}")
        
        return violations
    
    async def calculate_metrics(self) -> TradingMetrics:
        """Calculate current trading metrics"""
        account = await self.get_account_status()
        positions = await self.get_positions()
        
        # Calculate performance metrics
        total_profit = sum(pos['unrealized_pnl'] for pos in positions.values())
        
        # Calculate win rate (simplified)
        successful_trades = sum(1 for pos in positions.values() if pos['unrealized_pnl'] > 0)
        total_trades = len(positions)
        win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(self.metrics_history) > 1:
            returns = [m.total_profit for m in self.metrics_history[-24:]]  # Last 24 hours
            if len(returns) > 1:
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                sharpe_ratio = avg_return / (variance ** 0.5) if variance > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        metrics = TradingMetrics(
            timestamp=datetime.now().isoformat(),
            total_trades=self.daily_trades,
            successful_trades=successful_trades,
            failed_trades=total_trades - successful_trades,
            total_profit=total_profit,
            total_fees=0.0,  # Would need to track from actual trades
            current_positions={symbol: pos['size'] for symbol, pos in positions.items()},
            account_balance=account.get('balance', 0),
            unrealized_pnl=account.get('unrealized_pnl', 0),
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate
        )
        
        return metrics
    
    async def monitor_system_health(self) -> str:
        """Monitor overall system health"""
        try:
            # Test API connectivity
            account = await self.get_account_status()
            if not account:
                return "API_CONNECTION_ERROR"
            
            # Check for emergency stop
            if self.config.emergency_stop:
                return "EMERGENCY_STOP"
            
            # Check drawdown
            if account.get('unrealized_pnl', 0) < -account.get('balance', 0) * 0.15:  # 15% drawdown
                return "CRITICAL_DRAWDOWN"
            
            # Check daily loss
            if self.daily_pnl < -self.risk_limits.max_daily_loss * 2:  # Double daily limit
                return "DAILY_LOSS_LIMIT"
            
            return "HEALTHY"
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return "SYSTEM_ERROR"
    
    async def generate_governance_report(self) -> Dict:
        """Generate comprehensive governance report"""
        metrics = await self.calculate_metrics()
        positions = await self.get_positions()
        account = await self.get_account_status()
        health = await self.monitor_system_health()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': health,
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'account_status': account,
            'positions': positions,
            'performance_metrics': asdict(metrics),
            'risk_limits': asdict(self.risk_limits),
            'alerts': self.alerts[-10:],  # Last 10 alerts
            'governance_config': {
                'monitoring_interval': self.config.monitoring_interval,
                'emergency_stop': self.config.emergency_stop,
                'auto_restart': self.config.auto_restart
            }
        }
        
        return report
    
    async def save_governance_state(self):
        """Save current governance state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'metrics_history': [asdict(m) for m in self.metrics_history[-100:]],  # Last 100 metrics
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'alerts': self.alerts,
            'config': asdict(self.config),
            'risk_limits': asdict(self.risk_limits)
        }
        
        try:
            with open('/Users/alep/Downloads/governance_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            logger.info("Governance state saved")
        except Exception as e:
            logger.error(f"Failed to save governance state: {e}")
    
    async def load_governance_state(self):
        """Load previous governance state"""
        try:
            with open('/Users/alep/Downloads/governance_state.json', 'r') as f:
                state = json.load(f)
            
            # Restore metrics history
            self.metrics_history = [TradingMetrics(**m) for m in state.get('metrics_history', [])]
            self.daily_pnl = state.get('daily_pnl', 0.0)
            self.daily_trades = state.get('daily_trades', 0)
            self.alerts = state.get('alerts', [])
            
            logger.info("Governance state loaded")
        except FileNotFoundError:
            logger.info("No previous governance state found")
        except Exception as e:
            logger.error(f"Failed to load governance state: {e}")
    
    async def governance_loop(self):
        """Main governance monitoring loop"""
        logger.info("🏛️ TRADING GOVERNANCE SYSTEM STARTED")
        logger.info(f"📊 Monitoring interval: {self.config.monitoring_interval}s")
        logger.info(f"📋 Report interval: {self.config.report_interval}s")
        
        last_report_time = datetime.now()
        last_backup_time = datetime.now()
        
        while True:
            try:
                current_time = datetime.now()
                
                # Get current metrics
                metrics = await self.calculate_metrics()
                self.current_metrics = metrics
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check system health
                health = await self.monitor_system_health()
                self.system_health = health
                
                # Get positions and check risk limits
                positions = await self.get_positions()
                account = await self.get_account_status()
                violations = await self.check_risk_limits(positions, account)
                
                # Log status
                logger.info(f"📊 Status: {health} | Balance: ${account.get('balance', 0):.2f} | PnL: ${metrics.total_profit:+.4f} | Positions: {len(positions)}")
                
                # Handle violations
                if violations:
                    for violation in violations:
                        alert = f"⚠️ RISK VIOLATION: {violation}"
                        logger.warning(alert)
                        self.alerts.append(alert)
                        
                        # Emergency stop for critical violations
                        if "exceeded" in violation.lower():
                            self.config.emergency_stop = True
                            logger.critical("🚨 EMERGENCY STOP ACTIVATED")
                
                # Generate periodic reports
                if (current_time - last_report_time).total_seconds() >= self.config.report_interval:
                    report = await self.generate_governance_report()
                    
                    # Save report
                    report_file = f"/Users/alep/Downloads/governance_report_{current_time.strftime('%Y%m%d_%H%M%S')}.json"
                    with open(report_file, 'w') as f:
                        json.dump(report, f, indent=2)
                    
                    logger.info(f"📋 Governance report saved: {report_file}")
                    last_report_time = current_time
                
                # Backup state
                if (current_time - last_backup_time).total_seconds() >= self.config.backup_frequency:
                    await self.save_governance_state()
                    last_backup_time = current_time
                
                # Reset daily metrics at midnight
                if current_time.hour == 0 and current_time.minute == 0:
                    self.daily_pnl = 0.0
                    self.daily_trades = 0
                    logger.info("📅 Daily metrics reset")
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Governance loop error: {e}")
                await asyncio.sleep(10)
    
    async def emergency_procedures(self):
        """Execute emergency procedures if needed"""
        if self.config.emergency_stop:
            logger.critical("🚨 EXECUTING EMERGENCY STOP PROCEDURES")
            
            # Cancel all open orders
            try:
                orders = self.api.list_futures_orders(settle='usdt', status='open')
                for order in orders:
                    self.api.cancel_futures_order(settle='usdt', order_id=order.id)
                    logger.info(f"🛑 Emergency cancelled order: {order.id}")
            except Exception as e:
                logger.error(f"Emergency order cancellation failed: {e}")
            
            # Save emergency state
            await self.save_governance_state()
            
            logger.critical("🚨 EMERGENCY STOP COMPLETED")
    
    def set_emergency_stop(self, reason: str):
        """Manually trigger emergency stop"""
        self.config.emergency_stop = True
        alert = f"🚨 MANUAL EMERGENCY STOP: {reason}"
        logger.critical(alert)
        self.alerts.append(alert)
    
    async def start_governance(self):
        """Start the governance system"""
        # Load previous state
        await self.load_governance_state()
        
        # Start monitoring loop
        await self.governance_loop()

class GovernanceDashboard:
    """Simple dashboard for governance monitoring"""
    
    def __init__(self, governance: TradingGovernance):
        self.governance = governance
        
    async def show_status(self):
        """Show current governance status"""
        while True:
            metrics = await self.governance.calculate_metrics()
            positions = await self.governance.get_positions()
            account = await self.governance.get_account_status()
            health = await self.governance.monitor_system_health()
            
            print("\n" + "="*80)
            print(f"🏛️ TRADING GOVERNANCE DASHBOARD - {datetime.now().strftime('%H:%M:%S')}")
            print("="*80)
            print(f"🚦 System Health: {health}")
            print(f"💰 Account Balance: ${account.get('balance', 0):.2f}")
            print(f"📊 Available: ${account.get('available', 0):.2f}")
            print(f"💵 Unrealized PnL: ${account.get('unrealized_pnl', 0):+4f}")
            print(f"📈 Total Profit: ${metrics.total_profit:+.4f}")
            print(f"🎯 Win Rate: {metrics.win_rate:.1f}%")
            print(f"📊 Sharpe Ratio: {metrics.sharpe_ratio:.3f}")
            print(f"📋 Active Positions: {len(positions)}")
            
            if positions:
                print("\n📊 Current Positions:")
                for symbol, pos in positions.items():
                    side = "LONG" if pos['size'] > 0 else "SHORT"
                    print(f"   {symbol}: {side} {abs(pos['size']):.3f} @ ${pos['entry_price']:.4f} (PnL: ${pos['unrealized_pnl']:+.4f})")
            
            if self.governance.alerts:
                print(f"\n⚠️ Recent Alerts ({len(self.governance.alerts)}):")
                for alert in self.governance.alerts[-3:]:
                    print(f"   {alert}")
            
            print("="*80)
            
            await asyncio.sleep(30)  # Update every 30 seconds

async def main():
    """Main governance system"""
    print("🏛️ STARTING 24/7 TRADING GOVERNANCE SYSTEM")
    print("="*60)
    print("🤖 Robot Development Oversight")
    print("📊 Real-time Risk Management")
    print("🛡️ Automated Safety Controls")
    print("📋 Continuous Performance Monitoring")
    print("="*60)
    
    # Initialize governance system
    governance = TradingGovernance()
    
    # Start dashboard
    dashboard = GovernanceDashboard(governance)
    
    # Run governance and dashboard concurrently
    governance_task = asyncio.create_task(governance.start_governance())
    dashboard_task = asyncio.create_task(dashboard.show_status())
    
    try:
        await asyncio.gather(governance_task, dashboard_task)
    except KeyboardInterrupt:
        print("\n🏛️ Governance system stopped by user")
        await governance.save_governance_state()
    except Exception as e:
        print(f"\n❌ Governance system error: {e}")
        await governance.save_governance_state()

if __name__ == "__main__":
    asyncio.run(main())
