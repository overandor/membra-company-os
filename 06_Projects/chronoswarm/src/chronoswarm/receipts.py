"""Receipt construction on top of WorkflowStore. Every governor/scheduler
action that changes real state writes one of these — the receipt ledger is
the audit trail for "what changed, why, and what it did to fitness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .store import WorkflowStore


@dataclass(frozen=True)
class Receipt:
    id: int
    ts: float
    pane_id: str
    action: str
    detail: Dict[str, Any]
    fitness_before: Optional[float]
    fitness_after: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.ts,
            "pane_id": self.pane_id,
            "action": self.action,
            "detail": self.detail,
            "fitness_before": self.fitness_before,
            "fitness_after": self.fitness_after,
        }

    @classmethod
    def from_row(cls, row) -> "Receipt":
        rid, ts, pane_id, action, detail, fitness_before, fitness_after = row
        return cls(
            id=rid,
            ts=ts,
            pane_id=pane_id,
            action=action,
            detail=json.loads(detail),
            fitness_before=fitness_before,
            fitness_after=fitness_after,
        )


def record_layout_breed(
    store: WorkflowStore,
    pane_id: str,
    genome_weights: tuple,
    new_width: int,
    fitness_before: float,
    fitness_after: float,
    now: float,
) -> Receipt:
    detail = {"genome_weights": list(genome_weights), "new_width": new_width}
    rid = store.add_receipt(
        pane_id, "layout_breed", json.dumps(detail), now, fitness_before, fitness_after
    )
    return Receipt(rid, now, pane_id, "layout_breed", detail, fitness_before, fitness_after)


def record_state_transition(
    store: WorkflowStore, pane_id: str, from_state: str, to_state: str, now: float
) -> Receipt:
    detail = {"from_state": from_state, "to_state": to_state}
    rid = store.add_receipt(pane_id, "state_transition", json.dumps(detail), now)
    return Receipt(rid, now, pane_id, "state_transition", detail, None, None)


def list_receipts(store: WorkflowStore, pane_id: Optional[str] = None):
    return [Receipt.from_row(row) for row in store.list_receipts(pane_id)]
