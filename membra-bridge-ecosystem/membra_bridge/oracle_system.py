"""
Oracle System Module - 30+ endpoint integration for price discovery and KPI tracking
Builds on existing MEMBRA finance oracle infrastructure with expanded endpoints.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import hashlib
from collections import defaultdict
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OracleEndpoint:
    """Configuration for an oracle endpoint"""
    name: str
    url: str
    category: str
    enabled: bool
    weight: float
    timeout: int = 30
    api_key: Optional[str] = None
    params: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class OracleDataPoint:
    """Single data point from oracle"""
    source: str
    timestamp: str
    value: float
    metadata: Dict
    confidence: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class KPISignal:
    """KPI signal for arbitrage"""
    name: str
    value: float
    threshold: float
    signal: str  # 'buy', 'sell', 'hold'
    confidence: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class OracleSystem:
    """Main oracle system with 30+ endpoints"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.endpoints: List[OracleEndpoint] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Tuple[OracleDataPoint, datetime]] = {}
        self.cache_ttl = timedelta(seconds=60)
        self.historical_data: Dict[str, List[OracleDataPoint]] = defaultdict(list)
        
        self._initialize_endpoints()
    
    def _initialize_endpoints(self):
        """Initialize all 30+ oracle endpoints"""
        
        # Cryptocurrency/Blockchain Endpoints (12)
        crypto_endpoints = [
            OracleEndpoint("coingecko_trending", "https://api.coingecko.com/api/v3/search/trending", 
                          "crypto", True, 1.0),
            OracleEndpoint("coingecko_price", "https://api.coingecko.com/api/v3/simple/price", 
                          "crypto", True, 1.0, params={"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd"}),
            OracleEndpoint("dexscreener_latest", "https://api.dexscreener.com/latest/v1/pairs", 
                          "crypto", True, 0.9),
            OracleEndpoint("gateio_tickers", "https://api.gate.io/api/v4/spot/tickers", 
                          "crypto", True, 0.9),
            OracleEndpoint("binance_ticker", "https://api.binance.com/api/v3/ticker/24hr", 
                          "crypto", True, 0.9),
            OracleEndpoint("kraken_ticker", "https://api.kraken.com/0/public/Ticker", 
                          "crypto", True, 0.8),
            OracleEndpoint("coinpaprika_tickers", "https://api.coinpaprika.com/v1/tickers", 
                          "crypto", True, 0.8),
            OracleEndpoint("messari_metrics", "https://data.messari.io/api/v1/assets", 
                          "crypto", True, 0.8, params={"fields": "name,symbol,metrics"}),
            OracleEndpoint("jupiter_tokens", "https://token.jup.ag/all", 
                          "crypto", True, 0.7),
            OracleEndpoint("birdeye_markets", "https://public-api.birdeye.so/defi/markets", 
                          "crypto", True, 0.7),
            OracleEndpoint("solana_rpc", "https://api.mainnet-beta.solana.com", 
                          "crypto", True, 0.6),
            OracleEndpoint("ethereum_rpc", "https://eth.llamarpc.com", 
                          "crypto", True, 0.6),
        ]
        
        # Traditional Finance Endpoints (8)
        tradfi_endpoints = [
            OracleEndpoint("alpha_vantage", "https://www.alphavantage.co/query", 
                          "tradfi", True, 0.9, params={"function": "GLOBAL_QUOTE", "symbol": "IBM"}),
            OracleEndpoint("yahoo_finance", "https://query1.finance.yahoo.com/v8/finance/chart/", 
                          "tradfi", True, 0.8),
            OracleEndpoint("iex_cloud", "https://cloud.iexapis.com/stable/stock/", 
                          "tradfi", True, 0.7),
            OracleEndpoint("finnhub", "https://finnhub.io/api/v1/quote", 
                          "tradfi", True, 0.7),
            OracleEndpoint("polygon_io", "https://api.polygon.io/v2/aggs/ticker/", 
                          "tradfi", True, 0.7),
            OracleEndpoint("marketstack", "https://api.marketstack.com/v1/eod", 
                          "tradfi", True, 0.6),
            OracleEndpoint("twelvedata", "https://api.twelvedata.com/price", 
                          "tradfi", True, 0.6),
            OracleEndpoint("federal_reserve", "https://api.federalreserve.gov/v1/fedservices/daily/", 
                          "tradfi", True, 0.5),
        ]
        
        # DeFi/DEX Endpoints (5)
        defi_endpoints = [
            OracleEndpoint("uniswap_v3", "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3", 
                          "defi", True, 0.8),
            OracleEndpoint("curve_finance", "https://api.curve.fi/v1/getPools/all", 
                          "defi", True, 0.7),
            OracleEndpoint("sushiswap", "https://api.sushi.com/price", 
                          "defi", True, 0.7),
            OracleEndpoint("balancer", "https://api.balancer.fi/v1/pools", 
                          "defi", True, 0.6),
            OracleEndpoint("aave", "https://aave-api-v2.aave.com/data/markets", 
                          "defi", True, 0.6),
        ]
        
        # Social/Sentiment Endpoints (3)
        social_endpoints = [
            OracleEndpoint("twitter_api", "https://api.twitter.com/2/tweets/search/recent", 
                          "social", True, 0.7),
            OracleEndpoint("reddit_api", "https://www.reddit.com/r/cryptocurrency/new.json", 
                          "social", True, 0.6),
            OracleEndpoint("discord_api", "https://discord.com/api/v10", 
                          "social", True, 0.5),
        ]
        
        # GitHub/Development Endpoints (2)
        github_endpoints = [
            OracleEndpoint("github_trending", "https://api.github.com/search/repositories", 
                          "github", True, 0.7, params={"q": "stars:>1000", "sort": "stars"}),
            OracleEndpoint("github_events", "https://api.github.com/events", 
                          "github", True, 0.6),
        ]
        
        # Network/Infrastructure Endpoints (2)
        network_endpoints = [
            OracleEndpoint("gas_price_oracle", "https://ethgasstation.info/api/ethgasAPI.json", 
                          "network", True, 0.8),
            OracleEndpoint("network_stats", "https://api.blockchain.info/stats", 
                          "network", True, 0.7),
        ]
        
        # Commodity/Real World Endpoints (2)
        commodity_endpoints = [
            OracleEndpoint("metals_api", "https://metals-api.com/api/latest", 
                          "commodity", True, 0.7),
            OracleEndpoint("oil_prices", "https://api.oilpriceapi.com/v1/prices/latest", 
                          "commodity", True, 0.6),
        ]
        
        # Combine all endpoints
        self.endpoints = (
            crypto_endpoints + tradfi_endpoints + defi_endpoints + 
            social_endpoints + github_endpoints + network_endpoints + commodity_endpoints
        )
        
        logger.info(f"Initialized {len(self.endpoints)} oracle endpoints")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_endpoint(self, endpoint: OracleEndpoint) -> Optional[OracleDataPoint]:
        """Fetch data from a single endpoint"""
        cache_key = f"{endpoint.name}:{endpoint.url}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if datetime.now() - cache_time < self.cache_ttl:
                return cached_data
        
        try:
            headers = {}
            if endpoint.api_key:
                headers['Authorization'] = f'Bearer {endpoint.api_key}'
            
            params = endpoint.params or {}
            
            async with self.session.get(endpoint.url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract numeric value based on endpoint type
                    value = self._extract_value(endpoint.name, data)
                    
                    if value is not None:
                        data_point = OracleDataPoint(
                            source=endpoint.name,
                            timestamp=datetime.now().isoformat(),
                            value=value,
                            metadata={'category': endpoint.category, 'raw_data': str(data)[:500]},
                            confidence=endpoint.weight
                        )
                        
                        # Update cache
                        self.cache[cache_key] = (data_point, datetime.now())
                        
                        # Store historical data
                        self.historical_data[endpoint.name].append(data_point)
                        
                        return data_point
                else:
                    logger.warning(f"Endpoint {endpoint.name} returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching {endpoint.name}: {e}")
        
        return None
    
    def _extract_value(self, endpoint_name: str, data: Dict) -> Optional[float]:
        """Extract numeric value from endpoint response"""
        try:
            # Different endpoints have different response structures
            if endpoint_name == "coingecko_price":
                if 'bitcoin' in data and 'usd' in data['bitcoin']:
                    return float(data['bitcoin']['usd'])
            elif endpoint_name == "binance_ticker":
                if isinstance(data, list) and len(data) > 0:
                    return float(data[0].get('lastPrice', 0))
            elif endpoint_name == "gas_price_oracle":
                return float(data.get('fast', 0))
            elif endpoint_name == "network_stats":
                return float(data.get('market_price_usd', 0))
            
            # Generic extraction - try to find first numeric value
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        return float(value)
            elif isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    for key, value in data[0].items():
                        if isinstance(value, (int, float)):
                            return float(value)
                elif isinstance(data[0], (int, float)):
                    return float(data[0])
            
        except Exception as e:
            logger.error(f"Error extracting value from {endpoint_name}: {e}")
        
        return None
    
    async def fetch_all_endpoints(self) -> List[OracleDataPoint]:
        """Fetch data from all enabled endpoints"""
        enabled_endpoints = [e for e in self.endpoints if e.enabled]
        
        tasks = [self.fetch_endpoint(endpoint) for endpoint in enabled_endpoints]
        results = await asyncio.gather(*tasks)
        
        # Filter out None values
        valid_results = [r for r in results if r is not None]
        
        logger.info(f"Fetched {len(valid_results)}/{len(enabled_endpoints)} endpoints successfully")
        return valid_results
    
    async def get_aggregated_price(self, symbol: str = "bitcoin") -> Dict:
        """Get aggregated price from multiple sources"""
        data_points = await self.fetch_all_endpoints()
        
        crypto_points = [dp for dp in data_points if dp.metadata.get('category') == 'crypto']
        
        if not crypto_points:
            return {'error': 'No price data available'}
        
        # Calculate weighted average
        total_weight = sum(dp.confidence for dp in crypto_points)
        weighted_sum = sum(dp.value * dp.confidence for dp in crypto_points)
        aggregated_price = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Calculate statistics
        values = [dp.value for dp in crypto_points]
        price_std = statistics.stdev(values) if len(values) > 1 else 0
        price_min = min(values)
        price_max = max(values)
        
        return {
            'symbol': symbol,
            'aggregated_price': aggregated_price,
            'price_std': price_std,
            'price_min': price_min,
            'price_max': price_max,
            'data_points_count': len(crypto_points),
            'sources': [dp.source for dp in crypto_points],
            'timestamp': datetime.now().isoformat()
        }


class KPITracker:
    """Tracks KPIs and generates arbitrage signals"""
    
    def __init__(self, oracle_system: OracleSystem):
        self.oracle_system = oracle_system
        self.kpi_history: Dict[str, List[KPISignal]] = defaultdict(list)
        self.thresholds = {
            'price_momentum': 2.0,
            'volume_surge': 1.5,
            'volatility_index': 0.05,
            'liquidity_depth': 1000000,
            'social_sentiment': 0.6,
            'github_activity': 10,
            'network_congestion': 50,
            'cross_chain_premium': 0.02
        }
    
    async def calculate_kpis(self) -> Dict[str, KPISignal]:
        """Calculate all KPIs and generate signals"""
        data_points = await self.oracle_system.fetch_all_endpoints()
        signals = {}
        
        # Price momentum KPI
        price_momentum = self._calculate_price_momentum(data_points)
        signals['price_momentum'] = self._generate_signal(
            'price_momentum', price_momentum, self.thresholds['price_momentum']
        )
        
        # Volume surge KPI
        volume_surge = self._calculate_volume_surge(data_points)
        signals['volume_surge'] = self._generate_signal(
            'volume_surge', volume_surge, self.thresholds['volume_surge']
        )
        
        # Volatility index KPI
        volatility_index = self._calculate_volatility(data_points)
        signals['volatility_index'] = self._generate_signal(
            'volatility_index', volatility_index, self.thresholds['volatility_index'], reverse=True
        )
        
        # Liquidity depth KPI
        liquidity_depth = self._calculate_liquidity_depth(data_points)
        signals['liquidity_depth'] = self._generate_signal(
            'liquidity_depth', liquidity_depth, self.thresholds['liquidity_depth']
        )
        
        # Store signals
        for name, signal in signals.items():
            self.kpi_history[name].append(signal)
        
        return signals
    
    def _calculate_price_momentum(self, data_points: List[OracleDataPoint]) -> float:
        """Calculate price momentum from data points"""
        if len(data_points) < 2:
            return 0.0
        
        values = [dp.value for dp in data_points if dp.metadata.get('category') == 'crypto']
        if len(values) < 2:
            return 0.0
        
        # Calculate percentage change
        momentum = (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else 0.0
        return abs(momentum)
    
    def _calculate_volume_surge(self, data_points: List[OracleDataPoint]) -> float:
        """Calculate volume surge indicator"""
        # Simplified calculation based on data point frequency
        crypto_points = [dp for dp in data_points if dp.metadata.get('category') == 'crypto']
        return len(crypto_points) / 10.0  # Normalized by expected count
    
    def _calculate_volatility(self, data_points: List[OracleDataPoint]) -> float:
        """Calculate volatility index"""
        values = [dp.value for dp in data_points if dp.metadata.get('category') == 'crypto']
        if len(values) < 2:
            return 0.0
        
        try:
            return statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) != 0 else 0.0
        except:
            return 0.0
    
    def _calculate_liquidity_depth(self, data_points: List[OracleDataPoint]) -> float:
        """Calculate liquidity depth indicator"""
        # Simplified based on number of active endpoints
        active_endpoints = len(set(dp.source for dp in data_points))
        return active_endpoints * 100000  # Mock liquidity value
    
    def _generate_signal(
        self, name: str, value: float, threshold: float, reverse: bool = False
    ) -> KPISignal:
        """Generate trading signal based on KPI value"""
        if reverse:
            # For reverse thresholds (lower is better)
            if value < threshold:
                signal = 'buy'
                confidence = min(0.9, (threshold - value) / threshold)
            elif value > threshold * 1.5:
                signal = 'sell'
                confidence = min(0.9, (value - threshold * 1.5) / threshold)
            else:
                signal = 'hold'
                confidence = 0.5
        else:
            # Normal thresholds (higher is better)
            if value > threshold:
                signal = 'buy'
                confidence = min(0.9, (value - threshold) / threshold)
            elif value < threshold * 0.5:
                signal = 'sell'
                confidence = min(0.9, (threshold * 0.5 - value) / threshold)
            else:
                signal = 'hold'
                confidence = 0.5
        
        return KPISignal(
            name=name,
            value=value,
            threshold=threshold,
            signal=signal,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )
    
    def get_arbitrage_signals(self) -> Dict:
        """Get current arbitrage signals based on KPIs"""
        signals = asyncio.run(self.calculate_kpis())
        
        # Calculate overall signal
        buy_signals = sum(1 for s in signals.values() if s.signal == 'buy')
        sell_signals = sum(1 for s in signals.values() if s.signal == 'sell')
        
        if buy_signals > sell_signals:
            overall_signal = 'buy'
        elif sell_signals > buy_signals:
            overall_signal = 'sell'
        else:
            overall_signal = 'hold'
        
        return {
            'overall_signal': overall_signal,
            'signals': {name: signal.to_dict() for name, signal in signals.items()},
            'buy_count': buy_signals,
            'sell_count': sell_signals,
            'hold_count': len(signals) - buy_signals - sell_signals,
            'timestamp': datetime.now().isoformat()
        }


async def main():
    """Example usage"""
    async with OracleSystem() as oracle:
        # Fetch all endpoint data
        data_points = await oracle.fetch_all_endpoints()
        print(f"Fetched {len(data_points)} data points")
        
        # Get aggregated price
        price_data = await oracle.get_aggregated_price("bitcoin")
        print(f"\n=== Aggregated Price Data ===")
        print(json.dumps(price_data, indent=2))
        
        # Calculate KPIs
        kpi_tracker = KPITracker(oracle)
        arbitrage_signals = kpi_tracker.get_arbitrage_signals()
        
        print(f"\n=== Arbitrage Signals ===")
        print(json.dumps(arbitrage_signals, indent=2))


if __name__ == '__main__':
    asyncio.run(main())