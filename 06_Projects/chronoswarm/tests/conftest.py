import os
import time

import pytest

from chronoswarm.tmuxctl import TmuxController


def unique_session_name(prefix: str = "cs-test") -> str:
    return f"{prefix}-{os.getpid()}-{int(time.time() * 1_000_000)}"


@pytest.fixture
def tmux_session():
    """A real, live tmux session (single pane), killed after the test."""
    tmux = TmuxController(unique_session_name())
    tmux.new_session(width=160, height=40)
    yield tmux
    tmux.kill_session()
