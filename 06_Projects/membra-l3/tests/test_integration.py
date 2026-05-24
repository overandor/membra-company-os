"""
End-to-end integration tests for MEMBRA L3 Protocol.

Full flow: Identity → ZK Proof → Fee Credits → Intent → Relayer → Settlement → Reimbursement
"""
import pytest
import time
from membra_l3.proof_book import proof_book, ProofType
from membra_l3.gas_vault import gas_vault
from membra_l3.volatility_oracle import volatility_oracle
from membra_l3.intent_network import intent_network, IntentStatus
from membra_l3.token_router import token_router
from membra_l3.identity import identity_registry, IdentityProvider
from membra_l3.relayer import Relayer, RelayerConfig
from membra_l3.governance import governance, ProposalType, VoteChoice


class TestFullFlow:
    """
    Simulates the complete MEMBRA L3 flow:

    1. Alice links her Venmo identity
    2. Alice performs ZK compute, earns fee credits
    3. Market shows volatility → Proof-of-Volatility logged
    4. Alice creates a gasless payment intent to Bob
    5. Relayer picks up intent, settles on-chain
    6. Relayer gets reimbursed from GasVault
    7. Governance proposal for emission adjustment
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Seed the vault with SOL so coverage is healthy."""
        gas_vault.deposit_sol(100_000_000_000, "test_setup")  # 100 SOL

    def test_full_flow(self):
        alice = "alice_solana_wallet_addr"
        bob = "bob_solana_wallet_addr"
        relayer_addr = "relayer_service_addr"

        # ── Step 1: Alice links Venmo identity ──────────────
        link = identity_registry.link_identity(
            alice, IdentityProvider.VENMO, "@alice_venmo",
            proof_data={"oauth_token": "simulated"}
        )
        assert link is not None
        assert link.status.value == "pending"

        verified = identity_registry.verify_link(link.link_id)
        assert verified is True
        assert identity_registry.has_venmo_linked(alice) is True
        assert identity_registry.get_venmo_username(alice) == "@alice_venmo"

        # ── Step 2: Alice performs ZK compute, earns credits ─
        zk_entry = proof_book.append(ProofType.ZK_COMPUTE, {
            "proof_type": "recursive_compression",
            "work_units": 50,
            "nullifier": "nullifier_alice_001",
        })

        credit = gas_vault.issue_credit(alice, zk_entry.entry_hash, work_score=1.0)
        assert credit is not None
        assert credit.user_address == alice
        assert credit.amount_lamports > 0

        # ── Step 3: Market shows volatility ─────────────────
        base_price = 1.00
        for i in range(20):
            price = base_price * (1 + i * 0.005)
            volatility_oracle.feed_price(price, "jupiter", 5000.0)
            time.sleep(0.001)
        volatility_oracle.feed_gas(5000, 0, False)
        volatility_oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)

        report = volatility_oracle.assess(gas_vault.coverage_ratio)
        assert report is not None
        assert volatility_oracle.can_unlock_rebase is True

        # ── Step 4: Alice creates gasless payment intent ─────
        intent = intent_network.create_intent(
            sender_address=alice,
            receiver_address=bob,
            token_symbol="USDC",
            amount=50_000_000,  # 50 USDC
            sender_signature="alice_signed_intent_hash",
        )
        assert intent is not None
        assert intent.status == IntentStatus.PENDING
        assert intent.is_claimable() is True

        # ── Step 5: Relayer picks up and settles ────────────
        relayer = Relayer(RelayerConfig(relayer_address=relayer_addr))

        claimable = relayer.find_claimable_intents()
        assert len(claimable) >= 1

        result = relayer.relay_intent(intent)
        assert result.success is True
        assert result.tx_signature is not None
        assert result.profit_lamports > 0

        # Verify intent is settled
        settled = intent_network.get_intent(intent.intent_id)
        assert settled.status == IntentStatus.CLAIMED
        assert settled.settlement_tx == result.tx_signature

        # ── Step 6: Verify GasVault state ───────────────────
        stats = gas_vault.stats
        assert stats["total_reimbursements"] >= 1
        assert gas_vault.is_healthy() is True

        # ── Step 7: Governance proposal ─────────────────────
        governance.set_voting_power("governor_1", 100.0)
        governance.set_voting_power("governor_2", 50.0)
        governance.set_voting_power("governor_3", 75.0)

        vol_proofs = proof_book.get_entries(ProofType.VOLATILITY, limit=5)
        proof_hashes = [p.entry_hash for p in vol_proofs]

        proposal = governance.propose(
            ProposalType.EMISSION_PROPOSAL,
            "Capped emission based on Proof-of-Volatility",
            "Market volatility confirmed. Propose capped emission of 5000 MEMBRA.",
            "governor_1",
            proof_hashes,
            {"emission_amount": 5000_000_000_000, "epoch": 1},
        )
        assert proposal is not None

        governance.start_voting(proposal.proposal_id)
        governance.vote(proposal.proposal_id, "governor_1", VoteChoice.FOR, "Volatility confirmed")
        governance.vote(proposal.proposal_id, "governor_2", VoteChoice.FOR, "Development active")
        governance.vote(proposal.proposal_id, "governor_3", VoteChoice.AGAINST, "Prefer smaller emission")

        # Fast-forward past voting period
        proposal.voting_ends_at = time.time() - 1
        governance.finalize(proposal.proposal_id)

        finalized = governance.get_proposal(proposal.proposal_id)
        assert finalized.status.value in ("approved", "rejected")

        # ── Step 8: Verify ProofBook chain integrity ─────────
        assert proof_book.verify_chain() is True
        assert proof_book.entry_count >= 10  # many entries logged

        # ── Summary ──────────────────────────────────────────
        print(f"\n  ProofBook entries: {proof_book.entry_count}")
        print(f"  GasVault: {gas_vault.stats}")
        print(f"  Intent Network: {intent_network.stats}")
        print(f"  Relayer: {relayer.stats}")
        print(f"  Governance: {governance.stats}")
        print(f"  Identity: Alice linked={identity_registry.has_venmo_linked(alice)}")
        print(f"  Chain integrity: {proof_book.verify_chain()}")
