"""Real tmux process control. No simulated panes — every call shells out to the
real `tmux` binary and reflects the real state of a real session."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List, Optional

_PANE_FORMAT = (
    "#{pane_id}\t#{session_name}\t#{window_index}\t#{pane_left}\t#{pane_top}\t"
    "#{pane_width}\t#{pane_height}\t#{pane_active}\t#{pane_pid}\t#{pane_current_command}"
)


class TmuxError(RuntimeError):
    """Raised when the underlying `tmux` binary returns a non-zero exit code."""


@dataclass(frozen=True)
class PaneInfo:
    pane_id: str
    session_name: str
    window_index: int
    left: int
    top: int
    width: int
    height: int
    active: bool
    pid: int
    current_command: str

    @classmethod
    def from_line(cls, line: str) -> "PaneInfo":
        (
            pane_id,
            session_name,
            window_index,
            left,
            top,
            width,
            height,
            active,
            pid,
            current_command,
        ) = line.split("\t")
        return cls(
            pane_id=pane_id,
            session_name=session_name,
            window_index=int(window_index),
            left=int(left),
            top=int(top),
            width=int(width),
            height=int(height),
            active=active == "1",
            pid=int(pid),
            current_command=current_command,
        )


class TmuxController:
    """Thin, real wrapper around the `tmux` CLI for a single named session."""

    def __init__(self, session_name: str, tmux_bin: str = "tmux"):
        self.session_name = session_name
        self._tmux_bin = tmux_bin

    def _run(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            [self._tmux_bin, *args],
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise TmuxError(
                f"tmux {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}"
            )
        return result.stdout.strip()

    def session_exists(self) -> bool:
        result = subprocess.run(
            [self._tmux_bin, "has-session", "-t", self.session_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def new_session(self, width: int = 200, height: int = 50) -> str:
        """Create the detached session and return the id of its first pane."""
        if self.session_exists():
            raise TmuxError(f"session {self.session_name!r} already exists")
        self._run(
            "new-session",
            "-d",
            "-s",
            self.session_name,
            "-x",
            str(width),
            "-y",
            str(height),
        )
        panes = self.list_panes()
        return panes[0].pane_id

    def kill_session(self) -> None:
        if self.session_exists():
            self._run("kill-session", "-t", self.session_name)

    def list_panes(self) -> List[PaneInfo]:
        out = self._run("list-panes", "-t", self.session_name, "-F", _PANE_FORMAT)
        if not out:
            return []
        return [PaneInfo.from_line(line) for line in out.splitlines()]

    def split_window(
        self,
        pane_id: str,
        vertical: bool = False,
        size_pct: Optional[int] = None,
    ) -> str:
        """Split `pane_id`. Horizontal split (default) stacks left/right;
        vertical=True stacks top/bottom. Returns the new pane's id."""
        args = ["split-window", "-P", "-F", "#{pane_id}", "-t", pane_id]
        args.append("-v" if vertical else "-h")
        if size_pct is not None:
            args.extend(["-p", str(size_pct)])
        return self._run(*args)

    def resize_pane(self, pane_id: str, width: Optional[int] = None, height: Optional[int] = None) -> None:
        if width is not None:
            self._run("resize-pane", "-t", pane_id, "-x", str(width))
        if height is not None:
            self._run("resize-pane", "-t", pane_id, "-y", str(height))

    def select_pane(self, pane_id: str) -> None:
        self._run("select-pane", "-t", pane_id)

    def capture_pane(self, pane_id: str, history_lines: int = 200) -> str:
        return self._run(
            "capture-pane", "-p", "-t", pane_id, "-S", f"-{history_lines}"
        )

    def send_keys(self, pane_id: str, keys: str, enter: bool = True) -> None:
        args = ["send-keys", "-t", pane_id, keys]
        if enter:
            args.append("Enter")
        self._run(*args)

    def kill_pane(self, pane_id: str) -> None:
        self._run("kill-pane", "-t", pane_id)
