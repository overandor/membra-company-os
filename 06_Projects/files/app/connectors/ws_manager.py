"""
ws_manager.py — Dual WebSocket manager for Gate.io futures.

Public WS:  book_ticker (BBO updates) per contract.
Private WS: futures.orders (fill/cancel notifications), authenticated.

Both connections run as persistent async tasks with auto-reconnect.
All received messages are dispatched synchronously within the asyncio event loop.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp

from app.connectors.auth import ws_auth_message
from app.core.config import (
    FUTURES_WS_URL, MICRO_CONTRACTS, mm_config,
    API_KEY, API_SECRET,
)
from app.market_data.order_book import registry as ob_registry
from app.strategy.quoting_engine import signal_bbo_change
from app.oms.oms import oms

log = logging.getLogger("ws_manager")

_PING_INTERVAL_S = 25.0
_RECONNECT_DELAY_S = 2.0
_MAX_RECONNECT = 20


# ─── Message builders ────────────────────────────────────────────────────────

def _sub_msg(channel: str, payload: Any, request_id: int = 1) -> str:
    return json.dumps({
        "time":    int(time.time()),
        "id":      request_id,
        "channel": channel,
        "event":   "subscribe",
        "payload": payload,
    })


def _ping_msg() -> str:
    return json.dumps({
        "time":    int(time.time()),
        "channel": "futures.ping",
    })


def _auth_msg() -> str:
    msg = ws_auth_message(API_KEY, API_SECRET)
    return json.dumps(msg)


# ─── Public WebSocket ────────────────────────────────────────────────────────

class PublicWS:
    """
    Subscribes to futures.book_ticker for every micro-price contract.
    Dispatches BBO updates to OrderBookRegistry + QuotingEngine event bus.
    """

    def __init__(self):
        self._ws:      Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._running: bool = False
        self._reconnects: int = 0

    async def run(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._running = True

        while self._running and self._reconnects < _MAX_RECONNECT:
            try:
                await self._connect_and_consume()
            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError) as exc:
                self._reconnects += 1
                delay = min(_RECONNECT_DELAY_S * (2 ** self._reconnects), 60.0)
                log.warning(
                    "Public WS disconnected (%s). Reconnect %d in %.1fs",
                    exc, self._reconnects, delay,
                )
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break

        log.info("PublicWS exiting. Reconnects: %d", self._reconnects)

    async def _connect_and_consume(self) -> None:
        log.info("Public WS connecting: %s", FUTURES_WS_URL)
        async with self._session.ws_connect(
            FUTURES_WS_URL,
            heartbeat=_PING_INTERVAL_S,
            receive_timeout=60.0,
        ) as ws:
            self._ws = ws
            self._reconnects = 0
            log.info("Public WS connected")

            # Subscribe to book_ticker for each contract.
            for i, contract in enumerate(MICRO_CONTRACTS, start=1):
                if contract not in mm_config.contracts:
                    continue
                sub = _sub_msg("futures.book_ticker", [contract], request_id=i)
                await ws.send_str(sub)
                log.debug("Subscribed book_ticker: %s", contract)

            # Start ping coroutine.
            ping_task = asyncio.create_task(self._ping_loop(ws))

            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._dispatch(msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        log.warning("Public WS closed by server")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        log.error("Public WS error: %s", ws.exception())
                        break
            finally:
                ping_task.cancel()

    async def _ping_loop(self, ws) -> None:
        while not ws.closed:
            await asyncio.sleep(_PING_INTERVAL_S)
            if not ws.closed:
                await ws.send_str(_ping_msg())

    def _dispatch(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Public WS: failed to decode: %s", raw[:200])
            return

        channel = msg.get("channel", "")
        event   = msg.get("event", "")
        result  = msg.get("result")

        if channel == "futures.book_ticker" and event == "update" and result:
            contract = result.get("s", "")
            if contract:
                ob = ob_registry.get_or_create(contract)
                changed_bbo = ob.on_book_ticker(result)
                if changed_bbo:
                    signal_bbo_change(contract)


# ─── Private WebSocket ────────────────────────────────────────────────────────

class PrivateWS:
    """
    Authenticated Gate.io futures WebSocket.
    Subscribes to:
      • futures.orders      — order status updates (fill / cancel)
      • futures.usertrades  — individual trade confirmations
    """

    def __init__(self):
        self._ws:       Optional[aiohttp.ClientWebSocketResponse] = None
        self._session:  Optional[aiohttp.ClientSession] = None
        self._running:  bool = False
        self._authed:   bool = False
        self._reconnects: int = 0

    async def run(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._running = True

        while self._running and self._reconnects < _MAX_RECONNECT:
            try:
                await self._connect_and_consume()
            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError) as exc:
                self._reconnects += 1
                delay = min(_RECONNECT_DELAY_S * (2 ** self._reconnects), 60.0)
                log.warning(
                    "Private WS disconnected (%s). Reconnect %d in %.1fs",
                    exc, self._reconnects, delay,
                )
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break

        log.info("PrivateWS exiting. Reconnects: %d", self._reconnects)

    async def _connect_and_consume(self) -> None:
        log.info("Private WS connecting: %s", FUTURES_WS_URL)
        async with self._session.ws_connect(
            FUTURES_WS_URL,
            heartbeat=_PING_INTERVAL_S,
            receive_timeout=60.0,
        ) as ws:
            self._ws = ws
            self._authed = False
            self._reconnects = 0
            log.info("Private WS connected — authenticating")

            # Login frame.
            await ws.send_str(_auth_msg())

            ping_task = asyncio.create_task(self._ping_loop(ws))
            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._dispatch(ws, msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        log.warning("Private WS closed by server")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        log.error("Private WS error: %s", ws.exception())
                        break
            finally:
                ping_task.cancel()

    async def _ping_loop(self, ws) -> None:
        while not ws.closed:
            await asyncio.sleep(_PING_INTERVAL_S)
            if not ws.closed:
                await ws.send_str(_ping_msg())

    def _dispatch(self, ws, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Private WS: bad JSON: %s", raw[:200])
            return

        channel = msg.get("channel", "")
        event   = msg.get("event", "")
        result  = msg.get("result")
        header  = msg.get("header", {})

        # ── Login acknowledgement ─────────────────────────────────────────────
        if channel == "futures.login" and event == "api":
            status = header.get("status", "")
            if status == "200":
                log.info("Private WS authenticated successfully")
                self._authed = True
                # Schedule subscriptions after auth.
                asyncio.create_task(self._subscribe_private(ws))
            else:
                log.error("Private WS auth failed: %s", msg)
            return

        if not self._authed:
            return

        # ── Order updates ─────────────────────────────────────────────────────
        if channel == "futures.orders" and event == "update" and result:
            oms.on_order_update(result)

        # ── User trade confirmations ──────────────────────────────────────────
        elif channel == "futures.usertrades" and event == "update" and result:
            self._on_user_trade(result)

    async def _subscribe_private(self, ws) -> None:
        """Send subscriptions for all private channels after successful auth."""
        # Subscribe to orders and trades for all our contracts.
        contracts = [c for c in MICRO_CONTRACTS if c in mm_config.contracts]

        await ws.send_str(_sub_msg("futures.orders",     contracts, request_id=100))
        await ws.send_str(_sub_msg("futures.usertrades", contracts, request_id=101))
        log.info(
            "Private WS subscribed to orders+trades for %d contracts",
            len(contracts),
        )

    def _on_user_trade(self, result: Any) -> None:
        """
        futures.usertrades provides per-trade fill details with exact price/fee.
        Used as an authoritative reconciliation source alongside order updates.
        """
        trades = result if isinstance(result, list) else [result]
        for t in trades:
            log.info(
                "TRADE contract=%-20s  size=%+6d  price=%s  fee=%s  role=%s  id=%s",
                t.get("contract", "?"),
                int(t.get("size", 0)),
                t.get("price", "?"),
                t.get("fee", "?"),
                t.get("role", "?"),    # taker / maker
                t.get("id", "?"),
            )


# ─── WS Manager façade ───────────────────────────────────────────────────────

class WSManager:
    """Launches and supervises both WS connections."""

    def __init__(self, session: aiohttp.ClientSession):
        self._session   = session
        self._public    = PublicWS()
        self._private   = PrivateWS()
        self._tasks:    List[asyncio.Task] = []

    async def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._public.run(self._session),  name="ws-public"),
            asyncio.create_task(self._private.run(self._session), name="ws-private"),
        ]
        log.info("WSManager: both WebSocket connections launched")

    async def stop(self) -> None:
        self._public._running  = False
        self._private._running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        log.info("WSManager stopped")

    async def wait(self) -> None:
        await asyncio.gather(*self._tasks, return_exceptions=True)
