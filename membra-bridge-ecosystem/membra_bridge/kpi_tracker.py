"""
KPI Tracker Module - Advanced KPI tracking and arbitrage signal generation
Integrates with oracle system for real-time trading signals and market analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import json
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KPIData:
    """KPI measurement data"""
    name: str
    value: float
    timestamp: str
    source: str
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ArbitrageOpportunity:
    """Detected arbitrage opportunity"""
    id: str
    type: str
    profit_estimate: float
    confidence: float
    entry_point: str
    exit_point: str
    timestamp: str
    kpi_signals: Dict[str, str]
    risk_score: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AdvancedKPITracker:
    """Advanced KPI tracker with sophisticated signal generation"""
    
    def __init__(self):
        self.kpi_history: Dict[str, List[KPIData]] = defaultdict(list)
        self.signal_history: List[ArbitrageOpportunity] = []
        self.baseline_values: Dict[str, float] = {}
        self.kpi_configs = self._initialize_kpi_configs()
        
    def _initialize_kpi_configs(self) -> Dict:
        """Initialize KPI configurations with thresholds and weights"""
        return {
            # Price-based KPIs
            'price_momentum': {
                'weight': 0.15,
                'threshold_buy': 2.5,
                'threshold_sell': -2.0,
                'window': 3600,  # 1 hour
                'description': 'Rate of price change'
            },
            'price_volatility': {
                'weight': 0.12,
                'threshold_buy': 0.03,
                'threshold_sell': 0.08,
                'window': 1800,  # 30 minutes
                'description': 'Price variability'
            },
            'volume_surge': {
                'weight': 0.10,
                'threshold_buy': 1.8,
                'threshold_sell': 0.5,
                'window': 600,  # 10 minutes
                'description': 'Trading volume spike'
            },
            # Market Structure KPIs
            'liquidity_depth': {
                'weight': 0.08,
                'threshold_buy': 1000000,
                'threshold_sell': 100000,
                'window': 60,  # 1 minute
                'description': 'Available liquidity'
            },
            'order_book_imbalance': {
                'weight': 0.07,
                'threshold_buy': 0.6,
                'threshold_sell': 0.4,
                'window': 30,  # 30 seconds
                'description': 'Buy vs sell pressure'
            },
            'spread_tightness': {
                'weight': 0.06,
                'threshold_buy': 0.001,
                'threshold_sell': 0.01,
                'window': 30,
                'description': 'Bid-ask spread'
            },
            # Cross-chain KPIs
            'cross_chain_premium': {
                'weight': 0.10,
                'threshold_buy': 0.03,
                'threshold_sell': -0.02,
                'window': 120,
                'description': 'Price difference across chains'
            },
            'bridge_congestion': {
                'weight': 0.05,
                'threshold_buy': 0.3,
                'threshold_sell': 0.8,
                'window': 60,
                'description': 'Network congestion level'
            },
            # Sentiment KPIs
            'social_sentiment': {
                'weight': 0.08,
                'threshold_buy': 0.7,
                'threshold_sell': 0.3,
                'window': 1800,
                'description': 'Social media sentiment'
            },
            'news_sentiment': {
                'weight': 0.06,
                'threshold_buy': 0.65,
                'threshold_sell': 0.35,
                'window': 3600,
                'description': 'News sentiment analysis'
            },
            # On-chain KPIs
            'whale_activity': {
                'weight': 0.07,
                'threshold_buy': 1000000,
                'threshold_sell': 500000,
                'window': 300,
                'description': 'Large transaction activity'
            },
            'exchange_flow': {
                'weight': 0.06,
                'threshold_buy': -0.05,
                'threshold_sell': 0.05,
                'window': 600,
                'description': 'Token flow to/from exchanges'
            }
        }
    
    def add_kpi_measurement(self, name: str, value: float, source: str = "system", metadata: Dict = None):
        """Add a KPI measurement"""
        metadata = metadata or {}
        
        kpi_data = KPIData(
            name=name,
            value=value,
            timestamp=datetime.now().isoformat(),
            source=source,
            metadata=metadata
        )
        
        self.kpi_history[name].append(kpi_data)
        
        # Trim old data based on window
        window = self.kpi_configs.get(name, {}).get('window', 3600)
        cutoff_time = datetime.now() - timedelta(seconds=window)
        self.kpi_history[name] = [
            kpi for kpi in self.kpi_history[name]
            if datetime.fromisoformat(kpi.timestamp) > cutoff_time
        ]
        
        # Update baseline if we have enough data
        if len(self.kpi_history[name]) > 10:
            values = [kpi.value for kpi in self.kpi_history[name]]
            self.baseline_values[name] = statistics.mean(values)
    
    def calculate_kpi_score(self, name: str) -> Tuple[float, str]:
        """Calculate KPI score and generate signal"""
        if name not in self.kpi_history or not self.kpi_history[name]:
            return 0.0, 'hold'
        
        config = self.kpi_configs.get(name, {})
        recent_value = self.kpi_history[name][-1].value
        
        # Calculate deviation from baseline
        baseline = self.baseline_values.get(name, recent_value)
        if baseline != 0:
            deviation = (recent_value - baseline) / baseline
        else:
            deviation = 0.0
        
        # Generate signal based on thresholds
        threshold_buy = config.get('threshold_buy', 0)
        threshold_sell = config.get('threshold_sell', 0)
        
        if deviation > threshold_buy:
            signal = 'buy'
            confidence = min(0.95, abs(deviation) / threshold_buy)
        elif deviation < threshold_sell:
            signal = 'sell'
            confidence = min(0.95, abs(deviation) / abs(threshold_sell))
        else:
            signal = 'hold'
            confidence = 0.5
        
        # Apply weight
        weighted_score = deviation * config.get('weight', 0.1)
        
        return weighted_score, signal
    
    def calculate_composite_signal(self) -> Dict:
        """Calculate composite trading signal from all KPIs"""
        signals = {}
        total_weight = 0.0
        weighted_sum = 0.0
        
        for name in self.kpi_configs.keys():
            score, signal = self.calculate_kpi_score(name)
            weight = self.kpi_configs[name].get('weight', 0.1)
            
            signals[name] = {
                'signal': signal,
                'score': score,
                'weight': weight,
                'confidence': self.kpi_configs[name].get('threshold_buy', 0)
            }
            
            total_weight += weight
            weighted_sum += score
        
        # Calculate overall signal
        if total_weight > 0:
            overall_score = weighted_sum / total_weight
        else:
            overall_score = 0.0
        
        if overall_score > 0.15:
            overall_signal = 'strong_buy'
        elif overall_score > 0.05:
            overall_signal = 'buy'
        elif overall_score < -0.15:
            overall_signal = 'strong_sell'
        elif overall_score < -0.05:
            overall_signal = 'sell'
        else:
            overall_signal = 'hold'
        
        return {
            'overall_signal': overall_signal,
            'overall_score': overall_score,
            'individual_signals': signals,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """Detect arbitrage opportunities based on KPI signals"""
        opportunities = []
        composite_signal = self.calculate_composite_signal()
        
        # Cross-chain arbitrage
        cross_chain_premium = self.kpi_history.get('cross_chain_premium', [])
        if cross_chain_premium:
            latest_premium = cross_chain_premium[-1].value
            if latest_premium > 0.03:  # 3% premium threshold
                opportunity = ArbitrageOpportunity(
                    id=hashlib.sha256(f"cross_chain_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                    type='cross_chain_arbitrage',
                    profit_estimate=latest_premium * 100,  # Convert to percentage
                    confidence=min(0.9, latest_premium / 0.05),
                    entry_point='low_premium_chain',
                    exit_point='high_premium_chain',
                    timestamp=datetime.now().isoformat(),
                    kpi_signals={'cross_chain_premium': 'buy'},
                    risk_score=self._calculate_risk_score(composite_signal)
                )
                opportunities.append(opportunity)
        
        # Liquidity arbitrage
        liquidity_depth = self.kpi_history.get('liquidity_depth', [])
        spread_tightness = self.kpi_history.get('spread_tightness', [])
        
        if liquidity_depth and spread_tightness:
            latest_liquidity = liquidity_depth[-1].value
            latest_spread = spread_tightness[-1].value
            
            if latest_liquidity > 500000 and latest_spread < 0.002:
                opportunity = ArbitrageOpportunity(
                    id=hashlib.sha256(f"liquidity_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                    type='liquidity_arbitrage',
                    profit_estimate=(0.002 - latest_spread) * 1000,
                    confidence=0.7,
                    entry_point='tight_spread_exchange',
                    exit_point='wide_spread_exchange',
                    timestamp=datetime.now().isoformat(),
                    kpi_signals={'liquidity_depth': 'buy', 'spread_tightness': 'buy'},
                    risk_score=self._calculate_risk_score(composite_signal)
                )
                opportunities.append(opportunity)
        
        # Sentiment-based arbitrage
        social_sentiment = self.kpi_history.get('social_sentiment', [])
        price_momentum = self.kpi_history.get('price_momentum', [])
        
        if social_sentiment and price_momentum:
            latest_sentiment = social_sentiment[-1].value
            latest_momentum = price_momentum[-1].value
            
            if latest_sentiment > 0.8 and latest_momentum < 1.0:
                opportunity = ArbitrageOpportunity(
                    id=hashlib.sha256(f"sentiment_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
                    type='sentiment_arbitrage',
                    profit_estimate=abs(latest_momentum) * 50,
                    confidence=0.6,
                    entry_point='contrarian_position',
                    exit_point='momentum_follow',
                    timestamp=datetime.now().isoformat(),
                    kpi_signals={'social_sentiment': 'sell', 'price_momentum': 'buy'},
                    risk_score=self._calculate_risk_score(composite_signal)
                )
                opportunities.append(opportunity)
        
        # Store opportunities
        self.signal_history.extend(opportunities)
        
        # Keep only recent opportunities
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.signal_history = [
            opp for opp in self.signal_history
            if datetime.fromisoformat(opp.timestamp) > cutoff_time
        ]
        
        return opportunities
    
    def _calculate_risk_score(self, composite_signal: Dict) -> float:
        """Calculate risk score based on composite signal"""
        volatility = self.kpi_history.get('price_volatility', [])
        if volatility:
            latest_volatility = volatility[-1].value
            # Higher volatility = higher risk
            return min(1.0, latest_volatility * 10)
        return 0.5
    
    def get_kpi_summary(self) -> Dict:
        """Get summary of all KPIs"""
        summary = {}
        
        for name, config in self.kpi_configs.items():
            history = self.kpi_history.get(name, [])
            if history:
                latest = history[-1]
                score, signal = self.calculate_kpi_score(name)
                
                summary[name] = {
                    'current_value': latest.value,
                    'signal': signal,
                    'score': score,
                    'weight': config['weight'],
                    'description': config['description'],
                    'timestamp': latest.timestamp
                }
            else:
                summary[name] = {
                    'status': 'no_data',
                    'description': config['description']
                }
        
        return summary
    
    def export_kpi_data(self, hours: int = 24) -> Dict:
        """Export KPI data for analysis"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        export_data = {}
        
        for name, history in self.kpi_history.items():
            filtered_history = [
                kpi for kpi in history
                if datetime.fromisoformat(kpi.timestamp) > cutoff_time
            ]
            
            export_data[name] = [kpi.to_dict() for kpi in filtered_history]
        
        return {
            'export_timestamp': datetime.now().isoformat(),
            'time_range_hours': hours,
            'kpi_data': export_data,
            'baseline_values': self.baseline_values
        }


class ArbitrageEngine:
    """Main arbitrage engine coordinating KPI tracking and signal generation"""
    
    def __init__(self, kpi_tracker: AdvancedKPITracker):
        self.kpi_tracker = kpi_tracker
        self.active_opportunities: List[ArbitrageOpportunity] = []
        self.executed_trades: List[Dict] = []
    
    async def analyze_market(self, market_data: Dict) -> Dict:
        """Analyze market data and generate arbitrage signals"""
        # Extract KPIs from market data
        for kpi_name, kpi_value in market_data.items():
            if isinstance(kpi_value, (int, float)):
                self.kpi_tracker.add_kpi_measurement(kpi_name, kpi_value)
        
        # Calculate composite signal
        composite_signal = self.kpi_tracker.calculate_composite_signal()
        
        # Detect arbitrage opportunities
        opportunities = self.kpi_tracker.detect_arbitrage_opportunities()
        
        # Update active opportunities
        self.active_opportunities = opportunities
        
        return {
            'composite_signal': composite_signal,
            'arbitrage_opportunities': [opp.to_dict() for opp in opportunities],
            'kpi_summary': self.kpi_tracker.get_kpi_summary(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_top_opportunity(self) -> Optional[ArbitrageOpportunity]:
        """Get the top arbitrage opportunity by confidence"""
        if not self.active_opportunities:
            return None
        
        return max(self.active_opportunities, key=lambda x: x.confidence)
    
    def execute_opportunity(self, opportunity_id: str) -> Dict:
        """Execute an arbitrage opportunity (placeholder for actual execution)"""
        opportunity = next(
            (opp for opp in self.active_opportunities if opp.id == opportunity_id),
            None
        )
        
        if not opportunity:
            return {'error': 'Opportunity not found'}
        
        # In production, this would execute the actual trade
        trade_record = {
            'opportunity_id': opportunity_id,
            'type': opportunity.type,
            'executed_at': datetime.now().isoformat(),
            'status': 'executed',
            'estimated_profit': opportunity.profit_estimate
        }
        
        self.executed_trades.append(trade_record)
        
        return trade_record


def main():
    """Example usage"""
    # Initialize KPI tracker
    kpi_tracker = AdvancedKPITracker()
    arbitrage_engine = ArbitrageEngine(kpi_tracker)
    
    # Simulate market data
    market_data = {
        'price_momentum': 3.5,
        'price_volatility': 0.04,
        'volume_surge': 2.1,
        'liquidity_depth': 1500000,
        'order_book_imbalance': 0.65,
        'spread_tightness': 0.0015,
        'cross_chain_premium': 0.035,
        'bridge_congestion': 0.25,
        'social_sentiment': 0.75,
        'news_sentiment': 0.7,
        'whale_activity': 1200000,
        'exchange_flow': -0.03
    }
    
    # Analyze market
    analysis = asyncio.run(arbitrage_engine.analyze_market(market_data))
    
    print("=== Market Analysis ===")
    print(json.dumps(analysis, indent=2))
    
    # Get top opportunity
    top_opportunity = arbitrage_engine.get_top_opportunity()
    if top_opportunity:
        print(f"\n=== Top Opportunity ===")
        print(json.dumps(top_opportunity.to_dict(), indent=2))


if __name__ == '__main__':
    main()