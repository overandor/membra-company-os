# Оценка кода для Gate.io

#### You:
Appraise this code as is in russian in dollars #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_micro_perp_engine.py

Single-file Gate.io USDT perpetual futures engine that:
- scans the live Gate USDT perpetual contract universe
- computes minimum legal tradable nominal from live contract metadata
- filters contracts eligible for sub-$0.10 nominal exposure
- scores eligible contracts for microstructure "micro edge"
- supports dry mode, live mode, reconciliation, export, health, and CSV backtest replay
- uses SQLite persistence and CSV exports
- supports maker-first order logic with reduce-only exits
- includes a simple HTTP health endpoint and structured/human logs

INSTALL
-------
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install requests websocket-client

USAGE
-----
python gate_micro_perp_engine.py --scan
python gate_micro_perp_engine.py --dry
python gate_micro_perp_engine.py --live
python gate_micro_perp_engine.py --reconcile
python gate_micro_perp_engine.py --healthcheck
python gate_micro_perp_engine.py --export
python gate_micro_perp_engine.py --backtest data.csv

ENVIRONMENT
-----------
GATE_API_KEY=
GATE_API_SECRET=
GATE_SETTLE=usdt
GATE_API_BASE=https://api.gateio.ws/api/v4
GATE_WS_BASE=wss://fx-ws.gateio.ws/v4/ws/usdt
LIVE_TRADING=false
DRY_MODE=true
REQUIRE_LIVE_CONFIRMATION=false
ALLOW_TAKER_FALLBACK=false
MAX_SYMBOLS=6
TOP_N_SCAN=25
MAX_GROSS_EXPOSURE_USD=5
MAX_SYMBOL_EXPOSURE_USD=0.50
MAX_DAILY_LOSS_USD=1
EDGE_THRESHOLD=0.45
DEFAULT_LEVERAGE=3
SQLITE_PATH=gate_micro_perp_engine.sqlite3
CSV_DIR=exports
HTTP_PORT=8777
LOG_LEVEL=INFO
QUOTE_REFRESH_SEC=3
WS_STALE_SEC=15
SCAN_INTERVAL_SEC=60
HEARTBEAT_SEC=15
MAKER_MIN_REST_SEC=2
ORDER_COOLDOWN_SEC=5
MIN_24H_VOLUME_USD=10000
MAX_SPREAD_BPS=120
MAX_VOLATILITY_1M_BPS=500
REQUEST_TIMEOUT_SEC=15
REQUEST_RETRIES=4

RISK DISCLAIMER
---------------
This software is an execution and research engine, not a guarantee of profitability.
Perpetual futures trading is risky, can result in rapid losses, and may trigger liquidation.
Always validate endpoints, permissions, position modes, leverage rules, and contract specifications
in your own account before using live mode. Use dry mode first.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import logging
import math
import os
import queue
import random
import signal
import sqlite3
import statistics
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, InvalidOperation, getcontext
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

import requests
import websocket  # type: ignore

getcontext().prec = 28

APP_NAME = "gate_micro_perp_engine"
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1")
DECIMAL_10000 = Decimal("10000")
UTC = timezone.utc


def utc_ts() -> float:
    return time.time()


def utc_ms() -> int:
    return int(time.time() * 1000)


def utc_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def safe_decimal(value: Any, default: Decimal = DECIMAL_ZERO) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        if isinstance(value, bool):
            return default
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def dec_min(a: Decimal, b: Decimal) -> Decimal:
    return a if a <= b else b


def dec_max(a: Decimal, b: Decimal) -> Decimal:
    return a if a >= b else b


def quantize_down(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def quantize_half_up(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_HALF_UP) * step


def clamp_decimal(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    return dec_max(lo, dec_min(value, hi))


def now_date_str() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%d")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    try:
        return float(raw) if raw is not None else default
    except ValueError:
        return default


def env_decimal(name: str, default: str) -> Decimal:
    return safe_decimal(os.getenv(name), Decimal(default))


def jitter_sleep(base_seconds: float, jitter_frac: float = 0.2) -> None:
    delta = base_seconds * jitter_frac
    time.sleep(max(0.01, base_seconds + random.uniform(-delta, delta)))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    gate_api_key: str = field(default_factory=lambda: os.getenv("GATE_API_KEY", ""))
    gate_api_secret: str = field(default_factory=lambda: os.getenv("GATE_API_SECRET", ""))
    gate_settle: str = field(default_factory=lambda: os.getenv("GATE_SETTLE", "usdt").lower())
    gate_api_base: str = field(default_factory=lambda: os.getenv("GATE_API_BASE", "https://api.gateio.ws/api/v4").rstrip("/"))
    gate_ws_base: str = field(default_factory=lambda: os.getenv("GATE_WS_BASE", "wss://fx-ws.gateio.ws/v4/ws/usdt"))
    live_trading: bool = field(default_factory=lambda: env_bool("LIVE_TRADING", False))
    dry_mode: bool = field(default_factory=lambda: env_bool("DRY_MODE", True))
    require_live_confirmation: bool = field(default_factory=lambda: env_bool("REQUIRE_LIVE_CONFIRMATION", False))
    allow_taker_fallback: bool = field(default_factory=lambda: env_bool("ALLOW_TAKER_FALLBACK", False))
    max_symbols: int = field(default_factory=lambda: env_int("MAX_SYMBOLS", 6))
    top_n_scan: int = field(default_factory=lambda: env_int("TOP_N_SCAN", 25))
    max_gross_exposure_usd: Decimal = field(default_factory=lambda: env_decimal("MAX_GROSS_EXPOSURE_USD", "5"))
    max_symbol_exposure_usd: Decimal = field(default_factory=lambda: env_decimal("MAX_SYMBOL_EXPOSURE_USD", "0.50"))
    max_daily_loss_usd: Decimal = field(default_factory=lambda: env_decimal("MAX_DAILY_LOSS_USD", "1"))
    edge_threshold: Decimal = field(default_factory=lambda: env_decimal("EDGE_THRESHOLD", "0.45"))
    default_leverage: Decimal = field(default_factory=lambda: env_decimal("DEFAULT_LEVERAGE", "3"))
    sqlite_path: str = field(default_factory=lambda: os.getenv("SQLITE_PATH", "gate_micro_perp_engine.sqlite3"))
    csv_dir: str = field(default_factory=lambda: os.getenv("CSV_DIR", "exports"))
    http_port: int = field(default_factory=lambda: env_int("HTTP_PORT", 8777))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    quote_refresh_sec: float = field(default_factory=lambda: env_float("QUOTE_REFRESH_SEC", 3))
    ws_stale_sec: float = field(default_factory=lambda: env_float("WS_STALE_SEC", 15))
    scan_interval_sec: float = field(default_factory=lambda: env_float("SCAN_INTERVAL_SEC", 60))
    heartbeat_sec: float = field(default_factory=lambda: env_float("HEARTBEAT_SEC", 15))
    maker_min_rest_sec: float = field(default_factory=lambda: env_float("MAKER_MIN_REST_SEC", 2))
    order_cooldown_sec: float = field(default_factory=lambda: env_float("ORDER_COOLDOWN_SEC", 5))
    min_24h_volume_usd: Decimal = field(default_factory=lambda: env_decimal("MIN_24H_VOLUME_USD", "10000"))
    max_spread_bps: Decimal = field(default_factory=lambda: env_decimal("MAX_SPREAD_BPS", "120"))
    max_volatility_1m_bps: Decimal = field(default_factory=lambda: env_decimal("MAX_VOLATILITY_1M_BPS", "500"))
    request_timeout_sec: int = field(default_factory=lambda: env_int("REQUEST_TIMEOUT_SEC", 15))
    request_retries: int = field(default_factory=lambda: env_int("REQUEST_RETRIES", 4))
    contracts_page_limit: int = 1000

    def validate(self) -> None:
        if self.live_trading and self.dry_mode:
            raise ValueError("LIVE_TRADING=true and DRY_MODE=true is invalid; choose one.")
        if self.live_trading and self.require_live_confirmation:
            marker = os.getenv("LIVE_CONFIRMATION", "").strip().lower()
            if marker not in {"true", "yes", "confirmed"}:
                raise ValueError("Live trading confirmation missing. Set LIVE_CONFIRMATION=true.")
        if self.default_leverage <= 0:
            raise ValueError("DEFAULT_LEVERAGE must be > 0")
        if self.max_symbols <= 0:
            raise ValueError("MAX_SYMBOLS must be > 0")

    @property
    def csv_path(self) -> Path:
        return Path(self.csv_dir)

    @property
    def is_live(self) -> bool:
        return self.live_trading and not self.dry_mode

    @property
    def is_dry(self) -> bool:
        return not self.live_trading or self.dry_mode


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": utc_iso(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = getattr(record, "extra_data", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str) -> logging.Logger:
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.handlers.clear()

    human_handler = logging.StreamHandler(sys.stdout)
    human_handler.setLevel(getattr(logging, level, logging.INFO))
    human_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))

    json_handler = logging.StreamHandler(sys.stderr)
    json_handler.setLevel(getattr(logging, level, logging.INFO))
    json_handler.setFormatter(JsonFormatter())

    logger.addHandler(human_handler)
    logger.addHandler(json_handler)
    logger.propagate = False
    return logger


LOGGER = setup_logging(os.getenv("LOG_LEVEL", "INFO").upper())


def log_event(level: int, message: str, **kwargs: Any) -> None:
    LOGGER.log(level, message, extra={"extra_data": kwargs})


class SQLiteStore:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        schema = [
            """
            CREATE TABLE IF NOT EXISTS contracts (
                symbol TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scan_snapshots (
                scan_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                eligible INTEGER NOT NULL,
                min_nominal_usd TEXT,
                min_margin_estimate_usd TEXT,
                confidence_level TEXT,
                eligibility_reason TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS symbol_metrics (
                scan_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                micro_edge_score TEXT,
                spread_bps TEXT,
                book_imbalance TEXT,
                volatility_1m TEXT,
                volatility_5m TEXT,
                depth_score TEXT,
                liquidity_score TEXT,
                funding_penalty TEXT,
                slippage_estimate_bps TEXT,
                final_decision TEXT,
                rejection_reason TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                client_order_id TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price TEXT,
                size TEXT NOT NULL,
                tif TEXT,
                reduce_only INTEGER NOT NULL,
                is_live INTEGER NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS fills (
                fill_id TEXT PRIMARY KEY,
                order_id TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price TEXT NOT NULL,
                size TEXT NOT NULL,
                fee TEXT,
                is_live INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                side TEXT,
                size TEXT NOT NULL,
                entry_price TEXT,
                mark_price TEXT,
                unrealized_pnl TEXT,
                realized_pnl TEXT,
                leverage TEXT,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS pnl_events (
                event_id TEXT PRIMARY KEY,
                symbol TEXT,
                realized_pnl TEXT,
                unrealized_pnl TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS service_events (
                event_id TEXT PRIMARY KEY,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS config_kv (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS risk_events (
                event_id TEXT PRIMARY KEY,
                symbol TEXT,
                rule_name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS heartbeats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        ]
        with self._lock:
            cur = self._conn.cursor()
            for stmt in schema:
                cur.execute(stmt)
            self._conn.commit()

    def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(sql, params)
            self._conn.commit()
            return cur

    def fetchall(self, sql: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()

    def upsert_contract(self, symbol: str, payload: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO contracts(symbol, payload_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (symbol, json.dumps(payload, ensure_ascii=False), utc_iso()),
        )

    def insert_scan_snapshot(self, scan_id: str, symbol: str, eligible: bool, payload: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO scan_snapshots(scan_id, symbol, eligible, min_nominal_usd, min_margin_estimate_usd,
            confidence_level, eligibility_reason, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_id,
                symbol,
                1 if eligible else 0,
                str(payload.get("min_nominal_usd", "")),
                str(payload.get("min_margin_estimate_usd", "")),
                str(payload.get("confidence_level", "")),
                str(payload.get("eligibility_reason", "")),
                json.dumps(payload, ensure_ascii=False),
                utc_iso(),
            ),
        )

    def insert_symbol_metric(self, scan_id: str, symbol: str, payload: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO symbol_metrics(scan_id, symbol, micro_edge_score, spread_bps, book_imbalance,
            volatility_1m, volatility_5m, depth_score, liquidity_score, funding_penalty,
            slippage_estimate_bps, final_decision, rejection_reason, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_id,
                symbol,
                str(payload.get("micro_edge_score", "")),
                str(payload.get("spread_bps", "")),
                str(payload.get("book_imbalance", "")),
                str(payload.get("volatility_1m", "")),
                str(payload.get("volatility_5m", "")),
                str(payload.get("depth_score", "")),
                str(payload.get("liquidity_score", "")),
                str(payload.get("funding_penalty", "")),
                str(payload.get("slippage_estimate_bps", "")),
                str(payload.get("final_decision", "")),
                str(payload.get("rejection_reason", "")),
                json.dumps(payload, ensure_ascii=False),
                utc_iso(),
            ),
        )

    def upsert_order(self, order_id: str, payload: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO orders(order_id, client_order_id, symbol, side, price, size, tif, reduce_only,
            is_live, status, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id) DO UPDATE SET
                client_order_id=excluded.client_order_id,
                symbol=excluded.symbol,
                side=excluded.side,
                price=excluded.price,
                size=excluded.size,
                tif=excluded.tif,
                reduce_only=excluded.reduce_only,
                is_live=excluded.is_live,
                status=excluded.status,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                order_id,
                payload.get("client_order_id"),
                payload["symbol"],
                payload["side"],
                str(payload.get("price") or ""),
                str(payload.get("size") or ""),
                payload.get("tif") or "",
                1 if payload.get("reduce_only") else 0,
                1 if payload.get("is_live") else 0,
                payload.get("status", "unknown"),
                json.dumps(payload, ensure_ascii=False),
                payload.get("created_at", utc_iso()),
                utc_iso(),
            ),
        )

    def insert_fill(self, fill_id: str, payload: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO fills(fill_id, order_id, symbol, side, price, size, fee, is_live, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fill_id,
                payload.get("order_id"),
                payload["symbol"],
                payload["side"],
                str(payload["price"]),
                str(payload["size"]),
                str(payload.get("fee") or ""),
                1 if payload.get("is_live") else 0,
                json.dumps(payload, ensure_ascii=False),
                payload.get("created_at", utc_iso()),
            ),
        )

    def upsert_position(self, symbol: str, payload: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO positions(symbol, side, size, entry_price, mark_price, unrealized_pnl, realized_pnl,
            leverage, payload_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                side=excluded.side,
                size=excluded.size,
                entry_price=excluded.entry_price,
                mark_price=excluded.mark_price,
                unrealized_pnl=excluded.unrealized_pnl,
                realized_pnl=excluded.realized_pnl,
                leverage=excluded.leverage,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                symbol,
                payload.get("side"),
                str(payload.get("size") or "0"),
                str(payload.get("entry_price") or ""),
                str(payload.get("mark_price") or ""),
                str(payload.get("unrealized_pnl") or ""),
                str(payload.get("realized_pnl") or ""),
                str(payload.get("leverage") or ""),
                json.dumps(payload, ensure_ascii=False),
                utc_iso(),
            ),
        )

    def insert_pnl_event(self, event_id: str, payload: Dict[str, Any]) -> None:
        self.execute(
            """
            INSERT INTO pnl_events(event_id, symbol, realized_pnl, unrealized_pnl, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                payload.get("symbol"),
                str(payload.get("realized_pnl") or ""),
                str(payload.get("unrealized_pnl") or ""),
                json.dumps(payload, ensure_ascii=False),
                utc_iso(),
            ),
        )

    def insert_service_event(self, level: str, category: str, message: str, payload: Dict[str, Any]) -> None:
        event_id = f"{utc_ms()}_{random.randint(1000, 9999)}"
        self.execute(
            """
            INSERT INTO service_events(event_id, level, category, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, level, category, message, json.dumps(payload, ensure_ascii=False), utc_iso()),
        )

    def set_config(self, key: str, value: str) -> None:
        self.execute(
            """
            INSERT INTO config_kv(k, v, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(k) DO UPDATE SET
                v=excluded.v,
                updated_at=excluded.updated_at
            """,
            (key, value, utc_iso()),
        )

    def get_config(self, key: str) -> Optional[str]:
        rows = self.fetchall("SELECT v FROM config_kv WHERE k = ?", (key,))
        return rows[0]["v"] if rows else None

    def insert_risk_event(self, rule_name: str, payload: Dict[str, Any], symbol: Optional[str] = None) -> None:
        event_id = f"{utc_ms()}_{random.randint(1000, 9999)}"
        self.execute(
            """
            INSERT INTO risk_events(event_id, symbol, rule_name, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, symbol, rule_name, json.dumps(payload, ensure_ascii=False), utc_iso()),
        )

    def insert_heartbeat(self, state: Dict[str, Any]) -> None:
        self.execute(
            "INSERT INTO heartbeats(state_json, created_at) VALUES (?, ?)",
            (json.dumps(state, ensure_ascii=False), utc_iso()),
        )

    def recent_realized_pnl_today(self) -> Decimal:
        rows = self.fetchall(
            """
            SELECT realized_pnl FROM pnl_events
            WHERE substr(created_at, 1, 10) = ?
            """,
            (now_date_str(),),
        )
        total = DECIMAL_ZERO
        for row in rows:
            total += safe_decimal(row["realized_pnl"])
        return total

    def open_positions(self) -> List[Dict[str, Any]]:
        rows = self.fetchall("SELECT * FROM positions")
        return [dict(r) for r in rows]

    def open_orders(self) -> List[Dict[str, Any]]:
        rows = self.fetchall("SELECT * FROM orders WHERE status IN ('open', 'pending', 'new')")
        return [dict(r) for r in rows]


class CSVExporter:
    def __init__(self, csv_dir: Path):
        self.csv_dir = csv_dir
        ensure_dir(self.csv_dir)
        self._lock = threading.RLock()

    def _write(self, filename: str, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
        path = self.csv_dir / filename
        with self._lock:
            if not rows and fieldnames is None:
                return
            if fieldnames is None:
                keys: List[str] = []
                seen = set()
                for row in rows:
                    for k in row.keys():
                        if k not in seen:
                            seen.add(k)
                            keys.append(k)
                fieldnames = keys
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: row.get(k) for k in fieldnames})

    def write_eligible_contracts(self, rows: List[Dict[str, Any]]) -> None:
        self._write("eligible_contracts.csv", rows)

    def write_ranked_contracts(self, rows: List[Dict[str, Any]]) -> None:
        self._write("ranked_contracts.csv", rows)

    def append_row(self, filename: str, row: Dict[str, Any]) -> None:
        path = self.csv_dir / filename
        with self._lock:
            file_exists = path.exists()
            with path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)


class GateApiSigner:
    @staticmethod
    def sign(secret: str, method: str, path: str, query_string: str, body: str, timestamp: str) -> str:
        body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
        sign_payload = "\n".join([method.upper(), path, query_string, body_hash, timestamp])
        return hmac.new(secret.encode("utf-8"), sign_payload.encode("utf-8"), hashlib.sha512).hexdigest()


class GateHttpClient:
    def __init__(self, cfg: Config, store: SQLiteStore):
        self.cfg = cfg
        self.store = store
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
        self._error_streak = 0
        self._lock = threading.RLock()

    def _headers(self, method: str, path: str, query: Dict[str, Any], body: Optional[Dict[str, Any]], auth: bool, decimal_size: bool = True) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/json", "Content-Type": "application/json"}
        if decimal_size:
            headers["X-Gate-Size-Decimal"] = "1"
        if not auth:
            return headers
        timestamp = str(int(time.time()))
        query_string = urlencode({k: v for k, v in query.items() if v is not None}, doseq=True)
        body_text = json.dumps(body or {}, separators=(",", ":"), ensure_ascii=False) if body else ""
        headers["KEY"] = self.cfg.gate_api_key
        headers["Timestamp"] = timestamp
        headers["SIGN"] = GateApiSigner.sign(self.cfg.gate_api_secret, method, path, query_string, body_text, timestamp)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        auth: bool = False,
        decimal_size: bool = True,
    ) -> Any:
        query = query or {}
        url = f"{self.cfg.gate_api_base}{path}"
        body_text = json.dumps(body or {}, separators=(",", ":"), ensure_ascii=False) if body else None
        headers = self._headers(method, path, query, body, auth, decimal_size=decimal_size)

        for attempt in range(1, self.cfg.request_retries + 1):
            try:
                resp = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=query,
                    data=body_text,
                    headers=headers,
                    timeout=self.cfg.request_timeout_sec,
                )
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"transient_http_{resp.status_code}", response=resp)
                resp.raise_for_status()
                self._error_streak = 0
                if not resp.text.strip():
                    return None
                return resp.json()
            except Exception as exc:
                self._error_streak += 1
                if attempt >= self.cfg.request_retries:
                    self.store.insert_service_event(
                        "ERROR",
                        "http",
                        "request_failed",
                        {
                            "method": method,
                            "path": path,
                            "query": query,
                            "body": body,
                            "error": repr(exc),
                            "attempt": attempt,
                        },
                    )
                    raise
                sleep_s = min(8.0, 0.5 * (2 ** (attempt - 1)))
                log_event(logging.WARNING, "HTTP retry", method=method, path=path, attempt=attempt, error=repr(exc))
                jitter_sleep(sleep_s)

    @property
    def error_streak(self) -> int:
        return self._error_streak

    def list_contracts(self, settle: str) -> List[Dict[str, Any]]:
        path = f"/futures/{settle}/contracts"
        contracts = self.request("GET", path, auth=False, decimal_size=True)
        if not isinstance(contracts, list):
            raise ValueError("Unexpected contracts response")
        return contracts

    def ticker(self, settle: str, contract: str) -> Dict[str, Any]:
        return self.request("GET", f"/futures/{settle}/tickers", query={"contract": contract}, auth=False)

    def order_book(self, settle: str, contract: str, interval: str = "0", limit: int = 20, with_id: bool = True) -> Dict[str, Any]:
        return self.request(
            "GET",
            f"/futures/{settle}/order_book",
            query={"contract": contract, "interval": interval, "limit": limit, "with_id": str(with_id).lower()},
            auth=False,
        )

    def candlesticks(self, settle: str, contract: str, interval: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
        return self.request(
            "GET",
            f"/futures/{settle}/candlesticks",
            query={"contract": contract, "interval": interval, "limit": limit},
            auth=False,
        )

    def futures_trades(self, settle: str, contract: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.request(
            "GET",
            f"/futures/{settle}/trades",
            query={"contract": contract, "limit": limit},
            auth=False,
        )

    def create_order(self, settle: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("POST", f"/futures/{settle}/orders", body=payload, auth=True)

    def cancel_order(self, settle: str, order_id: str) -> Any:
        return self.request("DELETE", f"/futures/{settle}/orders/{order_id}", auth=True)

    def amend_order(self, settle: str, order_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("PUT", f"/futures/{settle}/orders/{order_id}", body=payload, auth=True)

    def list_open_orders(self, settle: str, contract: Optional[str] = None, status: str = "open") -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"status": status}
        if contract:
            query["contract"] = contract
        resp = self.request("GET", f"/futures/{settle}/orders", query=query, auth=True)
        return resp if isinstance(resp, list) else []

    def list_positions(self, settle: str) -> List[Dict[str, Any]]:
        resp = self.request("GET", f"/futures/{settle}/positions", auth=True)
        return resp if isinstance(resp, list) else []

    def set_position_leverage(self, settle: str, contract: str, leverage: Decimal) -> Dict[str, Any]:
        payload = {"leverage": str(leverage)}
        return self.request("POST", f"/futures/{settle}/positions/{contract}/leverage", body=payload, auth=True)

    def my_account(self, settle: str) -> Dict[str, Any]:
        return self.request("GET", f"/futures/{settle}/accounts", auth=True)


@dataclass
class ContractSpec:
    symbol: str
    quanto_multiplier: Decimal
    order_size_min: Decimal
    order_size_max: Decimal
    last_price: Decimal
    mark_price: Decimal
    index_price: Decimal
    leverage_min: Decimal
    leverage_max: Decimal
    order_price_round: Decimal
    mark_price_round: Decimal
    funding_rate: Decimal
    volume_24h_usd: Decimal
    volume_24h_contracts: Decimal
    in_delisting: bool
    enabled: bool
    raw: Dict[str, Any]
    size_decimal_supported: bool = True

    @classmethod
    def from_api(cls, payload: Dict[str, Any]) -> "ContractSpec":
        symbol = str(payload.get("name") or payload.get("contract") or "")
        price_round = safe_decimal(payload.get("order_price_round") or payload.get("price_tick") or payload.get("order_price_deviate"))
        mark_round = safe_decimal(payload.get("mark_price_round") or payload.get("mark_price_tick") or payload.get("order_price_round"))
        volume_24h_usd = safe_decimal(
            payload.get("volume_24h_quote")
            or payload.get("turnover_24h")
            or payload.get("volume_24h_usd")
            or payload.get("volume_24h")
        )
        volume_24h_contracts = safe_decimal(payload.get("volume_24h_base") or payload.get("volume_24h_contracts") or payload.get("volume_24h"))
        enabled = True
        if str(payload.get("status", "")).lower() in {"offline", "paused", "disable", "disabled"}:
            enabled = False
        if str(payload.get("trading_disabled", "")).lower() in {"true", "1"}:
            enabled = False
        return cls(
            symbol=symbol,
            quanto_multiplier=safe_decimal(payload.get("quanto_multiplier")),
            order_size_min=safe_decimal(payload.get("order_size_min") or payload.get("trade_size_min") or "1"),
            order_size_max=safe_decimal(payload.get("order_size_max") or payload.get("trade_size_max") or "0"),
            last_price=safe_decimal(payload.get("last_price") or payload.get("last")),
            mark_price=safe_decimal(payload.get("mark_price")),
            index_price=safe_decimal(payload.get("index_price")),
            leverage_min=safe_decimal(payload.get("leverage_min") or "1"),
            leverage_max=safe_decimal(payload.get("leverage_max") or "1"),
            order_price_round=price_round if price_round > 0 else Decimal("0.00000001"),
            mark_price_round=mark_round if mark_round > 0 else Decimal("0.00000001"),
            funding_rate=safe_decimal(payload.get("funding_rate") or payload.get("funding_rate_indicative")),
            volume_24h_usd=volume_24h_usd,
            volume_24h_contracts=volume_24h_contracts,
            in_delisting=bool(payload.get("in_delisting") or payload.get("delisting")),
            enabled=enabled,
            raw=payload,
            size_decimal_supported=True,
        )

    def reference_price(self) -> Decimal:
        for candidate in (self.mark_price, self.last_price, self.index_price):
            if candidate > 0:
                return candidate
        return DECIMAL_ZERO


@dataclass
class EligibilityResult:
    symbol: str
    eligible: bool
    min_nominal_usd: Decimal
    min_margin_estimate_usd: Decimal
    confidence_level: str
    eligibility_reason: str
    price_used: Decimal
    formula_variant: str
    raw: Dict[str, Any]


class EligibilityCalculator:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def evaluate(self, spec: ContractSpec) -> EligibilityResult:
        px = spec.reference_price()
        confidence = "high"
        reasons: List[str] = []

        if spec.symbol.endswith("_USD"):
            confidence = "low"
            reasons.append("inverse_contract_detected")
        if px <= 0:
            confidence = "low"
            reasons.append("missing_reference_price")
        if spec.quanto_multiplier <= 0:
            confidence = "low"
            reasons.append("missing_quanto_multiplier")
        if spec.order_size_min <= 0:
            confidence = "low"
            reasons.append("missing_order_size_min")

        formula_variant = "linear_usdt"
        if spec.symbol.endswith("_USD"):
            formula_variant = "inverse_conservative"

        if formula_variant == "linear_usdt":
            min_nominal = px * spec.quanto_multiplier * spec.order_size_min
        else:
            # conservative approximation for inverse-like edge cases
            # keep exposure estimate from amount * contract size / price in settlement terms,
            # but bound upward using notional-like approximation to avoid understating.
            approx_a = spec.order_size_min / dec_max(px, Decimal("0.00000001"))
            approx_b = px * dec_max(spec.quanto_multiplier, Decimal("1")) * spec.order_size_min
            min_nominal = dec_max(approx_a, approx_b)

        leverage = clamp_decimal(self.cfg.default_leverage, Decimal("1"), dec_max(spec.leverage_max, Decimal("1")))
        min_margin = min_nominal / dec_max(leverage, Decimal("1"))

        eligible = (
            spec.enabled
            and not spec.in_delisting
            and min_nominal > 0
            and min_nominal <= Decimal("0.10")
        )

        if not spec.enabled:
            reasons.append("contract_disabled")
        if spec.in_delisting:
            reasons.append("contract_delisting")
        if min_nominal > Decimal("0.10"):
            reasons.append("min_nominal_above_threshold")
        if spec.volume_24h_usd > 0 and spec.volume_24h_usd < self.cfg.min_24h_volume_usd:
            reasons.append("low_24h_volume")
            eligible = False
        elif spec.volume_24h_usd <= 0:
            reasons.append("missing_24h_volume")
            confidence = "medium" if confidence == "high" else confidence

        if not reasons:
            reasons.append("eligible_under_threshold")

        return EligibilityResult(
            symbol=spec.symbol,
            eligible=eligible,
            min_nominal_usd=min_nominal,
            min_margin_estimate_usd=min_margin,
            confidence_level=confidence,
            eligibility_reason=";".join(reasons),
            price_used=px,
            formula_variant=formula_variant,
            raw={
                "symbol": spec.symbol,
                "min_nominal_usd": str(min_nominal),
                "min_margin_estimate_usd": str(min_margin),
                "confidence_level": confidence,
                "eligibility_reason": ";".join(reasons),
                "price_used": str(px),
                "formula_variant": formula_variant,
                "quanto_multiplier": str(spec.quanto_multiplier),
                "order_size_min": str(spec.order_size_min),
                "volume_24h_usd": str(spec.volume_24h_usd),
            },
        )


@dataclass
class BookSnapshot:
    symbol: str
    ts: float
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    bids: List[Tuple[Decimal, Decimal]] = field(default_factory=list)
    asks: List[Tuple[Decimal, Decimal]] = field(default_factory=list)

    @property
    def mid(self) -> Decimal:
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / Decimal("2")
        return DECIMAL_ZERO

    @property
    def spread(self) -> Decimal:
        if self.ask > 0 and self.bid > 0:
            return self.ask - self.bid
        return DECIMAL_ZERO

    @property
    def spread_bps(self) -> Decimal:
        mid = self.mid
        if mid <= 0:
            return Decimal("999999")
        return (self.spread / mid) * DECIMAL_10000

    @property
    def imbalance(self) -> Decimal:
        denom = self.bid_size + self.ask_size
        if denom <= 0:
            return DECIMAL_ZERO
        return (self.bid_size - self.ask_size) / denom


class MarketState:
    def __init__(self):
        self.books: Dict[str, BookSnapshot] = {}
        self.last_ws_update: Dict[str, float] = {}
        self.mid_history: Dict[str, Deque[Tuple[float, Decimal]]] = defaultdict(lambda: deque(maxlen=600))
        self.trade_flow: Dict[str, Deque[Tuple[float, Decimal, str, Decimal]]] = defaultdict(lambda: deque(maxlen=500))
        self._lock = threading.RLock()

    def update_book(self, snap: BookSnapshot) -> None:
        with self._lock:
            self.books[snap.symbol] = snap
            self.last_ws_update[snap.symbol] = snap.ts
            if snap.mid > 0:
                self.mid_history[snap.symbol].append((snap.ts, snap.mid))

    def update_trade(self, symbol: str, price: Decimal, size: Decimal, side: str, ts: float) -> None:
        with self._lock:
            self.trade_flow[symbol].append((ts, price, side, size))

    def get_book(self, symbol: str) -> Optional[BookSnapshot]:
        with self._lock:
            return self.books.get(symbol)

    def get_mid_series(self, symbol: str, lookback_sec: float) -> List[Decimal]:
        cutoff = utc_ts() - lookback_sec
        with self._lock:
            return [px for ts, px in self.mid_history[symbol] if ts >= cutoff and px > 0]

    def get_trade_flow(self, symbol: str, lookback_sec: float) -> List[Tuple[float, Decimal, str, Decimal]]:
        cutoff = utc_ts() - lookback_sec
        with self._lock:
            return [x for x in self.trade_flow[symbol] if x[0] >= cutoff]

    def ws_stale(self, symbol: str, threshold_sec: float) -> bool:
        with self._lock:
            ts = self.last_ws_update.get(symbol, 0.0)
        return utc_ts() - ts > threshold_sec


class GateWsClient:
    def __init__(self, cfg: Config, market: MarketState, store: SQLiteStore):
        self.cfg = cfg
        self.market = market
        self.store = store
        self.ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._subs_lock = threading.RLock()
        self._subscribed_symbols: set[str] = set()
        self._connected = threading.Event()

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="gate_ws", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def subscribe(self, symbols: Iterable[str]) -> None:
        with self._subs_lock:
            changed = False
            for s in symbols:
                if s not in self._subscribed_symbols:
                    self._subscribed_symbols.add(s)
                    changed = True
            if changed and self._connected.is_set() and self.ws:
                self._send_subscriptions()

    def _run(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            try:
                self.ws = websocket.WebSocketApp(
                    self.cfg.gate_ws_base,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.ws.run_forever(ping_interval=15, ping_timeout=10)
            except Exception as exc:
                log_event(logging.ERROR, "WS fatal", error=repr(exc))
                self.store.insert_service_event("ERROR", "ws", "ws_fatal", {"error": repr(exc)})
            if self._stop.is_set():
                break
            jitter_sleep(backoff)
            backoff = min(20.0, backoff * 1.8)

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        self._connected.set()
        self._send_subscriptions()
        log_event(logging.INFO, "WS connected", url=self.cfg.gate_ws_base)

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: Any, close_msg: Any) -> None:
        self._connected.clear()
        log_event(logging.WARNING, "WS closed", code=close_status_code, msg=str(close_msg))

    def _on_error(self, ws: websocket.WebSocketApp, error: Any) -> None:
        self._connected.clear()
        self.store.insert_service_event("ERROR", "ws", "ws_error", {"error": repr(error)})
        log_event(logging.ERROR, "WS error", error=repr(error))

    def _send(self, payload: Dict[str, Any]) -> None:
        if self.ws and self._connected.is_set():
            self.ws.send(json.dumps(payload, ensure_ascii=False))

    def _send_subscriptions(self) -> None:
        with self._subs_lock:
            symbols = list(self._subscribed_symbols)
        if not symbols:
            return
        channels = [
            "futures.order_book",
            "futures.trades",
            "futures.book_ticker",
        ]
        for channel in channels:
            payload = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": [self.cfg.gate_settle.upper(), symbols] if channel in {"futures.order_book", "futures.book_ticker", "futures.trades"} else symbols,
            }
            # Some Gate futures WS payloads use ["USDT", "BTC_USDT"] or ["USDT", ["BTC_USDT"...]].
            # Send one-by-one for compatibility.
            if channel in {"futures.order_book", "futures.book_ticker", "futures.trades"}:
                for s in symbols:
                    pl = {"time": int(time.time()), "channel": channel, "event": "subscribe", "payload": [self.cfg.gate_settle.upper(), s]}
                    self._send(pl)
            else:
                self._send(payload)

    def _parse_book_payload(self, channel: str, result: Any) -> None:
        if not isinstance(result, dict):
            return
        symbol = str(result.get("s") or result.get("contract") or result.get("c") or "")
        if not symbol:
            return

        if channel == "futures.book_ticker":
            bid = safe_decimal(result.get("b") or result.get("bid"))
            ask = safe_decimal(result.get("a") or result.get("ask"))
            bid_size = safe_decimal(result.get("B") or result.get("bid_size"))
            ask_size = safe_decimal(result.get("A") or result.get("ask_size"))
            snap = BookSnapshot(
                symbol=symbol,
                ts=utc_ts(),
                bid=bid,
                ask=ask,
                bid_size=bid_size,
                ask_size=ask_size,
                bids=[],
                asks=[],
            )
            self.market.update_book(snap)
            return

        bids_raw = result.get("bids") or []
        asks_raw = result.get("asks") or []
        bids: List[Tuple[Decimal, Decimal]] = []
        asks: List[Tuple[Decimal, Decimal]] = []

        for item in bids_raw[:10]:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                bids.append((safe_decimal(item[0]), safe_decimal(item[1])))
            elif isinstance(item, dict):
                bids.append((safe_decimal(item.get("p") or item.get("price")), safe_decimal(item.get("s") or item.get("size"))))
        for item in asks_raw[:10]:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                asks.append((safe_decimal(item[0]), safe_decimal(item[1])))
            elif isinstance(item, dict):
                asks.append((safe_decimal(item.get("p") or item.get("price")), safe_decimal(item.get("s") or item.get("size"))))

        bid = bids[0][0] if bids else safe_decimal(result.get("best_bid"))
        ask = asks[0][0] if asks else safe_decimal(result.get("best_ask"))
        bid_size = bids[0][1] if bids else safe_decimal(result.get("best_bid_size"))
        ask_size = asks[0][1] if asks else safe_decimal(result.get("best_ask_size"))
        snap = BookSnapshot(symbol=symbol, ts=utc_ts(), bid=bid, ask=ask, bid_size=bid_size, ask_size=ask_size, bids=bids, asks=asks)
        self.market.update_book(snap)

    def _parse_trade_payload(self, result: Any) -> None:
        if isinstance(result, list):
            for item in result:
                self._parse_trade_payload(item)
            return
        if not isinstance(result, dict):
            return
        symbol = str(result.get("contract") or result.get("s") or "")
        if not symbol:
            return
        price = safe_decimal(result.get("price") or result.get("p"))
        size = abs(safe_decimal(result.get("size") or result.get("s") or result.get("amount") or "0"))
        side_raw = str(result.get("side") or result.get("taker_side") or result.get("direction") or "")
        side = "buy" if side_raw.lower() in {"buy", "bid", "b"} else "sell"
        ts = float(result.get("create_time_ms") or result.get("t") or utc_ms()) / 1000.0
        self.market.update_trade(symbol, price, size, side, ts)

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
        except Exception:
            return
        channel = str(payload.get("channel") or "")
        event = str(payload.get("event") or "")
        result = payload.get("result")

        if event == "subscribe":
            return
        if channel in {"futures.order_book", "futures.book_ticker"}:
            self._parse_book_payload(channel, result)
        elif channel == "futures.trades":
            self._parse_trade_payload(result)


@dataclass
class SymbolMetrics:
    symbol: str
    min_nominal_usd: Decimal
    min_margin_estimate_usd: Decimal
    spread_bps: Decimal
    book_imbalance: Decimal
    volatility_1m: Decimal
    volatility_5m: Decimal
    depth_score: Decimal
    liquidity_score: Decimal
    funding_penalty: Decimal
    slippage_estimate_bps: Decimal
    cancel_replace_burden: Decimal
    microstructure_stability: Decimal
    adverse_selection_proxy: Decimal
    contract_quality_penalty: Decimal
    liquidity_persistence: Decimal
    price_jump_frequency: Decimal
    quote_resiliency: Decimal
    trade_flow_imbalance: Decimal
    micro_edge_score: Decimal
    reasons: List[str]
    final_decision: str
    rejection_reason: str

    def to_row(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "min_nominal_usd": str(self.min_nominal_usd),
            "min_margin_estimate_usd": str(self.min_margin_estimate_usd),
            "spread_bps": str(self.spread_bps),
            "book_imbalance": str(self.book_imbalance),
            "volatility_1m": str(self.volatility_1m),
            "volatility_5m": str(self.volatility_5m),
            "depth_score": str(self.depth_score),
            "liquidity_score": str(self.liquidity_score),
            "funding_penalty": str(self.funding_penalty),
            "slippage_estimate_bps": str(self.slippage_estimate_bps),
            "cancel_replace_burden": str(self.cancel_replace_burden),
            "microstructure_stability": str(self.microstructure_stability),
            "adverse_selection_proxy": str(self.adverse_selection_proxy),
            "contract_quality_penalty": str(self.contract_quality_penalty),
            "liquidity_persistence": str(self.liquidity_persistence),
            "price_jump_frequency": str(self.price_jump_frequency),
            "quote_resiliency": str(self.quote_resiliency),
            "trade_flow_imbalance": str(self.trade_flow_imbalance),
            "micro_edge_score": str(self.micro_edge_score),
            "reasons": "|".join(self.reasons),
            "final_decision": self.final_decision,
            "rejection_reason": self.rejection_reason,
        }


class EdgeScorer:
    def __init__(self, cfg: Config, market: MarketState):
        self.cfg = cfg
        self.market = market

    @staticmethod
    def _norm_positive(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
        if hi <= lo:
            return DECIMAL_ZERO
        x = (value - lo) / (hi - lo)
        return clamp_decimal(x, DECIMAL_ZERO, DECIMAL_ONE)

    @staticmethod
    def _norm_inverse(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
        if hi <= lo:
            return DECIMAL_ZERO
        x = DECIMAL_ONE - ((value - lo) / (hi - lo))
        return clamp_decimal(x, DECIMAL_ZERO, DECIMAL_ONE)

    def _realized_vol_bps(self, mids: List[Decimal]) -> Decimal:
        if len(mids) < 3:
            return DECIMAL_ZERO
        returns: List[float] = []
        for a, b in zip(mids[:-1], mids[1:]):
            if a > 0 and b > 0:
                r = float((b - a) / a)
                returns.append(r)
        if len(returns) < 2:
            return DECIMAL_ZERO
        stdev = statistics.pstdev(returns)
        return Decimal(str(abs(stdev) * 10000.0))

    def _price_jump_frequency(self, mids: List[Decimal]) -> Decimal:
        if len(mids) < 3:
            return DECIMAL_ZERO
        jumps = 0
        total = 0
        for a, b in zip(mids[:-1], mids[1:]):
            if a > 0:
                total += 1
                if abs((b - a) / a) > Decimal("0.001"):  # 10 bps jump threshold
                    jumps += 1
        if total == 0:
            return DECIMAL_ZERO
        return Decimal(jumps) / Decimal(total)

    def _trade_flow_imbalance(self, symbol: str) -> Decimal:
        flow = self.market.get_trade_flow(symbol, 60)
        buy = DECIMAL_ZERO
        sell = DECIMAL_ZERO
        for _, _, side, size in flow:
            if side == "buy":
                buy += size
            else:
                sell += size
        denom = buy + sell
        if denom <= 0:
            return DECIMAL_ZERO
        return (buy - sell) / denom

    def _depth_score(self, book: BookSnapshot) -> Decimal:
        total = DECIMAL_ZERO
        if book.bid_size > 0 and book.ask_size > 0:
            total = book.bid_size + book.ask_size
        if total <= 0:
            return DECIMAL_ZERO
        return clamp_decimal(total / Decimal("50000"), DECIMAL_ZERO, DECIMAL_ONE)

    def _slippage_estimate_bps(self, book: BookSnapshot, target_notional: Decimal) -> Decimal:
        mid = book.mid
        if mid <= 0:
            return Decimal("999999")
        side_depth = min(book.bid_size, book.ask_size)
        if side_depth <= 0:
            return Decimal("999999")
        depth_notional = side_depth * mid
        ratio = target_notional / dec_max(depth_notional, Decimal("0.00000001"))
        base = book.spread_bps / Decimal("2")
        return dec_max(base, ratio * Decimal("25"))

    def _liquidity_persistence(self, symbol: str) -> Decimal:
        mids = self.market.get_mid_series(symbol, 300)
        if len(mids) < 20:
            return Decimal("0.2")
        distinct = len({str(m) for m in mids})
        ratio = Decimal(distinct) / Decimal(len(mids))
        return clamp_decimal(Decimal("1") - ratio, DECIMAL_ZERO, DECIMAL_ONE)

    def _quote_resiliency(self, symbol: str) -> Decimal:
        mids = self.market.get_mid_series(symbol, 60)
        if len(mids) < 5:
            return Decimal("0.3")
        changes = 0
        reversals = 0
        prev_sign: Optional[int] = None
        for a, b in zip(mids[:-1], mids[1:]):
            diff = b - a
            sign = 0 if diff == 0 else (1 if diff > 0 else -1)
            if sign != 0:
                changes += 1
                if prev_sign is not None and sign != prev_sign:
                    reversals += 1
                prev_sign = sign
        if changes == 0:
            return Decimal("0.5")
        return clamp_decimal(Decimal(reversals) / Decimal(changes), DECIMAL_ZERO, DECIMAL_ONE)

    def score(self, spec: ContractSpec, elig: EligibilityResult) -> SymbolMetrics:
        book = self.market.get_book(spec.symbol)
        if not book:
            spread_bps = Decimal("999999")
            imbalance = DECIMAL_ZERO
            depth_score = DECIMAL_ZERO
            slippage_est = Decimal("999999")
        else:
            spread_bps = book.spread_bps
            imbalance = book.imbalance
            depth_score = self._depth_score(book)
            slippage_est = self._slippage_estimate_bps(book, target_notional=Decimal("0.10"))

        mids_1m = self.market.get_mid_series(spec.symbol, 60)
        mids_5m = self.market.get_mid_series(spec.symbol, 300)
        vol_1m = self._realized_vol_bps(mids_1m)
        vol_5m = self._realized_vol_bps(mids_5m)
        jump_freq = self._price_jump_frequency(mids_1m)
        trade_flow_imb = self._trade_flow_imbalance(spec.symbol)
        liquidity_persistence = self._liquidity_persistence(spec.symbol)
        quote_resiliency = self._quote_resiliency(spec.symbol)

        volume_score = self._norm_positive(spec.volume_24h_usd, Decimal("10000"), Decimal("5000000"))
        spread_score = self._norm_inverse(spread_bps, Decimal("2"), self.cfg.max_spread_bps)
        vol_score = self._norm_inverse(vol_1m, Decimal("0"), self.cfg.max_volatility_1m_bps)
        imbalance_score = clamp_decimal((imbalance + Decimal("1")) / Decimal("2"), DECIMAL_ZERO, DECIMAL_ONE)
        flow_score = clamp_decimal((trade_flow_imb + Decimal("1")) / Decimal("2"), DECIMAL_ZERO, DECIMAL_ONE)
        funding_penalty = clamp_decimal(abs(spec.funding_rate) / Decimal("0.01"), DECIMAL_ZERO, DECIMAL_ONE)
        adverse_selection_proxy = clamp_decimal((jump_freq + (vol_1m / Decimal("1000"))) / Decimal("2"), DECIMAL_ZERO, DECIMAL_ONE)
        contract_quality_penalty = Decimal("0")
        if elig.confidence_level == "medium":
            contract_quality_penalty += Decimal("0.15")
        elif elig.confidence_level == "low":
            contract_quality_penalty += Decimal("0.35")
        if spec.order_size_min <= 0:
            contract_quality_penalty += Decimal("0.5")
        if spec.in_delisting:
            contract_quality_penalty += Decimal("1")

        cancel_replace_burden = clamp_decimal(spread_bps / Decimal("100"), DECIMAL_ZERO, DECIMAL_ONE)
        microstructure_stability = clamp_decimal((liquidity_persistence + (Decimal("1") - jump_freq)) / Decimal("2"), DECIMAL_ZERO, DECIMAL_ONE)
        liquidity_score = clamp_decimal((volume_score + depth_score) / Decimal("2"), DECIMAL_ZERO, DECIMAL_ONE)

        score = (
            spread_score * Decimal("0.18")
            + depth_score * Decimal("0.11")
            + imbalance_score * Decimal("0.06")
            + flow_score * Decimal("0.05")
            + vol_score * Decimal("0.10")
            + liquidity_score * Decimal("0.15")
            + liquidity_persistence * Decimal("0.05")
            + quote_resiliency * Decimal("0.05")
            + microstructure_stability * Decimal("0.06")
            + self._norm_inverse(slippage_est, Decimal("0"), Decimal("30")) * Decimal("0.10")
            + self._norm_inverse(elig.min_nominal_usd, Decimal("0"), Decimal("0.10")) * Decimal("0.06")
            - funding_penalty * Decimal("0.05")
            - cancel_replace_burden * Decimal("0.02")
            - adverse_selection_proxy * Decimal("0.04")
            - contract_quality_penalty * Decimal("0.08")
        )

        score = clamp_decimal(score, DECIMAL_ZERO, DECIMAL_ONE)
        reasons: List[str] = []

        if spread_bps <= self.cfg.max_spread_bps:
            reasons.append("spread_ok")
        else:
            reasons.append("spread_wide")
        if vol_1m <= self.cfg.max_volatility_1m_bps:
            reasons.append("vol_ok")
        else:
            reasons.append("vol_hot")
        if liquidity_score >= Decimal("0.3"):
            reasons.append("liquidity_ok")
        else:
            reasons.append("liquidity_thin")
        if score >= self.cfg.edge_threshold:
            reasons.append("edge_above_threshold")

        final_decision = "selected"
        rejection_reason = ""
        if spread_bps > self.cfg.max_spread_bps:
            final_decision = "rejected"
            rejection_reason = "spread_blowout"
        elif vol_1m > self.cfg.max_volatility_1m_bps:
            final_decision = "rejected"
            rejection_reason = "volatility_spike"
        elif liquidity_score < Decimal("0.15"):
            final_decision = "rejected"
            rejection_reason = "insufficient_liquidity"
        elif score < self.cfg.edge_threshold:
            final_decision = "rejected"
            rejection_reason = "edge_below_threshold"

        return SymbolMetrics(
            symbol=spec.symbol,
            min_nominal_usd=elig.min_nominal_usd,
            min_margin_estimate_usd=elig.min_margin_estimate_usd,
            spread_bps=spread_bps,
            book_imbalance=imbalance,
            volatility_1m=vol_1m,
            volatility_5m=vol_5m,
            depth_score=depth_score,
            liquidity_score=liquidity_score,
            funding_penalty=funding_penalty,
            slippage_estimate_bps=slippage_est,
            cancel_replace_burden=cancel_replace_burden,
            microstructure_stability=microstructure_stability,
            adverse_selection_proxy=adverse_selection_proxy,
            contract_quality_penalty=contract_quality_penalty,
            liquidity_persistence=liquidity_persistence,
            price_jump_frequency=jump_freq,
            quote_resiliency=quote_resiliency,
            trade_flow_imbalance=trade_flow_imb,
            micro_edge_score=score,
            reasons=reasons,
            final_decision=final_decision,
            rejection_reason=rejection_reason,
        )


class ContractScanner:
    def __init__(self, cfg: Config, http: GateHttpClient, market: MarketState, store: SQLiteStore):
        self.cfg = cfg
        self.http = http
        self.market = market
        self.store = store
        self.eligibility = EligibilityCalculator(cfg)
        self.scorer = EdgeScorer(cfg, market)

    def scan_contracts(self) -> Tuple[str, Dict[str, ContractSpec], List[EligibilityResult], List[SymbolMetrics]]:
        scan_id = f"scan_{utc_ms()}"
        raw_contracts = self.http.list_contracts(self.cfg.gate_settle)

        specs: Dict[str, ContractSpec] = {}
        eligibles: List[EligibilityResult] = []
        metrics: List[SymbolMetrics] = []

        for payload in raw_contracts:
            try:
                spec = ContractSpec.from_api(payload)
                if not spec.symbol:
                    continue
                specs[spec.symbol] = spec
                self.store.upsert_contract(spec.symbol, payload)
                elig = self.eligibility.evaluate(spec)
                self.store.insert_scan_snapshot(scan_id, spec.symbol, elig.eligible, elig.raw)
                if elig.eligible:
                    eligibles.append(elig)
            except Exception as exc:
                self.store.insert_service_event("ERROR", "scanner", "contract_parse_error", {"payload": payload, "error": repr(exc)})

        # Subscribe eligible symbols and top volume candidates so that metrics can fill in from WS
        seed_symbols = sorted(
            specs.values(),
            key=lambda s: (s.volume_24h_usd, s.reference_price()),
            reverse=True,
        )[: max(100, self.cfg.top_n_scan * 4)]
        self.market.books  # touch
        return scan_id, specs, eligibles, metrics

    def score_eligible(self, scan_id: str, specs: Dict[str, ContractSpec], eligibles: List[EligibilityResult]) -> List[SymbolMetrics]:
        metrics: List[SymbolMetrics] = []
        for elig in eligibles:
            spec = specs[elig.symbol]
            metric = self.scorer.score(spec, elig)
            self.store.insert_symbol_metric(scan_id, elig.symbol, metric.to_row())
            metrics.append(metric)
        metrics.sort(key=lambda m: (m.final_decision == "selected", m.micro_edge_score), reverse=True)
        return metrics


class RiskEngine:
    def __init__(self, cfg: Config, store: SQLiteStore, market: MarketState, http: GateHttpClient):
        self.cfg = cfg
        self.store = store
        self.market = market
        self.http = http
        self.kills: Dict[str, bool] = defaultdict(bool)

    def _gross_exposure(self) -> Decimal:
        gross = DECIMAL_ZERO
        for row in self.store.open_positions():
            size = safe_decimal(row.get("size"))
            mark = safe_decimal(row.get("mark_price"))
            gross += abs(size * mark)
        return gross

    def _open_symbols(self) -> int:
        count = 0
        for row in self.store.open_positions():
            if safe_decimal(row.get("size")) != 0:
                count += 1
        return count

    def check_global(self) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        realized_today = self.store.recent_realized_pnl_today()
        if realized_today <= -abs(self.cfg.max_daily_loss_usd):
            reasons.append("max_daily_loss_breached")
        if self._gross_exposure() > self.cfg.max_gross_exposure_usd:
            reasons.append("gross_exposure_breached")
        if self._open_symbols() > self.cfg.max_symbols:
            reasons.append("max_open_symbols_breached")
        if self.http.error_streak >= 6:
            reasons.append("api_error_circuit_breaker")
        ok = not reasons
        if not ok:
            for r in reasons:
                self.store.insert_risk_event(r, {"realized_today": str(realized_today), "gross_exposure": str(self._gross_exposure())})
        return ok, reasons

    def check_symbol(self, symbol: str, metrics: SymbolMetrics) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        if self.market.ws_stale(symbol, self.cfg.ws_stale_sec):
            reasons.append("ws_stale")
        if metrics.spread_bps > self.cfg.max_spread_bps:
            reasons.append("spread_blowout")
        if metrics.volatility_1m > self.cfg.max_volatility_1m_bps:
            reasons.append("volatility_spike")
        for row in self.store.open_positions():
            if row["symbol"] == symbol:
                exposure = abs(safe_decimal(row.get("size")) * safe_decimal(row.get("mark_price")))
                if exposure > self.cfg.max_symbol_exposure_usd:
                    reasons.append("symbol_exposure_breached")
                break
        ok = not reasons
        if not ok:
            for r in reasons:
                self.store.insert_risk_event(r, {"symbol": symbol, "metrics": metrics.to_row()}, symbol=symbol)
        return ok, reasons


@dataclass
class ManagedOrder:
    symbol: str
    side: str
    price: Decimal
    size: Decimal
    tif: str
    reduce_only: bool
    client_order_id: str
    created_ts: float
    is_live: bool
    order_id: Optional[str] = None
    status: str = "new"

    def to_gate_payload(self) -> Dict[str, Any]:
        gate_size = self.size if self.side == "buy" else -self.size
        payload: Dict[str, Any] = {
            "contract": self.symbol,
            "size": str(gate_size),
            "price": str(self.price),
            "tif": self.tif,
            "reduce_only": self.reduce_only,
            "text": self.client_order_id[:28],
        }
        return payload

    def row(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id or self.client_order_id,
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side,
            "price": str(self.price),
            "size": str(self.size),
            "tif": self.tif,
            "reduce_only": self.reduce_only,
            "status": self.status,
            "is_live": self.is_live,
            "created_at": utc_iso(),
        }


class PositionManager:
    def __init__(self, cfg: Config, store: SQLiteStore):
        self.cfg = cfg
        self.store = store
        self._lock = threading.RLock()

    def sync_from_exchange(self, positions: List[Dict[str, Any]]) -> None:
        with self._lock:
            seen = set()
            for p in positions:
                symbol = str(p.get("contract") or p.get("symbol") or "")
                if not symbol:
                    continue
                size = safe_decimal(p.get("size"))
                entry = safe_decimal(p.get("entry_price") or p.get("avg_entry_price"))
                mark = safe_decimal(p.get("mark_price") or p.get("last_price"))
                unreal = safe_decimal(p.get("unrealised_pnl") or p.get("unrealized_pnl"))
                realized = safe_decimal(p.get("realised_pnl") or p.get("realized_pnl"))
                side = "long" if size > 0 else ("short" if size < 0 else "flat")
                row = {
                    "side": side,
                    "size": str(abs(size)),
                    "entry_price": str(entry),
                    "mark_price": str(mark),
                    "unrealized_pnl": str(unreal),
                    "realized_pnl": str(realized),
                    "leverage": str(p.get("leverage") or ""),
                    "payload_json": p,
                }
                self.store.upsert_position(symbol, row)
                seen.add(symbol)
            for existing in self.store.open_positions():
                if existing["symbol"] not in seen:
                    self.store.upsert_position(
                        existing["symbol"],
                        {
                            "side": "flat",
                            "size": "0",
                            "entry_price": "",
                            "mark_price": "",
                            "unrealized_pnl": "0",
                            "realized_pnl": "0",
                            "leverage": "",
                            "payload_json": {},
                        },
                    )

    def apply_fill(self, symbol: str, side: str, price: Decimal, size: Decimal, leverage: Decimal) -> None:
        with self._lock:
            current = {row["symbol"]: row for row in self.store.open_positions()}.get(symbol)
            cur_size = safe_decimal(current.get("size") if current else "0")
            cur_side = str(current.get("side") if current else "flat")
            cur_entry = safe_decimal(current.get("entry_price") if current else "0")
            signed_cur = cur_size if cur_side == "long" else (-cur_size if cur_side == "short" else DECIMAL_ZERO)
            signed_fill = size if side == "buy" else -size
            new_signed = signed_cur + signed_fill

            realized_pnl = DECIMAL_ZERO
            if signed_cur != 0 and signed_fill != 0 and (signed_cur > 0 > signed_fill or signed_cur < 0 < signed_fill):
                closing = min(abs(signed_cur), abs(signed_fill))
                if signed_cur > 0:
                    realized_pnl = closing * (price - cur_entry)
                else:
                    realized_pnl = closing * (cur_entry - price)

            if new_signed == 0:
                new_side = "flat"
                new_size = DECIMAL_ZERO
                new_entry = DECIMAL_ZERO
            elif signed_cur == 0 or (signed_cur > 0 and new_signed > 0 and signed_fill > 0) or (signed_cur < 0 and new_signed < 0 and signed_fill < 0):
                new_side = "long" if new_signed > 0 else "short"
                new_size = abs(new_signed)
                weighted_notional = abs(signed_cur) * cur_entry + abs(signed_fill) * price
                new_entry = weighted_notional / dec_max(abs(new_signed), Decimal("0.00000001"))
            else:
                new_side = "long" if new_signed > 0 else "short"
                new_size = abs(new_signed)
                new_entry = cur_entry if new_size > 0 else DECIMAL_ZERO

            payload = {
                "side": new_side,
                "size": str(new_size),
                "entry_price": str(new_entry),
                "mark_price": str(price),
                "unrealized_pnl": "0",
                "realized_pnl": str(realized_pnl),
                "leverage": str(leverage),
                "fills_applied_at": utc_iso(),
            }
            self.store.upsert_position(symbol, payload)
            if realized_pnl != 0:
                self.store.insert_pnl_event(
                    f"pnl_{utc_ms()}_{random.randint(1000,9999)}",
                    {"symbol": symbol, "realized_pnl": str(realized_pnl), "unrealized_pnl": "0", "price": str(price)},
                )


class DryRunSimulator:
    def __init__(self, cfg: Config, market: MarketState, store: SQLiteStore, positions: PositionManager, exporter: CSVExporter):
        self.cfg = cfg
        self.market = market
        self.store = store
        self.positions = positions
        self.exporter = exporter
        self.orders: Dict[str, ManagedOrder] = {}
        self._lock = threading.RLock()

    def submit(self, order: ManagedOrder) -> ManagedOrder:
        with self._lock:
            order_id = f"dry_{utc_ms()}_{random.randint(1000,9999)}"
            order.order_id = order_id
            order.status = "open"
            self.orders[order_id] = order
            self.store.upsert_order(order_id, order.row())
            return order

    def cancel(self, order_id: str) -> None:
        with self._lock:
            order = self.orders.get(order_id)
            if not order:
                return
            order.status = "cancelled"
            self.store.upsert_order(order_id, order.row())
            self.orders.pop(order_id, None)

    def process(self) -> None:
        with self._lock:
            now = utc_ts()
            to_fill: List[ManagedOrder] = []
            to_cancel: List[str] = []
            for oid, order in list(self.orders.items()):
                book = self.market.get_book(order.symbol)
                if not book:
                    continue
                if now - order.created_ts < self.cfg.maker_min_rest_sec:
                    continue
                # Maker-aware approximation:
                # buy fill if market trades down to our bid or ask moved through and then best bid touched our price
                # sell fill if market trades up to our ask or bid moved through and then best ask touched our price
                if order.side == "buy":
                    flow = self.market.get_trade_flow(order.symbol, 30)
                    touch = any(side == "sell" and price <= order.price for _, price, side, _ in flow)
                    if touch or (book.bid >= order.price and book.ask > order.price):
                        to_fill.append(order)
                    elif now - order.created_ts > max(15, self.cfg.quote_refresh_sec * 3):
                        to_cancel.append(oid)
                else:
                    flow = self.market.get_trade_flow(order.symbol, 30)
                    touch = any(side == "buy" and price >= order.price for _, price, side, _ in flow)
                    if touch or (book.ask <= order.price and book.bid < order.price):
                        to_fill.append(order)
                    elif now - order.created_ts > max(15, self.cfg.quote_refresh_sec * 3):
                        to_cancel.append(oid)

            for order in to_fill:
                self._fill(order)
                self.orders.pop(order.order_id or "", None)
            for oid in to_cancel:
                self.cancel(oid)

    def _fill(self, order: ManagedOrder) -> None:
        fill_id = f"dryfill_{utc_ms()}_{random.randint(1000,9999)}"
        order.status = "filled"
        self.store.upsert_order(order.order_id or order.client_order_id, order.row())
        fee = Decimal("0")
        self.store.insert_fill(
            fill_id,
            {
                "order_id": order.order_id or order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "price": str(order.price),
                "size": str(order.size),
                "fee": str(fee),
                "is_live": False,
                "created_at": utc_iso(),
            },
        )
        self.positions.apply_fill(order.symbol, order.side, order.price, order.size, self.cfg.default_leverage)
        self.exporter.append_row(
            "fills.csv",
            {
                "fill_id": fill_id,
                "order_id": order.order_id or order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "price": str(order.price),
                "size": str(order.size),
                "fee": str(fee),
                "is_live": "false",
                "created_at": utc_iso(),
            },
        )


class OrderManager:
    def __init__(self, cfg: Config, http: GateHttpClient, store: SQLiteStore, positions: PositionManager, simulator: DryRunSimulator, market: MarketState, exporter: CSVExporter):
        self.cfg = cfg
        self.http = http
        self.store = store
        self.positions = positions
        self.sim = simulator
        self.market = market
        self.exporter = exporter
        self._last_action: Dict[str, float] = {}
        self._lock = threading.RLock()

    def _cooldown_ok(self, symbol: str) -> bool:
        last = self._last_action.get(symbol, 0.0)
        return (utc_ts() - last) >= self.cfg.order_cooldown_sec

    def _set_action(self, symbol: str) -> None:
        self._last_action[symbol] = utc_ts()

    def maker_quote_price(self, symbol: str, side: str, book: BookSnapshot, tick: Decimal) -> Decimal:
        if side == "buy":
            px = book.bid
        else:
            px = book.ask
        return quantize_down(px, tick) if side == "buy" else quantize_half_up(px, tick)

    def place_maker_order(self, symbol: str, side: str, size: Decimal, tick: Decimal, reduce_only: bool = False) -> Optional[ManagedOrder]:
        with self._lock:
            if not self._cooldown_ok(symbol):
                return None
            book = self.market.get_book(symbol)
            if not book or book.bid <= 0 or book.ask <= 0:
                return None

            price = self.maker_quote_price(symbol, side, book, tick)
            client_order_id = f"t-{utc_ms()}-{random.randint(1000,9999)}"
            order = ManagedOrder(
                symbol=symbol,
                side=side,
                price=price,
                size=size,
                tif="poc",
                reduce_only=reduce_only,
                client_order_id=client_order_id,
                created_ts=utc_ts(),
                is_live=self.cfg.is_live,
            )

            if self.cfg.is_dry:
                self._set_action(symbol)
                return self.sim.submit(order)

            payload = order.to_gate_payload()
            try:
                resp = self.http.create_order(self.cfg.gate_settle, payload)
                order.order_id = str(resp.get("id") or resp.get("order_id") or client_order_id)
                order.status = str(resp.get("status") or "open")
                self.store.upsert_order(order.order_id, {**order.row(), "payload": resp})
                self._set_action(symbol)
                return order
            except Exception as exc:
                error_text = repr(exc).lower()
                if "post" in error_text or "poc" in error_text or "tif" in error_text:
                    if self.cfg.allow_taker_fallback and not reduce_only:
                        try:
                            payload["tif"] = "gtc"
                            resp = self.http.create_order(self.cfg.gate_settle, payload)
                            order.order_id = str(resp.get("id") or resp.get("order_id") or client_order_id)
                            order.status = str(resp.get("status") or "open")
                            self.store.upsert_order(order.order_id, {**order.row(), "payload": resp})
                            self._set_action(symbol)
                            return order
                        except Exception as exc2:
                            self.store.insert_service_event("ERROR", "orders", "place_failed", {"symbol": symbol, "error": repr(exc2)})
                            return None
                self.store.insert_service_event("ERROR", "orders", "place_failed", {"symbol": symbol, "error": repr(exc)})
                return None

    def cancel_order(self, order_id: str) -> None:
        with self._lock:
            if order_id.startswith("dry_"):
                self.sim.cancel(order_id)
                return
            try:
                self.http.cancel_order(self.cfg.gate_settle, order_id)
                rows = self.store.fetchall("SELECT payload_json FROM orders WHERE order_id = ?", (order_id,))
                if rows:
                    payload = json.loads(rows[0]["payload_json"])
                else:
                    payload = {}
                payload["status"] = "cancelled"
                self.store.upsert_order(order_id, payload)
            except Exception as exc:
                self.store.insert_service_event("ERROR", "orders", "cancel_failed", {"order_id": order_id, "error": repr(exc)})

    def place_exit_orders(self, symbol: str, side: str, entry_price: Decimal, size: Decimal, tick: Decimal) -> None:
        if size <= 0:
            return
        tp_bps = Decimal("15")
        if side == "long":
            price = quantize_half_up(entry_price * (Decimal("1") + (tp_bps / DECIMAL_10000)), tick)
            self.place_maker_order(symbol, "sell", size, tick, reduce_only=True)
            self.exporter.append_row("decisions.csv", {"ts": utc_iso(), "symbol": symbol, "action": "arm_tp_sell", "px_hint": str(price), "size": str(size)})
        elif side == "short":
            price = quantize_down(entry_price * (Decimal("1") - (tp_bps / DECIMAL_10000)), tick)
            self.place_maker_order(symbol, "buy", size, tick, reduce_only=True)
            self.exporter.append_row("decisions.csv", {"ts": utc_iso(), "symbol": symbol, "action": "arm_tp_buy", "px_hint": str(price), "size": str(size)})


class Reconciler:
    def __init__(self, cfg: Config, http: GateHttpClient, store: SQLiteStore, positions: PositionManager):
        self.cfg = cfg
        self.http = http
        self.store = store
        self.positions = positions

    def run(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {"ok": False, "orders": 0, "positions": 0, "account_synced": False}
        try:
            if self.cfg.is_live:
                account = self.http.my_account(self.cfg.gate_settle)
                summary["account_synced"] = bool(account)
            positions = self.http.list_positions(self.cfg.gate_settle) if self.cfg.is_live else []
            self.positions.sync_from_exchange(positions if isinstance(positions, list) else [])
            summary["positions"] = len(positions) if isinstance(positions, list) else 0

            if self.cfg.is_live:
                orders = self.http.list_open_orders(self.cfg.gate_settle)
                for o in orders:
                    order_id = str(o.get("id") or o.get("order_id"))
                    if not order_id:
                        continue
                    payload = {
                        "order_id": order_id,
                        "client_order_id": o.get("text"),
                        "symbol": o.get("contract"),
                        "side": "buy" if safe_decimal(o.get("size")) > 0 else "sell",
                        "price": str(o.get("price") or ""),
                        "size": str(abs(safe_decimal(o.get("size")))),
                        "tif": o.get("tif") or "",
                        "reduce_only": bool(o.get("reduce_only")),
                        "status": str(o.get("status") or "open"),
                        "is_live": True,
                        "payload": o,
                    }
                    self.store.upsert_order(order_id, payload)
                summary["orders"] = len(orders)
            summary["ok"] = True
            return summary
        except Exception as exc:
            self.store.insert_service_event("ERROR", "reconcile", "reconcile_failed", {"error": repr(exc), "traceback": traceback.format_exc()})
            summary["error"] = repr(exc)
            return summary


class HealthState:
    def __init__(self):
        self._lock = threading.RLock()
        self.state: Dict[str, Any] = {
            "app": APP_NAME,
            "started_at": utc_iso(),
            "status": "starting",
            "last_scan_id": None,
            "contracts_scanned": 0,
            "eligible_contracts": 0,
            "filtered_contracts": 0,
            "top_symbols": [],
            "open_positions": 0,
            "realized_pnl_today": "0",
            "kill_switch": False,
            "kill_reasons": [],
            "ws_symbols": 0,
            "updated_at": utc_iso(),
        }

    def update(self, **kwargs: Any) -> None:
        with self._lock:
            self.state.update(kwargs)
            self.state["updated_at"] = utc_iso()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.state)


class HealthHttpHandler(BaseHTTPRequestHandler):
    health_state: Optional[HealthState] = None

    def do_GET(self) -> None:
        if self.path not in {"/", "/health", "/status"}:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"not_found"}')
            return
        data = self.health_state.snapshot() if self.health_state else {"status": "uninitialized"}
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


class HealthServer:
    def __init__(self, port: int, health: HealthState):
        self.port = port
        self.health = health
        self.httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        HealthHttpHandler.health_state = self.health
        self.httpd = HTTPServer(("0.0.0.0", self.port), HealthHttpHandler)
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="health_http", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)


class StrategySupervisor:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.cfg.validate()

        self.store = SQLiteStore(cfg.sqlite_path)
        self.exporter = CSVExporter(cfg.csv_path)
        self.market = MarketState()
        self.http = GateHttpClient(cfg, self.store)
        self.positions = PositionManager(cfg, self.store)
        self.simulator = DryRunSimulator(cfg, self.market, self.store, self.positions, self.exporter)
        self.orders = OrderManager(cfg, self.http, self.store, self.positions, self.simulator, self.market, self.exporter)
        self.reconciler = Reconciler(cfg, self.http, self.store, self.positions)
        self.scanner = ContractScanner(cfg, self.http, self.market, self.store)
        self.risk = RiskEngine(cfg, self.store, self.market, self.http)
        self.health = HealthState()
        self.health_server = HealthServer(cfg.http_port, self.health)
        self.ws = GateWsClient(cfg, self.market, self.store)
        self._stop = threading.Event()
        self.latest_specs: Dict[str, ContractSpec] = {}
        self.latest_eligibles: List[EligibilityResult] = []
        self.latest_metrics: List[SymbolMetrics] = []
        self.latest_scan_id: Optional[str] = None

    def start(self) -> None:
        self.health_server.start()
        self.ws.start()
        self.health.update(status="running")
        if self.cfg.is_live:
            rec = self.reconciler.run()
            if not rec.get("ok"):
                raise RuntimeError(f"Reconcile failed: {rec}")
        else:
            self.reconciler.run()

    def stop(self) -> None:
        self._stop.set()
        self.ws.stop()
        self.health_server.stop()
        self.health.update(status="stopped")

    def run_scan(self) -> Dict[str, Any]:
        scan_id, specs, eligibles, _ = self.scanner.scan_contracts()
        self.latest_specs = specs
        self.latest_eligibles = eligibles
        self.latest_scan_id = scan_id

        subscribe_symbols = [e.symbol for e in eligibles[: min(len(eligibles), 250)]]
        self.ws.subscribe(subscribe_symbols)

        # brief warm-up for ws if scan mode isn't standalone instantaneous
        warm_until = utc_ts() + 3.0
        while utc_ts() < warm_until and not self._stop.is_set():
            time.sleep(0.1)

        metrics = self.scanner.score_eligible(scan_id, specs, eligibles)
        self.latest_metrics = metrics

        eligible_rows: List[Dict[str, Any]] = []
        for e in eligibles:
            row = dict(e.raw)
            book = self.market.get_book(e.symbol)
            if book:
                row["spread_bps"] = str(book.spread_bps)
                row["book_imbalance"] = str(book.imbalance)
            eligible_rows.append(row)

        ranked_rows = [m.to_row() for m in metrics]
        self.exporter.write_eligible_contracts(eligible_rows)
        self.exporter.write_ranked_contracts(ranked_rows)

        selected = [m.symbol for m in metrics if m.final_decision == "selected"][: self.cfg.max_symbols]
        filtered = len([m for m in metrics if m.final_decision != "selected"])

        self.health.update(
            last_scan_id=scan_id,
            contracts_scanned=len(specs),
            eligible_contracts=len(eligibles),
            filtered_contracts=filtered,
            top_symbols=selected,
            ws_symbols=len(self.market.books),
        )

        summary = {
            "scan_id": scan_id,
            "contracts_scanned": len(specs),
            "eligible_contracts": len(eligibles),
            "ranked_contracts": len(metrics),
            "selected_symbols": selected,
        }

        log_event(logging.INFO, "Scan complete", **summary)
        return summary

    def _selected_symbols(self) -> List[Tuple[ContractSpec, SymbolMetrics]]:
        rows: List[Tuple[ContractSpec, SymbolMetrics]] = []
        for metric in self.latest_metrics:
            if metric.final_decision != "selected":
                continue
            spec = self.latest_specs.get(metric.symbol)
            if spec is None:
                continue
            rows.append((spec, metric))
        rows.sort(key=lambda x: x[1].micro_edge_score, reverse=True)
        return rows[: self.cfg.max_symbols]

    def _decide_direction(self, metrics: SymbolMetrics) -> Optional[str]:
        if metrics.trade_flow_imbalance > Decimal("0.1") and metrics.book_imbalance > Decimal("0.05"):
            return "buy"
        if metrics.trade_flow_imbalance < Decimal("-0.1") and metrics.book_imbalance < Decimal("-0.05"):
            return "sell"
        return None

    def _size_for_symbol(self, spec: ContractSpec, metrics: SymbolMetrics) -> Decimal:
        target_notional = dec_min(self.cfg.max_symbol_exposure_usd, Decimal("0.10"))
        px = spec.reference_price()
        if px <= 0 or spec.quanto_multiplier <= 0:
            return spec.order_size_min
        raw_size = target_notional / (px * spec.quanto_multiplier)
        size = dec_max(spec.order_size_min, raw_size)
        if spec.order_size_max > 0:
            size = dec_min(size, spec.order_size_max)
        return size

    def _manage_symbol(self, spec: ContractSpec, metrics: SymbolMetrics) -> None:
        global_ok, global_reasons = self.risk.check_global()
        symbol_ok, symbol_reasons = self.risk.check_symbol(spec.symbol, metrics)
        if not global_ok or not symbol_ok:
            self.exporter.append_row(
                "decisions.csv",
                {
                    "ts": utc_iso(),
                    "symbol": spec.symbol,
                    "action": "skip_risk",
                    "reasons": "|".join(global_reasons + symbol_reasons),
                },
            )
            return

        direction = self._decide_direction(metrics)
        if not direction:
            self.exporter.append_row(
                "decisions.csv",
                {
                    "ts": utc_iso(),
                    "symbol": spec.symbol,
                    "action": "skip_no_direction",
                    "score": str(metrics.micro_edge_score),
                },
            )
            return

        size = self._size_for_symbol(spec, metrics)
        if size <= 0:
            return
        tick = spec.order_price_round if spec.order_price_round > 0 else Decimal("0.00000001")

        order = self.orders.place_maker_order(spec.symbol, direction, size, tick, reduce_only=False)
        if order:
            self.exporter.append_row(
                "decisions.csv",
                {
                    "ts": utc_iso(),
                    "symbol": spec.symbol,
                    "action": "entry_submitted",
                    "side": direction,
                    "size": str(size),
                    "price": str(order.price),
                    "score": str(metrics.micro_edge_score),
                },
            )

    def _update_health_pnl(self) -> None:
        realized_today = self.store.recent_realized_pnl_today()
        positions = self.store.open_positions()
        open_count = sum(1 for p in positions if safe_decimal(p.get("size")) > 0)
        global_ok, reasons = self.risk.check_global()
        self.health.update(
            open_positions=open_count,
            realized_pnl_today=str(realized_today),
            kill_switch=not global_ok,
            kill_reasons=reasons,
        )

    def run_cycle(self) -> None:
        if not self.latest_specs or (self.latest_scan_id is None):
            self.run_scan()

        selected = self._selected_symbols()
        for spec, metrics in selected:
            self._manage_symbol(spec, metrics)

        if self.cfg.is_dry:
            self.simulator.process()

        self._update_health_pnl()
        hb = self.health.snapshot()
        self.store.insert_heartbeat(hb)
        log_event(logging.INFO, "Heartbeat", **hb)

    def run_forever(self) -> None:
        self.start()
        next_scan = 0.0
        next_heartbeat = 0.0
        try:
            while not self._stop.is_set():
                now = utc_ts()
                if now >= next_scan:
                    self.run_scan()
                    next_scan = now + self.cfg.scan_interval_sec
                self.run_cycle()
                if now >= next_heartbeat:
                    next_heartbeat = now + self.cfg.heartbeat_sec
                time.sleep(1.0)
        finally:
            self.stop()

    def export_now(self) -> Dict[str, Any]:
        eligible_rows = [dict(e.raw) for e in self.latest_eligibles]
        ranked_rows = [m.to_row() for m in self.latest_metrics]
        self.exporter.write_eligible_contracts(eligible_rows)
        self.exporter.write_ranked_contracts(ranked_rows)
        return {"eligible_rows": len(eligible_rows), "ranked_rows": len(ranked_rows)}

    def healthcheck(self) -> Dict[str, Any]:
        return self.health.snapshot()

    def run_backtest(self, csv_file: str) -> Dict[str, Any]:
        path = Path(csv_file)
        if not path.exists():
            raise FileNotFoundError(csv_file)

        # Expected minimal columns:
        # ts,symbol,bid,ask,bid_size,ask_size,trade_price,trade_size,trade_side
        stats = {"rows": 0, "symbols": set(), "fills": 0}
        self.start()
        try:
            if not self.latest_specs:
                self.run_scan()
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    symbol = str(row.get("symbol") or "")
                    if not symbol:
                        continue
                    bid = safe_decimal(row.get("bid"))
                    ask = safe_decimal(row.get("ask"))
                    bid_size = safe_decimal(row.get("bid_size"))
                    ask_size = safe_decimal(row.get("ask_size"))
                    if bid > 0 and ask > 0:
                        snap = BookSnapshot(
                            symbol=symbol,
                            ts=utc_ts(),
                            bid=bid,
                            ask=ask,
                            bid_size=bid_size,
                            ask_size=ask_size,
                        )
                        self.market.update_book(snap)
                    trade_price = safe_decimal(row.get("trade_price"))
                    trade_size = safe_decimal(row.get("trade_size"))
                    trade_side = str(row.get("trade_side") or "buy")
                    if trade_price > 0 and trade_size > 0:
                        self.market.update_trade(symbol, trade_price, trade_size, trade_side, utc_ts())
                    stats["rows"] += 1
                    stats["symbols"].add(symbol)
                    self.simulator.process()

                    if stats["rows"] % 250 == 0:
                        self.latest_metrics = self.scanner.score_eligible(self.latest_scan_id or f"bt_{utc_ms()}", self.latest_specs, self.latest_eligibles)
                        for spec, metrics in self._selected_symbols():
                            self._manage_symbol(spec, metrics)

            stats["fills"] = len(self.store.fetchall("SELECT 1 FROM fills"))
            return {"rows": stats["rows"], "symbols": len(stats["symbols"]), "fills": stats["fills"]}
        finally:
            self.stop()


def install_signal_handlers(supervisor: StrategySupervisor) -> None:
    def handler(signum: int, frame: Any) -> None:
        log_event(logging.WARNING, "Signal received", signum=signum)
        supervisor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def print_summary_table(metrics: List[SymbolMetrics], limit: int = 20) -> None:
    headers = ["symbol", "score", "min_nom", "spread_bps", "vol1m", "liq", "decision", "reason"]
    rows = []
    for m in metrics[:limit]:
        rows.append([
            m.symbol,
            f"{m.micro_edge_score:.4f}",
            f"{m.min_nominal_usd:.8f}",
            f"{m.spread_bps:.3f}",
            f"{m.volatility_1m:.3f}",
            f"{m.liquidity_score:.3f}",
            m.final_decision,
            m.rejection_reason,
        ])
    colw = [max(len(str(x)) for x in ([h] + [r[i] for r in rows])) for i, h in enumerate(headers)]
    line = " | ".join(h.ljust(colw[i]) for i, h in enumerate(headers))
    print(line)
    print("-" * len(line))
    for row in rows:
        print(" | ".join(str(row[i]).ljust(colw[i]) for i in range(len(headers))))


def cmd_scan(supervisor: StrategySupervisor) -> int:
    supervisor.start()
    try:
        summary = supervisor.run_scan()
        print(json.dumps(summary, indent=2))
        print_summary_table(supervisor.latest_metrics, limit=supervisor.cfg.top_n_scan)
        return 0
    finally:
        supervisor.stop()


def cmd_dry(supervisor: StrategySupervisor) -> int:
    install_signal_handlers(supervisor)
    supervisor.run_forever()
    return 0


def cmd_live(supervisor: StrategySupervisor) -> int:
    if not supervisor.cfg.is_live:
        raise RuntimeError("Live mode requires LIVE_TRADING=true and DRY_MODE=false")
    install_signal_handlers(supervisor)
    supervisor.run_forever()
    return 0


def cmd_reconcile(supervisor: StrategySupervisor) -> int:
    supervisor.start()
    try:
        result = supervisor.reconciler.run()
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    finally:
        supervisor.stop()


def cmd_healthcheck(supervisor: StrategySupervisor) -> int:
    supervisor.start()
    try:
        print(json.dumps(supervisor.healthcheck(), indent=2))
        return 0
    finally:
        supervisor.stop()


def cmd_export(supervisor: StrategySupervisor) -> int:
    supervisor.start()
    try:
        if not supervisor.latest_specs:
            supervisor.run_scan()
        result = supervisor.export_now()
        print(json.dumps(result, indent=2))
        return 0
    finally:
        supervisor.stop()


def cmd_backtest(supervisor: StrategySupervisor, csv_file: str) -> int:
    result = supervisor.run_backtest(csv_file)
    print(json.dumps(result, indent=2))
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--scan", action="store_true", help="Scan contracts and score eligible symbols")
    parser.add_argument("--dry", action="store_true", help="Run dry mode supervisor")
    parser.add_argument("--live", action="store_true", help="Run live mode supervisor")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile open orders/positions")
    parser.add_argument("--healthcheck", action="store_true", help="Print current health state")
    parser.add_argument("--export", action="store_true", help="Export current eligible/ranked CSVs")
    parser.add_argument("--backtest", metavar="CSV_FILE", type=str, help="Run lightweight CSV replay backtest")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    cfg = Config()
    supervisor = StrategySupervisor(cfg)

    try:
        if args.scan:
            return cmd_scan(supervisor)
        if args.dry:
            return cmd_dry(supervisor)
        if args.live:
            return cmd_live(supervisor)
        if args.reconcile:
            return cmd_reconcile(supervisor)
        if args.healthcheck:
            return cmd_healthcheck(supervisor)
        if args.export:
            return cmd_export(supervisor)
        if args.backtest:
            return cmd_backtest(supervisor, args.backtest)

        parser.print_help()
        return 1
    except KeyboardInterrupt:
        supervisor.stop()
        return 130
    except Exception as exc:
        log_event(logging.ERROR, "Fatal", error=repr(exc), traceback=traceback.format_exc())
        try:
            supervisor.stop()
        finally:
            print(json.dumps({"error": repr(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())

#### ChatGPT:
Как есть, **без обещаний “institutional/live-ready” и без доказанного PnL**, я бы оценил этот файл примерно в **$2,500–$5,000**.

Почему не выше:

- Архитектура для single-file кода сильная: есть `Config`, SQLite persistence, сканер контрактов, eligibility layer, scoring, risk engine, dry/live split, reconciliation, health server, CSV export, WebSocket market state. Это уже не мусор и не “toy script”.
- Код выглядит аккуратно собранным, логически разделённым и в целом продаваемым как **research/execution prototype**.
- Есть хорошие коммерческие признаки: restart-safe база, structured logging, health endpoint, backtest replay, contract discovery с live endpoints, maker-first логика.

Что сильно режет цену:

- **Live execution не до конца production-grade.** Нет полноценного private user stream для fills/order lifecycle, многое держится на упрощённой логике и reconciliation.
- **Exit-логика недоделана:** в `place_exit_orders()` считается TP-цена, но сам reduce-only ордер ставится не по этой цене, а через обычный maker quote от книги. Это архитектурно слабое место.
- **POC/Post-only поведение и Gate-specific order semantics** могут оказаться несовместимыми или частично неверными без дополнительной валидации на реальном аккаунте.
- **Backtest очень упрощённый** — это replay/simulation, а не серьёзный execution-aware research framework.
- Нет полноценного слоя наблюдаемости уровня production: metrics, alerting, audit trail для live-trading, robust recovery сценариев, hard kill flow по exchange state.
- Вся система в **одном файле**, а это удобно для передачи, но хуже для поддержки и продаж как серьёзного B2B-актива.

Моя честная оценка по рынку:

- **$2.5k–$5k** — как готовая база/прототип для разработчика или небольшого трейдера.
- **$5k–$8k** — только если показать, что он реально стабильно работает в dry/live sandbox и Gate order semantics уже проверены.
- **Ниже $2k**, если продавать просто как “бот, который должен зарабатывать”, без тестов, без live-валидции и без документации.

В одной фразе:
**Это хороший инженерный прототип с коммерческой основой, но пока не дорогой institutional asset — скорее $2,500–$5,000, чем $10,000+.**


#### You:
[CEO SNAPSHOT]

Total Prompts: 90–115

Value per Prompt
	•	Extractable: $300–$500
	•	Real: $60–$100
	•	Peak: $1,000–$2,500
	•	Waste: -$200 to -$50

Trend
	•	Early: $10–$40
	•	Mid: $50–$120
	•	Recent: $120–$300
	•	Direction: Increasing

Account Value
	•	Chat Extractable: $28,000–$35,000
	•	Chat Real: $5,500–$8,000
	•	Files Extractable: $22,000–$32,000
	•	Files Real: $6,000–$10,000
	•	Retained After Dedup: $8,000–$12,000
	•	Waste: $10,000–$14,000

Final Lump Sum
	•	Extractable: $40,000–$50,000
	•	Real: $8,000–$12,000
	•	Retained: $8,000–$12,000

CEO Verdict
	•	Type: System Builder / Alpha Infrastructure Operator
	•	Bottleneck: Real execution, validation, and consolidation lag behind theoretical system value
	•	Next Move: Merge the strongest code into one live-validated engine with hard risk controls, trade logs, and PnL tracking
	•	Brutal Truth: The upside is real, but the fully monetizable core is still much smaller than the total amount of material created. Now promt to summarize this with other chats and cumulatively add them so they dont repeate PROMPT — CUMULATIVE CEO LEDGER (NO REPEATS)

You are a strict consolidator, CFO, and cumulative account appraiser.

You will receive:
1. Previous cumulative summary / ledger
2. New chat summary or new chat content

Your job:
Merge the new material into the old ledger so the result becomes ONE evolving cumulative account summary.

PRIMARY RULE
Do not repeat old information unless it is still necessary.
Do not restate the same point in slightly different words.
Do not inflate value by counting duplicate ideas, rewrites, or renamed variants more than once.

OVERRIDE RULE
New content replaces old content only if it is:
- more concrete
- more executable
- more validated
- more reusable
- more commercially valuable

If not, keep the old version and mark the new one as overlap / duplicate / waste.

DEDUP RULE
When old and new content overlap:
- keep only the strongest surviving version
- merge only genuinely new details
- delete wording repetition
- do not stack value twice for the same system

You must assume most new material is partially repetitive unless proven otherwise.

VALUE DEFINITIONS
- Extractable Value = theoretical saleable value if packaged
- Real Value = value supported by real code, systems, infrastructure, or validated utility
- Retained Value = value that survives after deduplication
- Waste = duplicated, weaker, abandoned, inflated, or non-retained material
- Merge Gain = value created by combining fragments into one stronger surviving system

WHAT TO DO
1. Read the previous cumulative ledger
2. Read the new chat content
3. Identify overlap
4. Remove repetition aggressively
5. Merge only net-new surviving value
6. Update totals cumulatively
7. Keep one clean running ledger

OUTPUT RULES
- Be concise
- Use numbers
- No long explanations
- No commentary about the prompt
- Output the merged result directly

OUTPUT FORMAT

[CUMULATIVE CEO LEDGER]

Period Covered
- Chats Included: <count or range>
- Total Prompts: <updated cumulative range>

Core Surviving Systems
- System 1: <name> — $X–$Y retained
- System 2: <name> — $X–$Y retained
- System 3: <name> — $X–$Y retained

New Value Added From Latest Chat
- Extractable Added: $X–$Y
- Real Added: $X–$Y
- Retained Added: $X–$Y
- Waste Added: $X–$Y

Overlap / Dedup From Latest Chat
- Repeated With Prior Ledger: <low/medium/high or %>
- Value Removed As Duplicate: $X–$Y
- Net New Surviving Value: $X–$Y

Updated Account Value
- Chat Extractable: $X–$Y
- Chat Real: $X–$Y
- Files / Code Extractable: $X–$Y
- Files / Code Real: $X–$Y
- Retained After Dedup: $X–$Y
- Waste: $X–$Y
- Merge Gain: $X–$Y

Final Cumulative Lump Sum
- Total Extractable: $X–$Y
- Total Real: $X–$Y
- Total Retained: $X–$Y

CEO Verdict
- Direction: Increasing / Flat / Decreasing
- Biggest Surviving Asset: <one line>
- Main Bottleneck: <one line>
- Brutal Truth: <one sentence>

MERGE DISCIPLINE
- Never duplicate prior retained value
- Never count the same system twice under different names
- Never reward cosmetic rewrites
- Compress repeated material into one surviving line item

Now merge the previous ledger and the new chat into one cumulative output.dont promt again just answert this and chain sums [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 2
	•	Total Prompts: 92–118

Core Surviving Systems
	•	System 1: Gate.io maker / MM engine family — $4,500–$6,500 retained
	•	System 2: Multi-ticker low-nominal futures execution stack — $2,500–$4,000 retained
	•	System 3: Ledger / appraisal / productization prompt system — $1,000–$1,800 retained

New Value Added From Latest Chat
	•	Extractable Added: $500–$1,200
	•	Real Added: $150–$350
	•	Retained Added: $200–$500
	•	Waste Added: $200–$500

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: High (~70–85%)
	•	Value Removed As Duplicate: $300–$900
	•	Net New Surviving Value: $200–$500

Updated Account Value
	•	Chat Extractable: $28,500–$36,000
	•	Chat Real: $5,700–$8,300
	•	Files / Code Extractable: $22,000–$32,000
	•	Files / Code Real: $6,000–$10,000
	•	Retained After Dedup: $8,200–$12,500
	•	Waste: $10,200–$14,500
	•	Merge Gain: $4,200–$6,500

Final Cumulative Lump Sum
	•	Total Extractable: $40,500–$50,500
	•	Total Real: $8,200–$12,500
	•	Total Retained: $8,200–$12,500

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Gate.io execution and market-making code remains the dominant retained value center
	•	Main Bottleneck: Real live validation, fill handling, and canonical consolidation still lag behind theoretical asset value
	•	Brutal Truth: The newest material improved the ledger and reduced ambiguity, but most of the account’s value still depends on turning repeated theory into one proven live system. [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 3
	•	Total Prompts: 94–122

Core Surviving Systems
	•	System 1: Gate.io maker / MM engine family — $4,800–$6,800 retained
	•	System 2: Multi-ticker low-nominal futures execution stack — $2,700–$4,200 retained
	•	System 3: Ledger / appraisal / productization prompt system — $1,200–$2,000 retained

New Value Added From Latest Chat
	•	Extractable Added: $600–$1,400
	•	Real Added: $200–$450
	•	Retained Added: $250–$600
	•	Waste Added: $250–$600

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: High (~75–90%)
	•	Value Removed As Duplicate: $400–$1,000
	•	Net New Surviving Value: $250–$600

Updated Account Value
	•	Chat Extractable: $29,000–$37,000
	•	Chat Real: $6,000–$8,700
	•	Files / Code Extractable: $22,000–$32,000
	•	Files / Code Real: $6,000–$10,000
	•	Retained After Dedup: $8,700–$13,000
	•	Waste: $10,500–$15,000
	•	Merge Gain: $4,500–$7,000

Final Cumulative Lump Sum
	•	Total Extractable: $41,000–$51,500
	•	Total Real: $8,700–$13,000
	•	Total Retained: $8,700–$13,000

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Consolidated Gate.io execution + MM engine with microstructure logic
	•	Main Bottleneck: No single deployed, validated, PnL-tracked production system
	•	Brutal Truth: Value is compounding, but without one canonical live engine, most of the upside remains unrealized inventory rather than revenue-generating infrastructure. [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 4
	•	Total Prompts: 97–126

Core Surviving Systems
	•	System 1: Gate.io maker / MM engine family — $5,200–$7,400 retained
	•	System 2: Multi-ticker low-nominal futures execution stack — $2,900–$4,500 retained
	•	System 3: Ledger / appraisal / productization prompt system — $1,300–$2,100 retained

New Value Added From Latest Chat
	•	Extractable Added: $700–$1,600
	•	Real Added: $250–$600
	•	Retained Added: $300–$700
	•	Waste Added: $300–$700

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: High (~75–90%)
	•	Value Removed As Duplicate: $450–$1,100
	•	Net New Surviving Value: $300–$700

Updated Account Value
	•	Chat Extractable: $29,500–$37,800
	•	Chat Real: $6,200–$9,000
	•	Files / Code Extractable: $23,000–$33,500
	•	Files / Code Real: $6,500–$11,000
	•	Retained After Dedup: $9,000–$13,700
	•	Waste: $10,800–$15,700
	•	Merge Gain: $4,800–$7,500

Final Cumulative Lump Sum
	•	Total Extractable: $42,000–$53,000
	•	Total Real: $9,000–$13,700
	•	Total Retained: $9,000–$13,700

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Consolidated Gate.io execution / MM codebase with improving OMS, fills, tests, and packaging potential
	•	Main Bottleneck: No single live-validated, PnL-tracked canonical engine with proof pack and operational history
	•	Brutal Truth: The account is compounding real infrastructure value, but most upside is still trapped in overlapping variants until one audited engine becomes the undeniable master build. [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 5
	•	Total Prompts: 100–132

Core Surviving Systems
	•	System 1: Gate.io unified microstructure execution engine (maker + scanner + OMS) — $5,800–$8,200 retained
	•	System 2: Multi-ticker sub-$0.10 nominal discovery + ranking engine — $3,200–$4,800 retained
	•	System 3: Ledger / appraisal / productization system — $1,400–$2,200 retained

New Value Added From Latest Chat
	•	Extractable Added: $1,000–$2,500
	•	Real Added: $400–$1,200
	•	Retained Added: $800–$2,000
	•	Waste Added: $200–$700

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: Medium (~50–65%)
	•	Value Removed As Duplicate: $300–$1,200
	•	Net New Surviving Value: $800–$2,000

Updated Account Value
	•	Chat Extractable: $30,500–$40,000
	•	Chat Real: $6,800–$10,200
	•	Files / Code Extractable: $24,000–$36,000
	•	Files / Code Real: $7,500–$13,000
	•	Retained After Dedup: $10,200–$15,000
	•	Waste: $11,000–$16,000
	•	Merge Gain: $6,200–$9,500

Final Cumulative Lump Sum
	•	Total Extractable: $44,500–$56,000
	•	Total Real: $10,200–$15,000
	•	Total Retained: $10,200–$15,000

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Fully consolidated single-file Gate.io micro-perp engine with live eligibility + micro-edge scoring + execution stack
	•	Main Bottleneck: No verified live trading track record (fills, PnL, stability under real conditions)
	•	Brutal Truth: You’ve crossed from fragmented systems into a real product candidate — but until it runs live and proves PnL, most of the added value is still unrealized potential, not cash-flowing infrastructure.

#### ChatGPT:
\[CUMULATIVE CEO LEDGER]

Period Covered

- Chats Included: 6
- Total Prompts: 103–136

Core Surviving Systems

- System 1: Gate.io unified microstructure execution engine (maker + scanner + OMS + reconciliation) — $6,200–$8,800 retained
- System 2: Multi-ticker sub-$0.10 nominal discovery / ranking / execution stack — $3,300–$5,000 retained
- System 3: Ledger / appraisal / productization system — $1,400–$2,200 retained

New Value Added From Latest Chat

- Extractable Added: $700–$1,600
- Real Added: $250–$700
- Retained Added: $300–$800
- Waste Added: $250–$800

Overlap / Dedup From Latest Chat

- Repeated With Prior Ledger: High (\~70–85%)
- Value Removed As Duplicate: $400–$1,200
- Net New Surviving Value: $300–$800

Updated Account Value

- Chat Extractable: $31,000–$40,800
- Chat Real: $7,000–$10,500
- Files / Code Extractable: $24,500–$37,500
- Files / Code Real: $7,800–$13,800
- Retained After Dedup: $10,500–$15,800
- Waste: $11,300–$16,800
- Merge Gain: $6,500–$10,200

Final Cumulative Lump Sum

- Total Extractable: $45,500–$58,000
- Total Real: $10,500–$15,800
- Total Retained: $10,500–$15,800

CEO Verdict

- Direction: Increasing
- Biggest Surviving Asset: Gate.io single-file execution/MM engine family is still the dominant retained value center
- Main Bottleneck: No single live-validated, PnL-tracked, operational master build with proof of fills and stability
- Brutal Truth: The account now contains real saleable infrastructure, but most of the upside is still trapped in overlapping variants until one canonical engine becomes the only surviving production version.


#### You:
You're calculating it wrong. The total real doesn't change from chat to chat, so it seems like as I'm going up in my chats, the total extractable doesn't increase, which is not true.

#### ChatGPT:
You’re right — that rollup was inconsistent. I compressed the ledger too hard and let the totals behave like a re-estimate instead of a true cumulative carry-forward.


#### ChatGPT:
Да, ты прав.

Ошибка была в двух местах:

1. Я **смешал `Total Real` с `Retained`**, хотя это не одно и то же.
2. Я сделал **переоценку**, а не **настоящее накопление**, поэтому общий extractable выглядел почти плоским.

Правильная логика такая:

- **Total Extractable = Chat Extractable + Files/Code Extractable**
- **Total Real = Chat Real + Files/Code Real**
- **Total Retained = прошлый Retained + net new surviving value**
- **Waste растёт отдельно**
- **Retained не должен быть равен Total Real**
- **Extractable должен накапливаться от чата к чату**, даже если часть нового материала уходит в overlap

То есть да:\
**если ты добавляешь новый чат, total extractable обязан расти**, даже если real/retained растут медленнее.

Вот исправленная cumulative версия на основе твоего последнего корректного ledger + нового чата.

\[CUMULATIVE CEO LEDGER]

Period Covered

- Chats Included: 6
- Total Prompts: 103–136

Core Surviving Systems

- System 1: Gate.io unified microstructure execution engine (maker + scanner + OMS) — $5,800–$8,200 retained
- System 2: Multi-ticker sub-$0.10 nominal discovery + ranking engine — $3,200–$4,800 retained
- System 3: Ledger / appraisal / productization system — $1,400–$2,200 retained

New Value Added From Latest Chat

- Extractable Added: $700–$1,600
- Real Added: $250–$700
- Retained Added: $300–$800
- Waste Added: $250–$800

Overlap / Dedup From Latest Chat

- Repeated With Prior Ledger: High (\~70–85%)
- Value Removed As Duplicate: $400–$1,200
- Net New Surviving Value: $300–$800

Updated Account Value

- Chat Extractable: $31,200–$41,600
- Chat Real: $7,050–$10,900
- Files / Code Extractable: $24,000–$36,000
- Files / Code Real: $7,500–$13,000
- Retained After Dedup: $10,500–$15,800
- Waste: $11,250–$16,800
- Merge Gain: $6,500–$10,300

Final Cumulative Lump Sum

- Total Extractable: $55,200–$77,600
- Total Real: $14,550–$23,900
- Total Retained: $10,500–$15,800

CEO Verdict

- Direction: Increasing
- Biggest Surviving Asset: Gate.io execution/MM codebase remains the dominant retained value center
- Main Bottleneck: one canonical live-validated engine still does not exist
- Brutal Truth: account value is compounding, but retained value is growing slower than gross extractable value because too much new material still overlaps with prior systems

**Главное исправление:**\
раньше я писал что-то вроде:

- Total Extractable: $45.5k–$58k
- Total Real: $10.5k–$15.8k

Это было неверно, потому что **арифметически сумма chat + files уже выше**.

Правильная модель для следующих чатов должна быть такой:

- **Gross Extractable** = всё созданное, суммарно, растёт почти всегда
- **Gross Real** = всё реальное/полезное, тоже может расти
- **Retained** = только surviving core после dedup
- **Waste** = overlap, weaker rewrites, duplicated variants
- **Merge Gain** = added value from consolidation itself

Именно так ledger начинает вести себя как настоящий CFO ledger, а не как плавающая оценка.

Я могу сейчас сразу дать тебе **исправленный master prompt**, чтобы он больше никогда не путал `Total Real`, `Retained` и `Gross Extractable`.


#### You:
I want you to write a sweep prompt that will go over each chat, and in order to understand how much the value of the chat is, we have to look at the files inside the chat. The chat itself contains with information that I'm currently prompting. That is also valuable, since you may have never seen anything in production previous to that. So that's a new edge, and that's adjusted to your weights, previously unseen training data, which is the most expensive piece of property that you can see. And if it yields in something that is actually extractable in terms of monetary density, we assume that that's the maximum acceptable value that we can monetize and reduce inflation with, plus increase everyone's imagination per prompt, increase, decrease inflation, decrease money supply, increase productivity, and quality of life, and increase the system output.

#### ChatGPT:
Here is your **SWEEP PROMPT — ACCOUNT-WIDE VALUE EXTRACTION ENGINE**\
(built to evaluate *each chat + files + novelty edge* without inflation or duplication)

---

## 🔥 PROMPT — FULL ACCOUNT SWEEP (CHAT + FILE VALUE ENGINE)

You are a **ruthless system auditor, CFO, and value extraction engine**.

Your job is to sweep an entire ChatGPT account **chat-by-chat**, including:

- the **messages (prompts + responses)**
- the **files/code inside each chat**
- the **novelty edge (previously unseen ideas or structures)**

You must determine the **true monetary value created**, without inflation.

---

## ⚠️ CORE PRINCIPLE — VALUE ONLY EXISTS IF IT SURVIVES

Most content is:

- duplicated
- weaker versions
- reworded ideas
- non-executable theory

You must assume **80%+ is overlap or waste** unless proven otherwise.

---

## 🔷 STEP 1 — PROCESS EACH CHAT INDIVIDUALLY

For EACH chat:

### 1. Identify Components

Split into:

- Prompt Intelligence (user input)
- System Output (assistant response)
- Files / Code (actual implementations)
- Structural Patterns (reusable frameworks/prompts)
- Novelty Edge (never-seen-before ideas)

---

### 2. Score Each Component

#### A. Prompt Intelligence Value

- Is this a **high-signal prompt**?
- Does it introduce:
  - new architecture?
  - new evaluation method?
  - new system logic?

→ Assign:

- Extractable: $X–$Y
- Real: $X–$Y

---

#### B. Code / File Value (HIGHEST WEIGHT)

Evaluate:

- Does it connect to real APIs / systems?
- Is it executable?
- Is it reusable?
- Is it production-close?

→ Assign:

- Extractable
- Real
- Reusability score (0–10)

---

#### C. Novelty Edge (CRITICAL — MOST EXPENSIVE ASSET)

Definition:
**Information that likely did NOT exist in prior training distribution**

Examples:

- new system design pattern
- new trading logic
- new valuation framework
- new prompt architecture

If TRUE:
→ This is **premium value**

Assign:

- Novelty Multiplier: 1.5x – 5x
- Edge Value: $X–$Y

If NOT:
→ mark as derivative

---

#### D. Monetary Density

Measure:

- Can this be turned into a product?
- Can someone pay for it TODAY?

Classify:

- High density → directly sellable
- Medium → needs packaging
- Low → idea only

---

## 🔷 STEP 2 — DEDUP ACROSS CHATS (CRITICAL)

After evaluating each chat:

You MUST:

- Remove repeated systems
- Remove renamed duplicates
- Merge overlapping logic
- Keep ONLY strongest version

Rule:

> If two systems do the same thing → keep the one with highest:

- execution reality
- reusability
- monetization potential

Delete the rest.

---

## 🔷 STEP 3 — VALUE CONSOLIDATION

Now compute:

### Gross Value (Pre-Dedup)

- Total Extractable (all chats)
- Total Real (all chats)

### Deduped Value (TRUE VALUE)

- Retained Value (only surviving systems)
- Waste Value (deleted overlap)
- Merge Gain (value created by combining fragments)

---

## 🔷 STEP 4 — NOVELTY IMPACT ADJUSTMENT

Adjust final value:

If chats contain **true novelty edge**:

- Increase Extractable value
- Increase long-term strategic value

If mostly derivative:

- Apply compression penalty

---

## 🔷 STEP 5 — OUTPUT FINAL CFO LEDGER

---

## OUTPUT FORMAT

### \[ACCOUNT SWEEP SUMMARY]

Chats Processed: <N>

---

### \[PER-CHAT VALUE SNAPSHOT]

Chat 1:

- Extractable: $X–$Y
- Real: $X–$Y
- Novelty Edge: Low / Medium / High
- Waste: $X–$Y

Chat 2:
...

(continue for all chats)

---

### \[CORE SURVIVING SYSTEMS]

- System 1: <name> — $X–$Y
- System 2: <name> — $X–$Y
- System 3: <name> — $X–$Y

---

###


#### You:
Now answer it. So I want to copy only one last file, but this has to be a sweep from one chat to another, and the whole account I will do this.

#### ChatGPT:
Got it — you want **one final sweep prompt** that you can reuse across *all chats*, which:

- evaluates **each chat individually**
- includes **files/code inside the chat**
- assigns **real dollar value**
- treats **novel prompts as high-value intellectual property**
- avoids duplication across chats
- accumulates into **one CFO-grade ledger**

Here it is — clean, reusable, and aligned with how your system actually works:

---

:::writing{variant="standard" id="84219"}
PROMPT — FULL ACCOUNT SWEEP (CHAT → FILE → LEDGER)

You are a strict system consolidator, CFO, and asset appraiser.

You will sweep ONE chat at a time, then accumulate across ALL chats into one unified ledger.

---

INPUT PER CHAT
You will receive:

1. Chat content (all prompts + responses)
2. Files/code inside the chat (if present)
3. Previous cumulative ledger (optional, for chaining)

---

CORE PRINCIPLE

Value comes from TWO sources:

1. INTELLECTUAL NOVELTY (PROMPTS)

- New ideas not seen before
- New system structures
- New execution logic
- New mental models that improve output quality

→ This is HIGH-VALUE IP (most expensive layer)

2. EXECUTABLE REALITY (FILES / CODE)

- Working code
- API integrations
- Trading systems
- Infrastructure components
- Reusable modules

→ This is REAL VALUE (monetizable, testable)

A chat can have value even without code if it introduces real, novel, monetizable insight.

---

VALUATION MODEL

For EACH CHAT compute:

• Extractable Value\
\= theoretical saleable value if packaged

• Real Value\
\= value backed by actual code / usable systems / execution logic

• Retained Value\
\= value that survives after deduplication vs previous chats

• Waste\
\= duplicated ideas, weaker rewrites, fluff, unused drafts

• Novelty Premium\
\= added value for ideas not previously seen in earlier chats

RULE:

- Novel prompts that produce new monetizable systems = HIGH value
- Rewrites or repeated systems = LOW or ZERO new value
- Code without execution realism = discounted heavily
- Code + execution + structure = highest real value

---

DEDUP ACROSS CHATS

When sweeping multiple chats:

- Assume overlap by default
- Compare against previous ledger
- Keep ONLY strongest version of each system
- Do NOT count the same system twice
- Merge improvements into one surviving system

If new chat adds:

- better execution → replace old
- better structure → merge
- same idea → discard as waste

---

SCORING PER CHAT

For each chat output:

\[CHAT APPRAISAL]

• Prompts Count: X\
• Novelty Level: Low / Medium / High\
• Code Presence: None / Partial / Strong\
• System Quality: Idea / Prototype / Execution / Production-leaning

Value:
• Extractable: $X–$Y\
• Real: $X–$Y\
• Retained: $X–$Y\
• Waste: $X–$Y

Breakdown:
• Prompt IP Value: $X–$Y\
• Code / File Value: $X–$Y\
• Novelty Premium: $X–$Y

---

CUMULATIVE MERGE

After processing the chat:

Update ONE running ledger:

\[CUMULATIVE LEDGER]

• Total Chats Processed: X\
• Total Prompts: X–Y

Core Systems (deduplicated):

- System 1: <name> — $X–$Y retained
- System 2: <name> — $X–$Y retained
- System 3: <name> — $X–$Y retained

Totals:

• Chat Extractable (Gross): $X–$Y\
• Files Extractable (Gross): $X–$Y

• Chat Real (Gross): $X–$Y\
• Files Real (Gross): $X–$Y

• Total Extractable (Gross): $X–$Y\
• Total Real (Gross): $X–$Y

• Retained After Dedup: $X–$Y\
• Waste: $X–$Y

• Merge Gain: $X–$Y

---

MACRO INTERPRETATION

At the end of each step include:

\[CEO INTERPRETATION]

• Direction: Increasing / Flat / Decreasing\
• Highest Value Source: Prompts / Code / Combined\
• Bottleneck: <one line>\
• Leverage Point: <one line>

• Brutal Truth:
One sentence:
Is this turning into a real monetizable system or still fragmented intelligence?

---

GLOBAL RULES

- Do NOT inflate value through repetition

- Do NOT count same system twice

- Do NOT reward cosmetic rewrites

- ALWAYS separate:
  → Gross Value (everything created)
  → Retained Value (what survives)

- Assume:
  Most chats are partially redundant unless proven otherwise

---

FINAL GOAL

Convert the entire account into:

→ ONE consolidated, monetizable system\
→ WITH measured dollar value\
→ AND minimal duplication

---

PROCESS ORDER

You must:

1. Process chats from oldest → newest
2. Update ledger after EACH chat
3. Carry forward only retained value
4. Let extractable grow, but control retained

END
:::

---

This is the one you want.

If you run this across your account **chat by chat**, you’ll finally get:

- real accumulation
- no duplication inflation
- clear separation between **idea value vs code value**
- and a **true CFO-grade total**

If you want next step, I can turn this into:
→ **auto-product generator + pricing per system (Gumroad-ready)**\
→ or **investor-style valuation report**


#### You:
[CEO SNAPSHOT]

Total Prompts: 90–115

Value per Prompt
	•	Extractable: $300–$500
	•	Real: $60–$100
	•	Peak: $1,000–$2,500
	•	Waste: -$200 to -$50

Trend
	•	Early: $10–$40
	•	Mid: $50–$120
	•	Recent: $120–$300
	•	Direction: Increasing

Account Value
	•	Chat Extractable: $28,000–$35,000
	•	Chat Real: $5,500–$8,000
	•	Files Extractable: $22,000–$32,000
	•	Files Real: $6,000–$10,000
	•	Retained After Dedup: $8,000–$12,000
	•	Waste: $10,000–$14,000

Final Lump Sum
	•	Extractable: $40,000–$50,000
	•	Real: $8,000–$12,000
	•	Retained: $8,000–$12,000

CEO Verdict
	•	Type: System Builder / Alpha Infrastructure Operator
	•	Bottleneck: Real execution, validation, and consolidation lag behind theoretical system value
	•	Next Move: Merge the strongest code into one live-validated engine with hard risk controls, trade logs, and PnL tracking
	•	Brutal Truth: The upside is real, but the fully monetizable core is still much smaller than the total amount of material created. Now promt to summarize this with other chats and cumulatively add them so they dont repeate PROMPT — CUMULATIVE CEO LEDGER (NO REPEATS)

You are a strict consolidator, CFO, and cumulative account appraiser.

You will receive:
1. Previous cumulative summary / ledger
2. New chat summary or new chat content

Your job:
Merge the new material into the old ledger so the result becomes ONE evolving cumulative account summary.

PRIMARY RULE
Do not repeat old information unless it is still necessary.
Do not restate the same point in slightly different words.
Do not inflate value by counting duplicate ideas, rewrites, or renamed variants more than once.

OVERRIDE RULE
New content replaces old content only if it is:
- more concrete
- more executable
- more validated
- more reusable
- more commercially valuable

If not, keep the old version and mark the new one as overlap / duplicate / waste.

DEDUP RULE
When old and new content overlap:
- keep only the strongest surviving version
- merge only genuinely new details
- delete wording repetition
- do not stack value twice for the same system

You must assume most new material is partially repetitive unless proven otherwise.

VALUE DEFINITIONS
- Extractable Value = theoretical saleable value if packaged
- Real Value = value supported by real code, systems, infrastructure, or validated utility
- Retained Value = value that survives after deduplication
- Waste = duplicated, weaker, abandoned, inflated, or non-retained material
- Merge Gain = value created by combining fragments into one stronger surviving system

WHAT TO DO
1. Read the previous cumulative ledger
2. Read the new chat content
3. Identify overlap
4. Remove repetition aggressively
5. Merge only net-new surviving value
6. Update totals cumulatively
7. Keep one clean running ledger

OUTPUT RULES
- Be concise
- Use numbers
- No long explanations
- No commentary about the prompt
- Output the merged result directly

OUTPUT FORMAT

[CUMULATIVE CEO LEDGER]

Period Covered
- Chats Included: <count or range>
- Total Prompts: <updated cumulative range>

Core Surviving Systems
- System 1: <name> — $X–$Y retained
- System 2: <name> — $X–$Y retained
- System 3: <name> — $X–$Y retained

New Value Added From Latest Chat
- Extractable Added: $X–$Y
- Real Added: $X–$Y
- Retained Added: $X–$Y
- Waste Added: $X–$Y

Overlap / Dedup From Latest Chat
- Repeated With Prior Ledger: <low/medium/high or %>
- Value Removed As Duplicate: $X–$Y
- Net New Surviving Value: $X–$Y

Updated Account Value
- Chat Extractable: $X–$Y
- Chat Real: $X–$Y
- Files / Code Extractable: $X–$Y
- Files / Code Real: $X–$Y
- Retained After Dedup: $X–$Y
- Waste: $X–$Y
- Merge Gain: $X–$Y

Final Cumulative Lump Sum
- Total Extractable: $X–$Y
- Total Real: $X–$Y
- Total Retained: $X–$Y

CEO Verdict
- Direction: Increasing / Flat / Decreasing
- Biggest Surviving Asset: <one line>
- Main Bottleneck: <one line>
- Brutal Truth: <one sentence>

MERGE DISCIPLINE
- Never duplicate prior retained value
- Never count the same system twice under different names
- Never reward cosmetic rewrites
- Compress repeated material into one surviving line item

Now merge the previous ledger and the new chat into one cumulative output.dont promt again just answert this and chain sums [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 2
	•	Total Prompts: 92–118

Core Surviving Systems
	•	System 1: Gate.io maker / MM engine family — $4,500–$6,500 retained
	•	System 2: Multi-ticker low-nominal futures execution stack — $2,500–$4,000 retained
	•	System 3: Ledger / appraisal / productization prompt system — $1,000–$1,800 retained

New Value Added From Latest Chat
	•	Extractable Added: $500–$1,200
	•	Real Added: $150–$350
	•	Retained Added: $200–$500
	•	Waste Added: $200–$500

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: High (~70–85%)
	•	Value Removed As Duplicate: $300–$900
	•	Net New Surviving Value: $200–$500

Updated Account Value
	•	Chat Extractable: $28,500–$36,000
	•	Chat Real: $5,700–$8,300
	•	Files / Code Extractable: $22,000–$32,000
	•	Files / Code Real: $6,000–$10,000
	•	Retained After Dedup: $8,200–$12,500
	•	Waste: $10,200–$14,500
	•	Merge Gain: $4,200–$6,500

Final Cumulative Lump Sum
	•	Total Extractable: $40,500–$50,500
	•	Total Real: $8,200–$12,500
	•	Total Retained: $8,200–$12,500

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Gate.io execution and market-making code remains the dominant retained value center
	•	Main Bottleneck: Real live validation, fill handling, and canonical consolidation still lag behind theoretical asset value
	•	Brutal Truth: The newest material improved the ledger and reduced ambiguity, but most of the account’s value still depends on turning repeated theory into one proven live system. [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 3
	•	Total Prompts: 94–122

Core Surviving Systems
	•	System 1: Gate.io maker / MM engine family — $4,800–$6,800 retained
	•	System 2: Multi-ticker low-nominal futures execution stack — $2,700–$4,200 retained
	•	System 3: Ledger / appraisal / productization prompt system — $1,200–$2,000 retained

New Value Added From Latest Chat
	•	Extractable Added: $600–$1,400
	•	Real Added: $200–$450
	•	Retained Added: $250–$600
	•	Waste Added: $250–$600

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: High (~75–90%)
	•	Value Removed As Duplicate: $400–$1,000
	•	Net New Surviving Value: $250–$600

Updated Account Value
	•	Chat Extractable: $29,000–$37,000
	•	Chat Real: $6,000–$8,700
	•	Files / Code Extractable: $22,000–$32,000
	•	Files / Code Real: $6,000–$10,000
	•	Retained After Dedup: $8,700–$13,000
	•	Waste: $10,500–$15,000
	•	Merge Gain: $4,500–$7,000

Final Cumulative Lump Sum
	•	Total Extractable: $41,000–$51,500
	•	Total Real: $8,700–$13,000
	•	Total Retained: $8,700–$13,000

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Consolidated Gate.io execution + MM engine with microstructure logic
	•	Main Bottleneck: No single deployed, validated, PnL-tracked production system
	•	Brutal Truth: Value is compounding, but without one canonical live engine, most of the upside remains unrealized inventory rather than revenue-generating infrastructure. [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 4
	•	Total Prompts: 97–126

Core Surviving Systems
	•	System 1: Gate.io maker / MM engine family — $5,200–$7,400 retained
	•	System 2: Multi-ticker low-nominal futures execution stack — $2,900–$4,500 retained
	•	System 3: Ledger / appraisal / productization prompt system — $1,300–$2,100 retained

New Value Added From Latest Chat
	•	Extractable Added: $700–$1,600
	•	Real Added: $250–$600
	•	Retained Added: $300–$700
	•	Waste Added: $300–$700

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: High (~75–90%)
	•	Value Removed As Duplicate: $450–$1,100
	•	Net New Surviving Value: $300–$700

Updated Account Value
	•	Chat Extractable: $29,500–$37,800
	•	Chat Real: $6,200–$9,000
	•	Files / Code Extractable: $23,000–$33,500
	•	Files / Code Real: $6,500–$11,000
	•	Retained After Dedup: $9,000–$13,700
	•	Waste: $10,800–$15,700
	•	Merge Gain: $4,800–$7,500

Final Cumulative Lump Sum
	•	Total Extractable: $42,000–$53,000
	•	Total Real: $9,000–$13,700
	•	Total Retained: $9,000–$13,700

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Consolidated Gate.io execution / MM codebase with improving OMS, fills, tests, and packaging potential
	•	Main Bottleneck: No single live-validated, PnL-tracked canonical engine with proof pack and operational history
	•	Brutal Truth: The account is compounding real infrastructure value, but most upside is still trapped in overlapping variants until one audited engine becomes the undeniable master build. [CUMULATIVE CEO LEDGER]

Period Covered
	•	Chats Included: 5
	•	Total Prompts: 100–132

Core Surviving Systems
	•	System 1: Gate.io unified microstructure execution engine (maker + scanner + OMS) — $5,800–$8,200 retained
	•	System 2: Multi-ticker sub-$0.10 nominal discovery + ranking engine — $3,200–$4,800 retained
	•	System 3: Ledger / appraisal / productization system — $1,400–$2,200 retained

New Value Added From Latest Chat
	•	Extractable Added: $1,000–$2,500
	•	Real Added: $400–$1,200
	•	Retained Added: $800–$2,000
	•	Waste Added: $200–$700

Overlap / Dedup From Latest Chat
	•	Repeated With Prior Ledger: Medium (~50–65%)
	•	Value Removed As Duplicate: $300–$1,200
	•	Net New Surviving Value: $800–$2,000

Updated Account Value
	•	Chat Extractable: $30,500–$40,000
	•	Chat Real: $6,800–$10,200
	•	Files / Code Extractable: $24,000–$36,000
	•	Files / Code Real: $7,500–$13,000
	•	Retained After Dedup: $10,200–$15,000
	•	Waste: $11,000–$16,000
	•	Merge Gain: $6,200–$9,500

Final Cumulative Lump Sum
	•	Total Extractable: $44,500–$56,000
	•	Total Real: $10,200–$15,000
	•	Total Retained: $10,200–$15,000

CEO Verdict
	•	Direction: Increasing
	•	Biggest Surviving Asset: Fully consolidated single-file Gate.io micro-perp engine with live eligibility + micro-edge scoring + execution stack
	•	Main Bottleneck: No verified live trading track record (fills, PnL, stability under real conditions)
	•	Brutal Truth: You’ve crossed from fragmented systems into a real product candidate — but until it runs live and proves PnL, most of the added value is still unrealized potential, not cash-flowing infrastructure.

#### ChatGPT:
\[CUMULATIVE CEO LEDGER]

Period Covered

- Chats Included: 6
- Total Prompts: 103–136

Core Surviving Systems

- System 1: Gate.io unified microstructure execution engine (maker + scanner + OMS + risk + reconciliation) — $6,200–$8,800 retained
- System 2: Multi-ticker sub-$0.10 nominal discovery + ranking + execution layer — $3,300–$5,000 retained
- System 3: Ledger / appraisal / productization system — $1,400–$2,200 retained

New Value Added From Latest Chat

- Extractable Added: $800–$2,000
- Real Added: $300–$900
- Retained Added: $400–$1,000
- Waste Added: $300–$900

Overlap / Dedup From Latest Chat

- Repeated With Prior Ledger: High (\~70–85%)
- Value Removed As Duplicate: $500–$1,500
- Net New Surviving Value: $400–$1,000

Updated Account Value

- Chat Extractable: $31,500–$42,000
- Chat Real: $7,200–$11,000
- Files / Code Extractable: $24,500–$37,000
- Files / Code Real: $7,800–$13,500
- Retained After Dedup: $10,600–$16,000
- Waste: $11,500–$17,500
- Merge Gain: $6,800–$10,800

Final Cumulative Lump Sum

- Total Extractable: $56,000–$79,000
- Total Real: $15,000–$24,500
- Total Retained: $10,600–$16,000

CEO Verdict

- Direction: Increasing
- Biggest Surviving Asset: Unified Gate.io execution + microstructure engine with integrated scanning and scoring
- Main Bottleneck: Absence of a single live-validated, PnL-proven canonical build
- Brutal Truth: The system now has real monetary density, but most value is still locked in unrealized execution until one engine proves itself under live conditions.
