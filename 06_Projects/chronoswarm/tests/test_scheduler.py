import os
import time

import pytest

from chronoswarm.scheduler import ChronoScheduler, SchedulerThresholds, next_state
from chronoswarm.store import WorkflowStore

THRESHOLDS = SchedulerThresholds(
    cool_after_seconds=100.0,
    sleep_after_seconds=200.0,
    archive_after_seconds=300.0,
    working_after_seconds=5.0,
)


@pytest.fixture
def store(tmp_path):
    db_path = os.path.join(tmp_path, "chronoswarm.db")
    s = WorkflowStore(db_path)
    yield s
    s.close()


def test_next_state_error_always_wins():
    assert next_state("sleeping", idle_seconds=1000.0, has_error=True, thresholds=THRESHOLDS) == "working"


def test_next_state_fresh_activity_is_working():
    assert next_state("awake", idle_seconds=0.0, has_error=False, thresholds=THRESHOLDS) == "working"


def test_next_state_settles_to_awake_between_working_and_cool():
    assert next_state("awake", idle_seconds=50.0, has_error=False, thresholds=THRESHOLDS) == "awake"


def test_next_state_cools_after_threshold():
    assert next_state("awake", idle_seconds=150.0, has_error=False, thresholds=THRESHOLDS) == "cooling"


def test_next_state_sleeps_after_threshold():
    assert next_state("cooling", idle_seconds=250.0, has_error=False, thresholds=THRESHOLDS) == "sleeping"


def test_next_state_archives_after_threshold():
    assert next_state("sleeping", idle_seconds=400.0, has_error=False, thresholds=THRESHOLDS) == "archived"


def test_next_state_warms_when_sleeping_pane_gets_recent_activity():
    assert next_state("sleeping", idle_seconds=10.0, has_error=False, thresholds=THRESHOLDS) == "warming"


def test_next_state_warms_when_archived_pane_gets_recent_activity():
    assert next_state("archived", idle_seconds=10.0, has_error=False, thresholds=THRESHOLDS) == "warming"


def test_tick_transitions_idle_pane_through_ladder(tmux_session, store):
    pane_id = tmux_session.list_panes()[0].pane_id
    store.register_pane(pane_id, tmux_session.session_name, role="worker", now=0.0)
    scheduler = ChronoScheduler(store, THRESHOLDS)

    transitions = scheduler.tick(tmux_session, now=2.0)
    assert store.get_pane(pane_id).state == "working"
    assert transitions[0]["detail"]["to_state"] == "working"

    transitions = scheduler.tick(tmux_session, now=150.0)
    assert store.get_pane(pane_id).state == "cooling"

    transitions = scheduler.tick(tmux_session, now=250.0)
    assert store.get_pane(pane_id).state == "sleeping"

    transitions = scheduler.tick(tmux_session, now=400.0)
    assert store.get_pane(pane_id).state == "archived"


def test_tick_marks_externally_killed_pane_archived(tmux_session, store):
    pane = tmux_session.list_panes()[0]
    other_pane_id = tmux_session.split_window(pane.pane_id)
    store.register_pane(pane.pane_id, tmux_session.session_name, role="worker", now=0.0)
    store.register_pane(other_pane_id, tmux_session.session_name, role="worker", now=0.0)

    tmux_session.kill_pane(other_pane_id)

    scheduler = ChronoScheduler(store, THRESHOLDS)
    transitions = scheduler.tick(tmux_session, now=1.0)

    assert store.get_pane(other_pane_id).state == "archived"
    archived_transition = [t for t in transitions if t["pane_id"] == other_pane_id][0]
    assert archived_transition["detail"]["to_state"] == "archived"


def test_tick_error_marker_forces_working_state(tmux_session, store):
    pane_id = tmux_session.list_panes()[0].pane_id
    store.register_pane(pane_id, tmux_session.session_name, role="worker", now=0.0)
    store.update_state(pane_id, "sleeping", now=0.0)

    tmux_session.send_keys(pane_id, "echo 'Traceback (most recent call last):'")
    time.sleep(0.3)

    scheduler = ChronoScheduler(store, THRESHOLDS)
    scheduler.tick(tmux_session, now=500.0)

    assert store.get_pane(pane_id).state == "working"


def test_tick_returns_empty_when_state_unchanged(tmux_session, store):
    pane_id = tmux_session.list_panes()[0].pane_id
    store.register_pane(pane_id, tmux_session.session_name, role="worker", now=0.0)
    scheduler = ChronoScheduler(store, THRESHOLDS)

    first = scheduler.tick(tmux_session, now=2.0)
    assert first != []
    second = scheduler.tick(tmux_session, now=2.0)
    assert second == []
