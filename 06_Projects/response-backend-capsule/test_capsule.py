"""Tests for the Response Backend Capsule runtime. python3 test_capsule.py (or pytest)."""
import tempfile
import capsule as C
import demo as D


def _rt():
    return C.Runtime(tempfile.mkdtemp())


def test_classifier_routes():
    assert C.classify("What is a tesseract?") == C.EXPLANATION
    assert C.classify("what time is it") == C.EXPLANATION
    assert C.classify("convert Beige Book adjectives into policy pressure") == C.ENDPOINT
    assert C.classify("build a shadow receivable ledger system") == C.WORKFLOW


def test_explanation_emits_no_backend():
    rt = _rt()
    cap = C.Capsule("A 4-D cube.", C.Manifest("q", "explain", C.EXPLANATION))
    r = rt.process("what is a tesseract", cap)
    assert r["served"] is False


def test_endpoint_compiles_serves_tests_and_receipts():
    rt = _rt()
    r = rt.process("convert beige book adjectives into policy pressure", D.make_beige_book_capsule())
    assert r["tests_pass"] is True and r["served"] is True and r["blocked"] is False
    assert r["endpoint"] == "local://beige_book_pressure"
    out = rt.call("beige_book_pressure", {"adjectives": ["strong", "robust"]})
    assert out["pressure"] > 0 and out["stance"] == "hawkish"
    assert rt.tech.verify()                       # technical chain intact


def test_safety_blocks_malicious_capsule():
    rt = _rt()
    r = rt.process("build evil", D.make_malicious_capsule())
    assert r["blocked"] is True and r["served"] is False
    assert any("rm -rf" in f or "os.system" in f for f in r["findings"])
    try:
        rt.call("evil", {}); assert False, "blocked capsule must not be callable"
    except KeyError:
        pass


def test_no_phantom_revenue_and_separate_ledgers():
    rt = _rt()
    rt.process("convert ... into policy pressure", D.make_beige_book_capsule())
    rt.econ.log_usage("beige_book_pressure", "t", seconds=0.2, human_baseline_seconds=600)
    s = rt.econ.summary()
    assert s["revenue"] == 0.0                     # no money logged -> no revenue
    assert s["total_time_saved_seconds"] > 0
    # revenue only appears when money actually moves
    rt.econ.log_usage("beige_book_pressure", "paid", seconds=0.2, money_moved=5.0)
    assert rt.econ.summary()["revenue"] == 5.0
    # technical ledger never carries revenue
    assert all("money_moved" not in e["payload"] for e in rt.tech.chain)


def test_economic_proof_requires_all_four_parts():
    rt = _rt()
    rt.process("convert ... pressure", D.make_beige_book_capsule())
    before = rt.economic_proof("beige_book_pressure")
    assert before["executable_artifact"] is True and before["usage_event"] is False
    assert before["activity_proven"] is False      # served but unused
    rt.econ.log_usage("beige_book_pressure", "t", seconds=0.2, human_baseline_seconds=600)
    after = rt.economic_proof("beige_book_pressure")
    assert after["activity_proven"] is True        # artifact + usage + optimization + receipt
    assert after["revenue"] == 0.0                 # still no revenue guaranteed


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
