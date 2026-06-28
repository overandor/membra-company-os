"""Signed settlement receipts.

A SettlementOutcome (escrow.py) describes what happened to the money. A
SettlementReceipt wraps that outcome plus the answer's commitment hash in a
canonical JSON document and signs it with Ed25519, producing the kind of
self-verifying, low-lambda receipt glyph described in BlurHash64 Section 6
(the Receipt level): anyone holding the signer's public key can verify the
claim, time, and resolution without trusting the parties or re-running the
oracle.

The `scheme` field is carried explicitly in every receipt so that verifiers
can branch on signature algorithm; this is the crypto-agility the BlurHash64
paper recommends (Section 9) for receipts that need to survive algorithm
migrations (e.g. to a post-quantum scheme) without changing the receipt
format.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

SCHEME = "ed25519"


def canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def generate_keypair() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


def load_or_create_signing_key(path: str) -> Ed25519PrivateKey:
    """Load a raw 32-byte Ed25519 private key from `path`, generating and
    persisting one with 0600 permissions if it does not yet exist. This is
    the protocol notary's real signing identity -- not a placeholder key."""
    if os.path.exists(path):
        with open(path, "rb") as fh:
            raw = fh.read()
        return Ed25519PrivateKey.from_private_bytes(raw)
    key = generate_keypair()
    raw = key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(raw)
    return key


def public_key_b64(private_key: Ed25519PrivateKey) -> str:
    import base64

    raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(raw).decode("ascii")


@dataclass
class SettlementReceipt:
    receipt_id: str
    scheme: str
    answer_id: str
    claim_id: str
    commitment_sha256: str
    outcome: dict
    issued_at: float
    signer_public_key_b64: str
    signature_b64: str

    def _signed_payload(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "scheme": self.scheme,
            "answer_id": self.answer_id,
            "claim_id": self.claim_id,
            "commitment_sha256": self.commitment_sha256,
            "outcome": self.outcome,
            "issued_at": self.issued_at,
            "signer_public_key_b64": self.signer_public_key_b64,
        }

    def to_dict(self) -> dict:
        return {**self._signed_payload(), "signature_b64": self.signature_b64}

    @classmethod
    def from_dict(cls, data: dict) -> "SettlementReceipt":
        return cls(**data)


def sign_settlement(
    outcome_dict: dict, commitment_sha256: str, private_key: Ed25519PrivateKey,
) -> SettlementReceipt:
    import base64

    receipt = SettlementReceipt(
        receipt_id=f"receipt-{uuid.uuid4().hex[:16]}",
        scheme=SCHEME,
        answer_id=outcome_dict["answer_id"],
        claim_id=outcome_dict["claim_id"],
        commitment_sha256=commitment_sha256,
        outcome=outcome_dict,
        issued_at=time.time(),
        signer_public_key_b64=public_key_b64(private_key),
        signature_b64="",
    )
    payload = canonical_json(receipt._signed_payload())
    signature = private_key.sign(payload)
    receipt.signature_b64 = base64.b64encode(signature).decode("ascii")
    return receipt


def verify_settlement(receipt: SettlementReceipt) -> bool:
    import base64

    if receipt.scheme != SCHEME:
        raise ValueError(f"unsupported signature scheme: {receipt.scheme}")
    public_key = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(receipt.signer_public_key_b64)
    )
    payload = canonical_json(receipt._signed_payload())
    try:
        public_key.verify(base64.b64decode(receipt.signature_b64), payload)
        return True
    except InvalidSignature:
        return False
