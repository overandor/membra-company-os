#!/usr/bin/env python3
"""
AI CONTROL CENTER
Self-Developing Trading System with Full Autonomous Control
"""

import asyncio
import json
import time
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import gate_api
from gate_api import ApiClient, Configuration, FuturesApi
import requests
import hashlib
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AIState:
    """AI system state and memory"""
    learning_rate: float = 0.01
    confidence_threshold: float = 0.75
    risk_tolerance: float = 0.02
    adaptation_speed: float = 0.1
    memory_size: int = 1000
    current_strategy: str = "conservative"
    performance_score: float = 0.0
    evolution_count: int = 0
    last_optimization: str = ""
    
@dataclass
class TradingDecision:
    """AI trading decision structure"""
    action: str  # buy, sell, hold, close
    symbol: str
    size: float
    price: Optional[float]
    confidence: float
    reasoning: str
    expected_profit: float
    risk_level: str  # low, medium, high
    timestamp: str

class AILearningEngine:
    """Self-learning and adaptation engine"""
    
    def __init__(self):
        self.trade_history: List[Dict] = []
        self.strategy_performance: Dict[str, float] = {}
        self.market_patterns: List[Dict] = []
        self.adaptation_history: List[Dict] = []
        
    def analyze_performance(self, trades: List[Dict]) -> Dict:
        """Analyze recent trading performance"""
        if not trades:
            return {'score': 0.0, 'insights': []}
        
        # Calculate performance metrics
        profits = [t.get('profit', 0) for t in trades]
        win_rate = sum(1 for p in profits if p > 0) / len(profits) if profits else 0
        avg_profit = np.mean(profits) if profits else 0
        sharpe_ratio = np.mean(profits) / (np.std(profits) + 1e-6) if len(profits) > 1 else 0
        
        # Generate insights
        insights = []
        if win_rate < 0.5:
            insights.append("Low win rate detected - strategy adjustment needed")
        if avg_profit < 0:
            insights.append("Negative average profit - risk management review required")
        if sharpe_ratio < 1.0:
            insights.append("Low risk-adjusted returns - optimization needed")
        
        performance_score = (win_rate * 0.4 + min(avg_profit * 100, 1) * 0.3 + min(sharpe_ratio / 2, 1) * 0.3)
        
        return {
            'score': performance_score,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'sharpe_ratio': sharpe_ratio,
            'insights': insights
        }
    
    def adapt_strategy(self, current_state: AIState, performance: Dict) -> AIState:
        """Adapt AI strategy based on performance"""
        new_state = AIState(**asdict(current_state))
        
        # Adapt learning rate
        if performance['score'] < 0.5:
            new_state.learning_rate = min(current_state.learning_rate * 1.1, 0.1)
        elif performance['score'] > 0.8:
            new_state.learning_rate = max(current_state.learning_rate * 0.9, 0.001)
        
        # Adapt risk tolerance
        if performance['win_rate'] < 0.4:
            new_state.risk_tolerance = max(current_state.risk_tolerance * 0.9, 0.01)
        elif performance['win_rate'] > 0.6:
            new_state.risk_tolerance = min(current_state.risk_tolerance * 1.05, 0.05)
        
        # Adapt confidence threshold
        if performance['avg_profit'] < 0:
            new_state.confidence_threshold = min(current_state.confidence_threshold * 1.05, 0.95)
        elif performance['avg_profit'] > 0:
            new_state.confidence_threshold = max(current_state.confidence_threshold * 0.95, 0.6)
        
        # Update strategy
        if performance['score'] < 0.3:
            new_state.current_strategy = "conservative"
        elif performance['score'] > 0.7:
            new_state.current_strategy = "aggressive"
        else:
            new_state.current_strategy = "balanced"
        
        new_state.evolution_count += 1
        new_state.last_optimization = datetime.now().isoformat()
        new_state.performance_score = performance['score']
        
        return new_state
    
    def learn_from_market(self, market_data: Dict) -> List[str]:
        """Learn patterns from market data"""
        patterns = []
        
        # Analyze volatility patterns
        if 'price_changes' in market_data:
            volatility = np.std(market_data['price_changes'])
            if volatility > 0.02:
                patterns.append("High volatility detected - reduce position sizes")
            elif volatility < 0.005:
                patterns.append("Low volatility - increase position sizes")
        
        # Analyze trend patterns
        if 'prices' in market_data and len(market_data['prices']) > 10:
            prices = market_data['prices'][-10:]
            trend = np.polyfit(range(len(prices)), prices, 1)[0]
            if trend > 0:
                patterns.append("Uptrend detected - favor long positions")
            elif trend < 0:
                patterns.append("Downtrend detected - favor short positions")
        
        return patterns

class AIControlCenter:
    """Main AI Control Center for autonomous trading"""
    
    def __init__(self):
        self.state = AIState()
        self.learning_engine = AILearningEngine()
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        
        # Initialize API
        cfg = Configuration(key=self.api_key, secret=self.api_secret)
        self.api = FuturesApi(ApiClient(cfg))
        
        # AI Memory
        self.decisions: List[TradingDecision] = []
        self.market_memory: List[Dict] = []
        self.performance_history: List[Dict] = []
        
        # Autonomous control flags
        self.autonomous_mode = True
        self.self_improvement_enabled = True
        self.risk_management_active = True
        
        logger.info("🧠 AI Control Center initialized")
        logger.info(f"🤖 Autonomous Mode: {self.autonomous_mode}")
        logger.info(f"📚 Self-Improvement: {self.self_improvement_enabled}")
        logger.info(f"🛡️ Risk Management: {self.risk_management_active}")
    
    async def get_market_data(self, symbol: str = "ENA_USDT") -> Dict:
        """Get comprehensive market data for AI analysis"""
        try:
            # Get order book
            book = self.api.list_futures_order_book(settle='usdt', contract=symbol, limit=20)
            
            # Get recent trades (if available)
            # Note: This would need additional API endpoints
            
            # Get positions
            positions = self.api.list_positions(settle='usdt')
            ena_positions = [p for p in positions if p.contract == symbol and float(p.size) != 0]
            
            # Process order book
            if book.bids and book.asks:
                bids = [[float(b.p), float(b.s)] for b in book.bids]
                asks = [[float(a.p), float(a.s)] for a in book.asks]
                
                mid_price = (bids[0][0] + asks[0][0]) / 2
                spread_bps = (asks[0][0] - bids[0][0]) / mid_price * 10000
                
                # Calculate market depth
                bid_depth = sum(b[1] for b in bids[:5])
                ask_depth = sum(a[1] for a in asks[:5])
                imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
                
                return {
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat(),
                    'bids': bids,
                    'asks': asks,
                    'mid_price': mid_price,
                    'spread_bps': spread_bps,
                    'bid_depth': bid_depth,
                    'ask_depth': ask_depth,
                    'imbalance': imbalance,
                    'positions': ena_positions,
                    'market_sentiment': 'bullish' if imbalance > 0.1 else 'bearish' if imbalance < -0.1 else 'neutral'
                }
        except Exception as e:
            logger.error(f"Market data error: {e}")
        
        return {}
    
    def analyze_market_conditions(self, market_data: Dict) -> Dict:
        """AI analysis of market conditions"""
        if not market_data:
            return {'decision': 'hold', 'confidence': 0.0, 'reasoning': 'No market data'}
        
        analysis = {
            'volatility': 'normal',
            'trend': 'neutral',
            'liquidity': 'good',
            'opportunity_score': 0.0,
            'risk_factors': []
        }
        
        # Analyze spread
        spread = market_data.get('spread_bps', 0)
        if spread < 5:
            analysis['liquidity'] = 'excellent'
            analysis['opportunity_score'] += 0.3
        elif spread > 20:
            analysis['liquidity'] = 'poor'
            analysis['risk_factors'].append('Wide spread')
        
        # Analyze order book imbalance
        imbalance = market_data.get('imbalance', 0)
        if imbalance > 0.2:
            analysis['trend'] = 'bullish'
            analysis['opportunity_score'] += 0.2
        elif imbalance < -0.2:
            analysis['trend'] = 'bearish'
            analysis['opportunity_score'] += 0.2
        
        # Analyze positions
        positions = market_data.get('positions', [])
        if positions:
            total_position = sum(float(p.size) for p in positions)
            if abs(total_position) > 10:
                analysis['risk_factors'].append('Large position exposure')
        
        return analysis
    
    def make_trading_decision(self, market_data: Dict, analysis: Dict) -> TradingDecision:
        """AI makes autonomous trading decision"""
        current_time = datetime.now().isoformat()
        
        # Calculate decision confidence
        base_confidence = 0.5
        if analysis['opportunity_score'] > 0.5:
            base_confidence += 0.2
        if analysis['liquidity'] == 'excellent':
            base_confidence += 0.1
        if not analysis['risk_factors']:
            base_confidence += 0.1
        
        # Adjust confidence based on AI state
        confidence = base_confidence * (1 + self.state.performance_score * 0.2)
        confidence = min(confidence, 0.95)
        
        # Decision logic
        action = 'hold'
        size = 0.0
        price = None
        reasoning = ""
        expected_profit = 0.0
        risk_level = 'low'
        
        if confidence > self.state.confidence_threshold:
            if analysis['trend'] == 'bullish' and analysis['opportunity_score'] > 0.4:
                action = 'buy'
                size = min(5.0, max(1.0, self.state.risk_tolerance * 100))
                price = market_data['bids'][0][0] if market_data.get('bids') else None
                reasoning = f"Bullish trend with {analysis['opportunity_score']:.2f} opportunity score"
                expected_profit = size * 0.002  # 0.2% expected profit
                risk_level = 'medium'
                
            elif analysis['trend'] == 'bearish' and analysis['opportunity_score'] > 0.4:
                action = 'sell'
                size = min(5.0, max(1.0, self.state.risk_tolerance * 100))
                price = market_data['asks'][0][0] if market_data.get('asks') else None
                reasoning = f"Bearish trend with {analysis['opportunity_score']:.2f} opportunity score"
                expected_profit = size * 0.002  # 0.2% expected profit
                risk_level = 'medium'
        
        # Adjust based on strategy
        if self.state.current_strategy == 'conservative':
            size *= 0.5
            risk_level = 'low'
        elif self.state.current_strategy == 'aggressive':
            size *= 1.5
            risk_level = 'high'
        
        decision = TradingDecision(
            action=action,
            symbol=market_data.get('symbol', 'ENA_USDT'),
            size=size,
            price=price,
            confidence=confidence,
            reasoning=reasoning,
            expected_profit=expected_profit,
            risk_level=risk_level,
            timestamp=current_time
        )
        
        return decision
    
    async def execute_decision(self, decision: TradingDecision) -> bool:
        """Execute AI trading decision"""
        if decision.action == 'hold':
            return True
        
        if not self.autonomous_mode:
            logger.info(f"🤖 AI Decision (DRY RUN): {decision.action} {decision.size} {decision.symbol}")
            return True
        
        try:
            # Create order payload
            order_payload = {
                'contract': decision.symbol,
                'size': decision.size,
                'price': str(decision.price) if decision.price else None,
                'type': 'limit' if decision.price else 'market',
                'time_in_force': 'post_only' if decision.price else 'ioc'
            }
            
            if decision.action == 'buy':
                order_payload['side'] = 'buy'
            elif decision.action == 'sell':
                order_payload['side'] = 'sell'
            
            # Execute order
            result = self.api.create_futures_order(settle='usdt', **order_payload)
            
            logger.info(f"🤖 AI Executed: {decision.action.upper()} {decision.size} {decision.symbol} @ {decision.price}")
            logger.info(f"🧠 Reasoning: {decision.reasoning}")
            logger.info(f"📊 Confidence: {decision.confidence:.2f} | Expected Profit: ${decision.expected_profit:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ AI Execution failed: {e}")
            return False
    
    async def self_improvement_cycle(self):
        """AI self-improvement and learning cycle"""
        if not self.self_improvement_enabled:
            return
        
        # Analyze recent performance
        recent_decisions = self.decisions[-50:] if len(self.decisions) >= 50 else self.decisions
        if recent_decisions:
            # Simulate performance analysis (would track actual results)
            performance = self.learning_engine.analyze_performance([])
            
            # Adapt strategy
            old_state = AIState(**asdict(self.state))
            self.state = self.learning_engine.adapt_strategy(self.state, performance)
            
            if self.state.evolution_count > old_state.evolution_count:
                logger.info(f"🧠 AI EVOLUTION #{self.state.evolution_count}")
                logger.info(f"📊 Performance Score: {performance['score']:.3f}")
                logger.info(f"🎯 Strategy: {old_state.current_strategy} → {self.state.current_strategy}")
                logger.info(f"⚡ Learning Rate: {old_state.learning_rate:.4f} → {self.state.learning_rate:.4f}")
                logger.info(f"🛡️ Risk Tolerance: {old_state.risk_tolerance:.4f} → {self.state.risk_tolerance:.4f}")
    
    async def autonomous_control_loop(self):
        """Main autonomous control loop"""
        logger.info("🚀 AI Autonomous Control Loop Started")
        
        while True:
            try:
                # Get market data
                market_data = await self.get_market_data()
                
                if market_data:
                    # Store in memory
                    self.market_memory.append(market_data)
                    if len(self.market_memory) > self.state.memory_size:
                        self.market_memory = self.market_memory[-self.state.memory_size:]
                    
                    # Analyze market
                    analysis = self.analyze_market_conditions(market_data)
                    
                    # Make decision
                    decision = self.make_trading_decision(market_data, analysis)
                    
                    # Store decision
                    self.decisions.append(decision)
                    if len(self.decisions) > 1000:
                        self.decisions = self.decisions[-1000:]
                    
                    # Execute decision
                    success = await self.execute_decision(decision)
                    
                    if success and decision.action != 'hold':
                        logger.info(f"🤖 AI Decision: {decision.action.upper()} {decision.size} {decision.symbol}")
                        logger.info(f"🧠 Confidence: {decision.confidence:.2f} | Risk: {decision.risk_level}")
                        logger.info(f"💭 Reasoning: {decision.reasoning}")
                
                # Self-improvement cycle
                await self.self_improvement_cycle()
                
                # Control loop interval
                await asyncio.sleep(5)  # Analyze every 5 seconds
                
            except Exception as e:
                logger.error(f"🚨 AI Control Loop Error: {e}")
                await asyncio.sleep(10)
    
    def save_ai_state(self):
        """Save AI state and memory"""
        try:
            ai_state = {
                'state': asdict(self.state),
                'decisions': [asdict(d) for d in self.decisions[-100:]],
                'market_memory': self.market_memory[-50:],
                'performance_history': self.performance_history,
                'timestamp': datetime.now().isoformat()
            }
            
            with open('/Users/alep/Downloads/ai_state.json', 'w') as f:
                json.dump(ai_state, f, indent=2)
            
            logger.info("💾 AI State saved")
        except Exception as e:
            logger.error(f"Failed to save AI state: {e}")
    
    def load_ai_state(self):
        """Load previous AI state"""
        try:
            with open('/Users/alep/Downloads/ai_state.json', 'r') as f:
                ai_state = json.load(f)
            
            self.state = AIState(**ai_state['state'])
            self.decisions = [TradingDecision(**d) for d in ai_state.get('decisions', [])]
            self.market_memory = ai_state.get('market_memory', [])
            self.performance_history = ai_state.get('performance_history', [])
            
            logger.info("📂 AI State loaded")
            logger.info(f"🧠 Evolution Count: {self.state.evolution_count}")
            logger.info(f"📊 Performance Score: {self.state.performance_score:.3f}")
            
        except FileNotFoundError:
            logger.info("No previous AI state found - starting fresh")
        except Exception as e:
            logger.error(f"Failed to load AI state: {e}")
    
    def set_autonomous_mode(self, enabled: bool):
        """Enable/disable autonomous trading"""
        self.autonomous_mode = enabled
        status = "ENABLED" if enabled else "DISABLED"
        logger.info(f"🤖 Autonomous Trading {status}")
    
    def emergency_stop(self):
        """Emergency stop all AI operations"""
        self.autonomous_mode = False
        self.self_improvement_enabled = False
        logger.critical("🚨 AI EMERGENCY STOP ACTIVATED")
        self.save_ai_state()

async def main():
    """Main AI Control Center"""
    print("🧠 AI CONTROL CENTER - SELF-DEVELOPING TRADING SYSTEM")
    print("="*70)
    print("🤖 Full Autonomous Control")
    print("📚 Self-Improvement Engine")
    print("🛡️ Risk Management")
    print("🧠 Learning & Adaptation")
    print("="*70)
    
    # Initialize AI Control Center
    ai_control = AIControlCenter()
    
    # Load previous state
    ai_control.load_ai_state()
    
    # Start autonomous control
    try:
        await ai_control.autonomous_control_loop()
    except KeyboardInterrupt:
        print("\n🧠 AI Control Center stopped by user")
        ai_control.save_ai_state()
    except Exception as e:
        print(f"\n❌ AI Control Center error: {e}")
        ai_control.emergency_stop()

if __name__ == "__main__":
    asyncio.run(main())
