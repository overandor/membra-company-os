"""GeneticLayoutGovernor: breeds real tmux layouts against layout_fitness and
applies the winner with real `resize-pane` calls. Every snapshot it scores is
built from a real `capture-pane` and real `list-panes` geometry; only the
candidate widths explored during the GA search are hypothetical."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import List, Optional

from .fitness import FitnessWeights, PaneSnapshot, layout_fitness
from .genome import LayoutGenome, evolve_layout
from .receipts import record_layout_breed
from .store import WorkflowStore
from .tmuxctl import TmuxController


class GeneticLayoutGovernor:
    def __init__(
        self,
        tmux: TmuxController,
        store: WorkflowStore,
        fitness_weights: Optional[FitnessWeights] = None,
    ):
        self.tmux = tmux
        self.store = store
        self.fitness_weights = fitness_weights or FitnessWeights()

    def build_snapshots(self, now: Optional[float] = None) -> List[PaneSnapshot]:
        real_now = now if now is not None else time.time()
        panes = sorted(self.tmux.list_panes(), key=lambda p: p.left)
        snapshots = []
        for pane in panes:
            record = self.store.get_pane(pane.pane_id)
            if record is None:
                record = self.store.register_pane(
                    pane.pane_id, pane.session_name, role="unlabeled", now=real_now
                )
            text = self.tmux.capture_pane(pane.pane_id)
            snapshots.append(
                PaneSnapshot(
                    pane_id=pane.pane_id,
                    active=pane.active,
                    left=pane.left,
                    top=pane.top,
                    width=pane.width,
                    height=pane.height,
                    captured_text=text,
                    last_activity_ts=record.last_activity_ts,
                )
            )
        return snapshots

    def breed_and_apply(
        self,
        now: Optional[float] = None,
        generations: int = 30,
        population_size: int = 20,
        seed: Optional[int] = None,
    ) -> dict:
        real_now = now if now is not None else time.time()
        snapshots = self.build_snapshots(real_now)

        if len(snapshots) < 2:
            return {
                "applied": False,
                "reason": "fewer than 2 panes; nothing to breed",
                "pane_count": len(snapshots),
            }

        total_width = sum(s.width for s in snapshots)
        seed_genome = LayoutGenome(weights=tuple(float(s.width) for s in snapshots))
        fitness_before = layout_fitness(snapshots, self.fitness_weights, real_now)

        best = evolve_layout(
            snapshots,
            self.fitness_weights,
            real_now,
            total_width,
            generations=generations,
            population_size=population_size,
            seed=seed,
            seed_genome=seed_genome,
        )
        new_widths = best.to_widths(total_width)
        bred_snapshots = [
            replace(snap, width=w) for snap, w in zip(snapshots, new_widths)
        ]
        fitness_after = layout_fitness(bred_snapshots, self.fitness_weights, real_now)

        receipts = []
        for snap, new_width in zip(snapshots, new_widths):
            if new_width != snap.width:
                self.tmux.resize_pane(snap.pane_id, width=new_width)
            receipt = record_layout_breed(
                self.store,
                snap.pane_id,
                best.weights,
                new_width,
                fitness_before,
                fitness_after,
                real_now,
            )
            receipts.append(receipt.to_dict())

        return {
            "applied": True,
            "fitness_before": fitness_before,
            "fitness_after": fitness_after,
            "pane_count": len(snapshots),
            "receipts": receipts,
        }
