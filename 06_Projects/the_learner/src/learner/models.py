"""The Learner and the Anchor — one architecture, one birth, two fates.

TinyPolicyNet: MLP(input_dim -> 16 tanh -> 3 softmax) implemented in numpy.
Both models are instantiated from the same seed and the same weight blob:
  - The Anchor: loaded once, frozen forever, hash re-verified every cycle.
  - The Learner: may be updated only through the bounded trainer, every
    update logged in the journal with before/after weight hashes.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

ACTIONS = ["LONG", "SHORT", "WAIT"]
HIDDEN = 16
INIT_SEED = 20261104


def weights_hash(w1: np.ndarray, b1: np.ndarray,
                 w2: np.ndarray, b2: np.ndarray) -> str:
    """Canonical hash over raw array bytes — stable across npz timestamps."""
    h = hashlib.sha256()
    for a in (w1, b1, w2, b2):
        c = np.ascontiguousarray(a, dtype=np.float64)
        h.update(str(c.shape).encode() + c.tobytes())
    return h.hexdigest()


def save_weights(path: str, w1, b1, w2, b2) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez(path, w1=w1, b1=b1, w2=w2, b2=b2)
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_weights(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    d = np.load(path)
    return d["w1"].copy(), d["b1"].copy(), d["w2"].copy(), d["b2"].copy()


def file_hash(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def init_weights(input_dim: int, seed: int = INIT_SEED):
    rng = np.random.RandomState(seed)
    w1 = rng.randn(input_dim, HIDDEN) * np.sqrt(2.0 / input_dim)
    b1 = np.zeros(HIDDEN)
    w2 = rng.randn(HIDDEN, 3) * np.sqrt(2.0 / HIDDEN)
    b2 = np.zeros(3)
    return w1, b1, w2, b2


@dataclass
class Prediction:
    action: str
    confidence: float
    probs: dict


class TinyPolicyNet:
    def __init__(self, w1, b1, w2, b2, name: str):
        self.w1, self.b1, self.w2, self.b2 = w1, b1, w2, b2
        self.name = name

    def probs(self, x: np.ndarray) -> np.ndarray:
        h = np.tanh(x @ self.w1 + self.b1)
        logits = h @ self.w2 + self.b2
        logits = logits - logits.max()
        e = np.exp(logits)
        return e / e.sum()

    def predict(self, x: np.ndarray) -> Prediction:
        p = self.probs(x)
        i = int(np.argmax(p))
        return Prediction(action=ACTIONS[i], confidence=float(p[i]),
                          probs={a: float(p[j]) for j, a in enumerate(ACTIONS)})

    def hash(self) -> str:
        return weights_hash(self.w1, self.b1, self.w2, self.b2)


class Birth:
    """Creates the initial shared weights and both models' files on disk."""

    def __init__(self, input_dim: int, weights_dir: str):
        os.makedirs(weights_dir, exist_ok=True)
        w1, b1, w2, b2 = init_weights(input_dim)
        self.birth_path = os.path.join(weights_dir, "birth.npz")
        self.learner_path = os.path.join(weights_dir, "learner.npz")
        self.anchor_path = os.path.join(weights_dir, "anchor.npz")
        save_weights(self.birth_path, w1, b1, w2, b2)
        self.birth_hash = weights_hash(w1, b1, w2, b2)
        save_weights(self.learner_path, w1, b1, w2, b2)
        save_weights(self.anchor_path, w1, b1, w2, b2)
        self.learner = TinyPolicyNet(w1, b1, w2, b2, "learner")
        self.anchor = TinyPolicyNet(w1.copy(), b1.copy(),
                                    w2.copy(), b2.copy(), "anchor")
