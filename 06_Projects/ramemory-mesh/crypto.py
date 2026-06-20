"""
crypto.py — RAMemory Mesh cryptography (REFERENCE implementation).

Hard rule from the spec: no raw secrets in peer RAM; all chunks encrypted
before leaving the device; receipts are signed; owner can revoke.

This reference uses only the Python stdlib so the demo runs anywhere:
  * sealing  = hash-based stream cipher (SHA-256 keystream) + HMAC-SHA-256
               in encrypt-then-MAC form (authenticated, tamper-evident);
  * identity = device secret -> public id via SHA-256;
  * signing  = HMAC-SHA-256 over a canonical message.

PRODUCTION SWAP (documented, not optional): replace `seal/open_` with
libsodium XChaCha20-Poly1305 and `sign/verify`/identity with Ed25519
(age for at-rest). The interfaces below are intentionally drop-in.
"""
from __future__ import annotations
import hashlib, hmac, secrets

_NONCE = 16
_TAG = 32


def device_keypair() -> tuple[bytes, str]:
    """Return (secret, device_id). device_id is public; secret never leaves device."""
    secret = secrets.token_bytes(32)
    return secret, "dev_" + hashlib.sha256(secret).hexdigest()[:16]


def group_key() -> bytes:
    """Symmetric key shared across an owner's *trusted* device group (the only parties who can open chunks)."""
    return secrets.token_bytes(32)


def content_id(data: bytes) -> str:
    """Content address: object_id = sha256(bytes)."""
    return hashlib.sha256(data).hexdigest()


def _keystream(key: bytes, nonce: bytes, n: int) -> bytes:
    out, ctr = bytearray(), 0
    while len(out) < n:
        out += hashlib.sha256(key + nonce + ctr.to_bytes(8, "big")).digest()
        ctr += 1
    return bytes(out[:n])


def seal(key: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    """Authenticated encryption: returns nonce || tag || ciphertext."""
    nonce = secrets.token_bytes(_NONCE)
    ks = _keystream(key, nonce, len(plaintext))
    ct = bytes(a ^ b for a, b in zip(plaintext, ks))
    tag = hmac.new(key, nonce + ct + aad, hashlib.sha256).digest()
    return nonce + tag + ct


def open_(key: bytes, blob: bytes, aad: bytes = b"") -> bytes:
    """Verify + decrypt. Raises ValueError on tamper / wrong key (privacy guarantee)."""
    nonce, tag, ct = blob[:_NONCE], blob[_NONCE:_NONCE + _TAG], blob[_NONCE + _TAG:]
    expect = hmac.new(key, nonce + ct + aad, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expect):
        raise ValueError("auth failed: tampered chunk or unauthorized device")
    ks = _keystream(key, nonce, len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks))


def sign(secret: bytes, message: bytes) -> str:
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify(secret: bytes, message: bytes, signature: str) -> bool:
    return hmac.compare_digest(signature, sign(secret, message))
