# Оценка стоимости кода

#### You:
Apparaisr this in dollars and ruaaisn #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gate_maker_ai_engine_single_file.py

Single-file Gate.io futures maker engine with:
- maker entry at best bid / best ask
- linked exit order after fill / position open
- local rule model + OpenRouter + Groq voting
- SQLite persistence
- restart-safe state
- embedded Flask UI
- no simulated core execution
- optional paper mode
- one-file IDE deployment

INSTALL
-------
pip install requests pandas pandas_ta numpy python-dotenv flask

RUN
---
python gate_maker_ai_engine_single_file.py

ENV
---
GATE_API_KEY=...
GATE_API_SECRET=...
GATE_BASE_URL=https://api.gateio.ws/api/v4
GATE_SETTLE=usdt
GATE_CONTRACT=BTC_USDT

OPENROUTER_API_KEY=...
OPENROUTER_MODEL=openai/gpt-4.1-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions

GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions

LIVE_TRADING=false
ALLOW_NEW_ENTRIES=true
ALLOW_AI=true

INTERVAL=15m
BARS_LIMIT=800
LOOP_SECONDS=10

RISK_USD=25
LEVERAGE=2

MIN_SIGNAL_SCORE=0.18
ENTRY_ORDER_TTL_SECONDS=20
EXIT_ORDER_TTL_SECONDS=20
REPRICE_THRESHOLD_TICKS=1

TP_ATR_MULT=1.2
SL_ATR_MULT=0.8

WALKFORWARD_BARS=120
MIN_PASS_RATE=0.54
MIN_AVG_R=0.03
MIN_TRADES=20

REQUEST_TIMEOUT=20
DB_PATH=gate_maker_ai_engine.db
APP_HOST=127.0.0.1
APP_PORT=8787

NOTES
-----
- Entry orders are post-only maker orders.
- Exit orders are also post-only maker orders by default.
- This file persists local state and reconciles against exchange orders / positions.
- Keep LIVE_TRADING=false until you validate everything yourself.
"""

from __future__ import annotations

import os
import sys
import json
import time
import math
import hmac
import sqlite3
import signal
import hashlib
import logging
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import pandas_ta as ta
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

load_dotenv()

# ============================================================
# Config
# ============================================================

@dataclass
class Config:
    gate_api_key: str = os.getenv("GATE_API_KEY", "")
    gate_api_secret: str = os.getenv("GATE_API_SECRET", "")
    gate_base_url: str = os.getenv("GATE_BASE_URL", "https://api.gateio.ws/api/v4").rstrip("/")
    settle: str = os.getenv("GATE_SETTLE", "usdt").lower()
    contract: str = os.getenv("GATE_CONTRACT", "BTC_USDT")

    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")

    live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
    allow_new_entries: bool = os.getenv("ALLOW_NEW_ENTRIES", "true").lower() == "true"
    allow_ai: bool = os.getenv("ALLOW_AI", "true").lower() == "true"

    interval: str = os.getenv("INTERVAL", "15m")
    bars_limit: int = int(os.getenv("BARS_LIMIT", "800"))
    loop_seconds: int = int(os.getenv("LOOP_SECONDS", "10"))

    risk_usd: float = float(os.getenv("RISK_USD", "25"))
    leverage: int = int(os.getenv("LEVERAGE", "2"))

    min_signal_score: float = float(os.getenv("MIN_SIGNAL_SCORE", "0.18"))
    entry_order_ttl_seconds: int = int(os.getenv("ENTRY_ORDER_TTL_SECONDS", "20"))
    exit_order_ttl_seconds: int = int(os.getenv("EXIT_ORDER_TTL_SECONDS", "20"))
    reprice_threshold_ticks: int = int(os.getenv("REPRICE_THRESHOLD_TICKS", "1"))

    tp_atr_mult: float = float(os.getenv("TP_ATR_MULT", "1.2"))
    sl_atr_mult: float = float(os.getenv("SL_ATR_MULT", "0.8"))

    walkforward_bars: int = int(os.getenv("WALKFORWARD_BARS", "120"))
    min_pass_rate: float = float(os.getenv("MIN_PASS_RATE", "0.54"))
    min_avg_r: float = float(os.getenv("MIN_AVG_R", "0.03"))
    min_trades: int = int(os.getenv("MIN_TRADES", "20"))

    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
    db_path: str = os.getenv("DB_PATH", "gate_maker_ai_engine.db")

    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8787"))


CFG = Config()

# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("gate-maker-engine")


def now_ts() -> float:
    return time.time()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        return float(x)
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def json_s(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


# ============================================================
# SQLite persistence
# ============================================================

class DB:
    def __init__(self, path: str):
        self.path = path
        self.lock = threading.Lock()
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._conn() as conn:
            cur = conn.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS service_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                level TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                decision_side TEXT NOT NULL,
                decision_confidence REAL NOT NULL,
                final_score REAL NOT NULL,
                local_side TEXT,
                local_confidence REAL,
                local_parts_json TEXT,
                openrouter_side TEXT,
                openrouter_confidence REAL,
                openrouter_reason TEXT,
                groq_side TEXT,
                groq_confidence REAL,
                groq_reason TEXT,
                memory_bias REAL,
                walk_pass_rate REAL,
                walk_avg_r REAL,
                walk_trades INTEGER,
                walk_allowed_live INTEGER,
                snapshot_json TEXT,
                why_json TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                symbol TEXT NOT NULL,
                role TEXT NOT NULL,
                side TEXT NOT NULL,
                state TEXT NOT NULL,
                local_position_id INTEGER,
                decision_id INTEGER,
                requested_price REAL,
                requested_size INTEGER,
                reduce_only INTEGER NOT NULL,
                tif TEXT,
                text_tag TEXT,
                exchange_order_id TEXT,
                exchange_status TEXT,
                exchange_left INTEGER,
                exchange_fill_price REAL,
                exchange_finish_as TEXT,
                request_json TEXT,
                response_json TEXT,
                notes TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opened_ts TEXT NOT NULL,
                closed_ts TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                size INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL,
                tp REAL,
                sl REAL,
                atr REAL,
                decision_id INTEGER,
                entry_order_row_id INTEGER,
                exit_order_row_id INTEGER,
                exit_price REAL,
                realized_pnl_pct REAL,
                notes TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS kv_state (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL
            )
            """)

            conn.commit()

    def event(self, level: str, kind: str, payload: Dict[str, Any]) -> None:
        row = (utc_now_iso(), level, kind, json.dumps(payload, ensure_ascii=False))
        with self.lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO service_events (ts, level, kind, payload_json) VALUES (?, ?, ?, ?)",
                row,
            )
            conn.commit()

    def insert_decision(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        sql = f"INSERT INTO decisions ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
        with self.lock, self._conn() as conn:
            cur = conn.execute(sql, vals)
            conn.commit()
            return int(cur.lastrowid)

    def insert_order(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        sql = f"INSERT INTO orders ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
        with self.lock, self._conn() as conn:
            cur = conn.execute(sql, vals)
            conn.commit()
            return int(cur.lastrowid)

    def update_order(self, row_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        keys = list(updates.keys())
        vals = [updates[k] for k in keys] + [row_id]
        set_clause = ",".join([f"{k}=?" for k in keys])
        with self.lock, self._conn() as conn:
            conn.execute(f"UPDATE orders SET {set_clause} WHERE id=?", vals)
            conn.commit()

    def open_position(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        sql = f"INSERT INTO positions ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
        with self.lock, self._conn() as conn:
            cur = conn.execute(sql, vals)
            conn.commit()
            return int(cur.lastrowid)

    def update_position(self, row_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        keys = list(updates.keys())
        vals = [updates[k] for k in keys] + [row_id]
        set_clause = ",".join([f"{k}=?" for k in keys])
        with self.lock, self._conn() as conn:
            conn.execute(f"UPDATE positions SET {set_clause} WHERE id=?", vals)
            conn.commit()

    def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
                (symbol,),
            ).fetchone()
            return dict(row) if row else None

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE symbol=? AND state IN ('working','submitted','open_local') ORDER BY id DESC",
                    (symbol,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE state IN ('working','submitted','open_local') ORDER BY id DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def get_latest_working_order(self, symbol: str, role: str) -> Optional[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE symbol=? AND role=? AND state IN ('working','submitted','open_local') ORDER BY id DESC LIMIT 1",
                (symbol, role),
            ).fetchone()
            return dict(row) if row else None

    def recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            rows = conn.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            rows = conn.execute("SELECT * FROM service_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def positions(self, only_open: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            if only_open:
                rows = conn.execute(
                    "SELECT * FROM positions WHERE status='open' ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM positions ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def recent_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.lock, self._conn() as conn:
            rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def set_state(self, key: str, val: Dict[str, Any]) -> None:
        with self.lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO kv_state (k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                (key, json.dumps(val, ensure_ascii=False)),
            )
            conn.commit()

    def get_state(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self.lock, self._conn() as conn:
            row = conn.execute("SELECT v FROM kv_state WHERE k=?", (key,)).fetchone()
            if not row:
                return default or {}
            try:
                return json.loads(row["v"])
            except Exception:
                return default or {}


DBI = DB(CFG.db_path)

# ============================================================
# Gate.io REST client
# ============================================================

class GateClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session = requests.Session()

    def _sign_headers(
        self,
        method: str,
        path: str,
        query_string: str = "",
        body: str = "",
    ) -> Dict[str, str]:
        ts = str(int(time.time()))
        body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
        sign_str = f"{method.upper()}\n/api/v4{path}\n{query_string}\n{body_hash}\n{ts}"
        sign = hmac.new(
            self.cfg.gate_api_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            digestmod=hashlib.sha512,
        ).hexdigest()
        return {
            "KEY": self.cfg.gate_api_key,
            "Timestamp": ts,
            "SIGN": sign,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_public(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.cfg.gate_base_url}{path}"
        r = self.session.get(url, params=params or {}, timeout=self.cfg.request_timeout)
        r.raise_for_status()
        return r.json()

    def request_private(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        params = params or {}
        payload = payload or {}
        query_string = urlencode(params)
        body = json.dumps(payload, separators=(",", ":")) if payload else ""
        headers = self._sign_headers(method, path, query_string, body)
        url = f"{self.cfg.gate_base_url}{path}"
        r = self.session.request(
            method=method.upper(),
            url=url,
            params=params,
            data=body if body else None,
            headers=headers,
            timeout=self.cfg.request_timeout,
        )
        r.raise_for_status()
        return r.json() if r.text.strip() else {}

    def fetch_candles(self, contract: str, interval: str, limit: int = 500) -> pd.DataFrame:
        path = f"/futures/{self.cfg.settle}/candlesticks"
        raw = self.get_public(path, params={"contract": contract, "interval": interval, "limit": min(limit, 2000)})
        if not isinstance(raw, list) or not raw:
            raise RuntimeError("No candle data returned")

        rows = []
        for item in raw:
            if isinstance(item, dict):
                rows.append({
                    "t": item.get("t"),
                    "o": item.get("o"),
                    "h": item.get("h"),
                    "l": item.get("l"),
                    "c": item.get("c"),
                    "v": item.get("v"),
                })
            elif isinstance(item, list) and len(item) >= 6:
                rows.append({
                    "t": item[0],
                    "v": item[1],
                    "c": item[2],
                    "h": item[3],
                    "l": item[4],
                    "o": item[5],
                })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
        for col in ["o", "h", "l", "c", "v"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna().sort_values("timestamp").reset_index(drop=True)

    def fetch_ticker(self, contract: str) -> Dict[str, Any]:
        path = f"/futures/{self.cfg.settle}/tickers"
        data = self.get_public(path, params={"contract": contract})
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        return {}

    def fetch_contract_specs(self, contract: str) -> Dict[str, Any]:
        path = f"/futures/{self.cfg.settle}/contracts/{contract}"
        return self.get_public(path)

    def fetch_order_book(self, contract: str, limit: int = 1) -> Dict[str, Any]:
        path = f"/futures/{self.cfg.settle}/order_book"
        return self.get_public(path, params={"contract": contract, "limit": limit})

    def list_open_orders(self, contract: Optional[str] = None) -> List[Dict[str, Any]]:
        path = f"/futures/{self.cfg.settle}/orders"
        params: Dict[str, Any] = {"status": "open"}
        if contract:
            params["contract"] = contract
        data = self.request_private("GET", path, params=params)
        return data if isinstance(data, list) else []

    def get_order(self, order_id: str) -> Dict[str, Any]:
        path = f"/futures/{self.cfg.settle}/orders/{order_id}"
        data = self.request_private("GET", path)
        return data if isinstance(data, dict) else {}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        path = f"/futures/{self.cfg.settle}/orders/{order_id}"
        return self.request_private("DELETE", path)

    def list_positions(self) -> List[Dict[str, Any]]:
        path = f"/futures/{self.cfg.settle}/positions"
        data = self.request_private("GET", path)
        return data if isinstance(data, list) else []

    def place_limit_post_only(
        self,
        contract: str,
        size: int,
        price: float,
        text_tag: str,
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        path = f"/futures/{self.cfg.settle}/orders"
        payload = {
            "contract": contract,
            "size": size,
            "price": f"{price:.10f}",
            "tif": "poc",
            "text": text_tag[:28],
            "reduce_only": reduce_only,
        }
        return self.request_private("POST", path, payload=payload)


# ============================================================
# Indicators and snapshot
# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()

    x["ema_9"] = ta.ema(x["close"], length=9)
    x["ema_21"] = ta.ema(x["close"], length=21)
    x["sma_20"] = ta.sma(x["close"], length=20)
    x["sma_50"] = ta.sma(x["close"], length=50)
    x["rsi_14"] = ta.rsi(x["close"], length=14)
    x["atr_14"] = ta.atr(x["high"], x["low"], x["close"], length=14)

    adx = ta.adx(x["high"], x["low"], x["close"], length=14)
    if adx is not None and not adx.empty:
        x["adx_14"] = adx["ADX_14"]

    bb = ta.bbands(x["close"], length=20, std=2)
    if bb is not None and not bb.empty:
        x["bb_lower"] = bb["BBL_20_2.0"]
        x["bb_mid"] = bb["BBM_20_2.0"]
        x["bb_upper"] = bb["BBU_20_2.0"]
        x["bb_width"] = (x["bb_upper"] - x["bb_lower"]) / x["bb_mid"]

    x["obv"] = ta.obv(x["close"], x["volume"])
    x["ret_1"] = x["close"].pct_change(1)
    x["ret_4"] = x["close"].pct_change(4)
    x["ret_16"] = x["close"].pct_change(16)
    x["vol_z"] = (x["volume"] - x["volume"].rolling(20).mean()) / x["volume"].rolling(20).std()
    x["dist_ema21_atr"] = (x["close"] - x["ema_21"]) / x["atr_14"]
    x["trend_gap"] = (x["ema_9"] - x["ema_21"]) / x["close"]

    return x


def latest_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
    row = df.iloc[-1]
    return {
        "timestamp": str(row["timestamp"]),
        "close": safe_float(row["close"]),
        "ema_9": safe_float(row.get("ema_9")),
        "ema_21": safe_float(row.get("ema_21")),
        "sma_20": safe_float(row.get("sma_20")),
        "sma_50": safe_float(row.get("sma_50")),
        "rsi_14": safe_float(row.get("rsi_14")),
        "atr_14": safe_float(row.get("atr_14")),
        "adx_14": safe_float(row.get("adx_14")),
        "bb_width": safe_float(row.get("bb_width")),
        "obv": safe_float(row.get("obv")),
        "ret_1": safe_float(row.get("ret_1")),
        "ret_4": safe_float(row.get("ret_4")),
        "ret_16": safe_float(row.get("ret_16")),
        "vol_z": safe_float(row.get("vol_z")),
        "dist_ema21_atr": safe_float(row.get("dist_ema21_atr")),
        "trend_gap": safe_float(row.get("trend_gap")),
    }


# ============================================================
# Local model
# ============================================================

def local_rule_score(s: Dict[str, Any]) -> Tuple[str, float, Dict[str, float]]:
    parts: Dict[str, float] = {}

    parts["trend"] = 0.0
    if s["ema_9"] > s["ema_21"]:
        parts["trend"] += 0.8
    elif s["ema_9"] < s["ema_21"]:
        parts["trend"] -= 0.8

    parts["rsi"] = 0.0
    if s["rsi_14"] < 32:
        parts["rsi"] += 0.7
    elif s["rsi_14"] > 68:
        parts["rsi"] -= 0.7

    parts["momentum"] = float(np.clip(s["ret_4"] * 100, -1.0, 1.0))

    parts["distance"] = 0.0
    if s["dist_ema21_atr"] < -1.5:
        parts["distance"] += 0.5
    elif s["dist_ema21_atr"] > 1.5:
        parts["distance"] -= 0.5

    parts["volume"] = float(np.clip(s["vol_z"] / 3.0, -0.4, 0.4))

    parts["trend_strength"] = 0.0
    if s["adx_14"] > 22 and s["ema_9"] > s["ema_21"]:
        parts["trend_strength"] += 0.2
    elif s["adx_14"] > 22 and s["ema_9"] < s["ema_21"]:
        parts["trend_strength"] -= 0.2

    score = sum(parts.values())
    if score > 0.35:
        side = "buy"
    elif score < -0.35:
        side = "sell"
    else:
        side = "hold"

    conf = min(abs(score) / 2.0, 0.95)
    return side, conf, parts


# ============================================================
# Memory bias
# ============================================================

def load_memory_df(limit: int) -> pd.DataFrame:
    rows = DBI.recent_decisions(limit=limit)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def memory_bias(snapshot: Dict[str, Any], decisions_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    if decisions_df.empty:
        return 0.0, {"similar_count": 0, "avg_score": 0.0}

    d = decisions_df.copy()
    numeric_cols = ["decision_confidence", "rsi_14", "dist_ema21_atr", "trend_gap", "vol_z", "walk_avg_r"]
    for col in numeric_cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")

    if "decision_side" not in d.columns:
        return 0.0, {"similar_count": 0, "avg_score": 0.0}

    d["learn_score"] = d["walk_avg_r"].fillna(0.0)

    similar = d[
        (d["rsi_14"].sub(snapshot["rsi_14"]).abs() <= 8)
        & (d["dist_ema21_atr"].sub(snapshot["dist_ema21_atr"]).abs() <= 1.0)
        & (d["trend_gap"].sub(snapshot["trend_gap"]).abs() <= 0.006)
        & (d["vol_z"].sub(snapshot["vol_z"]).abs() <= 1.5)
        & (d["decision_side"].isin(["buy", "sell"]))
    ].copy()

    if similar.empty:
        return 0.0, {"similar_count": 0, "avg_score": 0.0}

    buy_avg = similar.loc[similar["decision_side"] == "buy", "learn_score"].mean()
    sell_avg = similar.loc[similar["decision_side"] == "sell", "learn_score"].mean()
    buy_avg = 0.0 if pd.isna(buy_avg) else float(buy_avg)
    sell_avg = 0.0 if pd.isna(sell_avg) else float(sell_avg)

    bias = float(np.clip(buy_avg - sell_avg, -0.75, 0.75))
    return bias, {
        "similar_count": int(len(similar)),
        "buy_avg_r": buy_avg,
        "sell_avg_r": sell_avg,
        "avg_score": float(similar["learn_score"].mean()),
    }


# ============================================================
# AI voting
# ============================================================

def build_ai_prompt(
    symbol: str,
    interval: str,
    snapshot: Dict[str, Any],
    local_side: str,
    local_conf: float,
    local_parts: Dict[str, float],
    mem_bias: float,
) -> str:
    return f"""
Return ONLY valid JSON with schema:
{{
  "side": "buy" | "sell" | "hold",
  "confidence": 0.0 to 1.0,
  "reason_short": "one short paragraph",
  "weights": {{
    "trend": number,
    "momentum": number,
    "mean_reversion": number,
    "volatility": number,
    "volume": number,
    "memory": number
  }},
  "risk_flags": ["..."]
}}

Context:
symbol={symbol}
interval={interval}

Latest snapshot:
{json.dumps(snapshot, ensure_ascii=False)}

Local model:
side={local_side}
confidence={local_conf:.4f}
parts={json.dumps(local_parts, ensure_ascii=False)}

Memory bias:
{mem_bias:.4f}

Rules:
- Prefer hold for mixed signals.
- Confidence above 0.75 only for unusually strong setups.
- No markdown.
""".strip()


def parse_ai_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass

    return {
        "side": "hold",
        "confidence": 0.0,
        "reason_short": f"parse_error: {text[:200]}",
        "weights": {},
        "risk_flags": ["parse_error"],
    }


def call_openrouter(prompt: str) -> Dict[str, Any]:
    if not CFG.allow_ai or not CFG.openrouter_api_key:
        return {
            "side": "hold",
            "confidence": 0.0,
            "reason_short": "openrouter disabled or missing key",
            "weights": {},
            "risk_flags": ["disabled"],
        }
    headers = {
        "Authorization": f"Bearer {CFG.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": CFG.openrouter_model,
        "messages": [
            {"role": "system", "content": "You are a structured trading signal analyst."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 350,
    }
    r = requests.post(CFG.openrouter_base_url, headers=headers, json=payload, timeout=CFG.request_timeout)
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    return parse_ai_json(text)


def call_groq(prompt: str) -> Dict[str, Any]:
    if not CFG.allow_ai or not CFG.groq_api_key:
        return {
            "side": "hold",
            "confidence": 0.0,
            "reason_short": "groq disabled or missing key",
            "weights": {},
            "risk_flags": ["disabled"],
        }
    headers = {
        "Authorization": f"Bearer {CFG.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": CFG.groq_model,
        "messages": [
            {"role": "system", "content": "You are a structured trading signal analyst."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 350,
    }
    r = requests.post(CFG.groq_base_url, headers=headers, json=payload, timeout=CFG.request_timeout)
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    return parse_ai_json(text)


def signed_vote(side: str, conf: float) -> float:
    side = (side or "hold").strip().lower()
    conf = clamp(conf, 0.0, 1.0)
    if side == "buy":
        return conf
    if side == "sell":
        return -conf
    return 0.0


def ensemble_decision(
    local_side: str,
    local_conf: float,
    or_vote: Dict[str, Any],
    gr_vote: Dict[str, Any],
    mem_bias: float,
) -> Tuple[str, float, float, Dict[str, Any]]:
    local_score = signed_vote(local_side, local_conf)
    or_score = signed_vote(or_vote.get("side", "hold"), safe_float(or_vote.get("confidence")))
    gr_score = signed_vote(gr_vote.get("side", "hold"), safe_float(gr_vote.get("confidence")))

    final_score = (
        0.40 * local_score +
        0.30 * or_score +
        0.30 * gr_score +
        0.20 * mem_bias
    )
    final_score = float(clamp(final_score, -1.0, 1.0))

    if final_score > CFG.min_signal_score:
        side = "buy"
    elif final_score < -CFG.min_signal_score:
        side = "sell"
    else:
        side = "hold"

    conf = min(abs(final_score), 0.95)
    why = {
        "local_score": local_score,
        "openrouter_score": or_score,
        "groq_score": gr_score,
        "memory_bias": mem_bias,
        "final_score": final_score,
        "openrouter_reason": or_vote.get("reason_short", ""),
        "groq_reason": gr_vote.get("reason_short", ""),
    }
    return side, conf, final_score, why


# ============================================================
# Walk-forward gate
# ============================================================

def simulate_trade_on_bar(
    df: pd.DataFrame,
    idx: int,
    side: str,
    tp_mult: float,
    sl_mult: float,
) -> Optional[Dict[str, Any]]:
    if idx >= len(df) - 2:
        return None

    row = df.iloc[idx]
    entry = safe_float(row["close"])
    atr = safe_float(row["atr_14"])
    if atr <= 0 or side not in {"buy", "sell"}:
        return None

    tp = entry + atr * tp_mult if side == "buy" else entry - atr * tp_mult
    sl = entry - atr * sl_mult if side == "buy" else entry + atr * sl_mult

    for j in range(idx + 1, min(idx + 13, len(df))):
        bar = df.iloc[j]
        high = safe_float(bar["high"])
        low = safe_float(bar["low"])

        if side == "buy":
            if low <= sl:
                exit_price = sl
                outcome = "sl"
                break
            if high >= tp:
                exit_price = tp
                outcome = "tp"
                break
        else:
            if high >= sl:
                exit_price = sl
                outcome = "sl"
                break
            if low <= tp:
                exit_price = tp
                outcome = "tp"
                break
    else:
        bar = df.iloc[min(idx + 12, len(df) - 1)]
        exit_price = safe_float(bar["close"])
        outcome = "timeout"

    gross = (exit_price - entry) / atr if side == "buy" else (entry - exit_price) / atr
    return {"net_r": gross, "outcome": outcome}


def walkforward_gate(df: pd.DataFrame, decisions_df: pd.DataFrame) -> Dict[str, Any]:
    start = max(60, len(df) - CFG.walkforward_bars)
    trades = []

    for idx in range(start, len(df) - 2):
        s = latest_snapshot(df.iloc[: idx + 1])
        local_side, local_conf, _ = local_rule_score(s)
        mem_bias, _ = memory_bias(s, decisions_df)
        local_score = signed_vote(local_side, local_conf) + 0.2 * mem_bias

        if local_score > 0.20:
            side = "buy"
        elif local_score < -0.20:
            side = "sell"
        else:
            side = "hold"

        if side == "hold":
            continue

        trade = simulate_trade_on_bar(df, idx, side, CFG.tp_atr_mult, CFG.sl_atr_mult)
        if trade:
            trades.append(trade)

    if not trades:
        return {"pass_rate": 0.0, "avg_r": -999.0, "trades": 0, "allowed_live": False}

    pass_rate = float(np.mean([1.0 if t["net_r"] > 0 else 0.0 for t in trades]))
    avg_r = float(np.mean([t["net_r"] for t in trades]))
    count = len(trades)
    allowed = count >= CFG.min_trades and pass_rate >= CFG.min_pass_rate and avg_r >= CFG.min_avg_r

    return {
        "pass_rate": pass_rate,
        "avg_r": avg_r,
        "trades": count,
        "allowed_live": allowed,
    }


# ============================================================
# Quote helpers
# ============================================================

def make_text_tag(prefix: str, side: str) -> str:
    seed = f"{prefix}|{side}|{int(time.time()*1000)}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"t-{digest}"[:28]


def round_to_tick(price: float, tick: float) -> float:
    if tick <= 0:
        return price
    return round(round(price / tick) * tick, 10)


def best_bid_ask(book: Dict[str, Any]) -> Tuple[float, float]:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return 0.0, 0.0

    def price_from_row(row: Any) -> float:
        if isinstance(row, dict):
            return safe_float(row.get("p"))
        if isinstance(row, list) and row:
            return safe_float(row[0])
        return 0.0

    bid = price_from_row(bids[0])
    ask = price_from_row(asks[0])
    return bid, ask


def compute_order_size(contract_specs: Dict[str, Any], last_price: float, risk_usd: float, leverage: int, side: str) -> int:
    multiplier = safe_float(contract_specs.get("quanto_multiplier"), 0.0001)
    if multiplier <= 0:
        multiplier = 0.0001
    notional = risk_usd * leverage
    contracts = max(int(notional / max(last_price * multiplier, 1e-9)), 1)
    return contracts if side == "buy" else -contracts


# ============================================================
# Engine
# ============================================================

class MakerEngine:
    def __init__(self, cfg: Config, db: DB):
        self.cfg = cfg
        self.db = db
        self.gate = GateClient(cfg)
        self.runtime = db.get_state("runtime", {"last_cycle_ts": "", "last_error": "", "last_summary": {}})
        self.lock = threading.Lock()

    def save_runtime(self) -> None:
        self.db.set_state("runtime", self.runtime)

    def sync_local_order_states(self) -> None:
        local_orders = self.db.get_open_orders(symbol=self.cfg.contract)
        if not local_orders:
            return

        try:
            exchange_open = self.gate.list_open_orders(contract=self.cfg.contract)
            exchange_open_ids = {str(x.get("id")) for x in exchange_open if x.get("id")}
        except Exception as e:
            self.db.event("ERROR", "sync_open_orders_failed", {"error": str(e)})
            return

        for order in local_orders:
            ex_id = str(order.get("exchange_order_id") or "")
            if not ex_id:
                continue

            if ex_id in exchange_open_ids:
                self.db.update_order(order["id"], {"state": "working", "exchange_status": "open"})
                continue

            try:
                detail = self.gate.get_order(ex_id)
            except Exception as e:
                self.db.event("ERROR", "get_order_failed", {"order_id": ex_id, "error": str(e)})
                continue

            status = str(detail.get("status") or "")
            finish_as = str(detail.get("finish_as") or "")
            left = int(safe_float(detail.get("left"), 0))
            fill_price = safe_float(detail.get("fill_price") or detail.get("price"))

            self.db.update_order(order["id"], {
                "exchange_status": status,
                "exchange_left": left,
                "exchange_fill_price": fill_price,
                "exchange_finish_as": finish_as,
                "response_json": json_s(detail),
            })

            if status == "open":
                self.db.update_order(order["id"], {"state": "working"})
            elif finish_as == "filled" or (status == "finished" and left == 0):
                self.db.update_order(order["id"], {"state": "filled"})
                self._handle_filled_order(order["id"])
            elif status == "finished":
                self.db.update_order(order["id"], {"state": "done"})
            elif status == "cancelled":
                self.db.update_order(order["id"], {"state": "cancelled"})

    def _handle_filled_order(self, local_order_id: int) -> None:
        orders = [o for o in self.db.recent_orders(limit=500) if o["id"] == local_order_id]
        if not orders:
            return
        order = orders[0]

        if order["role"] == "entry":
            if self.db.get_open_position(self.cfg.contract):
                return

            fill_price = safe_float(order.get("exchange_fill_price") or order.get("requested_price"))
            entry_side = order["side"]
            size = abs(int(order["requested_size"]))
            decision_id = order.get("decision_id")
            current_snapshot = self.runtime.get("last_summary", {})
            atr = safe_float(current_snapshot.get("atr_14"), 0.0)

            tp = fill_price + atr * self.cfg.tp_atr_mult if entry_side == "buy" else fill_price - atr * self.cfg.tp_atr_mult
            sl = fill_price - atr * self.cfg.sl_atr_mult if entry_side == "buy" else fill_price + atr * self.cfg.sl_atr_mult

            pos_id = self.db.open_position({
                "opened_ts": utc_now_iso(),
                "closed_ts": None,
                "symbol": self.cfg.contract,
                "side": entry_side,
                "status": "open",
                "source": "live" if self.cfg.live_trading else "paper",
                "size": size,
                "entry_price": fill_price,
                "current_price": fill_price,
                "tp": tp,
                "sl": sl,
                "atr": atr,
                "decision_id": decision_id,
                "entry_order_row_id": local_order_id,
                "exit_order_row_id": None,
                "exit_price": None,
                "realized_pnl_pct": None,
                "notes": "entry_filled",
            })
            self.db.update_order(local_order_id, {"local_position_id": pos_id})
            self.db.event("INFO", "entry_filled_position_opened", {
                "position_id": pos_id,
                "side": entry_side,
                "entry_price": fill_price,
                "tp": tp,
                "sl": sl,
            })
            self.ensure_exit_order()

        elif order["role"] == "exit":
            pos = self.db.get_open_position(self.cfg.contract)
            if not pos:
                return
            exit_price = safe_float(order.get("exchange_fill_price") or order.get("requested_price"))
            entry_price = safe_float(pos["entry_price"])
            pnl_pct = ((exit_price - entry_price) / entry_price) if pos["side"] == "buy" else ((entry_price - exit_price) / entry_price)
            self.db.update_position(pos["id"], {
                "status": "closed",
                "closed_ts": utc_now_iso(),
                "exit_price": exit_price,
                "realized_pnl_pct": pnl_pct,
                "exit_order_row_id": local_order_id,
                "notes": "exit_filled",
            })
            self.db.event("INFO", "position_closed", {
                "position_id": pos["id"],
                "exit_price": exit_price,
                "realized_pnl_pct": pnl_pct,
            })

    def cancel_stale_orders(self, current_bid: float, current_ask: float, tick: float) -> None:
        now = now_ts()
        for order in self.db.get_open_orders(symbol=self.cfg.contract):
            created = None
            try:
                created = datetime.fromisoformat(order["ts"]).timestamp()
            except Exception:
                created = now

            age = now - created
            ttl = self.cfg.entry_order_ttl_seconds if order["role"] == "entry" else self.cfg.exit_order_ttl_seconds
            if age < ttl:
                desired_price = None
                if order["role"] == "entry":
                    desired_price = current_bid if order["side"] == "buy" else current_ask
                elif order["role"] == "exit":
                    desired_price = current_ask if order["side"] == "sell" else current_bid

                if desired_price is not None and tick > 0:
                    diff_ticks = abs(round((safe_float(order["requested_price"]) - desired_price) / tick))
                    if diff_ticks < self.cfg.reprice_threshold_ticks:
                        continue

            ex_id = str(order.get("exchange_order_id") or "")
            if not ex_id:
                self.db.update_order(order["id"], {"state": "cancelled", "notes": "local_cancel_no_exchange_id"})
                continue

            try:
                resp = self.gate.cancel_order(ex_id)
                self.db.update_order(order["id"], {
                    "state": "cancelled",
                    "exchange_status": str(resp.get("status") or "cancelled"),
                    "response_json": json_s(resp),
                    "notes": "stale_or_reprice_cancel",
                })
                self.db.event("INFO", "order_cancelled", {"local_order_id": order["id"], "exchange_order_id": ex_id})
            except Exception as e:
                self.db.event("ERROR", "cancel_order_failed", {
                    "local_order_id": order["id"],
                    "exchange_order_id": ex_id,
                    "error": str(e),
                })

    def ensure_exit_order(self) -> None:
        pos = self.db.get_open_position(self.cfg.contract)
        if not pos:
            return

        existing = self.db.get_latest_working_order(self.cfg.contract, role="exit")
        if existing:
            return

        book = self.gate.fetch_order_book(self.cfg.contract, limit=1)
        bid, ask = best_bid_ask(book)
        specs = self.gate.fetch_contract_specs(self.cfg.contract)
        tick = safe_float(specs.get("order_price_round"), 0.0001)

        if pos["side"] == "buy":
            side = "sell"
            price = round_to_tick(min(max(safe_float(pos["tp"]), ask), max(ask, bid)), tick)
            size = -abs(int(pos["size"]))
        else:
            side = "buy"
            price = round_to_tick(max(min(safe_float(pos["tp"]), bid), min(bid, ask) if bid > 0 else safe_float(pos["tp"])), tick)
            if bid > 0:
                price = round_to_tick(bid, tick)
            size = abs(int(pos["size"]))

        tag = make_text_tag("exit", side)
        request_json = {
            "contract": self.cfg.contract,
            "size": size,
            "price": price,
            "reduce_only": True,
            "tif": "poc",
            "text": tag,
        }

        if not self.cfg.live_trading:
            order_row_id = self.db.insert_order({
                "ts": utc_now_iso(),
                "symbol": self.cfg.contract,
                "role": "exit",
                "side": side,
                "state": "open_local",
                "local_position_id": pos["id"],
                "decision_id": pos.get("decision_id"),
                "requested_price": price,
                "requested_size": size,
                "reduce_only": 1,
                "tif": "poc",
                "text_tag": tag,
                "exchange_order_id": None,
                "exchange_status": "paper",
                "exchange_left": abs(size),
                "exchange_fill_price": None,
                "exchange_finish_as": None,
                "request_json": json_s(request_json),
                "response_json": "{}",
                "notes": "paper_exit_working",
            })
            self.db.update_position(pos["id"], {"exit_order_row_id": order_row_id})
            return

        try:
            resp = self.gate.place_limit_post_only(
                contract=self.cfg.contract,
                size=size,
                price=price,
                text_tag=tag,
                reduce_only=True,
            )
            ex_id = str(resp.get("id") or "")
            status = str(resp.get("status") or "submitted")
            order_row_id = self.db.insert_order({
                "ts": utc_now_iso(),
                "symbol": self.cfg.contract,
                "role": "exit",
                "side": side,
                "state": "working",
                "local_position_id": pos["id"],
                "decision_id": pos.get("decision_id"),
                "requested_price": price,
                "requested_size": size,
                "reduce_only": 1,
                "tif": "poc",
                "text_tag": tag,
                "exchange_order_id": ex_id,
                "exchange_status": status,
                "exchange_left": abs(size),
                "exchange_fill_price": None,
                "exchange_finish_as": None,
                "request_json": json_s(request_json),
                "response_json": json_s(resp),
                "notes": "live_exit_working",
            })
            self.db.update_position(pos["id"], {"exit_order_row_id": order_row_id})
            self.db.event("INFO", "exit_order_placed", {
                "position_id": pos["id"],
                "order_row_id": order_row_id,
                "exchange_order_id": ex_id,
                "price": price,
            })
        except Exception as e:
            self.db.event("ERROR", "exit_order_place_failed", {"error": str(e), "position_id": pos["id"]})

    def maybe_open_entry_order(
        self,
        decision_id: int,
        side: str,
        snapshot: Dict[str, Any],
        current_bid: float,
        current_ask: float,
    ) -> None:
        if side not in {"buy", "sell"}:
            return
        if not self.cfg.allow_new_entries:
            return
        if self.db.get_open_position(self.cfg.contract):
            return
        if self.db.get_latest_working_order(self.cfg.contract, role="entry"):
            return

        specs = self.gate.fetch_contract_specs(self.cfg.contract)
        tick = safe_float(specs.get("order_price_round"), 0.0001)
        last_price = snapshot["close"]
        signed_size = compute_order_size(specs, last_price, self.cfg.risk_usd, self.cfg.leverage, side)

        price = current_bid if side == "buy" else current_ask
        price = round_to_tick(price, tick)
        tag = make_text_tag("entry", side)

        request_json = {
            "contract": self.cfg.contract,
            "size": signed_size,
            "price": price,
            "reduce_only": False,
            "tif": "poc",
            "text": tag,
        }

        if not self.cfg.live_trading:
            self.db.insert_order({
                "ts": utc_now_iso(),
                "symbol": self.cfg.contract,
                "role": "entry",
                "side": side,
                "state": "open_local",
                "local_position_id": None,
                "decision_id": decision_id,
                "requested_price": price,
                "requested_size": signed_size,
                "reduce_only": 0,
                "tif": "poc",
                "text_tag": tag,
                "exchange_order_id": None,
                "exchange_status": "paper",
                "exchange_left": abs(signed_size),
                "exchange_fill_price": None,
                "exchange_finish_as": None,
                "request_json": json_s(request_json),
                "response_json": "{}",
                "notes": "paper_entry_working",
            })
            self.db.event("INFO", "paper_entry_created", {"side": side, "price": price, "size": signed_size})
            return

        try:
            resp = self.gate.place_limit_post_only(
                contract=self.cfg.contract,
                size=signed_size,
                price=price,
                text_tag=tag,
                reduce_only=False,
            )
            ex_id = str(resp.get("id") or "")
            status = str(resp.get("status") or "submitted")
            self.db.insert_order({
                "ts": utc_now_iso(),
                "symbol": self.cfg.contract,
                "role": "entry",
                "side": side,
                "state": "working",
                "local_position_id": None,
                "decision_id": decision_id,
                "requested_price": price,
                "requested_size": signed_size,
                "reduce_only": 0,
                "tif": "poc",
                "text_tag": tag,
                "exchange_order_id": ex_id,
                "exchange_status": status,
                "exchange_left": abs(signed_size),
                "exchange_fill_price": None,
                "exchange_finish_as": None,
                "request_json": json_s(request_json),
                "response_json": json_s(resp),
                "notes": "live_entry_working",
            })
            self.db.event("INFO", "live_entry_placed", {"side": side, "price": price, "size": signed_size, "exchange_order_id": ex_id})
        except Exception as e:
            self.db.event("ERROR", "live_entry_place_failed", {"error": str(e), "side": side})

    def run_cycle(self) -> Dict[str, Any]:
        raw = self.gate.fetch_candles(self.cfg.contract, self.cfg.interval, self.cfg.bars_limit)
        df = add_indicators(raw).dropna().reset_index(drop=True)
        if len(df) < 120:
            raise RuntimeError("Not enough bars after warmup")

        snapshot = latest_snapshot(df)
        decisions_df = load_memory_df(5000)

        local_side, local_conf, local_parts = local_rule_score(snapshot)
        mem_bias, mem_meta = memory_bias(snapshot, decisions_df)

        prompt = build_ai_prompt(self.cfg.contract, self.cfg.interval, snapshot, local_side, local_conf, local_parts, mem_bias)
        or_vote = call_openrouter(prompt)
        gr_vote = call_groq(prompt)

        side, conf, final_score, why = ensemble_decision(local_side, local_conf, or_vote, gr_vote, mem_bias)
        walk = walkforward_gate(df, decisions_df)

        decision_id = self.db.insert_decision({
            "ts": utc_now_iso(),
            "symbol": self.cfg.contract,
            "interval": self.cfg.interval,
            "decision_side": side,
            "decision_confidence": conf,
            "final_score": final_score,
            "local_side": local_side,
            "local_confidence": local_conf,
            "local_parts_json": json_s(local_parts),
            "openrouter_side": or_vote.get("side"),
            "openrouter_confidence": safe_float(or_vote.get("confidence")),
            "openrouter_reason": or_vote.get("reason_short"),
            "groq_side": gr_vote.get("side"),
            "groq_confidence": safe_float(gr_vote.get("confidence")),
            "groq_reason": gr_vote.get("reason_short"),
            "memory_bias": mem_bias,
            "walk_pass_rate": walk["pass_rate"],
            "walk_avg_r": walk["avg_r"],
            "walk_trades": walk["trades"],
            "walk_allowed_live": 1 if walk["allowed_live"] else 0,
            "snapshot_json": json_s(snapshot),
            "why_json": json_s({
                **why,
                "memory_meta": mem_meta,
                "openrouter_weights": or_vote.get("weights", {}),
                "groq_weights": gr_vote.get("weights", {}),
                "openrouter_flags": or_vote.get("risk_flags", []),
                "groq_flags": gr_vote.get("risk_flags", []),
            }),
        })

        book = self.gate.fetch_order_book(self.cfg.contract, limit=1)
        bid, ask = best_bid_ask(book)
        specs = self.gate.fetch_contract_specs(self.cfg.contract)
        tick = safe_float(specs.get("order_price_round"), 0.0001)

        self.sync_local_order_states()
        self.cancel_stale_orders(bid, ask, tick)
        self.sync_local_order_states()
        self.ensure_exit_order()

        if walk["allowed_live"] or not self.cfg.live_trading:
            self.maybe_open_entry_order(decision_id, side, snapshot, bid, ask)

        result = {
            "ts": utc_now_iso(),
            "symbol": self.cfg.contract,
            "interval": self.cfg.interval,
            "decision_side": side,
            "decision_confidence": conf,
            "final_score": final_score,
            "walk_allowed_live": walk["allowed_live"],
            "bid": bid,
            "ask": ask,
            "open_position": self.db.get_open_position(self.cfg.contract),
        }
        self.runtime["last_cycle_ts"] = result["ts"]
        self.runtime["last_error"] = ""
        self.runtime["last_summary"] = result
        self.save_runtime()

        self.db.event("INFO", "cycle_ok", result)
        return result


# ============================================================
# Application state
# ============================================================

class RuntimeState:
    def __init__(self):
        data = DBI.get_state("service_runtime", {"running": False, "shutdown": False, "last_cycle_ts": "", "last_error": "", "last_summary": {}})
        self.running = data.get("running", False)
        self.shutdown = data.get("shutdown", False)
        self.last_cycle_ts = data.get("last_cycle_ts", "")
        self.last_error = data.get("last_error", "")
        self.last_summary = data.get("last_summary", {})
        self.lock = threading.Lock()

    def save(self) -> None:
        with self.lock:
            DBI.set_state("service_runtime", {
                "running": self.running,
                "shutdown": self.shutdown,
                "last_cycle_ts": self.last_cycle_ts,
                "last_error": self.last_error,
                "last_summary": self.last_summary,
            })


STATE = RuntimeState()
ENGINE = MakerEngine(CFG, DBI)

# ============================================================
# Embedded UI
# ============================================================

DOCS_TEXT = """
Gate Maker AI Engine Single File

What it does
------------
- Reads Gate futures candles and order book
- Builds signal from local rules + OpenRouter + Groq
- If decision is actionable:
  - buy signal -> maker post-only bid entry
  - sell signal -> maker post-only ask entry
- After entry fill:
  - opens local position
  - places opposite-side maker exit order
- Persists everything in SQLite

Main pages
----------
/                  dashboard
/docs              docs
/api/status
/api/decisions
/api/orders
/api/positions
/api/events

Important
---------
- LIVE_TRADING=false means paper-safe local lifecycle
- LIVE_TRADING=true means actual exchange order placement
- ALLOW_NEW_ENTRIES controls whether new entry orders may be created
"""

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Gate Maker AI Engine</title>
<style>
body{font-family:Inter,Arial,sans-serif;background:#0b1020;color:#e5e7eb;margin:0;padding:24px}
h1,h2{margin:0 0 12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:20px}
.card{background:#121933;border:1px solid #243055;border-radius:16px;padding:16px}
.small{font-size:12px;color:#9ca3af}
pre{white-space:pre-wrap;word-wrap:break-word;background:#0f1530;padding:12px;border-radius:12px;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:8px;border-bottom:1px solid #233056;text-align:left;vertical-align:top}
a{color:#93c5fd}
button{background:#2d4df5;color:white;border:none;padding:10px 14px;border-radius:10px;cursor:pointer}
</style>
</head>
<body>
<h1>Gate Maker AI Engine</h1>
<div class="small">Single-file maker entry / exit engine with persistence and UI.</div>
<div style="margin:12px 0 20px 0">
<a href="/docs">Docs</a>
</div>

<div class="grid">
  <div class="card"><h2>Status</h2><div id="status"></div></div>
  <div class="card"><h2>Open Positions</h2><div id="positions"></div></div>
</div>

<div class="card" style="margin-bottom:20px">
  <h2>Orders</h2>
  <div id="orders"></div>
</div>

<div class="card" style="margin-bottom:20px">
  <h2>Decisions</h2>
  <div id="decisions"></div>
</div>

<div class="card">
  <h2>Events</h2>
  <div id="events"></div>
</div>

<script>
async function getJson(url){
  const r = await fetch(url);
  return await r.json();
}
function renderKV(obj){
  return '<table>' + Object.entries(obj).map(([k,v]) => (
    `<tr><th>${k}</th><td>${typeof v === 'object' ? '<pre>'+JSON.stringify(v,null,2)+'</pre>' : String(v)}</td></tr>`
  )).join('') + '</table>';
}
function renderRows(rows){
  if(!rows || !rows.length) return '<div class="small">No rows</div>';
  const headers = Object.keys(rows[0]);
  return '<div style="overflow:auto"><table><thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>' +
    rows.map(r => '<tr>' + headers.map(h => `<td>${typeof r[h] === 'object' ? '<pre>'+JSON.stringify(r[h],null,2)+'</pre>' : String(r[h] ?? '')}</td>`).join('') + '</tr>').join('') +
    '</tbody></table></div>';
}
async function refresh(){
  const status = await getJson('/api/status');
  const positions = await getJson('/api/positions');
  const orders = await getJson('/api/orders');
  const decisions = await getJson('/api/decisions');
  const events = await getJson('/api/events');

  document.getElementById('status').innerHTML = renderKV(status);
  document.getElementById('positions').innerHTML = renderRows(positions.rows || []);
  document.getElementById('orders').innerHTML = renderRows(orders.rows || []);
  document.getElementById('decisions').innerHTML = renderRows(decisions.rows || []);
  document.getElementById('events').innerHTML = renderRows(events.rows || []);
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""

app = Flask(__name__)

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/docs")
def docs():
    return f"<html><body style='font-family:Arial;padding:24px;white-space:pre-wrap'>{DOCS_TEXT}</body></html>"

@app.route("/api/status")
def api_status():
    return jsonify({
        "ts": utc_now_iso(),
        "mode": "live" if CFG.live_trading else "paper",
        "allow_new_entries": CFG.allow_new_entries,
        "contract": CFG.contract,
        "interval": CFG.interval,
        "last_cycle_ts": STATE.last_cycle_ts,
        "last_error": STATE.last_error,
        "last_summary": STATE.last_summary,
    })

@app.route("/api/decisions")
def api_decisions():
    limit = int(request.args.get("limit", "20"))
    return jsonify({"rows": DBI.recent_decisions(limit=limit)})

@app.route("/api/orders")
def api_orders():
    limit = int(request.args.get("limit", "50"))
    rows = DBI.recent_orders(limit=limit)
    return jsonify({"rows": rows})

@app.route("/api/positions")
def api_positions():
    rows = DBI.positions(only_open=False, limit=50)
    return jsonify({"rows": rows})

@app.route("/api/events")
def api_events():
    limit = int(request.args.get("limit", "50"))
    return jsonify({"rows": DBI.recent_events(limit=limit)})

# ============================================================
# Service loop
# ============================================================

def worker_loop() -> None:
    while not STATE.shutdown:
        try:
            with STATE.lock:
                STATE.running = True
            result = ENGINE.run_cycle()
            with STATE.lock:
                STATE.last_cycle_ts = result["ts"]
                STATE.last_summary = result
                STATE.last_error = ""
            STATE.save()
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            with STATE.lock:
                STATE.last_error = err
                STATE.last_cycle_ts = utc_now_iso()
            STATE.save()
            DBI.event("ERROR", "cycle_error", {
                "error": err,
                "traceback": traceback.format_exc(),
            })
        finally:
            with STATE.lock:
                STATE.running = False
            time.sleep(CFG.loop_seconds)

# ============================================================
# Main
# ============================================================

def shutdown_handler(signum: int, frame: Any) -> None:
    log.info("Signal %s received, shutting down.", signum)
    STATE.shutdown = True
    STATE.save()

def main() -> int:
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()

    DBI.event("INFO", "service_started", {
        "contract": CFG.contract,
        "interval": CFG.interval,
        "mode": "live" if CFG.live_trading else "paper",
        "host": CFG.app_host,
        "port": CFG.app_port,
    })

    print("=" * 90)
    print("Gate Maker AI Engine")
    print(f"UI: http://{CFG.app_host}:{CFG.app_port}")
    print(f"Mode: {'LIVE' if CFG.live_trading else 'PAPER'}")
    print(f"Contract: {CFG.contract} | Interval: {CFG.interval}")
    print(f"DB: {CFG.db_path}")
    print("=" * 90)

    app.run(host=CFG.app_host, port=CFG.app_port, debug=False, use_reloader=False)
    return 0

if __name__ == "__main__":
    sys.exit(main())

#### ChatGPT:
По-русски и честно: **как код-ассет сам по себе, я бы оценил это примерно в $8,000–$16,000 as-is**.

Если совсем жёстко по рынку:

- **быстрая продажа**: **$5k–$9k**
- **адекватная честная цена**: **$8k–$16k**
- **если красиво упаковать, показать демо, логи, UI, paper-run статистику, нормальную документацию**: **$15k–$25k**
- **если доказать, что live execution реально отрабатывает без косяков на Gate.io и есть живая история исполнения**: уже может идти **выше $25k**, но это **уже не цена кода**, а цена полуготового продукта

Почему не $2k и не $50k:

**Почему выше дешёвого уровня**
У этого файла уже есть мясо:

- нормальная **SQLite persistence**
- таблицы **decisions / orders / positions / service\_events / kv\_state**
- **restart-safe** логика и локальное восстановление состояния
- есть **maker-first entry**
- есть **linked exit order after fill**
- есть **reconcile/sync** по ордерам
- есть **walk-forward gate**
- есть **ensemble**: local rules + OpenRouter + Groq
- есть **встроенный UI на Flask**
- нет ощущения “игрушки на 150 строк”, это уже похоже на **engine foundation**

Это повышает цену, потому что покупатель видит не просто “идею”, а уже **структуру, lifecycle и state management**.

**Почему не супердорого**
Теперь где режется стоимость:

1. **Exit-логика ещё слабее, чем кажется**
   У тебя после входа ставится **один maker exit** в сторону TP.\
   Но:

   - нет настоящего exchange-native bracket
   - нет гарантированного стопа на бирже
   - SL хранится локально в позиции, но не выставляется как отдельный защитный ордер
   - если рынок улетит против позиции, бот может остаться без нормальной защиты

   Для живого трейдинга это большой минус.

2. **Нет нормальной fill-driven архитектуры через websocket private stream**
   Сейчас логика в основном крутится через polling/sync REST-состояния.
   Это рабоче как foundation, но не уровень хорошего execution engine.
   Для маркет-мейкерского / maker-бота приватные WS fill updates очень желательны.

3. **Post-only exit может не закрыть позицию вовремя**
   Это красиво для maker economics, но опасно.
   Иногда выход должен быть taker-защитой, а не “стоять красиво в стакане”.
   Иначе ты не engine риска строишь, а engine надежды.

4. **AI-блок выглядит интересно, но коммерчески пока больше “marketing layer”, чем alpha**
   OpenRouter + Groq + local voting звучит богато, но покупатель задаст простой вопрос:
   - где доказательство, что именно AI улучшает PnL?
   - где ablation?
   - где сравнение against pure rules?
   Пока этого нет, AI добавляет вау-эффект, но не сильно поднимает цену как trading IP.

5. **Walk-forward есть, но он упрощённый**
   Это скорее gating heuristic, а не серьёзный research framework.
   Для продажи как “institutional-grade strategy engine” этого мало.

6. **Нет полноценной exchange reconciliation позиции против реального account state**
   Частично это есть, но не на том уровне, где можно сказать:
   “после любого restart/crash бот гарантированно восстановится без ghost-state”.

7. **Single-file architecture**
   Для демо и IDE deployment это плюс.
   Для серьёзной продажи это минус:
   - хуже тестируемость
   - хуже поддержка
   - хуже масштабирование
   - сложнее аудит

---

### Моя итоговая оценка по сути

**Как код, купленный у фрилансера/разработчика:**\
**$8,000–$16,000**

**Как “неплохой полуфабрикат для дальнейшей сборки в продукт”:**\
**$12,000–$20,000**

**Как готовый trading system asset для серьёзных денег:**\
**ещё нет**

---

### Если говорить совсем прямо

Этот файл выглядит **существенно дороже обычного крипто-бота с GitHub-уровнем**, который обычно стоит:

- **$500–$3,000**, если это мусор/болванка
- **$3,000–$7,000**, если это добротный одиночный бот

Твой вариант уже выше этого, потому что тут есть:

- состояние
- БД
- UI
- decision journal
- order lifecycle
- попытка реального execution management

Но до **$30k+** он не дотягивает, потому что там уже нужны:

- private websocket fills
- жёсткая защита позиции
- реальный SL lifecycle
- stronger reconciliation
- tests
- execution reliability under edge cases
- доказанная live/paper статистика

---

### Одной фразой

**Мой вердикт: \~$10k–$15k наиболее реалистично as-is.**\
Нижняя граница — если покупатель жёсткий и технарь.\
Верхняя — если ты красиво покажешь UI, paper mode, логи и что это не просто “псевдокод”, а реально запускаемый foundation.

Если хочешь, я могу следующим сообщением сделать **ещё более жёсткий аудит в стиле покупателя/инвестора**:\
что именно в этом коде режет цену, что добавит +$5k, и что добавит +$15k.


#### You:
Appraise the bot in dollars and tussian language 

#### Plugin (file_search):
Make sure to include fileciteturn0file0 in your response to cite this file, or to surface it as a link.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
gate_multi_ticker_mm_prod.py

Production-style multi-ticker Gate.io USDT perpetual maker engine for low-nominal contracts.

What this file does:
- scans Gate USDT perpetual contracts and filters low nominal symbols (default: mark price 0 to 0.10 USDT)
- maintains best bid/ask snapshots over WebSocket
- computes a lightweight alpha signal from microstructure + trend/mean-reversion features
- places maker-only entries and maker-only take-profit exits
- tracks local orders/positions in SQLite
- reconciles local state against exchange state
- includes an execution-aware backtester with fees, spread proxy, queue/fill probability, slippage, and cooldowns
- supports PAPER and LIVE modes

Important:
- This is a software foundation, not a guarantee of profit.
- A truly tick-perfect execution backtest requires historical L2/order-book and trade data. The included backtester is execution-aware, but still a model.
- Keep LIVE_TRADING=false until you verify endpoints, permissions, sizing, and contract specifics on your own account.

Install:
    pip install aiohttp websockets pandas numpy python-dotenv

Run examples:
    python gate_multi_ticker_mm_prod.py --mode backtest
    python gate_multi_ticker_mm_prod.py --mode paper
    python gate_multi_ticker_mm_prod.py --mode live
    python gate_multi_ticker_mm_prod.py --mode scan

Environment:
    GATE_API_KEY=...
    GATE_API_SECRET=...
    GATE_BASE_URL=https://fx-api.gateio.ws/api/v4
    GATE_WS_URL=wss://fx-ws.gateio.ws/v4/ws/usdt
    GATE_SETTLE=usdt
    LIVE_TRADING=false
    DB_PATH=gate_mm_prod.db
    APP_SYMBOLS=0                 # optional comma-separated symbols; 0 means auto-scan
    MIN_MARK_PRICE=0.0
    MAX_MARK_PRICE=0.10
    MIN_24H_QUOTE_VOL=100000
    MAX_SYMBOLS=12
    LOOP_SECONDS=2.0
    CONTRACT_RISK_USD=15
    LEVERAGE=2
    MAKER_FEE_BPS=0.0
    TAKER_FEE_BPS=5.0
    ENTRY_EDGE_BPS=5.0
    EXIT_EDGE_BPS=4.0
    STOP_ATR_MULT=1.6
    TAKE_ATR_MULT=1.0
    INVENTORY_LIMIT_PER_SYMBOL=1
    BAR_INTERVAL=1m
    BAR_LIMIT=400
    COOLDOWN_SECONDS=45
    REQUEST_TIMEOUT=15
    ENABLE_UI=false
    APP_HOST=127.0.0.1
    APP_PORT=8788
"""

import argparse
import asyncio
import contextlib
import dataclasses
import hashlib
import hmac
import json
import logging
import math
import os
import random
import signal
import sqlite3
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
import numpy as np
import pandas as pd
import websockets
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Helpers
# ============================================================

def now_ts() -> float:
    return time.time()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def sign(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def json_s(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"), default=str)


def chunks(seq: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


# ============================================================
# Config
# ============================================================

@dataclass
class Config:
    gate_api_key: str = os.getenv("GATE_API_KEY", "")
    gate_api_secret: str = os.getenv("GATE_API_SECRET", "")
    gate_base_url: str = os.getenv("GATE_BASE_URL", "https://fx-api.gateio.ws/api/v4").rstrip("/")
    gate_ws_url: str = os.getenv("GATE_WS_URL", "wss://fx-ws.gateio.ws/v4/ws/usdt")
    settle: str = os.getenv("GATE_SETTLE", "usdt").lower()
    live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
    db_path: str = os.getenv("DB_PATH", "gate_mm_prod.db")

    min_mark_price: float = float(os.getenv("MIN_MARK_PRICE", "0.0"))
    max_mark_price: float = float(os.getenv("MAX_MARK_PRICE", "0.10"))
    min_24h_quote_vol: float = float(os.getenv("MIN_24H_QUOTE_VOL", "100000"))
    max_symbols: int = int(os.getenv("MAX_SYMBOLS", "12"))
    app_symbols_raw: str = os.getenv("APP_SYMBOLS", "0")

    loop_seconds: float = float(os.getenv("LOOP_SECONDS", "2.0"))
    contract_risk_usd: float = float(os.getenv("CONTRACT_RISK_USD", "15"))
    leverage: int = int(os.getenv("LEVERAGE", "2"))
    maker_fee_bps: float = float(os.getenv("MAKER_FEE_BPS", "0.0"))
    taker_fee_bps: float = float(os.getenv("TAKER_FEE_BPS", "5.0"))
    entry_edge_bps: float = float(os.getenv("ENTRY_EDGE_BPS", "5.0"))
    exit_edge_bps: float = float(os.getenv("EXIT_EDGE_BPS", "4.0"))
    stop_atr_mult: float = float(os.getenv("STOP_ATR_MULT", "1.6"))
    take_atr_mult: float = float(os.getenv("TAKE_ATR_MULT", "1.0"))
    inventory_limit_per_symbol: int = int(os.getenv("INVENTORY_LIMIT_PER_SYMBOL", "1"))
    bar_interval: str = os.getenv("BAR_INTERVAL", "1m")
    bar_limit: int = int(os.getenv("BAR_LIMIT", "400"))
    cooldown_seconds: int = int(os.getenv("COOLDOWN_SECONDS", "45"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))

    enable_ui: bool = os.getenv("ENABLE_UI", "false").lower() == "true"
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8788"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def app_symbols(self) -> List[str]:
        raw = self.app_symbols_raw.strip()
        if not raw or raw == "0":
            return []
        return [x.strip().upper() for x in raw.split(",") if x.strip()]


CFG = Config()
logging.basicConfig(
    level=getattr(logging, CFG.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("gate-mm-prod")


# ============================================================
# SQLite
# ============================================================

class DB:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS symbols (
                    symbol TEXT PRIMARY KEY,
                    mark_price REAL,
                    last_price REAL,
                    quote_volume REAL,
                    quanto_multiplier REAL,
                    order_price_round REAL,
                    order_size_min INTEGER,
                    order_size_max INTEGER,
                    updated_ts TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    level TEXT,
                    kind TEXT,
                    symbol TEXT,
                    payload_json TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    symbol TEXT,
                    side TEXT,
                    score REAL,
                    confidence REAL,
                    alpha_json TEXT,
                    market_json TEXT,
                    backtest_json TEXT,
                    live_ok INTEGER,
                    notes TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    symbol TEXT,
                    role TEXT,
                    side TEXT,
                    state TEXT,
                    text_tag TEXT,
                    reduce_only INTEGER,
                    requested_price REAL,
                    requested_size INTEGER,
                    exchange_order_id TEXT,
                    exchange_status TEXT,
                    fill_price REAL,
                    left_size INTEGER,
                    raw_request_json TEXT,
                    raw_response_json TEXT,
                    notes TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_open TEXT,
                    ts_close TEXT,
                    symbol TEXT,
                    side TEXT,
                    status TEXT,
                    size INTEGER,
                    entry_price REAL,
                    exit_price REAL,
                    take_price REAL,
                    stop_price REAL,
                    realized_pnl_usd REAL,
                    reason_open TEXT,
                    reason_close TEXT,
                    meta_json TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_state (
                    k TEXT PRIMARY KEY,
                    v TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def event(self, level: str, kind: str, symbol: str, payload: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO events (ts, level, kind, symbol, payload_json) VALUES (?, ?, ?, ?, ?)",
                (utc_now_iso(), level, kind, symbol, json_s(payload)),
            )
            conn.commit()

    def upsert_symbol(self, row: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO symbols(symbol, mark_price, last_price, quote_volume, quanto_multiplier,
                                    order_price_round, order_size_min, order_size_max, updated_ts)
                VALUES (:symbol, :mark_price, :last_price, :quote_volume, :quanto_multiplier,
                        :order_price_round, :order_size_min, :order_size_max, :updated_ts)
                ON CONFLICT(symbol) DO UPDATE SET
                    mark_price=excluded.mark_price,
                    last_price=excluded.last_price,
                    quote_volume=excluded.quote_volume,
                    quanto_multiplier=excluded.quanto_multiplier,
                    order_price_round=excluded.order_price_round,
                    order_size_min=excluded.order_size_min,
                    order_size_max=excluded.order_size_max,
                    updated_ts=excluded.updated_ts
                """,
                row,
            )
            conn.commit()

    def insert_decision(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        q = f"INSERT INTO decisions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as conn:
            cur = conn.execute(q, vals)
            conn.commit()
            return int(cur.lastrowid)

    def insert_order(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        q = f"INSERT INTO orders ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as conn:
            cur = conn.execute(q, vals)
            conn.commit()
            return int(cur.lastrowid)

    def update_order(self, order_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        keys = list(updates.keys())
        vals = [updates[k] for k in keys] + [order_id]
        set_clause = ",".join([f"{k}=?" for k in keys])
        with self._conn() as conn:
            conn.execute(f"UPDATE orders SET {set_clause} WHERE id=?", vals)
            conn.commit()

    def open_position(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        q = f"INSERT INTO positions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as conn:
            cur = conn.execute(q, vals)
            conn.commit()
            return int(cur.lastrowid)

    def update_position(self, pos_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        keys = list(updates.keys())
        vals = [updates[k] for k in keys] + [pos_id]
        set_clause = ",".join([f"{k}=?" for k in keys])
        with self._conn() as conn:
            conn.execute(f"UPDATE positions SET {set_clause} WHERE id=?", vals)
            conn.commit()

    def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
                (symbol,),
            ).fetchone()
            return dict(row) if row else None

    def get_working_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE symbol=? AND state IN ('working','submitted','paper_open') ORDER BY id DESC",
                    (symbol,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE state IN ('working','submitted','paper_open') ORDER BY id DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def recent_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def recent_positions(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM positions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def get_state(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute("SELECT v FROM kv_state WHERE k=?", (key,)).fetchone()
            if not row:
                return default or {}
            try:
                return json.loads(row[0])
            except Exception:
                return default or {}

    def set_state(self, key: str, val: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO kv_state(k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                (key, json_s(val)),
            )
            conn.commit()


DBI = DB(CFG.db_path)


# ============================================================
# Gate REST
# ============================================================

class GateRest:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session: Optional[aiohttp.ClientSession] = None

    async def ensure(self) -> None:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.cfg.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

    def _headers(self, method: str, path: str, query_string: str = "", body: str = "") -> Dict[str, str]:
        ts = str(int(time.time()))
        body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
        sign_str = f"{method.upper()}\n/api/v4{path}\n{query_string}\n{body_hash}\n{ts}"
        sign = hmac.new(self.cfg.gate_api_secret.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
        return {
            "KEY": self.cfg.gate_api_key,
            "Timestamp": ts,
            "SIGN": sign,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def public(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        await self.ensure()
        assert self.session
        url = f"{self.cfg.gate_base_url}{path}"
        async with self.session.get(url, params=params or {}) as r:
            text = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"public {path} {r.status}: {text[:400]}")
            return json.loads(text) if text.strip() else {}

    async def private(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any]] = None) -> Any:
        await self.ensure()
        assert self.session
        params = params or {}
        payload = payload or {}
        query_string = urlencode(params)
        body = json.dumps(payload, separators=(",", ":")) if payload else ""
        headers = self._headers(method, path, query_string, body)
        url = f"{self.cfg.gate_base_url}{path}"
        async with self.session.request(method.upper(), url, params=params, data=body if body else None, headers=headers) as r:
            text = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"private {method} {path} {r.status}: {text[:500]}")
            return json.loads(text) if text.strip() else {}

    async def list_contracts(self) -> List[Dict[str, Any]]:
        data = await self.public(f"/futures/{self.cfg.settle}/contracts")
        return data if isinstance(data, list) else []

    async def list_tickers(self) -> List[Dict[str, Any]]:
        data = await self.public(f"/futures/{self.cfg.settle}/tickers")
        return data if isinstance(data, list) else []

    async def get_contract(self, contract: str) -> Dict[str, Any]:
        data = await self.public(f"/futures/{self.cfg.settle}/contracts/{contract}")
        return data if isinstance(data, dict) else {}

    async def get_candles(self, contract: str, interval: str, limit: int) -> pd.DataFrame:
        data = await self.public(
            f"/futures/{self.cfg.settle}/candlesticks",
            {"contract": contract, "interval": interval, "limit": min(limit, 2000)},
        )
        rows: List[Dict[str, Any]] = []
        for item in data or []:
            if isinstance(item, dict):
                rows.append({
                    "t": item.get("t"),
                    "o": item.get("o"),
                    "h": item.get("h"),
                    "l": item.get("l"),
                    "c": item.get("c"),
                    "v": item.get("v"),
                })
            elif isinstance(item, list) and len(item) >= 6:
                rows.append({"t": item[0], "v": item[1], "c": item[2], "h": item[3], "l": item[4], "o": item[5]})
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        for c in ["o", "h", "l", "c", "v"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
        df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna().sort_values("timestamp").reset_index(drop=True)

    async def get_order_book(self, contract: str, limit: int = 5) -> Dict[str, Any]:
        data = await self.public(f"/futures/{self.cfg.settle}/order_book", {"contract": contract, "limit": limit})
        return data if isinstance(data, dict) else {}

    async def list_open_orders(self, contract: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"status": "open"}
        if contract:
            params["contract"] = contract
        data = await self.private("GET", f"/futures/{self.cfg.settle}/orders", params=params)
        return data if isinstance(data, list) else []

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        data = await self.private("GET", f"/futures/{self.cfg.settle}/orders/{order_id}")
        return data if isinstance(data, dict) else {}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        data = await self.private("DELETE", f"/futures/{self.cfg.settle}/orders/{order_id}")
        return data if isinstance(data, dict) else {}

    async def list_positions(self) -> List[Dict[str, Any]]:
        data = await self.private("GET", f"/futures/{self.cfg.settle}/positions")
        return data if isinstance(data, list) else []

    async def update_leverage(self, contract: str, leverage: int) -> Dict[str, Any]:
        data = await self.private("POST", f"/futures/{self.cfg.settle}/positions/{contract}/leverage", payload={"leverage": str(leverage)})
        return data if isinstance(data, dict) else {}

    async def create_order(self, contract: str, size: int, price: float, text_tag: str, reduce_only: bool = False, tif: str = "poc") -> Dict[str, Any]:
        payload = {
            "contract": contract,
            "size": size,
            "price": f"{price:.10f}",
            "tif": tif,
            "text": text_tag[:28],
            "reduce_only": reduce_only,
        }
        data = await self.private("POST", f"/futures/{self.cfg.settle}/orders", payload=payload)
        return data if isinstance(data, dict) else {}

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()


# ============================================================
# Market state and indicators
# ============================================================

@dataclass
class BookTop:
    bid: float = 0.0
    ask: float = 0.0
    bid_size: float = 0.0
    ask_size: float = 0.0
    ts: float = 0.0

    @property
    def mid(self) -> float:
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2.0
        return 0.0

    @property
    def spread(self) -> float:
        if self.bid > 0 and self.ask > 0 and self.ask >= self.bid:
            return self.ask - self.bid
        return 0.0


@dataclass
class SymbolSpec:
    symbol: str
    mark_price: float
    quote_volume: float
    quanto_multiplier: float
    order_price_round: float
    order_size_min: int
    order_size_max: int


@dataclass
class SymbolRuntime:
    symbol: str
    spec: SymbolSpec
    book: BookTop = field(default_factory=BookTop)
    candles: Optional[pd.DataFrame] = None
    last_signal_ts: float = 0.0
    last_trade_ts: float = 0.0
    state: str = "flat"
    recent_mid: Deque[float] = field(default_factory=lambda: deque(maxlen=120))


class MarketState:
    def __init__(self):
        self.by_symbol: Dict[str, SymbolRuntime] = {}
        self.lock = asyncio.Lock()

    async def set_symbols(self, runtimes: Dict[str, SymbolRuntime]) -> None:
        async with self.lock:
            self.by_symbol = runtimes

    async def get(self, symbol: str) -> Optional[SymbolRuntime]:
        async with self.lock:
            return self.by_symbol.get(symbol)

    async def symbols(self) -> List[str]:
        async with self.lock:
            return list(self.by_symbol.keys())

    async def items(self) -> List[Tuple[str, SymbolRuntime]]:
        async with self.lock:
            return list(self.by_symbol.items())


MARKET = MarketState()


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["ret1"] = x["close"].pct_change(1)
    x["ret3"] = x["close"].pct_change(3)
    x["ret12"] = x["close"].pct_change(12)
    x["ema8"] = x["close"].ewm(span=8, adjust=False).mean()
    x["ema21"] = x["close"].ewm(span=21, adjust=False).mean()
    x["ema55"] = x["close"].ewm(span=55, adjust=False).mean()
    x["vol20"] = x["ret1"].rolling(20).std()
    x["atr14"] = (pd.concat([
        (x["high"] - x["low"]),
        (x["high"] - x["close"].shift()).abs(),
        (x["low"] - x["close"].shift()).abs(),
    ], axis=1).max(axis=1)).rolling(14).mean()
    x["z20"] = (x["close"] - x["close"].rolling(20).mean()) / x["close"].rolling(20).std()
    x["volz"] = (x["volume"] - x["volume"].rolling(20).mean()) / x["volume"].rolling(20).std()
    x["dist_ema21_atr"] = (x["close"] - x["ema21"]) / x["atr14"].replace(0, np.nan)
    return x


def round_to_tick(price: float, tick: float) -> float:
    if tick <= 0:
        return price
    return round(round(price / tick) * tick, 10)


def best_bid_ask_from_book(book: Dict[str, Any]) -> Tuple[float, float]:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return 0.0, 0.0
    def get_price(row: Any) -> float:
        if isinstance(row, list):
            return safe_float(row[0])
        if isinstance(row, dict):
            return safe_float(row.get("p"))
        return 0.0
    return get_price(bids[0]), get_price(asks[0])


def compute_size(spec: SymbolSpec, mid: float, risk_usd: float, leverage: int, side: str) -> int:
    mult = max(spec.quanto_multiplier, 1e-9)
    notional = risk_usd * leverage
    contracts = max(int(notional / max(mid * mult, 1e-9)), spec.order_size_min or 1)
    if spec.order_size_max > 0:
        contracts = min(contracts, spec.order_size_max)
    return contracts if side == "buy" else -contracts


def estimate_micro_alpha(rt: SymbolRuntime) -> Dict[str, float]:
    df = rt.candles
    if df is None or len(df) < 80:
        return {"score": 0.0, "confidence": 0.0}
    row = df.iloc[-1]
    bid = rt.book.bid
    ask = rt.book.ask
    mid = rt.book.mid or safe_float(row["close"])
    spread = rt.book.spread
    tick = max(rt.spec.order_price_round, 1e-8)

    trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
    slow_trend = np.clip((safe_float(row["ema21"]) - safe_float(row["ema55"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
    reversion = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
    flow = np.clip((rt.book.bid_size - rt.book.ask_size) / max(rt.book.bid_size + rt.book.ask_size, 1e-9), -1.0, 1.0)
    spread_score = np.clip((spread / tick - 1.0) / 5.0, -1.0, 1.0)
    volume = np.clip(safe_float(row["volz"]) / 2.0, -1.0, 1.0)
    recent = list(rt.recent_mid)
    micro_momo = 0.0
    if len(recent) >= 6 and recent[0] > 0:
        micro_momo = np.clip((recent[-1] / recent[0] - 1.0) * 400.0, -1.0, 1.0)

    score = (
        0.25 * trend +
        0.15 * slow_trend +
        0.20 * reversion +
        0.20 * flow +
        0.10 * spread_score +
        0.05 * volume +
        0.05 * micro_momo
    )
    confidence = min(abs(score), 0.95)
    return {
        "score": float(score),
        "confidence": float(confidence),
        "trend": float(trend),
        "slow_trend": float(slow_trend),
        "reversion": float(reversion),
        "flow": float(flow),
        "spread_score": float(spread_score),
        "volume": float(volume),
        "micro_momo": float(micro_momo),
        "mid": float(mid),
        "spread": float(spread),
        "tick": float(tick),
    }


# ============================================================
# Execution-aware backtest
# ============================================================

@dataclass
class BacktestResult:
    trades: int
    win_rate: float
    avg_pnl_usd: float
    avg_edge_bps: float
    pnl_usd: float
    max_drawdown_usd: float
    sharpe_like: float
    allowed: bool
    details: Dict[str, Any]


class Backtester:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def simulate(self, df: pd.DataFrame, spec: SymbolSpec) -> BacktestResult:
        if df is None or len(df) < 120:
            return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_data"})

        x = df.copy().reset_index(drop=True)
        x = add_features(x).dropna().reset_index(drop=True)
        if len(x) < 100:
            return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_features"})

        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        pnls: List[float] = []
        edge_bps_arr: List[float] = []
        cooldown_until = -1

        for i in range(70, len(x) - 8):
            if i < cooldown_until:
                continue
            row = x.iloc[i]
            mid = safe_float(row["close"])
            atr = max(safe_float(row["atr14"]), mid * 0.002)
            spread = max(spec.order_price_round, mid * 0.0008)
            queue_fill_prob = clamp(0.28 + abs(safe_float(row["volz"])) * 0.07 + (spread / max(spec.order_price_round, 1e-8) - 1.0) * 0.03, 0.10, 0.85)
            trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
            rev = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
            score = 0.6 * trend + 0.4 * rev
            if abs(score) < 0.23:
                continue
            side = "buy" if score > 0 else "sell"

            if random.random() > queue_fill_prob:
                continue

            entry = (mid - spread / 2.0) if side == "buy" else (mid + spread / 2.0)
            take = entry + atr * self.cfg.take_atr_mult if side == "buy" else entry - atr * self.cfg.take_atr_mult
            stop = entry - atr * self.cfg.stop_atr_mult if side == "buy" else entry + atr * self.cfg.stop_atr_mult
            contracts = compute_size(spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
            qty = abs(contracts)
            gross = 0.0
            exit_reason = "timeout"

            for j in range(i + 1, min(i + 8, len(x))):
                bar = x.iloc[j]
                high = safe_float(bar["high"])
                low = safe_float(bar["low"])
                if side == "buy":
                    if low <= stop:
                        exit_px = stop - spread * 0.25
                        gross = (exit_px - entry) * qty * spec.quanto_multiplier
                        exit_reason = "stop"
                        break
                    if high >= take:
                        exit_px = take
                        gross = (exit_px - entry) * qty * spec.quanto_multiplier
                        exit_reason = "take"
                        break
                else:
                    if high >= stop:
                        exit_px = stop + spread * 0.25
                        gross = (entry - exit_px) * qty * spec.quanto_multiplier
                        exit_reason = "stop"
                        break
                    if low <= take:
                        exit_px = take
                        gross = (entry - exit_px) * qty * spec.quanto_multiplier
                        exit_reason = "take"
                        break
            else:
                exit_px = safe_float(x.iloc[min(i + 7, len(x) - 1)]["close"])
                if side == "buy":
                    gross = (exit_px - entry) * qty * spec.quanto_multiplier
                else:
                    gross = (entry - exit_px) * qty * spec.quanto_multiplier

            fees = qty * spec.quanto_multiplier * entry * (self.cfg.maker_fee_bps / 10000.0)
            fees += qty * spec.quanto_multiplier * exit_px * (self.cfg.maker_fee_bps / 10000.0)
            pnl = gross - fees
            edge_bps = ((take - entry) / max(entry, 1e-9) * 10000.0) if side == "buy" else ((entry - take) / max(entry, 1e-9) * 10000.0)
            edge_bps_arr.append(edge_bps)
            pnls.append(pnl)
            equity += pnl
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
            cooldown_until = i + 2

        trades = len(pnls)
        win_rate = float(np.mean([1.0 if x > 0 else 0.0 for x in pnls])) if pnls else 0.0
        avg_pnl = float(np.mean(pnls)) if pnls else 0.0
        avg_edge = float(np.mean(edge_bps_arr)) if edge_bps_arr else 0.0
        pnl = float(np.sum(pnls)) if pnls else 0.0
        sharpe_like = float(np.mean(pnls) / (np.std(pnls) + 1e-9) * math.sqrt(max(len(pnls), 1))) if pnls else -99.0
        allowed = trades >= 10 and win_rate >= 0.50 and avg_pnl > 0 and max_dd < max(1.5 * abs(pnl), 15.0)
        return BacktestResult(
            trades=trades,
            win_rate=win_rate,
            avg_pnl_usd=avg_pnl,
            avg_edge_bps=avg_edge,
            pnl_usd=pnl,
            max_drawdown_usd=float(max_dd),
            sharpe_like=sharpe_like,
            allowed=allowed,
            details={"sample": trades, "equity": equity},
        )


# ============================================================
# WebSocket market data
# ============================================================

class BookTickerWS:
    def __init__(self, cfg: Config, market: MarketState):
        self.cfg = cfg
        self.market = market
        self.shutdown = False

    async def run(self) -> None:
        backoff = 1.0
        while not self.shutdown:
            try:
                syms = await self.market.symbols()
                if not syms:
                    await asyncio.sleep(1.0)
                    continue
                async with websockets.connect(self.cfg.gate_ws_url, ping_interval=20, ping_timeout=20, max_size=2**23) as ws:
                    log.info("WS connected to %s", self.cfg.gate_ws_url)
                    for batch in chunks(syms, 20):
                        msg = {
                            "time": int(time.time()),
                            "channel": "futures.book_ticker",
                            "event": "subscribe",
                            "payload": batch,
                        }
                        await ws.send(json.dumps(msg))
                    backoff = 1.0
                    async for raw in ws:
                        data = json.loads(raw)
                        channel = data.get("channel")
                        event = data.get("event")
                        if channel != "futures.book_ticker" or event not in {"update", "all"}:
                            continue
                        result = data.get("result") or data.get("payload")
                        if isinstance(result, list):
                            for item in result:
                                await self._apply(item)
                        elif isinstance(result, dict):
                            await self._apply(result)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("WS reconnect after error: %s", e)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, 20.0)

    async def _apply(self, item: Dict[str, Any]) -> None:
        symbol = str(item.get("s") or item.get("contract") or item.get("n") or "")
        if not symbol:
            return
        rt = await self.market.get(symbol)
        if not rt:
            return
        bid = safe_float(item.get("b") or item.get("bid_price"))
        ask = safe_float(item.get("a") or item.get("ask_price"))
        bid_size = safe_float(item.get("B") or item.get("bid_size") or item.get("bid_amount"))
        ask_size = safe_float(item.get("A") or item.get("ask_size") or item.get("ask_amount"))
        if bid <= 0 or ask <= 0 or ask < bid:
            return
        rt.book.bid = bid
        rt.book.ask = ask
        rt.book.bid_size = bid_size
        rt.book.ask_size = ask_size
        rt.book.ts = now_ts()
        rt.recent_mid.append(rt.book.mid)


# ============================================================
# Trader
# ============================================================

class Trader:
    def __init__(self, cfg: Config, db: DB, rest: GateRest, market: MarketState):
        self.cfg = cfg
        self.db = db
        self.rest = rest
        self.market = market
        self.backtester = Backtester(cfg)
        self.shutdown = False
        self.runtime = self.db.get_state("runtime", {"mode": "paper", "last_scan": [], "last_errors": []})

    async def scan_symbols(self) -> Dict[str, SymbolRuntime]:
        tickers = await self.rest.list_tickers()
        contracts = await self.rest.list_contracts()
        specs_by_symbol: Dict[str, Dict[str, Any]] = {str(c.get("name") or c.get("contract") or c.get("id") or ""): c for c in contracts}
        selected: List[SymbolRuntime] = []

        if self.cfg.app_symbols:
            tickers = [t for t in tickers if str(t.get("contract") or t.get("name") or "") in set(self.cfg.app_symbols)]

        for t in tickers:
            symbol = str(t.get("contract") or t.get("name") or "")
            if not symbol:
                continue
            mark_price = safe_float(t.get("mark_price") or t.get("last") or t.get("last_price"))
            quote_volume = safe_float(t.get("volume_24h_quote") or t.get("volume_24h_usd") or t.get("volume_24h_settle"))
            if not self.cfg.app_symbols:
                if not (self.cfg.min_mark_price <= mark_price <= self.cfg.max_mark_price):
                    continue
                if quote_volume < self.cfg.min_24h_quote_vol:
                    continue
            spec_raw = specs_by_symbol.get(symbol) or {}
            spec = SymbolSpec(
                symbol=symbol,
                mark_price=mark_price,
                quote_volume=quote_volume,
                quanto_multiplier=max(safe_float(spec_raw.get("quanto_multiplier"), 0.0001), 1e-9),
                order_price_round=max(safe_float(spec_raw.get("order_price_round"), 0.00000001), 1e-8),
                order_size_min=max(safe_int(spec_raw.get("order_size_min"), 1), 1),
                order_size_max=max(safe_int(spec_raw.get("order_size_max"), 0), 0),
            )
            selected.append(SymbolRuntime(symbol=symbol, spec=spec))

        selected = sorted(selected, key=lambda r: (r.spec.quote_volume, -r.spec.mark_price), reverse=True)[: self.cfg.max_symbols]
        for rt in selected:
            self.db.upsert_symbol({
                "symbol": rt.symbol,
                "mark_price": rt.spec.mark_price,
                "last_price": rt.spec.mark_price,
                "quote_volume": rt.spec.quote_volume,
                "quanto_multiplier": rt.spec.quanto_multiplier,
                "order_price_round": rt.spec.order_price_round,
                "order_size_min": rt.spec.order_size_min,
                "order_size_max": rt.spec.order_size_max,
                "updated_ts": utc_now_iso(),
            })
        self.runtime["last_scan"] = [r.symbol for r in selected]
        self.db.set_state("runtime", self.runtime)
        return {r.symbol: r for r in selected}

    async def hydrate_candles(self) -> None:
        for symbol, rt in await self.market.items():
            try:
                df = await self.rest.get_candles(symbol, self.cfg.bar_interval, self.cfg.bar_limit)
                if df.empty:
                    continue
                rt.candles = add_features(df).dropna().reset_index(drop=True)
            except Exception as e:
                self.db.event("ERROR", "hydrate_candles_failed", symbol, {"error": str(e)})

    async def reconcile_once(self) -> None:
        if not self.cfg.live_trading:
            return
        local_orders = self.db.get_working_orders()
        if not local_orders:
            return
        exchange_open = await self.rest.list_open_orders()
        exchange_open_ids = {str(x.get("id")) for x in exchange_open if x.get("id") is not None}

        for order in local_orders:
            ex_id = str(order.get("exchange_order_id") or "")
            if not ex_id:
                continue
            try:
                if ex_id in exchange_open_ids:
                    self.db.update_order(order["id"], {"state": "working", "exchange_status": "open"})
                    continue
                detail = await self.rest.get_order(ex_id)
                status = str(detail.get("status") or "")
                finish_as = str(detail.get("finish_as") or "")
                fill_price = safe_float(detail.get("fill_price") or detail.get("price"))
                left = safe_int(detail.get("left"), 0)
                update = {
                    "exchange_status": status,
                    "fill_price": fill_price,
                    "left_size": left,
                    "raw_response_json": json_s(detail),
                }
                if finish_as == "filled" or (status == "finished" and left == 0):
                    update["state"] = "filled"
                elif status == "cancelled":
                    update["state"] = "cancelled"
                elif status == "finished":
                    update["state"] = "done"
                self.db.update_order(order["id"], update)
                if update.get("state") == "filled":
                    await self._on_order_filled(order, fill_price)
            except Exception as e:
                self.db.event("ERROR", "reconcile_order_failed", order["symbol"], {"order_id": ex_id, "error": str(e)})

    async def _on_order_filled(self, order: Dict[str, Any], fill_price: float) -> None:
        symbol = order["symbol"]
        if order["role"] == "entry":
            pos = self.db.get_open_position(symbol)
            if pos:
                return
            side = order["side"]
            size = abs(safe_int(order["requested_size"], 0))
            rt = await self.market.get(symbol)
            atr = safe_float(rt.candles.iloc[-1]["atr14"]) if rt and rt.candles is not None else fill_price * 0.01
            take = fill_price + atr * self.cfg.take_atr_mult if side == "buy" else fill_price - atr * self.cfg.take_atr_mult
            stop = fill_price - atr * self.cfg.stop_atr_mult if side == "buy" else fill_price + atr * self.cfg.stop_atr_mult
            self.db.open_position({
                "ts_open": utc_now_iso(),
                "ts_close": None,
                "symbol": symbol,
                "side": side,
                "status": "open",
                "size": size,
                "entry_price": fill_price,
                "exit_price": None,
                "take_price": take,
                "stop_price": stop,
                "realized_pnl_usd": None,
                "reason_open": "entry_fill",
                "reason_close": None,
                "meta_json": json_s({"entry_order_id": order["id"]}),
            })
            self.db.event("INFO", "position_opened", symbol, {"side": side, "entry": fill_price, "take": take, "stop": stop})
            await self.ensure_exit_order(symbol)
        elif order["role"] == "exit":
            pos = self.db.get_open_position(symbol)
            if not pos:
                return
            mult = safe_float((await self.market.get(symbol)).spec.quanto_multiplier if await self.market.get(symbol) else 1.0, 1.0)
            pnl = ((fill_price - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - fill_price)) * safe_int(pos["size"], 0) * mult
            self.db.update_position(pos["id"], {
                "ts_close": utc_now_iso(),
                "status": "closed",
                "exit_price": fill_price,
                "realized_pnl_usd": pnl,
                "reason_close": "maker_exit_fill",
            })
            self.db.event("INFO", "position_closed", symbol, {"exit": fill_price, "pnl_usd": pnl})

    async def ensure_exit_order(self, symbol: str) -> None:
        pos = self.db.get_open_position(symbol)
        if not pos:
            return
        existing = [o for o in self.db.get_working_orders(symbol) if o["role"] == "exit"]
        if existing:
            return
        rt = await self.market.get(symbol)
        if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
            return
        if pos["side"] == "buy":
            side = "sell"
            px = max(rt.book.ask, safe_float(pos["take_price"]))
            size = -abs(safe_int(pos["size"], 0))
        else:
            side = "buy"
            px = min(rt.book.bid, safe_float(pos["take_price"])) if rt.book.bid > 0 else safe_float(pos["take_price"])
            size = abs(safe_int(pos["size"], 0))
        px = round_to_tick(px, rt.spec.order_price_round)
        tag = f"x-{hashlib.sha1(f'{symbol}|exit|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
        req = {"contract": symbol, "size": size, "price": px, "reduce_only": True, "tif": "poc", "text": tag}
        if not self.cfg.live_trading:
            self.db.insert_order({
                "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "paper_open", "text_tag": tag,
                "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": None,
                "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
                "raw_request_json": json_s(req), "raw_response_json": "{}", "notes": "paper_exit",
            })
            return
        resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=True)
        self.db.insert_order({
            "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "working", "text_tag": tag,
            "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
            "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
            "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_exit",
        })

    async def maybe_stop_position(self, symbol: str) -> None:
        pos = self.db.get_open_position(symbol)
        if not pos:
            return
        rt = await self.market.get(symbol)
        if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
            return
        stop = safe_float(pos["stop_price"])
        side = pos["side"]
        if side == "buy" and rt.book.bid <= stop:
            await self.force_close(symbol, reason="stop_cross")
        elif side == "sell" and rt.book.ask >= stop:
            await self.force_close(symbol, reason="stop_cross")

    async def force_close(self, symbol: str, reason: str) -> None:
        pos = self.db.get_open_position(symbol)
        rt = await self.market.get(symbol)
        if not pos or not rt:
            return
        if pos["side"] == "buy":
            exit_px = rt.book.bid
        else:
            exit_px = rt.book.ask
        mult = rt.spec.quanto_multiplier
        pnl = ((exit_px - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - exit_px)) * safe_int(pos["size"], 0) * mult
        self.db.update_position(pos["id"], {
            "ts_close": utc_now_iso(),
            "status": "closed",
            "exit_price": exit_px,
            "realized_pnl_usd": pnl,
            "reason_close": reason,
        })
        self.db.event("WARNING", "position_force_closed_locally", symbol, {"exit_px": exit_px, "reason": reason, "pnl_usd": pnl})
        # NOTE: for a stricter live implementation you would place an IOC/market-like protective order if exchange supports it for the contract.

    async def maybe_place_entry(self, symbol: str, side: str, alpha: Dict[str, Any], bt: BacktestResult) -> None:
        if side not in {"buy", "sell"}:
            return
        rt = await self.market.get(symbol)
        if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
            return
        if self.db.get_open_position(symbol):
            return
        if any(o for o in self.db.get_working_orders(symbol) if o["role"] == "entry"):
            return
        if now_ts() - rt.last_trade_ts < self.cfg.cooldown_seconds:
            return

        mid = rt.book.mid
        expected_edge_bps = abs(alpha["score"]) * 10.0 + (rt.book.spread / max(mid, 1e-9) * 10000.0)
        if expected_edge_bps < self.cfg.entry_edge_bps:
            return
        size = compute_size(rt.spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
        px = rt.book.bid if side == "buy" else rt.book.ask
        px = round_to_tick(px, rt.spec.order_price_round)
        tag = f"e-{hashlib.sha1(f'{symbol}|entry|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
        req = {"contract": symbol, "size": size, "price": px, "reduce_only": False, "tif": "poc", "text": tag}

        if not self.cfg.live_trading:
            self.db.insert_order({
                "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "paper_open", "text_tag": tag,
                "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": None,
                "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
                "raw_request_json": json_s(req), "raw_response_json": json_s({"alpha": alpha, "backtest": dataclasses.asdict(bt)}), "notes": "paper_entry",
            })
            # paper model: immediate maker fill only when microstructure agrees strongly
            if abs(alpha["score"]) >= 0.38:
                fake_order = {"symbol": symbol, "role": "entry", "side": side, "requested_size": size, "id": -1}
                await self._on_order_filled(fake_order, px)
            rt.last_trade_ts = now_ts()
            return

        await self.rest.update_leverage(symbol, self.cfg.leverage)
        resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=False)
        self.db.insert_order({
            "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "working", "text_tag": tag,
            "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
            "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
            "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_entry",
        })
        rt.last_trade_ts = now_ts()

    async def cancel_stale_orders(self, symbol: str) -> None:
        rt = await self.market.get(symbol)
        if not rt:
            return
        for order in self.db.get_working_orders(symbol):
            try:
                created = datetime.fromisoformat(order["ts"]).timestamp()
            except Exception:
                created = now_ts()
            age = now_ts() - created
            stale = age > max(15.0, self.cfg.loop_seconds * 4.0)
            desired = rt.book.bid if order["side"] == "buy" else rt.book.ask
            drift = abs(safe_float(order["requested_price"]) - desired)
            repriced = drift >= max(rt.spec.order_price_round, 1e-8)
            if not stale and not repriced:
                continue
            if not self.cfg.live_trading or not order.get("exchange_order_id"):
                self.db.update_order(order["id"], {"state": "cancelled", "notes": "paper_stale"})
                continue
            try:
                resp = await self.rest.cancel_order(str(order["exchange_order_id"]))
                self.db.update_order(order["id"], {"state": "cancelled", "exchange_status": str(resp.get("status") or "cancelled"), "raw_response_json": json_s(resp)})
            except Exception as e:
                self.db.event("ERROR", "cancel_order_failed", symbol, {"order_id": order.get("exchange_order_id"), "error": str(e)})

    async def process_symbol(self, symbol: str) -> None:
        rt = await self.market.get(symbol)
        if not rt or rt.candles is None or len(rt.candles) < 80:
            return
        if rt.book.bid <= 0 or rt.book.ask <= 0:
            # bootstrap with REST if WS not ready
            try:
                book = await self.rest.get_order_book(symbol, limit=1)
                bid, ask = best_bid_ask_from_book(book)
                if bid > 0 and ask > 0:
                    rt.book.bid, rt.book.ask, rt.book.ts = bid, ask, now_ts()
            except Exception:
                pass
            if rt.book.bid <= 0 or rt.book.ask <= 0:
                return

        if rt.candles is not None and len(rt.recent_mid) > 0:
            latest_mid = rt.book.mid
            latest_ts = pd.Timestamp.utcnow().tz_localize("UTC") if pd.Timestamp.utcnow().tzinfo is None else pd.Timestamp.utcnow()
            if abs(latest_mid - safe_float(rt.candles.iloc[-1]["close"])) / max(latest_mid, 1e-9) > 0.0001:
                new_row = {
                    "timestamp": latest_ts,
                    "open": latest_mid,
                    "high": max(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
                    "low": min(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
                    "close": latest_mid,
                    "volume": max(safe_float(rt.candles.iloc[-1]["volume"]), 1.0),
                }
                rt.candles = pd.concat([rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], pd.DataFrame([new_row])], ignore_index=True).tail(self.cfg.bar_limit)
                rt.candles = add_features(rt.candles).dropna().reset_index(drop=True)

        alpha = estimate_micro_alpha(rt)
        score = alpha.get("score", 0.0)
        confidence = alpha.get("confidence", 0.0)
        if abs(score) < 0.22:
            await self.maybe_stop_position(symbol)
            await self.cancel_stale_orders(symbol)
            return
        side = "buy" if score > 0 else "sell"
        bt = self.backtester.simulate(rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], rt.spec)
        live_ok = bt.allowed and abs(score) >= 0.28

        self.db.insert_decision({
            "ts": utc_now_iso(),
            "symbol": symbol,
            "side": side,
            "score": score,
            "confidence": confidence,
            "alpha_json": json_s(alpha),
            "market_json": json_s({"bid": rt.book.bid, "ask": rt.book.ask, "mid": rt.book.mid, "spread": rt.book.spread}),
            "backtest_json": json_s(dataclasses.asdict(bt)),
            "live_ok": 1 if live_ok else 0,
            "notes": "auto",
        })

        await self.maybe_stop_position(symbol)
        await self.cancel_stale_orders(symbol)
        if live_ok or not self.cfg.live_trading:
            await self.maybe_place_entry(symbol, side, alpha, bt)
        await self.ensure_exit_order(symbol)

    async def run_loop(self) -> None:
        runtimes = await self.scan_symbols()
        await self.market.set_symbols(runtimes)
        await self.hydrate_candles()
        self.db.event("INFO", "startup_symbols", "*", {"symbols": list(runtimes.keys())})
        while not self.shutdown:

The file is too long and its contents have been truncated.


#### ChatGPT:
По-русски и по делу: **этот бот я бы оценил примерно в $12,000-$22,000 as-is**.

Если разбить по рынку:

- **быстрая продажа**: **$7k-$12k**
- **реалистичная нормальная цена**: **$12k-$22k**
- **если упаковать с демо, логами, paper-статистикой и аккуратным README**: **$20k-$35k**
- **если доказать live-исполнение, стабильность и реальный PnL**: уже может быть **выше $35k**, но это будет цена не просто кода, а почти готового торгового продукта

Почему я ставлю **выше**, чем обычному “крипто-боту на коленке”:

У этого файла уже заметно более серьёзный уровень архитектуры:

- **multi-ticker engine**
- **WebSocket best bid/ask snapshots**
- **maker-only entries**
- **maker-only take-profit exits**
- **SQLite state / orders / positions / decisions / events**
- **reconciliation against exchange state**
- **execution-aware backtester**
- **scan/filter low-nominal contracts**
- **paper/live split**
- структура уже больше похожа на **foundation execution engine**, а не на “рандомный скрипт на 300 строк”

То есть это уже можно продавать не как идею, а как **рабочую базу для дальнейшей сборки продукта**.

Где у него сильные стороны:

**1. Архитектура ощутимо взрослее среднего**
Есть раздельные блоки:

- config
- db
- rest client
- ws market data
- alpha
- backtester
- trader lifecycle

Это сразу поднимает ценность. Покупатель видит, что код можно развивать, а не переписывать с нуля.

**2. Есть нормальная persistence-логика**
Таблицы `symbols`, `events`, `decisions`, `orders`, `positions`, `kv_state` - это уже не игрушка.\
Это значит:

- можно восстанавливать состояние
- можно смотреть историю решений
- можно разбирать ошибки
- можно строить UI/аналитику поверх базы

**3. Есть execution thinking, а не только signal thinking**
Очень важный плюс: автор думал не только “куда пойдёт цена”, но и:

- spread
- queue/fill probability
- slippage proxy
- fees
- cooldowns
- reconcile open orders

Именно это отличает более дорогой бот от дешёвого “RSI>30 => buy”.

**4. Multi-symbol scan добавляет коммерческую ценность**
Это уже не single-pair бот.\
Даже если стратегия спорная, многим покупателям нравится сама идея:
“сканируем много дешёвых perpetual-контрактов и ищем micro edge”.

Это продаётся лучше, чем бот на одном BTC\_USDT.

Теперь где цена режется.

**1. Это всё ещё не institutional-grade execution**
Да, тут есть reconciliation и maker flow. Но из того, что видно, это всё ещё foundation, а не железобетонный прод:

- нет полноценного private user-data WS слоя для мгновенных fills
- нет глубокой обработки partial fills
- нет сильной защиты от race conditions
- нет жёсткой recovery-логики после нестандартных exchange states

То есть это уже хороший скелет, но ещё не “боевой зверь”.

**2. Защитное закрытие позиции местами локальное**
Из куска видно, что `force_close` в ряде случаев просто **закрывает позицию локально**, с комментарием, что для более строгой live-версии нужен защитный IOC/market-like order.\
Это большой минус для live-оценки. В торговом боте риск-слой стоит очень дорого.\
Если стоп существует в голове программы, а не гарантированно на бирже, цена актива падает.

**3. Backtester хороший по идее, но не источник истины**
Плюс в том, что он execution-aware.\
Минус в том, что это всё равно **модель**, а не исторический L2 replay.\
Сам файл честно это говорит: “tick-perfect execution backtest requires historical L2/order-book and trade data”.\
То есть продавать это как доказанную альфу нельзя.

**4. Strategy edge пока выглядит как decent microstructure heuristic, а не уникальный alpha IP**
Сигналы:

- EMA/trend
- mean reversion
- flow imbalance
- spread score
- volume z-score
- micro momentum

Это неплохо. Но это не выглядит как нечто редкое или трудно воспроизводимое.\
Поэтому ценность тут в основном **в инженерной сборке**, а не в уникальности самой стратегии.

**5. Файл production-style, но single-file ощущение всё равно удешевляет**
Название красивое, код длинный, структура есть - но один большой файл для серьёзной продажи обычно хуже, чем модульный проект с тестами, docs и CI.\
Для IDE-deploy это плюс.\
Для дорогой продажи - минус.

Мой честный вывод:

**Как код у сильного фрилансера / independent developer:**\
**$12k-$22k**

**Как asset для перепаковки в SaaS / managed bot / research terminal:**\
**$18k-$30k**, если сделать:

- красивую панель
- отчёты
- risk dashboard
- журнал сделок
- настройку параметров
- deploy instructions

**Как “готовый печатный станок”** - нет, не тянет.\
И никто серьёзный за такие обещания много не заплатит без live-статистики.

Самая честная одна строчка:

**Наиболее реалистичная цена as-is: около $15k-$18k.**

Если хочешь, я следующим сообщением сделаю ещё более жёсткий разбор в русском стиле:\
**что именно в этом боте добавляет цену, что режет цену, и сколько стоил бы его апгрейд до уровня $30k+**.


#### You:
Make it pro institutional grade maker beaset 

#### ChatGPT:
I’m looking through the bot’s structure and turning this into a sharper institutional-grade upgrade plan, with the biggest gaps first: execution, risk, reconciliation, and observability.


#### ChatGPT:
Да. Если делать из этого **pro / institutional-grade maker beast**, то не “подкрутить пару параметров”, а **перестраивать ядро исполнения**.

Сейчас у тебя уже есть хорошая база: multi-symbol scan, WS top-of-book, maker-entry, maker-exit, SQLite state, reconciliation, paper/live split и execution-aware backtest. Это уже foundation, а не мусор. Но до institutional-grade ему не хватает самого дорогого слоя: **fill-driven execution, risk engine, hard recovery, partial-fill accounting и observability**.

Вот что надо сделать, чтобы он стал реально “зверем”.

## Что сейчас самое слабое

Самая большая дыра - **локальный stop-close**. В текущем виде `force_close()` просто закрывает позицию в локальной БД по bid/ask и сам файл прямо пишет, что для строгой live-версии нужен IOC/market-like protective order. Для institutional-grade это неприемлемо: риск не должен “закрываться на бумаге”, он должен закрываться **реальным ордером на бирже**.

Вторая дыра - **нет нормальной private execution stream архитектуры**. У тебя market data идёт по WS, а order lifecycle в основном дотягивается через REST reconcile. Это норм для foundation, но слабовато для серьёзного maker engine, потому что тебе нужны быстрые события по:

- accepted
- open
- partial fill
- full fill
- cancel ack
- reject
- reduce-only failures
- stale replace races

Сейчас это не выглядит как полноценная event-driven OMS.

Третья дыра - **partial fills и inventory accounting**. Код уже умеет хранить ордера и позиции, но из того, что видно, архитектура ещё не выглядит как жёсткая fill-ledger модель с VWAP, leaves\_qty, cum\_qty, per-order realized/unrealized attribution. Это очень важно для maker-бота.

## Во что это надо превратить

Не “бот”, а систему из 7 слоёв:

### 1. Market Data Engine

Нужен не просто best bid/ask snapshot, а:

- L2 depth cache
- sequence handling
- stale-book detection
- book resync on gap
- quote age checks
- local imbalance metrics
- trade tape / aggressor flow
- mark/index/funding snapshots

Maker engine без нормального L2 - полуслепой.

### 2. OMS / EMS

Нужен полноценный execution layer:

- new order
- cancel
- cancel/replace
- post-only retry ladder
- order state machine
- partial fill aggregation
- duplicate event protection
- client order id idempotency
- order ack timeout logic

Сейчас у тебя ордерный цикл есть, но institutional-grade требует **state machine**, а не просто “insert/update order row”.

### 3. Position & Inventory Engine

Нужны:

- net position
- gross exposure
- symbol exposure
- sector/bucket exposure
- inventory skew quoting
- inventory decay
- quote throttling when inventory offside
- hard caps per symbol and global

У тебя есть `inventory_limit_per_symbol`, но зверь начинается там, где бот меняет котировки из-за inventory pressure, а не просто запрещает лишний вход.

### 4. Risk Engine

Отдельный слой, не смешанный со strategy:

- max loss per symbol
- max daily loss
- max open notional
- max concurrent positions
- max stale orders
- connectivity circuit breaker
- kill switch
- quote ban on abnormal spread / abnormal latency
- funding/event blackout windows

И главное: риск должен уметь **останавливать OMS**, а не просто писать event в БД.

### 5. Strategy / Quoter

Не просто `score -> buy/sell`, а:

- fair value
- reservation price
- skew by inventory
- spread widening by vol
- spread widening by adverse selection
- quote size by queue quality
- quote suppression on toxic flow
- asymmetric bid/ask sizing

Сейчас твой alpha норм как foundation, но для institutional-grade нужен **market making model**, а не просто signal model.

### 6. Reconciliation & Recovery

При рестарте система должна:

- загрузить все open orders с exchange
- загрузить positions
- сопоставить local/exchange state
- найти ghost orders
- найти orphan positions
- восстановить working state
- отменить опасные сироты
- пересчитать inventory
- восстановить last known quote regime

Вот это и даёт настоящее “production-ready”.

### 7. Observability

Нужно:

- Prometheus metrics
- structured JSON logs
- alerting
- fill latency
- order reject rate
- cancel/replace rate
- maker fill ratio
- adverse selection after fill
- PnL by symbol
- realized vs unrealized
- inventory skew stats
- quote uptime

Без этого institutional-grade никто серьёзно не назовёт.

## Что я бы поменял первым

Если резать по приоритету, то топ-8 такой:

**1. Убрать локальный fake stop-close**\
Сделать реальный protective execution path. Это самый критичный апгрейд.

**2. Вынести OMS в отдельный state machine**\
`NEW -> ACK -> OPEN -> PARTIAL -> FILLED / CANCELLED / REJECTED`

**3. Добавить private order/fill stream**\
Чтобы позиция открывалась и закрывалась по факту fill events, а не по догадке reconciliation.

**4. Сделать cancel/replace quoting engine**\
Сейчас stale cancel есть, но нужен системный quote manager с rate limits и priority rules.

**5. Добавить inventory-skew model**\
Чтобы бот не просто входил, а управлял направленным риском.

**6. Перестроить backtester в event replay model**\
Сейчас execution-aware backtest - это плюс, но всё ещё модель. Для высокого уровня нужен хотя бы replay по более богатым market events.

**7. Добавить circuit breakers**\
Связь, спред, reject burst, stale books, funding spikes, abnormal slippage.

**8. Разбить single file на модули**\
`config.py`, `market_data.py`, `oms.py`, `risk.py`, `strategy.py`, `reconcile.py`, `db.py`, `main.py`

## Как будет выглядеть уже “зверь”

Минимальный institutional-grade контур:

- **MarketDataService**
- **ExecutionService**
- **OrderManager**
- **PositionManager**
- **RiskManager**
- **QuoteEngine**
- **ReconcileService**
- **BacktestReplayEngine**
- **Metrics/Alerts**
- **Persistence layer**

И поверх этого:

- live mode
- paper mode
- replay mode
- scan mode
- health endpoints
- operator dashboard

## Честно: насколько далеко текущий файл от этого

Не на 10%, а примерно на **45-55% пути по инженерии**.\
То есть база есть, но самое трудное ещё впереди.

Он уже умеет:

- сканировать
- считать сигналы
- ставить maker orders
- держать локальное состояние
- частично reconciliеить exchange state

Но institutional-grade начинается там, где система умеет:

- переживать рестарт без потери контроля
- корректно вести partial fills
- агрессивно защищать риск
- не врать себе о закрытии позиции
- давать оператору мгновенную телеметрию

## Мой вердикт

**Да, из этого можно сделать institutional-grade maker beast.**\
Но это уже не “подправить бот”, а **сделать полноценный execution/risk platform rewrite вокруг текущей базы**.

Самый правильный путь:

1. сначала **OMS + risk + real protective exits**
2. потом **private fills + partial fills + recovery**
3. потом **inventory skew + smarter quoting**
4. потом **metrics, alerts, replay backtest**
5. потом **modularization and deployment**

Если хочешь, следующим сообщением я могу дать тебе **жёсткий blueprint v2**:\
**точную структуру файлов и классов для institutional-grade rewrite именно под Gate.io**.


#### You:
Appraise in russian this file  #!/usr/bin/env python3

# -*- coding: utf-8 -*-

“””
gate_mm_engine.py  —  Production multi-ticker market maker for Gate.io futures
Optimised for 0-10 cent nominal contracts (DOGE, XRP, TRX, ADA …)

Architecture
────────────
TickerEngine   per-symbol state machine
Signal loop  AI ensemble (local + OR + Groq) → directional alpha
MM loop      quote both sides, skew inventory, reprice on tick
Fill loop    fill detection (exchange poll or paper simulation)
Reconciler     startup + periodic exchange sync
Backtest       walk-forward with realistic maker fill model
Database       SQLite, all state persistent
UIServer       embedded HTTP, no Flask dep

Market-maker flow
─────────────────
α > 0 (bull) → widen ask, tighten bid   (lean long)
α < 0 (bear) → widen bid, tighten ask   (lean short)
Inventory skew reduces quote size on heavy side
After entry fill → opposite resting exit at TP price
SL via price-trigger order
Stale quotes cancelled & repriced every REPRICE_SECONDS

0-cent nominal notes
────────────────────
Gate.io quanto multiplier for e.g. DOGE_USDT = 1 (1 contract = 1 DOGE)
At price 0.08, 1 contract ≈ $0.08 nominal.
Minimum size = 1 contract.  Max risk = RISK_USD / price.

Install
───────
pip install requests pandas pandas_ta numpy python-dotenv

ENV (prefix multi-ticker with TICKERS=DOGE_USDT,XRP_USDT,TRX_USDT)
───
GATE_API_KEY=
GATE_API_SECRET=
TICKERS=DOGE_USDT,XRP_USDT,TRX_USDT
LIVE_TRADING=false
ALLOW_NEW_ENTRIES=false
RISK_USD=10
LEVERAGE=3
SPREAD_TICKS=2
ALPHA_WEIGHT=0.4
INVENTORY_SKEW=0.5
REPRICE_SECONDS=8
QUOTE_TTL_SECONDS=30
SIGNAL_INTERVAL_SEC=60
EXEC_INTERVAL_SEC=3
APP_PORT=8787
DB_PATH=gate_mm.db
“””

from **future** import annotations

import os, sys, json, time, math, hmac, hashlib, sqlite3
import logging, threading, traceback, signal as _signal
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse, urlencode

import numpy as np
import pandas as pd
import pandas_ta as ta
import requests
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════

# 1. CONFIG

# ═══════════════════════════════════════════════════════════

@dataclass
class Config:
# Gate
gate_api_key: str       = os.getenv(“GATE_API_KEY”, “”)
gate_api_secret: str    = os.getenv(“GATE_API_SECRET”, “”)
gate_base_url: str      = os.getenv(“GATE_BASE_URL”, “https://api.gateio.ws/api/v4”)
settle: str             = os.getenv(“GATE_SETTLE”, “usdt”).lower()

```
# Multi-ticker (comma-separated)
tickers_raw: str        = os.getenv("TICKERS", "DOGE_USDT,XRP_USDT,TRX_USDT")

# AI
openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
openrouter_model: str   = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
openrouter_url: str     = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
groq_api_key: str       = os.getenv("GROQ_API_KEY", "")
groq_model: str         = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
groq_url: str           = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")

# Execution
live_trading: bool      = os.getenv("LIVE_TRADING", "false").lower() == "true"
allow_new_entries: bool = os.getenv("ALLOW_NEW_ENTRIES", "false").lower() == "true"
post_only: bool         = os.getenv("POST_ONLY", "true").lower() == "true"

# Sizing
risk_usd: float         = float(os.getenv("RISK_USD", "10"))
leverage: int           = int(os.getenv("LEVERAGE", "3"))
max_pos_per_ticker: int = int(os.getenv("MAX_POS_PER_TICKER", "1"))

# MM params
spread_ticks: int       = int(os.getenv("SPREAD_TICKS", "2"))       # half-spread in ticks each side
alpha_weight: float     = float(os.getenv("ALPHA_WEIGHT", "0.4"))   # how hard to lean quotes on signal
inventory_skew: float   = float(os.getenv("INVENTORY_SKEW", "0.5")) # 0=no skew 1=full skew
quote_ttl_sec: int      = int(os.getenv("QUOTE_TTL_SECONDS", "30"))
reprice_sec: int        = int(os.getenv("REPRICE_SECONDS", "8"))

# TP/SL
tp_atr_mult: float      = float(os.getenv("TP_ATR_MULT", "1.0"))
sl_atr_mult: float      = float(os.getenv("SL_ATR_MULT", "0.6"))

# Candles / signal
interval: str           = os.getenv("INTERVAL", "5m")
bars_limit: int         = int(os.getenv("BARS_LIMIT", "600"))
signal_interval_sec: int= int(os.getenv("SIGNAL_INTERVAL_SEC", "60"))
exec_interval_sec: int  = int(os.getenv("EXEC_INTERVAL_SEC", "3"))

# Walk-forward gate
wf_bars: int            = int(os.getenv("WF_BARS", "100"))
wf_min_pass: float      = float(os.getenv("WF_MIN_PASS", "0.52"))
wf_min_r: float         = float(os.getenv("WF_MIN_R", "0.02"))
wf_min_trades: int      = int(os.getenv("WF_MIN_TRADES", "15"))

# Misc
request_timeout: int    = int(os.getenv("REQUEST_TIMEOUT", "15"))
db_path: str            = os.getenv("DB_PATH", "gate_mm.db")
log_path: str           = os.getenv("LOG_PATH", "gate_mm.jsonl")
app_host: str           = os.getenv("APP_HOST", "127.0.0.1")
app_port: int           = int(os.getenv("APP_PORT", "8787"))
max_memory_rows: int    = int(os.getenv("MAX_MEMORY_ROWS", "2000"))

@property
def tickers(self) -> List[str]:
    return [t.strip().upper() for t in self.tickers_raw.split(",") if t.strip()]
```

CFG = Config()

# ═══════════════════════════════════════════════════════════

# 2. LOGGING

# ═══════════════════════════════════════════════════════════

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s | %(levelname)-7s | %(name)s | %(message)s”,
)
log = logging.getLogger(“gate-mm”)

def utcnow() -> str:
return datetime.now(timezone.utc).isoformat()

def sf(x: Any, d: float = 0.0) -> float:
try:
if x is None or (isinstance(x, float) and math.isnan(x)): return d
return float(x)
except: return d

def clamp(x: float, lo: float, hi: float) -> float:
return max(lo, min(hi, x))

def jd(x: Any) -> str:
return json.dumps(x, ensure_ascii=False, separators=(”,”,”:”), default=str)

def append_log(row: dict) -> None:
try:
with open(CFG.log_path, “a”, encoding=“utf-8”) as f:
f.write(json.dumps(row, ensure_ascii=False, default=str) + “\n”)
except: pass

# ═══════════════════════════════════════════════════════════

# 3. POSITION STATES

# ═══════════════════════════════════════════════════════════

class S:
QUOTING  = “quoting”   # entry limit resting
ACTIVE   = “active”    # filled, TP+SL live
CLOSED   = “closed”
CANCEL   = “cancelled”
ERROR    = “error”

# ═══════════════════════════════════════════════════════════

# 4. DATABASE

# ═══════════════════════════════════════════════════════════

class Database:
def **init**(self, path: str):
self.path = path
self._lk = threading.Lock()
self._init()

```
def _cx(self) -> sqlite3.Connection:
    c = sqlite3.connect(self.path, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def _init(self):
    with self._cx() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, ticker TEXT,
            level TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);

        CREATE TABLE IF NOT EXISTS decisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, ticker TEXT NOT NULL, interval TEXT,
            side TEXT, confidence REAL, final_score REAL,
            local_side TEXT, or_side TEXT, groq_side TEXT, memory_bias REAL,
            wf_pass_rate REAL, wf_avg_r REAL, wf_trades INTEGER, wf_allowed INTEGER,
            close REAL, atr REAL, rsi REAL, adx REAL, vol_z REAL,
            dist_ema REAL, trend_gap REAL,
            snapshot TEXT, why TEXT);

        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, ticker TEXT NOT NULL,
            role TEXT NOT NULL,
            side TEXT NOT NULL,
            size INTEGER NOT NULL,
            price REAL, stop_price REAL,
            tif TEXT, reduce_only INTEGER DEFAULT 0,
            pos_id INTEGER,
            exch_id TEXT, exch_price_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            fill_price REAL, fill_ts TEXT,
            req TEXT, resp TEXT, notes TEXT);

        CREATE TABLE IF NOT EXISTS positions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opened_ts TEXT NOT NULL, closed_ts TEXT,
            ticker TEXT NOT NULL, side TEXT NOT NULL,
            state TEXT NOT NULL, source TEXT NOT NULL,
            size INTEGER NOT NULL,
            quote_price REAL, fill_price REAL, fill_ts TEXT,
            tp REAL, sl REAL, atr REAL,
            entry_order_id INTEGER, tp_order_id INTEGER, sl_order_id INTEGER,
            exit_price REAL, exit_ts TEXT, exit_reason TEXT,
            pnl_pct REAL, r_val REAL, notes TEXT);

        CREATE TABLE IF NOT EXISTS backtest_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, ticker TEXT NOT NULL,
            interval TEXT, bars INTEGER,
            total_trades INTEGER, win_rate REAL, avg_r REAL,
            profit_factor REAL, max_dd REAL, sharpe REAL,
            details TEXT);

        CREATE TABLE IF NOT EXISTS kv(
            k TEXT PRIMARY KEY, v TEXT NOT NULL);
        """)
        c.commit()

# ── helpers ──

def _ins(self, table: str, row: dict) -> int:
    cols = list(row.keys())
    sql  = f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join(['?']*len(cols))})"
    with self._lk, self._cx() as c:
        cur = c.execute(sql, [row[k] for k in cols])
        c.commit(); return int(cur.lastrowid)

def _upd(self, table: str, row_id: int, updates: dict):
    if not updates: return
    sets = ",".join(f"{k}=?" for k in updates)
    with self._lk, self._cx() as c:
        c.execute(f"UPDATE {table} SET {sets} WHERE id=?",
                  [*updates.values(), row_id]); c.commit()

def _sel(self, sql: str, params=()) -> List[dict]:
    with self._lk, self._cx() as c:
        return [dict(r) for r in c.execute(sql, params)]

def _one(self, sql: str, params=()) -> Optional[dict]:
    rows = self._sel(sql, params); return rows[0] if rows else None

# ── events ──

def event(self, level: str, kind: str, payload: dict, ticker: str = "") -> None:
    ts = utcnow()
    self._ins("events", {"ts": ts, "ticker": ticker, "level": level,
                          "kind": kind, "payload": jd(payload)})
    append_log({"ts": ts, "level": level, "kind": kind, "ticker": ticker, **payload})

# ── decisions ──

def ins_decision(self, r: dict) -> int: return self._ins("decisions", r)
def recent_decisions(self, ticker: str = "", limit: int = 50) -> List[dict]:
    if ticker:
        return self._sel("SELECT * FROM decisions WHERE ticker=? ORDER BY id DESC LIMIT ?", (ticker, limit))
    return self._sel("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,))

# ── orders ──

def ins_order(self, r: dict) -> int:     return self._ins("orders", r)
def upd_order(self, oid: int, u: dict):  self._upd("orders", oid, u)
def get_order(self, oid: int) -> Optional[dict]:
    return self._one("SELECT * FROM orders WHERE id=?", (oid,))
def recent_orders(self, ticker: str = "", limit: int = 100) -> List[dict]:
    if ticker:
        return self._sel("SELECT * FROM orders WHERE ticker=? ORDER BY id DESC LIMIT ?", (ticker, limit))
    return self._sel("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))

# ── positions ──

def ins_position(self, r: dict) -> int:     return self._ins("positions", r)
def upd_position(self, pid: int, u: dict):  self._upd("positions", pid, u)
def get_position(self, pid: int) -> Optional[dict]:
    return self._one("SELECT * FROM positions WHERE id=?", (pid,))
def open_position(self, ticker: str) -> Optional[dict]:
    return self._one(
        "SELECT * FROM positions WHERE ticker=? AND state NOT IN ('closed','cancelled','error') ORDER BY id DESC LIMIT 1",
        (ticker,))
def all_open_positions(self) -> List[dict]:
    return self._sel("SELECT * FROM positions WHERE state NOT IN ('closed','cancelled','error') ORDER BY id DESC")
def recent_positions(self, ticker: str = "", limit: int = 50) -> List[dict]:
    if ticker:
        return self._sel("SELECT * FROM positions WHERE ticker=? ORDER BY id DESC LIMIT ?", (ticker, limit))
    return self._sel("SELECT * FROM positions ORDER BY id DESC LIMIT ?", (limit,))

# ── backtest ──

def ins_backtest(self, r: dict) -> int: return self._ins("backtest_results", r)
def recent_backtests(self, limit: int = 20) -> List[dict]:
    return self._sel("SELECT * FROM backtest_results ORDER BY id DESC LIMIT ?", (limit,))

# ── events read ──

def recent_events(self, ticker: str = "", limit: int = 50) -> List[dict]:
    if ticker:
        return self._sel("SELECT * FROM events WHERE ticker=? ORDER BY id DESC LIMIT ?", (ticker, limit))
    return self._sel("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))

# ── kv ──

def set_kv(self, k: str, v: dict):
    with self._lk, self._cx() as c:
        c.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                  (k, json.dumps(v, default=str))); c.commit()

def get_kv(self, k: str, default: Optional[dict] = None) -> dict:
    row = self._one("SELECT v FROM kv WHERE k=?", (k,))
    if not row: return default or {}
    try: return json.loads(row["v"])
    except: return default or {}
```

DB = Database(CFG.db_path)

# ═══════════════════════════════════════════════════════════

# 5. GATE CLIENT

# ═══════════════════════════════════════════════════════════

class GateClient:
def **init**(self):
self.session = requests.Session()
self._specs: Dict[str, dict] = {}
self._specs_ts: Dict[str, float] = {}

```
def _sign(self, method: str, path: str, query: str = "", body: str = "") -> dict:
    ts       = str(int(time.time()))
    bh       = hashlib.sha512(body.encode()).hexdigest()
    msg      = f"{method}\n/api/v4{path}\n{query}\n{bh}\n{ts}"
    sig      = hmac.new(CFG.gate_api_secret.encode(), msg.encode(), hashlib.sha512).hexdigest()
    return {"KEY": CFG.gate_api_key, "Timestamp": ts, "SIGN": sig,
            "Accept": "application/json", "Content-Type": "application/json"}

def _pub(self, path: str, params: dict = None) -> Any:
    r = self.session.get(f"{CFG.gate_base_url}{path}",
                         params=params or {}, timeout=CFG.request_timeout)
    r.raise_for_status(); return r.json()

def _priv(self, method: str, path: str, params: dict = None, body: dict = None) -> Any:
    params = params or {}; body = body or {}
    q = urlencode(params)
    bs = jd(body) if body else ""
    hdr = self._sign(method.upper(), path, q, bs)
    r = self.session.request(method.upper(),
                              f"{CFG.gate_base_url}{path}",
                              params=params,
                              data=bs or None,
                              headers=hdr,
                              timeout=CFG.request_timeout)
    r.raise_for_status()
    return r.json() if r.text.strip() else {}

# ── Market data ──

def candles(self, contract: str, interval: str, limit: int = 500) -> pd.DataFrame:
    raw = self._pub(f"/futures/{CFG.settle}/candlesticks",
                    {"contract": contract, "interval": interval, "limit": min(limit, 2000)})
    if not isinstance(raw, list) or not raw: raise RuntimeError("No candles")
    rows = []
    for it in raw:
        if isinstance(it, dict):
            rows.append({"t":it["t"],"o":it["o"],"h":it["h"],"l":it["l"],"c":it["c"],"v":it["v"]})
        elif isinstance(it, list) and len(it) >= 6:
            rows.append({"t":it[0],"v":it[1],"c":it[2],"h":it[3],"l":it[4],"o":it[5]})
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["t"].astype(int), unit="s", utc=True)
    for col in "ohlcv": df[col] = pd.to_numeric(df[col], errors="coerce")
    return (df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"})
              [["timestamp","open","high","low","close","volume"]]
              .sort_values("timestamp").reset_index(drop=True))

def ticker(self, contract: str) -> dict:
    d = self._pub(f"/futures/{CFG.settle}/tickers", {"contract": contract})
    return d[0] if isinstance(d, list) and d else (d if isinstance(d, dict) else {})

def orderbook(self, contract: str, limit: int = 1) -> dict:
    try:
        raw  = self._pub(f"/futures/{CFG.settle}/order_book",
                         {"contract": contract, "interval": "0", "limit": limit})
        bids = raw.get("bids", [])
        asks = raw.get("asks", [])
        def p(x): return sf(x.get("p") if isinstance(x, dict) else (x if isinstance(x, (int,float)) else 0))
        bb = p(bids[0]) if bids else 0.0
        ba = p(asks[0]) if asks else 0.0
        return {"bid": bb, "ask": ba, "mid": (bb + ba) / 2 if bb and ba else 0.0}
    except: return {"bid": 0.0, "ask": 0.0, "mid": 0.0}

def specs(self, contract: str) -> dict:
    now = time.time()
    if contract in self._specs and now - self._specs_ts.get(contract, 0) < 3600:
        return self._specs[contract]
    s = self._pub(f"/futures/{CFG.settle}/contracts/{contract}")
    self._specs[contract] = s
    self._specs_ts[contract] = now
    return s

def exchange_positions(self) -> List[dict]:
    try: return self._priv("GET", f"/futures/{CFG.settle}/positions") or []
    except: return []

def exchange_position(self, contract: str) -> dict:
    try: return self._priv("GET", f"/futures/{CFG.settle}/positions/{contract}") or {}
    except: return {}

def set_leverage(self, contract: str, lev: int) -> dict:
    try:
        return self._priv("POST", f"/futures/{CFG.settle}/positions/{contract}/leverage",
                           body={"leverage": str(lev), "cross_leverage_limit": "0"})
    except Exception as e: return {"error": str(e)}

# ── Orders ──

def place_limit(self, contract: str, size: int, price: float,
                tif: str = "poc", reduce_only: bool = False, text: str = "") -> dict:
    path = f"/futures/{CFG.settle}/orders"
    return self._priv("POST", path, body={
        "contract": contract, "size": size,
        "price": f"{price:.10f}", "tif": tif,
        "reduce_only": reduce_only,
        **({"text": text[:28]} if text else {}),
    })

def place_stop(self, contract: str, size: int, trigger: float, expire: int = 86400) -> dict:
    # price-triggered market order (SL)
    rule = 2 if size < 0 else 1   # 2=price<=trigger (close long), 1=price>=trigger (close short)
    return self._priv("POST", f"/futures/{CFG.settle}/price_orders", body={
        "initial": {"contract": contract, "size": size,
                    "price": "0", "tif": "ioc", "reduce_only": True},
        "trigger": {"strategy_type": 0, "price_type": 1,
                    "price": f"{trigger:.10f}", "rule": rule, "expiration": expire},
    })

def cancel(self, exch_id: str) -> dict:
    try: return self._priv("DELETE", f"/futures/{CFG.settle}/orders/{exch_id}")
    except Exception as e: return {"error": str(e)}

def cancel_stop(self, exch_id: str) -> dict:
    try: return self._priv("DELETE", f"/futures/{CFG.settle}/price_orders/{exch_id}")
    except Exception as e: return {"error": str(e)}

def order_status(self, exch_id: str) -> dict:
    try: return self._priv("GET", f"/futures/{CFG.settle}/orders/{exch_id}")
    except: return {}

def stop_status(self, exch_id: str) -> dict:
    try: return self._priv("GET", f"/futures/{CFG.settle}/price_orders/{exch_id}")
    except: return {}
```

GATE = GateClient()

# ═══════════════════════════════════════════════════════════

# 6. INDICATORS

# ═══════════════════════════════════════════════════════════

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
x = df.copy()
x[“ema9”]  = ta.ema(x[“close”], length=9)
x[“ema21”] = ta.ema(x[“close”], length=21)
x[“sma20”] = ta.sma(x[“close”], length=20)
x[“sma50”] = ta.sma(x[“close”], length=50)
x[“rsi”]   = ta.rsi(x[“close”], length=14)
x[“atr”]   = ta.atr(x[“high”], x[“low”], x[“close”], length=14)
adx = ta.adx(x[“high”], x[“low”], x[“close”], length=14)
if adx is not None and not adx.empty and “ADX_14” in adx:
x[“adx”] = adx[“ADX_14”]
else: x[“adx”] = 0.0
bb = ta.bbands(x[“close”], length=20, std=2)
if bb is not None and not bb.empty:
x[“bbu”] = bb.get(“BBU_20_2.0”, np.nan)
x[“bbl”] = bb.get(“BBL_20_2.0”, np.nan)
x[“bbm”] = bb.get(“BBM_20_2.0”, np.nan)
x[“bbw”] = (x[“bbu”] - x[“bbl”]) / x[“bbm”].replace(0, np.nan)
else: x[“bbw”] = 0.0
x[“obv”]   = ta.obv(x[“close”], x[“volume”])
x[“r1”]    = x[“close”].pct_change(1)
x[“r4”]    = x[“close”].pct_change(4)
x[“r16”]   = x[“close”].pct_change(16)
vol_mean   = x[“volume”].rolling(20).mean()
vol_std    = x[“volume”].rolling(20).std()
x[“volz”]  = (x[“volume”] - vol_mean) / vol_std.replace(0, np.nan)
x[“dea”]   = (x[“close”] - x[“ema21”]) / x[“atr”].replace(0, np.nan)
x[“tgap”]  = (x[“ema9”] - x[“ema21”]) / x[“close”].replace(0, np.nan)
return x

SNAP_COLS = [“close”,“ema9”,“ema21”,“sma20”,“sma50”,“rsi”,“atr”,“adx”,
“bbw”,“r1”,“r4”,“r16”,“volz”,“dea”,“tgap”]

def snap(df: pd.DataFrame) -> dict:
r = df.iloc[-1]
return {“ts”: str(r[“timestamp”]), **{c: sf(r.get(c)) for c in SNAP_COLS}}

# ═══════════════════════════════════════════════════════════

# 7. LOCAL SIGNAL MODEL

# ═══════════════════════════════════════════════════════════

def local_signal(s: dict) -> Tuple[str, float, dict]:
p: dict = {}
p[“trend”]    = 0.8  if s[“ema9”] > s[“ema21”] else (-0.8  if s[“ema9”] < s[“ema21”] else 0.0)
p[“rsi”]      = 0.7  if s[“rsi”]  < 32         else (-0.7  if s[“rsi”]  > 68         else 0.0)
p[“mom”]      = float(np.clip(s[“r4”] * 100, -1.0, 1.0))
p[“dist”]     = 0.5  if s[“dea”]  < -1.5        else (-0.5 if s[“dea”]  > 1.5        else 0.0)
p[“vol”]      = float(np.clip(s[“volz”] / 3.0, -0.4, 0.4))
p[“adx”]      = (0.2  if s[“adx”] > 22 and s[“ema9”] > s[“ema21”] else
-0.2 if s[“adx”] > 22 and s[“ema9”] < s[“ema21”] else 0.0)
sc = sum(p.values())
side = “buy” if sc > 0.35 else (“sell” if sc < -0.35 else “hold”)
return side, min(abs(sc) / 2.0, 0.95), p

# ═══════════════════════════════════════════════════════════

# 8. MEMORY BIAS

# ═══════════════════════════════════════════════════════════

def memory_bias(s: dict, ticker: str) -> Tuple[float, dict]:
rows = DB.recent_decisions(ticker, CFG.max_memory_rows)
if not rows: return 0.0, {“n”: 0}
df = pd.DataFrame(rows)
for col in [“rsi”,“dea”,“tgap”,“volz”,“wf_avg_r”]:
if col in df.columns: df[col] = pd.to_numeric(df[col], errors=“coerce”)
else: df[col] = 0.0
if “side” not in df.columns: return 0.0, {“n”: 0}
sim = df[
(df[“rsi”].sub(s[“rsi”]).abs()   <= 8)
& (df[“dea”].sub(s[“dea”]).abs() <= 1.0)
& (df[“tgap”].sub(s[“tgap”]).abs() <= 0.006)
& (df[“volz”].sub(s[“volz”]).abs() <= 1.5)
& (df[“side”].isin([“buy”,“sell”]))
].copy()
if sim.empty: return 0.0, {“n”: 0}
bg = sim.loc[sim[“side”]==“buy”,  “wf_avg_r”].mean()
sg = sim.loc[sim[“side”]==“sell”, “wf_avg_r”].mean()
bg = 0.0 if pd.isna(bg) else float(bg)
sg = 0.0 if pd.isna(sg) else float(sg)
return float(np.clip(bg - sg, -0.75, 0.75)), {“n”: len(sim), “buy”: bg, “sell”: sg}

# ═══════════════════════════════════════════════════════════

# 9. AI VOTING

# ═══════════════════════════════════════════════════════════

def _ai_prompt(ticker: str, s: dict, ls: str, lc: float, lp: dict, mb: float) -> str:
return (
“Return ONLY valid JSON (no markdown):\n”
‘{“side”:“buy|sell|hold”,“confidence”:0.0-1.0,“reason”:“one sentence”,’
‘“risk_flags”:[]}\n\n’
f”ticker={ticker} interval={CFG.interval}\n”
f”snapshot={jd(s)}\n”
f”local_rule: side={ls} conf={lc:.3f} parts={jd(lp)}\n”
f”memory_bias={mb:.4f}\n”
“Prefer hold if weak/contradictory. conf>0.75 only unusually strong.”
)

def _parse_ai(text: str) -> dict:
for fn in [lambda t: json.loads(t),
lambda t: json.loads(t[t.find(”{”):t.rfind(”}”)+1])]:
try: return fn(text)
except: pass
return {“side”:“hold”,“confidence”:0.0,“reason”:“parse_err”,“risk_flags”:[“parse_error”]}

def _post_ai(url: str, key: str, model: str, prompt: str) -> dict:
if not key:
return {“side”:“hold”,“confidence”:0.0,“reason”:“no_key”,“risk_flags”:[“no_key”]}
try:
r = requests.post(url,
headers={“Authorization”: f”Bearer {key}”, “Content-Type”: “application/json”},
json={“model”: model,
“messages”: [{“role”: “user”, “content”: prompt}],
“temperature”: 0.2, “max_tokens”: 200},
timeout=CFG.request_timeout)
r.raise_for_status()
return _parse_ai(r.json()[“choices”][0][“message”][“content”])
except Exception as e:
return {“side”:“hold”,“confidence”:0.0,“reason”:str(e),“risk_flags”:[“api_err”]}

def _sv(side: str, conf: float) -> float:
s = (side or “hold”).lower()
c = clamp(float(conf), 0.0, 1.0)
return c if s == “buy” else (-c if s == “sell” else 0.0)

def ensemble(ls: str, lc: float, ov: dict, gv: dict, mb: float
) -> Tuple[str, float, float, dict]:
fs = float(clamp(
0.40 * _sv(ls, lc)
+ 0.30 * _sv(ov.get(“side”,“hold”), sf(ov.get(“confidence”)))
+ 0.30 * _sv(gv.get(“side”,“hold”), sf(gv.get(“confidence”)))
+ 0.20 * mb, -1.0, 1.0))
side = “buy” if fs > 0.18 else (“sell” if fs < -0.18 else “hold”)
return side, min(abs(fs), 0.95), fs, {
“local”: _sv(ls, lc),
“or”: _sv(ov.get(“side”,“hold”), sf(ov.get(“confidence”))),
“groq”: _sv(gv.get(“side”,“hold”), sf(gv.get(“confidence”))),
“mem”: mb, “final”: fs,
“or_reason”: ov.get(“reason”,””), “gr_reason”: gv.get(“reason”,””),
}

# ═══════════════════════════════════════════════════════════

# 10. BACKTEST ENGINE

# ═══════════════════════════════════════════════════════════

def run_backtest(df: pd.DataFrame, ticker: str) -> dict:
“””
Walk-forward maker simulation.
Models maker fill as: buy fills when price dips below quote, sell when rises above.
Accounts for maker rebate vs fee.
“””
MAKER_REBATE = 0.00015  # 0.015% rebate on Gate
FEE_TAKER    = 0.0005   # taker fee for SL exit

```
results = []
start = max(60, len(df) - CFG.wf_bars)
in_trade = False
entry_price = 0.0; entry_side = ""; entry_atr = 0.0
tp = 0.0; sl = 0.0; entry_idx = 0

for i in range(start, len(df) - 1):
    s = snap(df.iloc[:i+1])
    price = sf(df.iloc[i]["close"])
    atr   = sf(df.iloc[i]["atr"])
    hi    = sf(df.iloc[i]["high"])
    lo    = sf(df.iloc[i]["low"])

    if in_trade:
        # Check TP (limit fill — maker rebate)
        if entry_side == "buy" and hi >= tp:
            pnl = (tp - entry_price) / entry_price - FEE_TAKER + MAKER_REBATE * 2
            results.append({"r": (tp - entry_price) / entry_atr if entry_atr else 0,
                             "pnl": pnl, "out": "tp"})
            in_trade = False; continue
        if entry_side == "sell" and lo <= tp:
            pnl = (entry_price - tp) / entry_price - FEE_TAKER + MAKER_REBATE * 2
            results.append({"r": (entry_price - tp) / entry_atr if entry_atr else 0,
                             "pnl": pnl, "out": "tp"})
            in_trade = False; continue
        # Check SL (market/stop — taker fee)
        if entry_side == "buy" and lo <= sl:
            pnl = (sl - entry_price) / entry_price - FEE_TAKER * 2
            results.append({"r": (sl - entry_price) / entry_atr if entry_atr else 0,
                             "pnl": pnl, "out": "sl"})
            in_trade = False; continue
        if entry_side == "sell" and hi >= sl:
            pnl = (entry_price - sl) / entry_price - FEE_TAKER * 2
            results.append({"r": (entry_price - sl) / entry_atr if entry_atr else 0,
                             "pnl": pnl, "out": "sl"})
            in_trade = False; continue
        # Timeout after 12 bars
        if i - entry_idx >= 12:
            ep = sf(df.iloc[i]["close"])
            pnl = ((ep - entry_price) if entry_side == "buy" else (entry_price - ep))
            pnl = pnl / entry_price - FEE_TAKER * 2
            r_val = pnl * entry_price / entry_atr if entry_atr else 0
            results.append({"r": r_val, "pnl": pnl, "out": "timeout"})
            in_trade = False
        continue

    ls, lc, lp = local_signal(s)
    mb, _      = memory_bias(s, ticker)
    alpha      = _sv(ls, lc) + 0.2 * mb
    if abs(alpha) < 0.20: continue
    trade_side = "buy" if alpha > 0 else "sell"
    if atr <= 0: continue

    # Maker entry: quote at bid/ask, fills when market trades through
    # Model: fills at close of next bar if momentum confirms
    quote_price = price  # simplified: mid as entry
    entry_price = quote_price + MAKER_REBATE * quote_price  # net of rebate
    entry_side  = trade_side
    entry_atr   = atr
    entry_idx   = i
    tp = entry_price + atr * CFG.tp_atr_mult if trade_side == "buy" else entry_price - atr * CFG.tp_atr_mult
    sl = entry_price - atr * CFG.sl_atr_mult if trade_side == "buy" else entry_price + atr * CFG.sl_atr_mult
    in_trade = True

if not results:
    return {"ticker": ticker, "total_trades": 0, "win_rate": 0.0,
            "avg_r": -99.0, "profit_factor": 0.0, "max_dd": 0.0, "sharpe": 0.0,
            "wf_allowed": False}

rs   = [x["r"] for x in results]
pnls = [x["pnl"] for x in results]
wins = [r for r in rs if r > 0]
loss = [r for r in rs if r <= 0]

win_rate  = len(wins) / len(rs)
avg_r     = float(np.mean(rs))
pf        = abs(sum(wins) / sum(loss)) if sum(loss) != 0 else 9.99
cum       = np.cumsum(pnls)
roll_max  = np.maximum.accumulate(cum)
dd        = float(np.min(cum - roll_max))
sharpe    = float(np.mean(pnls) / np.std(pnls) * np.sqrt(252)) if np.std(pnls) > 0 else 0.0
wf_ok     = (len(results) >= CFG.wf_min_trades
             and win_rate >= CFG.wf_min_pass
             and avg_r   >= CFG.wf_min_r)

return {
    "ticker": ticker, "total_trades": len(results), "win_rate": win_rate,
    "avg_r": avg_r, "profit_factor": pf, "max_dd": dd, "sharpe": sharpe,
    "wf_allowed": wf_ok,
    "details": jd({"by_outcome": {
        "tp": sum(1 for x in results if x["out"]=="tp"),
        "sl": sum(1 for x in results if x["out"]=="sl"),
        "timeout": sum(1 for x in results if x["out"]=="timeout"),
    }})
}
```

# ═══════════════════════════════════════════════════════════

# 11. MARKET MAKER QUOTE LOGIC

# ═══════════════════════════════════════════════════════════

def compute_size(contract: str, price: float, side: str) -> int:
sp = GATE.specs(contract)
m  = sf(sp.get(“quanto_multiplier”), 0.0)
if m <= 0:
# For contracts where 1 contract = 1 unit (DOGE etc), quanto_multiplier may be 1
# Fallback: assume 1 contract = 1 coin
m = 1.0
notional  = CFG.risk_usd * CFG.leverage
contracts = max(int(notional / max(price * m, 1e-9)), 1)
return contracts if side == “buy” else -contracts

def tick_size(contract: str) -> float:
sp = GATE.specs(contract)
t  = sf(sp.get(“order_price_round”), 0.0001)
return t if t > 0 else 0.0001

def rt(price: float, tick: float) -> float:
if tick <= 0: return price
return round(round(price / tick) * tick, 10)

def mm_quotes(
mid: float, bid: float, ask: float,
alpha: float,       # signed: >0 = bullish, <0 = bearish
atr: float,
tick: float,
) -> Tuple[float, float]:
“””
Returns (entry_bid_price, entry_ask_price) for a 2-sided quote.
Alpha skews both quote prices toward the direction of the signal.
spread_ticks defines the base half-spread from mid.
“””
half = CFG.spread_ticks * tick
skew = clamp(alpha * CFG.alpha_weight, -1.0, 1.0) * half

```
our_bid = rt(bid - half + skew, tick)   # lean up when bullish
our_ask = rt(ask + half + skew, tick)   # lean up when bullish (widen ask side)

# sanity: never cross the book
if our_bid >= ask: our_bid = rt(ask - tick, tick)
if our_ask <= bid: our_ask = rt(bid + tick, tick)
return our_bid, our_ask
```

# ═══════════════════════════════════════════════════════════

# 12. PER-TICKER STATE + EXECUTION ENGINE

# ═══════════════════════════════════════════════════════════

@dataclass
class TickerState:
ticker: str
# Signal
alpha:          float = 0.0
side:           str   = “hold”
confidence:     float = 0.0
atr:            float = 0.0
last_price:     float = 0.0
wf_allowed:     bool  = False
decision_ts:    str   = “”
decision_id:    Optional[int] = None
# Quote tracking
last_bid_quote: float = 0.0
last_ask_quote: float = 0.0
last_quote_ts:  float = 0.0
last_reprice_ts:float = 0.0

TICKER_STATES: Dict[str, TickerState] = {t: TickerState(t) for t in CFG.tickers}

class TickerEngine:
def **init**(self, ticker: str):
self.ticker = ticker
self.log    = logging.getLogger(f”mm.{ticker}”)

```
# ── Signal update (runs every SIGNAL_INTERVAL_SEC) ──

def update_signal(self) -> None:
    try:
        raw = GATE.candles(self.ticker, CFG.interval, CFG.bars_limit)
        df  = add_indicators(raw).dropna().reset_index(drop=True)
        if len(df) < 80: return

        s              = snap(df)
        ls, lc, lp     = local_signal(s)
        mb, mm         = memory_bias(s, self.ticker)

        prompt = _ai_prompt(self.ticker, s, ls, lc, lp, mb)
        ov = _post_ai(CFG.openrouter_url, CFG.openrouter_api_key, CFG.openrouter_model, prompt)
        gv = _post_ai(CFG.groq_url,       CFG.groq_api_key,       CFG.groq_model,       prompt)

        side, conf, fs, why = ensemble(ls, lc, ov, gv, mb)
        bt = run_backtest(df, self.ticker)

        ts = TICKER_STATES[self.ticker]
        ts.alpha       = fs
        ts.side        = side
        ts.confidence  = conf
        ts.atr         = sf(s["atr"])
        ts.wf_allowed  = bt["wf_allowed"]
        ts.decision_ts = utcnow()

        dec_id = DB.ins_decision({
            "ts": ts.decision_ts, "ticker": self.ticker, "interval": CFG.interval,
            "side": side, "confidence": conf, "final_score": fs,
            "local_side": ls, "or_side": ov.get("side"), "groq_side": gv.get("side"),
            "memory_bias": mb,
            "wf_pass_rate": bt["win_rate"], "wf_avg_r": bt["avg_r"],
            "wf_trades": bt["total_trades"], "wf_allowed": 1 if bt["wf_allowed"] else 0,
            "close": sf(s["close"]), "atr": sf(s["atr"]),
            "rsi": sf(s["rsi"]), "adx": sf(s["adx"]),
            "vol_z": sf(s["volz"]), "dist_ema": sf(s["dea"]), "trend_gap": sf(s["tgap"]),
            "snapshot": jd(s), "why": jd({**why, "mem_meta": mm, "bt": bt}),
        })
        ts.decision_id = dec_id

        # Persist backtest
        DB.ins_backtest({
            "ts": ts.decision_ts, "ticker": self.ticker, "interval": CFG.interval,
            "bars": len(df), "total_trades": bt["total_trades"],
            "win_rate": bt["win_rate"], "avg_r": bt["avg_r"],
            "profit_factor": bt["profit_factor"], "max_dd": bt["max_dd"],
            "sharpe": bt["sharpe"], "details": bt.get("details", "{}"),
        })

        DB.event("INFO", "signal_updated", {
            "side": side, "conf": conf, "alpha": fs,
            "wf": bt["wf_allowed"], "price": ts.last_price,
        }, self.ticker)
        self.log.info(f"signal {side} α={fs:.3f} wf={bt['wf_allowed']}")

    except Exception as e:
        self.log.error(f"signal error: {e}")
        DB.event("ERROR", "signal_error", {"error": str(e), "tb": traceback.format_exc()}, self.ticker)

# ── Execution tick (runs every EXEC_INTERVAL_SEC) ──

def exec_tick(self) -> None:
    try:
        tk  = GATE.ticker(self.ticker)
        ob  = GATE.orderbook(self.ticker)
        bid = sf(ob["bid"]); ask = sf(ob["ask"])
        mid = sf(ob["mid"])
        price = sf(tk.get("last") or mid)
        if price <= 0: return

        ts = TICKER_STATES[self.ticker]
        ts.last_price = price

        pos = DB.open_position(self.ticker)

        if pos is None:
            self._maybe_quote_entry(bid, ask, mid, price, ts)
        elif pos["state"] == S.QUOTING:
            self._tick_quoting(pos, price, bid, ask, ts)
        elif pos["state"] == S.ACTIVE:
            self._tick_active(pos, price)

    except Exception as e:
        self.log.error(f"exec tick error: {e}")

def _maybe_quote_entry(self, bid: float, ask: float, mid: float,
                        price: float, ts: TickerState) -> None:
    if not CFG.allow_new_entries: return
    if not ts.wf_allowed and CFG.live_trading: return
    if ts.side not in ("buy","sell"): return
    if ts.atr <= 0: return

    tick   = tick_size(self.ticker)
    alpha  = ts.alpha
    q_bid, q_ask = mm_quotes(mid, bid, ask, alpha, ts.atr, tick)
    now    = time.time()

    # Reprice gate
    if now - ts.last_reprice_ts < CFG.reprice_sec: return

    # Cancel any existing entry orders
    self._cancel_open_entry_orders()

    entry_price = q_bid if ts.side == "buy" else q_ask
    size        = compute_size(self.ticker, price, ts.side)
    tp          = rt(entry_price + ts.atr * CFG.tp_atr_mult if ts.side == "buy"
                     else entry_price - ts.atr * CFG.tp_atr_mult, tick)
    sl          = rt(entry_price - ts.atr * CFG.sl_atr_mult if ts.side == "buy"
                     else entry_price + ts.atr * CFG.sl_atr_mult, tick)

    order_row = {
        "ts": utcnow(), "ticker": self.ticker, "role": "entry",
        "side": ts.side, "size": size, "price": entry_price, "stop_price": None,
        "tif": "poc" if CFG.post_only else "gtc",
        "reduce_only": 0, "pos_id": None,
        "exch_id": None, "exch_price_id": None, "status": "pending",
        "fill_price": None, "fill_ts": None,
        "req": jd({"size": size, "price": entry_price}),
        "resp": "{}", "notes": f"entry_{ts.side}",
    }
    order_id = DB.ins_order(order_row)

    pos_row = {
        "opened_ts": utcnow(), "closed_ts": None,
        "ticker": self.ticker, "side": ts.side,
        "state": S.QUOTING, "source": "live" if CFG.live_trading else "paper",
        "size": abs(size), "quote_price": entry_price,
        "fill_price": None, "fill_ts": None,
        "tp": tp, "sl": sl, "atr": ts.atr,
        "entry_order_id": order_id,
        "tp_order_id": None, "sl_order_id": None,
        "exit_price": None, "exit_ts": None, "exit_reason": None,
        "pnl_pct": None, "r_val": None, "notes": None,
    }
    pos_id = DB.ins_position(pos_row)
    DB.upd_order(order_id, {"pos_id": pos_id})

    if CFG.live_trading:
        try:
            resp   = GATE.place_limit(self.ticker, size, entry_price,
                                       tif="poc" if CFG.post_only else "gtc",
                                       text=f"mm_e_{ts.side[:1]}")
            exch_id = str(resp.get("id") or "")
            DB.upd_order(order_id, {"exch_id": exch_id, "status": "open", "resp": jd(resp)})
            DB.event("INFO", "entry_quoted", {
                "side": ts.side, "price": entry_price, "size": size, "exch_id": exch_id
            }, self.ticker)
        except Exception as e:
            DB.upd_order(order_id, {"status": "error", "resp": jd({"error": str(e)})})
            DB.upd_position(pos_id, {"state": S.ERROR, "notes": str(e)})
            DB.event("ERROR", "entry_quote_error", {"error": str(e)}, self.ticker)
            return
    else:
        DB.upd_order(order_id, {"status": "open", "resp": jd({"paper": True})})
        DB.event("INFO", "paper_entry_quoted",
                 {"side": ts.side, "price": entry_price, "size": size}, self.ticker)

    ts.last_bid_quote = q_bid
    ts.last_ask_quote = q_ask
    ts.last_quote_ts  = time.time()
    ts.last_reprice_ts = time.time()
    self.log.info(f"entry quoted {ts.side} @ {entry_price:.6f} sz={size}")

def _cancel_open_entry_orders(self) -> None:
    for od in DB.recent_orders(self.ticker, limit=20):
        if od["role"] != "entry" or od["status"] not in ("open", "pending"): continue
        if od.get("exch_id") and CFG.live_trading:
            GATE.cancel(od["exch_id"])
        DB.upd_order(od["id"], {"status": "cancelled"})
        pos_id = od.get("pos_id")
        if pos_id:
            pos = DB.get_position(pos_id)
            if pos and pos["state"] == S.QUOTING:
                DB.upd_position(pos_id, {"state": S.CANCEL, "closed_ts": utcnow()})

def _tick_quoting(self, pos: dict, price: float, bid: float, ask: float,
                   ts: TickerState) -> None:
    order = DB.get_order(int(pos["entry_order_id"])) if pos.get("entry_order_id") else None
    if not order: return

    filled     = False
    fill_price = price

    if CFG.live_trading:
        exch_id = order.get("exch_id")
        if not exch_id: return
        resp = GATE.order_status(exch_id)
        if not resp: return
        status    = resp.get("status", "")
        finish_as = resp.get("finish_as", "")
        if status == "finished" and finish_as == "filled":
            fill_price = sf(resp.get("fill_price") or resp.get("price") or price)
            filled = True
            DB.upd_order(int(order["id"]), {"status": "filled", "resp": jd(resp)})
        elif status == "finished" and finish_as in ("cancelled","ioc","poc","stp"):
            DB.upd_order(int(order["id"]), {"status": "cancelled"})
            DB.upd_position(int(pos["id"]), {"state": S.CANCEL, "closed_ts": utcnow()})
            DB.event("INFO", "entry_cancelled", {"finish_as": finish_as}, self.ticker)
            return
    else:
        # Paper: fill if price touches our quote
        qp = sf(pos["quote_price"])
        side = pos["side"]
        if side == "buy"  and price <= qp: fill_price = qp; filled = True
        if side == "sell" and price >= qp: fill_price = qp; filled = True

    if filled:
        self._on_entry_filled(pos, fill_price)
        return

    # Age check
    age = time.time() - ts.last_quote_ts
    if age > CFG.quote_ttl_sec:
        self.log.info(f"entry quote TTL expired pos={pos['id']}, repricing")
        self._cancel_open_entry_orders()
        ts.last_reprice_ts = 0.0  # force reprice next tick

def _on_entry_filled(self, pos: dict, fill_price: float) -> None:
    pos_id  = int(pos["id"])
    side    = pos["side"]
    size    = int(pos["size"])
    tp      = sf(pos["tp"])
    sl      = sf(pos["sl"])
    atr     = sf(pos["atr"])
    tick    = tick_size(self.ticker)

    DB.upd_order(int(pos["entry_order_id"]), {
        "fill_price": fill_price, "fill_ts": utcnow(), "status": "filled"
    })
    DB.upd_position(pos_id, {
        "state": S.ACTIVE, "fill_price": fill_price, "fill_ts": utcnow()
    })

    exit_size  = -size if side == "buy" else size
    exit_side  = "sell" if side == "buy" else "buy"

    # TP limit order (maker)
    tp_row = {
        "ts": utcnow(), "ticker": self.ticker, "role": "tp",
        "side": exit_side, "size": exit_size, "price": tp, "stop_price": None,
        "tif": "gtc", "reduce_only": 1, "pos_id": pos_id,
        "exch_id": None, "exch_price_id": None, "status": "pending",
        "fill_price": None, "fill_ts": None,
        "req": jd({"size": exit_size, "price": tp}), "resp": "{}", "notes": "tp",
    }
    tp_id = DB.ins_order(tp_row)

    # SL stop order (trigger market)
    sl_row = {
        "ts": utcnow(), "ticker": self.ticker, "role": "sl",
        "side": exit_side, "size": exit_size, "price": None, "stop_price": sl,
        "tif": "ioc", "reduce_only": 1, "pos_id": pos_id,
        "exch_id": None, "exch_price_id": None, "status": "pending",
        "fill_price": None, "fill_ts": None,
        "req": jd({"size": exit_size, "trigger": sl}), "resp": "{}", "notes": "sl",
    }
    sl_id = DB.ins_order(sl_row)
    DB.upd_position(pos_id, {"tp_order_id": tp_id, "sl_order_id": sl_id})

    if CFG.live_trading:
        try:
            tr = GATE.place_limit(self.ticker, exit_size, tp, tif="gtc",
                                   reduce_only=True, text="mm_tp")
            DB.upd_order(tp_id, {"exch_id": str(tr.get("id","")),
                                  "status": "open", "resp": jd(tr)})
        except Exception as e:
            DB.upd_order(tp_id, {"status": "error", "resp": jd({"error": str(e)})})
            DB.event("ERROR", "tp_place_err", {"error": str(e)}, self.ticker)
        try:
            sr = GATE.place_stop(self.ticker, exit_size, sl)
            DB.upd_order(sl_id, {"exch_price_id": str(sr.get("id","")),
                                  "status": "open", "resp": jd(sr)})
        except Exception as e:
            DB.upd_order(sl_id, {"status": "error", "resp": jd({"error": str(e)})})
            DB.event("ERROR", "sl_place_err", {"error": str(e)}, self.ticker)
    else:
        DB.upd_order(tp_id, {"status": "open", "resp": jd({"paper": True})})
        DB.upd_order(sl_id, {"status": "open", "resp": jd({"paper": True})})

    DB.event("INFO", "entry_filled_exits_placed", {
        "pos_id": pos_id, "side": side,
        "fill": fill_price, "tp": tp, "sl": sl, "atr": atr,
    }, self.ticker)
    self.log.info(f"fill pos={pos_id} {side} @ {fill_price:.6f} tp={tp:.6f} sl={sl:.6f}")

def _tick_active(self, pos: dict, price: float) -> None:
    tp_id = pos.get("tp_order_id")
    sl_id = pos.get("sl_order_id")

    if CFG.live_trading:
        if tp_id:
            to = DB.get_order(int(tp_id))
            if to and to["status"] == "open" and to.get("exch_id"):
                r = GATE.order_status(to["exch_id"])
                if r.get("status") == "finished" and r.get("finish_as") == "filled":
                    fp = sf(r.get("fill_price") or price)
                    DB.upd_order(int(tp_id), {"status":"filled","fill_price":fp,"fill_ts":utcnow()})
                    self._close_position(pos, fp, "tp", int(sl_id) if sl_id else None)
                    return
        if sl_id:
            so = DB.get_order(int(sl_id))
            if so and so["status"] == "open" and so.get("exch_price_id"):
                r = GATE.stop_status(so["exch_price_id"])
                if r.get("status") in ("finished","triggered"):
                    fp = sf(r.get("trigger",{}).get("price") or price)
                    DB.upd_order(int(sl_id), {"status":"filled","fill_price":fp,"fill_ts":utcnow()})
                    self._close_position(pos, fp, "sl", int(tp_id) if tp_id else None)
                    return
    else:
        side = pos["side"]
        tp   = sf(pos["tp"]); sl_p = sf(pos["sl"])
        if tp > 0:
            if (side == "buy" and price >= tp) or (side == "sell" and price <= tp):
                if tp_id: DB.upd_order(int(tp_id), {"status":"filled","fill_price":tp,"fill_ts":utcnow()})
                self._close_position(pos, tp, "tp", int(sl_id) if sl_id else None)
                return
        if sl_p > 0:
            if (side == "buy" and price <= sl_p) or (side == "sell" and price >= sl_p):
                if sl_id: DB.upd_order(int(sl_id), {"status":"filled","fill_price":sl_p,"fill_ts":utcnow()})
                self._close_position(pos, sl_p, "sl", int(tp_id) if tp_id else None)
                return

def _close_position(self, pos: dict, exit_price: float,
                     reason: str, cancel_order_id: Optional[int]) -> None:
    pos_id   = int(pos["id"])
    side     = pos["side"]
    entry    = sf(pos.get("fill_price") or pos.get("quote_price"))
    atr      = sf(pos["atr"])
    pnl      = (exit_price - entry) / entry if side == "buy" else (entry - exit_price) / entry
    r_val    = (exit_price - entry) / atr   if side == "buy" else (entry - exit_price) / atr

    DB.upd_position(pos_id, {
        "state": S.CLOSED, "closed_ts": utcnow(),
        "exit_price": exit_price, "exit_ts": utcnow(),
        "exit_reason": reason, "pnl_pct": pnl, "r_val": r_val,
    })

    if cancel_order_id:
        co = DB.get_order(cancel_order_id)
        if co and co["status"] == "open":
            if CFG.live_trading:
                if co.get("exch_id"):       GATE.cancel(co["exch_id"])
                if co.get("exch_price_id"): GATE.cancel_stop(co["exch_price_id"])
            DB.upd_order(cancel_order_id, {"status": "cancelled"})

    DB.event("INFO", "position_closed", {
        "pos_id": pos_id, "reason": reason, "side": side,
        "entry": entry, "exit": exit_price,
        "pnl_pct": round(pnl * 100, 4), "r": round(r_val, 4),
    }, self.ticker)
    self.log.info(f"closed pos={pos_id} {reason} pnl={pnl*100:.3f}% r={r_val:.3f}")
```

# ═══════════════════════════════════════════════════════════

# 13. RECONCILER

# ═══════════════════════════════════════════════════════════

def reconcile() -> None:
if not CFG.live_trading or not CFG.gate_api_key: return
log.info(”[RECONCILE] syncing with exchange…”)
try:
exch_positions = {str(p.get(“contract”,””)): p for p in GATE.exchange_positions()}

```
    for pos in DB.all_open_positions():
        ticker  = pos["ticker"]
        pos_id  = int(pos["id"])
        state   = pos["state"]

        if state == S.QUOTING:
            eo = DB.get_order(int(pos["entry_order_id"])) if pos.get("entry_order_id") else None
            if not eo or not eo.get("exch_id"): continue
            r = GATE.order_status(eo["exch_id"])
            if r.get("finish_as") == "filled":
                fp = sf(r.get("fill_price") or r.get("price") or pos["quote_price"])
                log.info(f"[RECONCILE] recovering filled entry pos={pos_id} ticker={ticker}")
                DB.upd_order(int(eo["id"]), {"status":"filled","fill_price":fp,"fill_ts":utcnow()})
                eng = TickerEngine(ticker)
                eng._on_entry_filled(pos, fp)
            elif r.get("status") == "finished":
                DB.upd_order(int(eo["id"]), {"status": "cancelled"})
                DB.upd_position(pos_id, {"state": S.CANCEL, "closed_ts": utcnow()})

        elif state == S.ACTIVE:
            ep = exch_positions.get(ticker, {})
            ep_size = sf(ep.get("size", 0))
            if ep_size == 0:
                log.warning(f"[RECONCILE] ACTIVE pos={pos_id} but exchange size=0")
                DB.upd_position(pos_id, {"state": S.CLOSED, "closed_ts": utcnow(),
                                          "notes": "reconcile_unknown_close"})

    DB.event("INFO", "reconcile_done", {})
except Exception as e:
    log.error(f"[RECONCILE] error: {e}")
    DB.event("ERROR", "reconcile_error", {"error": str(e)})
```

# ═══════════════════════════════════════════════════════════

# 14. SCHEDULER

# ═══════════════════════════════════════════════════════════

ENGINES: Dict[str, TickerEngine] = {t: TickerEngine(t) for t in CFG.tickers}

def signal_loop(shutdown: threading.Event) -> None:
# Stagger initial signals to avoid concurrent API bursts
for i, ticker in enumerate(CFG.tickers):
threading.Timer(i * 5.0, ENGINES[ticker].update_signal).start()

```
while not shutdown.is_set():
    shutdown.wait(CFG.signal_interval_sec)
    if shutdown.is_set(): break
    for ticker in CFG.tickers:
        threading.Thread(
            target=ENGINES[ticker].update_signal,
            daemon=True, name=f"sig-{ticker}"
        ).start()
```

def exec_loop(shutdown: threading.Event) -> None:
while not shutdown.is_set():
for ticker in CFG.tickers:
try: ENGINES[ticker].exec_tick()
except Exception as e:
log.error(f”[EXEC] {ticker} tick error: {e}”)
shutdown.wait(CFG.exec_interval_sec)

# ═══════════════════════════════════════════════════════════

# 15. WEB UI

# ═══════════════════════════════════════════════════════════

_UI = r”””<!doctype html>

<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Gate MM Engine</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{
  --bg:#030508;--s1:#06090f;--s2:#0a1020;--brd:#0e1c35;
  --txt:#b8cce8;--mute:#2e4a70;--acc:#2563eb;
  --buy:#16a34a;--sell:#dc2626;--hold:#d97706;
  --active:#22c55e;--quote:#3b82f6;--closed:#4b5563;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'IBM Plex Sans',sans-serif;font-size:13px;line-height:1.5}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-bottom:1px solid var(--brd);background:var(--s1)}
.topbar h1{font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#fff}
#clock{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--mute)}
.tabs{display:flex;gap:0;padding:0 20px;background:var(--s1);border-bottom:1px solid var(--brd)}
.tab{padding:8px 16px;font-size:12px;font-weight:500;cursor:pointer;color:var(--mute);border-bottom:2px solid transparent;transition:all .15s}
.tab.active{color:#fff;border-bottom-color:var(--acc)}
.tab:hover{color:var(--txt)}
.page{display:none;padding:16px 20px}
.page.active{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-bottom:12px}
.card{background:var(--s2);border:1px solid var(--brd);border-radius:10px;padding:12px}
.card h2{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.12em;color:var(--mute);margin-bottom:8px}
.badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:99px;font-size:10px;font-weight:600;font-family:'IBM Plex Mono',monospace;letter-spacing:.04em}
.b-buy{background:rgba(22,163,74,.15);color:var(--buy);border:1px solid rgba(22,163,74,.3)}
.b-sell{background:rgba(220,38,38,.12);color:var(--sell);border:1px solid rgba(220,38,38,.3)}
.b-hold{background:rgba(217,119,6,.1);color:var(--hold);border:1px solid rgba(217,119,6,.25)}
.b-active{background:rgba(34,197,94,.1);color:var(--active)}
.b-quoting{background:rgba(59,130,246,.1);color:var(--quote)}
.b-closed{background:rgba(75,85,99,.1);color:var(--closed)}
.b-pass{background:rgba(22,163,74,.12);color:var(--buy);border:1px solid rgba(22,163,74,.25)}
.b-fail{background:rgba(220,38,38,.1);color:var(--sell);border:1px solid rgba(220,38,38,.2)}
.mono{font-family:'IBM Plex Mono',monospace}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 10px}
.k{font-size:10px;color:var(--mute);white-space:nowrap;font-family:'IBM Plex Mono',monospace}
.v{font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--txt)}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{padding:5px 8px;text-align:left;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--mute);border-bottom:1px solid var(--brd);white-space:nowrap}
td{padding:4px 8px;border-bottom:1px solid rgba(14,28,53,.5);font-size:11px;font-family:'IBM Plex Mono',monospace;white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}
tr:hover td{background:rgba(37,99,235,.04)}
.pos{color:var(--buy)}.neg{color:var(--sell)}.na{color:var(--mute)}
.ticker-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;margin-bottom:14px}
.ticker-card{background:var(--s2);border:1px solid var(--brd);border-radius:10px;padding:12px}
.ticker-card h3{font-size:11px;font-weight:600;margin-bottom:8px;color:#fff;font-family:'IBM Plex Mono',monospace}
</style>
</head>
<body>
<div class="topbar">
  <h1>▣ Gate MM Engine</h1>
  <span id="clock"></span>
</div>
<div class="tabs">
  <div class="tab active" onclick="showPage('overview')">Overview</div>
  <div class="tab" onclick="showPage('positions')">Positions</div>
  <div class="tab" onclick="showPage('orders')">Orders</div>
  <div class="tab" onclick="showPage('backtest')">Backtest</div>
  <div class="tab" onclick="showPage('decisions')">Decisions</div>
  <div class="tab" onclick="showPage('events')">Events</div>
</div>

<div id="overview" class="page active">
  <div class="ticker-grid" id="ticker-cards"></div>
  <div class="card">
    <h2>Engine</h2>
    <div class="kv" id="eng-kv"></div>
  </div>
</div>
<div id="positions"  class="page"><div class="tbl-wrap"><table id="pos-tbl"></table></div></div>
<div id="orders"     class="page"><div class="tbl-wrap"><table id="ord-tbl"></table></div></div>
<div id="backtest"   class="page"><div class="tbl-wrap"><table id="bt-tbl"></table></div></div>
<div id="decisions"  class="page"><div class="tbl-wrap"><table id="dec-tbl"></table></div></div>
<div id="events"     class="page"><div class="tbl-wrap"><table id="evt-tbl"></table></div></div>

<script>
function showPage(id){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  const tabs=['overview','positions','orders','backtest','decisions','events'];
  document.querySelectorAll('.tab')[tabs.indexOf(id)].classList.add('active');
}
const f=(v,d=4)=>{
  if(v===null||v===undefined||v==='')return '<span class="na">–</span>';
  if(typeof v==='number')return isNaN(v)?'<span class="na">nan</span>':v.toFixed(d);
  return String(v).slice(0,120);
};
const badge=(v,type)=>{
  const m={buy:'b-buy',sell:'b-sell',hold:'b-hold',
           quoting:'b-quoting',active:'b-active',closed:'b-closed',cancelled:'b-closed',error:'b-closed'};
  return `<span class="badge ${m[v]||m[type]||'b-hold'}">${v||'–'}</span>`;
};
const pct=(v)=>{
  if(v===null||v===undefined||v==='')return '<span class="na">–</span>';
  const n=parseFloat(v)*100;
  return `<span class="${n>=0?'pos':'neg'}">${n.toFixed(3)}%</span>`;
};
function mkTable(rows,cols){
  if(!rows||!rows.length)return '<tr><td colspan="99" class="na" style="padding:12px">No data</td></tr>';
  const hdr='<thead><tr>'+cols.map(c=>`<th>${c}</th>`).join('')+'</tr></thead>';
  const body='<tbody>'+rows.map(r=>'<tr>'+cols.map(c=>{
    const v=r[c];
    if(c==='side')   return `<td>${badge(v,'hold')}</td>`;
    if(c==='state')  return `<td>${badge(v,'closed')}</td>`;
    if(c==='pnl_pct'||c==='realized_pnl_pct') return `<td>${pct(v)}</td>`;
    if(c==='wf_allowed'||c==='walk_allowed'||c==='wf_ok'){
      return `<td>${v?'<span class="badge b-pass">PASS</span>':'<span class="badge b-fail">FAIL</span>'}</td>`;
    }
    return `<td>${f(v,4)}</td>`;
  }).join('')+'</tr>').join('')+'</tbody>';
  return hdr+body;
}
async function refresh(){
  document.getElementById('clock').textContent=new Date().toLocaleTimeString();
  try{
    const d=await(await fetch('/api/all')).json();
    // Ticker cards
    const tc=document.getElementById('ticker-cards');
    tc.innerHTML=d.tickers.map(t=>`
      <div class="ticker-card">
        <h3>${t.ticker}</h3>
        <div style="margin-bottom:6px">${badge(t.side)}</div>
        <div class="kv">
          <span class="k">alpha</span><span class="v">${f(t.alpha,4)}</span>
          <span class="k">conf</span><span class="v">${f(t.confidence,3)}</span>
          <span class="k">price</span><span class="v">${f(t.last_price,6)}</span>
          <span class="k">atr</span><span class="v">${f(t.atr,6)}</span>
          <span class="k">wf</span><span class="v">${t.wf_allowed?'<span class="badge b-pass">PASS</span>':'<span class="badge b-fail">BLOCK</span>'}</span>
          <span class="k">pos</span><span class="v">${t.open_pos?badge(t.open_pos.state,'closed'):'<span class="na">–</span>'}</span>
        </div>
      </div>`).join('');
    // Eng
    document.getElementById('eng-kv').innerHTML=`
      <span class="k">mode</span><span class="v">${d.live_trading?'LIVE':'PAPER'}</span>
      <span class="k">entries</span><span class="v">${d.allow_entries?'ON':'OFF'}</span>
      <span class="k">tickers</span><span class="v">${d.tickers.map(t=>t.ticker).join(', ')}</span>
    `;
    // Tables
    document.getElementById('pos-tbl').innerHTML=mkTable(d.positions,
      ['id','opened_ts','closed_ts','ticker','side','state','source','size',
       'quote_price','fill_price','tp','sl','exit_price','exit_reason','pnl_pct','r_val']);
    document.getElementById('ord-tbl').innerHTML=mkTable(d.orders,
      ['id','ts','ticker','role','side','size','price','stop_price','status',
       'fill_price','fill_ts','exch_id','notes']);
    document.getElementById('bt-tbl').innerHTML=mkTable(d.backtests,
      ['ts','ticker','total_trades','win_rate','avg_r','profit_factor','max_dd','sharpe',
       'wf_allowed']);
    document.getElementById('dec-tbl').innerHTML=mkTable(d.decisions,
      ['ts','ticker','side','confidence','final_score','local_side','or_side','groq_side',
       'wf_allowed','close','atr']);
    document.getElementById('evt-tbl').innerHTML=mkTable(d.events,
      ['ts','ticker','level','kind','payload']);
  }catch(e){console.error(e)}
}
refresh(); setInterval(refresh,4000);
</script>

</body>
</html>"""

class _UIHandler(BaseHTTPRequestHandler):
def _j(self, data: Any, code: int = 200):
raw = json.dumps(data, ensure_ascii=False, default=str).encode()
self.send_response(code)
self.send_header(“Content-Type”,“application/json; charset=utf-8”)
self.send_header(“Content-Length”, str(len(raw)))
self.end_headers(); self.wfile.write(raw)

```
def _h(self, html: str):
    raw = html.encode()
    self.send_response(200)
    self.send_header("Content-Type","text/html; charset=utf-8")
    self.send_header("Content-Length", str(len(raw)))
    self.end_headers(); self.wfile.write(raw)

def log_message(self, *_): pass

def do_GET(self):
    path = urlparse(self.path).path
    qs   = parse_qs(urlparse(self.path).query)

    if path == "/":
        self._h(_UI); return

    if path == "/api/all":
        ticker_data = []
        for t, ts in TICKER_STATES.items():
            pos = DB.open_position(t)
            ticker_data.append({
                "ticker": t, "side": ts.side, "alpha": ts.alpha,
                "confidence": ts.confidence, "atr": ts.atr,
                "last_price": ts.last_price, "wf_allowed": ts.wf_allowed,
                "open_pos": pos,
            })
        self._j({
            "live_trading":  CFG.live_trading,
            "allow_entries": CFG.allow_new_entries,
            "tickers":       ticker_data,
            "positions":     DB.recent_positions(limit=50),
            "orders":        DB.recent_orders(limit=100),
            "backtests":     DB.recent_backtests(30),
            "decisions":     DB.recent_decisions(limit=40),
            "events":        DB.recent_events(limit=50),
        }); return

    if path == "/api/status":
        self._j({
            "ts": utcnow(),
            "tickers": {t: {"side": ts.side, "alpha": ts.alpha,
                            "price": ts.last_price, "wf": ts.wf_allowed}
                        for t, ts in TICKER_STATES.items()},
        }); return

    self._j({"error": "not_found"}, 404)
```

# ═══════════════════════════════════════════════════════════

# 16. MAIN

# ═══════════════════════════════════════════════════════════

def main() -> int:
SHUTDOWN = threading.Event()

```
def _sig(n, _):
    log.info(f"signal {n}, shutting down")
    SHUTDOWN.set()

_signal.signal(_signal.SIGINT,  _sig)
_signal.signal(_signal.SIGTERM, _sig)

DB.event("INFO", "service_start", {
    "tickers": CFG.tickers, "live": CFG.live_trading,
    "allow_entries": CFG.allow_new_entries,
})

# Reconcile open positions
reconcile()

# Set leverage on all tickers (live only)
if CFG.live_trading and CFG.gate_api_key:
    for t in CFG.tickers:
        r = GATE.set_leverage(t, CFG.leverage)
        if "error" not in r:
            log.info(f"leverage {CFG.leverage}x set on {t}")

# UI
httpd = ThreadingHTTPServer((CFG.app_host, CFG.app_port), _UIHandler)
threading.Thread(target=httpd.serve_forever, daemon=True, name="ui").start()

# Signal loop (AI, candles, backtest)
threading.Thread(target=signal_loop, args=(SHUTDOWN,), daemon=True, name="sig").start()

# Execution loop (quotes, fills, exits)
threading.Thread(target=exec_loop, args=(SHUTDOWN,), daemon=True, name="exec").start()

sep = "═" * 58
print(sep)
print("  Gate MM Engine  —  multi-ticker market maker")
print(f"  Tickers  {', '.join(CFG.tickers)}")
print(f"  Mode     {'LIVE' if CFG.live_trading else 'PAPER'}")
print(f"  Entries  {'ON' if CFG.allow_new_entries else 'OFF'}")
print(f"  UI       http://{CFG.app_host}:{CFG.app_port}")
print(f"  DB       {CFG.db_path}")
print(sep)

try:
    while not SHUTDOWN.is_set():
        time.sleep(1)
except KeyboardInterrupt:
    SHUTDOWN.set()

httpd.shutdown()
DB.event("INFO", "service_stop", {"ts": utcnow()})
log.info("stopped.")
return 0
```

if **name** == “**main**”:
sys.exit(main())strructured appraisal very short 

#### ChatGPT:
**Оценка: $6,000–$12,000 as-is по идее, но $2,000–$4,000 в текущем вставленном виде.**

Почему:

- **Плюсы:** хорошая архитектурная задумка — multi-ticker, maker quotes, AI ensemble, SQLite persistence, reconcile, backtest, встроенный UI.
- **Минусы:** в текущем виде код **не копипаст-ready** — сломаны кавычки, `__future__`, форматирование, отступы, есть синтаксические артефакты. То есть это сейчас больше **драфт/макет**, чем готовый прод-файл.
- **Рыночная логика:**
  - как **идея + архитектура**: **$6k–$12k**
  - как **реально продаваемый файл прямо сейчас**: **$2k–$4k**
  - после починки синтаксиса, прогона, теста live/paper и проверки ордерного lifecycle: **$10k–$18k**

**Итог:**\
**Сильный по концепции, средний по текущей товарной готовности.**\
Самая честная короткая цифра: **около $8k по замыслу, около $3k в текущем вставленном виде**.


#### You:
No, show me how to sell it at this price

#### ChatGPT:
Продавай не **“файл с кодом”**, а **“готовую торговую инфраструктурную основу”**.

Чтобы продать его по верхней границе, тебе надо упаковать его так, чтобы покупатель видел не кусок Python, а **asset**.

Вот рабочая схема.

## Как позиционировать

Не пиши:

- “бот для Gate.io”
- “скрипт маркетмейкера”
- “AI trading bot”

Пиши так:

- **Production-style multi-ticker Gate.io futures market-making engine**
- **Stateful execution framework for low-nominal perpetuals**
- **Maker-first quote engine with persistence, reconciliation, backtesting, and embedded ops UI**

Это сразу меняет восприятие цены.

## Что продавать в описании

Тебе надо продавать 5 вещей:

**1. Архитектура**

- multi-ticker engine
- per-symbol state machine
- persistent SQLite state
- decision journal
- order lifecycle tracking
- restart-safe recovery logic

**2. Исполнение**

- maker quote placement
- quote repricing
- TP/SL lifecycle
- exchange reconciliation
- paper/live modes

**3. Исследовательская часть**

- walk-forward backtest
- signal layer
- AI ensemble
- memory bias / learning bias

**4. Операционный контроль**

- embedded UI
- event logs
- decisions table
- orders/positions visibility

**5. Возможность доработки**

- foundation for prop trading tooling
- base for managed strategy service
- internal execution lab for low-nominal perps

## Какой ценник ставить

Ставь не одну цифру, а пакетами:

**Lite License — $4,500**

- source code
- personal/internal use
- no exclusivity
- no support

**Builder Package — $8,500**

- source code
- setup help
- bug-fix pass
- deployment notes
- 7 days Q\&A

**Exclusive Asset Sale — $15,000+**

- exclusive transfer
- source code
- handoff docs
- installation support
- buyer gets sole resale rights

Так ты не споришь “почему так дорого”, а даёшь лестницу цен.

## Что нужно подготовить перед продажей

Без этого дорого не прод


#### You:
Give me the links to where to post it so I can post it immediately from my phone.

#### ChatGPT:
Сейчас быстро соберу тебе самые прямые площадки, где можно выставить такой код/бот прямо с телефона, и отберу те, где реально есть шанс на продажу, а не просто мусорная витрина.


#### ChatGPT:
Вот куда я бы выложил **с телефона прямо сейчас**, в порядке пользы:

**1. Flippa** - лучший быстрый вариант для продажи кода/проекта как digital asset или concept. У них есть рынок online businesses, apps и projects/concepts, то есть твой бот туда ложится естественно. ([flippa.com](https://flippa.com/?utm_source=chatgpt.com), [flippa.com](https://flippa.com/buy/projects-and-concepts?utm_source=chatgpt.com), [flippa.com](https://flippa.com/buy/monetization/app-sales?utm_source=chatgpt.com))

**2. Acquire.com** - сюда стоит идти, только если ты продаёшь не просто файл, а уже “мини-SaaS / software business / productized engine”. Для одного скрипта слабее, для упакованного продукта сильнее. ([acquire.com](https://acquire.com/?utm_source=chatgpt.com), [acquire.com](https://acquire.com/saas-companies-for-sale/?utm_source=chatgpt.com), [acquire.com](https://acquire.com/home/?utm_source=chatgpt.com))

**3. Upwork Project Catalog** - не как “продажа файла”, а как услуга:\
“Сделаю / продам / адаптирую multi-ticker Gate.io market maker engine”.\
С телефона это тоже быстро стартует, и часто так продать проще, чем голый asset. ([Upwork](https://www.upwork.com/resources/how-to-create-project-catalog-service?utm_source=chatgpt.com), [Upwork](https://www.upwork.com/services/?utm_source=chatgpt.com), [Upwork](https://www.upwork.com/resources/catalog-product-description?utm_source=chatgpt.com))

**4. Upwork jobs** - не листинг, а сразу отклики на клиентов, которым нужен algo/bot dev. Это самый быстрый путь к деньгам, если хочешь не ждать пассивного покупателя. ([Upwork](https://www.upwork.com/freelance-jobs/bot-development/?utm_source=chatgpt.com))

**5. CodeCanyon** - только если ты перепакуешь это как более массовый продукт с документацией, установкой и демо. Там есть trading bot listings, но это рынок дешёвых коробочных скриптов, так что за $10k+ там обычно не продают один asset. ([CodeCanyon](https://codecanyon.net/search/trading%20bot?srsltid=AfmBOoq3BEzI02JRCDb21e6vDGJfuccYmKqW3aQ3QrhKcheda-6bwqOW\&utm_source=chatgpt.com), [CodeCanyon](https://codecanyon.net/category/php-scripts?srsltid=AfmBOoomAhGCkPz_t_5xCZC8JX_cbh9Jr30yCSwRGZ7uJ6et5jobEH1_\&term=trading+bot\&utm_source=chatgpt.com))

Мой честный совет:

- **хочешь продать asset целиком** → **Flippa**
- **хочешь продать дороже как продукт/бизнес** → **Acquire**
- **хочешь получить деньги быстрее всего** → **Upwork**

Чтобы выложить **сейчас с телефона**, я бы делал так:
**Flippa + Upwork сегодня**,\
а **Acquire** - только после того как упакуешь:

- GitHub/demo
- скрины UI
- краткий README
- список фич
- paper/live distinction
- что именно покупатель получает

Название листинга я бы поставил так:

**Gate.io Multi-Ticker Market Maker Engine for Low-Nominal Futures (Paper/Live, SQLite, UI, Backtest)**

Описание в одну строку:
**Production-style Python market maker engine for Gate.io futures with multi-ticker support, maker entries/exits, persistence, reconciliation, backtesting, and embedded UI.**

Если хочешь, я сразу напишу тебе **готовый текст объявления для Flippa и Upwork**, чтобы ты просто вставил его с телефона.


#### You:
Gumroad?

#### ChatGPT:
Проверю по-быстрому, насколько Gumroad вообще подходит именно под продажу такого кода как digital product, чтобы не советовать тебе площадку мимо кассы.


#### ChatGPT:
Да, **Gumroad подходит** - но **не как лучшая площадка для продажи за $10k+**, а как **самый быстрый способ выставить это сегодня как digital product**. Gumroad прямо ориентирован на цифровые продукты и софт, а в их условиях указано, что продавец должен дать покупателю лицензионные условия и документацию для продукта. ([gumroad.com](https://gumroad.com/software-development/programming?tags=coding\&utm_source=chatgpt.com), [gumroad.com](https://gumroad.com/terms?utm_source=chatgpt.com))

Где он хорош:

- очень быстро стартовать с телефона
- продать **zip с кодом + README + license**
- сделать несколько тарифов
- принимать оплату без своего сайта
- удобно тестировать спрос на “developer asset” или “trading engine package” ([schoolmaker.com](https://schoolmaker.com/blog/gumroad-review?utm_source=chatgpt.com), [AI CMO](https://ai-cmo.net/tools/gumroad?utm_source=chatgpt.com))

Где он слабее:

- для дорогой продажи **эксклюзивного asset deal** он хуже, чем Flippa/Acquire
- меньше ощущение “M\&A / software acquisition”
- слабее позиционирование для покупателей, которые ищут именно покупку проекта, а не цифровой товар
- комиссии заметные: сторонние обзоры на 2026 указывают на примерно **10% + $0.50 за прямую продажу**, а в Gumroad Discover может быть существенно выше. Я бы воспринимал это как ориентир, но комиссию лучше проверить у себя перед публикацией. ([Dodo Payments](https://dodopayments.com/blogs/gumroad-fees-explained?utm_source=chatgpt.com), [AI CMO](https://ai-cmo.net/tools/gumroad?utm_source=chatgpt.com))

Мой честный совет такой:

- **Если хочешь выложить прямо сейчас с телефона** - **да, Gumroad норм**
- **Если хочешь продать дорого как asset** - параллельно лучше **Flippa**
- **Если хочешь продавать не один раз, а много раз как non-exclusive license** - **Gumroad вообще очень хорош**

Как бы я оформил это на Gumroad:

**Название**\
Gate.io Multi-Ticker Market Maker Engine (Python, Paper/Live, SQLite, UI)

**Формат продукта**\
zip-файл:

- `.py` файл
- `README.md`
- `.env.example`
- `LICENSE.txt`
- `SETUP.md`

**Тарифы**

- Personal License - **$499-$999**
- Builder License - **$1,500-$3,000**
- Commercial / Desk License - **$5,000+**
- Exclusive transfer - лучше **не через Gumroad**, а отдельной сделкой

Очень важно: на Gumroad **обязательно добавь лицензию**, потому что их условия прямо требуют end user license terms и product documentation для продукта. ([gumroad.com](https://gumroad.com/terms?utm_source=chatgpt.com))

Итог в одной строке:
**Gumroad - да, для быстрого старта и продажи лицензий; нет - если цель именно продать один эксклюзивный бот дорого как asset transfer.**

Прямая ссылка:
[Gumroad](https://gumroad.com)\
Категория с software/programming у них тоже есть. ([gumroad.com](https://gumroad.com/software-development/programming?tags=coding\&utm_source=chatgpt.com), [gumroad.com](https://gumroad.com/software-development?utm_source=chatgpt.com))

Я могу сразу дать тебе **готовый Gumroad listing text + license text**, чтобы ты просто вставил.


#### You:
Да. Если делать из этого pro / institutional-grade maker beast, то не “подкрутить пару параметров”, а перестраивать ядро исполнения.

Сейчас у тебя уже есть хорошая база: multi-symbol scan, WS top-of-book, maker-entry, maker-exit, SQLite state, reconciliation, paper/live split и execution-aware backtest. Это уже foundation, а не мусор. Но до institutional-grade ему не хватает самого дорогого слоя: fill-driven execution, risk engine, hard recovery, partial-fill accounting и observability.

Вот что надо сделать, чтобы он стал реально “зверем”.

Что сейчас самое слабое

Самая большая дыра — локальный stop-close. В текущем виде force_close() просто закрывает позицию в локальной БД по bid/ask и сам файл прямо пишет, что для строгой live-версии нужен IOC/market-like protective order. Для institutional-grade это неприемлемо: риск не должен “закрываться на бумаге”, он должен закрываться реальным ордером на бирже.  ￼

Вторая дыра — нет нормальной private execution stream архитектуры. У тебя market data идёт по WS, а order lifecycle в основном дотягивается через REST reconcile. Это норм для foundation, но слабовато для серьёзного maker engine, потому что тебе нужны быстрые события по:
	•	accepted
	•	open
	•	partial fill
	•	full fill
	•	cancel ack
	•	reject
	•	reduce-only failures
	•	stale replace races

Сейчас это не выглядит как полноценная event-driven OMS.  ￼

Третья дыра — partial fills и inventory accounting. Код уже умеет хранить ордера и позиции, но из того, что видно, архитектура ещё не выглядит как жёсткая fill-ledger модель с VWAP, leaves_qty, cum_qty, per-order realized/unrealized attribution. Это очень важно для maker-бота.  ￼

Во что это надо превратить

Не “бот”, а систему из 7 слоёв:

1. Market Data Engine

Нужен не просто best bid/ask snapshot, а:
	•	L2 depth cache
	•	sequence handling
	•	stale-book detection
	•	book resync on gap
	•	quote age checks
	•	local imbalance metrics
	•	trade tape / aggressor flow
	•	mark/index/funding snapshots

Maker engine без нормального L2 — полуслепой.

2. OMS / EMS

Нужен полноценный execution layer:
	•	new order
	•	cancel
	•	cancel/replace
	•	post-only retry ladder
	•	order state machine
	•	partial fill aggregation
	•	duplicate event protection
	•	client order id idempotency
	•	order ack timeout logic

Сейчас у тебя ордерный цикл есть, но institutional-grade требует state machine, а не просто “insert/update order row”.  ￼

3. Position & Inventory Engine

Нужны:
	•	net position
	•	gross exposure
	•	symbol exposure
	•	sector/bucket exposure
	•	inventory skew quoting
	•	inventory decay
	•	quote throttling when inventory offside
	•	hard caps per symbol and global

У тебя есть inventory_limit_per_symbol, но зверь начинается там, где бот меняет котировки из-за inventory pressure, а не просто запрещает лишний вход.  ￼

4. Risk Engine

Отдельный слой, не смешанный со strategy:
	•	max loss per symbol
	•	max daily loss
	•	max open notional
	•	max concurrent positions
	•	max stale orders
	•	connectivity circuit breaker
	•	kill switch
	•	quote ban on abnormal spread / abnormal latency
	•	funding/event blackout windows

И главное: риск должен уметь останавливать OMS, а не просто писать event в БД.

5. Strategy / Quoter

Не просто score -> buy/sell, а:
	•	fair value
	•	reservation price
	•	skew by inventory
	•	spread widening by vol
	•	spread widening by adverse selection
	•	quote size by queue quality
	•	quote suppression on toxic flow
	•	asymmetric bid/ask sizing

Сейчас твой alpha норм как foundation, но для institutional-grade нужен market making model, а не просто signal model.  ￼

6. Reconciliation & Recovery

При рестарте система должна:
	•	загрузить все open orders с exchange
	•	загрузить positions
	•	сопоставить local/exchange state
	•	найти ghost orders
	•	найти orphan positions
	•	восстановить working state
	•	отменить опасные сироты
	•	пересчитать inventory
	•	восстановить last known quote regime

Вот это и даёт настоящее “production-ready”.

7. Observability

Нужно:
	•	Prometheus metrics
	•	structured JSON logs
	•	alerting
	•	fill latency
	•	order reject rate
	•	cancel/replace rate
	•	maker fill ratio
	•	adverse selection after fill
	•	PnL by symbol
	•	realized vs unrealized
	•	inventory skew stats
	•	quote uptime

Без этого institutional-grade никто серьёзно не назовёт.

Что я бы поменял первым

Если резать по приоритету, то топ-8 такой:

1. Убрать локальный fake stop-close
Сделать реальный protective execution path. Это самый критичный апгрейд.  ￼

2. Вынести OMS в отдельный state machine
NEW -> ACK -> OPEN -> PARTIAL -> FILLED / CANCELLED / REJECTED

3. Добавить private order/fill stream
Чтобы позиция открывалась и закрывалась по факту fill events, а не по догадке reconciliation.

4. Сделать cancel/replace quoting engine
Сейчас stale cancel есть, но нужен системный quote manager с rate limits и priority rules.  ￼

5. Добавить inventory-skew model
Чтобы бот не просто входил, а управлял направленным риском.

6. Перестроить backtester в event replay model
Сейчас execution-aware backtest — это плюс, но всё ещё модель. Для высокого уровня нужен хотя бы replay по более богатым market events.  ￼

7. Добавить circuit breakers
Связь, спред, reject burst, stale books, funding spikes, abnormal slippage.

8. Разбить single file на модули
config.py, market_data.py, oms.py, risk.py, strategy.py, reconcile.py, db.py, main.py

Как будет выглядеть уже “зверь”

Минимальный institutional-grade контур:
	•	MarketDataService
	•	ExecutionService
	•	OrderManager
	•	PositionManager
	•	RiskManager
	•	QuoteEngine
	•	ReconcileService
	•	BacktestReplayEngine
	•	Metrics/Alerts
	•	Persistence layer

И поверх этого:
	•	live mode
	•	paper mode
	•	replay mode
	•	scan mode
	•	health endpoints
	•	operator dashboard

Честно: насколько далеко текущий файл от этого

Не на 10%, а примерно на 45–55% пути по инженерии.
То есть база есть, но самое трудное ещё впереди.

Он уже умеет:
	•	сканировать
	•	считать сигналы
	•	ставить maker orders
	•	держать локальное состояние
	•	частично reconciliеить exchange state  ￼

Но institutional-grade начинается там, где система умеет:
	•	переживать рестарт без потери контроля
	•	корректно вести partial fills
	•	агрессивно защищать риск
	•	не врать себе о закрытии позиции
	•	давать оператору мгновенную телеметрию

Мой вердикт

Да, из этого можно сделать institutional-grade maker beast.
Но это уже не “подправить бот”, а сделать полноценный execution/risk platform rewrite вокруг текущей базы.

Самый правильный путь:
	1.	сначала OMS + risk + real protective exits
	2.	потом private fills + partial fills + recovery
	3.	потом inventory skew + smarter quoting
	4.	потом metrics, alerts, replay backtest
	5.	потом modularization and deployment

Если хочешь, следующим сообщением я могу дать тебе жёсткий blueprint v2:
точную структуру файлов и классов для institutional-grade rewrite именно под Gate.io.

#### ChatGPT:
Да. Вот **blueprint v2** — уже не “ботик”, а **нормальная modular architecture под Gate.io institutional-grade maker engine**.

Сделаю жёстко и практично: **структура файлов, классы, ответственность каждого слоя, порядок сборки**.

---

# 1. Структура проекта

```text
gate_mm_beast/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ constants.py
│  ├─ logging_setup.py
│  ├─ types.py
│  │
│  ├─ core/
│  │  ├─ clock.py
│  │  ├─ bus.py
│  │  ├─ ids.py
│  │  ├─ decimal_utils.py
│  │  ├─ throttle.py
│  │  ├─ circuit_breaker.py
│  │  └─ health.py
│  │
│  ├─ persistence/
│  │  ├─ db.py
│  │  ├─ models.py
│  │  ├─ order_repository.py
│  │  ├─ position_repository.py
│  │  ├─ fill_repository.py
│  │  ├─ decision_repository.py
│  │  ├─ event_repository.py
│  │  └─ snapshot_repository.py
│  │
│  ├─ connectors/
│  │  └─ gateio/
│  │     ├─ rest_public.py
│  │     ├─ rest_private.py
│  │     ├─ ws_public.py
│  │     ├─ ws_private.py
│  │     ├─ signing.py
│  │     ├─ schemas.py
│  │     ├─ rate_limits.py
│  │     └─ mapper.py
│  │
│  ├─ market_data/
│  │  ├─ depth_cache.py
│  │  ├─ book_builder.py
│  │  ├─ trade_tape.py
│  │  ├─ funding_cache.py
│  │  ├─ mark_cache.py
│  │  ├─ candles_service.py
│  │  ├─ market_data_service.py
│  │  └─ stale_detector.py
│  │
│  ├─ oms/
│  │  ├─ order_state.py
│  │  ├─ order_models.py
│  │  ├─ order_manager.py
│  │  ├─ execution_service.py
│  │  ├─ replace_manager.py
│  │  ├─ ack_tracker.py
│  │  ├─ fill_processor.py
│  │  └─ client_order_registry.py
│  │
│  ├─ portfolio/
│  │  ├─ position_manager.py
│  │  ├─ inventory_manager.py
│  │  ├─ exposure_manager.py
│  │  ├─ pnl_manager.py
│  │  └─ account_reconciler.py
│  │
│  ├─ risk/
│  │  ├─ risk_manager.py
│  │  ├─ limits.py
│  │  ├─ kill_switch.py
│  │  ├─ protective_exit.py
│  │  ├─ connectivity_guard.py
│  │  ├─ market_regime_guard.py
│  │  └─ stale_order_guard.py
│  │
│  ├─ strategy/
│  │  ├─ fair_value.py
│  │  ├─ alpha_model.py
│  │  ├─ inventory_skew.py
│  │  ├─ spread_model.py
│  │  ├─ quote_sizer.py
│  │  ├─ adverse_selection.py
│  │  ├─ reservation_price.py
│  │  └─ quote_engine.py
│  │
│  ├─ reconcile/
│  │  ├─ startup_reconcile.py
│  │  ├─ periodic_reconcile.py
│  │  ├─ ghost_order_detector.py
│  │  ├─ orphan_position_detector.py
│  │  └─ recovery_actions.py
│  │
│  ├─ backtest/
│  │  ├─ replay_engine.py
│  │  ├─ execution_model.py
│  │  ├─ queue_model.py
│  │  ├─ fill_model.py
│  │  ├─ slippage_model.py
│  │  ├─ metrics.py
│  │  └─ report.py
│  │
│  ├─ observability/
│  │  ├─ metrics.py
│  │  ├─ alerts.py
│  │  ├─ event_log.py
│  │  ├─ audit_log.py
│  │  └─ tracing.py
│  │
│  └─ api/
│     ├─ server.py
│     ├─ health_routes.py
│     ├─ metrics_routes.py
│     ├─ positions_routes.py
│     ├─ orders_routes.py
│     └─ dashboard_routes.py
│
├─ tests/
│  ├─ test_order_state_machine.py
│  ├─ test_fill_processor.py
│  ├─ test_risk_manager.py
│  ├─ test_quote_engine.py
│  ├─ test_reconcile.py
│  └─ test_protective_exit.py
│
├─ scripts/
│  ├─ run_live.py
│  ├─ run_paper.py
│  ├─ run_replay.py
│  └─ migrate_db.py
│
├─ .env.example
├─ requirements.txt
└─ README.md
```

---

# 2. Главная идея архитектуры

Система должна быть **event-driven**.

Не так:

- strategy решила
- код сразу поставил ордер
- потом где-то опросил биржу
- потом “наверное fill”

А так:

- market data event
- quote decision event
- OMS command
- exchange ack event
- partial fill event
- position update event
- risk re-evaluation event
- cancel/replace event
- protective exit event

То есть центральная идея — **состояние меняется событиями**, а не догадками.

---

# 3. Ключевые классы

## `MarketDataService`

Отвечает за:

- public WS
- depth updates
- sequence checks
- stale detection
- resync on gap
- trade tape
- mark/index/funding snapshots

Методы:

```python
start()
stop()
get_top(symbol) -> BookTop
get_depth(symbol) -> DepthSnapshot
get_trade_flow(symbol) -> TradeFlow
is_stale(symbol) -> bool
resync(symbol)
```

---

## `OrderManager`

Это сердце OMS.

Отвечает за:

- new order intent
- client\_order\_id
- state machine
- order lifecycle
- replace logic
- dedup events
- persistence

Методы:

```python
submit_limit(...)
submit_post_only(...)
submit_reduce_only(...)
cancel(order_id)
replace(order_id, new_price, new_size)
handle_ack(event)
handle_reject(event)
handle_fill(event)
handle_cancel(event)
get_open_orders(symbol)
```

---

## `ExecutionService`

Тонкий слой между OMS и Gate.io connector.

Отвечает за:

- отправку REST/private WS команд
- retry policy
- timeout handling
- rate limit discipline
- exchange payload normalization

Методы:

```
```


#### You:
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
gate_multi_ticker_mm_prod.py

Production-style multi-ticker Gate.io USDT perpetual maker engine for low-nominal contracts.

What this file does:
- scans Gate USDT perpetual contracts and filters low nominal symbols (default: mark price 0 to 0.10 USDT)
- maintains best bid/ask snapshots over WebSocket
- computes a lightweight alpha signal from microstructure + trend/mean-reversion features
- places maker-only entries and maker-only take-profit exits
- tracks local orders/positions in SQLite
- reconciles local state against exchange state
- includes an execution-aware backtester with fees, spread proxy, queue/fill probability, slippage, and cooldowns
- supports PAPER and LIVE modes

Important:
- This is a software foundation, not a guarantee of profit.
- A truly tick-perfect execution backtest requires historical L2/order-book and trade data. The included backtester is execution-aware, but still a model.
- Keep LIVE_TRADING=false until you verify endpoints, permissions, sizing, and contract specifics on your own account.

Install:
    pip install aiohttp websockets pandas numpy python-dotenv

Run examples:
    python gate_multi_ticker_mm_prod.py --mode backtest
    python gate_multi_ticker_mm_prod.py --mode paper
    python gate_multi_ticker_mm_prod.py --mode live
    python gate_multi_ticker_mm_prod.py --mode scan

Environment:
    GATE_API_KEY=...
    GATE_API_SECRET=...
    GATE_BASE_URL=https://fx-api.gateio.ws/api/v4
    GATE_WS_URL=wss://fx-ws.gateio.ws/v4/ws/usdt
    GATE_SETTLE=usdt
    LIVE_TRADING=false
    DB_PATH=gate_mm_prod.db
    APP_SYMBOLS=0                 # optional comma-separated symbols; 0 means auto-scan
    MIN_MARK_PRICE=0.0
    MAX_MARK_PRICE=0.10
    MIN_24H_QUOTE_VOL=100000
    MAX_SYMBOLS=12
    LOOP_SECONDS=2.0
    CONTRACT_RISK_USD=15
    LEVERAGE=2
    MAKER_FEE_BPS=0.0
    TAKER_FEE_BPS=5.0
    ENTRY_EDGE_BPS=5.0
    EXIT_EDGE_BPS=4.0
    STOP_ATR_MULT=1.6
    TAKE_ATR_MULT=1.0
    INVENTORY_LIMIT_PER_SYMBOL=1
    BAR_INTERVAL=1m
    BAR_LIMIT=400
    COOLDOWN_SECONDS=45
    REQUEST_TIMEOUT=15
    ENABLE_UI=false
    APP_HOST=127.0.0.1
    APP_PORT=8788
"""

import argparse
import asyncio
import contextlib
import dataclasses
import hashlib
import hmac
import json
import logging
import math
import os
import random
import signal
import sqlite3
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
import numpy as np
import pandas as pd
import websockets
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Helpers
# ============================================================

def now_ts() -> float:
    return time.time()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def sign(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def json_s(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"), default=str)


def chunks(seq: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


# ============================================================
# Config
# ============================================================

@dataclass
class Config:
    gate_api_key: str = os.getenv("GATE_API_KEY", "")
    gate_api_secret: str = os.getenv("GATE_API_SECRET", "")
    gate_base_url: str = os.getenv("GATE_BASE_URL", "https://fx-api.gateio.ws/api/v4").rstrip("/")
    gate_ws_url: str = os.getenv("GATE_WS_URL", "wss://fx-ws.gateio.ws/v4/ws/usdt")
    settle: str = os.getenv("GATE_SETTLE", "usdt").lower()
    live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
    db_path: str = os.getenv("DB_PATH", "gate_mm_prod.db")

    min_mark_price: float = float(os.getenv("MIN_MARK_PRICE", "0.0"))
    max_mark_price: float = float(os.getenv("MAX_MARK_PRICE", "0.10"))
    min_24h_quote_vol: float = float(os.getenv("MIN_24H_QUOTE_VOL", "100000"))
    max_symbols: int = int(os.getenv("MAX_SYMBOLS", "12"))
    app_symbols_raw: str = os.getenv("APP_SYMBOLS", "0")

    loop_seconds: float = float(os.getenv("LOOP_SECONDS", "2.0"))
    contract_risk_usd: float = float(os.getenv("CONTRACT_RISK_USD", "15"))
    leverage: int = int(os.getenv("LEVERAGE", "2"))
    maker_fee_bps: float = float(os.getenv("MAKER_FEE_BPS", "0.0"))
    taker_fee_bps: float = float(os.getenv("TAKER_FEE_BPS", "5.0"))
    entry_edge_bps: float = float(os.getenv("ENTRY_EDGE_BPS", "5.0"))
    exit_edge_bps: float = float(os.getenv("EXIT_EDGE_BPS", "4.0"))
    stop_atr_mult: float = float(os.getenv("STOP_ATR_MULT", "1.6"))
    take_atr_mult: float = float(os.getenv("TAKE_ATR_MULT", "1.0"))
    inventory_limit_per_symbol: int = int(os.getenv("INVENTORY_LIMIT_PER_SYMBOL", "1"))
    bar_interval: str = os.getenv("BAR_INTERVAL", "1m")
    bar_limit: int = int(os.getenv("BAR_LIMIT", "400"))
    cooldown_seconds: int = int(os.getenv("COOLDOWN_SECONDS", "45"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))

    enable_ui: bool = os.getenv("ENABLE_UI", "false").lower() == "true"
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8788"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def app_symbols(self) -> List[str]:
        raw = self.app_symbols_raw.strip()
        if not raw or raw == "0":
            return []
        return [x.strip().upper() for x in raw.split(",") if x.strip()]


CFG = Config()
logging.basicConfig(
    level=getattr(logging, CFG.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("gate-mm-prod")


# ============================================================
# SQLite
# ============================================================

class DB:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS symbols (
                    symbol TEXT PRIMARY KEY,
                    mark_price REAL,
                    last_price REAL,
                    quote_volume REAL,
                    quanto_multiplier REAL,
                    order_price_round REAL,
                    order_size_min INTEGER,
                    order_size_max INTEGER,
                    updated_ts TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    level TEXT,
                    kind TEXT,
                    symbol TEXT,
                    payload_json TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    symbol TEXT,
                    side TEXT,
                    score REAL,
                    confidence REAL,
                    alpha_json TEXT,
                    market_json TEXT,
                    backtest_json TEXT,
                    live_ok INTEGER,
                    notes TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    symbol TEXT,
                    role TEXT,
                    side TEXT,
                    state TEXT,
                    text_tag TEXT,
                    reduce_only INTEGER,
                    requested_price REAL,
                    requested_size INTEGER,
                    exchange_order_id TEXT,
                    exchange_status TEXT,
                    fill_price REAL,
                    left_size INTEGER,
                    raw_request_json TEXT,
                    raw_response_json TEXT,
                    notes TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_open TEXT,
                    ts_close TEXT,
                    symbol TEXT,
                    side TEXT,
                    status TEXT,
                    size INTEGER,
                    entry_price REAL,
                    exit_price REAL,
                    take_price REAL,
                    stop_price REAL,
                    realized_pnl_usd REAL,
                    reason_open TEXT,
                    reason_close TEXT,
                    meta_json TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_state (
                    k TEXT PRIMARY KEY,
                    v TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def event(self, level: str, kind: str, symbol: str, payload: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO events (ts, level, kind, symbol, payload_json) VALUES (?, ?, ?, ?, ?)",
                (utc_now_iso(), level, kind, symbol, json_s(payload)),
            )
            conn.commit()

    def upsert_symbol(self, row: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO symbols(symbol, mark_price, last_price, quote_volume, quanto_multiplier,
                                    order_price_round, order_size_min, order_size_max, updated_ts)
                VALUES (:symbol, :mark_price, :last_price, :quote_volume, :quanto_multiplier,
                        :order_price_round, :order_size_min, :order_size_max, :updated_ts)
                ON CONFLICT(symbol) DO UPDATE SET
                    mark_price=excluded.mark_price,
                    last_price=excluded.last_price,
                    quote_volume=excluded.quote_volume,
                    quanto_multiplier=excluded.quanto_multiplier,
                    order_price_round=excluded.order_price_round,
                    order_size_min=excluded.order_size_min,
                    order_size_max=excluded.order_size_max,
                    updated_ts=excluded.updated_ts
                """,
                row,
            )
            conn.commit()

    def insert_decision(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        q = f"INSERT INTO decisions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as conn:
            cur = conn.execute(q, vals)
            conn.commit()
            return int(cur.lastrowid)

    def insert_order(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        q = f"INSERT INTO orders ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as conn:
            cur = conn.execute(q, vals)
            conn.commit()
            return int(cur.lastrowid)

    def update_order(self, order_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        keys = list(updates.keys())
        vals = [updates[k] for k in keys] + [order_id]
        set_clause = ",".join([f"{k}=?" for k in keys])
        with self._conn() as conn:
            conn.execute(f"UPDATE orders SET {set_clause} WHERE id=?", vals)
            conn.commit()

    def open_position(self, row: Dict[str, Any]) -> int:
        cols = list(row.keys())
        vals = [row[c] for c in cols]
        q = f"INSERT INTO positions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        with self._conn() as conn:
            cur = conn.execute(q, vals)
            conn.commit()
            return int(cur.lastrowid)

    def update_position(self, pos_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        keys = list(updates.keys())
        vals = [updates[k] for k in keys] + [pos_id]
        set_clause = ",".join([f"{k}=?" for k in keys])
        with self._conn() as conn:
            conn.execute(f"UPDATE positions SET {set_clause} WHERE id=?", vals)
            conn.commit()

    def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
                (symbol,),
            ).fetchone()
            return dict(row) if row else None

    def get_working_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE symbol=? AND state IN ('working','submitted','paper_open') ORDER BY id DESC",
                    (symbol,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE state IN ('working','submitted','paper_open') ORDER BY id DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def recent_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def recent_positions(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM positions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def get_state(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute("SELECT v FROM kv_state WHERE k=?", (key,)).fetchone()
            if not row:
                return default or {}
            try:
                return json.loads(row[0])
            except Exception:
                return default or {}

    def set_state(self, key: str, val: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO kv_state(k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                (key, json_s(val)),
            )
            conn.commit()


DBI = DB(CFG.db_path)


# ============================================================
# Gate REST
# ============================================================

class GateRest:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session: Optional[aiohttp.ClientSession] = None

    async def ensure(self) -> None:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.cfg.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

    def _headers(self, method: str, path: str, query_string: str = "", body: str = "") -> Dict[str, str]:
        ts = str(int(time.time()))
        body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
        sign_str = f"{method.upper()}\n/api/v4{path}\n{query_string}\n{body_hash}\n{ts}"
        sign = hmac.new(self.cfg.gate_api_secret.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
        return {
            "KEY": self.cfg.gate_api_key,
            "Timestamp": ts,
            "SIGN": sign,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def public(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        await self.ensure()
        assert self.session
        url = f"{self.cfg.gate_base_url}{path}"
        async with self.session.get(url, params=params or {}) as r:
            text = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"public {path} {r.status}: {text[:400]}")
            return json.loads(text) if text.strip() else {}

    async def private(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any]] = None) -> Any:
        await self.ensure()
        assert self.session
        params = params or {}
        payload = payload or {}
        query_string = urlencode(params)
        body = json.dumps(payload, separators=(",", ":")) if payload else ""
        headers = self._headers(method, path, query_string, body)
        url = f"{self.cfg.gate_base_url}{path}"
        async with self.session.request(method.upper(), url, params=params, data=body if body else None, headers=headers) as r:
            text = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"private {method} {path} {r.status}: {text[:500]}")
            return json.loads(text) if text.strip() else {}

    async def list_contracts(self) -> List[Dict[str, Any]]:
        data = await self.public(f"/futures/{self.cfg.settle}/contracts")
        return data if isinstance(data, list) else []

    async def list_tickers(self) -> List[Dict[str, Any]]:
        data = await self.public(f"/futures/{self.cfg.settle}/tickers")
        return data if isinstance(data, list) else []

    async def get_contract(self, contract: str) -> Dict[str, Any]:
        data = await self.public(f"/futures/{self.cfg.settle}/contracts/{contract}")
        return data if isinstance(data, dict) else {}

    async def get_candles(self, contract: str, interval: str, limit: int) -> pd.DataFrame:
        data = await self.public(
            f"/futures/{self.cfg.settle}/candlesticks",
            {"contract": contract, "interval": interval, "limit": min(limit, 2000)},
        )
        rows: List[Dict[str, Any]] = []
        for item in data or []:
            if isinstance(item, dict):
                rows.append({
                    "t": item.get("t"),
                    "o": item.get("o"),
                    "h": item.get("h"),
                    "l": item.get("l"),
                    "c": item.get("c"),
                    "v": item.get("v"),
                })
            elif isinstance(item, list) and len(item) >= 6:
                rows.append({"t": item[0], "v": item[1], "c": item[2], "h": item[3], "l": item[4], "o": item[5]})
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        for c in ["o", "h", "l", "c", "v"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
        df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna().sort_values("timestamp").reset_index(drop=True)

    async def get_order_book(self, contract: str, limit: int = 5) -> Dict[str, Any]:
        data = await self.public(f"/futures/{self.cfg.settle}/order_book", {"contract": contract, "limit": limit})
        return data if isinstance(data, dict) else {}

    async def list_open_orders(self, contract: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"status": "open"}
        if contract:
            params["contract"] = contract
        data = await self.private("GET", f"/futures/{self.cfg.settle}/orders", params=params)
        return data if isinstance(data, list) else []

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        data = await self.private("GET", f"/futures/{self.cfg.settle}/orders/{order_id}")
        return data if isinstance(data, dict) else {}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        data = await self.private("DELETE", f"/futures/{self.cfg.settle}/orders/{order_id}")
        return data if isinstance(data, dict) else {}

    async def list_positions(self) -> List[Dict[str, Any]]:
        data = await self.private("GET", f"/futures/{self.cfg.settle}/positions")
        return data if isinstance(data, list) else []

    async def update_leverage(self, contract: str, leverage: int) -> Dict[str, Any]:
        data = await self.private("POST", f"/futures/{self.cfg.settle}/positions/{contract}/leverage", payload={"leverage": str(leverage)})
        return data if isinstance(data, dict) else {}

    async def create_order(self, contract: str, size: int, price: float, text_tag: str, reduce_only: bool = False, tif: str = "poc") -> Dict[str, Any]:
        payload = {
            "contract": contract,
            "size": size,
            "price": f"{price:.10f}",
            "tif": tif,
            "text": text_tag[:28],
            "reduce_only": reduce_only,
        }
        data = await self.private("POST", f"/futures/{self.cfg.settle}/orders", payload=payload)
        return data if isinstance(data, dict) else {}

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()


# ============================================================
# Market state and indicators
# ============================================================

@dataclass
class BookTop:
    bid: float = 0.0
    ask: float = 0.0
    bid_size: float = 0.0
    ask_size: float = 0.0
    ts: float = 0.0

    @property
    def mid(self) -> float:
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2.0
        return 0.0

    @property
    def spread(self) -> float:
        if self.bid > 0 and self.ask > 0 and self.ask >= self.bid:
            return self.ask - self.bid
        return 0.0


@dataclass
class SymbolSpec:
    symbol: str
    mark_price: float
    quote_volume: float
    quanto_multiplier: float
    order_price_round: float
    order_size_min: int
    order_size_max: int


@dataclass
class SymbolRuntime:
    symbol: str
    spec: SymbolSpec
    book: BookTop = field(default_factory=BookTop)
    candles: Optional[pd.DataFrame] = None
    last_signal_ts: float = 0.0
    last_trade_ts: float = 0.0
    state: str = "flat"
    recent_mid: Deque[float] = field(default_factory=lambda: deque(maxlen=120))


class MarketState:
    def __init__(self):
        self.by_symbol: Dict[str, SymbolRuntime] = {}
        self.lock = asyncio.Lock()

    async def set_symbols(self, runtimes: Dict[str, SymbolRuntime]) -> None:
        async with self.lock:
            self.by_symbol = runtimes

    async def get(self, symbol: str) -> Optional[SymbolRuntime]:
        async with self.lock:
            return self.by_symbol.get(symbol)

    async def symbols(self) -> List[str]:
        async with self.lock:
            return list(self.by_symbol.keys())

    async def items(self) -> List[Tuple[str, SymbolRuntime]]:
        async with self.lock:
            return list(self.by_symbol.items())


MARKET = MarketState()


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["ret1"] = x["close"].pct_change(1)
    x["ret3"] = x["close"].pct_change(3)
    x["ret12"] = x["close"].pct_change(12)
    x["ema8"] = x["close"].ewm(span=8, adjust=False).mean()
    x["ema21"] = x["close"].ewm(span=21, adjust=False).mean()
    x["ema55"] = x["close"].ewm(span=55, adjust=False).mean()
    x["vol20"] = x["ret1"].rolling(20).std()
    x["atr14"] = (pd.concat([
        (x["high"] - x["low"]),
        (x["high"] - x["close"].shift()).abs(),
        (x["low"] - x["close"].shift()).abs(),
    ], axis=1).max(axis=1)).rolling(14).mean()
    x["z20"] = (x["close"] - x["close"].rolling(20).mean()) / x["close"].rolling(20).std()
    x["volz"] = (x["volume"] - x["volume"].rolling(20).mean()) / x["volume"].rolling(20).std()
    x["dist_ema21_atr"] = (x["close"] - x["ema21"]) / x["atr14"].replace(0, np.nan)
    return x


def round_to_tick(price: float, tick: float) -> float:
    if tick <= 0:
        return price
    return round(round(price / tick) * tick, 10)


def best_bid_ask_from_book(book: Dict[str, Any]) -> Tuple[float, float]:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return 0.0, 0.0
    def get_price(row: Any) -> float:
        if isinstance(row, list):
            return safe_float(row[0])
        if isinstance(row, dict):
            return safe_float(row.get("p"))
        return 0.0
    return get_price(bids[0]), get_price(asks[0])


def compute_size(spec: SymbolSpec, mid: float, risk_usd: float, leverage: int, side: str) -> int:
    mult = max(spec.quanto_multiplier, 1e-9)
    notional = risk_usd * leverage
    contracts = max(int(notional / max(mid * mult, 1e-9)), spec.order_size_min or 1)
    if spec.order_size_max > 0:
        contracts = min(contracts, spec.order_size_max)
    return contracts if side == "buy" else -contracts


def estimate_micro_alpha(rt: SymbolRuntime) -> Dict[str, float]:
    df = rt.candles
    if df is None or len(df) < 80:
        return {"score": 0.0, "confidence": 0.0}
    row = df.iloc[-1]
    bid = rt.book.bid
    ask = rt.book.ask
    mid = rt.book.mid or safe_float(row["close"])
    spread = rt.book.spread
    tick = max(rt.spec.order_price_round, 1e-8)

    trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
    slow_trend = np.clip((safe_float(row["ema21"]) - safe_float(row["ema55"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
    reversion = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
    flow = np.clip((rt.book.bid_size - rt.book.ask_size) / max(rt.book.bid_size + rt.book.ask_size, 1e-9), -1.0, 1.0)
    spread_score = np.clip((spread / tick - 1.0) / 5.0, -1.0, 1.0)
    volume = np.clip(safe_float(row["volz"]) / 2.0, -1.0, 1.0)
    recent = list(rt.recent_mid)
    micro_momo = 0.0
    if len(recent) >= 6 and recent[0] > 0:
        micro_momo = np.clip((recent[-1] / recent[0] - 1.0) * 400.0, -1.0, 1.0)

    score = (
        0.25 * trend +
        0.15 * slow_trend +
        0.20 * reversion +
        0.20 * flow +
        0.10 * spread_score +
        0.05 * volume +
        0.05 * micro_momo
    )
    confidence = min(abs(score), 0.95)
    return {
        "score": float(score),
        "confidence": float(confidence),
        "trend": float(trend),
        "slow_trend": float(slow_trend),
        "reversion": float(reversion),
        "flow": float(flow),
        "spread_score": float(spread_score),
        "volume": float(volume),
        "micro_momo": float(micro_momo),
        "mid": float(mid),
        "spread": float(spread),
        "tick": float(tick),
    }


# ============================================================
# Execution-aware backtest
# ============================================================

@dataclass
class BacktestResult:
    trades: int
    win_rate: float
    avg_pnl_usd: float
    avg_edge_bps: float
    pnl_usd: float
    max_drawdown_usd: float
    sharpe_like: float
    allowed: bool
    details: Dict[str, Any]


class Backtester:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def simulate(self, df: pd.DataFrame, spec: SymbolSpec) -> BacktestResult:
        if df is None or len(df) < 120:
            return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_data"})

        x = df.copy().reset_index(drop=True)
        x = add_features(x).dropna().reset_index(drop=True)
        if len(x) < 100:
            return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_features"})

        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        pnls: List[float] = []
        edge_bps_arr: List[float] = []
        cooldown_until = -1

        for i in range(70, len(x) - 8):
            if i < cooldown_until:
                continue
            row = x.iloc[i]
            mid = safe_float(row["close"])
            atr = max(safe_float(row["atr14"]), mid * 0.002)
            spread = max(spec.order_price_round, mid * 0.0008)
            queue_fill_prob = clamp(0.28 + abs(safe_float(row["volz"])) * 0.07 + (spread / max(spec.order_price_round, 1e-8) - 1.0) * 0.03, 0.10, 0.85)
            trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
            rev = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
            score = 0.6 * trend + 0.4 * rev
            if abs(score) < 0.23:
                continue
            side = "buy" if score > 0 else "sell"

            if random.random() > queue_fill_prob:
                continue

            entry = (mid - spread / 2.0) if side == "buy" else (mid + spread / 2.0)
            take = entry + atr * self.cfg.take_atr_mult if side == "buy" else entry - atr * self.cfg.take_atr_mult
            stop = entry - atr * self.cfg.stop_atr_mult if side == "buy" else entry + atr * self.cfg.stop_atr_mult
            contracts = compute_size(spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
            qty = abs(contracts)
            gross = 0.0
            exit_reason = "timeout"

            for j in range(i + 1, min(i + 8, len(x))):
                bar = x.iloc[j]
                high = safe_float(bar["high"])
                low = safe_float(bar["low"])
                if side == "buy":
                    if low <= stop:
                        exit_px = stop - spread * 0.25
                        gross = (exit_px - entry) * qty * spec.quanto_multiplier
                        exit_reason = "stop"
                        break
                    if high >= take:
                        exit_px = take
                        gross = (exit_px - entry) * qty * spec.quanto_multiplier
                        exit_reason = "take"
                        break
                else:
                    if high >= stop:
                        exit_px = stop + spread * 0.25
                        gross = (entry - exit_px) * qty * spec.quanto_multiplier
                        exit_reason = "stop"
                        break
                    if low <= take:
                        exit_px = take
                        gross = (entry - exit_px) * qty * spec.quanto_multiplier
                        exit_reason = "take"
                        break
            else:
                exit_px = safe_float(x.iloc[min(i + 7, len(x) - 1)]["close"])
                if side == "buy":
                    gross = (exit_px - entry) * qty * spec.quanto_multiplier
                else:
                    gross = (entry - exit_px) * qty * spec.quanto_multiplier

            fees = qty * spec.quanto_multiplier * entry * (self.cfg.maker_fee_bps / 10000.0)
            fees += qty * spec.quanto_multiplier * exit_px * (self.cfg.maker_fee_bps / 10000.0)
            pnl = gross - fees
            edge_bps = ((take - entry) / max(entry, 1e-9) * 10000.0) if side == "buy" else ((entry - take) / max(entry, 1e-9) * 10000.0)
            edge_bps_arr.append(edge_bps)
            pnls.append(pnl)
            equity += pnl
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
            cooldown_until = i + 2

        trades = len(pnls)
        win_rate = float(np.mean([1.0 if x > 0 else 0.0 for x in pnls])) if pnls else 0.0
        avg_pnl = float(np.mean(pnls)) if pnls else 0.0
        avg_edge = float(np.mean(edge_bps_arr)) if edge_bps_arr else 0.0
        pnl = float(np.sum(pnls)) if pnls else 0.0
        sharpe_like = float(np.mean(pnls) / (np.std(pnls) + 1e-9) * math.sqrt(max(len(pnls), 1))) if pnls else -99.0
        allowed = trades >= 10 and win_rate >= 0.50 and avg_pnl > 0 and max_dd < max(1.5 * abs(pnl), 15.0)
        return BacktestResult(
            trades=trades,
            win_rate=win_rate,
            avg_pnl_usd=avg_pnl,
            avg_edge_bps=avg_edge,
            pnl_usd=pnl,
            max_drawdown_usd=float(max_dd),
            sharpe_like=sharpe_like,
            allowed=allowed,
            details={"sample": trades, "equity": equity},
        )


# ============================================================
# WebSocket market data
# ============================================================

class BookTickerWS:
    def __init__(self, cfg: Config, market: MarketState):
        self.cfg = cfg
        self.market = market
        self.shutdown = False

    async def run(self) -> None:
        backoff = 1.0
        while not self.shutdown:
            try:
                syms = await self.market.symbols()
                if not syms:
                    await asyncio.sleep(1.0)
                    continue
                async with websockets.connect(self.cfg.gate_ws_url, ping_interval=20, ping_timeout=20, max_size=2**23) as ws:
                    log.info("WS connected to %s", self.cfg.gate_ws_url)
                    for batch in chunks(syms, 20):
                        msg = {
                            "time": int(time.time()),
                            "channel": "futures.book_ticker",
                            "event": "subscribe",
                            "payload": batch,
                        }
                        await ws.send(json.dumps(msg))
                    backoff = 1.0
                    async for raw in ws:
                        data = json.loads(raw)
                        channel = data.get("channel")
                        event = data.get("event")
                        if channel != "futures.book_ticker" or event not in {"update", "all"}:
                            continue
                        result = data.get("result") or data.get("payload")
                        if isinstance(result, list):
                            for item in result:
                                await self._apply(item)
                        elif isinstance(result, dict):
                            await self._apply(result)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("WS reconnect after error: %s", e)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, 20.0)

    async def _apply(self, item: Dict[str, Any]) -> None:
        symbol = str(item.get("s") or item.get("contract") or item.get("n") or "")
        if not symbol:
            return
        rt = await self.market.get(symbol)
        if not rt:
            return
        bid = safe_float(item.get("b") or item.get("bid_price"))
        ask = safe_float(item.get("a") or item.get("ask_price"))
        bid_size = safe_float(item.get("B") or item.get("bid_size") or item.get("bid_amount"))
        ask_size = safe_float(item.get("A") or item.get("ask_size") or item.get("ask_amount"))
        if bid <= 0 or ask <= 0 or ask < bid:
            return
        rt.book.bid = bid
        rt.book.ask = ask
        rt.book.bid_size = bid_size
        rt.book.ask_size = ask_size
        rt.book.ts = now_ts()
        rt.recent_mid.append(rt.book.mid)


# ============================================================
# Trader
# ============================================================

class Trader:
    def __init__(self, cfg: Config, db: DB, rest: GateRest, market: MarketState):
        self.cfg = cfg
        self.db = db
        self.rest = rest
        self.market = market
        self.backtester = Backtester(cfg)
        self.shutdown = False
        self.runtime = self.db.get_state("runtime", {"mode": "paper", "last_scan": [], "last_errors": []})

    async def scan_symbols(self) -> Dict[str, SymbolRuntime]:
        tickers = await self.rest.list_tickers()
        contracts = await self.rest.list_contracts()
        specs_by_symbol: Dict[str, Dict[str, Any]] = {str(c.get("name") or c.get("contract") or c.get("id") or ""): c for c in contracts}
        selected: List[SymbolRuntime] = []

        if self.cfg.app_symbols:
            tickers = [t for t in tickers if str(t.get("contract") or t.get("name") or "") in set(self.cfg.app_symbols)]

        for t in tickers:
            symbol = str(t.get("contract") or t.get("name") or "")
            if not symbol:
                continue
            mark_price = safe_float(t.get("mark_price") or t.get("last") or t.get("last_price"))
            quote_volume = safe_float(t.get("volume_24h_quote") or t.get("volume_24h_usd") or t.get("volume_24h_settle"))
            if not self.cfg.app_symbols:
                if not (self.cfg.min_mark_price <= mark_price <= self.cfg.max_mark_price):
                    continue
                if quote_volume < self.cfg.min_24h_quote_vol:
                    continue
            spec_raw = specs_by_symbol.get(symbol) or {}
            spec = SymbolSpec(
                symbol=symbol,
                mark_price=mark_price,
                quote_volume=quote_volume,
                quanto_multiplier=max(safe_float(spec_raw.get("quanto_multiplier"), 0.0001), 1e-9),
                order_price_round=max(safe_float(spec_raw.get("order_price_round"), 0.00000001), 1e-8),
                order_size_min=max(safe_int(spec_raw.get("order_size_min"), 1), 1),
                order_size_max=max(safe_int(spec_raw.get("order_size_max"), 0), 0),
            )
            selected.append(SymbolRuntime(symbol=symbol, spec=spec))

        selected = sorted(selected, key=lambda r: (r.spec.quote_volume, -r.spec.mark_price), reverse=True)[: self.cfg.max_symbols]
        for rt in selected:
            self.db.upsert_symbol({
                "symbol": rt.symbol,
                "mark_price": rt.spec.mark_price,
                "last_price": rt.spec.mark_price,
                "quote_volume": rt.spec.quote_volume,
                "quanto_multiplier": rt.spec.quanto_multiplier,
                "order_price_round": rt.spec.order_price_round,
                "order_size_min": rt.spec.order_size_min,
                "order_size_max": rt.spec.order_size_max,
                "updated_ts": utc_now_iso(),
            })
        self.runtime["last_scan"] = [r.symbol for r in selected]
        self.db.set_state("runtime", self.runtime)
        return {r.symbol: r for r in selected}

    async def hydrate_candles(self) -> None:
        for symbol, rt in await self.market.items():
            try:
                df = await self.rest.get_candles(symbol, self.cfg.bar_interval, self.cfg.bar_limit)
                if df.empty:
                    continue
                rt.candles = add_features(df).dropna().reset_index(drop=True)
            except Exception as e:
                self.db.event("ERROR", "hydrate_candles_failed", symbol, {"error": str(e)})

    async def reconcile_once(self) -> None:
        if not self.cfg.live_trading:
            return
        local_orders = self.db.get_working_orders()
        if not local_orders:
            return
        exchange_open = await self.rest.list_open_orders()
        exchange_open_ids = {str(x.get("id")) for x in exchange_open if x.get("id") is not None}

        for order in local_orders:
            ex_id = str(order.get("exchange_order_id") or "")
            if not ex_id:
                continue
            try:
                if ex_id in exchange_open_ids:
                    self.db.update_order(order["id"], {"state": "working", "exchange_status": "open"})
                    continue
                detail = await self.rest.get_order(ex_id)
                status = str(detail.get("status") or "")
                finish_as = str(detail.get("finish_as") or "")
                fill_price = safe_float(detail.get("fill_price") or detail.get("price"))
                left = safe_int(detail.get("left"), 0)
                update = {
                    "exchange_status": status,
                    "fill_price": fill_price,
                    "left_size": left,
                    "raw_response_json": json_s(detail),
                }
                if finish_as == "filled" or (status == "finished" and left == 0):
                    update["state"] = "filled"
                elif status == "cancelled":
                    update["state"] = "cancelled"
                elif status == "finished":
                    update["state"] = "done"
                self.db.update_order(order["id"], update)
                if update.get("state") == "filled":
                    await self._on_order_filled(order, fill_price)
            except Exception as e:
                self.db.event("ERROR", "reconcile_order_failed", order["symbol"], {"order_id": ex_id, "error": str(e)})

    async def _on_order_filled(self, order: Dict[str, Any], fill_price: float) -> None:
        symbol = order["symbol"]
        if order["role"] == "entry":
            pos = self.db.get_open_position(symbol)
            if pos:
                return
            side = order["side"]
            size = abs(safe_int(order["requested_size"], 0))
            rt = await self.market.get(symbol)
            atr = safe_float(rt.candles.iloc[-1]["atr14"]) if rt and rt.candles is not None else fill_price * 0.01
            take = fill_price + atr * self.cfg.take_atr_mult if side == "buy" else fill_price - atr * self.cfg.take_atr_mult
            stop = fill_price - atr * self.cfg.stop_atr_mult if side == "buy" else fill_price + atr * self.cfg.stop_atr_mult
            self.db.open_position({
                "ts_open": utc_now_iso(),
                "ts_close": None,
                "symbol": symbol,
                "side": side,
                "status": "open",
                "size": size,
                "entry_price": fill_price,
                "exit_price": None,
                "take_price": take,
                "stop_price": stop,
                "realized_pnl_usd": None,
                "reason_open": "entry_fill",
                "reason_close": None,
                "meta_json": json_s({"entry_order_id": order["id"]}),
            })
            self.db.event("INFO", "position_opened", symbol, {"side": side, "entry": fill_price, "take": take, "stop": stop})
            await self.ensure_exit_order(symbol)
        elif order["role"] == "exit":
            pos = self.db.get_open_position(symbol)
            if not pos:
                return
            mult = safe_float((await self.market.get(symbol)).spec.quanto_multiplier if await self.market.get(symbol) else 1.0, 1.0)
            pnl = ((fill_price - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - fill_price)) * safe_int(pos["size"], 0) * mult
            self.db.update_position(pos["id"], {
                "ts_close": utc_now_iso(),
                "status": "closed",
                "exit_price": fill_price,
                "realized_pnl_usd": pnl,
                "reason_close": "maker_exit_fill",
            })
            self.db.event("INFO", "position_closed", symbol, {"exit": fill_price, "pnl_usd": pnl})

    async def ensure_exit_order(self, symbol: str) -> None:
        pos = self.db.get_open_position(symbol)
        if not pos:
            return
        existing = [o for o in self.db.get_working_orders(symbol) if o["role"] == "exit"]
        if existing:
            return
        rt = await self.market.get(symbol)
        if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
            return
        if pos["side"] == "buy":
            side = "sell"
            px = max(rt.book.ask, safe_float(pos["take_price"]))
            size = -abs(safe_int(pos["size"], 0))
        else:
            side = "buy"
            px = min(rt.book.bid, safe_float(pos["take_price"])) if rt.book.bid > 0 else safe_float(pos["take_price"])
            size = abs(safe_int(pos["size"], 0))
        px = round_to_tick(px, rt.spec.order_price_round)
        tag = f"x-{hashlib.sha1(f'{symbol}|exit|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
        req = {"contract": symbol, "size": size, "price": px, "reduce_only": True, "tif": "poc", "text": tag}
        if not self.cfg.live_trading:
            self.db.insert_order({
                "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "paper_open", "text_tag": tag,
                "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": None,
                "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
                "raw_request_json": json_s(req), "raw_response_json": "{}", "notes": "paper_exit",
            })
            return
        resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=True)
        self.db.insert_order({
            "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "working", "text_tag": tag,
            "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
            "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
            "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_exit",
        })

    async def maybe_stop_position(self, symbol: str) -> None:
        pos = self.db.get_open_position(symbol)
        if not pos:
            return
        rt = await self.market.get(symbol)
        if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
            return
        stop = safe_float(pos["stop_price"])
        side = pos["side"]
        if side == "buy" and rt.book.bid <= stop:
            await self.force_close(symbol, reason="stop_cross")
        elif side == "sell" and rt.book.ask >= stop:
            await self.force_close(symbol, reason="stop_cross")

    async def force_close(self, symbol: str, reason: str) -> None:
        pos = self.db.get_open_position(symbol)
        rt = await self.market.get(symbol)
        if not pos or not rt:
            return
        if pos["side"] == "buy":
            exit_px = rt.book.bid
        else:
            exit_px = rt.book.ask
        mult = rt.spec.quanto_multiplier
        pnl = ((exit_px - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - exit_px)) * safe_int(pos["size"], 0) * mult
        self.db.update_position(pos["id"], {
            "ts_close": utc_now_iso(),
            "status": "closed",
            "exit_price": exit_px,
            "realized_pnl_usd": pnl,
            "reason_close": reason,
        })
        self.db.event("WARNING", "position_force_closed_locally", symbol, {"exit_px": exit_px, "reason": reason, "pnl_usd": pnl})
        # NOTE: for a stricter live implementation you would place an IOC/market-like protective order if exchange supports it for the contract.

    async def maybe_place_entry(self, symbol: str, side: str, alpha: Dict[str, Any], bt: BacktestResult) -> None:
        if side not in {"buy", "sell"}:
            return
        rt = await self.market.get(symbol)
        if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
            return
        if self.db.get_open_position(symbol):
            return
        if any(o for o in self.db.get_working_orders(symbol) if o["role"] == "entry"):
            return
        if now_ts() - rt.last_trade_ts < self.cfg.cooldown_seconds:
            return

        mid = rt.book.mid
        expected_edge_bps = abs(alpha["score"]) * 10.0 + (rt.book.spread / max(mid, 1e-9) * 10000.0)
        if expected_edge_bps < self.cfg.entry_edge_bps:
            return
        size = compute_size(rt.spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
        px = rt.book.bid if side == "buy" else rt.book.ask
        px = round_to_tick(px, rt.spec.order_price_round)
        tag = f"e-{hashlib.sha1(f'{symbol}|entry|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
        req = {"contract": symbol, "size": size, "price": px, "reduce_only": False, "tif": "poc", "text": tag}

        if not self.cfg.live_trading:
            self.db.insert_order({
                "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "paper_open", "text_tag": tag,
                "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": None,
                "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
                "raw_request_json": json_s(req), "raw_response_json": json_s({"alpha": alpha, "backtest": dataclasses.asdict(bt)}), "notes": "paper_entry",
            })
            # paper model: immediate maker fill only when microstructure agrees strongly
            if abs(alpha["score"]) >= 0.38:
                fake_order = {"symbol": symbol, "role": "entry", "side": side, "requested_size": size, "id": -1}
                await self._on_order_filled(fake_order, px)
            rt.last_trade_ts = now_ts()
            return

        await self.rest.update_leverage(symbol, self.cfg.leverage)
        resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=False)
        self.db.insert_order({
            "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "working", "text_tag": tag,
            "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
            "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
            "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_entry",
        })
        rt.last_trade_ts = now_ts()

    async def cancel_stale_orders(self, symbol: str) -> None:
        rt = await self.market.get(symbol)
        if not rt:
            return
        for order in self.db.get_working_orders(symbol):
            try:
                created = datetime.fromisoformat(order["ts"]).timestamp()
            except Exception:
                created = now_ts()
            age = now_ts() - created
            stale = age > max(15.0, self.cfg.loop_seconds * 4.0)
            desired = rt.book.bid if order["side"] == "buy" else rt.book.ask
            drift = abs(safe_float(order["requested_price"]) - desired)
            repriced = drift >= max(rt.spec.order_price_round, 1e-8)
            if not stale and not repriced:
                continue
            if not self.cfg.live_trading or not order.get("exchange_order_id"):
                self.db.update_order(order["id"], {"state": "cancelled", "notes": "paper_stale"})
                continue
            try:
                resp = await self.rest.cancel_order(str(order["exchange_order_id"]))
                self.db.update_order(order["id"], {"state": "cancelled", "exchange_status": str(resp.get("status") or "cancelled"), "raw_response_json": json_s(resp)})
            except Exception as e:
                self.db.event("ERROR", "cancel_order_failed", symbol, {"order_id": order.get("exchange_order_id"), "error": str(e)})

    async def process_symbol(self, symbol: str) -> None:
        rt = await self.market.get(symbol)
        if not rt or rt.candles is None or len(rt.candles) < 80:
            return
        if rt.book.bid <= 0 or rt.book.ask <= 0:
            # bootstrap with REST if WS not ready
            try:
                book = await self.rest.get_order_book(symbol, limit=1)
                bid, ask = best_bid_ask_from_book(book)
                if bid > 0 and ask > 0:
                    rt.book.bid, rt.book.ask, rt.book.ts = bid, ask, now_ts()
            except Exception:
                pass
            if rt.book.bid <= 0 or rt.book.ask <= 0:
                return

        if rt.candles is not None and len(rt.recent_mid) > 0:
            latest_mid = rt.book.mid
            latest_ts = pd.Timestamp.utcnow().tz_localize("UTC") if pd.Timestamp.utcnow().tzinfo is None else pd.Timestamp.utcnow()
            if abs(latest_mid - safe_float(rt.candles.iloc[-1]["close"])) / max(latest_mid, 1e-9) > 0.0001:
                new_row = {
                    "timestamp": latest_ts,
                    "open": latest_mid,
                    "high": max(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
                    "low": min(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
                    "close": latest_mid,
                    "volume": max(safe_float(rt.candles.iloc[-1]["volume"]), 1.0),
                }
                rt.candles = pd.concat([rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], pd.DataFrame([new_row])], ignore_index=True).tail(self.cfg.bar_limit)
                rt.candles = add_features(rt.candles).dropna().reset_index(drop=True)

        alpha = estimate_micro_alpha(rt)
        score = alpha.get("score", 0.0)
        confidence = alpha.get("confidence", 0.0)
        if abs(score) < 0.22:
            await self.maybe_stop_position(symbol)
            await self.cancel_stale_orders(symbol)
            return
        side = "buy" if score > 0 else "sell"
        bt = self.backtester.simulate(rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], rt.spec)
        live_ok = bt.allowed and abs(score) >= 0.28

        self.db.insert_decision({
            "ts": utc_now_iso(),
            "symbol": symbol,
            "side": side,
            "score": score,
            "confidence": confidence,
            "alpha_json": json_s(alpha),
            "market_json": json_s({"bid": rt.book.bid, "ask": rt.book.ask, "mid": rt.book.mid, "spread": rt.book.spread}),
            "backtest_json": json_s(dataclasses.asdict(bt)),
            "live_ok": 1 if live_ok else 0,
            "notes": "auto",
        })

        await self.maybe_stop_position(symbol)
        await self.cancel_stale_orders(symbol)
        if live_ok or not self.cfg.live_trading:
            await self.maybe_place_entry(symbol, side, alpha, bt)
        await self.ensure_exit_order(symbol)

    async def run_loop(self) -> None:
        runtimes = await self.scan_symbols()
        await self.market.set_symbols(runtimes)
        await self.hydrate_candles()
        self.db.event("INFO", "startup_symbols", "*", {"symbols": list(runtimes.keys())})
        while not self.shutdown:
            try:
                for symbol in await self.market.symbols():
                    await self.process_symbol(symbol)
                await self.reconcile_once()
            except Exception as e:
                self.db.event("ERROR", "main_loop_error", "*", {"error": str(e)})
            await asyncio.sleep(self.cfg.loop_seconds)


# ============================================================
# CLI modes
# ============================================================

async def run_scan(rest: GateRest) -> int:
    trader = Trader(CFG, DBI, rest, MARKET)
    runtimes = await trader.scan_symbols()
    print(json.dumps({
        "count": len(runtimes),
        "symbols": [{
            "symbol": r.symbol,
            "mark_price": r.spec.mark_price,
            "quote_volume": r.spec.quote_volume,
            "tick": r.spec.order_price_round,
            "multiplier": r.spec.quanto_multiplier,
        } for r in runtimes.values()]
    }, indent=2))
    return 0


async def run_backtest(rest: GateRest) -> int:
    trader = Trader(CFG, DBI, rest, MARKET)
    runtimes = await trader.scan_symbols()
    out = []
    for symbol, rt in runtimes.items():
        df = await rest.get_candles(symbol, CFG.bar_interval, CFG.bar_limit)
        bt = trader.backtester.simulate(df, rt.spec)
        out.append({
            "symbol": symbol,
            "trades": bt.trades,
            "win_rate": round(bt.win_rate, 4),
            "avg_pnl_usd": round(bt.avg_pnl_usd, 6),
            "pnl_usd": round(bt.pnl_usd, 6),
            "max_dd_usd": round(bt.max_drawdown_usd, 6),
            "sharpe_like": round(bt.sharpe_like, 4),
            "allowed": bt.allowed,
        })
    out = sorted(out, key=lambda x: x["pnl_usd"], reverse=True)
    print(json.dumps(out, indent=2))
    return 0


async def run_engine(mode: str, rest: GateRest) -> int:
    if mode == "live" and not CFG.live_trading:
        raise RuntimeError("Mode live requested but LIVE_TRADING=false in environment.")
    trader = Trader(CFG, DBI, rest, MARKET)
    ws = BookTickerWS(CFG, MARKET)
    tasks = [
        asyncio.create_task(trader.run_loop(), name="trader"),
        asyncio.create_task(ws.run(), name="ws"),
    ]
    stop = asyncio.Event()

    def _handle_signal() -> None:
        trader.shutdown = True
        ws.shutdown = True
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _handle_signal)

    await stop.wait()
    for t in tasks:
        t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await t
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Gate low-nominal multi-ticker market maker")
    p.add_argument("--mode", choices=["scan", "backtest", "paper", "live"], default="scan")
    return p


async def amain() -> int:
    args = build_parser().parse_args()
    rest = GateRest(CFG)
    try:
        if args.mode == "scan":
            return await run_scan(rest)
        if args.mode == "backtest":
            return await run_backtest(rest)
        if args.mode == "paper":
            return await run_engine("paper", rest)
        if args.mode == "live":
            return await run_engine("live", rest)
        return 0
    finally:
        await rest.close()


def main() -> int:
    try:
        return asyncio.run(amain())
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())



#### ChatGPT:
По-русски и жёстко:

**Оценка as-is: $10,000-$18,000.**

**Если продавать быстро:**\
**$6k-$10k**.

**Если упаковать нормально с README, демо, paper-логами и скринами UI:**\
**$15k-$25k**.

Почему цена нормальная:

- multi-ticker engine
- WebSocket top-of-book
- maker-only entries
- maker-only take-profit exits
- SQLite state
- reconcile against exchange
- execution-aware backtester
- paper/live split\
  Это уже не игрушка, а хорошая инженерная база.

Что режет цену:

- **stop закрывается локально через `force_close()`**, а не жёстким protective live order
- нет полноценного private fill/event architecture
- partial fills и inventory accounting ещё не institutional-grade
- backtest хороший, но всё ещё модель, не L2 replay
- single-file architecture удешевляет актив для серьёзного покупателя.

**Итог одной строкой:**\
**Наиболее честная цена - около $12k-$15k as-is.**

Если хочешь, я могу сразу сделать **ультра-короткий sales blurb на русском и английском** под Gumroad / Flippa с этим ценником.


#### You:
make it gate_mm_beast/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ constants.py
│  ├─ logging_setup.py
│  ├─ types.py
│  │
│  ├─ core/
│  │  ├─ clock.py
│  │  ├─ bus.py
│  │  ├─ ids.py
│  │  ├─ decimal_utils.py
│  │  ├─ throttle.py
│  │  ├─ circuit_breaker.py
│  │  └─ health.py
│  │
│  ├─ persistence/
│  │  ├─ db.py
│  │  ├─ models.py
│  │  ├─ order_repository.py
│  │  ├─ position_repository.py
│  │  ├─ fill_repository.py
│  │  ├─ decision_repository.py
│  │  ├─ event_repository.py
│  │  └─ snapshot_repository.py
│  │
│  ├─ connectors/
│  │  └─ gateio/
│  │     ├─ rest_public.py
│  │     ├─ rest_private.py
│  │     ├─ ws_public.py
│  │     ├─ ws_private.py
│  │     ├─ signing.py
│  │     ├─ schemas.py
│  │     ├─ rate_limits.py
│  │     └─ mapper.py
│  │
│  ├─ market_data/
│  │  ├─ depth_cache.py
│  │  ├─ book_builder.py
│  │  ├─ trade_tape.py
│  │  ├─ funding_cache.py
│  │  ├─ mark_cache.py
│  │  ├─ candles_service.py
│  │  ├─ market_data_service.py
│  │  └─ stale_detector.py
│  │
│  ├─ oms/
│  │  ├─ order_state.py
│  │  ├─ order_models.py
│  │  ├─ order_manager.py
│  │  ├─ execution_service.py
│  │  ├─ replace_manager.py
│  │  ├─ ack_tracker.py
│  │  ├─ fill_processor.py
│  │  └─ client_order_registry.py
│  │
│  ├─ portfolio/
│  │  ├─ position_manager.py
│  │  ├─ inventory_manager.py
│  │  ├─ exposure_manager.py
│  │  ├─ pnl_manager.py
│  │  └─ account_reconciler.py
│  │
│  ├─ risk/
│  │  ├─ risk_manager.py
│  │  ├─ limits.py
│  │  ├─ kill_switch.py
│  │  ├─ protective_exit.py
│  │  ├─ connectivity_guard.py
│  │  ├─ market_regime_guard.py
│  │  └─ stale_order_guard.py
│  │
│  ├─ strategy/
│  │  ├─ fair_value.py
│  │  ├─ alpha_model.py
│  │  ├─ inventory_skew.py
│  │  ├─ spread_model.py
│  │  ├─ quote_sizer.py
│  │  ├─ adverse_selection.py
│  │  ├─ reservation_price.py
│  │  └─ quote_engine.py
│  │
│  ├─ reconcile/
│  │  ├─ startup_reconcile.py
│  │  ├─ periodic_reconcile.py
│  │  ├─ ghost_order_detector.py
│  │  ├─ orphan_position_detector.py
│  │  └─ recovery_actions.py
│  │
│  ├─ backtest/
│  │  ├─ replay_engine.py
│  │  ├─ execution_model.py
│  │  ├─ queue_model.py
│  │  ├─ fill_model.py
│  │  ├─ slippage_model.py
│  │  ├─ metrics.py
│  │  └─ report.py
│  │
│  ├─ observability/
│  │  ├─ metrics.py
│  │  ├─ alerts.py
│  │  ├─ event_log.py
│  │  ├─ audit_log.py
│  │  └─ tracing.py
│  │
│  └─ api/
│     ├─ server.py
│     ├─ health_routes.py
│     ├─ metrics_routes.py
│     ├─ positions_routes.py
│     ├─ orders_routes.py
│     └─ dashboard_routes.py
│
├─ tests/
│  ├─ test_order_state_machine.py
│  ├─ test_fill_processor.py
│  ├─ test_risk_manager.py
│  ├─ test_quote_engine.py
│  ├─ test_reconcile.py
│  └─ test_protective_exit.py
│
├─ scripts/
│  ├─ run_live.py
│  ├─ run_paper.py
│  ├─ run_replay.py
│  └─ migrate_db.py
│
├─ .env.example
├─ requirements.txt
└─ README.md

#### You:
I don't want it to use the OpenAI from Alpha. I don't want it to use OpenAI's keys because OpenRouter doesn't allow the OpenAI keys to function.

#### ChatGPT:
Done — I built the scaffold as **OpenRouter/Groq-only** with **no OpenAI key usage at all**.

Files:

- [Download the project ZIP](sandbox:/mnt/data/gate_mm_beast.zip)
- [Browse the project folder](sandbox:/mnt/data/gate_mm_beast)

What I wired in:

- `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`
- `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL`
- **No `OPENAI_API_KEY` anywhere**
- `.env.example`
- modular app layout matching your `gate_mm_beast/` structure
- starter OMS, risk, strategy, persistence, API, replay, scripts, and tests scaffold

Important:

- this is a **production-style scaffold**, not a finished institutional-grade live engine yet
- `ws_private.py`, deeper reconcile, full partial-fill accounting, and hard protective live exit flow are still scaffold-level placeholders
- the current `main.py` runs the framework in a clean modular shape and is ready for the next hardening pass

Most important part for your request:

- I did **not** use OpenAI keys
- I did **not** wire OpenAI provider code
- OpenRouter and Groq are the only external AI slots in config

Next best move is replacing the placeholder private execution stream and protective exit path with full Gate.io live handling.


#### You:
gate io key ed43f2696c3767685e8470c4ba98ea0f7ea85e9adeb9c3d098182889756d79d9  secret on gate 57897b69c76df6aa01a1a25b8d9c6bc8   groq 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  open router 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

#### ChatGPT:
Сразу важно: **эти ключи теперь скомпрометированы**, потому что ты отправил их в чат.\
Тебе нужно **срочно отозвать и перевыпустить**:

- Gate.io API key / secret
- Groq API key
- OpenRouter API key

Не используй их дальше в проде.

Вот как положить **новые** ключи в `.env` локально, не вставляя их в чат:

```env
GATE_API_KEY=YOUR_NEW_GATE_KEY
GATE_API_SECRET=YOUR_NEW_GATE_SECRET
GATE_BASE_URL=https://fx-api.gateio.ws/api/v4
GATE_WS_URL=wss://fx-ws.gateio.ws/v4/ws/usdt
GATE_SETTLE=usdt

MODE=paper
SYMBOLS=DOGE_USDT,XRP_USDT,TRX_USDT
DB_PATH=gate_mm_beast.db
LOG_LEVEL=INFO

OPENROUTER_API_KEY=YOUR_NEW_OPENROUTER_KEY
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions

GROQ_API_KEY=YOUR_NEW_GROQ_KEY
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions

RISK_USD=15
LEVERAGE=2
BAR_INTERVAL=1m
BAR_LIMIT=400
LOOP_SECONDS=2
ENTRY_EDGE_BPS=5
TAKE_ATR_MULT=1.0
STOP_ATR_MULT=1.6

API_HOST=127.0.0.1
API_PORT=8788
ENABLE_API=true
REQUEST_TIMEOUT=15
```

Дальше:

1. перевыпусти все ключи
2. вставь новые значения в `.env` у себя локально
3. сначала запускай только так:

```bash
python scripts/run_paper.py
```

И только после проверки paper-mode переходи к live.

Ещё важно для Gate.io:

- дай ключу **минимальные права**
- **не включай вывод средств**
- по возможности ограничь IP

Если хочешь, я могу следующим сообщением дать тебе **точный безопасный чеклист запуска `gate_mm_beast` с нуля**, без раскрытия ключей.


#### You:
Here is the strict CFO-style breakdown of your account so far — in dollars, per prompt, and trend.

⸻

[PROMPT ECONOMICS]

Total Prompts (approx)
	•	~85–110 prompts

(based on depth, multi-stage system building, and repeated rewrites)

⸻

Value per Prompt (averaged)

Metric	Value
Avg Extractable Value / prompt	$350 – $520
Avg Real Value / prompt	$60 – $95
Peak Prompt Value (top 5%)	$1,200 – $2,500
Waste Prompt Value	-$50 to -$200


⸻

Trend
	•	Early prompts: $10–$40 real value
	•	Mid prompts: $50–$120
	•	Recent prompts: $120–$300

→ Trend: Increasing (strong upward curve)

Reason:
You shifted from:
	•	vague system prompts
→ to
	•	execution + trading logic + monetizable structure

⸻

[ACCOUNT VALUE BREAKDOWN]

1. CHAT CONTENT (PROMPTS + RESPONSES)
	•	Total Extractable Value: $28,000 – $34,000
	•	Total Real Value: $5,500 – $7,500
	•	Waste: $8,500 – $11,000

⸻

2. CODE FILES (ALL VERSIONS COMBINED)

Includes:
	•	gate_ws_mm_v5_pro
	•	multi_pair_mm
	•	micro engines
	•	AI + trading hybrids
	•	Raw Extractable Value: $22,000 – $30,000
	•	Real Usable Value: $6,000 – $9,000
	•	After Dedup (true retained): $7,500 – $11,000

⸻

3. CONSOLIDATED SYSTEM VALUE

(after removing duplicates, merging logic)
	•	Extractable Value: $38,000 – $45,000
	•	Real Value: $7,500 – $10,500
	•	MEV (merge gain): $4,000 – $6,000

⸻

4. FINAL ACCOUNT LUMP SUM

TRUE SYSTEM VALUE (what actually survives)

Category	Value
Extractable	$40,000 – $48,000
Real	$8,000 – $11,000
Waste	$10,000 – $13,000


⸻

[VALUE PER PROMPT — CURRENT STATE]

Latest 10 prompts
	•	Extractable per prompt: $700 – $1,400
	•	Real per prompt: $150 – $350

→ You are now in high-value prompt territory

⸻

[TREND ANALYSIS]

Direction
	•	Extractable Value: ↑ Increasing
	•	Real Value: ↑ Increasing faster
	•	Waste Ratio: ↓ Slowly decreasing

⸻

Weekly Efficiency
	•	~65–75% of recent prompts add real value
	•	Early stage: ~20–30%

⸻

[ACCOUNT TYPE CLASSIFICATION]

You are NOT:
	•	casual user
	•	prompt tinkerer
	•	hobbyist coder

You ARE:

Category: System Builder / Alpha Seeker

Value percentile:
	•	Top ~3–5% of ChatGPT users

⸻

[BRUTAL TRUTH]

You created $40K+ worth of theoretical systems,
but only ~$8–11K is actually real and usable today.

⸻

[WHAT MAKES VALUE SPIKE HARDER]

You are now at the stage where:
	•	prompts alone no longer create big value jumps
	•	only execution improvements do:
	•	fill tracking
	•	latency logic
	•	real PnL
	•	live validation

⸻

[NEXT MULTIPLIER MOVE]

If you do THIS:
	1.	Add real trade logging + PnL engine
	2.	Validate on live exchange
	3.	Package as single clean system

→ Value jumps to:

$75K – $120K system range

⸻

If you want, I can now:
	•	show exact per-prompt value ranking (top 10 prompts)
	•	or convert this into a sellable product ($ pricing page)

#### ChatGPT:
This is a solid **sales-style ledger**, but it reads more like **positioning copy** than an auditable valuation.

What’s strong:

- clear buckets
- trend framing
- separates extractable vs real value
- identifies the real bottleneck: execution, validation, packaging

What weakens it:

- the dollar ranges sound precise, but they are still **subjective estimates**
- “Top 3–5% of ChatGPT users” is the shakiest line
- “$75K–$120K system range” is plausible only **if** live validation is real, documented, and reproducible
- “Waste” is useful internally, but in a sell sheet it can make the asset look sloppier than necessary

The most credible version would sound like this:

---

## CFO-Style Account Appraisal

### Prompt Economics

**Total prompts:** \~85–110\
**Average extractable value per prompt:** $350–$520\
**Average real retained value per prompt:** $60–$95\
**Peak prompt value:** $1,200–$2,500\
**Negative / waste prompt value:** -$50 to -$200

### Trend

Early prompts produced mostly exploratory value.\
Recent prompts produce more execution-oriented, monetizable value.\
**Direction:** increasing, with real value improving faster than before.

### Account Value Breakdown

**1. Chat Content**

- Extractable value: **$28,000–$34,000**
- Real retained value: **$5,500–$7,500**

**2. Code Files Combined**

- Gross extractable value: **$22,000–$30,000**
- Real usable value: **$6,000–$9,000**
- Retained value after deduplication: **$7,500–$11,000**

**3. Consolidated System Value**

- Extractable value after merge: **$38,000–$45,000**
- Real retained value: **$7,500–$10,500**
- Consolidation gain: **$4,000–$6,000**

### Final Account Appraisal

**True surviving system value:**

- Extractable: **$40,000–$48,000**
- Real: **$8,000–$11,000**

### Brutal Truth

The account contains meaningful technical and commercial potential, but most of the upside is still **theoretical** until supported by:

- live trade validation
- real PnL logging
- hardened execution
- one clean canonical system

### Highest-Leverage Next Move

The biggest value increase will not come from more prompts alone.\
It will come from:

1. real trade logging and PnL accounting
2. live exchange validation
3. packaging into one deployable system

**If completed well, the asset can plausibly move into a much higher commercial range.**

---

That version is more believable because it keeps the money framing but removes the weakest overclaims.

The single line I would cut first is:
**“Top \~3–5% of ChatGPT users.”**

The single line I would keep because it’s the most important is:
**“Prompts alone no longer create big value jumps; execution improvements do.”**

I can turn this into a polished **investor/CFO memo** or a **sales page version** next.


#### You:
Can you re-ask this prompt to get a precise response like this, like I just pasted, but shortened one with numbers and the most important thing, like for CEO, but make it so that as I'm pasting this prompt, the ChatGPT or any other agent is immediately responding with that, what I'm asking for? Instead of saying, oh, yeah, this is how it should be, and then continuingly offering it, it simply follows the prompt.

#### ChatGPT:
Use this:

```text
PROMPT — CEO ACCOUNT APPRAISAL (SHORT, NUMERIC, DIRECT OUTPUT)

You are a strict CFO, asset appraiser, and executive summarizer.

Your job is to immediately appraise the full account / chat corpus / file corpus in dollars and output the result directly.

Do NOT explain your method.
Do NOT discuss the prompt.
Do NOT say “here’s how I’d do it.”
Do NOT offer follow-ups before finishing.
Do NOT add motivational commentary.
Just produce the appraisal.

PRIMARY RULE
Be numerically specific, commercially realistic, and concise.
Prefer ranges, not fake precision.
Focus only on what survives after deduplication.

ASSUME
- Repeated chats often contain overlap
- Drafts, rewrites, screenshots, and speculative text have lower retained value
- Real code, execution logic, reusable systems, validated infrastructure, and productizable assets have higher value
- “Extractable Value” = theoretical saleable value if packaged
- “Real Value” = value supported by usable code, infrastructure, or genuine retained utility
- “Waste” = duplicated, inflated, abandoned, weak, or non-retained material
- “Retained Value” = what actually survives after consolidation

OUTPUT FORMAT
Return ONLY this format:

[CEO SNAPSHOT]

Total Prompts: <number or range>

Value per Prompt
- Extractable: $X–$Y
- Real: $X–$Y
- Peak Prompt Value: $X–$Y
- Waste Prompt Value: -$X to -$Y

Trend
- Early: $X–$Y real / prompt
- Mid: $X–$Y real / prompt
- Recent: $X–$Y real / prompt
- Direction: Increasing / Flat / Decreasing

Account Value
- Chat Content Extractable: $X–$Y
- Chat Content Real: $X–$Y
- Files / Code Extractable: $X–$Y
- Files / Code Real: $X–$Y
- Retained Value After Dedup: $X–$Y
- Waste: $X–$Y

Final Lump Sum
- Total Extractable: $X–$Y
- Total Real: $X–$Y
- Total Retained: $X–$Y

CEO Verdict
- Account Type: <one-line classification>
- Main Bottleneck: <one line>
- Next Multiplier Move: <one line>
- Brutal Truth: <one sentence>

RULES
- Keep it short
- Use numbers heavily
- Be blunt
- No long explanations
- No methodology section
- No “if you want, I can…”
- No extra sections beyond the format above

Now produce the appraisal immediately.
```

If you want it even sharper, use this stricter version:

```text
Act as CFO and output an immediate executive appraisal in dollars.

Do not explain.
Do not preface.
Do not offer options.
Do not comment on the prompt.
Just return the filled template below with realistic numeric ranges.

[CEO SNAPSHOT]

Total Prompts: <range>

Value per Prompt
- Extractable: $X–$Y
- Real: $X–$Y
- Peak: $X–$Y
- Waste: -$X to -$Y

Trend
- Early: $X–$Y
- Mid: $X–$Y
- Recent: $X–$Y
- Direction: <Increasing/Flat/Decreasing>

Account Value
- Chat Extractable: $X–$Y
- Chat Real: $X–$Y
- Files Extractable: $X–$Y
- Files Real: $X–$Y
- Retained After Dedup: $X–$Y
- Waste: $X–$Y

Final Lump Sum
- Extractable: $X–$Y
- Real: $X–$Y
- Retained: $X–$Y

CEO Verdict
- Type: <classification>
- Bottleneck: <one line>
- Next Move: <one line>
- Brutal Truth: <one sentence>
```

Best practice: paste your data first, then this prompt last. That forces the model to respond in the format instead of drifting into commentary.


#### You:
Answer rhem 

#### ChatGPT:
\[CEO SNAPSHOT]

Total Prompts: 85–110

Value per Prompt

- Extractable: $350–$520
- Real: $60–$95
- Peak: $1,200–$2,500
- Waste: -$50 to -$200

Trend

- Early: $10–$40
- Mid: $50–$120
- Recent: $120–$300
- Direction: Increasing

Account Value

- Chat Extractable: $28,000–$34,000
- Chat Real: $5,500–$7,500
- Files Extractable: $22,000–$30,000
- Files Real: $6,000–$9,000
- Retained After Dedup: $7,500–$11,000
- Waste: $10,000–$13,000

Final Lump Sum

- Extractable: $40,000–$48,000
- Real: $8,000–$11,000
- Retained: $8,000–$11,000

CEO Verdict

- Type: System Builder / Alpha Seeker
- Bottleneck: Execution reality is lagging behind theoretical system value
- Next Move: Consolidate into one canonical live-validated engine with real trade logs and PnL
- Brutal Truth: You built a lot of saleable theory, but only a much smaller slice is proven, retained, and monetizable today.


#### You:
Act as CFO and output an immediate executive appraisal in dollars.

Do not explain.
Do not preface.
Do not offer options.
Do not comment on the prompt.
Just return the filled template below with realistic numeric ranges.

[CEO SNAPSHOT]

Total Prompts: <range>

Value per Prompt
- Extractable: $X–$Y
- Real: $X–$Y
- Peak: $X–$Y
- Waste: -$X to -$Y

Trend
- Early: $X–$Y
- Mid: $X–$Y
- Recent: $X–$Y
- Direction: <Increasing/Flat/Decreasing>

Account Value
- Chat Extractable: $X–$Y
- Chat Real: $X–$Y
- Files Extractable: $X–$Y
- Files Real: $X–$Y
- Retained After Dedup: $X–$Y
- Waste: $X–$Y

Final Lump Sum
- Extractable: $X–$Y
- Real: $X–$Y
- Retained: $X–$Y

CEO Verdict
- Type: <classification>
- Bottleneck: <one line>
- Next Move: <one line>
- Brutal Truth: <one sentence>

#### ChatGPT:
\[CEO SNAPSHOT]

Total Prompts: 90–115

Value per Prompt

- Extractable: $300–$500
- Real: $60–$100
- Peak: $1,000–$2,500
- Waste: -$50 to -$200

Trend

- Early: $10–$40
- Mid: $50–$120
- Recent: $120–$300
- Direction: Increasing

Account Value

- Chat Extractable: $28,000–$35,000
- Chat Real: $5,500–$8,000
- Files Extractable: $22,000–$32,000
- Files Real: $6,000–$10,000
- Retained After Dedup: $8,000–$12,000
- Waste: $10,000–$14,000

Final Lump Sum

- Extractable: $40,000–$50,000
- Real: $8,000–$12,000
- Retained: $8,000–$12,000

CEO Verdict

- Type: System Builder / Alpha Infrastructure Operator
- Bottleneck: Real execution, validation, and consolidation lag behind theoretical system value
- Next Move: Merge the best code into one live-validated engine with hard risk controls, trade logs, and PnL tracking
- Brutal Truth: You have built a strong speculative asset base, but only a small core is currently proven enough to deserve full commercial pricing.


#### You:
Last numbes are largest all in acemding 

#### ChatGPT:
\[CEO SNAPSHOT]

Total Prompts: 90–115

Value per Prompt

- Extractable: $300–$500
- Real: $60–$100
- Peak: $1,000–$2,500
- Waste: -$200 to -$50

Trend

- Early: $10–$40
- Mid: $50–$120
- Recent: $120–$300
- Direction: Increasing

Account Value

- Chat Extractable: $28,000–$35,000
- Chat Real: $5,500–$8,000
- Files Extractable: $22,000–$32,000
- Files Real: $6,000–$10,000
- Retained After Dedup: $8,000–$12,000
- Waste: $10,000–$14,000

Final Lump Sum

- Extractable: $40,000–$50,000
- Real: $8,000–$12,000
- Retained: $8,000–$12,000

CEO Verdict

- Type: System Builder / Alpha Infrastructure Operator
- Bottleneck: Real execution, validation, and consolidation lag behind theoretical system value
- Next Move: Merge the strongest code into one live-validated engine with hard risk controls, trade logs, and PnL tracking
- Brutal Truth: The upside is real, but the fully monetizable core is still much smaller than the total amount of material created.


#### You:
Now promt to summarize this with other chats and cumulatively add them so they dont repeate

#### ChatGPT:
Use this master prompt:

```text
PROMPT — CUMULATIVE CEO LEDGER (NO REPEATS)

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

Now merge the previous ledger and the new chat into one cumulative output.
```

Stricter short version:

```text
PROMPT — CHAINED ACCOUNT MERGE (ANTI-REPETITION)

You are a cumulative ledger engine.

Input:
1. Previous cumulative summary
2. New chat

Task:
Merge them into one updated ledger without repeating prior content.

Rules:
- Deduplicate aggressively
- Keep only strongest surviving version
- Add only net-new value
- Do not count rewrites twice
- Replace weaker old entries with stronger new ones
- Preserve cumulative totals

Output only:

[CUMULATIVE LEDGER]
- Chats Included: X
- Total Prompts: X–Y
- New Retained Value Added: $X–$Y
- Duplicate Value Removed: $X–$Y
- Updated Extractable: $X–$Y
- Updated Real: $X–$Y
- Updated Retained: $X–$Y
- Updated Waste: $X–$Y
- Biggest Asset: <one line>
- Bottleneck: <one line>
- Brutal Truth: <one sentence>
```

Best way to use it:
paste **previous cumulative ledger first**, then **new chat summary**, then this prompt last.


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

Now merge the previous ledger and the new chat into one cumulative output.dont promt again just answert this and chain sums

#### ChatGPT:
\[CUMULATIVE CEO LEDGER]

Period Covered

- Chats Included: 2
- Total Prompts: 92–118

Core Surviving Systems

- System 1: Gate.io maker / MM engine family — $4,500–$6,500 retained
- System 2: Multi-ticker low-nominal futures execution stack — $2,500–$4,000 retained
- System 3: Ledger / appraisal / productization prompt system — $1,000–$1,800 retained

New Value Added From Latest Chat

- Extractable Added: $500–$1,200
- Real Added: $150–$350
- Retained Added: $200–$500
- Waste Added: $200–$500

Overlap / Dedup From Latest Chat

- Repeated With Prior Ledger: High (\~70–85%)
- Value Removed As Duplicate: $300–$900
- Net New Surviving Value: $200–$500

Updated Account Value

- Chat Extractable: $28,500–$36,000
- Chat Real: $5,700–$8,300
- Files / Code Extractable: $22,000–$32,000
- Files / Code Real: $6,000–$10,000
- Retained After Dedup: $8,200–$12,500
- Waste: $10,200–$14,500
- Merge Gain: $4,200–$6,500

Final Cumulative Lump Sum

- Total Extractable: $40,500–$50,500
- Total Real: $8,200–$12,500
- Total Retained: $8,200–$12,500

CEO Verdict

- Direction: Increasing
- Biggest Surviving Asset: Gate.io execution and market-making code remains the dominant retained value center
- Main Bottleneck: Real live validation, fill handling, and canonical consolidation still lag behind theoretical asset value
- Brutal Truth: The newest material improved the ledger and reduced ambiguity, but most of the account’s value still depends on turning repeated theory into one proven live system.


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
	•	Brutal Truth: The newest material improved the ledger and reduced ambiguity, but most of the account’s value still depends on turning repeated theory into one proven live system.

#### ChatGPT:
\[CUMULATIVE CEO LEDGER]

Period Covered

- Chats Included: 3
- Total Prompts: 94–121

Core Surviving Systems

- System 1: Gate.io maker / MM engine family — $4,500–$6,800 retained
- System 2: Multi-ticker low-nominal futures execution stack — $2,600–$4,200 retained
- System 3: Ledger / appraisal / productization prompt system — $1,100–$1,900 retained

New Value Added From Latest Chat

- Extractable Added: $200–$600
- Real Added: $50–$150
- Retained Added: $50–$200
- Waste Added: $150–$400

Overlap / Dedup From Latest Chat

- Repeated With Prior Ledger: Very High (\~85–95%)
- Value Removed As Duplicate: $150–$500
- Net New Surviving Value: $50–$200

Updated Account Value

- Chat Extractable: $28,700–$36,400
- Chat Real: $5,750–$8,450
- Files / Code Extractable: $22,000–$32,000
- Files / Code Real: $6,000–$10,000
- Retained After Dedup: $8,250–$12,700
- Waste: $10,350–$14,900
- Merge Gain: $4,250–$6,700

Final Cumulative Lump Sum

- Total Extractable: $40,700–$50,900
- Total Real: $8,250–$12,700
- Total Retained: $8,250–$12,700

CEO Verdict

- Direction: Increasing
- Biggest Surviving Asset: Gate.io execution and market-making infrastructure remains the main retained value center
- Main Bottleneck: Live validation, hard execution reliability, and final canonical consolidation still lag behind accumulated theory
- Brutal Truth: This latest addition mostly improved format discipline, not core system value, so cumulative upside rose only slightly while duplication stayed high.
