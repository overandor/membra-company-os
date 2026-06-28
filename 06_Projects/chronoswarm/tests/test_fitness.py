from chronoswarm.fitness import (
    FitnessWeights,
    PaneSnapshot,
    has_error_marker,
    layout_fitness,
    nonblank_line_count,
)


def _snap(**kwargs):
    defaults = dict(
        pane_id="%0",
        active=False,
        left=0,
        top=0,
        width=80,
        height=40,
        captured_text="",
        last_activity_ts=0.0,
    )
    defaults.update(kwargs)
    return PaneSnapshot(**defaults)


def test_has_error_marker_detects_traceback():
    assert has_error_marker("Traceback (most recent call last):\nValueError\n") is True


def test_has_error_marker_detects_pytest_failed():
    assert has_error_marker("FAILED tests/test_x.py::test_y") is True


def test_has_error_marker_false_for_plain_output():
    assert has_error_marker("hello world\nall good\n") is False


def test_nonblank_line_count_ignores_blank_lines():
    assert nonblank_line_count("a\n\n  \nb\n") == 2


def test_layout_fitness_empty_panes_returns_zero():
    assert layout_fitness([], FitnessWeights(), now=100.0) == 0.0


def test_layout_fitness_rewards_large_readable_active_pane():
    weights = FitnessWeights()
    small_active = [
        _snap(pane_id="%0", active=True, width=10, height=2, last_activity_ts=100.0),
        _snap(pane_id="%1", active=False, width=150, height=40, last_activity_ts=100.0),
    ]
    large_active = [
        _snap(pane_id="%0", active=True, width=150, height=40, last_activity_ts=100.0),
        _snap(pane_id="%1", active=False, width=10, height=2, last_activity_ts=100.0),
    ]
    score_small = layout_fitness(small_active, weights, now=100.0)
    score_large = layout_fitness(large_active, weights, now=100.0)
    assert score_large > score_small


def test_layout_fitness_rewards_visible_error_pane():
    weights = FitnessWeights()
    error_hidden = [
        _snap(pane_id="%0", active=True, width=150, height=40, last_activity_ts=100.0),
        _snap(
            pane_id="%1",
            active=False,
            width=10,
            height=40,
            captured_text="Traceback (most recent call last):\n",
            last_activity_ts=100.0,
        ),
    ]
    error_visible = [
        _snap(pane_id="%0", active=True, width=10, height=40, last_activity_ts=100.0),
        _snap(
            pane_id="%1",
            active=False,
            width=150,
            height=40,
            captured_text="Traceback (most recent call last):\n",
            last_activity_ts=100.0,
        ),
    ]
    assert layout_fitness(error_visible, weights, now=100.0) > layout_fitness(
        error_hidden, weights, now=100.0
    )


def test_layout_fitness_penalizes_idle_clutter():
    weights = FitnessWeights()
    now = 10_000.0
    stale_idle = [
        _snap(pane_id="%0", active=True, width=100, height=40, last_activity_ts=now),
        _snap(pane_id="%1", active=False, width=100, height=40, last_activity_ts=0.0),
    ]
    fresh_idle = [
        _snap(pane_id="%0", active=True, width=100, height=40, last_activity_ts=now),
        _snap(pane_id="%1", active=False, width=100, height=40, last_activity_ts=now),
    ]
    assert layout_fitness(fresh_idle, weights, now=now) > layout_fitness(stale_idle, weights, now=now)


def test_layout_fitness_context_switch_penalty_reduces_score():
    weights = FitnessWeights()
    panes = [_snap(pane_id="%0", active=True, last_activity_ts=100.0)]
    no_switches = layout_fitness(panes, weights, now=100.0, context_switches=0)
    with_switches = layout_fitness(panes, weights, now=100.0, context_switches=5)
    assert with_switches < no_switches


def test_layout_fitness_readability_scales_with_nonblank_content():
    weights = FitnessWeights()
    sparse = [_snap(pane_id="%0", width=100, height=40, captured_text="one line\n", last_activity_ts=100.0)]
    dense = [
        _snap(
            pane_id="%0",
            width=100,
            height=40,
            captured_text="\n".join(f"line {i}" for i in range(40)),
            last_activity_ts=100.0,
        )
    ]
    assert layout_fitness(dense, weights, now=100.0) > layout_fitness(sparse, weights, now=100.0)
