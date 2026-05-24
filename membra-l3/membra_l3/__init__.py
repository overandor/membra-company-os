"""
MEMBRA Layer-3 Protocol
Python-powered Solana L3 for gas-deferred intents, proof-gated tokenomics,
ZK fee credits, and verified token routing.

Architecture:
    Python L3 (this package) → intents, proofs, relayers, oracles
    Solana L1            → final settlement, token transfers, vaults
    Rust/Anchor          → on-chain program enforcement
"""
from .config import L3Config, DEFAULT_CONFIG, Chain, TokenStatus, TokenConfig, RouteConfig
from .proof_book import ProofBook, ProofEntry, ProofType, proof_book
from .gas_vault import GasVault, FeeCredit, CreditStatus, Reimbursement, gas_vault
from .volatility_oracle import (
    VolatilityOracle, VolatilitySignal, VolatilityReport,
    PricePoint, GasConditions, LiquiditySnapshot, volatility_oracle,
)
from .intent_network import (
    IntentNetwork, PaymentIntent, IntentStatus, intent_network,
)
from .token_router import (
    TokenRouter, TokenAdapter, RouteQuote,
    SplSwapAdapter, WormholeBridgeAdapter, token_router,
)
from .identity import (
    IdentityRegistry, IdentityLink, IdentityProvider, LinkStatus,
    SocialScore, identity_registry,
)
from .relayer import Relayer, RelayerConfig, RelayResult
from .governance import (
    Governance, GovernanceProposal, ProposalType, ProposalStatus,
    Vote, VoteChoice, governance,
)

__version__ = "0.1.0"
__all__ = [
    # Config
    "L3Config", "DEFAULT_CONFIG", "Chain", "TokenStatus", "TokenConfig", "RouteConfig",
    # ProofBook
    "ProofBook", "ProofEntry", "ProofType", "proof_book",
    # GasVault
    "GasVault", "FeeCredit", "CreditStatus", "Reimbursement", "gas_vault",
    # Volatility Oracle
    "VolatilityOracle", "VolatilitySignal", "VolatilityReport",
    "PricePoint", "GasConditions", "LiquiditySnapshot", "volatility_oracle",
    # Intent Network
    "IntentNetwork", "PaymentIntent", "IntentStatus", "intent_network",
    # Token Router
    "TokenRouter", "TokenAdapter", "RouteQuote",
    "SplSwapAdapter", "WormholeBridgeAdapter", "token_router",
    # Identity
    "IdentityRegistry", "IdentityLink", "IdentityProvider", "LinkStatus",
    "SocialScore", "identity_registry",
    # Relayer
    "Relayer", "RelayerConfig", "RelayResult",
    # Governance
    "Governance", "GovernanceProposal", "ProposalType", "ProposalStatus",
    "Vote", "VoteChoice", "governance",
]
