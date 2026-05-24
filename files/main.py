"""
main.py — DepthOS Micro-Price Market Maker — Entry Point.

Launch sequence:
  1.  Validate environment (API keys present).
  2.  Open aiohttp session.
  3.  REST bootstrap: fetch contract specs, verify account mode, load positions.
  4.  Start WebSocket manager (public book_ticker + private orders).
  5.  Start QuotingEngine (one coroutine per contract).
  6.  Run heartbeat loop (logs status, enforces daily reset).
  7.  On SIGINT/SIGTERM: graceful shutdown → cancel all orders.

Usage:
  GATE_API_KEY=xxx GATE_API_SECRET=yyy python main.py

Optionally set:
  DRY_RUN=1   → log orders but never send to exchange
  LOG_LEVEL=DEBUG
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import aiohttp

import config as cfg
from config import mm_config, MICRO_CONTRACTS
from rest_client import (
    fetch_contract_specs,
    fetch_account_mode,
    fetch_balance,
    fetch_position,
    cancel_all_orders,
)
from ws_manager import WSManager
from quoting_engine import QuotingEngine, engine as _engine_module
from risk import risk
from oms import oms
import quoting_engine  # to set engine singleton

# ─── Logging setup ───────────────────────────────────────────────────────────

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s.%(msecs)03d  %(levelname)-7s  %(name)-20s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("main")


# ─── Startup validation ───────────────────────────────────────────────────────

def _validate_env() -> None:
    missing = [k for k in ("GATE_API_KEY", "GATE_API_SECRET") if not os.environ.get(k)]
    if missing:
        log.critical("Missing required environment variables: %s", missing)
        sys.exit(1)

    if os.environ.get("DRY_RUN", "").strip() in ("1", "true", "yes"):
        mm_config.dry_run = True
        log.warning("⚠ DRY_RUN mode enabled — no orders will be sent")


# ─── Bootstrap ───────────────────────────────────────────────────────────────

async def _bootstrap(session: aiohttp.ClientSession) -> bool:
    """
    Fetch all exchange metadata needed before starting.
    Returns False if we cannot safely proceed (e.g. no valid contracts found).
    """
    log.info("=== BOOTSTRAP START ===")

    # Account mode (single/dual).
    mm_config.account_mode = await fetch_account_mode(session)

    # Balance check.
    balance = await fetch_balance(session)
    log.info("USDT Futures balance: %s", balance)
    if balance < Decimal("1.0"):
        log.warning("Balance %.4f USDT is very low — dry_run forced", balance)
        mm_config.dry_run = True

    # Contract specs.
    specs = await fetch_contract_specs(session, MICRO_CONTRACTS)
    if not specs:
        log.error("No valid micro-price contracts found. Check MICRO_CONTRACTS list.")
        return False
    mm_config.contracts = specs
    log.info("Loaded %d valid contracts: %s", len(specs), list(specs.keys()))

    # Seed risk engine with existing positions (crash recovery).
    for contract in specs:
        try:
            pos = await fetch_position(session, contract)
            if pos != 0:
                log.warning(
                    "Existing position %s: %+d contracts — seeding risk state",
                    contract, pos,
                )
                risk.state(contract).net_position = pos
        except Exception as exc:
            log.warning("Could not fetch position for %s: %s", contract, exc)

    log.info("=== BOOTSTRAP COMPLETE ===")
    return True


# ─── Heartbeat ────────────────────────────────────────────────────────────────

async def _heartbeat_loop() -> None:
    """
    Periodic status log + daily PnL reset at UTC midnight.
    """
    last_reset_day: Optional[int] = None

    while True:
        await asyncio.sleep(mm_config.heartbeat_interval_s)

        # Daily reset.
        now_utc = datetime.now(timezone.utc)
        today   = now_utc.date().toordinal()
        if last_reset_day is None:
            last_reset_day = today
        elif today > last_reset_day:
            last_reset_day = today
            risk.reset_daily()

        # Status dump.
        log.info(
            "HEARTBEAT  live_orders=%d  %s",
            oms.live_order_count(),
            datetime.now(timezone.utc).isoformat(),
        )
        log.info(risk.summary())


# ─── Graceful shutdown ────────────────────────────────────────────────────────

_shutdown_event: asyncio.Event = asyncio.Event()


def _register_signals() -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: _shutdown_event.set())


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    _validate_env()
    _register_signals()

    connector = aiohttp.TCPConnector(
        limit=50,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=15, connect=5),
    ) as session:

        # ── Bootstrap ─────────────────────────────────────────────────────────
        ok = await _bootstrap(session)
        if not ok:
            log.critical("Bootstrap failed — aborting")
            return

        # ── WebSocket manager ─────────────────────────────────────────────────
        ws_mgr = WSManager(session)

        # ── Quoting engine ────────────────────────────────────────────────────
        qe = QuotingEngine(session)
        quoting_engine.engine = qe   # expose as module-level singleton

        log.info("Starting WebSocket connections …")
        await ws_mgr.start()

        # Give public WS ~1 s to receive initial BBO snapshots.
        log.info("Waiting for initial BBO data …")
        await asyncio.sleep(1.5)

        log.info("Starting quoting engine …")
        await qe.start()

        # ── Heartbeat ─────────────────────────────────────────────────────────
        hb_task = asyncio.create_task(_heartbeat_loop(), name="heartbeat")

        log.info("=== MARKET MAKER RUNNING ===  (CTRL-C to stop)")

        # ── Wait for shutdown signal ──────────────────────────────────────────
        await _shutdown_event.wait()
        log.info("Shutdown signal received — stopping gracefully …")

        # ── Graceful teardown ─────────────────────────────────────────────────
        hb_task.cancel()

        await qe.stop()       # cancels all orders + stops quoting tasks
        await ws_mgr.stop()   # closes WS connections

        # Final risk summary.
        log.info("Final risk state:\n%s", risk.summary())
        log.info("=== SHUTDOWN COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
