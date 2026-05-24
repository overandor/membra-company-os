"""
MEMBRA L3 Protocol — End-to-End Demo

Demonstrates the full flow:
1. Identity linking (Venmo)
2. ZK compute → fee credits
3. Proof-of-Volatility signal
4. Gasless payment intent
5. Relayer settlement + GasVault reimbursement
6. Governance proposal
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from membra_l3.proof_book import proof_book, ProofType
from membra_l3.gas_vault import gas_vault
from membra_l3.volatility_oracle import volatility_oracle, VolatilitySignal
from membra_l3.intent_network import intent_network, IntentStatus
from membra_l3.token_router import token_router
from membra_l3.identity import identity_registry, IdentityProvider
from membra_l3.relayer import Relayer, RelayerConfig
from membra_l3.governance import governance, ProposalType, VoteChoice


def divider(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    divider("MEMBRA L3 Protocol — Full Demo")
    print("Python L3 brain → Solana settlement → Rust/Anchor enforcement\n")

    alice = "alice_wallet_abc123"
    bob = "bob_wallet_xyz789"
    relayer_addr = "relayer_service_001"

    # ═══════════════════════════════════════════════════════════
    # 1. SEED GASVAULT
    # ═══════════════════════════════════════════════════════════
    divider("1. Seed GasVault with SOL")
    gas_vault.deposit_sol(100_000_000_000, "initial_treasury")  # 100 SOL
    print(f"   GasVault reserves: {gas_vault.sol_reserves / 1e9:.2f} SOL")
    print(f"   Coverage ratio: {gas_vault.coverage_ratio}")
    print(f"   Healthy: {gas_vault.is_healthy()}")

    # ═══════════════════════════════════════════════════════════
    # 2. IDENTITY — Alice links Venmo
    # ═══════════════════════════════════════════════════════════
    divider("2. Identity — Alice links Venmo")
    link = identity_registry.link_identity(
        alice, IdentityProvider.VENMO, "@alice_venmo",
        proof_data={"oauth_token": "sim_oauth_token"}
    )
    identity_registry.verify_link(link.link_id)
    print(f"   Venmo linked: {identity_registry.has_venmo_linked(alice)}")
    print(f"   Username: {identity_registry.get_venmo_username(alice)}")

    # Also link GitHub for higher score
    gh_link = identity_registry.link_identity(
        alice, IdentityProvider.GITHUB, "alice_dev",
        proof_data={"gist_verified": True}
    )
    identity_registry.verify_link(gh_link.link_id)

    score = identity_registry.get_score(alice)
    print(f"   Social score: {score.score:.2f}/1.0")
    print(f"   Max transfer: ${score.max_transfer_usd:.2f}")
    print(f"   Max fee credits: ${score.max_fee_credits_usd:.2f}")
    print(f"   Risk flags: {score.risk_flags}")

    # ═══════════════════════════════════════════════════════════
    # 3. ZK COMPUTE → FEE CREDITS
    # ═══════════════════════════════════════════════════════════
    divider("3. ZK Compute → Fee Credits")
    zk_entry = proof_book.append(ProofType.ZK_COMPUTE, {
        "proof_type": "recursive_proof_compression",
        "work_units": 75,
        "nullifier": "nullifier_alice_001",
        "circuit": "plonk_verifier",
    })
    print(f"   ZK proof logged: {zk_entry.entry_hash[:16]}...")

    credit = gas_vault.issue_credit(alice, zk_entry.entry_hash, work_score=1.0)
    if credit:
        print(f"   Fee credit issued: {credit.amount_lamports / 1e9:.6f} SOL equivalent")
        print(f"   Credit ID: {credit.credit_id}")
        print(f"   Expires: {time.ctime(credit.expires_at)}")
    else:
        print("   ERROR: Failed to issue credit")
        return

    # ═══════════════════════════════════════════════════════════
    # 4. PROOF-OF-VOLATILITY
    # ═══════════════════════════════════════════════════════════
    divider("4. Proof-of-Volatility Signal")
    base_price = 1.00
    for i in range(20):
        price = base_price * (1 + i * 0.005)  # 10% rise
        volatility_oracle.feed_price(price, "jupiter", 5000.0)
        time.sleep(0.001)
    volatility_oracle.feed_gas(5000, 0, False)
    volatility_oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)

    report = volatility_oracle.assess(gas_vault.coverage_ratio)
    print(f"   Signal: {report.signal.value}")
    print(f"   Confidence: {report.confidence:.2%}")
    print(f"   MEMBRA TWAP: ${report.membra_twap:.4f}")
    print(f"   Price change: {report.price_change_pct:.2f}%")
    print(f"   Can unlock rebase: {volatility_oracle.can_unlock_rebase}")

    # ═══════════════════════════════════════════════════════════
    # 5. GASLESS PAYMENT INTENT
    # ═══════════════════════════════════════════════════════════
    divider("5. Gasless Payment Intent (Alice → Bob)")
    intent = intent_network.create_intent(
        sender_address=alice,
        receiver_address=bob,
        token_symbol="USDC",
        amount=50_000_000,  # 50 USDC
        sender_signature="alice_ed25519_sig_simulated",
    )
    if intent:
        print(f"   Intent ID: {intent.intent_id}")
        print(f"   From: {intent.sender_address[:12]}...")
        print(f"   To: {intent.receiver_address[:12]}...")
        print(f"   Amount: {intent.amount / 1e6:.2f} USDC")
        print(f"   Status: {intent.status.value}")
        print(f"   Claim window: 7 days")
        print(f"   Sender paid: 0 SOL (gasless!)")
    else:
        print("   ERROR: Failed to create intent")
        return

    # ═══════════════════════════════════════════════════════════
    # 6. RELAYER SETTLES + GASVAULT REIMBURSES
    # ═══════════════════════════════════════════════════════════
    divider("6. Relayer Settlement + GasVault Reimbursement")
    relayer = Relayer(RelayerConfig(relayer_address=relayer_addr))

    claimable = relayer.find_claimable_intents()
    print(f"   Claimable intents found: {len(claimable)}")

    result = relayer.relay_intent(intent)
    if result.success:
        print(f"   ✓ Settlement successful")
        print(f"   Tx signature: {result.tx_signature}")
        print(f"   Gas spent by relayer: {result.gas_spent_lamports} lamports")
        print(f"   Reimbursement: {result.reimbursement_lamports} lamports")
        print(f"   Relayer profit: {result.profit_lamports} lamports ({result.profit_lamports / 1e9:.6f} SOL)")
    else:
        print(f"   ✗ Settlement failed: {result.error}")
        return

    # Verify final state
    settled = intent_network.get_intent(intent.intent_id)
    print(f"\n   Final intent status: {settled.status.value}")
    print(f"   Settlement tx: {settled.settlement_tx}")

    # ═══════════════════════════════════════════════════════════
    # 7. GOVERNANCE PROPOSAL
    # ═══════════════════════════════════════════════════════════
    divider("7. Governance — Emission Proposal")
    governance.set_voting_power("governor_1", 100.0)
    governance.set_voting_power("governor_2", 50.0)
    governance.set_voting_power("governor_3", 75.0)

    vol_proofs = proof_book.get_entries(ProofType.VOLATILITY, limit=3)
    proof_hashes = [p.entry_hash for p in vol_proofs]

    proposal = governance.propose(
        ProposalType.EMISSION_PROPOSAL,
        "Capped MEMBRA emission — Epoch 1",
        "Proof-of-Volatility confirmed 10% price movement. "
        "Propose capped emission of 5000 MEMBRA to reward liquidity providers.",
        "governor_1",
        proof_hashes,
        {"emission_amount": 5000_000_000_000, "epoch": 1, "cap_enforced": True},
    )
    print(f"   Proposal: {proposal.proposal_id}")
    print(f"   Type: {proposal.proposal_type.value}")
    print(f"   Required proofs: {len(proposal.required_proofs)}")

    governance.start_voting(proposal.proposal_id)
    governance.vote(proposal.proposal_id, "governor_1", VoteChoice.FOR, "Volatility confirmed")
    governance.vote(proposal.proposal_id, "governor_2", VoteChoice.FOR, "Development active")
    governance.vote(proposal.proposal_id, "governor_3", VoteChoice.FOR, "Community supports")

    proposal.voting_ends_at = time.time() - 1
    governance.finalize(proposal.proposal_id)

    finalized = governance.get_proposal(proposal.proposal_id)
    tally = finalized.tally()
    print(f"\n   Vote tally: FOR={tally['for']:.0f} AGAINST={tally['against']:.0f}")
    print(f"   Status: {finalized.status.value}")

    if finalized.status.value == "approved":
        governance.execute(proposal.proposal_id, "governor_1")
        print(f"   ✓ Proposal executed")

    # ═══════════════════════════════════════════════════════════
    # 8. TOKEN ROUTING
    # ═══════════════════════════════════════════════════════════
    divider("8. Token Routing — Verified Adapters")
    supported = token_router.get_supported_tokens()
    print(f"   Supported tokens: {supported}")

    routes = token_router.get_routes_for_token("MEMBRA")
    print(f"   MEMBRA routes to: {routes}")

    quote = token_router.get_quote("SOL", "USDC", 1_000_000_000)  # 1 SOL
    if quote:
        print(f"\n   SOL → USDC quote:")
        print(f"   From: {quote.from_amount / 1e9:.4f} SOL")
        print(f"   To: {quote.to_amount / 1e6:.2f} USDC")
        print(f"   Fee: {quote.fee_bps} bps ({quote.fee_amount / 1e9:.6f} SOL)")
        print(f"   Adapter: {quote.adapter}")

    # ═══════════════════════════════════════════════════════════
    # 9. PROOFBOOK INTEGRITY
    # ═══════════════════════════════════════════════════════════
    divider("9. ProofBook Chain Integrity")
    print(f"   Total entries: {proof_book.entry_count}")
    print(f"   Chain valid: {proof_book.verify_chain()}")
    print(f"   Last hash: {proof_book.last_hash[:16]}...")

    # ═══════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════
    divider("FINAL SUMMARY")
    print(f"""
    ┌─────────────────────────────────────────────────────────┐
    │  MEMBRA L3 Protocol — Demo Complete                     │
    ├─────────────────────────────────────────────────────────┤
    │  Identity:    Alice linked Venmo + GitHub               │
    │  ZK Compute:  Proof logged → fee credits earned         │
    │  Volatility:  {report.signal.value:<30}          │
    │  Intent:      Alice → Bob 50 USDC (0 gas for sender)   │
    │  Settlement:  Relayer paid gas, GasVault reimbursed     │
    │  Governance:  Emission proposal {finalized.status.value:<20}          │
    │  ProofBook:   {proof_book.entry_count} entries, chain valid={proof_book.verify_chain()}              │
    ├─────────────────────────────────────────────────────────┤
    │  SENDER PAID: 0 SOL (gasless!)                          │
    │  RELAYER PROFIT: {result.profit_lamports} lamports                          │
    │  GASVAULT: {gas_vault.sol_reserves / 1e9:.2f} SOL reserves                        │
    └─────────────────────────────────────────────────────────┘
    """)

    print("  MEMBRA thesis: Python-powered Solana L3 with proof-gated,")
    print("  community-approved, gas-deferred tokenomics. No magic")
    print("  free money — every dangerous action is capped, verified,")
    print("  logged, and governed.")


if __name__ == "__main__":
    main()
