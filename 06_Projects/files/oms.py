"""
oms.py — Order Management System.

Tracks all live maker orders for each contract.
Enforces TTL (time-to-live) expiry.
Detects fills from private WS and reconciles with risk engine.
Provides a clean API to the quoting logic.

State model per contract:
  ┌─────────────────────────────────────────────────────────┐
  │  bid_order_id:  int | None   (our live buy order)       │
  │  ask_order_id:  int | None   (our live sell order)      │
  │  bid_price:     Decimal | None                          │
  │  ask_price:     Decimal | None                          │
  │  bid_placed_ts: float                                   │
  │  ask_placed_ts: float                                   │
  └─────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Optional, Any

import aiohttp

from config import mm_config
from risk import risk, Fill

log = logging.getLogger("oms")

ZERO = Decimal("0")
_NO_ORDER = None


@dataclass
class ContractOrders:
    """Mutable per-contract order state."""
    contract: str

    bid_order_id:  Optional[int]     = None
    bid_price:     Optional[Decimal] = None
    bid_size:      int               = 0
    bid_placed_ts: float             = 0.0

    ask_order_id:  Optional[int]     = None
    ask_price:     Optional[Decimal] = None
    ask_size:      int               = 0
    ask_placed_ts: float             = 0.0

    # Pending cancellation flags to avoid double-cancel races.
    bid_cancelling: bool = False
    ask_cancelling: bool = False

    def bid_age(self) -> float:
        return time.time() - self.bid_placed_ts if self.bid_order_id else 0.0

    def ask_age(self) -> float:
        return time.time() - self.ask_placed_ts if self.ask_order_id else 0.0

    def bid_ttl_expired(self, ttl: float) -> bool:
        return self.bid_order_id is not None and self.bid_age() > ttl

    def ask_ttl_expired(self, ttl: float) -> bool:
        return self.ask_order_id is not None and self.ask_age() > ttl


class OMS:
    """
    Central order management system.

    Coordinates between the quoting logic, REST client, and risk engine.
    """

    def __init__(self):
        self._state:  Dict[str, ContractOrders] = {}
        self._lock:   asyncio.Lock = asyncio.Lock()

    def _get_or_create(self, contract: str) -> ContractOrders:
        if contract not in self._state:
            self._state[contract] = ContractOrders(contract=contract)
        return self._state[contract]

    # ─── Quote placement ──────────────────────────────────────────────────────

    async def quote(
        self,
        session:   aiohttp.ClientSession,
        contract:  str,
        bid_price: Optional[Decimal],
        ask_price: Optional[Decimal],
        bid_size:  int,
        ask_size:  int,
    ) -> None:
        """
        Idempotent quote update.

        For each side:
          • If no live order → place new order.
          • If live order price differs by ≥ reprice_threshold → cancel + replace.
          • If live order price unchanged → leave it (avoid unnecessary cancel).
          • If size is 0 (risk prohibited) → cancel any live order on that side.
        """
        from rest_client import place_order, cancel_order  # avoid circular at module level

        async with self._lock:
            s = self._get_or_create(contract)
            spec = mm_config.contracts.get(contract)
            if spec is None:
                log.warning("quote: unknown contract %s", contract)
                return

            tick = spec.tick_size

            # ── BID side ─────────────────────────────────────────────────────
            if bid_price is not None and bid_size > 0:
                await self._refresh_side(
                    session, s, contract, "bid",
                    target_price=bid_price,
                    target_size=bid_size,
                    tick=tick,
                    positive_size=+bid_size,
                )
            elif s.bid_order_id is not None and not s.bid_cancelling:
                await self._cancel_side(session, s, contract, "bid")

            # ── ASK side ─────────────────────────────────────────────────────
            if ask_price is not None and ask_size > 0:
                await self._refresh_side(
                    session, s, contract, "ask",
                    target_price=ask_price,
                    target_size=ask_size,
                    tick=tick,
                    positive_size=-ask_size,   # negative = sell
                )
            elif s.ask_order_id is not None and not s.ask_cancelling:
                await self._cancel_side(session, s, contract, "ask")

    async def _refresh_side(
        self,
        session:       aiohttp.ClientSession,
        s:             ContractOrders,
        contract:      str,
        side:          str,           # "bid" | "ask"
        target_price:  Decimal,
        target_size:   int,
        tick:          Decimal,
        positive_size: int,
    ) -> None:
        """Cancel and re-post if price has moved by ≥ reprice_tick_threshold ticks."""
        from rest_client import place_order, cancel_order

        live_id    = s.bid_order_id if side == "bid" else s.ask_order_id
        live_price = s.bid_price    if side == "bid" else s.ask_price

        if live_id is not None and live_price is not None:
            ticks_moved = abs(target_price - live_price) / tick
            ttl_expired = (
                s.bid_ttl_expired(mm_config.order_ttl_s)
                if side == "bid"
                else s.ask_ttl_expired(mm_config.order_ttl_s)
            )

            needs_reprice = (
                ticks_moved >= mm_config.reprice_tick_threshold
                or ttl_expired
            )

            if not needs_reprice:
                return  # Order is still good — leave it.

            # Cancel existing.
            await self._cancel_side(session, s, contract, side)

        # Place new order.
        resp = await place_order(
            session, contract,
            size=positive_size,
            price=target_price,
            tif="poc",  # post-only maker
        )
        if resp.get("id") and resp.get("id") != -1:
            order_id = int(resp["id"])
            now = time.time()
            if side == "bid":
                s.bid_order_id  = order_id
                s.bid_price     = target_price
                s.bid_size      = target_size
                s.bid_placed_ts = now
            else:
                s.ask_order_id  = order_id
                s.ask_price     = target_price
                s.ask_size      = target_size
                s.ask_placed_ts = now

            log.info(
                "Placed %s order  contract=%s  id=%d  price=%s  size=%+d",
                side.upper(), contract, order_id, target_price, positive_size,
            )
        else:
            log.warning("place_order returned no valid id: %s", resp)

    async def _cancel_side(
        self,
        session:  aiohttp.ClientSession,
        s:        ContractOrders,
        contract: str,
        side:     str,
    ) -> None:
        """Cancel one side, update state."""
        from rest_client import cancel_order

        order_id = s.bid_order_id if side == "bid" else s.ask_order_id
        if order_id is None:
            return

        if side == "bid":
            s.bid_cancelling = True
        else:
            s.ask_cancelling = True

        ok = await cancel_order(session, order_id, contract)
        if ok or True:   # always clear state regardless
            if side == "bid":
                s.bid_order_id  = None
                s.bid_price     = None
                s.bid_size      = 0
                s.bid_cancelling = False
            else:
                s.ask_order_id  = None
                s.ask_price     = None
                s.ask_size      = 0
                s.ask_cancelling = False

            log.debug("Cleared %s order id=%s for %s", side, order_id, contract)

    # ─── WS fill reconciliation ───────────────────────────────────────────────

    def on_order_update(self, event: Dict[str, Any]) -> None:
        """
        Handle futures.orders WS event.

        Status transitions:
          open       → order live
          finished   → filled or cancelled
          partial    → partial fill (size changed)
        """
        for item in (event if isinstance(event, list) else [event]):
            contract = item.get("contract", "")
            order_id = int(item.get("id", 0))
            status   = item.get("status", "")
            left     = int(item.get("left", 0))      # remaining size
            size     = int(item.get("size", 0))       # original size
            fill_price = item.get("fill_price")

            s = self._state.get(contract)
            if s is None:
                continue

            if status == "finished":
                # Determine which side filled.
                if s.bid_order_id == order_id:
                    filled_size = s.bid_size - left
                    if filled_size > 0 and fill_price:
                        self._record_fill(
                            contract, +filled_size,
                            Decimal(str(fill_price)),
                            item.get("fee", "0"),
                        )
                    s.bid_order_id  = None
                    s.bid_price     = None
                    s.bid_size      = 0
                    s.bid_placed_ts = 0.0

                elif s.ask_order_id == order_id:
                    filled_size = s.ask_size - left
                    if filled_size > 0 and fill_price:
                        self._record_fill(
                            contract, -filled_size,
                            Decimal(str(fill_price)),
                            item.get("fee", "0"),
                        )
                    s.ask_order_id  = None
                    s.ask_price     = None
                    s.ask_size      = 0
                    s.ask_placed_ts = 0.0

    def _record_fill(
        self,
        contract:   str,
        size:       int,
        price:      Decimal,
        fee_str:    Any,
    ) -> None:
        fill = Fill(
            contract=contract,
            size=size,
            price=price,
            fee=Decimal(str(fee_str)),
            ts_ms=int(time.time() * 1000),
        )
        risk.on_fill(fill)

    # ─── Cleanup ─────────────────────────────────────────────────────────────

    async def cancel_all(self, session: aiohttp.ClientSession) -> None:
        """Emergency cancel all open orders across all contracts."""
        from rest_client import cancel_all_orders
        async with self._lock:
            for contract, s in self._state.items():
                if s.bid_order_id or s.ask_order_id:
                    n = await cancel_all_orders(session, contract)
                    log.info("Emergency cancel: %s → %d orders killed", contract, n)
                    s.bid_order_id = s.ask_order_id = None
                    s.bid_price = s.ask_price = None

    def live_order_count(self) -> int:
        count = 0
        for s in self._state.values():
            if s.bid_order_id:
                count += 1
            if s.ask_order_id:
                count += 1
        return count


# Module-level singleton.
oms = OMS()
