import os

import pytest

from chronoswarm.store import WorkflowStore


@pytest.fixture
def store(tmp_path):
    db_path = os.path.join(tmp_path, "chronoswarm.db")
    s = WorkflowStore(db_path)
    yield s
    s.close()


def test_register_pane_persists_with_awake_state(store):
    record = store.register_pane("%0", "sess", role="worker", now=100.0)
    assert record.pane_id == "%0"
    assert record.state == "awake"
    assert record.role == "worker"


def test_get_pane_returns_none_for_unknown_pane(store):
    assert store.get_pane("%nope") is None


def test_update_state_rejects_invalid_state(store):
    store.register_pane("%0", "sess", role="worker", now=100.0)
    with pytest.raises(ValueError):
        store.update_state("%0", "not-a-real-state", now=101.0)


def test_update_state_persists_new_state(store):
    store.register_pane("%0", "sess", role="worker", now=100.0)
    store.update_state("%0", "cooling", now=101.0)
    assert store.get_pane("%0").state == "cooling"


def test_touch_activity_updates_timestamp(store):
    store.register_pane("%0", "sess", role="worker", now=100.0)
    store.touch_activity("%0", now=200.0)
    assert store.get_pane("%0").last_activity_ts == 200.0


def test_list_panes_filters_by_session(store):
    store.register_pane("%0", "sess-a", role="worker", now=100.0)
    store.register_pane("%1", "sess-b", role="worker", now=100.0)
    assert [p.pane_id for p in store.list_panes(session_name="sess-a")] == ["%0"]
    assert len(store.list_panes()) == 2


def test_remove_pane_cascades_receipts(store):
    store.register_pane("%0", "sess", role="worker", now=100.0)
    store.add_receipt("%0", "test_action", "{}", now=100.0)
    store.remove_pane("%0")
    assert store.get_pane("%0") is None
    assert store.list_receipts(pane_id="%0") == []


def test_add_receipt_and_list_receipts_round_trip(store):
    store.register_pane("%0", "sess", role="worker", now=100.0)
    rid = store.add_receipt(
        "%0", "layout_breed", '{"a": 1}', now=101.0, fitness_before=1.0, fitness_after=2.0
    )
    rows = store.list_receipts(pane_id="%0")
    assert len(rows) == 1
    assert rows[0][0] == rid
    assert rows[0][3] == "layout_breed"


def test_store_state_survives_reopen(tmp_path):
    db_path = os.path.join(tmp_path, "chronoswarm.db")
    s1 = WorkflowStore(db_path)
    s1.register_pane("%0", "sess", role="worker", now=100.0)
    s1.close()

    s2 = WorkflowStore(db_path)
    record = s2.get_pane("%0")
    s2.close()
    assert record is not None
    assert record.role == "worker"
