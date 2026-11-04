"""Gate.io public futures feed — BTC_USDT perpetual, read-only, unauthenticated.

Public endpoints only:
  GET /api/v4/futures/usdt/candlesticks?contract=BTC_USDT&interval=1m&limit=N
  GET /api/v4/futures/usdt/tickers?contract=BTC_USDT

A snapshot is either VALID (all checks pass) or explicitly INVALID with a
reason. Invalid/stale data never produces an interpolated prediction —
integrity rule 3.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import requests

BASE = "https://api.gateio.ws"
CONTRACT = "BTC_USDT"
SETTLE = "usdt"
TIMEOUT_S = 10
MAX_STALE_S = 75  # latest closed candle must open within 75s of the boundary
GAP_S = 90        # allowed gap between consecutive 1m candles before "non-contiguous"


@dataclass
class Candle:
    t: int          # open time, unix seconds (minute-aligned)
    o: float
    h: float
    l: float
    c: float
    v: float


@dataclass
class MarketSnapshot:
    minute_ts: int                      # the minute boundary this snapshot serves
    valid: bool
    invalid_reason: Optional[str] = None
    candles: list[Candle] = field(default_factory=list)   # closed candles, ascending t
    entry_price: Optional[float] = None  # close of the last closed candle
    mark_price: Optional[float] = None
    last_price: Optional[float] = None
    funding_rate: float = 0.0
    fetched_at: int = 0

    def price_at(self) -> Optional[float]:
        return self.entry_price


class GateFeed:
    def __init__(self, session: Optional[requests.Session] = None):
        self.s = session or requests.Session()
        self.s.headers.update({"Accept": "application/json"})

    def _get(self, path: str, params: dict):
        r = self.s.get(BASE + path, params=params, timeout=TIMEOUT_S)
        r.raise_for_status()
        return r.json()

    def ticker(self) -> dict:
        rows = self._get(f"/api/v4/futures/{SETTLE}/tickers",
                         {"contract": CONTRACT})
        return rows[0] if rows else {}

    def candles(self, limit: int = 40) -> list[Candle]:
        rows = self._get(f"/api/v4/futures/{SETTLE}/candlesticks",
                         {"contract": CONTRACT, "interval": "1m",
                          "limit": str(limit)})
        out = []
        for row in rows:
            out.append(Candle(t=int(row["t"]), o=float(row["o"]),
                              h=float(row["h"]), l=float(row["l"]),
                              c=float(row["c"]), v=float(row["v"])))
        out.sort(key=lambda c: c.t)
        return out

    def snapshot(self, minute_ts: int, limit: int = 40) -> MarketSnapshot:
        """Validate data for a prediction at boundary `minute_ts`.

        Closed candles only: the newest usable candle opens at minute_ts-60.
        """
        snap = MarketSnapshot(minute_ts=minute_ts, valid=False,
                              fetched_at=int(time.time()))
        try:
            candles = self.candles(limit=limit)
            tick = self.ticker()
        except Exception as exc:
            snap.invalid_reason = f"feed_unreachable:{type(exc).__name__}"
            return snap
        if not tick or "mark_price" not in tick or "last" not in tick:
            snap.invalid_reason = "ticker_missing_fields"
            return snap
        newest_allowed = minute_ts - 60
        closed = [c for c in candles if c.t <= newest_allowed]
        if not closed:
            snap.invalid_reason = "no_closed_candle"
            return snap
        if closed[-1].t < newest_allowed - (MAX_STALE_S - 60):
            snap.invalid_reason = (f"stale_candle:latest_open={closed[-1].t}"
                                   f"<{newest_allowed}")
            return snap
        for a, b in zip(closed, closed[1:]):
            if b.t - a.t > GAP_S:
                snap.invalid_reason = f"non_contiguous:{a.t}->{b.t}"
                return snap
        snap.valid = True
        snap.candles = closed
        snap.entry_price = closed[-1].c
        snap.mark_price = float(tick["mark_price"])
        snap.last_price = float(tick["last"])
        snap.funding_rate = float(tick.get("funding_rate", 0.0) or 0.0)
        return snap

    def exit_price(self, mature_minute_ts: int) -> tuple[Optional[float], Optional[str]]:
        """Close of the candle that opened at mature_minute_ts-60.

        With horizon H, a prediction at T matures at boundary T+H; the exit is
        the close of the candle opened at T+H-60 (the last fully closed minute).
        """
        want_t = mature_minute_ts - 60
        try:
            candles = self.candles(limit=8)
        except Exception as exc:
            return None, f"feed_unreachable:{type(exc).__name__}"
        for c in candles:
            if c.t == want_t:
                return c.c, None
        if candles and candles[-1].t < want_t:
            return None, f"exit_candle_not_yet_closed:latest={candles[-1].t}"
        return None, f"exit_candle_missing:t={want_t}"
