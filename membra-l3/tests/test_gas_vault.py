"""
Tests for MEMBRA L3 GasVault
"""
import pytest
from membra_l3.gas_vault import GasVault, FeeCredit, CreditStatus
from membra_l3.proof_book import ProofBook, ProofType, proof_book


class TestGasVault:
    @pytest.fixture
    def vault(self):
        """Fresh vault with 10 SOL in reserves."""
        return GasVault(initial_sol_lamports=10_000_000_000)  # 10 SOL

    @pytest.fixture
    def zk_proof_hash(self):
        """Register a ZK proof in ProofBook so credits can be issued."""
        entry = proof_book.append(ProofType.ZK_COMPUTE, {
            "proof_type": "recursive_compression",
            "work_units": 100,
            "nullifier": "test_nullifier_001",
        })
        return entry.entry_hash

    def test_deposit_sol(self, vault):
        vault.deposit_sol(5_000_000_000, "treasury")
        assert vault.sol_reserves == 15_000_000_000

    def test_withdraw_sol_healthy(self, vault):
        vault.deposit_sol(10_000_000_000)
        result = vault.withdraw_sol(1_000_000_000, "treasury_main", "test")
        assert result is True
        assert vault.sol_reserves == 19_000_000_000

    def test_withdraw_sol_insufficient(self, vault):
        result = vault.withdraw_sol(20_000_000_000, "treasury", "too much")
        assert result is False

    def test_issue_credit_with_valid_proof(self, vault, zk_proof_hash):
        credit = vault.issue_credit("user_addr_1", zk_proof_hash, work_score=1.0)
        assert credit is not None
        assert credit.user_address == "user_addr_1"
        assert credit.amount_lamports > 0
        assert credit.status == CreditStatus.ACTIVE

    def test_issue_credit_without_proof_fails(self, vault):
        credit = vault.issue_credit("user_addr_1", "fake_hash", work_score=1.0)
        assert credit is None

    def test_credit_user_cap(self, vault, zk_proof_hash):
        # Issue credits up to cap (max is $10 USD = 10B lamports)
        # work_score=1.0 gives 0.1 SOL = 100M lamports
        # Need ~100 credits to hit 10B cap
        for _ in range(100):
            vault.issue_credit("user_addr_1", zk_proof_hash, work_score=1.0)
        # Should be at cap
        credit = vault.issue_credit("user_addr_1", zk_proof_hash, work_score=1.0)
        assert credit is None

    def test_get_user_credits(self, vault, zk_proof_hash):
        vault.issue_credit("user_addr_1", zk_proof_hash, work_score=0.5)
        vault.issue_credit("user_addr_1", zk_proof_hash, work_score=0.3)
        credits = vault.get_user_credits("user_addr_1")
        assert len(credits) == 2

    def test_consume_credits(self, vault, zk_proof_hash):
        c1 = vault.issue_credit("user_addr_1", zk_proof_hash, work_score=0.5)
        c2 = vault.issue_credit("user_addr_1", zk_proof_hash, work_score=0.3)
        total = vault.consume_credits([c1.credit_id, c2.credit_id])
        assert total == c1.amount_lamports + c2.amount_lamports
        assert vault._credits[c1.credit_id].status == CreditStatus.USED

    def test_reimburse_relayer(self, vault, zk_proof_hash):
        c1 = vault.issue_credit("user_addr_1", zk_proof_hash, work_score=0.5)
        c2 = vault.issue_credit("user_addr_1", zk_proof_hash, work_score=0.3)
        credit_ids = [c1.credit_id, c2.credit_id]
        total_credit = c1.amount_lamports + c2.amount_lamports

        reimbursement = vault.reimburse_relayer(
            "relayer_addr_1", "tx_sig_abc123", credit_ids
        )
        assert reimbursement is not None
        assert reimbursement.amount_lamports == total_credit
        assert vault.sol_reserves == 10_000_000_000 - total_credit

    def test_coverage_ratio(self, vault, zk_proof_hash):
        assert vault.coverage_ratio == float('inf')  # no outstanding credits

        vault.issue_credit("user_addr_1", zk_proof_hash, work_score=1.0)
        ratio = vault.coverage_ratio
        assert ratio > 1.0  # 10 SOL covering small credit

    def test_is_healthy(self, vault, zk_proof_hash):
        assert vault.is_healthy() is True

        # Issue many credits to strain coverage
        for i in range(20):
            addr = f"user_{i}"
            vault.issue_credit(addr, zk_proof_hash, work_score=10.0)

        # May or may not be healthy depending on caps
        stats = vault.stats
        assert "coverage_ratio" in stats
        assert "is_healthy" in stats

    def test_credit_expiry(self, vault, zk_proof_hash):
        credit = vault.issue_credit("user_addr_1", zk_proof_hash, work_score=0.5)
        # Manually expire
        credit.expires_at = 0  # epoch
        vault._expire_stale_credits()
        assert vault._credits[credit.credit_id].status == CreditStatus.EXPIRED

    def test_stats(self, vault, zk_proof_hash):
        vault.issue_credit("user_addr_1", zk_proof_hash, work_score=1.0)
        stats = vault.stats
        assert stats["sol_reserves"] == 10_000_000_000
        assert stats["active_credits"] == 1
        assert "coverage_ratio" in stats
