"""
Overmanifold Core Types
Foundational data structures for the unified cryptographic-economic coordination manifold.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union
from enum import Enum
from datetime import datetime
import hashlib
import json


class TransportType(Enum):
    """Transport protocols for Overmanifold communication."""
    CHAIN = "chain"
    SMS = "sms"
    BROWSER = "browser"
    IPFS = "ipfs"
    RELAY = "relay"
    MESH = "mesh"
    BLUETOOTH = "bluetooth"
    QR = "qr"
    LOCAL_INFERENCE = "local_inference"


class CapabilityType(Enum):
    """Capability types for endpoint surfaces."""
    MESSAGING = "messaging"
    COMPUTE = "compute"
    STORAGE = "storage"
    SETTLEMENT = "settlement"
    RELAY = "relay"
    ORACLE = "oracle"
    GOVERNANCE = "governance"
    INFERENCE = "inference"
    VALIDATION = "validation"
    PRODUCTION = "production"


class StateTransitionType(Enum):
    """Types of verifiable state transitions."""
    MESSAGE = "message"
    PROMPT = "prompt"
    COMMIT = "commit"
    LIQUIDITY_ROUTE = "liquidity_route"
    WALLET_INTERACTION = "wallet_interaction"
    SMS_EVENT = "sms_event"
    BROWSER_SESSION = "browser_session"
    FILE_OPERATION = "file_operation"
    PROOF_SUBMISSION = "proof_submission"
    ORACLE_UPDATE = "oracle_update"
    INFERENCE_OPERATION = "inference_operation"
    DEPLOYMENT = "deployment"
    STAKING = "staking"
    COMPUTE_CONTRIBUTION = "compute_contribution"
    ENDPOINT_CONNECTION = "endpoint_connection"
    SEMANTIC_INTENT = "semantic_intent"


@dataclass
class Hash:
    """Cryptographic hash identifier."""
    value: str
    algorithm: str = "sha256"
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Hash value cannot be empty")
    
    @classmethod
    def from_data(cls, data: Union[str, bytes, Dict], algorithm: str = "sha256") -> 'Hash':
        """Create hash from arbitrary data."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithm == "sha256":
            hash_obj = hashlib.sha256(data)
        elif algorithm == "sha3_256":
            hash_obj = hashlib.sha3_256(data)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return cls(hash_obj.hexdigest(), algorithm)
    
    def __str__(self) -> str:
        return self.value


@dataclass
class EndpointID:
    """Transport-independent endpoint identifier."""
    did: str  # Decentralized Identifier
    namespace: str
    local_id: str
    
    def __post_init__(self):
        if not self.did.startswith("did:"):
            raise ValueError("DID must start with 'did:'")
    
    @classmethod
    def generate(cls, namespace: str, local_id: str, method: str = "om") -> 'EndpointID':
        """Generate new endpoint ID."""
        did = f"did:{method}:{namespace}:{local_id}"
        return cls(did, namespace, local_id)
    
    def __str__(self) -> str:
        return self.did


@dataclass
class CapabilitySurface:
    """Capability surface defining endpoint abilities."""
    capability_type: CapabilityType
    parameters: Dict[str, Any] = field(default_factory=dict)
    trust_score: float = 0.0
    availability: float = 1.0
    last_verified: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if capability is currently available."""
        return self.availability > 0.0


@dataclass
class LiquiditySurface:
    """Dynamic liquidity surface within the manifold."""
    token_address: str
    chain_id: str
    depth: float
    curvature: float  # Represents liquidity efficiency
    trust_density: float
    slippage_tolerance: float
    routes: List[str] = field(default_factory=list)
    
    def effective_liquidity(self) -> float:
        """Calculate effective liquidity considering trust and curvature."""
        return self.depth * self.trust_density * self.curvature


@dataclass
class Proof:
    """Cryptographic proof of state transition."""
    proof_type: str
    proof_hash: Hash
    timestamp: datetime
    prover_endpoint: EndpointID
    state_transition: StateTransitionType
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def verify(self) -> bool:
        """Verify proof validity (placeholder for actual verification logic)."""
        # Implementation depends on proof type
        return True


@dataclass
class StateTransition:
    """Verifiable state transition in the manifold."""
    transition_id: Hash
    transition_type: StateTransitionType
    from_state: Hash
    to_state: Hash
    timestamp: datetime
    actor: EndpointID
    proofs: List[Proof] = field(default_factory=list)
    transport: TransportType = TransportType.CHAIN
    
    def add_proof(self, proof: Proof) -> None:
        """Add proof to state transition."""
        self.proofs.append(proof)


@dataclass
class EconomicSignal:
    """Economic signal derived from manifold participation."""
    signal_id: Hash
    source_endpoint: EndpointID
    signal_type: str
    magnitude: float
    confidence: float
    timestamp: datetime
    provenance: List[Hash] = field(default_factory=list)
    
    def aggregate_strength(self) -> float:
        """Calculate aggregate signal strength."""
        return self.magnitude * self.confidence


@dataclass
class IntentFragment:
    """Unresolved semantic intent fragment."""
    fragment_id: Hash
    intent_data: Dict[str, Any]
    probability: float
    convergence_threshold: float
    observers: Set[EndpointID] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    
    def add_observer(self, endpoint: EndpointID) -> None:
        """Add observer to fragment."""
        self.observers.add(endpoint)
    
    def check_convergence(self) -> bool:
        """Check if fragment has reached convergence."""
        return len(self.observers) >= self.convergence_threshold


@dataclass
class ManifoldTopology:
    """Snapshot of manifold topology at a point in time."""
    topology_id: Hash
    endpoints: Dict[EndpointID, Dict[str, Any]] = field(default_factory=dict)
    liquidity_surfaces: Dict[str, LiquiditySurface] = field(default_factory=dict)
    capability_graph: Dict[EndpointID, List[CapabilitySurface]] = field(default_factory=dict)
    trust_matrix: Dict[EndpointID, Dict[EndpointID, float]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_trust_score(self, from_endpoint: EndpointID, to_endpoint: EndpointID) -> float:
        """Get trust score between endpoints."""
        return self.trust_matrix.get(from_endpoint, {}).get(to_endpoint, 0.0)
    
    def get_capabilities(self, endpoint: EndpointID) -> List[CapabilitySurface]:
        """Get capabilities for endpoint."""
        return self.capability_graph.get(endpoint, [])


@dataclass
class SettlementMapping:
    """Settlement mapping for economic resolution."""
    mapping_id: Hash
    participants: List[EndpointID]
    amounts: Dict[EndpointID, float]
    token_address: str
    conditions: List[str] = field(default_factory=list)
    executed: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RoutingPath:
    """Optimal routing path through the manifold."""
    path_id: Hash
    endpoints: List[EndpointID]
    total_cost: float
    total_trust: float
    estimated_latency: float
    liquidity_requirements: List[str] = field(default_factory=list)
    
    def efficiency_score(self) -> float:
        """Calculate routing efficiency score."""
        return self.total_trust / (self.total_cost * self.estimated_latency + 1e-6)