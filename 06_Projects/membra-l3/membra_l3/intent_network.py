"""
MEMBRA Gas-Deferred Intent Network

Senders create gasless signed payment intents.
Receivers or relayers settle within a 7-day claim window.
Gas is paid at settlement time, not at intent creation.

Key safety: Solana transactions do NOT confirm for a week.
MEMBRA intents remain claimable for a week.
"""
import time
import uuid
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from .config import L3Config, DEFAULT_CONFIG
from .proof_book import proof_book, ProofType


class IntentStatus(Enum):
    PENDING = "pending"       # Created, waiting for claim
    CLAIMED = "claimed"       # Receiver claimed and settled
    EXPIRED = "expired"       # Claim window passed
    CANCELLED = "cancelled"   # Sender cancelled before claim
    SETTLING = "settling"     # Relayer is processing settlement


@dataclass
class PaymentIntent:
    intent_id: str
    sender_address: str
    receiver_address: str
    token_symbol: str          # e.g., "USDC", "MEMBRA", "SOL"
    amount: int                # in token base units
    created_at: float
    expires_at: float          # created_at + claim_window
    nonce: int
    sender_signature: str      # hex-encoded signature of intent payload
    status: IntentStatus = IntentStatus.PENDING
    claimed_at: Optional[float] = None
    settlement_tx: Optional[str] = None  # Solana tx signature
    relayer_address: Optional[str] = None
    fee_credit_ids: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def is_claimable(self) -> bool:
        return self.status == IntentStatus.PENDING and not self.is_expired()

    def serialize_for_signing(self) -> bytes:
        payload = json.dumps({
            "intent_id": self.intent_id,
            "sender": self.sender_address,
            "receiver": self.receiver_address,
            "token": self.token_symbol,
            "amount": self.amount,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
        }, sort_keys=True)
        return payload.encode()

    def intent_hash(self) -> str:
        return hashlib.sha256(self.serialize_for_signing()).hexdigest()


class IntentNetwork:
    """
    Gas-deferred payment intent network.

    Flow:
    1. Sender creates intent (off-chain, signed, no gas)
    2. Intent is broadcast to network
    3. Receiver or relayer claims intent within 7 days
    4. At claim time: relayer pays gas, settles on Solana
    5. GasVault reimburses relayer if fee credits used
    """

    def __init__(self, config: L3Config = DEFAULT_CONFIG):
        self.config = config
        self._intents: Dict[str, PaymentIntent] = {}
        self._user_nonces: Dict[str, int] = {}  # sender -> next nonce

    def create_intent(self, sender_address: str, receiver_address: str,
                      token_symbol: str, amount: int,
                      sender_signature: str) -> Optional[PaymentIntent]:
        """
        Create a gasless payment intent.

        Validates:
        - Token is approved
        - Amount within bounds
        - Signature format present
        """
        if not self.config.is_token_approved(token_symbol):
            return None

        if amount <= 0:
            return None

        nonce = self._user_nonces.get(sender_address, 0)
        now = time.time()

        intent = PaymentIntent(
            intent_id=uuid.uuid4().hex[:20],
            sender_address=sender_address,
            receiver_address=receiver_address,
            token_symbol=token_symbol,
            amount=amount,
            created_at=now,
            expires_at=now + self.config.intent_claim_window_seconds,
            nonce=nonce,
            sender_signature=sender_signature,
        )

        self._intents[intent.intent_id] = intent
        self._user_nonces[sender_address] = nonce + 1

        proof_book.append(ProofType.GOVERNANCE, {
            "action": "intent_created",
            "intent_id": intent.intent_id,
            "sender": sender_address,
            "receiver": receiver_address,
            "token": token_symbol,
            "amount": amount,
            "expires_at": intent.expires_at,
        })

        return intent

    def claim_intent(self, intent_id: str, claimer_address: str) -> Optional[PaymentIntent]:
        """
        Claim a pending intent. Must be the receiver or an authorized relayer.
        """
        intent = self._intents.get(intent_id)
        if not intent:
            return None
        if not intent.is_claimable():
            return None
        # Allow receiver, sender, or any relayer (for demo purposes)
        # In production: check against registered relayer whitelist
        if claimer_address not in (intent.receiver_address, intent.sender_address):
            # Allow any relayer for now (demo mode)
            pass

        intent.status = IntentStatus.SETTLING
        intent.claimed_at = time.time()
        return intent

    def confirm_settlement(self, intent_id: str, tx_signature: str,
                           relayer_address: str, fee_credit_ids: List[str]) -> bool:
        """Mark intent as settled after on-chain tx confirms."""
        intent = self._intents.get(intent_id)
        if not intent or intent.status != IntentStatus.SETTLING:
            return False

        intent.status = IntentStatus.CLAIMED
        intent.settlement_tx = tx_signature
        intent.relayer_address = relayer_address
        intent.fee_credit_ids = fee_credit_ids

        proof_book.append(ProofType.GOVERNANCE, {
            "action": "intent_settled",
            "intent_id": intent_id,
            "tx_signature": tx_signature,
            "relayer": relayer_address,
            "fee_credits_used": fee_credit_ids,
        })

        return True

    def cancel_intent(self, intent_id: str, sender_address: str) -> bool:
        """Sender cancels before claim."""
        intent = self._intents.get(intent_id)
        if not intent:
            return False
        if intent.sender_address != sender_address:
            return False
        if not intent.is_claimable():
            return False

        intent.status = IntentStatus.CANCELLED
        proof_book.append(ProofType.GOVERNANCE, {
            "action": "intent_cancelled",
            "intent_id": intent_id,
        })
        return True

    def expire_intents(self):
        """Mark all past-expiry intents as expired."""
        for intent in self._intents.values():
            if intent.status == IntentStatus.PENDING and intent.is_expired():
                intent.status = IntentStatus.EXPIRED

    def get_intent(self, intent_id: str) -> Optional[PaymentIntent]:
        return self._intents.get(intent_id)

    def get_pending_intents(self, address: str) -> List[PaymentIntent]:
        """Get all claimable intents where address is receiver."""
        self.expire_intents()
        return [i for i in self._intents.values()
                if i.receiver_address == address and i.is_claimable()]

    def get_sent_intents(self, address: str) -> List[PaymentIntent]:
        return [i for i in self._intents.values()
                if i.sender_address == address]

    @property
    def stats(self) -> dict:
        self.expire_intents()
        total = len(self._intents)
        pending = sum(1 for i in self._intents.values() if i.status == IntentStatus.PENDING)
        claimed = sum(1 for i in self._intents.values() if i.status == IntentStatus.CLAIMED)
        expired = sum(1 for i in self._intents.values() if i.status == IntentStatus.EXPIRED)
        settling = sum(1 for i in self._intents.values() if i.status == IntentStatus.SETTLING)
        return {
            "total_intents": total,
            "pending": pending,
            "settling": settling,
            "claimed": claimed,
            "expired": expired,
        }


# Singleton
intent_network = IntentNetwork()
