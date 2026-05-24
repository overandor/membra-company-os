"""
Overmanifold Phone DID Mapping System
Maps phone numbers to wallet-linked telemetry endpoints.
Converts phone numbers into privacy-preserving DID-root credentials.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from ..core.types import EndpointID, Hash
from .did import DIDDocument, DIDGenerator


@dataclass
class PhoneDIDMapping:
    """Mapping between phone number and DID."""
    phone_hash: Hash  # Hashed phone number for privacy
    did: str
    wallet_address: str
    telemetry_endpoint: EndpointID
    created_at: datetime
    verified: bool = False
    verification_method: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert mapping to dictionary."""
        return {
            "phone_hash": str(self.phone_hash),
            "did": self.did,
            "wallet_address": self.wallet_address,
            "telemetry_endpoint": str(self.telemetry_endpoint),
            "created_at": self.created_at.isoformat(),
            "verified": self.verified,
            "verification_method": self.verification_method
        }


@dataclass
class TelemetryData:
    """Telemetry data from phone-linked endpoint."""
    endpoint_id: EndpointID
    data_type: str
    data: Dict
    timestamp: datetime
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert telemetry to dictionary."""
        return {
            "endpoint_id": str(self.endpoint_id),
            "data_type": self.data_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature
        }


class PhoneHasher:
    """
    Privacy-preserving phone number hashing.
    Uses salted hashing to protect phone number privacy.
    """
    
    def __init__(self, salt: Optional[str] = None):
        self.salt = salt or "overmanifold_default_salt"
    
    def hash_phone(self, phone_number: str) -> Hash:
        """
        Hash phone number with salt for privacy.
        Phone numbers are never stored in plaintext.
        """
        # Normalize phone number
        normalized = self._normalize_phone(phone_number)
        
        # Create salted hash
        salted_data = f"{normalized}{self.salt}".encode('utf-8')
        hash_value = hashlib.sha256(salted_data).hexdigest()
        
        return Hash(hash_value)
    
    def _normalize_phone(self, phone_number: str) -> str:
        """Normalize phone number format."""
        # Remove all non-numeric characters
        digits_only = ''.join(c for c in phone_number if c.isdigit())
        
        # Ensure country code (assume +1 if missing for US numbers)
        if len(digits_only) == 10:
            digits_only = f"1{digits_only}"
        
        return digits_only


class PhoneDIDRegistry:
    """
    Registry for phone-to-DID mappings.
    Manages the relationship between phone numbers and wallet endpoints.
    """
    
    def __init__(self):
        self.mappings: Dict[Hash, PhoneDIDMapping] = {}
        self.did_index: Dict[str, Hash] = {}  # DID -> phone_hash
        self.wallet_index: Dict[str, Hash] = {}  # wallet_address -> phone_hash
        self.phone_hasher = PhoneHasher()
        self.did_generator = DIDGenerator()
    
    def register_phone(self, phone_number: str, wallet_address: str, 
                      namespace: str = "phone") -> PhoneDIDMapping:
        """
        Register phone number and create DID mapping.
        Returns the mapping object.
        """
        # Hash phone number for privacy
        phone_hash = self.phone_hasher.hash_phone(phone_number)
        
        # Generate DID for phone
        local_id = phone_hash.value[:16]
        did = self.did_generator.generate_overmanifold_did(namespace, local_id)
        
        # Create telemetry endpoint
        telemetry_endpoint = EndpointID.generate("telemetry", local_id)
        
        # Create mapping
        mapping = PhoneDIDMapping(
            phone_hash=phone_hash,
            did=did,
            wallet_address=wallet_address,
            telemetry_endpoint=telemetry_endpoint,
            created_at=datetime.utcnow()
        )
        
        # Store mapping
        self.mappings[phone_hash] = mapping
        self.did_index[did] = phone_hash
        self.wallet_index[wallet_address] = phone_hash
        
        return mapping
    
    def verify_phone(self, phone_number: str, verification_code: str) -> bool:
        """
        Verify phone number ownership.
        In production, this would interface with SMS verification services.
        """
        phone_hash = self.phone_hasher.hash_phone(phone_number)
        mapping = self.mappings.get(phone_hash)
        
        if not mapping:
            return False
        
        # Simplified verification - in production would use actual SMS code
        mapping.verified = True
        mapping.verification_method = "sms_code"
        
        return True
    
    def get_mapping_by_phone(self, phone_number: str) -> Optional[PhoneDIDMapping]:
        """Get mapping by phone number."""
        phone_hash = self.phone_hasher.hash_phone(phone_number)
        return self.mappings.get(phone_hash)
    
    def get_mapping_by_did(self, did: str) -> Optional[PhoneDIDMapping]:
        """Get mapping by DID."""
        phone_hash = self.did_index.get(did)
        if phone_hash:
            return self.mappings.get(phone_hash)
        return None
    
    def get_mapping_by_wallet(self, wallet_address: str) -> Optional[PhoneDIDMapping]:
        """Get mapping by wallet address."""
        phone_hash = self.wallet_index.get(wallet_address)
        if phone_hash:
            return self.mappings.get(phone_hash)
        return None
    
    def update_wallet(self, phone_number: str, new_wallet_address: str) -> bool:
        """Update wallet address for phone number."""
        phone_hash = self.phone_hasher.hash_phone(phone_number)
        mapping = self.mappings.get(phone_hash)
        
        if not mapping:
            return False
        
        # Remove old wallet index
        old_wallet = mapping.wallet_address
        if old_wallet in self.wallet_index:
            del self.wallet_index[old_wallet]
        
        # Update mapping
        mapping.wallet_address = new_wallet_address
        self.wallet_index[new_wallet_address] = phone_hash
        
        return True
    
    def revoke_mapping(self, phone_number: str) -> bool:
        """Revoke phone DID mapping."""
        phone_hash = self.phone_hasher.hash_phone(phone_number)
        mapping = self.mappings.get(phone_hash)
        
        if not mapping:
            return False
        
        # Remove from indexes
        if mapping.did in self.did_index:
            del self.did_index[mapping.did]
        if mapping.wallet_address in self.wallet_index:
            del self.wallet_index[mapping.wallet_address]
        
        # Remove mapping
        del self.mappings[phone_hash]
        
        return True


class TelemetryCollector:
    """
    Collects telemetry data from phone-linked endpoints.
    Aggregates device and usage data for economic appraisal.
    """
    
    def __init__(self):
        self.telemetry_data: Dict[EndpointID, List[TelemetryData]] = {}
        self.aggregated_metrics: Dict[EndpointID, Dict] = {}
    
    def collect_telemetry(self, endpoint_id: EndpointID, data_type: str, 
                         data: Dict, signature: Optional[str] = None) -> TelemetryData:
        """Collect telemetry data from endpoint."""
        telemetry = TelemetryData(
            endpoint_id=endpoint_id,
            data_type=data_type,
            data=data,
            timestamp=datetime.utcnow(),
            signature=signature
        )
        
        if endpoint_id not in self.telemetry_data:
            self.telemetry_data[endpoint_id] = []
        
        self.telemetry_data[endpoint_id].append(telemetry)
        self._update_aggregated_metrics(endpoint_id)
        
        return telemetry
    
    def _update_aggregated_metrics(self, endpoint_id: EndpointID) -> None:
        """Update aggregated metrics for endpoint."""
        telemetry_list = self.telemetry_data.get(endpoint_id, [])
        
        if not telemetry_list:
            return
        
        # Calculate basic metrics
        total_data_points = len(telemetry_list)
        data_types = {}
        
        for telemetry in telemetry_list:
            data_types[telemetry.data_type] = data_types.get(telemetry.data_type, 0) + 1
        
        self.aggregated_metrics[endpoint_id] = {
            "total_data_points": total_data_points,
            "data_types": data_types,
            "first_seen": telemetry_list[0].timestamp.isoformat(),
            "last_seen": telemetry_list[-1].timestamp.isoformat(),
            "verified_count": sum(1 for t in telemetry_list if t.signature)
        }
    
    def get_telemetry_summary(self, endpoint_id: EndpointID) -> Optional[Dict]:
        """Get telemetry summary for endpoint."""
        return self.aggregated_metrics.get(endpoint_id)
    
    def get_recent_telemetry(self, endpoint_id: EndpointID, 
                           limit: int = 10) -> List[TelemetryData]:
        """Get recent telemetry data for endpoint."""
        telemetry_list = self.telemetry_data.get(endpoint_id, [])
        return telemetry_list[-limit:]


class PhoneWalletLinker:
    """
    Links phone DIDs to wallet addresses with cryptographic proofs.
    Enables phone-based wallet operations and verification.
    """
    
    def __init__(self):
        self.registry = PhoneDIDRegistry()
        self.telemetry_collector = TelemetryCollector()
        self.link_proofs: Dict[Hash, Dict] = {}
    
    def link_phone_to_wallet(self, phone_number: str, wallet_address: str,
                            signature: str) -> Tuple[PhoneDIDMapping, bool]:
        """
        Link phone number to wallet address with signature proof.
        Returns (mapping, success).
        """
        # Register phone
        mapping = self.registry.register_phone(phone_number, wallet_address)
        
        # Create link proof
        proof_data = {
            "phone_hash": str(mapping.phone_hash),
            "wallet_address": wallet_address,
            "did": mapping.did,
            "signature": signature,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        proof_hash = Hash.from_data(proof_data)
        self.link_proofs[proof_hash] = proof_data
        
        return mapping, True
    
    def verify_link(self, phone_number: str, wallet_address: str) -> bool:
        """Verify phone-to-wallet link."""
        mapping = self.registry.get_mapping_by_phone(phone_number)
        if not mapping:
            return False
        
        return mapping.wallet_address == wallet_address and mapping.verified
    
    def get_wallet_telemetry(self, wallet_address: str) -> Optional[Dict]:
        """Get telemetry data for wallet."""
        mapping = self.registry.get_mapping_by_wallet(wallet_address)
        if not mapping:
            return None
        
        return self.telemetry_collector.get_telemetry_summary(mapping.telemetry_endpoint)
    
    def generate_did_document(self, phone_number: str) -> Optional[DIDDocument]:
        """Generate DID document for phone number."""
        mapping = self.registry.get_mapping_by_phone(phone_number)
        if not mapping:
            return None
        
        did_doc = DIDDocument(mapping.did)
        did_doc.add_service(
            service_id=f"{mapping.did}#telemetry",
            type="TelemetryService",
            service_endpoint=str(mapping.telemetry_endpoint),
            properties={
                "wallet_address": mapping.wallet_address,
                "verified": mapping.verified
            }
        )
        
        return did_doc