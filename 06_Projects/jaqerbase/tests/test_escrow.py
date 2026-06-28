import os

import pytest

from arrowcap.antonymizer import antonymify
from arrowcap.claims import ClaimStore
from arrowcap.escrow import EscrowEngine, ProtocolViolation
from arrowcap.ledger import Ledger

HIDDEN_TEST = b'''
import submitted_answer

def test_add():
    assert submitted_answer.add(2, 3) == 5
'''

GOOD_ANSWER = b"def add(a, b):\n    return a + b\n"
BROKEN_ANSWER = b"def add(a, b):\n    return a - b\n"


@pytest.fixture
def engine(tmp_path):
    db_path = os.path.join(tmp_path, "ledger.db")
    ledger = Ledger(db_path)
    store = ClaimStore(db_path)
    eng = EscrowEngine(ledger, store, fee_bps=250)
    yield eng, ledger, store
    ledger.close()
    store.close()


@pytest.fixture
def hidden_test_file(tmp_path):
    path = tmp_path / "test_hidden.py"
    path.write_bytes(HIDDEN_TEST)
    return str(path)


def _fund(ledger, account, cents):
    ledger.open_account(account)
    ledger.deposit(account, cents)


def test_full_passing_lifecycle_reconciles_balances(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)

    claim = eng.post_claim("alice", "add task", "implement add", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)

    eng.post_bond(answer.answer_id)
    eng.fund_escrow(answer.answer_id)
    ok, mismatches = eng.reveal_answer(answer.answer_id, GOOD_ANSWER)
    assert ok and mismatches == []

    report = eng.run_oracle(answer.answer_id)
    assert report.passed is True

    outcome = eng.settle(answer.answer_id)
    assert outcome.passed is True
    assert outcome.fee_cents == 125  # 2.5% of 5000
    assert outcome.payout_cents == 4875
    assert outcome.bond_returned is True

    assert ledger.balance("alice") == 100000 - 5000
    assert ledger.balance("bob") == 100000 + 4875  # payout; bond hold released back, net zero
    assert ledger.balance("treasury") == 125


def test_failing_oracle_slashes_bond_and_refunds_buyer(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)

    claim = eng.post_claim("alice", "add task", "implement add", 5000, hidden_test_file)
    profile = antonymify(BROKEN_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)
    eng.post_bond(answer.answer_id)
    eng.fund_escrow(answer.answer_id)
    eng.reveal_answer(answer.answer_id, BROKEN_ANSWER)
    report = eng.run_oracle(answer.answer_id)
    assert report.passed is False

    outcome = eng.settle(answer.answer_id)
    assert outcome.passed is False
    assert outcome.payout_cents == 0
    assert outcome.bond_returned is False

    assert ledger.balance("alice") == 100000 + 1000  # escrow refunded (net zero) + slashed bond
    assert ledger.balance("bob") == 100000 - 1000  # bond gone, no payout
    assert ledger.balance("treasury") == 0


def test_binding_violation_slashes_bond_without_running_oracle(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)

    claim = eng.post_claim("alice", "add task", "implement add", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)
    eng.post_bond(answer.answer_id)
    eng.fund_escrow(answer.answer_id)

    tampered = b"import os\n" + GOOD_ANSWER
    ok, mismatches = eng.reveal_answer(answer.answer_id, tampered)
    assert ok is False
    assert mismatches

    outcome = eng.settle(answer.answer_id, binding_violation=True)
    assert outcome.binding_violation is True
    assert outcome.passed is False
    assert ledger.balance("bob") == 100000 - 1000
    assert ledger.balance("alice") == 100000 + 1000  # escrow refunded (net zero) + slashed bond


def test_submit_preview_rejected_when_claim_not_open(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)
    claim = eng.post_claim("alice", "t", "d", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)
    eng.post_bond(answer.answer_id)
    eng.fund_escrow(answer.answer_id)  # claim becomes 'escrowed'

    with pytest.raises(ProtocolViolation):
        eng.submit_preview(claim.claim_id, "carol", profile, 1000)


def test_fund_escrow_before_bond_is_protocol_violation(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)
    claim = eng.post_claim("alice", "t", "d", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)

    with pytest.raises(ProtocolViolation, match="no oracle without a bond"):
        eng.fund_escrow(answer.answer_id)


def test_reveal_before_funded_is_protocol_violation(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)
    claim = eng.post_claim("alice", "t", "d", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)
    eng.post_bond(answer.answer_id)

    with pytest.raises(ProtocolViolation, match="no full disclosure before payment"):
        eng.reveal_answer(answer.answer_id, GOOD_ANSWER)


def test_run_oracle_before_revealed_is_protocol_violation(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)
    claim = eng.post_claim("alice", "t", "d", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)
    eng.post_bond(answer.answer_id)
    eng.fund_escrow(answer.answer_id)

    with pytest.raises(ProtocolViolation):
        eng.run_oracle(answer.answer_id)


def test_settle_before_oracle_is_protocol_violation(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)
    claim = eng.post_claim("alice", "t", "d", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)
    eng.post_bond(answer.answer_id)
    eng.fund_escrow(answer.answer_id)
    eng.reveal_answer(answer.answer_id, GOOD_ANSWER)

    with pytest.raises(ProtocolViolation, match="no settlement without an oracle"):
        eng.settle(answer.answer_id)


def test_post_bond_requires_preview_status(engine, hidden_test_file):
    eng, ledger, store = engine
    _fund(ledger, "alice", 100000)
    _fund(ledger, "bob", 100000)
    claim = eng.post_claim("alice", "t", "d", 5000, hidden_test_file)
    profile = antonymify(GOOD_ANSWER, "source")
    answer = eng.submit_preview(claim.claim_id, "bob", profile, 1000)
    eng.post_bond(answer.answer_id)

    with pytest.raises(ProtocolViolation):
        eng.post_bond(answer.answer_id)
