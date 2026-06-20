"""Tests for the Sealed-Grade Exchange. Run: python test_assay.py (or pytest)."""
import hashlib
import assay as A


def _mk():
    ex = A.SealedGradeExchange()
    for who, amt in [("alice", 100), ("mallory", 100), ("eve", 100), ("bob", 200)]:
        ex.fund(who, amt)
    g = A.PreimageGrader("chal-X", required_bits=12)
    return ex, g


def test_grader_is_content_addressed_and_deterministic():
    g1 = A.PreimageGrader("c", 10); g2 = A.PreimageGrader("c", 10)
    assert g1.source_hash == g2.source_hash
    assert A.PreimageGrader("c", 11).source_hash != g1.source_hash


def test_honest_seller_settles_and_buyer_can_reverify():
    ex, g = _mk()
    nonce, grade = A.mine(g)
    key = hashlib.sha256(b"k1").digest()
    ex.list_offer("o1", "alice", g, nonce, "r1", key, grade, bond=50, price=30)
    ex.buy("o1", "bob")
    assert ex.settle("o1", nonce, "r1", key) == "SETTLED"
    assert ex.bal["alice"] == 100 + 30          # paid; bond returned
    assert ex.bal["bob"] == 200 - 30
    # buyer independently re-grades the revealed answer
    import json
    pt = A.unseal(ex.offers["o1"].enc_answer, key)
    assert g.grade(json.loads(pt)).passed


def test_false_grade_claim_is_slashed_to_buyer():
    ex, g = _mk()
    nonce, true_g = A.mine(g)
    forged = A.Grade(true_g.kind, score=true_g.score + 8, required=12, passed=True,
                     detail={"challenge": "chal-X"})
    key = hashlib.sha256(b"k2").digest()
    ex.list_offer("o2", "mallory", g, nonce, "r2", key, forged, bond=50, price=30)
    ex.buy("o2", "bob")
    assert ex.settle("o2", nonce, "r2", key) == "SLASHED"
    assert ex.bal["mallory"] == 100 - 50        # bond forfeited
    assert ex.bal["bob"] == 200 + 50            # escrow refunded + bond
    assert ex.rep["mallory"]["slashed"] == 1


def test_bait_and_switch_binding_fails():
    ex, g = _mk()
    nonce, grade = A.mine(g)
    key = hashlib.sha256(b"k3").digest()
    ex.list_offer("o3", "eve", g, nonce, "r3", key, grade, bond=50, price=30)
    ex.buy("o3", "bob")
    assert ex.settle("o3", "different-answer", "r3", key) == "SLASHED"
    assert ex.bal["eve"] == 100 - 50


def test_money_is_conserved():
    ex, g = _mk()
    total_before = sum(ex.bal.values())
    nonce, grade = A.mine(g)
    for i, who in enumerate(["alice", "mallory"]):
        key = hashlib.sha256(f"k{i}".encode()).digest()
        claim = grade if who == "alice" else A.Grade(grade.kind, 99, 12, True, {"challenge": "chal-X"})
        ex.list_offer(f"x{i}", who, g, nonce, f"r{i}", key, claim, bond=40, price=20)
        ex.buy(f"x{i}", "bob")
        ex.settle(f"x{i}", nonce, f"r{i}", key)
    assert sum(ex.bal.values()) == total_before     # zero-sum across all parties


def test_ledger_hash_chain_verifies():
    ex, g = _mk()
    nonce, grade = A.mine(g)
    key = hashlib.sha256(b"k").digest()
    ex.list_offer("o", "alice", g, nonce, "r", key, grade, bond=50, price=30)
    ex.buy("o", "bob"); ex.settle("o", nonce, "r", key)
    assert ex.ledger.verify()
    ex.ledger.chain[0].payload["bond"] = 999        # tamper
    assert not ex.ledger.verify()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
