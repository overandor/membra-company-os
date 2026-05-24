"""
quoting_engine.py — Core market-making quoting logic.

Strategy: Top-of-book maker quoting (micro-price perpetuals).

Execution rule:
  • BUY  order posted AT best bid price   → joins the bid queue
  • SELL order posted AT best ask price   → joins the ask queue

We are passive makers targeting the absolute inside spread.
This is maximum aggressive passive market making — minimum spread, maximum fill.

Quote decision flow:
  1. Check risk (can_quote, allowed sizes).
  2. Read BBO from local order book.
  3. Validate BBO (not stale, within price ceiling, spread ≥ 1 tick).
  4. Compute bid_size and ask_size respecting inventory skew.
  5. Call OMS.quote() → handles idempotent cancel/replace.
"""
from __future__ import annotations

import asyncio
import logging
import time
from decimal import Decimal
from typing import Optional

import aiohttp

from app.core.config import mm_config, ContractSpec, MICRO_CONTRACTS
from app.market_data.order_book import registry as ob_registry
from app.oms.oms import oms
from app.risk.risk import risk

log = logging.getLogger("quoting_engine")

ZERO = Decimal("0")

# Maximum age of BBO before we suppress quoting (stale feed guard).
_BBO_MAX_AGE_MS = 2_000


class QuotingEngine:
    """
    Per-session quoting engine.
    Spawns one coroutine per contract watching its BBO stream.
    """

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._tasks:   list[asyncio.Task] = []
        self._running: bool = False

    async def start(self) -> None:
        """Launch one quoting loop per contract."""
        self._running = True
        for contract in MICRO_CONTRACTS:
            if contract not in mm_config.contracts:
                log.warning("No spec for %s — skipping quoting", contract)
                continue
            task = asyncio.create_task(
                self._quote_loop(contract),
                name=f"quote-{contract}",
            )
            self._tasks.append(task)
        log.info("QuotingEngine started for %d contracts", len(self._tasks))

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        # Proper shutdown: cancel on exchange first, then clear local state
        await oms.cancel_all_exchange(self._session)
        await oms.clear_local_state()
        log.info("QuotingEngine stopped — all orders cancelled")

    async def _quote_loop(self, contract: str) -> None:
        """
        Single-contract quoting coroutine.
        Wakes on every BBO change via asyncio.Event signalled by the WS dispatcher.
        """
        ob    = ob_registry.get_or_create(contract)
        spec  = mm_config.contracts[contract]

        # BBO-change event injected by WS dispatcher.
        bbo_event: asyncio.Event = asyncio.Event()
        _bbo_events[contract] = bbo_event

        log.info("Quote loop active: %s", contract)

        while self._running:
            # Wait for BBO update or timeout (TTL enforcement).
            try:
                await asyncio.wait_for(
                    bbo_event.wait(),
                    timeout=mm_config.order_ttl_s,
                )
                bbo_event.clear()
            except asyncio.TimeoutError:
                pass  # Trigger TTL reprice check even without new BBO.

            await self._evaluate_and_quote(contract, spec, ob)

    async def _evaluate_and_quote(
        self,
        contract: str,
        spec:     ContractSpec,
        ob,
    ) -> None:
        """Core quoting decision for one contract at one moment."""

        # ── Guard: global / contract halt ────────────────────────────────────
        if not risk.can_quote(contract, spec):
            # Cancel any open orders when halted.
            await oms.quote(
                self._session, contract,
                bid_price=None, ask_price=None,
                bid_size=0, ask_size=0,
            )
            return

        # ── Guard: stale BBO ─────────────────────────────────────────────────
        bbo = ob.bbo
        if bbo is None or not bbo.valid():
            log.debug("%s: no valid BBO yet, skipping quote", contract)
            return

        if bbo.age_ms > _BBO_MAX_AGE_MS:
            log.warning(
                "%s: BBO stale (%d ms), suppressing quote",
                contract, bbo.age_ms,
            )
            await oms.quote(
                self._session, contract,
                bid_price=None, ask_price=None,
                bid_size=0, ask_size=0,
            )
            return

        # ── Guard: price ceiling (micro-price only) ───────────────────────────
        if bbo.ask_price > spec.max_price:
            log.warning(
                "%s: ask_price=%s exceeds micro ceiling %s, skipping",
                contract, bbo.ask_price, spec.max_price,
            )
            return

        # ── Guard: minimum spread (≥ 1 tick) ─────────────────────────────────
        if bbo.spread < spec.tick_size:
            log.debug(
                "%s: spread=%s < tick=%s — crossed book, skipping",
                contract, bbo.spread, spec.tick_size,
            )
            return

        # ── Compute sizes with inventory skew ────────────────────────────────
        base_size = mm_config.order_size

        bid_size = risk.allowed_buy_size(contract, base_size)
        ask_size = risk.allowed_sell_size(contract, base_size)

        # ── Quote prices: join top of book ────────────────────────────────────
        #   BUY  at best_bid  → we are at the front of the bid queue
        #   SELL at best_ask  → we are at the front of the ask queue
        bid_price: Optional[Decimal] = bbo.bid_price if bid_size > 0 else None
        ask_price: Optional[Decimal] = bbo.ask_price if ask_size > 0 else None

        log.debug(
            "Quote decision %s: BID %s×%s  ASK %s×%s  spread=%s  pos=%+d",
            contract,
            bid_size, bid_price,
            ask_size, ask_price,
            bbo.spread,
            risk.net_position(contract),
        )

        # ── Submit to OMS (idempotent — handles cancel/replace) ───────────────
        await oms.quote(
            self._session, contract,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=bid_size,
            ask_size=ask_size,
        )


# ─── BBO event bus ────────────────────────────────────────────────────────────
# Maps contract → asyncio.Event signalled on each BBO change.
# Populated by QuotingEngine, read by WS dispatcher.
_bbo_events: dict[str, asyncio.Event] = {}


def signal_bbo_change(contract: str) -> None:
    """Called by WS dispatcher when a BBO update arrives."""
    ev = _bbo_events.get(contract)
    if ev:
        ev.set()


# Module-level singleton engine (initialized in main.py).
engine: Optional[QuotingEngine] = None
