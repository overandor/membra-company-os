"""
Overmanifold Integration Package
Unified integration of all Overmanifold components into a civilization-scale coordination system.
"""

from overmanifold.core.engine import (
    OvermanifoldEngine,
    OvermanifoldEndpoint,
    StateTransition,
    SemanticIntent,
    Capability,
    RoutingSurface,
    SettlementMapping,
    Handler,
    StateTransitionType,
    CapabilityType,
    MerkleProof
)

from overmanifold.governance.llm_engine import (
    LLMGovernanceEngine,
    EconomicTask,
    IntentInterpretation,
    GovernanceDecision,
    IntentType,
    TaskPriority,
    TaskStatus,
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider
)

from overmanifold.routing.geodesic import (
    GeodesicRouter,
    LiquidityManifold,
    GeodesicPath,
    ManifoldEdge,
    RoutingConstraint,
    RoutingConstraintValue,
    RoutingMetrics
)

from overmanifold.consensus.proof_of_profit import (
    ProofOfProfitConsensus,
    EconomicWork,
    ProofOfProfit,
    InverseMiningOperation,
    TreasuryDeflation,
    WorkType,
    ConsensusStatus
)

from overmanifold.membra_integration.membra_bridge_client import (
    MembraBridgeClient,
    MembraWallet,
    SMSMiningReward
)

from overmanifold.membra_integration.sms_payment_gateway import (
    SMSPaymentGateway,
    SMSPaymentRequest,
    SMSPaymentResponse
)

from overmanifold.membra_integration.email_payment_gateway import (
    EmailPaymentGateway,
    EmailPaymentRequest,
    EmailPaymentResponse
)

from overmanifold.membra_integration.free_transaction_sponsor import (
    FreeTransactionSponsor,
    Sponsor,
    SponsoredTransaction
)

from overmanifold.membra_integration.unified_free_payment_api import (
    UnifiedFreePaymentAPI,
    FreePaymentRequest,
    FreePaymentResponse,
    PaymentMethod
)

# Dashboard and monitoring
from overmanifold.membra_integration.dashboard import app
from overmanifold.membra_integration.monitoring import sms_monitoring, TransactionLog, MetricType, AlertSeverity
from overmanifold.membra_integration.oracle_integration import MembraOracleIntegration, OracleEndpoint

# SMS transaction processing
from overmanifold.membra_integration.sms_transaction_processor import (
    SMSTransactionProcessor, 
    SMSMessage, 
    TransactionContext, 
    TransactionState
)

__version__ = "0.1.0"
__author__ = "Overmanifold Protocol Foundation"

__all__ = [
    # Core Engine
    'OvermanifoldEngine',
    'OvermanifoldEndpoint',
    'StateTransition',
    'SemanticIntent',
    'Capability',
    'RoutingSurface',
    'SettlementMapping',
    'Handler',
    'StateTransitionType',
    'CapabilityType',
    'MerkleProof',
    
    # LLM Governance
    'LLMGovernanceEngine',
    'EconomicTask',
    'IntentInterpretation',
    'GovernanceDecision',
    'IntentType',
    'TaskPriority',
    'TaskStatus',
    'LLMProvider',
    'OpenAIProvider',
    'AnthropicProvider',
    
    # Geodesic Routing
    'GeodesicRouter',
    'LiquidityManifold',
    'GeodesicPath',
    'ManifoldEdge',
    'RoutingConstraint',
    'RoutingConstraintValue',
    'RoutingMetrics',
    
    # Proof of Profit Consensus
    'ProofOfProfitConsensus',
    'EconomicWork',
    'ProofOfProfit',
    'InverseMiningOperation',
    'TreasuryDeflation',
    'WorkType',
    'ConsensusStatus',
    
    # Membra Bridge Integration
    'MembraBridgeClient',
    'MembraWallet',
    'SMSMiningReward',
    'SMSPaymentGateway',
    'SMSPaymentRequest',
    'SMSPaymentResponse',
    'EmailPaymentGateway',
    'EmailPaymentRequest',
    'EmailPaymentResponse',
    'FreeTransactionSponsor',
    'Sponsor',
    'SponsoredTransaction',
    'UnifiedFreePaymentAPI',
    'FreePaymentRequest',
    'FreePaymentResponse',
    'PaymentMethod',
    
    # Dashboard and monitoring
    'app',
    'sms_monitoring',
    'TransactionLog',
    'MetricType',
    'AlertSeverity',
    'MembraOracleIntegration',
    'OracleEndpoint',
    
    # SMS transaction processing
    'SMSTransactionProcessor',
    'SMSMessage',
    'TransactionContext',
    'TransactionState'
]