"""
order_book.py — Local limit order book (LOB) for Gate.io futures.

Maintains a L2 snapshot + incremental update state per contract.

Gate.io WS delivers:
  • futures.order_book  → "all" snapshot on subscribe, then incremental
  • futures.book_ticker → BBO (best bid/offer) tick — lightweight alternative

We use book_ticker (fastest BBO feed) as primary quoting signal, and
maintain full L2 only for depth validation / anti-gaming checks.

Thread safety: asyncio single-threaded; no locks needed.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("order_book")

PRICE_ZERO = Decimal("0")


@dataclass
class Level:
    price: Decimal
    size:  int       # 0 means level deleted


@dataclass
class BBO:
    """Best bid / best ask at a moment in time."""
    bid_price: Decimal
    bid_size:  int
    ask_price: Decimal
    ask_size:  int
    ts_ms:     int = field(default_factory=lambda: int(time.time() * 1000))

    @property
    def mid(self) -> Decimal:
        if self.bid_price > PRICE_ZERO and self.ask_price > PRICE_ZERO:
            return (self.bid_price + self.ask_price) / 2
        return PRICE_ZERO

    @property
    def spread(self) -> Decimal:
        if self.bid_price > PRICE_ZERO and self.ask_price > PRICE_ZERO:
            return self.ask_price - self.bid_price
        return PRICE_ZERO

    @property
    def age_ms(self) -> int:
        return int(time.time() * 1000) - self.ts_ms

    def valid(self) -> bool:
        return (
            self.bid_price > PRICE_ZERO
            and self.ask_price > PRICE_ZERO
            and self.ask_price > self.bid_price
        )


class OrderBook:
    """
    Per-contract local order book.

    Tracks BBO via book_ticker for quoting.
    Optionally tracks full L2 for depth analysis.
    """

    def __init__(self, contract: str):
        self.contract = contract

        # BBO (updated from book_ticker channel — lowest latency)
        self._bbo: Optional[BBO] = None

        # Full L2 (updated from order_book channel)
        self._bids: Dict[Decimal, int] = {}   # price → size
        self._asks: Dict[Decimal, int] = {}
        self._ob_seq: int = 0

        # Stale detection
        self._last_update_ms: int = 0
        self._stale_threshold_ms: int = 3_000  # 3 s without update = stale

    # ─── BBO accessors ───────────────────────────────────────────────────────

    @property
    def bbo(self) -> Optional[BBO]:
        return self._bbo

    def best_bid(self) -> Optional[Decimal]:
        return self._bbo.bid_price if self._bbo else None

    def best_ask(self) -> Optional[Decimal]:
        return self._bbo.ask_price if self._bbo else None

    def is_stale(self) -> bool:
        if self._last_update_ms == 0:
            return True
        return (int(time.time() * 1000) - self._last_update_ms) > self._stale_threshold_ms

    # ─── Update handlers (called from WS dispatcher) ─────────────────────────

    def on_book_ticker(self, data: dict) -> Optional[BBO]:
        """
        Handle futures.book_ticker message.
        Returns new BBO if it changed materially, else None.
        """
        try:
            bid_p = Decimal(str(data["b"]))
            bid_s = int(data["B"])
            ask_p = Decimal(str(data["a"]))
            ask_s = int(data["A"])
        except (KeyError, ValueError) as exc:
            log.warning("book_ticker parse error %s: %s", self.contract, exc)
            return None

        new_bbo = BBO(
            bid_price=bid_p, bid_size=bid_s,
            ask_price=ask_p, ask_size=ask_s,
        )
        self._last_update_ms = new_bbo.ts_ms

        prev = self._bbo
        self._bbo = new_bbo

        changed = (
            prev is None
            or prev.bid_price != new_bbo.bid_price
            or prev.ask_price != new_bbo.ask_price
        )
        return new_bbo if changed else None

    def on_order_book_snapshot(self, data: dict) -> None:
        """Handle full L2 snapshot (futures.order_book 'all' event)."""
        self._bids.clear()
        self._asks.clear()
        for lvl in data.get("bids", []):
            p, s = Decimal(str(lvl[0])), int(lvl[1])
            if s > 0:
                self._bids[p] = s
        for lvl in data.get("asks", []):
            p, s = Decimal(str(lvl[0])), int(lvl[1])
            if s > 0:
                self._asks[p] = s
        self._ob_seq = int(data.get("id", 0))
        self._last_update_ms = int(time.time() * 1000)
        self._sync_bbo_from_l2()

    def on_order_book_update(self, data: dict) -> None:
        """Handle incremental L2 delta."""
        for lvl in data.get("bids", []):
            p, s = Decimal(str(lvl[0])), int(lvl[1])
            if s == 0:
                self._bids.pop(p, None)
            else:
                self._bids[p] = s
        for lvl in data.get("asks", []):
            p, s = Decimal(str(lvl[0])), int(lvl[1])
            if s == 0:
                self._asks.pop(p, None)
            else:
                self._asks[p] = s
        self._ob_seq = int(data.get("id", 0))
        self._last_update_ms = int(time.time() * 1000)
        self._sync_bbo_from_l2()

    def _sync_bbo_from_l2(self) -> None:
        """Update BBO from L2 state (used when book_ticker is unavailable)."""
        if not self._bids or not self._asks:
            return
        best_bid_price = max(self._bids.keys())
        best_ask_price = min(self._asks.keys())
        new_bbo = BBO(
            bid_price=best_bid_price,
            bid_size=self._bids[best_bid_price],
            ask_price=best_ask_price,
            ask_size=self._asks[best_ask_price],
        )
        if self._bbo is None or self._bbo.bid_price != new_bbo.bid_price or self._bbo.ask_price != new_bbo.ask_price:
            self._bbo = new_bbo

    # ─── Depth utilities ─────────────────────────────────────────────────────

    def bid_depth(self, n: int = 5) -> List[Tuple[Decimal, int]]:
        return sorted(self._bids.items(), reverse=True)[:n]

    def ask_depth(self, n: int = 5) -> List[Tuple[Decimal, int]]:
        return sorted(self._asks.items())[:n]

    def cumulative_bid_depth(self, levels: int = 3) -> int:
        """Total contracts on bid side (top N levels)."""
        return sum(s for _, s in self.bid_depth(levels))

    def cumulative_ask_depth(self, levels: int = 3) -> int:
        """Total contracts on ask side (top N levels)."""
        return sum(s for _, s in self.ask_depth(levels))


class OrderBookRegistry:
    """Holds one OrderBook per tracked contract."""

    def __init__(self):
        self._books: Dict[str, OrderBook] = {}

    def get_or_create(self, contract: str) -> OrderBook:
        if contract not in self._books:
            self._books[contract] = OrderBook(contract)
        return self._books[contract]

    def __getitem__(self, contract: str) -> OrderBook:
        return self._books[contract]

    def contracts(self) -> List[str]:
        return list(self._books.keys())


# Module-level singleton.
registry = OrderBookRegistry()
