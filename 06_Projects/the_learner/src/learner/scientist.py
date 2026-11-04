"""The Scientist — Navier–Stokes-inspired and spinor feature models.

The Scientist treats the 1-minute return series as a one-dimensional fluid
(Navier–Stokes-inspired) and as a complex spinor field (time-delay embedding).
Its features are computed alongside simple indicators; the honest comparison
(baseline vs scientist) is evaluated on matured evidence and reported on air —
including when the scientist loses.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

from .feed import Candle

SIMPLE_NAMES = [
    "ret_1m_bps", "ret_5m_bps", "ret_15m_bps",
    "rsi14", "ema_diff_bps", "realized_vol_bps",
    "volume_z", "range_pos", "funding_rate_1e4",
]
SCIENTIST_NAMES = [
    "ns_velocity",       # momentum flux: EMA of returns
    "ns_acceleration",   # Δ of velocity — convective term
    "ns_dissipation",    # viscosity proxy: mean |r - v|
    "ns_reynolds",       # momentum-to-friction ratio
    "ns_vorticity",      # shear: fast-EMA minus slow-EMA
    "ns_pressure_grad",  # compression: |r| smoothed, two scales diff
    "sp_phase_coherence",  # |mean(e^{iφ})| of delay-embedded field
    "sp_phase_drift",      # Δφ of the embedded spinor
    "sp_modulus_energy",   # mean |z|^2
    "sp_chirality",        # signed spin imbalance (up-phase vs down-phase)
]

FEATURE_NAMES = SIMPLE_NAMES + SCIENTIST_NAMES

_EPS = 1e-12


def _ema(x: np.ndarray, span: int) -> float:
    if len(x) == 0:
        return 0.0
    alpha = 2.0 / (span + 1.0)
    out = float(x[0])
    for v in x[1:]:
        out = alpha * float(v) + (1.0 - alpha) * out
    return out


def _rsi(closes: np.ndarray, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    d = np.diff(closes[-(period + 1):])
    gains = np.where(d > 0, d, 0.0).mean()
    losses = np.where(d < 0, -d, 0.0).mean()
    if losses < _EPS:
        return 100.0 if gains > _EPS else 50.0
    rs = gains / losses
    return 100.0 - 100.0 / (1.0 + rs)


def compute_features(candles: list[Candle], funding_rate: float = 0.0) -> np.ndarray:
    """Deterministic feature vector from closed candles (ascending t)."""
    closes = np.array([c.c for c in candles], dtype=float)
    vols = np.array([c.v for c in candles], dtype=float)
    highs = np.array([c.h for c in candles], dtype=float)
    lows = np.array([c.l for c in candles], dtype=float)
    rets = np.diff(np.log(np.maximum(closes, _EPS))) * 1e4  # bps per minute

    def span_ret(n: int) -> float:
        if len(closes) > n:
            return (closes[-1] / closes[-1 - n] - 1.0) * 1e4
        return 0.0

    ema_fast = _ema(closes[-20:], 5)
    ema_slow = _ema(closes[-20:], 20)
    ema_diff = (ema_fast - ema_slow) / max(closes[-1], _EPS) * 1e4
    realized_vol = float(np.std(rets[-20:])) if len(rets) >= 5 else 0.0
    v_mu = float(np.mean(vols[-20:])) if len(vols) >= 5 else 0.0
    v_sd = float(np.std(vols[-20:])) or 1.0
    volume_z = (vols[-1] - v_mu) / v_sd
    win = min(20, len(closes))
    hi = float(np.max(highs[-win:])); lo = float(np.min(lows[-win:]))
    range_pos = (closes[-1] - lo) / max(hi - lo, _EPS)

    # --- Navier–Stokes-inspired fluid features on the return field ---
    r = rets[-30:] if len(rets) else np.array([0.0])
    v_flux = _ema(r, 8)                                  # velocity ≈ momentum flux
    v_flux_long = _ema(r, 21)
    accel = v_flux - _ema(r[:-1], 8) if len(r) > 1 else 0.0
    dissipation = float(np.mean(np.abs(r - v_flux))) or _EPS
    reynolds = abs(v_flux) * math.sqrt(len(r)) / dissipation
    vorticity = v_flux - v_flux_long                     # shear between scales
    p_fast = float(np.mean(np.abs(r[-5:])))
    p_slow = float(np.mean(np.abs(r)))
    pressure_grad = p_fast - p_slow

    # --- Spinor features: delay-embedded complex field ---
    k = 2
    if len(r) > k:
        z = r[k:] + 1j * r[:-k]
        phase = np.angle(z)
        coherence = float(np.abs(np.mean(np.exp(1j * phase))))
        drift = float(phase[-1] - phase[-2]) if len(phase) > 1 else 0.0
        modulus_energy = float(np.mean(np.abs(z) ** 2))
        up = float(np.mean(np.sin(phase) > 0))
        chirality = 2.0 * up - 1.0
    else:
        coherence = drift = modulus_energy = chirality = 0.0

    vec = np.array([
        span_ret(1), span_ret(5), span_ret(15),
        (_rsi(closes) - 50.0) / 50.0,
        ema_diff, realized_vol, volume_z, range_pos,
        funding_rate * 1e4,
        v_flux, accel, dissipation, reynolds, vorticity, pressure_grad,
        coherence, drift, modulus_energy, chirality,
    ], dtype=float)
    return np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)


def feature_spec() -> dict:
    return {"version": "features-v1", "names": FEATURE_NAMES,
            "dim": len(FEATURE_NAMES)}


def probe_accuracy(matured: list[dict], feature_idx: list[int],
                   min_samples: int = 8) -> Optional[float]:
    """Honest probe: single-layer logistic on the named features only.

    Leave-one-out on the matured evidence: predict the truth label's sign
    from a tiny ridge-regression fit, count directional correctness.
    Returns None when evidence is insufficient — never fabricates a number.
    """
    rows = [(np.array(m["features"], dtype=float), m["truth_bps"])
            for m in matured if m.get("features") and "truth_bps" in m]
    if len(rows) < min_samples:
        return None
    correct = 0
    n = 0
    for i in range(len(rows)):
        train = [rows[j] for j in range(len(rows)) if j != i]
        X = np.stack([r[0][feature_idx] for r in train])
        y = np.sign(np.array([r[1] for r in train]))
        Xs = (X - X.mean(0)) / (X.std(0) + _EPS)
        w = np.linalg.solve(Xs.T @ Xs + 1.0 * np.eye(len(feature_idx)),
                            Xs.T @ y)
        xt = rows[i][0][feature_idx]
        pred = float((xt - X.mean(0)) / (X.std(0) + _EPS) @ w)
        truth_sign = np.sign(rows[i][1])
        n += 1
        if truth_sign != 0 and np.sign(pred) == truth_sign:
            correct += 1
        elif truth_sign == 0:
            n -= 1
    return correct / n if n else None
