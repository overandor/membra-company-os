"""
Membra Oracle Integration
Integrates with the membra bridge oracle system for real-time data and validation.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import hashlib

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("oracle_integration")


class OracleEndpoint(Enum):
    """Membra oracle endpoints"""
    PHONE_VALIDATION = "phone_validation"
    WALLET_BALANCE = "wallet_balance"
    TRANSACTION_STATUS = "transaction_status"
    SMS_MINING_REWARDS = "sms_mining_rewards"
    NETWORK_STATUS = "network_status"
    TOKEN_PRICES = "token_prices"
    LIQUIDITY_INFO = "liquidity_info"
    ZK_VERIFICATION = "zk_verification"
    ORACLE_DATA = "oracle_data"


@dataclass
class OracleResponse:
    """Response from oracle"""
    endpoint: OracleEndpoint
    success: bool
    data: Any = None
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "endpoint": self.endpoint.value,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms
        }


@dataclass
class OracleData:
    """Cached oracle data"""
    endpoint: OracleEndpoint
    data: Any
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minutes default cache
    
    def is_expired(self) -> bool:
        """Check if cached data is expired"""
        return datetime.utcnow() > self.timestamp + timedelta(seconds=self.ttl_seconds)


class MembraOracleIntegration:
    """Integration with membra bridge oracle system"""
    
    def __init__(self, oracle_base_url: str = "http://localhost:8001"):
        self.oracle_base_url = oracle_base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, OracleData] = {}
        self.request_timeout = 10.0
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def call_oracle(
        self,
        endpoint: OracleEndpoint,
        params: Dict = None,
        use_cache: bool = True,
        cache_ttl: int = 300
    ) -> OracleResponse:
        """Call oracle endpoint with caching"""
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if not cached_data.is_expired():
                logger.debug(f"Cache hit for {endpoint.value}")
                return OracleResponse(
                    endpoint=endpoint,
                    success=True,
                    data=cached_data.data,
                    timestamp=cached_data.timestamp
                )
        
        # Make oracle call
        start_time = datetime.utcnow()
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout))
            
            url = f"{self.oracle_base_url}/oracle/{endpoint.value}"
            
            async with self.session.get(url, params=params) as response:
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache the response
                    if use_cache:
                        self.cache[cache_key] = OracleData(
                            endpoint=endpoint,
                            data=data,
                            timestamp=datetime.utcnow(),
                            ttl_seconds=cache_ttl
                        )
                    
                    return OracleResponse(
                        endpoint=endpoint,
                        success=True,
                        data=data,
                        response_time_ms=response_time
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Oracle error: {response.status} - {error_text}")
                    return OracleResponse(
                        endpoint=endpoint,
                        success=False,
                        error=f"HTTP {response.status}: {error_text}",
                        response_time_ms=response_time
                    )
                    
        except asyncio.TimeoutError:
            logger.error(f"Oracle timeout for {endpoint.value}")
            return OracleResponse(
                endpoint=endpoint,
                success=False,
                error="Request timeout",
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
        except Exception as e:
            logger.error(f"Oracle call failed: {e}")
            return OracleResponse(
                endpoint=endpoint,
                success=False,
                error=str(e),
                response_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
    
    async def validate_phone_number(self, phone_number: str) -> OracleResponse:
        """Validate phone number via oracle"""
        return await self.call_oracle(
            OracleEndpoint.PHONE_VALIDATION,
            params={"phone": phone_number}
        )
    
    async def get_wallet_balance(self, wallet_address: str) -> OracleResponse:
        """Get wallet balance from oracle"""
        return await self.call_oracle(
            OracleEndpoint.WALLET_BALANCE,
            params={"address": wallet_address},
            cache_ttl=60  # Cache balance for 1 minute
        )
    
    async def get_transaction_status(self, transaction_hash: str) -> OracleResponse:
        """Get transaction status from oracle"""
        return await self.call_oracle(
            OracleEndpoint.TRANSACTION_STATUS,
            params={"tx_hash": transaction_hash},
            use_cache=False  # Don't cache transaction status
        )
    
    async def get_sms_mining_rewards(self, phone_number: str) -> OracleResponse:
        """Get SMS mining rewards for phone number"""
        return await self.call_oracle(
            OracleEndpoint.SMS_MINING_REWARDS,
            params={"phone": phone_number},
            cache_ttl=120  # Cache for 2 minutes
        )
    
    async def get_network_status(self) -> OracleResponse:
        """Get network status from oracle"""
        return await self.call_oracle(
            OracleEndpoint.NETWORK_STATUS,
            cache_ttl=30  # Cache for 30 seconds
        )
    
    async def get_token_prices(self, tokens: List[str] = None) -> OracleResponse:
        """Get token prices from oracle"""
        params = {}
        if tokens:
            params["tokens"] = ",".join(tokens)
        
        return await self.call_oracle(
            OracleEndpoint.TOKEN_PRICES,
            params=params,
            cache_ttl=60  # Cache for 1 minute
        )
    
    async def get_liquidity_info(self, pool_address: str = None) -> OracleResponse:
        """Get liquidity information from oracle"""
        params = {}
        if pool_address:
            params["pool"] = pool_address
        
        return await self.call_oracle(
            OracleEndpoint.LIQUIDITY_INFO,
            params=params,
            cache_ttl=60
        )
    
    async def verify_zk_proof(self, proof_data: Dict) -> OracleResponse:
        """Verify zero-knowledge proof via oracle"""
        return await self.call_oracle(
            OracleEndpoint.ZK_VERIFICATION,
            params=proof_data,
            use_cache=False  # Never cache ZK verification
        )
    
    async def get_oracle_data(self, data_type: str, params: Dict = None) -> OracleResponse:
        """Get generic oracle data"""
        return await self.call_oracle(
            OracleEndpoint.ORACLE_DATA,
            params={"type": data_type, **(params or {})},
            cache_ttl=180  # Cache for 3 minutes
        )
    
    async def batch_oracle_calls(self, calls: List[tuple]) -> List[OracleResponse]:
        """Make multiple oracle calls in parallel"""
        tasks = []
        for endpoint, params, use_cache, cache_ttl in calls:
            task = self.call_oracle(endpoint, params, use_cache, cache_ttl)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    def _get_cache_key(self, endpoint: OracleEndpoint, params: Dict = None) -> str:
        """Generate cache key for endpoint and parameters"""
        key_data = f"{endpoint.value}"
        if params:
            key_data += json.dumps(params, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def clear_cache(self, endpoint: OracleEndpoint = None):
        """Clear cache for specific endpoint or all endpoints"""
        if endpoint:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(endpoint.value)]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()
        
        logger.info(f"Cleared cache for {'all' if not endpoint else endpoint.value}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for data in self.cache.values() if data.is_expired())
        
        endpoint_counts = {}
        for cache_key, data in self.cache.items():
            endpoint = data.endpoint.value
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "endpoint_counts": endpoint_counts
        }


# Global oracle integration instance
oracle_integration = MembraOracleIntegration()