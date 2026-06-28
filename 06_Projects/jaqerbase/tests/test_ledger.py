import os

import pytest

from arrowcap.ledger import (
    AccountNotFound,
    InsufficientFunds,
    InvalidHoldState,
    Ledger,
)


@pytest.fixture
def ledger(tmp_path):
    db_path = os.path.join(tmp_path, "ledger.db")
    led = Ledger(db_path)
    yield led
    led.close()


def test_open_account_and_deposit(ledger):
    ledger.open_account("alice")
    assert ledger.balance("alice") == 0
    ledger.deposit("alice", 1000)
    assert ledger.balance("alice") == 1000


def test_balance_unknown_account_raises(ledger):
    with pytest.raises(AccountNotFound):
        ledger.balance("nobody")


def test_deposit_rejects_non_positive_amount(ledger):
    ledger.open_account("alice")
    with pytest.raises(ValueError):
        ledger.deposit("alice", 0)
    with pytest.raises(ValueError):
        ledger.deposit("alice", -5)


def test_transfer_moves_funds_between_accounts(ledger):
    ledger.open_account("alice")
    ledger.open_account("bob")
    ledger.deposit("alice", 5000)
    ledger.transfer("alice", "bob", 2000, ref_id="ref-1", memo="payment")
    assert ledger.balance("alice") == 3000
    assert ledger.balance("bob") == 2000


def test_transfer_insufficient_funds_rolls_back_atomically(ledger):
    ledger.open_account("alice")
    ledger.open_account("bob")
    ledger.deposit("alice", 100)
    with pytest.raises(InsufficientFunds):
        ledger.transfer("alice", "bob", 200)
    assert ledger.balance("alice") == 100
    assert ledger.balance("bob") == 0


def test_create_hold_reduces_spendable_balance(ledger):
    ledger.open_account("seller")
    ledger.deposit("seller", 10000)
    hold_id = ledger.create_hold("seller", 1000, "bond", "answer-1")
    assert ledger.balance("seller") == 9000
    hold = ledger.get_hold(hold_id)
    assert hold.status == "active"
    assert hold.amount_cents == 1000
    assert hold.kind == "bond"


def test_create_hold_rejects_bad_kind(ledger):
    ledger.open_account("seller")
    ledger.deposit("seller", 10000)
    with pytest.raises(ValueError):
        ledger.create_hold("seller", 1000, "not-a-kind", "answer-1")


def test_create_hold_insufficient_funds(ledger):
    ledger.open_account("seller")
    ledger.deposit("seller", 100)
    with pytest.raises(InsufficientFunds):
        ledger.create_hold("seller", 1000, "bond", "answer-1")


def test_release_hold_returns_funds_to_holder_by_default(ledger):
    ledger.open_account("seller")
    ledger.deposit("seller", 10000)
    hold_id = ledger.create_hold("seller", 1000, "bond", "answer-1")
    ledger.release_hold(hold_id)
    assert ledger.balance("seller") == 10000
    assert ledger.get_hold(hold_id).status == "released"


def test_release_hold_can_redirect_to_counterparty(ledger):
    ledger.open_account("buyer")
    ledger.open_account("seller")
    ledger.deposit("buyer", 10000)
    hold_id = ledger.create_hold("buyer", 5000, "escrow", "answer-1")
    ledger.release_hold(hold_id, destination_account_id="seller")
    assert ledger.balance("buyer") == 5000
    assert ledger.balance("seller") == 5000


def test_slash_hold_sends_funds_to_explicit_destination(ledger):
    ledger.open_account("seller")
    ledger.open_account("buyer")
    ledger.deposit("seller", 10000)
    hold_id = ledger.create_hold("seller", 1000, "bond", "answer-1")
    ledger.slash_hold(hold_id, "buyer")
    assert ledger.balance("seller") == 9000
    assert ledger.balance("buyer") == 1000
    assert ledger.get_hold(hold_id).status == "slashed"


def test_double_release_raises_invalid_hold_state(ledger):
    ledger.open_account("seller")
    ledger.deposit("seller", 10000)
    hold_id = ledger.create_hold("seller", 1000, "bond", "answer-1")
    ledger.release_hold(hold_id)
    with pytest.raises(InvalidHoldState):
        ledger.release_hold(hold_id)


def test_slash_after_release_raises_invalid_hold_state(ledger):
    ledger.open_account("seller")
    ledger.open_account("buyer")
    ledger.deposit("seller", 10000)
    hold_id = ledger.create_hold("seller", 1000, "bond", "answer-1")
    ledger.release_hold(hold_id)
    with pytest.raises(InvalidHoldState):
        ledger.slash_hold(hold_id, "buyer")


def test_get_hold_for_nonexistent_id_raises(ledger):
    with pytest.raises(InvalidHoldState):
        ledger.get_hold(99999)


def test_holds_for_ref_groups_bond_and_escrow(ledger):
    ledger.open_account("seller")
    ledger.open_account("buyer")
    ledger.deposit("seller", 10000)
    ledger.deposit("buyer", 10000)
    bond_id = ledger.create_hold("seller", 1000, "bond", "answer-1")
    escrow_id = ledger.create_hold("buyer", 5000, "escrow", "answer-1")
    holds = ledger.holds_for_ref("answer-1")
    assert {h.hold_id for h in holds} == {bond_id, escrow_id}


def test_history_is_append_only_and_ordered(ledger):
    ledger.open_account("alice")
    ledger.deposit("alice", 100)
    ledger.deposit("alice", 200)
    entries = ledger.history("alice")
    assert [e["delta_cents"] for e in entries] == [100, 200]
    assert [e["balance_after_cents"] for e in entries] == [100, 300]


def test_all_resolved_holds_excludes_active(ledger):
    ledger.open_account("seller")
    ledger.deposit("seller", 10000)
    h1 = ledger.create_hold("seller", 1000, "bond", "answer-1")
    ledger.create_hold("seller", 500, "bond", "answer-2")
    ledger.release_hold(h1)
    resolved = ledger.all_resolved_holds(kind="bond")
    assert len(resolved) == 1
    assert resolved[0].hold_id == h1
