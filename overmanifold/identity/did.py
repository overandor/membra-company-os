"""
Overmanifold DID Integration
Decentralized Identifier implementation for Overmanifold endpoints.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid

from ..core.types import EndpointID, Hash


class DIDDocument:
    """
    DID Document representing a decentralized identifier.
    Follows W3C DID Core specification.
    """
    
    def __init__(self, did: str):
        self.did = did
        self.context = ["https://www.w3.org/ns/did/v1"]
        self.id = did
        self.created = datetime.utcnow()
        self.updated = datetime.utcnow()
        
        # DID components
        self.public_keys: List[Dict] = []
        self.authentication: List[Dict] = []
        self.assertion_method: List[Dict] = []
        self.capability_invocation: List[Dict] = []
        self.capability_delegation: List[Dict] = []
        self.services: List[Dict] = []
        self.verification_methods: List[Dict] = []
        
        # Overmanifold-specific extensions
        self.overmanifold_extensions: Dict = {}
    
    def add_verification_method(self, method_id: str, type: str, controller: str, 
                                public_key_base58: str) -> None:
        """Add verification method to DID document."""
        verification_method = {
            "id": method_id,
            "type": type,
            "controller": controller,
            "publicKeyBase58": public_key_base58
        }
        self.verification_methods.append(verification_method)
        self.updated = datetime.utcnow()
    
    def add_authentication(self, method_id: str) -> None:
        """Add authentication method."""
        self.authentication.append(method_id)
        self.updated = datetime.utcnow()
    
    def add_assertion_method(self, method_id: str) -> None:
        """Add assertion method."""
        self.assertion_method.append(method_id)
        self.updated = datetime.utcnow()
    
    def add_service(self, service_id: str, type: str, service_endpoint: str, 
                    properties: Optional[Dict] = None) -> None:
        """Add service endpoint to DID document."""
        service = {
            "id": service_id,
            "type": type,
            "serviceEndpoint": service_endpoint
        }
        if properties:
            service.update(properties)
        self.services.append(service)
        self.updated = datetime.utcnow()
    
    def add_overmanifold_extension(self, key: str, value: Any) -> None:
        """Add Overmanifold-specific extension."""
        self.overmanifold_extensions[key] = value
        self.updated = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert DID document to dictionary."""
        doc = {
            "@context": self.context,
            "id": self.id,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat()
        }
        
        if self.verification_methods:
            doc["verificationMethod"] = self.verification_methods
        
        if self.authentication:
            doc["authentication"] = self.authentication
        
        if self.assertion_method:
            doc["assertionMethod"] = self.assertion_method
        
        if self.services:
            doc["service"] = self.services
        
        if self.overmanifold_extensions:
            doc["overmanifoldExtensions"] = self.overmanifold_extensions
        
        return doc
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DIDDocument':
        """Create DID document from dictionary."""
        did_doc = cls(data["id"])
        
        if "created" in data:
            did_doc.created = datetime.fromisoformat(data["created"])
        if "updated" in data:
            did_doc.updated = datetime.fromisoformat(data["updated"])
        
        if "verificationMethod" in data:
            did_doc.verification_methods = data["verificationMethod"]
        if "authentication" in data:
            did_doc.authentication = data["authentication"]
        if "assertionMethod" in data:
            did_doc.assertion_method = data["assertionMethod"]
        if "service" in data:
            did_doc.services = data["service"]
        if "overmanifoldExtensions" in data:
            did_doc.overmanifold_extensions = data["overmanifoldExtensions"]
        
        return did_doc
    
    def compute_hash(self) -> Hash:
        """Compute hash of DID document."""
        return Hash.from_data(self.to_dict())


class DIDResolver:
    """
    DID Resolver for Overmanifold endpoints.
    Supports resolution of DIDs to DID documents.
    """
    
    def __init__(self):
        self.did_documents: Dict[str, DIDDocument] = {}
        self.resolution_cache: Dict[str, Dict] = {}
    
    def register_did_document(self, did_document: DIDDocument) -> None:
        """Register DID document in resolver."""
        self.did_documents[did_document.did] = did_document
        self.resolution_cache.clear()  # Clear cache on new registration
    
    def resolve(self, did: str, use_cache: bool = True) -> Optional[Dict]:
        """Resolve DID to DID document."""
        if use_cache and did in self.resolution_cache:
            return self.resolution_cache[did]
        
        did_document = self.did_documents.get(did)
        if did_document:
            result = did_document.to_dict()
            if use_cache:
                self.resolution_cache[did] = result
            return result
        
        return None
    
    def resolve_verification_method(self, did: str, method_id: str) -> Optional[Dict]:
        """Resolve specific verification method."""
        did_document = self.did_documents.get(did)
        if did_document:
            for method in did_document.verification_methods:
                if method["id"] == method_id:
                    return method
        return None
    
    def resolve_service(self, did: str, service_id: str) -> Optional[Dict]:
        """Resolve specific service endpoint."""
        did_document = self.did_documents.get(did)
        if did_document:
            for service in did_document.services:
                if service["id"] == service_id:
                    return service
        return None
    
    def deactivate_did(self, did: str) -> bool:
        """Deactivate DID (remove from registry)."""
        if did in self.did_documents:
            del self.did_documents[did]
            if did in self.resolution_cache:
                del self.resolution_cache[did]
            return True
        return False


class DIDGenerator:
    """
    Generator for creating Overmanifold DIDs.
    Supports multiple DID methods.
    """
    
    @staticmethod
    def generate_overmanifold_did(namespace: str, local_id: Optional[str] = None) -> str:
        """Generate Overmanifold DID."""
        if local_id is None:
            local_id = str(uuid.uuid4())
        return f"did:om:{namespace}:{local_id}"
    
    @staticmethod
    def generate_key_did(public_key: str) -> str:
        """Generate key-based DID."""
        # Simple implementation - in production would use proper key derivation
        return f"did:key:{public_key[:16]}"
    
    @staticmethod
    def generate_pkh_did(blockchain: str, address: str) -> str:
        """Generate public-key-hash DID (for blockchain addresses)."""
        return f"did:pkh:{blockchain}:{address}"
    
    @staticmethod
    def generate_web_did(domain: str, path: str = "") -> str:
        """Generate web-based DID."""
        did = f"did:web:{domain}"
        if path:
            did += f":{path}"
        return did


class DIDAuthentication:
    """
    Authentication utilities for DID operations.
    """
    
    @staticmethod
    def create_authentication_challenge(did: str, challenge_id: Optional[str] = None) -> Dict:
        """Create authentication challenge."""
        if challenge_id is None:
            challenge_id = str(uuid.uuid4())
        
        return {
            "challenge_id": challenge_id,
            "did": did,
            "timestamp": datetime.utcnow().isoformat(),
            "nonce": str(uuid.uuid4())
        }
    
    @staticmethod
    def verify_authentication_response(response: Dict, 
                                       expected_challenge_id: str) -> bool:
        """Verify authentication response."""
        return (
            "challenge_id" in response and
            response["challenge_id"] == expected_challenge_id and
            "signature" in response and
            "timestamp" in response
        )
    
    @staticmethod
    def create_capability_delegation(delegator_did: str, delegatee_did: str,
                                    capabilities: List[str]) -> Dict:
        """Create capability delegation."""
        return {
            "delegator": delegator_did,
            "delegatee": delegatee_did,
            "capabilities": capabilities,
            "created": datetime.utcnow().isoformat(),
            "expires": None,  # Can be set for time-limited delegation
            "delegation_id": str(uuid.uuid4())
        }