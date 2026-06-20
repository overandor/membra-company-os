"""Integration tests: collectors + appraiser bridge + ProofBook + portfolio.
Run: python test_integration.py  (or pytest)."""
import os, tempfile
import collect as COL
import appraiser_bridge as AB
import portfolio as PF
from proofbook import ProofBook

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

SAMPLE_REPOS = [
    {"name": "membra-company-os", "language": "Python", "size": 418321, "created_at": "2026-05-16"},
    {"name": "tokenize-camera", "language": "TypeScript", "size": 110353, "created_at": "2026-05-17"},
    {"name": "arb-execution-engine", "language": "Python", "size": 60, "created_at": "2026-04-20"},
    {"name": "zen-garden-art", "language": None, "size": 1, "created_at": "2026-05-10"},
]


def test_proofbook_chain_and_tamper():
    with tempfile.TemporaryDirectory() as d:
        pb = ProofBook(os.path.join(d, "pb.jsonl"))
        pb.append("x", {"a": 1}); pb.append("y", {"b": 2})
        assert pb.verify_chain()
        pb.entries[0]["payload"]["a"] = 999       # tamper in memory
        assert not pb.verify_chain()


def test_local_git_collector_reads_real_repo():
    m = COL.local_git_metrics(REPO_ROOT, login="overandor", followers=4, public_repos=176)
    assert m["code"]["portfolio_sloc"] > 1000      # real codebase
    assert m["code"]["implemented_defs"] > 100
    assert m["code"]["deployable_units"] >= 1
    assert m["subject"]["account_created"] <= "2026-06-20"


def test_appraiser_bridge_sums_ledger():
    a = AB.load_appraisal_total(os.path.join(HERE, "sample_appraisal_ledger.json"))
    assert a["n_files"] == 5
    assert a["appraised_total_usd"] == 7545          # 720+360+945+5400+120
    method = AB.as_valuation_method(os.path.join(HERE, "sample_appraisal_ledger.json"))
    assert method["net_usd"] == round(7545 * 0.5)


def test_portfolio_rollup_and_proofbook():
    with tempfile.TemporaryDirectory() as d:
        pb = ProofBook(os.path.join(d, "pb.jsonl"))
        rep = PF.underwrite_portfolio(SAMPLE_REPOS, pb)
        assert rep["n_repos"] == 4
        assert rep["portfolio_borrowing_base_usd"] > 0
        assert rep["proofbook_verified"] is True
        assert len(pb.entries) == 4                  # one hashed decision per repo
        # the big flagship should out-rank the 1KB art repo
        names = [r["repo"] for r in rep["top_contributors"]]
        assert names[0] == "membra-company-os"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
