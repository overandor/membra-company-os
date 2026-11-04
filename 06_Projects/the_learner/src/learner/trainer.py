"""Bounded RL trainer — REINFORCE on matured evidence, hard caps, full audit.

Bounds (trainer-v1), recorded in the journal at pilot_start:
  min_batch          : updates need at least this many matured records
  max_updates        : total accepted updates for the whole pilot
  cooldown_s         : minimum seconds between accepted updates
  lr                 : learning rate
  delta_norm_cap     : per-update L2 norm cap (scaled down, never exploded)
  max_drift          : cumulative parameter L2 distance from birth; reject above

Every call logs a training_update event: accepted or rejected, with the
reason, and before/after weight hashes. The Anchor is structurally
untouchable — this class only ever receives the Learner's arrays.
"""

from __future__ import annotations

import os
import time
from typing import Optional

import numpy as np

from . import models


class BoundedTrainer:
    VERSION = "trainer-v1"

    def __init__(self, min_batch: int = 8, max_updates: int = 10,
                 cooldown_s: int = 300, lr: float = 0.02,
                 delta_norm_cap: float = 0.05, max_drift: float = 1.0):
        self.min_batch = min_batch
        self.max_updates = max_updates
        self.cooldown_s = cooldown_s
        self.lr = lr
        self.delta_norm_cap = delta_norm_cap
        self.max_drift = max_drift
        self.updates_done = 0
        self.last_update_ts = 0.0
        self.trained_seqs: set[int] = set()

    def config(self) -> dict:
        return {"version": self.VERSION, "min_batch": self.min_batch,
                "max_updates": self.max_updates, "cooldown_s": self.cooldown_s,
                "lr": self.lr, "delta_norm_cap": self.delta_norm_cap,
                "max_drift": self.max_drift}

    def _reject(self, reason: str, evidence_n: int) -> dict:
        return {"accepted": False, "reason": reason,
                "evidence_n": evidence_n}

    def maybe_update(self, learner: models.TinyPolicyNet,
                     birth_w: tuple[np.ndarray, ...],
                     matured: list[dict],
                     weights_dir: str) -> dict:
        """Consider one update. `matured` = outcome payloads joined with their
        prediction records (features, action, probs, points)."""
        new_evidence = [m for m in matured
                        if m["prediction_seq"] not in self.trained_seqs]
        n = len(new_evidence)
        if self.updates_done >= self.max_updates:
            return self._reject("update_cap_reached", n)
        if time.time() - self.last_update_ts < self.cooldown_s:
            return self._reject("cooldown_active", n)
        if n < self.min_batch:
            return self._reject("insufficient_evidence", n)

        before_hash = learner.hash()
        g_w1 = np.zeros_like(learner.w1); g_b1 = np.zeros_like(learner.b1)
        g_w2 = np.zeros_like(learner.w2); g_b2 = np.zeros_like(learner.b2)
        rewards = [m["learner"]["points"] for m in new_evidence]
        baseline = float(np.mean(rewards))
        for m in new_evidence:
            x = np.array(m["features"], dtype=float)
            a_idx = models.ACTIONS.index(m["learner_action"])
            advantage = m["learner"]["points"] - baseline
            # forward
            h = np.tanh(x @ learner.w1 + learner.b1)
            logits = h @ learner.w2 + learner.b2
            p = np.exp(logits - logits.max()); p /= p.sum()
            # grad log p_a wrt logits
            dlog = -p.copy(); dlog[a_idx] += 1.0
            dlog *= advantage
            g_w2 += np.outer(h, dlog)
            g_b2 += dlog
            dh = (dlog @ learner.w2.T) * (1.0 - h * h)
            g_w1 += np.outer(x, dh)
            g_b1 += dh
        grads = [g_w1 / n, g_b1 / n, g_w2 / n, g_b2 / n]
        delta_norm = float(np.sqrt(sum(float(np.sum(g * g)) for g in grads)))
        if not np.isfinite(delta_norm):
            return self._reject("delta_not_finite", n)
        scale = self.lr
        if delta_norm * self.lr > self.delta_norm_cap:
            scale = self.delta_norm_cap / delta_norm
        cand = [w + scale * g for w, g in
                zip((learner.w1, learner.b1, learner.w2, learner.b2), grads)]
        drift = float(np.sqrt(sum(float(np.sum((c - b) ** 2)) for c, b in
                                  zip(cand, birth_w))))
        if drift > self.max_drift:
            return self._reject("max_drift_exceeded", n) | {"drift": drift}
        learner.w1, learner.b1, learner.w2, learner.b2 = cand
        after_hash = learner.hash()
        self.updates_done += 1
        self.last_update_ts = time.time()
        self.trained_seqs.update(m["prediction_seq"] for m in new_evidence)
        ckpt = os.path.join(weights_dir,
                            f"learner_update_{self.updates_done:02d}.npz")
        models.save_weights(ckpt, *cand)
        return {"accepted": True, "reason": "evidence_met_bounds",
                "evidence_n": n, "baseline": baseline,
                "delta_norm_raw": delta_norm,
                "delta_norm_applied": delta_norm * scale,
                "drift_from_birth": drift,
                "updates_done": self.updates_done,
                "weights_hash_before": before_hash,
                "weights_hash_after": after_hash,
                "checkpoint": os.path.basename(ckpt),
                "trained_seqs": sorted(m["prediction_seq"]
                                       for m in new_evidence)}
