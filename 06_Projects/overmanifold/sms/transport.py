"""
Overmanifold SMS Intent Transport Layer
Cryptographic packet semantics for SMS-based intent transport.
Converts human communication into cryptographically addressable semantic packets.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from ..core.types import Hash, EndpointID, StateTransition, StateTransitionType, TransportType
from ..core.config import SMSConfig


@dataclass
class SMSPacket:
    """Cryptographic SMS packet for intent transport."""
    packet_id: Hash
    sender_endpoint: EndpointID
    recipient_endpoint: EndpointID
    intent_data: Dict
    timestamp: datetime
    nonce: str
    signature: Optional[str] = None
    encrypted: bool = False
    packet_sequence: int = 0
    
    def to_dict(self) -> Dict:
        """Convert packet to dictionary."""
        return {
            "packet_id": str(self.packet_id),
            "sender": str(self.sender_endpoint),
            "recipient": str(self.recipient_endpoint),
            "intent_data": self.intent_data,
            "timestamp": self.timestamp.isoformat(),
            "nonce": self.nonce,
            "signature": self.signature,
            "encrypted": self.encrypted,
            "packet_sequence": self.packet_sequence
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SMSPacket':
        """Create packet from dictionary."""
        return cls(
            packet_id=Hash(data["packet_id"]),
            sender_endpoint=EndpointID(*data["sender"].split(":")[-2:]),
            recipient_endpoint=EndpointID(*data["recipient"].split(":")[-2:]),
            intent_data=data["intent_data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            nonce=data["nonce"],
            signature=data.get("signature"),
            encrypted=data.get("encrypted", False),
            packet_sequence=data.get("packet_sequence", 0)
        )


@dataclass
class SemanticIntent:
    """Semantic intent extracted from SMS communication."""
    intent_id: Hash
    original_message: str
    parsed_intent: Dict
    confidence: float
    intent_type: str
    parameters: Dict
    requires_settlement: bool = False
    settlement_conditions: Optional[Dict] = None


class IntentParser:
    """
    Parser for extracting semantic intent from SMS messages.
    Converts natural language to structured economic intent.
    """
    
    def __init__(self):
        self.intent_patterns = {
            "transfer": {
                "keywords": ["send", "transfer", "pay", "give"],
                "required_params": ["amount", "recipient"]
            },
            "swap": {
                "keywords": ["swap", "exchange", "convert"],
                "required_params": ["from_token", "to_token", "amount"]
            },
            "stake": {
                "keywords": ["stake", "lock", "deposit"],
                "required_params": ["amount", "token"]
            },
            "query": {
                "keywords": ["balance", "status", "check"],
                "required_params": ["target"]
            },
            "approve": {
                "keywords": ["approve", "authorize", "permit"],
                "required_params": ["spender", "amount"]
            }
        }
    
    def parse_intent(self, message: str) -> Tuple[Optional[SemanticIntent], float]:
        """
        Parse semantic intent from SMS message.
        Returns intent and confidence score.
        """
        message_lower = message.lower()
        best_intent = None
        best_confidence = 0.0
        
        for intent_type, pattern in self.intent_patterns.items():
            confidence = self._calculate_intent_confidence(message_lower, pattern["keywords"])
            
            if confidence > best_confidence:
                best_confidence = confidence
                parsed_params = self._extract_parameters(message, pattern["required_params"])
                
                if parsed_params or not pattern["required_params"]:
                    best_intent = SemanticIntent(
                        intent_id=Hash.from_data(message),
                        original_message=message,
                        parsed_intent={
                            "type": intent_type,
                            "parameters": parsed_params
                        },
                        confidence=confidence,
                        intent_type=intent_type,
                        parameters=parsed_params,
                        requires_settlement=intent_type in ["transfer", "swap", "approve"]
                    )
        
        return best_intent, best_confidence
    
    def _calculate_intent_confidence(self, message: str, keywords: List[str]) -> float:
        """Calculate confidence score for intent type."""
        keyword_count = sum(1 for keyword in keywords if keyword in message)
        return min(keyword_count / len(keywords), 1.0)
    
    def _extract_parameters(self, message: str, required_params: List[str]) -> Dict:
        """Extract parameters from message (simplified implementation)."""
        # In production, this would use NLP/ML for better extraction
        params = {}
        
        # Simple pattern matching for demonstration
        if "amount" in required_params:
            # Look for numbers in the message
            import re
            amounts = re.findall(r'\d+\.?\d*', message)
            if amounts:
                params["amount"] = float(amounts[0])
        
        if "recipient" in required_params or "spender" in required_params:
            # Look for addresses or identifiers
            import re
            addresses = re.findall(r'[a-zA-Z0-9]{32,}', message)
            if addresses:
                params["recipient" if "recipient" in required_params else "spender"] = addresses[0]
        
        return params


class SMSEncryption:
    """
    Encryption utilities for SMS packets.
    Uses AES-256-GCM for authenticated encryption.
    """
    
    @staticmethod
    def encrypt_packet(packet_data: Dict, encryption_key: bytes) -> Tuple[str, str]:
        """
        Encrypt packet data.
        Returns (encrypted_data_base64, nonce_base64).
        """
        nonce = bytes.fromhex(hex(int(datetime.utcnow().timestamp() * 1000000))[2:].zfill(24))
        
        # Serialize packet data
        json_data = json.dumps(packet_data, sort_keys=True).encode('utf-8')
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(json_data) + encryptor.finalize()
        
        # Return base64 encoded data and nonce
        return (
            base64.b64encode(encrypted_data + encryptor.tag).decode('utf-8'),
            base64.b64encode(nonce).decode('utf-8')
        )
    
    @staticmethod
    def decrypt_packet(encrypted_data_base64: str, nonce_base64: str, 
                      encryption_key: bytes) -> Optional[Dict]:
        """
        Decrypt packet data.
        Returns decrypted dictionary or None if decryption fails.
        """
        try:
            # Decode base64
            encrypted_data_with_tag = base64.b64decode(encrypted_data_base64)
            nonce = base64.b64decode(nonce_base64)
            
            # Split data and tag
            encrypted_data = encrypted_data_with_tag[:-16]
            tag = encrypted_data_with_tag[-16:]
            
            # Decrypt
            cipher = Cipher(
                algorithms.AES(encryption_key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return None
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))


class SMSTransportLayer:
    """
    SMS transport layer for Overmanifold intent transport.
    Handles packet creation, encryption, transmission, and processing.
    """
    
    def __init__(self, config: SMSConfig):
        self.config = config
        self.intent_parser = IntentParser()
        self.encryption = SMSEncryption()
        self.packet_queue: List[SMSPacket] = []
        self.sent_packets: Dict[str, SMSPacket] = {}
        self.received_packets: Dict[str, SMSPacket] = {}
        self.encryption_key: Optional[bytes] = None
    
    def set_encryption_key(self, key: bytes) -> None:
        """Set encryption key for packet encryption."""
        self.encryption_key = key
    
    def create_packet(self, sender: EndpointID, recipient: EndpointID,
                     message: str) -> Tuple[Optional[SMSPacket], Optional[SemanticIntent]]:
        """
        Create SMS packet from message.
        Returns (packet, parsed_intent).
        """
        # Parse semantic intent
        intent, confidence = self.intent_parser.parse_intent(message)
        
        if not intent or confidence < 0.5:
            return None, intent
        
        # Create packet
        packet = SMSPacket(
            packet_id=Hash.from_data(message + str(datetime.utcnow())),
            sender_endpoint=sender,
            recipient_endpoint=recipient,
            intent_data=intent.parsed_intent,
            timestamp=datetime.utcnow(),
            nonce=base64.b64encode(bytes.fromhex(hex(int(datetime.utcnow().timestamp() * 1000000))[2:].zfill(16))).decode('utf-8'),
            encrypted=self.config.encryption_enabled,
            packet_sequence=len(self.sent_packets)
        )
        
        return packet, intent
    
    def encrypt_packet(self, packet: SMSPacket) -> Optional[str]:
        """Encrypt packet for transmission."""
        if not self.encryption_key:
            return None
        
        packet_data = packet.to_dict()
        encrypted_data, nonce = self.encryption.encrypt_packet(packet_data, self.encryption_key)
        
        # Combine for SMS transmission
        combined = f"{nonce}:{encrypted_data}"
        
        # Check size constraint
        if len(combined) > self.config.max_packet_size:
            return None
        
        return combined
    
    def decrypt_packet(self, encrypted_message: str) -> Optional[SMSPacket]:
        """Decrypt received SMS packet."""
        if not self.encryption_key:
            return None
        
        try:
            nonce_b64, encrypted_data_b64 = encrypted_message.split(":", 1)
            packet_data = self.encryption.decrypt_packet(encrypted_data_b64, nonce_b64, self.encryption_key)
            
            if packet_data:
                return SMSPacket.from_dict(packet_data)
        except Exception:
            return None
        
        return None
    
    def queue_packet(self, packet: SMSPacket) -> bool:
        """Queue packet for transmission."""
        if len(self.packet_queue) < 1000:  # Prevent unlimited queue growth
            self.packet_queue.append(packet)
            return True
        return False
    
    def process_queue(self) -> List[str]:
        """
        Process packet queue and return transmitted packet IDs.
        In production, this would interface with SMS gateway API.
        """
        transmitted_ids = []
        
        for packet in self.packet_queue[:10]:  # Process in batches
            encrypted = self.encrypt_packet(packet)
            if encrypted:
                # Simulate transmission
                self.sent_packets[str(packet.packet_id)] = packet
                transmitted_ids.append(str(packet.packet_id))
        
        # Clear processed packets
        self.packet_queue = self.packet_queue[10:]
        
        return transmitted_ids
    
    def receive_packet(self, encrypted_message: str) -> Optional[SMSPacket]:
        """Receive and process incoming SMS packet."""
        packet = self.decrypt_packet(encrypted_message)
        if packet:
            self.received_packets[str(packet.packet_id)] = packet
            return packet
        return None
    
    def packet_to_state_transition(self, packet: SMSPacket) -> StateTransition:
        """Convert SMS packet to state transition."""
        return StateTransition(
            transition_id=packet.packet_id,
            transition_type=StateTransitionType.SMS_EVENT,
            from_state=Hash.from_data("received"),
            to_state=Hash.from_data("processed"),
            timestamp=packet.timestamp,
            actor=packet.sender_endpoint,
            transport=TransportType.SMS
        )
    
    def get_transport_statistics(self) -> Dict:
        """Get SMS transport layer statistics."""
        return {
            "queued_packets": len(self.packet_queue),
            "sent_packets": len(self.sent_packets),
            "received_packets": len(self.received_packets),
            "encryption_enabled": self.config.encryption_enabled,
            "max_packet_size": self.config.max_packet_size
        }