"""
MEMBRA L3 Configuration
Network settings, approved tokens, route registry, policy parameters.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Chain(Enum):
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    BASE = "base"
    ARBITRUM = "arbitrum"
    POLYGON = "polygon"


class TokenStatus(Enum):
    APPROVED = "approved"
    PENDING = "pending"
    DEPRECATED = "deprecated"
    BLACKLISTED = "blacklisted"


@dataclass
class TokenConfig:
    symbol: str
    name: str
    chain: Chain
    address: str  # mint address (Solana) or contract address (EVM)
    decimals: int = 9
    status: TokenStatus = TokenStatus.APPROVED
    min_route_amount: int = 0
    max_route_amount: int = 1_000_000_000_000  # in token base units


@dataclass
class RouteConfig:
    """Verified route between two tokens."""
    from_token: str  # symbol
    to_token: str    # symbol
    adapter: str     # adapter class name
    fee_bps: int = 30  # 0.3%
    min_liquidity_usd: float = 10_000.0
    enabled: bool = True


@dataclass
class L3Config:
    # Network
    intent_claim_window_seconds: int = 604800  # 7 days
    max_intent_amount_usd: float = 100_000.0
    min_intent_amount_usd: float = 0.01

    # GasVault
    gas_vault_min_coverage_ratio: float = 1.5  # 150% coverage
    gas_vault_target_coverage_ratio: float = 3.0
    fee_credit_expiry_seconds: int = 86400  # 24 hours
    max_fee_credit_per_user_usd: float = 10.0

    # Proof-of-Volatility
    volatility_twap_window_seconds: int = 3600  # 1 hour
    volatility_min_data_points: int = 12
    volatility_signal_threshold: float = 0.02  # 2% price movement
    oracle_staleness_seconds: int = 300  # 5 min max oracle age

    # Proof-of-Development
    dev_required_approvals: int = 3
    dev_review_window_seconds: int = 259200  # 3 days

    # Supply caps
    max_supply: int = 1_000_000_000_000_000  # 1 billion tokens (9 decimals)
    max_emission_per_epoch: int = 10_000_000_000_000  # 10k tokens per epoch
    epoch_duration_seconds: int = 86400  # 1 day

    # Approved tokens
    tokens: Dict[str, TokenConfig] = field(default_factory=dict)
    routes: List[RouteConfig] = field(default_factory=list)

    def __post_init__(self):
        if not self.tokens:
            self._init_default_tokens()
        if not self.routes:
            self._init_default_routes()

    def _init_default_tokens(self):
        defaults = [
            TokenConfig("MEMBRA", "MEMBRA Protocol Token", Chain.SOLANA,
                        "membra_token_mint_address_placeholder"),
            TokenConfig("USDC", "USD Coin", Chain.SOLANA,
                        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 6),
            TokenConfig("SOL", "Solana", Chain.SOLANA,
                        "So11111111111111111111111111111111111111112"),
            TokenConfig("USDT", "Tether USD", Chain.SOLANA,
                        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", 6),
            TokenConfig("USDC_ETH", "USD Coin (Ethereum)", Chain.ETHEREUM,
                        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6),
            TokenConfig("WETH", "Wrapped Ether", Chain.ETHEREUM,
                        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18),
        ]
        for t in defaults:
            self.tokens[t.symbol] = t

    def _init_default_routes(self):
        defaults = [
            RouteConfig("MEMBRA", "USDC", "SplSwapAdapter"),
            RouteConfig("USDC", "MEMBRA", "SplSwapAdapter"),
            RouteConfig("SOL", "USDC", "SplSwapAdapter"),
            RouteConfig("USDC", "SOL", "SplSwapAdapter"),
            RouteConfig("USDC", "USDC_ETH", "WormholeBridgeAdapter", fee_bps=10),
            RouteConfig("USDC_ETH", "USDC", "WormholeBridgeAdapter", fee_bps=10),
            RouteConfig("MEMBRA", "SOL", "SplSwapAdapter"),
            RouteConfig("SOL", "MEMBRA", "SplSwapAdapter"),
        ]
        self.routes = defaults

    def get_token(self, symbol: str) -> Optional[TokenConfig]:
        return self.tokens.get(symbol)

    def get_route(self, from_symbol: str, to_symbol: str) -> Optional[RouteConfig]:
        for r in self.routes:
            if r.from_token == from_symbol and r.to_token == to_symbol and r.enabled:
                return r
        return None

    def is_token_approved(self, symbol: str) -> bool:
        t = self.tokens.get(symbol)
        return t is not None and t.status == TokenStatus.APPROVED


DEFAULT_CONFIG = L3Config()
