import os

import pytest

from arrowcap.antonymizer import antonymify
from arrowcap.claims import ClaimStore
from arrowcap.escrow import EscrowEngine
from arrowcap.ledger import Ledger
from arrowcap.optimizer import (
    DEFAULT_ACTIONS,
    DEFAULT_GENOME,
    BondGenome,
    BondOptimizer,
    BondQLearner,
    HistoryRecord,
    collect_history,
    evolve_bond_genome,
    fitness,
)

HIDDEN_TEST = b'''
import submitted_answer

def test_add():
    assert submitted_answer.add(2, 3) == 5
'''

SAFE_ANSWER = b"def add(a, b):\n    return a + b\n"
RISKY_BROKEN_ANSWER = b"def add(a, b):\n    eval('1 + 1')\n    return None\n"


@pytest.fixture
def store(tmp_path):
    db_path = os.path.join(tmp_path, "ledger.db")
    ledger = Ledger(db_path)
    cs = ClaimStore(db_path)
    eng = EscrowEngine(ledger, cs)
    ledger.open_account("buyer")
    ledger.open_account("seller")
    ledger.deposit("buyer", 1_000_000)
    ledger.deposit("seller", 1_000_000)
    yield cs, eng
    ledger.close()
    cs.close()


@pytest.fixture
def hidden_test_file(tmp_path):
    path = tmp_path / "test_hidden.py"
    path.write_bytes(HIDDEN_TEST)
    return str(path)


def _settle_one(eng, hidden_test_file, *, answer_content, reward_cents=5000, bond_fraction=0.2):
    claim = eng.post_claim("buyer", "add task", "implement add", reward_cents, hidden_test_file)
    profile = antonymify(answer_content, "source")
    bond_cents = round(reward_cents * bond_fraction)
    answer = eng.submit_preview(claim.claim_id, "seller", profile, bond_cents)
    eng.post_bond(answer.answer_id)
    eng.fund_escrow(answer.answer_id)
    eng.reveal_answer(answer.answer_id, answer_content)
    eng.run_oracle(answer.answer_id)
    return eng.settle(answer.answer_id)


# ---------------------------------------------------------------------------
# Bootstrap / cold-start behavior (no fabricated history; documented default)
# ---------------------------------------------------------------------------


def test_evolve_bond_genome_bootstraps_to_default_with_no_history():
    result = evolve_bond_genome([])
    assert result.best_genome == DEFAULT_GENOME
    assert result.best_fitness == 0.0
    assert result.generations_run == 0
    assert result.history_size == 0


def test_q_learner_cold_start_recommends_middle_action():
    learner = BondQLearner()
    mid = DEFAULT_ACTIONS[len(DEFAULT_ACTIONS) // 2]
    assert learner.recommend_bond_fraction(0.0) == mid
    assert learner.recommend_bond_fraction(0.9) == mid


def test_bond_optimizer_bootstraps_with_empty_store(store):
    cs, _eng = store
    optimizer = BondOptimizer(cs)
    ga_result = optimizer.retrain()
    assert ga_result.history_size == 0
    assert ga_result.best_genome == DEFAULT_GENOME
    rec = optimizer.recommend(5000, 0.5)
    assert rec.history_size == 0
    assert 0.0 < rec.bond_fraction <= 1.0


# ---------------------------------------------------------------------------
# Genome mechanics
# ---------------------------------------------------------------------------


def test_bond_genome_fraction_is_clamped():
    genome = BondGenome(base_rate=0.9, risk_weight=0.9, min_fraction=0.02, max_fraction=0.6)
    assert genome.bond_fraction(1.0) == 0.6
    low = BondGenome(base_rate=0.0, risk_weight=0.0)
    assert low.bond_fraction(0.0) == low.min_fraction


def test_fitness_rewards_high_bond_on_failures_and_penalizes_on_passes():
    genome = BondGenome(base_rate=0.5, risk_weight=0.0)
    passing = [HistoryRecord(5000, 0.5, 0.5, passed=True)]
    failing = [HistoryRecord(5000, 0.5, 0.5, passed=False)]
    assert fitness(genome, passing) < 0
    assert fitness(genome, failing) > 0


def test_fitness_empty_records_is_zero():
    assert fitness(DEFAULT_GENOME, []) == 0.0


# ---------------------------------------------------------------------------
# Real, pipeline-derived settlement history (no mocked/fabricated outcomes)
# ---------------------------------------------------------------------------


def test_collect_history_reflects_real_settlements_only(store, hidden_test_file):
    cs, eng = store
    outcome = _settle_one(eng, hidden_test_file, answer_content=SAFE_ANSWER)
    assert outcome.passed is True
    records = collect_history(cs)
    assert len(records) == 1
    assert records[0].passed is True
    assert records[0].risk_score == 0.0
    assert records[0].bond_fraction_used == pytest.approx(0.2, abs=1e-6)


def test_optimizer_prices_high_risk_failures_above_low_risk_passes(store, hidden_test_file):
    cs, eng = store
    for _ in range(3):
        _settle_one(eng, hidden_test_file, answer_content=SAFE_ANSWER)
    for _ in range(3):
        _settle_one(eng, hidden_test_file, answer_content=RISKY_BROKEN_ANSWER)

    records = collect_history(cs)
    assert len(records) == 6
    assert sum(r.passed for r in records) == 3
    assert sum(r.risk_score > 0 for r in records) == 3

    optimizer = BondOptimizer(cs, ga_kwargs={"seed": 42})
    ga_result = optimizer.retrain()
    assert ga_result.history_size == 6

    low_risk = optimizer.recommend(5000, 0.0)
    high_risk = optimizer.recommend(5000, 1.0)
    assert high_risk.bond_fraction > low_risk.bond_fraction
    assert high_risk.bond_cents > low_risk.bond_cents
