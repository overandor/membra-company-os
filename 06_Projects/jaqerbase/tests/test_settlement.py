import os
import stat

import pytest

from arrowcap.settlement import (
    SettlementReceipt,
    generate_keypair,
    load_or_create_signing_key,
    public_key_b64,
    sign_settlement,
    verify_settlement,
)

OUTCOME = {
    "answer_id": "answer-1",
    "claim_id": "claim-1",
    "passed": True,
    "reward_cents": 5000,
}


def test_sign_and_verify_round_trip():
    key = generate_keypair()
    receipt = sign_settlement(OUTCOME, "deadbeef" * 8, key)
    assert verify_settlement(receipt) is True


def test_verify_detects_tampered_outcome():
    key = generate_keypair()
    receipt = sign_settlement(OUTCOME, "deadbeef" * 8, key)
    receipt.outcome["reward_cents"] = 999999
    assert verify_settlement(receipt) is False


def test_verify_detects_tampered_signature():
    key = generate_keypair()
    receipt = sign_settlement(OUTCOME, "deadbeef" * 8, key)
    receipt.signature_b64 = receipt.signature_b64[:-4] + "AAAA"
    assert verify_settlement(receipt) is False


def test_verify_rejects_unsupported_scheme():
    key = generate_keypair()
    receipt = sign_settlement(OUTCOME, "deadbeef" * 8, key)
    receipt.scheme = "rsa-9999"
    with pytest.raises(ValueError):
        verify_settlement(receipt)


def test_receipt_round_trips_through_dict():
    key = generate_keypair()
    receipt = sign_settlement(OUTCOME, "deadbeef" * 8, key)
    restored = SettlementReceipt.from_dict(receipt.to_dict())
    assert verify_settlement(restored) is True
    assert restored.receipt_id == receipt.receipt_id


def test_load_or_create_signing_key_persists_and_reloads(tmp_path):
    key_path = os.path.join(tmp_path, "signing.key")
    key1 = load_or_create_signing_key(key_path)
    assert os.path.exists(key_path)
    mode = stat.S_IMODE(os.stat(key_path).st_mode)
    assert mode == 0o600

    key2 = load_or_create_signing_key(key_path)
    assert public_key_b64(key1) == public_key_b64(key2)


def test_different_keys_produce_different_public_keys():
    key1 = generate_keypair()
    key2 = generate_keypair()
    assert public_key_b64(key1) != public_key_b64(key2)
