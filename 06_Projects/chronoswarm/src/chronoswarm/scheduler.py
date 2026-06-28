"""ChronoScheduler: deterministic wake/sleep lifecycle driven by a real clock
and real captured pane text. No timers are simulated — `tick()` takes the
actual current time (or an injected one, for tests) and actual tmux state."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from .fitness import has_error_marker
from .receipts import record_state_transition
from .store import WorkflowStore
from .tmuxctl import TmuxController


@dataclass(frozen=True)
class SchedulerThresholds:
    cool_after_seconds: float = 300.0
    sleep_after_seconds: float = 900.0
    archive_after_seconds: float = 3600.0
    working_after_seconds: float = 5.0


def next_state(
    current_state: str, idle_seconds: float, has_error: bool, thresholds: SchedulerThresholds
) -> str:
    """Pure function: (state, idle time, error presence) -> next state.
    Errors always demand attention. A pane coming back from sleeping/archived
    passes through 'warming' before settling into the idle-duration ladder."""
    if has_error:
        return "working"
    if current_state in ("sleeping", "archived") and idle_seconds < thresholds.cool_after_seconds:
        return "warming"
    if idle_seconds >= thresholds.archive_after_seconds:
        return "archived"
    if idle_seconds >= thresholds.sleep_after_seconds:
        return "sleeping"
    if idle_seconds >= thresholds.cool_after_seconds:
        return "cooling"
    if idle_seconds < thresholds.working_after_seconds:
        return "working"
    return "awake"


class ChronoScheduler:
    def __init__(self, store: WorkflowStore, thresholds: Optional[SchedulerThresholds] = None):
        self.store = store
        self.thresholds = thresholds or SchedulerThresholds()

    def tick(self, tmux: TmuxController, now: Optional[float] = None) -> List[dict]:
        real_now = now if now is not None else time.time()
        live_pane_ids = {p.pane_id for p in tmux.list_panes()}
        transitions = []

        for record in self.store.list_panes():
            if record.pane_id not in live_pane_ids:
                if record.state != "archived":
                    self.store.update_state(record.pane_id, "archived", real_now)
                    receipt = record_state_transition(
                        self.store, record.pane_id, record.state, "archived", real_now
                    )
                    transitions.append(receipt.to_dict())
                continue

            text = tmux.capture_pane(record.pane_id)
            error_present = has_error_marker(text)
            idle_seconds = max(real_now - record.last_activity_ts, 0.0)
            new_state = next_state(record.state, idle_seconds, error_present, self.thresholds)

            if new_state != record.state:
                self.store.update_state(record.pane_id, new_state, real_now)
                receipt = record_state_transition(
                    self.store, record.pane_id, record.state, new_state, real_now
                )
                transitions.append(receipt.to_dict())

        return transitions
