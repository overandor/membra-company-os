import os

import pytest

from chronoswarm.receipts import (
    Receipt,
    list_receipts,
    record_layout_breed,
    record_state_transition,
)
from chronoswarm.store import WorkflowStore


@pytest.fixture
def store(tmp_path):
    db_path = os.path.join(tmp_path, "chronoswarm.db")
    s = WorkflowStore(db_path)
    s.register_pane("%0", "sess", role="worker", now=100.0)
    yield s
    s.close()


def test_record_layout_breed_round_trips_genome_weights(store):
    receipt = record_layout_breed(
        store, "%0", genome_weights=(1.0, 2.5), new_width=80,
        fitness_before=1.0, fitness_after=2.0, now=150.0,
    )
    assert receipt.action == "layout_breed"
    assert receipt.detail["genome_weights"] == [1.0, 2.5]
    assert receipt.detail["new_width"] == 80
    assert receipt.fitness_before == 1.0
    assert receipt.fitness_after == 2.0

    [stored] = list_receipts(store, pane_id="%0")
    assert stored.id == receipt.id
    assert stored.detail == receipt.detail


def test_record_state_transition_round_trips(store):
    receipt = record_state_transition(store, "%0", "awake", "cooling", now=160.0)
    assert receipt.action == "state_transition"
    assert receipt.detail == {"from_state": "awake", "to_state": "cooling"}
    assert receipt.fitness_before is None
    assert receipt.fitness_after is None

    [stored] = list_receipts(store, pane_id="%0")
    assert stored.action == "state_transition"


def test_list_receipts_without_pane_id_returns_all(store):
    record_state_transition(store, "%0", "awake", "cooling", now=160.0)
    record_layout_breed(store, "%0", (1.0,), 80, 1.0, 2.0, now=161.0)
    assert len(list_receipts(store)) == 2


def test_receipt_to_dict_is_json_serializable_shape():
    receipt = Receipt(
        id=1, ts=100.0, pane_id="%0", action="layout_breed",
        detail={"x": 1}, fitness_before=1.0, fitness_after=2.0,
    )
    d = receipt.to_dict()
    assert d == {
        "id": 1, "ts": 100.0, "pane_id": "%0", "action": "layout_breed",
        "detail": {"x": 1}, "fitness_before": 1.0, "fitness_after": 2.0,
    }
