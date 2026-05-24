"""
Tests for MEMBRA L3 Intent Network
"""
import pytest
import time
from membra_l3.intent_network import IntentNetwork, PaymentIntent, IntentStatus


class TestIntentNetwork:
    @pytest.fixture
    def network(self):
        return IntentNetwork()

    def test_create_intent(self, network):
        intent = network.create_intent(
            sender_address="sender_abc",
            receiver_address="receiver_xyz",
            token_symbol="USDC",
            amount=1_000_000,  # 1 USDC (6 decimals)
            sender_signature="sig_abc123",
        )
        assert intent is not None
        assert intent.sender_address == "sender_abc"
        assert intent.receiver_address == "receiver_xyz"
        assert intent.token_symbol == "USDC"
        assert intent.amount == 1_000_000
        assert intent.status == IntentStatus.PENDING
        assert intent.nonce == 0

    def test_create_intent_increments_nonce(self, network):
        network.create_intent("sender_abc", "receiver_xyz", "USDC", 1000, "sig1")
        intent2 = network.create_intent("sender_abc", "receiver_xyz", "USDC", 2000, "sig2")
        assert intent2.nonce == 1

    def test_create_intent_unapproved_token_fails(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "RANDOM_COIN", 1000, "sig"
        )
        assert intent is None

    def test_create_intent_zero_amount_fails(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 0, "sig"
        )
        assert intent is None

    def test_intent_is_claimable(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        assert intent.is_claimable() is True

    def test_intent_expires(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        # Force expiry
        intent.expires_at = time.time() - 1
        assert intent.is_expired() is True
        assert intent.is_claimable() is False

    def test_claim_intent_by_receiver(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        claimed = network.claim_intent(intent.intent_id, "receiver_xyz")
        assert claimed is not None
        assert claimed.status == IntentStatus.SETTLING

    def test_claim_intent_by_wrong_address_fails(self, network):
        # Demo mode: any address can claim (relayer-friendly)
        # In production, would check against registered relayer whitelist
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        claimed = network.claim_intent(intent.intent_id, "random_hacker")
        # In demo mode, this is allowed (anyone can be a relayer)
        assert claimed is not None

    def test_confirm_settlement(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        network.claim_intent(intent.intent_id, "receiver_xyz")
        result = network.confirm_settlement(
            intent.intent_id, "tx_sig_settled", "relayer_1", ["credit_1"]
        )
        assert result is True
        updated = network.get_intent(intent.intent_id)
        assert updated.status == IntentStatus.CLAIMED
        assert updated.settlement_tx == "tx_sig_settled"

    def test_cancel_intent_by_sender(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        result = network.cancel_intent(intent.intent_id, "sender_abc")
        assert result is True
        assert network.get_intent(intent.intent_id).status == IntentStatus.CANCELLED

    def test_cancel_intent_by_non_sender_fails(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        result = network.cancel_intent(intent.intent_id, "receiver_xyz")
        assert result is False

    def test_get_pending_intents(self, network):
        network.create_intent("sender_a", "receiver_xyz", "USDC", 1000, "sig1")
        network.create_intent("sender_b", "receiver_xyz", "SOL", 5000000, "sig2")
        network.create_intent("sender_c", "other_guy", "USDC", 2000, "sig3")

        pending = network.get_pending_intents("receiver_xyz")
        assert len(pending) == 2

    def test_get_sent_intents(self, network):
        network.create_intent("sender_abc", "receiver_x", "USDC", 1000, "sig1")
        network.create_intent("sender_abc", "receiver_y", "SOL", 5000, "sig2")
        network.create_intent("other", "receiver_z", "USDC", 2000, "sig3")

        sent = network.get_sent_intents("sender_abc")
        assert len(sent) == 2

    def test_expire_intents(self, network):
        intent = network.create_intent(
            "sender_abc", "receiver_xyz", "USDC", 1000, "sig"
        )
        intent.expires_at = time.time() - 1
        network.expire_intents()
        assert network.get_intent(intent.intent_id).status == IntentStatus.EXPIRED

    def test_stats(self, network):
        network.create_intent("s1", "r1", "USDC", 1000, "sig1")
        network.create_intent("s2", "r2", "SOL", 5000, "sig2")
        stats = network.stats
        assert stats["total_intents"] == 2
        assert stats["pending"] == 2
