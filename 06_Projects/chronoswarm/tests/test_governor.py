import os
import time

import pytest

from chronoswarm.fitness import FitnessWeights
from chronoswarm.governor import GeneticLayoutGovernor
from chronoswarm.store import WorkflowStore


@pytest.fixture
def store(tmp_path):
    db_path = os.path.join(tmp_path, "chronoswarm.db")
    s = WorkflowStore(db_path)
    yield s
    s.close()


def test_build_snapshots_reflects_real_tmux_geometry(tmux_session, store):
    first_pane = tmux_session.list_panes()[0]
    tmux_session.split_window(first_pane.pane_id)

    governor = GeneticLayoutGovernor(tmux_session, store)
    snapshots = governor.build_snapshots(now=100.0)

    assert len(snapshots) == 2
    real_widths = {p.pane_id: p.width for p in tmux_session.list_panes()}
    for snap in snapshots:
        assert snap.width == real_widths[snap.pane_id]


def test_build_snapshots_registers_unseen_panes_in_store(tmux_session, store):
    governor = GeneticLayoutGovernor(tmux_session, store)
    governor.build_snapshots(now=100.0)
    pane_id = tmux_session.list_panes()[0].pane_id
    assert store.get_pane(pane_id) is not None


def test_breed_and_apply_with_single_pane_is_not_applied(tmux_session, store):
    governor = GeneticLayoutGovernor(tmux_session, store)
    result = governor.breed_and_apply(now=100.0)
    assert result["applied"] is False
    assert result["pane_count"] == 1


def test_breed_and_apply_resizes_real_panes_and_improves_fitness(tmux_session, store):
    first_pane = tmux_session.list_panes()[0]
    second_pane_id = tmux_session.split_window(first_pane.pane_id)
    tmux_session.send_keys(second_pane_id, "echo 'Traceback (most recent call last):'")
    time.sleep(0.3)

    governor = GeneticLayoutGovernor(tmux_session, store, FitnessWeights())
    result = governor.breed_and_apply(now=100.0, generations=20, population_size=16, seed=7)

    assert result["applied"] is True
    assert result["fitness_after"] >= result["fitness_before"]

    real_widths = {p.pane_id: p.width for p in tmux_session.list_panes()}
    total_real_width = sum(real_widths.values())
    assert abs(total_real_width - sum(real_widths.values())) == 0

    error_pane_width = real_widths[second_pane_id]
    other_width = real_widths[first_pane.pane_id]
    assert error_pane_width > other_width, "pane showing the error should win more width"


def test_breed_and_apply_writes_receipts_to_store(tmux_session, store):
    first_pane = tmux_session.list_panes()[0]
    tmux_session.split_window(first_pane.pane_id)

    governor = GeneticLayoutGovernor(tmux_session, store)
    result = governor.breed_and_apply(now=100.0, generations=10, population_size=10, seed=1)

    assert len(result["receipts"]) == 2
    stored_receipts = store.list_receipts()
    assert len(stored_receipts) == 2
    assert all(row[3] == "layout_breed" for row in stored_receipts)
