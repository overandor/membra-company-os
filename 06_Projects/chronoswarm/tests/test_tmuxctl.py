import os
import time

import pytest

from chronoswarm.tmuxctl import TmuxController, TmuxError


def unique_session_name(prefix: str = "cs-test") -> str:
    return f"{prefix}-{os.getpid()}-{int(time.time() * 1_000_000)}"


def test_new_session_creates_real_session(tmux_session):
    assert tmux_session.session_exists() is True
    panes = tmux_session.list_panes()
    assert len(panes) == 1
    assert panes[0].session_name == tmux_session.session_name


def test_session_exists_false_for_unknown_session():
    tmux = TmuxController(unique_session_name("cs-nonexistent"))
    assert tmux.session_exists() is False


def test_new_session_twice_raises(tmux_session):
    with pytest.raises(TmuxError):
        tmux_session.new_session()


def test_kill_session_makes_session_exists_false(tmux_session):
    tmux_session.kill_session()
    assert tmux_session.session_exists() is False


def test_split_window_creates_second_real_pane(tmux_session):
    first_pane = tmux_session.list_panes()[0]
    new_pane_id = tmux_session.split_window(first_pane.pane_id)
    panes = tmux_session.list_panes()
    assert len(panes) == 2
    assert {p.pane_id for p in panes} == {first_pane.pane_id, new_pane_id}


def test_split_window_vertical_changes_geometry(tmux_session):
    first_pane = tmux_session.list_panes()[0]
    tmux_session.split_window(first_pane.pane_id, vertical=True)
    panes = tmux_session.list_panes()
    tops = {p.top for p in panes}
    assert len(tops) == 2, "vertical split should stack panes at different top offsets"


def test_send_keys_and_capture_pane_reflects_real_output(tmux_session):
    pane_id = tmux_session.list_panes()[0].pane_id
    tmux_session.send_keys(pane_id, "echo CHRONOSWARM_MARKER_123")
    time.sleep(0.3)
    text = tmux_session.capture_pane(pane_id)
    assert "CHRONOSWARM_MARKER_123" in text


def test_resize_pane_changes_real_width(tmux_session):
    first_pane = tmux_session.list_panes()[0]
    tmux_session.split_window(first_pane.pane_id)
    tmux_session.resize_pane(first_pane.pane_id, width=40)
    panes = {p.pane_id: p for p in tmux_session.list_panes()}
    assert panes[first_pane.pane_id].width == 40


def test_kill_pane_removes_it_from_real_session(tmux_session):
    first_pane = tmux_session.list_panes()[0]
    new_pane_id = tmux_session.split_window(first_pane.pane_id)
    tmux_session.kill_pane(new_pane_id)
    panes = tmux_session.list_panes()
    assert new_pane_id not in {p.pane_id for p in panes}


def test_run_invalid_command_raises_tmux_error(tmux_session):
    with pytest.raises(TmuxError):
        tmux_session._run("definitely-not-a-real-tmux-subcommand")
