"""Deterministic fitness over real tmux pane state.

Every input here is something genuinely observable from a live tmux session:
geometry from `list-panes`, text from `capture-pane`, recency from a clock the
governor maintains by diffing successive captures. Nothing is sampled or
faked — the same snapshot always yields the same score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

ERROR_MARKERS = (
    "Traceback (most recent call last)",
    "FAILED",
    "Error:",
    "Exception:",
    "panic:",
    "fatal:",
)


@dataclass(frozen=True)
class PaneSnapshot:
    pane_id: str
    active: bool
    left: int
    top: int
    width: int
    height: int
    captured_text: str
    last_activity_ts: float

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class FitnessWeights:
    active_visibility: float = 3.0
    error_visibility: float = 4.0
    readability: float = 2.0
    recency: float = 1.5
    context_switch_penalty: float = 1.0
    noise_penalty: float = 1.0
    recency_decay_seconds: float = 120.0
    min_readable_height: int = 3
    min_readable_width: int = 20


def has_error_marker(text: str) -> bool:
    return any(marker in text for marker in ERROR_MARKERS)


def nonblank_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def layout_fitness(
    panes: List[PaneSnapshot],
    weights: FitnessWeights,
    now: float,
    context_switches: int = 0,
) -> float:
    """Higher is better. Rewards: active pane being large enough to read,
    error-bearing panes getting visible area, panes whose visible height
    actually fits their real content, and recently-active panes keeping
    area. Penalizes: idle panes with no errors and no recent activity
    hogging area, and excessive layout churn."""
    if not panes:
        return 0.0

    total_area = sum(p.area for p in panes) or 1
    score = 0.0

    for p in panes:
        area_fraction = p.area / total_area

        if p.active:
            readable = (
                1.0
                if p.height >= weights.min_readable_height
                and p.width >= weights.min_readable_width
                else 0.0
            )
            score += weights.active_visibility * area_fraction * readable

        if has_error_marker(p.captured_text):
            score += weights.error_visibility * area_fraction

        nonblank = nonblank_line_count(p.captured_text)
        readability = min(nonblank / max(p.height, 1), 1.0)
        score += weights.readability * area_fraction * readability

        age = max(now - p.last_activity_ts, 0.0)
        recency = math.exp(-age / weights.recency_decay_seconds)
        score += weights.recency * area_fraction * recency

        is_idle_clutter = (
            not p.active and not has_error_marker(p.captured_text) and recency < 0.05
        )
        if is_idle_clutter:
            score -= weights.noise_penalty * area_fraction

    score -= weights.context_switch_penalty * context_switches
    return score
