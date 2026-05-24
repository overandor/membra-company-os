"""
Overmanifold Core Module
Foundational systems for the unified cryptographic-economic coordination manifold.
"""

from .types import (
    TransportType,
    CapabilityType,
    StateTransitionType,
    Hash,
    EndpointID,
    CapabilitySurface,
    LiquiditySurface,
    Proof,
    StateTransition,
    EconomicSignal,
    IntentFragment,
    ManifoldTopology,
    SettlementMapping,
    RoutingPath
)

from .config import (
    Environment,
    Chain,
    ChainConfig,
    OracleConfig,
    LiquidityConfig,
    GovernanceConfig,
    SMSConfig,
    ComputeConfig,
    TreasuryConfig,
    OvermanifoldConfig,
    DEVNET_CONFIG,
    MAINNET_CONFIG
)

__all__ = [
    # Types
    "TransportType",
    "CapabilityType",
    "StateTransitionType",
    "Hash",
    "EndpointID",
    "CapabilitySurface",
    "LiquiditySurface",
    "Proof",
    "StateTransition",
    "EconomicSignal",
    "IntentFragment",
    "ManifoldTopology",
    "SettlementMapping",
    "RoutingPath",
    
    # Configuration
    "Environment",
    "Chain",
    "ChainConfig",
    "OracleConfig",
    "LiquidityConfig",
    "GovernanceConfig",
    "SMSConfig",
    "ComputeConfig",
    "TreasuryConfig",
    "OvermanifoldConfig",
    "DEVNET_CONFIG",
    "MAINNET_CONFIG"
]