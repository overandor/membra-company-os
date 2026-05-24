"""
Overmanifold Core Engine - Civilization-Scale State Transition System
Implements unified identity, Merkle-verifiable state transitions, and dynamic liquidity surfaces.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import base64
import pickle
from pathlib import Path
import cryptography.fernet
import nacl.signing
import nacl.encoding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateTransitionType(Enum):
    """Types of state transitions in the Overmanifold"""
    HUMAN_ACTION = "human_action"
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    REPOSITORY_COMMIT = "repository_commit"
    LIQUIDITY_ROUTE = "liquidity_route"
    WALLET_INTERACTION = "wallet_interaction"
    SMS_EVENT = "sms_event"
    BROWSER_SESSION = "browser_session"
    FILE_OPERATION = "file_operation"
    PROOF_GENERATION = "proof_generation"
    ORACLE_UPDATE = "oracle_update"
    INFERENCE_OPERATION = "inference_operation"
    DEPLOYMENT_ARTIFACT = "deployment_artifact"
    STAKING_POSITION = "staking_position"
    COMPUTE_CONTRIBUTION = "compute_contribution"
    ENDPOINT_CONNECTION = "endpoint_connection"
    SEMANTIC_INTENT = "semantic_intent"


class CapabilityType(Enum):
    """Types of capabilities an endpoint can possess"""
    MESSAGING_REACHABILITY = "messaging_reachability"
    COMPUTATION_AVAILABILITY = "computation_availability"
    STORAGE_RELIABILITY = "storage_reliability"
    SETTLEMENT_OPTIONALITY = "settlement_optionality"
    RELAY_THROUGHPUT = "relay_throughput"
    ORACLE_CONFIDENCE = "oracle_confidence"
    SOFTWARE_PRODUCTION = "software_production"
    SOCIAL_TRUST = "social_trust"
    SEMANTIC_INTEROPERABILITY = "semantic_interoperability"
    LIQUIDITY_PROVISION = "liquidity_provision"


@dataclass
class MerkleProof:
    """Merkle proof for state transition verification"""
    proof_hash: str
    sibling_hashes: List[str]
    root_hash: str
    position: int
    valid: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def verify(self, leaf_hash: str) -> bool:
        """Verify the Merkle proof"""
        current_hash = leaf_hash
        for sibling in self.sibling_hashes:
            if self.position % 2 == 0:
                combined = current_hash + sibling
            else:
                combined = sibling + current_hash
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
            self.position //= 2
        return current_hash == self.root_hash


@dataclass
class StateTransition:
    """A state transition in the Overmanifold"""
    transition_id: str
    transition_type: StateTransitionType
    from_state: str
    to_state: str
    timestamp: str
    endpoint_id: str
    semantic_intent: str
    proof: MerkleProof
    economic_value: float
    capability_requirements: List[CapabilityType]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['transition_type'] = self.transition_type.value
        data['capability_requirements'] = [c.value for c in self.capability_requirements]
        return data


@dataclass
class Capability:
    """A capability of an Overmanifold endpoint"""
    capability_type: CapabilityType
    strength: float  # 0.0 to 1.0
    last_verified: str
    proof_hash: str
    economic_weight: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['capability_type'] = self.capability_type.value
        return data


@dataclass
class RoutingSurface:
    """A routing surface exposed by an endpoint"""
    surface_id: str
    reachable_endpoints: Set[str]
    trust_density: float
    latency_ms: int
    cost_per_transaction: float
    capability_requirements: List[CapabilityType]
    active: bool
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['reachable_endpoints'] = list(self.reachable_endpoints)
        data['capability_requirements'] = [c.value for c in self.capability_requirements]
        return data


@dataclass
class SettlementMapping:
    """Cross-chain settlement mapping"""
    chain_id: str
    token_address: str
    settlement_contract: str
    minimum_amount: float
    maximum_amount: float
    fee_rate: float
    confirmation_blocks: int
    active: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Handler:
    """A handler for specific operations"""
    handler_type: str  # 'message', 'computation', 'storage', 'settlement'
    endpoint: str
    capability_required: CapabilityType
    execution_cost: float
    success_rate: float
    average_latency_ms: int
    active: bool
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['capability_required'] = self.capability_required.value
        return data


@dataclass
class OvermanifoldEndpoint:
    """
    Unified Overmanifold Endpoint Object
    Aggregates handlers, proofs, capabilities, settlement mappings, routing surfaces, 
    storage roots, and economic permissions into one offline-resolvable semantic identity manifold.
    """
    endpoint_id: str
    public_key: str
    private_key: str  # Encrypted in production
    handlers: Dict[str, Handler]
    capabilities: Dict[CapabilityType, Capability]
    settlement_mappings: Dict[str, SettlementMapping]
    routing_surfaces: Dict[str, RoutingSurface]
    storage_roots: Dict[str, str]  # IPFS CIDs and storage references
    economic_permissions: Dict[str, Any]
    total_economic_value: float
    trust_density: float
    proof_continuity_score: float
    human_participation_score: float
    connectivity_entropy: float
    created_at: str
    last_active: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['capabilities'] = {k.value: v.to_dict() for k, v in self.capabilities.items()}
        data['handlers'] = {k: v.to_dict() for k, v in self.handlers.items()}
        data['settlement_mappings'] = {k: v.to_dict() for k, v in self.settlement_mappings.items()}
        data['routing_surfaces'] = {k: v.to_dict() for k, v in self.routing_surfaces.items()}
        return data
    
    def add_capability(self, capability: Capability):
        """Add a capability to the endpoint"""
        self.capabilities[capability.capability_type] = capability
        self._recalculate_economic_value()
    
    def add_handler(self, handler: Handler):
        """Add a handler to the endpoint"""
        self.handlers[handler.handler_type] = handler
        self._recalculate_economic_value()
    
    def add_routing_surface(self, surface: RoutingSurface):
        """Add a routing surface to the endpoint"""
        self.routing_surfaces[surface.surface_id] = surface
        self._recalculate_economic_value()
    
    def add_settlement_mapping(self, chain_id: str, mapping: SettlementMapping):
        """Add a settlement mapping for a chain"""
        self.settlement_mappings[chain_id] = mapping
        self._recalculate_economic_value()
    
    def add_storage_root(self, name: str, root: str):
        """Add a storage root (IPFS CID, etc.)"""
        self.storage_roots[name] = root
    
    def _recalculate_economic_value(self):
        """Recalculate total economic value based on capabilities and handlers"""
        # Base value from capabilities
        capability_value = sum(
            cap.strength * cap.economic_weight 
            for cap in self.capabilities.values()
        )
        
        # Value from handlers
        handler_value = sum(
            handler.success_rate * (1000 - handler.execution_cost) / handler.average_latency_ms
            for handler in self.handlers.values()
        )
        
        # Value from routing surfaces
        routing_value = sum(
            surface.trust_density * len(surface.reachable_endpoints) / surface.cost_per_transaction
            for surface in self.routing_surfaces.values() if surface.active
        )
        
        # Value from settlement mappings
        settlement_value = len(self.settlement_mappings) * 100
        
        # Combine with existing scores
        self.total_economic_value = (
            capability_value + handler_value + routing_value + settlement_value
        ) * self.trust_density * self.proof_continuity_score
    
    def update_activity(self):
        """Update last activity timestamp and scores"""
        self.last_active = datetime.now().isoformat()
        
        # Decay scores over time if not active
        time_since_active = datetime.now() - datetime.fromisoformat(self.last_active)
        if time_since_active > timedelta(hours=1):
            decay_factor = 0.99 ** (time_since_active.total_seconds() / 3600)
            self.trust_density *= decay_factor
            self.proof_continuity_score *= decay_factor
            self.human_participation_score *= decay_factor
    
    def can_perform_transition(self, transition: StateTransition) -> bool:
        """Check if endpoint can perform a given state transition"""
        # Check capability requirements
        for req_cap in transition.capability_requirements:
            if req_cap not in self.capabilities:
                return False
            if self.capabilities[req_cap].strength < 0.5:
                return False
        
        # Check economic value threshold
        if self.total_economic_value < transition.economic_value:
            return False
        
        return True


class SemanticIntent:
    """
    Semantic intent representation that can exist as latent probabilistic 
    coordination state before convergence.
    """
    
    def __init__(self, intent_id: str, semantic_content: str, intent_type: str):
        self.intent_id = intent_id
        self.semantic_content = semantic_content
        self.intent_type = intent_type
        self.ambiguous_interpretations: List[Dict] = []
        self.convergence_conditions: List[str] = []
        self.observer_signatures: List[str] = []
        self.probability_distribution: Dict[str, float] = {}
        self.created_at = datetime.now().isoformat()
        self.converged = False
        self.final_interpretation: Optional[str] = None
    
    def add_interpretation(self, interpretation: str, probability: float, observer: str):
        """Add an ambiguous interpretation with probability"""
        self.ambiguous_interpretations.append({
            'interpretation': interpretation,
            'probability': probability,
            'observer': observer,
            'timestamp': datetime.now().isoformat()
        })
        self.probability_distribution[interpretation] = probability
    
    def add_observer_signature(self, observer_id: str, signature: str):
        """Add observer signature for convergence"""
        self.observer_signatures.append({
            'observer_id': observer_id,
            'signature': signature,
            'timestamp': datetime.now().isoformat()
        })
    
    def check_convergence(self, threshold: float = 0.8) -> bool:
        """Check if interpretations have converged"""
        if not self.probability_distribution:
            return False
        
        max_prob = max(self.probability_distribution.values())
        if max_prob >= threshold:
            self.converged = True
            self.final_interpretation = max(self.probability_distribution, key=self.probability_distribution.get)
            return True
        
        return False


class OvermanifoldEngine:
    """
    Core Overmanifold Engine
    Manages endpoints, state transitions, semantic intent, and the economic manifold.
    """
    
    def __init__(self):
        self.endpoints: Dict[str, OvermanifoldEndpoint] = {}
        self.state_transitions: List[StateTransition] = []
        self.semantic_intents: Dict[str, SemanticIntent] = {}
        self.merkle_roots: Dict[str, str] = {}
        self.liquidity_manifold: Dict[str, float] = {}  # Dynamic liquidity surfaces
        self.trust_topology: Dict[Tuple[str, str], float] = {}  # Trust relationships
        self.geodesic_paths: Dict[Tuple[str, str], List[str]] = {}  # Optimal routing paths
        
        # Economic parameters
        self.total_supply = 1_000_000_000  # Initial premine
        self.circulating_supply = self.total_supply
        self.inverse_mining_burn = 0.0
        self.treasury_balance = 0.0
        
        # Consensus parameters
        self.proof_of_profit_threshold = 0.7
        self.min_trust_density = 0.3
        self.min_capability_strength = 0.5
        
    def generate_endpoint_id(self, public_key: str) -> str:
        """Generate unique endpoint ID from public key"""
        return hashlib.sha256(public_key.encode()).hexdigest()[:32]
    
    def create_endpoint(
        self,
        public_key: str,
        private_key: str,
        initial_capabilities: List[Capability] = None,
        metadata: Dict = None
    ) -> OvermanifoldEndpoint:
        """Create a new Overmanifold endpoint"""
        endpoint_id = self.generate_endpoint_id(public_key)
        
        endpoint = OvermanifoldEndpoint(
            endpoint_id=endpoint_id,
            public_key=public_key,
            private_key=private_key,
            handlers={},
            capabilities={},
            settlement_mappings={},
            routing_surfaces={},
            storage_roots={},
            economic_permissions={},
            total_economic_value=0.0,
            trust_density=0.5,  # Start with neutral trust
            proof_continuity_score=0.5,
            human_participation_score=0.5,
            connectivity_entropy=1.0,
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        # Add initial capabilities
        if initial_capabilities:
            for cap in initial_capabilities:
                endpoint.add_capability(cap)
        
        self.endpoints[endpoint_id] = endpoint
        logger.info(f"Created Overmanifold endpoint: {endpoint_id}")
        
        return endpoint
    
    def create_state_transition(
        self,
        endpoint_id: str,
        transition_type: StateTransitionType,
        semantic_intent: str,
        from_state: str,
        to_state: str,
        economic_value: float,
        capability_requirements: List[CapabilityType] = None,
        metadata: Dict = None
    ) -> Optional[StateTransition]:
        """Create and execute a state transition"""
        if endpoint_id not in self.endpoints:
            logger.error(f"Endpoint {endpoint_id} not found")
            return None
        
        endpoint = self.endpoints[endpoint_id]
        capability_requirements = capability_requirements or []
        metadata = metadata or {}
        
        # Generate Merkle proof
        transition_data = f"{endpoint_id}{transition_type.value}{from_state}{to_state}{semantic_intent}{datetime.now().isoformat()}"
        leaf_hash = hashlib.sha256(transition_data.encode()).hexdigest()
        
        # Create simplified Merkle proof (in production, would use full tree)
        sibling_hashes = [hashlib.sha256(str(i).encode()).hexdigest() for i in range(10)]
        root_hash = hashlib.sha256(leaf_hash.encode() + ''.join(sibling_hashes).encode()).hexdigest()
        
        proof = MerkleProof(
            proof_hash=leaf_hash,
            sibling_hashes=sibling_hashes,
            root_hash=root_hash,
            position=0,
            valid=True
        )
        
        # Create state transition
        transition = StateTransition(
            transition_id=hashlib.sha256(transition_data.encode()).hexdigest()[:32],
            transition_type=transition_type,
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.now().isoformat(),
            endpoint_id=endpoint_id,
            semantic_intent=semantic_intent,
            proof=proof,
            economic_value=economic_value,
            capability_requirements=capability_requirements,
            metadata=metadata
        )
        
        # Verify endpoint can perform transition
        if not endpoint.can_perform_transition(transition):
            logger.warning(f"Endpoint {endpoint_id} cannot perform transition")
            return None
        
        # Execute transition
        self.state_transitions.append(transition)
        
        # Update endpoint
        endpoint.update_activity()
        endpoint.proof_continuity_score = min(1.0, endpoint.proof_continuity_score + 0.01)
        
        # Update manifold liquidity
        self._update_liquidity_manifold(endpoint_id, economic_value)
        
        # Inverse mining: burn supply based on useful work
        self._inverse_mining(economic_value)
        
        logger.info(f"State transition {transition.transition_id} executed by {endpoint_id}")
        return transition
    
    def create_semantic_intent(
        self,
        semantic_content: str,
        intent_type: str,
        initial_interpretations: List[Tuple[str, float]] = None
    ) -> SemanticIntent:
        """Create a semantic intent that can converge probabilistically"""
        intent_id = hashlib.sha256(
            f"{semantic_content}{intent_type}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        intent = SemanticIntent(intent_id, semantic_content, intent_type)
        
        # Add initial interpretations
        if initial_interpretations:
            for interpretation, probability in initial_interpretations:
                intent.add_interpretation(interpretation, probability, "system")
        
        self.semantic_intents[intent_id] = intent
        logger.info(f"Created semantic intent: {intent_id}")
        
        return intent
    
    def converge_semantic_intent(
        self,
        intent_id: str,
        observer_id: str,
        interpretation: str,
        signature: str
    ) -> bool:
        """Add observer interpretation and check for convergence"""
        if intent_id not in self.semantic_intents:
            return False
        
        intent = self.semantic_intents[intent_id]
        
        # Add interpretation
        current_prob = intent.probability_distribution.get(interpretation, 0.0)
        intent.add_interpretation(interpretation, current_prob + 0.1, observer_id)
        
        # Add signature
        intent.add_observer_signature(observer_id, signature)
        
        # Check convergence
        return intent.check_convergence()
    
    def _update_liquidity_manifold(self, endpoint_id: str, economic_value: float):
        """Update the dynamic liquidity manifold based on state transitions"""
        # Increase liquidity for the endpoint
        current_liquidity = self.liquidity_manifold.get(endpoint_id, 0.0)
        self.liquidity_manifold[endpoint_id] = current_liquidity + economic_value
        
        # Propagate liquidity to connected endpoints
        endpoint = self.endpoints.get(endpoint_id)
        if endpoint:
            for surface_id, surface in endpoint.routing_surfaces.items():
                for connected_endpoint in surface.reachable_endpoints:
                    connected_liquidity = self.liquidity_manifold.get(connected_endpoint, 0.0)
                    # Liquidity propagates with decay based on trust density
                    propagated_value = economic_value * surface.trust_density * 0.1
                    self.liquidity_manifold[connected_endpoint] = connected_liquidity + propagated_value
    
    def _inverse_mining(self, economic_value: float):
        """Burn supply based on verified useful work (inverse mining)"""
        # Burn rate: 0.001 tokens per unit of economic value
        burn_amount = economic_value * 0.001
        
        if burn_amount > 0 and self.circulating_supply > burn_amount:
            self.circulating_supply -= burn_amount
            self.inverse_mining_burn += burn_amount
            logger.info(f"Inverse mining: burned {burn_amount} tokens")
    
    def calculate_geodesic_path(
        self,
        from_endpoint: str,
        to_endpoint: str,
        constraints: Dict = None
    ) -> Optional[List[str]]:
        """
        Calculate optimal path through the manifold using geodesic routing.
        Considers trust density, slippage, proof risk, settlement cost, and latency.
        """
        constraints = constraints or {}
        
        if from_endpoint not in self.endpoints or to_endpoint not in self.endpoints:
            return None
        
        # Simplified Dijkstra's algorithm for path finding
        # In production, would use more sophisticated routing algorithms
        
        visited = set()
        distances = {endpoint_id: float('inf') for endpoint_id in self.endpoints}
        previous = {endpoint_id: None for endpoint_id in self.endpoints}
        distances[from_endpoint] = 0
        
        while len(visited) < len(self.endpoints):
            # Find unvisited endpoint with minimum distance
            current = min(
                (ep for ep in self.endpoints if ep not in visited),
                key=lambda x: distances[x],
                default=None
            )
            
            if current is None or distances[current] == float('inf'):
                break
            
            visited.add(current)
            
            if current == to_endpoint:
                break
            
            # Explore neighbors through routing surfaces
            current_endpoint = self.endpoints[current]
            for surface in current_endpoint.routing_surfaces.values():
                for neighbor in surface.reachable_endpoints:
                    if neighbor not in visited:
                        # Calculate cost based on constraints
                        cost = self._calculate_path_cost(surface, constraints)
                        
                        if distances[current] + cost < distances[neighbor]:
                            distances[neighbor] = distances[current] + cost
                            previous[neighbor] = current
        
        # Reconstruct path
        if distances[to_endpoint] == float('inf'):
            return None
        
        path = []
        current = to_endpoint
        while current is not None:
            path.append(current)
            current = previous[current]
        
        path.reverse()
        
        # Cache the path
        self.geodesic_paths[(from_endpoint, to_endpoint)] = path
        
        return path
    
    def _calculate_path_cost(self, surface: RoutingSurface, constraints: Dict) -> float:
        """Calculate path cost based on routing surface and constraints"""
        base_cost = surface.cost_per_transaction
        
        # Adjust for trust density
        trust_adjustment = 1.0 - surface.trust_density
        
        # Adjust for latency
        latency_adjustment = surface.latency_ms / 1000.0
        
        # Adjust for capability requirements
        capability_adjustment = len(surface.capability_requirements) * 0.1
        
        total_cost = base_cost + trust_adjustment + latency_adjustment + capability_adjustment
        
        return total_cost
    
    def get_manifold_state(self) -> Dict:
        """Get comprehensive state of the Overmanifold"""
        return {
            'endpoints': len(self.endpoints),
            'state_transitions': len(self.state_transitions),
            'semantic_intents': len(self.semantic_intents),
            'total_liquidity': sum(self.liquidity_manifold.values()),
            'circulating_supply': self.circulating_supply,
            'inverse_mining_burn': self.inverse_mining_burn,
            'average_trust_density': sum(
                ep.trust_density for ep in self.endpoints.values()
            ) / len(self.endpoints) if self.endpoints else 0.0,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Example usage of the Overmanifold engine"""
    engine = OvermanifoldEngine()
    
    # Create an endpoint
    messaging_capability = Capability(
        capability_type=CapabilityType.MESSAGING_REACHABILITY,
        strength=0.8,
        last_verified=datetime.now().isoformat(),
        proof_hash=hashlib.sha256(b"messaging_proof").hexdigest(),
        economic_weight=1.0,
        metadata={}
    )
    
    compute_capability = Capability(
        capability_type=CapabilityType.COMPUTATION_AVAILABILITY,
        strength=0.9,
        last_verified=datetime.now().isoformat(),
        proof_hash=hashlib.sha256(b"compute_proof").hexdigest(),
        economic_weight=1.5,
        metadata={}
    )
    
    # Generate key pair
    private_key = nacl.signing.SigningKey.generate()
    public_key = private_key.verify_key.encode(encoder=nacl.encoding.RawEncoder).hex()
    
    endpoint = engine.create_endpoint(
        public_key=public_key,
        private_key=private_key.encode(encoder=nacl.encoding.RawEncoder).hex(),
        initial_capabilities=[messaging_capability, compute_capability],
        metadata={"name": "Test Endpoint"}
    )
    
    print(f"Created endpoint: {endpoint.endpoint_id}")
    print(f"Total economic value: {endpoint.total_economic_value}")
    
    # Create a state transition
    transition = engine.create_state_transition(
        endpoint_id=endpoint.endpoint_id,
        transition_type=StateTransitionType.MESSAGE_SEND,
        semantic_intent="Send message to network",
        from_state="idle",
        to_state="messaging",
        economic_value=100.0,
        capability_requirements=[CapabilityType.MESSAGING_REACHABILITY],
        metadata={"recipient": "network"}
    )
    
    if transition:
        print(f"\nState transition executed: {transition.transition_id}")
        print(f"Economic value: {transition.economic_value}")
    
    # Create semantic intent
    intent = engine.create_semantic_intent(
        semantic_content="Coordinate resource allocation",
        intent_type="resource_coordination",
        initial_interpretations=[
            ("allocate_to_validator", 0.6),
            ("allocate_to_computation", 0.4)
        ]
    )
    
    print(f"\nSemantic intent created: {intent.intent_id}")
    print(f"Ambiguous interpretations: {len(intent.ambiguous_interpretations)}")
    
    # Get manifold state
    state = engine.get_manifold_state()
    print(f"\nManifold State:")
    print(json.dumps(state, indent=2))


if __name__ == '__main__':
    main()