"""
Overmanifold Endpoint Identity System
Transport-independent identity management with DID integration.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
import json
import hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from ..core.types import (
    EndpointID,
    CapabilitySurface,
    CapabilityType,
    Hash,
    TransportType,
    SettlementMapping
)


class Endpoint:
    """
    Overmanifold Endpoint - transport-independent identity manifold.
    Aggregates handlers, proofs, capabilities, settlement mappings, routing surfaces,
    storage roots, and economic permissions into one offline-resolvable semantic identity.
    """
    
    def __init__(self, endpoint_id: EndpointID):
        self.endpoint_id = endpoint_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Identity components
        self.public_key: Optional[str] = None
        self.private_key: Optional[bytes] = None
        self.verifiable_credentials: List[Dict] = []
        
        # Capability surfaces
        self.capabilities: Dict[CapabilityType, CapabilitySurface] = {}
        
        # Transport handlers
        self.transport_handlers: Dict[TransportType, Dict] = {}
        
        # Settlement mappings
        self.settlement_mappings: List[SettlementMapping] = []
        
        # Routing surfaces
        self.routing_surfaces: Dict[str, Dict] = {}
        
        # Storage roots
        self.storage_roots: Dict[str, Hash] = {}
        
        # Economic permissions
        self.economic_permissions: Dict[str, bool] = {}
        
        # Trust scores
        self.trust_score: float = 0.0
        self.reputation_score: float = 0.0
        
        # Metadata
        self.metadata: Dict = {}
    
    def generate_keypair(self) -> None:
        """Generate Ed25519 keypair for the endpoint."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        self.private_key = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        self.public_key = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()
    
    def add_capability(self, capability: CapabilitySurface) -> None:
        """Add capability surface to endpoint."""
        self.capabilities[capability.capability_type] = capability
        self.updated_at = datetime.utcnow()
    
    def remove_capability(self, capability_type: CapabilityType) -> None:
        """Remove capability from endpoint."""
        if capability_type in self.capabilities:
            del self.capabilities[capability_type]
            self.updated_at = datetime.utcnow()
    
    def has_capability(self, capability_type: CapabilityType) -> bool:
        """Check if endpoint has specific capability."""
        capability = self.capabilities.get(capability_type)
        return capability is not None and capability.is_available()
    
    def add_transport_handler(self, transport: TransportType, handler_config: Dict) -> None:
        """Add transport handler configuration."""
        self.transport_handlers[transport] = handler_config
        self.updated_at = datetime.utcnow()
    
    def add_settlement_mapping(self, mapping: SettlementMapping) -> None:
        """Add settlement mapping to endpoint."""
        self.settlement_mappings.append(mapping)
        self.updated_at = datetime.utcnow()
    
    def add_storage_root(self, name: str, root_hash: Hash) -> None:
        """Add storage root hash."""
        self.storage_roots[name] = root_hash
        self.updated_at = datetime.utcnow()
    
    def set_economic_permission(self, permission: str, allowed: bool) -> None:
        """Set economic permission."""
        self.economic_permissions[permission] = allowed
        self.updated_at = datetime.utcnow()
    
    def has_economic_permission(self, permission: str) -> bool:
        """Check if endpoint has economic permission."""
        return self.economic_permissions.get(permission, False)
    
    def update_trust_score(self, delta: float) -> None:
        """Update trust score with delta value."""
        self.trust_score = max(0.0, min(1.0, self.trust_score + delta))
        self.updated_at = datetime.utcnow()
    
    def update_reputation_score(self, delta: float) -> None:
        """Update reputation score with delta value."""
        self.reputation_score = max(0.0, min(1.0, self.reputation_score + delta))
        self.updated_at = datetime.utcnow()
    
    def sign_data(self, data: str) -> str:
        """Sign data with endpoint's private key."""
        if not self.private_key:
            raise ValueError("No private key available for signing")
        
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key)
        signature = private_key.sign(data.encode('utf-8'))
        return signature.hex()
    
    def verify_signature(self, data: str, signature: str, public_key: str) -> bool:
        """Verify signature against data."""
        try:
            public_key_bytes = bytes.fromhex(public_key)
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            signature_bytes = bytes.fromhex(signature)
            public_key_obj.verify(signature_bytes, data.encode('utf-8'))
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict:
        """Convert endpoint to dictionary representation."""
        return {
            "endpoint_id": str(self.endpoint_id),
            "public_key": self.public_key,
            "capabilities": {
                ct.value: {
                    "type": cs.capability_type.value,
                    "parameters": cs.parameters,
                    "trust_score": cs.trust_score,
                    "availability": cs.availability,
                    "last_verified": cs.last_verified.isoformat() if cs.last_verified else None
                }
                for ct, cs in self.capabilities.items()
            },
            "transport_handlers": {
                t.value: config for t, config in self.transport_handlers.items()
            },
            "trust_score": self.trust_score,
            "reputation_score": self.reputation_score,
            "economic_permissions": self.economic_permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Endpoint':
        """Create endpoint from dictionary representation."""
        endpoint_id = EndpointID(data["endpoint_id"].split(":")[-2], data["endpoint_id"].split(":")[-1])
        endpoint = cls(endpoint_id)
        
        endpoint.public_key = data.get("public_key")
        endpoint.trust_score = data.get("trust_score", 0.0)
        endpoint.reputation_score = data.get("reputation_score", 0.0)
        endpoint.economic_permissions = data.get("economic_permissions", {})
        endpoint.metadata = data.get("metadata", {})
        
        if "created_at" in data:
            endpoint.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            endpoint.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return endpoint
    
    def compute_hash(self) -> Hash:
        """Compute hash of endpoint state."""
        data = self.to_dict()
        return Hash.from_data(data)


class EndpointRegistry:
    """Registry for managing Overmanifold endpoints."""
    
    def __init__(self):
        self.endpoints: Dict[str, Endpoint] = {}
        self.did_index: Dict[str, str] = {}  # DID to endpoint ID mapping
    
    def register_endpoint(self, endpoint: Endpoint) -> str:
        """Register endpoint in registry."""
        endpoint_id = str(endpoint.endpoint_id)
        self.endpoints[endpoint_id] = endpoint
        self.did_index[str(endpoint.endpoint_id)] = endpoint_id
        return endpoint_id
    
    def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister endpoint from registry."""
        if endpoint_id in self.endpoints:
            endpoint = self.endpoints[endpoint_id]
            del self.did_index[str(endpoint.endpoint_id)]
            del self.endpoints[endpoint_id]
            return True
        return False
    
    def get_endpoint(self, endpoint_id: str) -> Optional[Endpoint]:
        """Get endpoint by ID."""
        return self.endpoints.get(endpoint_id)
    
    def get_endpoint_by_did(self, did: str) -> Optional[Endpoint]:
        """Get endpoint by DID."""
        endpoint_id = self.did_index.get(did)
        if endpoint_id:
            return self.endpoints.get(endpoint_id)
        return None
    
    def find_endpoints_by_capability(self, capability_type: CapabilityType) -> List[Endpoint]:
        """Find endpoints with specific capability."""
        return [
            endpoint for endpoint in self.endpoints.values()
            if endpoint.has_capability(capability_type)
        ]
    
    def find_endpoints_by_trust_threshold(self, min_trust: float) -> List[Endpoint]:
        """Find endpoints above trust threshold."""
        return [
            endpoint for endpoint in self.endpoints.values()
            if endpoint.trust_score >= min_trust
        ]
    
    def get_topology_snapshot(self) -> Dict:
        """Get snapshot of endpoint topology."""
        return {
            "total_endpoints": len(self.endpoints),
            "endpoints": {
                endpoint_id: endpoint.to_dict()
                for endpoint_id, endpoint in self.endpoints.items()
            },
            "capability_distribution": self._analyze_capability_distribution(),
            "trust_distribution": self._analyze_trust_distribution()
        }
    
    def _analyze_capability_distribution(self) -> Dict:
        """Analyze distribution of capabilities across endpoints."""
        distribution = {}
        for endpoint in self.endpoints.values():
            for capability_type in endpoint.capabilities.keys():
                distribution[capability_type.value] = distribution.get(capability_type.value, 0) + 1
        return distribution
    
    def _analyze_trust_distribution(self) -> Dict:
        """Analyze distribution of trust scores."""
        scores = [endpoint.trust_score for endpoint in self.endpoints.values()]
        if not scores:
            return {}
        
        return {
            "min": min(scores),
            "max": max(scores),
            "average": sum(scores) / len(scores),
            "total": len(scores)
        }