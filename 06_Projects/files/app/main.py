"""
DepthOS - Production-candidate Gate.io market maker.

Launch sequence with safety flags:
  1. Validate safety flags (LIVE_TRADING, LIVE_TRADING_CONFIRM)
  2. Allow dry-run mode without API keys
  3. Open aiohttp session
  4. REST bootstrap
  5. Start WebSocket manager
  6. Start QuotingEngine
  7. Run heartbeat loop
  8. Graceful shutdown with cancel-all

Usage:
  # Dry-run mode (no API keys required)
  python -m depthos --mode dry-run --duration 60

  # Live mode (requires explicit confirmation)
  LIVE_TRADING=1 LIVE_TRADING_CONFIRM=I_UNDERSTAND_RISK python -m depthos
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import argparse
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import aiohttp

from app.core.config import (
    mm_config,
    MICRO_CONTRACTS,
    LIVE_TRADING,
    LIVE_TRADING_CONFIRM,
    API_KEY,
    API_SECRET,
)
from app.connectors.rest_client import (
    fetch_contract_specs,
    fetch_account_mode,
    fetch_balance,
    fetch_position,
    cancel_all_orders,
)
from app.connectors.ws_manager import WSManager
from app.strategy.quoting_engine import QuotingEngine
from app.risk.risk import risk
from app.oms.oms import oms
from app.reconcile.reconcile import get_reconciler
from app.persistence.sqlite import get_db

# ─── Logging setup ───────────────────────────────────────────────────────────

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s.%(msecs)03d  %(levelname)-7s  %(name)-20s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("main")


# ─── Safety validation ───────────────────────────────────────────────────────

def _validate_safety_flags() -> None:
    """Validate safety flags before allowing any operation."""
    if LIVE_TRADING and not LIVE_TRADING_CONFIRM:
        log.critical(
            "LIVE_TRADING=1 but LIVE_TRADING_CONFIRM not set to 'I_UNDERSTAND_RISK'. "
            "Refusing to start."
        )
        sys.exit(1)
    
    if LIVE_TRADING and LIVE_TRADING_CONFIRM:
        if not API_KEY or not API_SECRET:
            log.critical("LIVE_TRADING enabled but API keys not set. Refusing to start.")
            sys.exit(1)
        log.warning("⚠ LIVE TRADING MODE ENABLED - REAL ORDERS WILL BE SENT")
    
    # Set dry-run based on environment or mode
    if os.environ.get("DRY_RUN", "").strip() in ("1", "true", "yes"):
        mm_config.dry_run = True
        log.warning("⚠ DRY_RUN mode enabled via environment - no orders will be sent")


# ─── Bootstrap ───────────────────────────────────────────────────────────────

async def _bootstrap(session: aiohttp.ClientSession) -> bool:
    """
    Fetch all exchange metadata needed before starting.
    Returns False if we cannot safely proceed.
    """
    log.info("=== BOOTSTRAP START ===")

    # Account mode (single/dual).
    if not mm_config.dry_run:
        mm_config.account_mode = await fetch_account_mode(session)

    # Balance check (skip in dry-run).
    if not mm_config.dry_run:
        balance = await fetch_balance(session)
        log.info("USDT Futures balance: %s", balance)
        if balance < Decimal("1.0"):
            log.warning("Balance %.4f USDT is very low — dry_run forced", balance)
            mm_config.dry_run = True

    # Contract specs.
    if not mm_config.dry_run:
        specs = await fetch_contract_specs(session, MICRO_CONTRACTS)
    else:
        # In dry-run, use placeholder specs
        from app.core.config import ContractSpec
        specs = {
            contract: ContractSpec(
                name=contract,
                tick_size=Decimal("0.000001"),
                lot_size=1,
                quanto_multiplier=Decimal("0.01"),
            )
            for contract in MICRO_CONTRACTS
        }
    
    if not specs:
        log.error("No valid micro-price contracts found. Check MICRO_CONTRACTS list.")
        return False
    mm_config.contracts = specs
    log.info("Loaded %d valid contracts: %s", len(specs), list(specs.keys()))

    # Seed risk engine with existing positions (skip in dry-run).
    if not mm_config.dry_run:
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
    """Periodic status log + daily PnL reset at UTC midnight."""
    last_reset_day: Optional[int] = None

    while True:
        await asyncio.sleep(mm_config.heartbeat_interval_s)

        # Daily reset.
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date().toordinal()
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

async def main(mode: str = "dry-run", duration: Optional[int] = None) -> None:
    _validate_safety_flags()
    _register_signals()

    # Set mode
    if mode == "dry-run":
        mm_config.dry_run = True
        log.info("DRY-RUN MODE: No orders will be sent to exchange")
    elif mode == "live":
        if not (LIVE_TRADING and LIVE_TRADING_CONFIRM):
            log.critical("LIVE mode requires LIVE_TRADING=1 and LIVE_TRADING_CONFIRM=I_UNDERSTAND_RISK")
            sys.exit(1)
        mm_config.dry_run = False
        log.warning("LIVE MODE: Real orders will be sent")

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

        # ── WebSocket manager (skip in dry-run) ─────────────────────────────────
        if not mm_config.dry_run:
            ws_mgr = WSManager(session)
            log.info("Starting WebSocket connections …")
            await ws_mgr.start()

            # Give public WS ~1 s to receive initial BBO snapshots.
            log.info("Waiting for initial BBO data …")
            await asyncio.sleep(1.5)
        else:
            ws_mgr = None

        # ── Quoting engine ────────────────────────────────────────────────────
        qe = QuotingEngine(session)

        log.info("Starting quoting engine …")
        await qe.start()

        # ── Reconciliation engine ─────────────────────────────────────────────
        db = get_db()
        reconciler = get_reconciler(oms, risk, db, interval_seconds=30)
        
        if not mm_config.dry_run:
            log.info("Starting reconciliation engine …")
            await reconciler.start(session)
        else:
            log.info("Reconciliation engine disabled in dry-run mode")

        # ── Heartbeat ─────────────────────────────────────────────────────────
        hb_task = asyncio.create_task(_heartbeat_loop(), name="heartbeat")

        log.info("=== MARKET MAKER RUNNING === (CTRL-C to stop)")

        # ── Run for duration if specified ──────────────────────────────────────
        if duration:
            log.info("Running for %d seconds in %s mode", duration, mode)
            await asyncio.sleep(duration)
            _shutdown_event.set()
        else:
            # ── Wait for shutdown signal ──────────────────────────────────────────
            await _shutdown_event.wait()

        log.info("Shutdown signal received — stopping gracefully …")

        # ── Graceful teardown ─────────────────────────────────────────────────
        hb_task.cancel()

        await qe.stop()  # cancels all orders + stops quoting tasks

        if not mm_config.dry_run:
            await reconciler.stop()  # stop reconciliation loop

        if ws_mgr:
            await ws_mgr.stop()  # closes WS connections

        # Final risk summary.
        log.info("Final risk state:\n%s", risk.summary())
        log.info("=== SHUTDOWN COMPLETE ===")


def cli():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="DepthOS - Production-candidate Gate.io market maker")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Main trading command (default)
    trading_parser = subparsers.add_parser("trade", help="Run market maker")
    trading_parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="Operating mode (default: dry-run)"
    )
    trading_parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Run duration in seconds (default: run indefinitely until SIGINT)"
    )
    
    # L2 recording and replay
    record_parser = subparsers.add_parser("record-l2", help="Record L2 orderbook data")
    record_parser.add_argument("--symbols", nargs="+", required=True, help="Contract symbols")
    record_parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    record_parser.add_argument("--output-dir", default="data/l2", help="Output directory")
    record_parser.add_argument("--depth-levels", type=int, default=20, help="Orderbook depth")
    
    # 24h L2 capture
    capture_24h_parser = subparsers.add_parser("capture-24h", help="24h continuous L2 capture")
    capture_24h_parser.add_argument("--contracts", nargs="+", default=["SHIB_USDT", "PEPE_USDT", "FLOKI_USDT"], help="Contract symbols")
    capture_24h_parser.add_argument("--output-dir", default="data/l2_24h", help="Output directory")
    capture_24h_parser.add_argument("--depth-levels", type=int, default=20, help="Orderbook depth")
    capture_24h_parser.add_argument("--duration-hours", type=int, default=24, help="Duration in hours")
    
    # L2 replay
    replay_parser = subparsers.add_parser("replay-l2", help="Replay L2 data")
    replay_parser.add_argument("--input", required=True, help="Input file path")
    replay_parser.add_argument("--quote-spread-bps", type=float, default=10.0, help="Quote spread in bps")
    replay_parser.add_argument("--quote-size", type=int, default=1000, help="Quote size")
    replay_parser.add_argument("--enable-queue-model", action="store_true", help="Enable queue model")
    replay_parser.add_argument("--enable-fill-probability", action="store_true", help="Enable fill probability")
    replay_parser.add_argument("--enable-toxic-detection", action="store_true", help="Enable toxic detection")
    
    # Edge decomposition
    edge_parser = subparsers.add_parser("edge-decomp", help="Edge decomposition analysis")
    edge_parser.add_argument("--data-dir", required=True, help="L2 data directory")
    edge_parser.add_argument("--quote-spread-bps", type=float, default=10.0, help="Quote spread in bps")
    edge_parser.add_argument("--quote-size", type=int, default=1000, help="Quote size")
    
    replay_parser.add_argument(
        "--no-fill-probability",
        action="store_true",
        help="Disable fill probability model"
    )
    replay_parser.add_argument(
        "--no-toxic-detection",
        action="store_true",
        help="Disable toxic flow detection"
    )
    
    args = parser.parse_args()
    
    # If no command specified, default to trade command
    if args.command is None:
        parser.print_help()
        return
    
    if args.command == "trade":
        asyncio.run(main(mode=args.mode, duration=args.duration))
    elif args.command == "record-l2":
        from app.cli.l2_commands import record_gate_l2
        record_gate_l2(
            symbols=args.symbols,
            duration=args.duration,
            output_dir=args.output_dir,
            depth_levels=args.depth_levels,
        )
    elif args.command == "capture-24h":
        from app.cli.l2_capture_24h import capture_24h
        asyncio.run(capture_24h(
            contracts=args.contracts,
            output_dir=args.output_dir,
            depth_levels=args.depth_levels,
        ))
    elif args.command == "replay-l2":
        from app.cli.l2_commands import replay_l2
        replay_l2(
            input_path=args.input,
            quote_spread_bps=args.quote_spread_bps,
            quote_size=args.quote_size,
            enable_queue_model=args.enable_queue_model,
            enable_fill_probability=args.enable_fill_probability,
            enable_toxic_detection=args.enable_toxic_detection,
            no_fill_probability=args.no_fill_probability,
            no_toxic_detection=args.no_toxic_detection,
        )
    elif args.command == "edge-decomp":
        from app.backtest.edge_decomposition import EdgeDecomposition
        decomp = EdgeDecomposition()
        metrics = decomp.run_pipeline(
            data_dir=args.data_dir,
            quote_spread_bps=args.quote_spread_bps,
            quote_size=args.quote_size,
        )
        print("\n" + "=" * 60)
        print("EDGE DECOMPOSITION SUMMARY")
        print("=" * 60)
        for key, value in metrics.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v:.2f}")
            else:
                print(f"{key}: {value}")
        print("=" * 60)


if __name__ == "__main__":
    cli()
