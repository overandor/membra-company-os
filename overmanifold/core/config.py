"""
Overmanifold Core Configuration
Central configuration for the manifold system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Environment(Enum):
    """Deployment environments."""
    DEVNET = "devnet"
    TESTNET = "testnet"
    MAINNET = "mainnet"


class Chain(Enum):
    """Supported blockchain networks."""
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"


@dataclass
class ChainConfig:
    """Configuration for a specific chain."""
    chain: Chain
    rpc_url: str
    ws_url: Optional[str] = None
    explorer_url: str = ""
    chain_id: int = 0
    native_token: str = ""
    block_time: float = 0.0


@dataclass
class OracleConfig:
    """Oracle network configuration."""
    oracle_addresses: List[str] = field(default_factory=list)
    update_interval: int = 60  # seconds
    confidence_threshold: float = 0.7
    max_appraisals: int = 5
    convergence_timeout: int = 300  # seconds


@dataclass
class LiquidityConfig:
    """Liquidity manifold configuration."""
    min_liquidity_depth: float = 1000.0
    max_slippage: float = 0.01
    trust_threshold: float = 0.5
    curvature_weight: float = 0.3
    routing_timeout: int = 30  # seconds


@dataclass
class GovernanceConfig:
    """LLM governance configuration."""
    model_endpoint: str = ""
    max_tokens: int = 2000
    temperature: float = 0.7
    intent_timeout: int = 120  # seconds
    convergence_threshold: int = 3  # minimum observers


@dataclass
class SMSConfig:
    """SMS transport layer configuration."""
    gateway_url: str = ""
    api_key: Optional[str] = None
    max_packet_size: int = 160  # characters
    encryption_enabled: bool = True
    rate_limit: int = 10  # messages per minute


@dataclass
class ComputeConfig:
    """Compute contribution configuration."""
    inference_reward_rate: float = 0.001  # per token
    validation_reward_rate: float = 0.01  # per validation
    min_compute_quality: float = 0.8
    max_batch_size: int = 100


@dataclass
class TreasuryConfig:
    """Treasury and deflation configuration."""
    treasury_address: str = ""
    burn_rate: float = 0.01  # 1% of verified work
    min_burn_amount: float = 0.001
    work_verification_threshold: float = 0.9
    deflation_enabled: bool = True


@dataclass
class OvermanifoldConfig:
    """Main Overmanifold configuration."""
    environment: Environment = Environment.DEVNET
    chains: Dict[Chain, ChainConfig] = field(default_factory=dict)
    oracle: OracleConfig = field(default_factory=OracleConfig)
    liquidity: LiquidityConfig = field(default_factory=LiquidityConfig)
    governance: GovernanceConfig = field(default_factory=GovernanceConfig)
    sms: SMSConfig = field(default_factory=SMSConfig)
    compute: ComputeConfig = field(default_factory=ComputeConfig)
    treasury: TreasuryConfig = field(default_factory=TreasuryConfig)
    
    # System-wide settings
    max_state_transition_history: int = 10000
    proof_retention_days: int = 90
    endpoint_sync_interval: int = 300  # seconds
    manifold_snapshot_interval: int = 3600  # seconds
    
    # Security
    enable_encryption: bool = True
    signature_algorithm: str = "ed25519"
    hash_algorithm: str = "sha256"
    
    def get_chain_config(self, chain: Chain) -> Optional[ChainConfig]:
        """Get configuration for specific chain."""
        return self.chains.get(chain)
    
    def add_chain_config(self, config: ChainConfig) -> None:
        """Add chain configuration."""
        self.chains[config.chain] = config


# Default configurations
DEVNET_CONFIG = OvermanifoldConfig(
    environment=Environment.DEVNET,
    chains={
        Chain.SOLANA: ChainConfig(
            chain=Chain.SOLANA,
            rpc_url="https://api.devnet.solana.com",
            ws_url="wss://api.devnet.solana.com",
            explorer_url="https://explorer.solana.com/?cluster=devnet",
            chain_id=101,
            native_token="SOL",
            block_time=0.4
        )
    },
    oracle=OracleConfig(
        update_interval=30,
        confidence_threshold=0.6,
        max_appraisals=3
    ),
    liquidity=LiquidityConfig(
        min_liquidity_depth=100.0,
        max_slippage=0.05,
        trust_threshold=0.3
    ),
    governance=GovernanceConfig(
        intent_timeout=60,
        convergence_threshold=2
    )
)

MAINNET_CONFIG = OvermanifoldConfig(
    environment=Environment.MAINNET,
    chains={
        Chain.SOLANA: ChainConfig(
            chain=Chain.SOLANA,
            rpc_url="https://api.mainnet-beta.solana.com",
            ws_url="wss://api.mainnet-beta.solana.com",
            explorer_url="https://explorer.solana.com",
            chain_id=101,
            native_token="SOL",
            block_time=0.4
        ),
        Chain.ETHEREUM: ChainConfig(
            chain=Chain.ETHEREUM,
            rpc_url="https://eth.llamarpc.com",
            ws_url="wss://eth.llamarpc.com",
            explorer_url="https://etherscan.io",
            chain_id=1,
            native_token="ETH",
            block_time=12.0
        )
    },
    oracle=OracleConfig(
        update_interval=60,
        confidence_threshold=0.8,
        max_appraisals=5
    ),
    liquidity=LiquidityConfig(
        min_liquidity_depth=10000.0,
        max_slippage=0.01,
        trust_threshold=0.7
    ),
    treasury=TreasuryConfig(
        burn_rate=0.02,
        deflation_enabled=True
    )
)