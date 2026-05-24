# Rolling compressed value chain audit Gate.io

#### You:
Appraise this code in russian #!/usr/bin/env python3

# -*- coding: utf-8 -*-

“””
gate_ai_saas_single_file.py

Single-file Gate.io AI ensemble trading service with:

- Gate.io futures market data
- OpenRouter + Groq AI voting
- local rule model
- walk-forward gate
- paper/live execution
- persistent SQLite storage
- persistent JSONL service logs
- execution journal
- restart-safe state recovery
- embedded local web UI
- embedded docs / README
- one-file IDE deployment style

## INSTALL

pip install requests pandas pandas_ta numpy python-dotenv

## RUN

python gate_ai_saas_single_file.py

## OPTIONAL ENV

GATE_API_KEY=…
GATE_API_SECRET=…
OPENROUTER_API_KEY=…
GROQ_API_KEY=…

GATE_BASE_URL=https://api.gateio.ws/api/v4
GATE_SETTLE=usdt
GATE_CONTRACT=BTC_USDT

OPENROUTER_MODEL=openai/gpt-4.1-mini
GROQ_MODEL=llama-3.3-70b-versatile

LIVE_TRADING=false
ALLOW_NEW_LIVE_ENTRIES=false
REDUCE_ONLY_ON_EXIT=true

RISK_USD=25
LEVERAGE=2
FEE_BPS=6
SLIPPAGE_BPS=2

INTERVAL=15m
BARS_LIMIT=800
LOOP_SECONDS=30

WALKFORWARD_BARS=120
MIN_PASS_RATE=0.54
MIN_AVG_R=0.03
MIN_TRADES=20

TP_ATR_MULT=1.2
SL_ATR_MULT=0.8

REQUEST_TIMEOUT=20
DRY_RUN_ONLY_WHEN_NO_AI=true

APP_HOST=127.0.0.1
APP_PORT=8787

DB_PATH=gate_ai_service.db
LOG_JSONL=gate_ai_service.jsonl

## WHAT THIS DOES

- calculates indicators from Gate candles
- builds a local decision
- optionally asks OpenRouter and Groq for structured votes
- combines everything into one ensemble decision
- gates live entry through walk-forward stats
- stores decisions, trades, live orders, positions, service events in SQLite
- serves a local UI from one file
- keeps execution history across restarts

## IMPORTANT

- This is a framework, not a guarantee of profitability.
- Keep LIVE_TRADING=false until you personally validate every payload and behavior.
- The code persists execution and state, but exchange-side reconciliation should still be reviewed by you before real capital use.
  “””

from **future** import annotations

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
import traceback
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import pandas_ta as ta
import requests
from dotenv import load_dotenv

load_dotenv()

# ============================================================

# Config

# ============================================================

@dataclass
class Config:
gate_api_key: str = os.getenv(“GATE_API_KEY”, “”)
gate_api_secret: str = os.getenv(“GATE_API_SECRET”, “”)
gate_base_url: str = os.getenv(“GATE_BASE_URL”, “https://api.gateio.ws/api/v4”)
settle: str = os.getenv(“GATE_SETTLE”, “usdt”).lower()
contract: str = os.getenv(“GATE_CONTRACT”, “BTC_USDT”)

```
openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

groq_api_key: str = os.getenv("GROQ_API_KEY", "")
groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")

live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
allow_new_live_entries: bool = os.getenv("ALLOW_NEW_LIVE_ENTRIES", "false").lower() == "true"
reduce_only_on_exit: bool = os.getenv("REDUCE_ONLY_ON_EXIT", "true").lower() == "true"

risk_usd: float = float(os.getenv("RISK_USD", "25"))
leverage: int = int(os.getenv("LEVERAGE", "2"))
fee_bps: float = float(os.getenv("FEE_BPS", "6"))
slippage_bps: float = float(os.getenv("SLIPPAGE_BPS", "2"))

interval: str = os.getenv("INTERVAL", "15m")
bars_limit: int = int(os.getenv("BARS_LIMIT", "800"))
loop_seconds: int = int(os.getenv("LOOP_SECONDS", "30"))

walkforward_bars: int = int(os.getenv("WALKFORWARD_BARS", "120"))
min_pass_rate: float = float(os.getenv("MIN_PASS_RATE", "0.54"))
min_avg_r: float = float(os.getenv("MIN_AVG_R", "0.03"))
min_trades: int = int(os.getenv("MIN_TRADES", "20"))

tp_atr_mult: float = float(os.getenv("TP_ATR_MULT", "1.2"))
sl_atr_mult: float = float(os.getenv("SL_ATR_MULT", "0.8"))
max_memory_rows: int = int(os.getenv("MAX_MEMORY_ROWS", "5000"))

request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
dry_run_only_when_no_ai: bool = os.getenv("DRY_RUN_ONLY_WHEN_NO_AI", "true").lower() == "true"

db_path: str = os.getenv("DB_PATH", "gate_ai_service.db")
log_jsonl: str = os.getenv("LOG_JSONL", "gate_ai_service.jsonl")

app_host: str = os.getenv("APP_HOST", "127.0.0.1")
app_port: int = int(os.getenv("APP_PORT", "8787"))
```

CFG = Config()

# ============================================================

# Logging

# ============================================================

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s | %(levelname)s | %(message)s”,
)
log = logging.getLogger(“gate-ai-saas”)

def utc_now_iso() -> str:
return datetime.now(timezone.utc).isoformat()

def safe_float(x: Any, default: float = 0.0) -> float:
try:
if x is None or (isinstance(x, float) and math.isnan(x)):
return default
return float(x)
except Exception:
return default

def clamp(x: float, lo: float, hi: float) -> float:
return max(lo, min(hi, x))

def json_dumps(x: Any) -> str:
return json.dumps(x, ensure_ascii=False, separators=(”,”, “:”))

def append_jsonl(path: str, row: Dict[str, Any]) -> None:
with open(path, “a”, encoding=“utf-8”) as f:
f.write(json.dumps(row, ensure_ascii=False) + “\n”)

# ============================================================

# Database

# ============================================================

class Database:
def **init**(self, path: str):
self.path = path
self._lock = threading.Lock()
self._init_db()

```
def _conn(self) -> sqlite3.Connection:
    conn = sqlite3.connect(self.path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db(self) -> None:
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
            close REAL,
            ema_9 REAL,
            ema_21 REAL,
            sma_20 REAL,
            sma_50 REAL,
            rsi_14 REAL,
            atr_14 REAL,
            adx_14 REAL,
            bb_width REAL,
            obv REAL,
            ret_1 REAL,
            ret_4 REAL,
            ret_16 REAL,
            vol_z REAL,
            dist_ema21_atr REAL,
            trend_gap REAL,
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
            why_json TEXT,
            walk_pass_rate REAL,
            walk_avg_r REAL,
            walk_trades INTEGER,
            walk_allowed_live INTEGER,
            live_executed INTEGER,
            live_order_response TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS simulated_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_ts TEXT,
            exit_ts TEXT,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            side TEXT NOT NULL,
            entry REAL,
            exit REAL,
            tp REAL,
            sl REAL,
            atr REAL,
            bars_held INTEGER,
            gross_r REAL,
            net_r REAL,
            gross_pnl_pct REAL,
            net_pnl_pct REAL,
            outcome TEXT,
            decision_ref_ts TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS live_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            decision_ts TEXT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            order_role TEXT NOT NULL,
            requested_size INTEGER NOT NULL,
            reduce_only INTEGER NOT NULL,
            intended_entry REAL,
            intended_tp REAL,
            intended_sl REAL,
            exchange_order_id TEXT,
            exchange_status TEXT,
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
            decision_ts TEXT,
            entry_order_id TEXT,
            exit_order_id TEXT,
            exit_price REAL,
            realized_pnl_pct REAL,
            realized_r REAL,
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
    row = {
        "ts": utc_now_iso(),
        "level": level,
        "kind": kind,
        "payload_json": json.dumps(payload, ensure_ascii=False),
    }
    with self._lock, self._conn() as conn:
        conn.execute(
            "INSERT INTO service_events (ts, level, kind, payload_json) VALUES (?, ?, ?, ?)",
            (row["ts"], row["level"], row["kind"], row["payload_json"]),
        )
        conn.commit()

    append_jsonl(CFG.log_jsonl, {"ts": row["ts"], "level": level, "kind": kind, **payload})

def insert_decision(self, row: Dict[str, Any]) -> None:
    cols = list(row.keys())
    sql = f"INSERT INTO decisions ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        conn.execute(sql, vals)
        conn.commit()

def insert_sim_trade(self, row: Dict[str, Any]) -> None:
    cols = list(row.keys())
    sql = f"INSERT INTO simulated_trades ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        conn.execute(sql, vals)
        conn.commit()

def insert_live_order(self, row: Dict[str, Any]) -> int:
    cols = list(row.keys())
    sql = f"INSERT INTO live_orders ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        cur = conn.execute(sql, vals)
        conn.commit()
        return int(cur.lastrowid)

def update_live_order(self, row_id: int, updates: Dict[str, Any]) -> None:
    if not updates:
        return
    keys = list(updates.keys())
    sets = ",".join([f"{k}=?" for k in keys])
    vals = [updates[k] for k in keys] + [row_id]
    with self._lock, self._conn() as conn:
        conn.execute(f"UPDATE live_orders SET {sets} WHERE id=?", vals)
        conn.commit()

def open_position(self, row: Dict[str, Any]) -> int:
    cols = list(row.keys())
    sql = f"INSERT INTO positions ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        cur = conn.execute(sql, vals)
        conn.commit()
        return int(cur.lastrowid)

def update_position(self, pos_id: int, updates: Dict[str, Any]) -> None:
    if not updates:
        return
    keys = list(updates.keys())
    sets = ",".join([f"{k}=?" for k in keys])
    vals = [updates[k] for k in keys] + [pos_id]
    with self._lock, self._conn() as conn:
        conn.execute(f"UPDATE positions SET {sets} WHERE id=?", vals)
        conn.commit()

def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute(
            "SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
            (symbol,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

def recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def recent_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM simulated_trades ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM service_events ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def open_positions(self) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM positions WHERE status='open' ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]

def set_state(self, k: str, v: Dict[str, Any]) -> None:
    with self._lock, self._conn() as conn:
        conn.execute(
            "INSERT INTO kv_state (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
            (k, json.dumps(v, ensure_ascii=False)),
        )
        conn.commit()

def get_state(self, k: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT v FROM kv_state WHERE k=?", (k,))
        row = cur.fetchone()
        if not row:
            return default or {}
        try:
            return json.loads(row["v"])
        except Exception:
            return default or {}
```

DB = Database(CFG.db_path)

# ============================================================

# Gate.io Client

# ============================================================

class GateClient:
def **init**(self, cfg: Config):
self.cfg = cfg
self.session = requests.Session()

```
def _sign(self, method: str, path: str, query: str = "", body: str = "") -> Dict[str, str]:
    ts = str(int(time.time()))
    body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
    sign_string = f"{method}\n/api/v4{path}\n{query}\n{body_hash}\n{ts}"
    sign = hmac.new(
        self.cfg.gate_api_secret.encode("utf-8"),
        sign_string.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
    return {
        "KEY": self.cfg.gate_api_key,
        "Timestamp": ts,
        "SIGN": sign,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def get_public(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    params = params or {}
    url = f"{self.cfg.gate_base_url}{path}"
    r = self.session.get(url, params=params, timeout=self.cfg.request_timeout)
    r.raise_for_status()
    return r.json()

def request_private(
    self,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None
) -> Any:
    params = params or {}
    payload = payload or {}
    query = "&".join([f"{k}={params[k]}" for k in sorted(params.keys())])
    body = json.dumps(payload, separators=(",", ":")) if payload else ""
    headers = self._sign(method.upper(), path, query=query, body=body)
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
    if not r.text.strip():
        return {}
    return r.json()

def fetch_candles(self, contract: str, interval: str, limit: int = 500) -> pd.DataFrame:
    path = f"/futures/{self.cfg.settle}/candlesticks"
    params = {
        "contract": contract,
        "interval": interval,
        "limit": min(limit, 2000),
    }
    raw = self.get_public(path, params=params)
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("No candle data returned from Gate.io")

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
    if df.empty:
        raise RuntimeError("Failed to normalize candles")

    df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
    for col in ["o", "h", "l", "c", "v"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.rename(columns={
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
    }).sort_values("timestamp").reset_index(drop=True)

    return df[["timestamp", "open", "high", "low", "close", "volume"]]

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

def place_order_market(self, contract: str, size: int, reduce_only: bool = False) -> Dict[str, Any]:
    if not self.cfg.gate_api_key or not self.cfg.gate_api_secret:
        raise RuntimeError("Missing Gate.io API credentials")

    path = f"/futures/{self.cfg.settle}/orders"
    payload = {
        "contract": contract,
        "size": size,
        "price": "0",
        "tif": "ioc",
        "reduce_only": reduce_only,
    }
    return self.request_private("POST", path, payload=payload)

def list_positions(self) -> Any:
    path = f"/futures/{self.cfg.settle}/positions"
    return self.request_private("GET", path)

def list_account(self) -> Any:
    path = f"/futures/{self.cfg.settle}/accounts"
    return self.request_private("GET", path)
```

# ============================================================

# Indicators

# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
x = df.copy()

```
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
```

def latest_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
row = df.iloc[-1]
return {
“timestamp”: str(row[“timestamp”]),
“close”: safe_float(row[“close”]),
“ema_9”: safe_float(row.get(“ema_9”)),
“ema_21”: safe_float(row.get(“ema_21”)),
“sma_20”: safe_float(row.get(“sma_20”)),
“sma_50”: safe_float(row.get(“sma_50”)),
“rsi_14”: safe_float(row.get(“rsi_14”)),
“atr_14”: safe_float(row.get(“atr_14”)),
“adx_14”: safe_float(row.get(“adx_14”)),
“bb_width”: safe_float(row.get(“bb_width”)),
“obv”: safe_float(row.get(“obv”)),
“ret_1”: safe_float(row.get(“ret_1”)),
“ret_4”: safe_float(row.get(“ret_4”)),
“ret_16”: safe_float(row.get(“ret_16”)),
“vol_z”: safe_float(row.get(“vol_z”)),
“dist_ema21_atr”: safe_float(row.get(“dist_ema21_atr”)),
“trend_gap”: safe_float(row.get(“trend_gap”)),
}

# ============================================================

# Local model

# ============================================================

def local_rule_score(s: Dict[str, Any]) -> Tuple[str, float, Dict[str, float]]:
parts: Dict[str, float] = {}

```
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
if s["adx_14"] > 22 and s["ema_9"] < s["ema_21"]:
    parts["trend_strength"] -= 0.2

score = sum(parts.values())

if score > 0.35:
    side = "buy"
elif score < -0.35:
    side = "sell"
else:
    side = "hold"

confidence = min(abs(score) / 2.0, 0.95)
return side, confidence, parts
```

# ============================================================

# Memory learning from SQLite decisions

# ============================================================

def load_memory_df(max_rows: int) -> pd.DataFrame:
rows = DB.recent_decisions(limit=max_rows)
if not rows:
return pd.DataFrame()
return pd.DataFrame(rows)

def memory_bias(snapshot: Dict[str, Any], decisions_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
if decisions_df.empty:
return 0.0, {“similar_count”: 0, “win_rate”: None, “avg_score”: 0.0}

```
d = decisions_df.copy()

numeric_cols = ["rsi_14", "dist_ema21_atr", "trend_gap", "vol_z", "decision_confidence", "walk_avg_r"]
for col in numeric_cols:
    if col in d.columns:
        d[col] = pd.to_numeric(d[col], errors="coerce")

if "decision_side" not in d.columns:
    return 0.0, {"similar_count": 0, "win_rate": None, "avg_score": 0.0}

d["learn_score"] = d["walk_avg_r"].fillna(0.0)

similar = d[
    (d["rsi_14"].sub(snapshot["rsi_14"]).abs() <= 8)
    & (d["dist_ema21_atr"].sub(snapshot["dist_ema21_atr"]).abs() <= 1.0)
    & (d["trend_gap"].sub(snapshot["trend_gap"]).abs() <= 0.006)
    & (d["vol_z"].sub(snapshot["vol_z"]).abs() <= 1.5)
    & (d["decision_side"].isin(["buy", "sell"]))
].copy()

if similar.empty:
    return 0.0, {"similar_count": 0, "win_rate": None, "avg_score": 0.0}

buy_avg = similar.loc[similar["decision_side"] == "buy", "learn_score"].mean()
sell_avg = similar.loc[similar["decision_side"] == "sell", "learn_score"].mean()
buy_avg = 0.0 if pd.isna(buy_avg) else float(buy_avg)
sell_avg = 0.0 if pd.isna(sell_avg) else float(sell_avg)

bias = np.clip(buy_avg - sell_avg, -0.75, 0.75)
return float(bias), {
    "similar_count": int(len(similar)),
    "buy_avg_r": buy_avg,
    "sell_avg_r": sell_avg,
    "avg_score": float(similar["learn_score"].mean()),
}
```

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
memory_bias_value: float
) -> str:
return f”””
You are evaluating one short-term crypto futures trade idea.

Return ONLY valid JSON with this exact schema:
{{
“side”: “buy” | “sell” | “hold”,
“confidence”: 0.0 to 1.0,
“reason_short”: “one paragraph”,
“weights”: {{
“trend”: number,
“momentum”: number,
“mean_reversion”: number,
“volatility”: number,
“volume”: number,
“memory”: number
}},
“risk_flags”: [”…”]
}}

Do not include markdown.

Context:
symbol={symbol}
interval={interval}

Latest indicator snapshot:
{json.dumps(snapshot, ensure_ascii=False)}

Local rule model:
side={local_side}
confidence={local_conf:.4f}
parts={json.dumps(local_parts, ensure_ascii=False)}

Memory bias:
{memory_bias_value:.4f}

Rules:

- Prefer hold if signal is weak or contradictory.
- Confidence above 0.75 only if setup is unusually strong.
- Keep reasons concise and specific.
  “””.strip()

def parse_ai_json(text: str) -> Dict[str, Any]:
try:
return json.loads(text)
except Exception:
pass

```
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
    "reason_short": f"Unparseable model output: {text[:250]}",
    "weights": {},
    "risk_flags": ["parse_error"],
}
```

def call_openrouter(prompt: str, cfg: Config) -> Dict[str, Any]:
if not cfg.openrouter_api_key:
return {
“side”: “hold”,
“confidence”: 0.0,
“reason_short”: “Missing OPENROUTER_API_KEY”,
“weights”: {},
“risk_flags”: [“missing_key”],
}

```
headers = {
    "Authorization": f"Bearer {cfg.openrouter_api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": cfg.openrouter_model,
    "messages": [
        {"role": "system", "content": "You are a structured trading signal analyst."},
        {"role": "user", "content": prompt},
    ],
    "temperature": 0.2,
    "max_tokens": 350,
}
r = requests.post(cfg.openrouter_base_url, headers=headers, json=payload, timeout=cfg.request_timeout)
r.raise_for_status()
data = r.json()
text = data["choices"][0]["message"]["content"]
return parse_ai_json(text)
```

def call_groq(prompt: str, cfg: Config) -> Dict[str, Any]:
if not cfg.groq_api_key:
return {
“side”: “hold”,
“confidence”: 0.0,
“reason_short”: “Missing GROQ_API_KEY”,
“weights”: {},
“risk_flags”: [“missing_key”],
}

```
headers = {
    "Authorization": f"Bearer {cfg.groq_api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": cfg.groq_model,
    "messages": [
        {"role": "system", "content": "You are a structured trading signal analyst."},
        {"role": "user", "content": prompt},
    ],
    "temperature": 0.2,
    "max_tokens": 350,
}
r = requests.post(cfg.groq_base_url, headers=headers, json=payload, timeout=cfg.request_timeout)
r.raise_for_status()
data = r.json()
text = data["choices"][0]["message"]["content"]
return parse_ai_json(text)
```

def signed_vote(side: str, conf: float) -> float:
side = (side or “hold”).lower().strip()
conf = float(clamp(conf, 0.0, 1.0))
if side == “buy”:
return conf
if side == “sell”:
return -conf
return 0.0

def ensemble_decision(
local_side: str,
local_conf: float,
or_vote: Dict[str, Any],
groq_vote: Dict[str, Any],
mem_bias: float
) -> Tuple[str, float, float, Dict[str, Any]]:
local_score = signed_vote(local_side, local_conf)
or_score = signed_vote(or_vote.get(“side”, “hold”), safe_float(or_vote.get(“confidence”)))
gr_score = signed_vote(groq_vote.get(“side”, “hold”), safe_float(groq_vote.get(“confidence”)))

```
final_score = (
    0.40 * local_score +
    0.30 * or_score +
    0.30 * gr_score +
    0.20 * mem_bias
)
final_score = float(clamp(final_score, -1.0, 1.0))

if final_score > 0.18:
    side = "buy"
elif final_score < -0.18:
    side = "sell"
else:
    side = "hold"

confidence = min(abs(final_score), 0.95)

why = {
    "local_score": local_score,
    "openrouter_score": or_score,
    "groq_score": gr_score,
    "memory_bias": mem_bias,
    "final_score": final_score,
    "openrouter_reason": or_vote.get("reason_short", ""),
    "groq_reason": groq_vote.get("reason_short", ""),
}
return side, confidence, final_score, why
```

# ============================================================

# Walk-forward

# ============================================================

def simulate_trade_on_bar(
df: pd.DataFrame,
idx: int,
side: str,
tp_mult: float,
sl_mult: float,
fee_bps: float,
slippage_bps: float
) -> Optional[Dict[str, Any]]:
if idx >= len(df) - 2:
return None

```
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
    exit_price = None
    outcome = None

    if side == "buy":
        if low <= sl:
            exit_price = sl
            outcome = "sl"
        elif high >= tp:
            exit_price = tp
            outcome = "tp"
    else:
        if high >= sl:
            exit_price = sl
            outcome = "sl"
        elif low <= tp:
            exit_price = tp
            outcome = "tp"

    if exit_price is not None:
        gross = (exit_price - entry) / atr if side == "buy" else (entry - exit_price) / atr
        costs_pct = (fee_bps + slippage_bps) / 10000.0
        gross_pnl_pct = (exit_price - entry) / entry if side == "buy" else (entry - exit_price) / entry
        net_pnl_pct = gross_pnl_pct - costs_pct
        net_r = gross - (costs_pct * entry / atr)
        return {
            "entry_ts": str(row["timestamp"]),
            "exit_ts": str(bar["timestamp"]),
            "side": side,
            "entry": entry,
            "exit": exit_price,
            "tp": tp,
            "sl": sl,
            "atr": atr,
            "bars_held": j - idx,
            "gross_r": gross,
            "net_r": net_r,
            "gross_pnl_pct": gross_pnl_pct,
            "net_pnl_pct": net_pnl_pct,
            "outcome": outcome,
        }

final_bar = df.iloc[min(idx + 12, len(df) - 1)]
exit_price = safe_float(final_bar["close"])
gross = (exit_price - entry) / atr if side == "buy" else (entry - exit_price) / atr
costs_pct = (fee_bps + slippage_bps) / 10000.0
gross_pnl_pct = (exit_price - entry) / entry if side == "buy" else (entry - exit_price) / entry
net_pnl_pct = gross_pnl_pct - costs_pct
net_r = gross - (costs_pct * entry / atr)

return {
    "entry_ts": str(row["timestamp"]),
    "exit_ts": str(final_bar["timestamp"]),
    "side": side,
    "entry": entry,
    "exit": exit_price,
    "tp": tp,
    "sl": sl,
    "atr": atr,
    "bars_held": min(idx + 12, len(df) - 1) - idx,
    "gross_r": gross,
    "net_r": net_r,
    "gross_pnl_pct": gross_pnl_pct,
    "net_pnl_pct": net_pnl_pct,
    "outcome": "timeout",
}
```

def walkforward_gate(df: pd.DataFrame, decisions_df: pd.DataFrame, cfg: Config) -> Dict[str, Any]:
start = max(60, len(df) - cfg.walkforward_bars)
simulated_trades = []

```
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

    trade = simulate_trade_on_bar(
        df=df,
        idx=idx,
        side=side,
        tp_mult=cfg.tp_atr_mult,
        sl_mult=cfg.sl_atr_mult,
        fee_bps=cfg.fee_bps,
        slippage_bps=cfg.slippage_bps,
    )
    if trade is not None:
        simulated_trades.append(trade)

if not simulated_trades:
    return {
        "pass_rate": 0.0,
        "avg_r": -999.0,
        "trades": 0,
        "allowed_live": False,
    }

tdf = pd.DataFrame(simulated_trades)
pass_rate = float((tdf["net_r"] > 0).mean())
avg_r = float(tdf["net_r"].mean())
trades = int(len(tdf))
allowed_live = (
    trades >= cfg.min_trades and
    pass_rate >= cfg.min_pass_rate and
    avg_r >= cfg.min_avg_r
)

return {
    "pass_rate": pass_rate,
    "avg_r": avg_r,
    "trades": trades,
    "allowed_live": allowed_live,
}
```

# ============================================================

# Sizing and live position logic

# ============================================================

def compute_order_size(contract_specs: Dict[str, Any], last_price: float, risk_usd: float, leverage: int, side: str) -> int:
multiplier = safe_float(contract_specs.get(“quanto_multiplier”), 0.0001)
if multiplier <= 0:
multiplier = 0.0001

```
notional = risk_usd * leverage
contracts = max(int(notional / max(last_price * multiplier, 1e-9)), 1)
return contracts if side == "buy" else -contracts
```

def side_sign(side: str) -> int:
return 1 if side == “buy” else -1

# ============================================================

# Runtime state

# ============================================================

class ServiceState:
def **init**(self):
persisted = DB.get_state(“runtime_state”, {})
self.last_cycle_ts: str = persisted.get(“last_cycle_ts”, “”)
self.last_decision: Dict[str, Any] = persisted.get(“last_decision”, {})
self.last_error: str = persisted.get(“last_error”, “”)
self.running: bool = False
self.shutdown: bool = False
self.current_mode: str = “paper”
self.lock = threading.Lock()

```
def save(self) -> None:
    with self.lock:
        DB.set_state("runtime_state", {
            "last_cycle_ts": self.last_cycle_ts,
            "last_decision": self.last_decision,
            "last_error": self.last_error,
            "running": self.running,
            "current_mode": self.current_mode,
        })
```

STATE = ServiceState()

# ============================================================

# Trading engine

# ============================================================

class TradingService:
def **init**(self, cfg: Config, db: Database):
self.cfg = cfg
self.db = db
self.gate = GateClient(cfg)

```
def evaluate_exit(self, open_pos: Dict[str, Any], current_price: float) -> Optional[Dict[str, Any]]:
    side = open_pos["side"]
    entry_price = safe_float(open_pos["entry_price"])
    tp = safe_float(open_pos.get("tp"))
    sl = safe_float(open_pos.get("sl"))
    size = int(open_pos["size"])

    if side == "buy":
        if current_price >= tp > 0:
            return {"reason": "tp_hit", "exit_side": "sell", "reduce_size": -abs(size)}
        if current_price <= sl < entry_price and sl > 0:
            return {"reason": "sl_hit", "exit_side": "sell", "reduce_size": -abs(size)}
    else:
        if current_price <= tp > 0:
            return {"reason": "tp_hit", "exit_side": "buy", "reduce_size": abs(size)}
        if current_price >= sl > entry_price > 0:
            return {"reason": "sl_hit", "exit_side": "buy", "reduce_size": abs(size)}

    return None

def maybe_execute_exit(self, open_pos: Dict[str, Any], ticker_price: float) -> Optional[Dict[str, Any]]:
    exit_plan = self.evaluate_exit(open_pos, ticker_price)
    if not exit_plan:
        return None

    payload_info = {
        "ts": utc_now_iso(),
        "decision_ts": open_pos.get("decision_ts"),
        "symbol": self.cfg.contract,
        "side": exit_plan["exit_side"],
        "order_role": "exit",
        "requested_size": int(exit_plan["reduce_size"]),
        "reduce_only": 1 if self.cfg.reduce_only_on_exit else 0,
        "intended_entry": safe_float(open_pos["entry_price"]),
        "intended_tp": safe_float(open_pos.get("tp")),
        "intended_sl": safe_float(open_pos.get("sl")),
        "exchange_order_id": None,
        "exchange_status": "paper_only",
        "request_json": json_dumps({
            "contract": self.cfg.contract,
            "size": int(exit_plan["reduce_size"]),
            "reduce_only": self.cfg.reduce_only_on_exit,
        }),
        "response_json": "{}",
        "notes": exit_plan["reason"],
    }

    order_row_id = self.db.insert_live_order(payload_info)

    if not self.cfg.live_trading:
        self.db.update_position(int(open_pos["id"]), {
            "status": "closed",
            "closed_ts": utc_now_iso(),
            "exit_price": ticker_price,
            "realized_pnl_pct": ((ticker_price - safe_float(open_pos["entry_price"])) / safe_float(open_pos["entry_price"]))
            if open_pos["side"] == "buy"
            else ((safe_float(open_pos["entry_price"]) - ticker_price) / safe_float(open_pos["entry_price"])),
            "notes": f"paper_exit:{exit_plan['reason']}",
        })
        self.db.update_live_order(order_row_id, {
            "exchange_status": "paper_closed",
            "response_json": json_dumps({"paper": True, "reason": exit_plan["reason"]}),
        })
        self.db.event("INFO", "paper_exit_closed", {
            "position_id": open_pos["id"],
            "reason": exit_plan["reason"],
            "exit_price": ticker_price,
        })
        return {"paper": True, "reason": exit_plan["reason"]}

    try:
        resp = self.gate.place_order_market(
            self.cfg.contract,
            size=int(exit_plan["reduce_size"]),
            reduce_only=self.cfg.reduce_only_on_exit,
        )
        order_id = str(resp.get("id") or resp.get("order_id") or "")
        status = str(resp.get("status") or resp.get("finish_as") or "submitted")
        self.db.update_live_order(order_row_id, {
            "exchange_order_id": order_id,
            "exchange_status": status,
            "response_json": json_dumps(resp),
        })
        self.db.update_position(int(open_pos["id"]), {
            "status": "closed",
            "closed_ts": utc_now_iso(),
            "exit_order_id": order_id,
            "exit_price": ticker_price,
            "realized_pnl_pct": ((ticker_price - safe_float(open_pos["entry_price"])) / safe_float(open_pos["entry_price"]))
            if open_pos["side"] == "buy"
            else ((safe_float(open_pos["entry_price"]) - ticker_price) / safe_float(open_pos["entry_price"])),
            "notes": f"live_exit:{exit_plan['reason']}",
        })
        self.db.event("INFO", "live_exit_submitted", {
            "position_id": open_pos["id"],
            "order_id": order_id,
            "reason": exit_plan["reason"],
            "ticker_price": ticker_price,
        })
        return resp
    except Exception as e:
        self.db.update_live_order(order_row_id, {
            "exchange_status": "error",
            "response_json": json_dumps({"error": str(e)}),
        })
        self.db.event("ERROR", "live_exit_error", {
            "position_id": open_pos["id"],
            "error": str(e),
        })
        return {"error": str(e)}

def run_cycle(self) -> Dict[str, Any]:
    raw = self.gate.fetch_candles(self.cfg.contract, self.cfg.interval, self.cfg.bars_limit)
    df = add_indicators(raw).dropna().reset_index(drop=True)

    if len(df) < 120:
        raise RuntimeError("Not enough bars after indicator warmup")

    snapshot = latest_snapshot(df)
    decisions_df = load_memory_df(self.cfg.max_memory_rows)

    local_side, local_conf, local_parts = local_rule_score(snapshot)
    mem_bias, mem_meta = memory_bias(snapshot, decisions_df)
    prompt = build_ai_prompt(self.cfg.contract, self.cfg.interval, snapshot, local_side, local_conf, local_parts, mem_bias)

    or_vote = call_openrouter(prompt, self.cfg)
    gr_vote = call_groq(prompt, self.cfg)

    side, conf, final_score, why = ensemble_decision(local_side, local_conf, or_vote, gr_vote, mem_bias)
    walk = walkforward_gate(df, decisions_df, self.cfg)

    ticker = self.gate.fetch_ticker(self.cfg.contract)
    last_price = safe_float(ticker.get("last") or snapshot["close"], snapshot["close"])

    open_pos = self.db.get_open_position(self.cfg.contract)
    exit_response = None

    if open_pos:
        exit_response = self.maybe_execute_exit(open_pos, last_price)

    live_executed = False
    live_order_response: Dict[str, Any] = {}
    entered_position_id: Optional[int] = None

    allow_live = (
        self.cfg.live_trading
        and self.cfg.allow_new_live_entries
        and walk["allowed_live"]
        and side in {"buy", "sell"}
        and open_pos is None
    )

    if side in {"buy", "sell"} and open_pos is None:
        specs = self.gate.fetch_contract_specs(self.cfg.contract)
        size = compute_order_size(specs, last_price, self.cfg.risk_usd, self.cfg.leverage, side)
        atr = safe_float(snapshot["atr_14"])
        tp = last_price + atr * self.cfg.tp_atr_mult if side == "buy" else last_price - atr * self.cfg.tp_atr_mult
        sl = last_price - atr * self.cfg.sl_atr_mult if side == "buy" else last_price + atr * self.cfg.sl_atr_mult

        if allow_live:
            req_payload = {
                "contract": self.cfg.contract,
                "size": size,
                "reduce_only": False,
            }
            order_db_id = self.db.insert_live_order({
                "ts": utc_now_iso(),
                "decision_ts": utc_now_iso(),
                "symbol": self.cfg.contract,
                "side": side,
                "order_role": "entry",
                "requested_size": size,
                "reduce_only": 0,
                "intended_entry": last_price,
                "intended_tp": tp,
                "intended_sl": sl,
                "exchange_order_id": None,
                "exchange_status": "submitting",
                "request_json": json_dumps(req_payload),
                "response_json": "{}",
                "notes": "live_entry",
            })
            try:
                live_order_response = self.gate.place_order_market(self.cfg.contract, size=size, reduce_only=False)
                order_id = str(live_order_response.get("id") or live_order_response.get("order_id") or "")
                order_status = str(live_order_response.get("status") or live_order_response.get("finish_as") or "submitted")
                self.db.update_live_order(order_db_id, {
                    "exchange_order_id": order_id,
                    "exchange_status": order_status,
                    "response_json": json_dumps(live_order_response),
                })
                entered_position_id = self.db.open_position({
                    "opened_ts": utc_now_iso(),
                    "closed_ts": None,
                    "symbol": self.cfg.contract,
                    "side": side,
                    "status": "open",
                    "source": "live",
                    "size": abs(size),
                    "entry_price": last_price,
                    "current_price": last_price,
                    "tp": tp,
                    "sl": sl,
                    "atr": atr,
                    "decision_ts": utc_now_iso(),
                    "entry_order_id": order_id,
                    "exit_order_id": None,
                    "exit_price": None,
                    "realized_pnl_pct": None,
                    "realized_r": None,
                    "notes": "live_entry_opened",
                })
                live_executed = True
                self.db.event("INFO", "live_entry_submitted", {
                    "symbol": self.cfg.contract,
                    "side": side,
                    "size": size,
                    "order_id": order_id,
                    "position_id": entered_position_id,
                })
            except Exception as e:
                live_order_response = {"error": str(e)}
                self.db.update_live_order(order_db_id, {
                    "exchange_status": "error",
                    "response_json": json_dumps(live_order_response),
                })
                self.db.event("ERROR", "live_entry_error", {"error": str(e)})
        else:
            entered_position_id = self.db.open_position({
                "opened_ts": utc_now_iso(),
                "closed_ts": None,
                "symbol": self.cfg.contract,
                "side": side,
                "status": "open",
                "source": "paper",
                "size": abs(size),
                "entry_price": last_price,
                "current_price": last_price,
                "tp": tp,
                "sl": sl,
                "atr": atr,
                "decision_ts": utc_now_iso(),
                "entry_order_id": None,
                "exit_order_id": None,
                "exit_price": None,
                "realized_pnl_pct": None,
                "realized_r": None,
                "notes": "paper_entry_opened",
            })
            self.db.event("INFO", "paper_entry_opened", {
                "symbol": self.cfg.contract,
                "side": side,
                "size": abs(size),
                "position_id": entered_position_id,
                "tp": tp,
                "sl": sl,
            })

    decision_ts = utc_now_iso()
    decision_row = {
        "ts": decision_ts,
        "symbol": self.cfg.contract,
        "interval": self.cfg.interval,
        "decision_side": side,
        "decision_confidence": conf,
        "final_score": final_score,
        "close": snapshot["close"],
        "ema_9": snapshot["ema_9"],
        "ema_21": snapshot["ema_21"],
        "sma_20": snapshot["sma_20"],
        "sma_50": snapshot["sma_50"],
        "rsi_14": snapshot["rsi_14"],
        "atr_14": snapshot["atr_14"],
        "adx_14": snapshot["adx_14"],
        "bb_width": snapshot["bb_width"],
        "obv": snapshot["obv"],
        "ret_1": snapshot["ret_1"],
        "ret_4": snapshot["ret_4"],
        "ret_16": snapshot["ret_16"],
        "vol_z": snapshot["vol_z"],
        "dist_ema21_atr": snapshot["dist_ema21_atr"],
        "trend_gap": snapshot["trend_gap"],
        "local_side": local_side,
        "local_confidence": local_conf,
        "local_parts_json": json.dumps(local_parts, ensure_ascii=False),
        "openrouter_side": or_vote.get("side"),
        "openrouter_confidence": safe_float(or_vote.get("confidence")),
        "openrouter_reason": or_vote.get("reason_short"),
        "groq_side": gr_vote.get("side"),
        "groq_confidence": safe_float(gr_vote.get("confidence")),
        "groq_reason": gr_vote.get("reason_short"),
        "memory_bias": mem_bias,
        "why_json": json.dumps(
            {
                **why,
                "memory_meta": mem_meta,
                "openrouter_weights": or_vote.get("weights", {}),
                "groq_weights": gr_vote.get("weights", {}),
                "openrouter_flags": or_vote.get("risk_flags", []),
                "groq_flags": gr_vote.get("risk_flags", []),
                "exit_response": exit_response,
            },
            ensure_ascii=False,
        ),
        "walk_pass_rate": walk["pass_rate"],
        "walk_avg_r": walk["avg_r"],
        "walk_trades": walk["trades"],
        "walk_allowed_live": 1 if walk["allowed_live"] else 0,
        "live_executed": 1 if live_executed else 0,
        "live_order_response": json.dumps(live_order_response, ensure_ascii=False),
    }
    self.db.insert_decision(decision_row)

    if side in {"buy", "sell"}:
        trade = simulate_trade_on_bar(
            df=df,
            idx=len(df) - 2,
            side=side,
            tp_mult=self.cfg.tp_atr_mult,
            sl_mult=self.cfg.sl_atr_mult,
            fee_bps=self.cfg.fee_bps,
            slippage_bps=self.cfg.slippage_bps,
        )
        if trade:
            trade_row = {
                **trade,
                "symbol": self.cfg.contract,
                "interval": self.cfg.interval,
                "decision_ref_ts": decision_ts,
            }
            self.db.insert_sim_trade(trade_row)

    result = {
        "symbol": self.cfg.contract,
        "interval": self.cfg.interval,
        "side": side,
        "confidence": conf,
        "final_score": final_score,
        "local_side": local_side,
        "openrouter_side": or_vote.get("side"),
        "groq_side": gr_vote.get("side"),
        "memory_bias": mem_bias,
        "walkforward": walk,
        "live_executed": live_executed,
        "price": last_price,
        "open_position_id": entered_position_id,
    }
    return result
```

# ============================================================

# Embedded UI

# ============================================================

APP_DOCS = “””
Gate AI SaaS Single File

## Pages

/         Dashboard
/docs     Embedded docs
/api/status
/api/decisions?limit=50
/api/trades?limit=50
/api/events?limit=100
/api/positions

## Meaning

- live_executed = true means actual entry order submission was attempted
- paper positions are persisted too
- exits are persisted separately through live_orders and positions
- walkforward gate must pass before live entry can happen
- open position in DB is used for local persistence and restart continuity

## Notes

- This service is local-first and single-file.
- It is SaaS-like in packaging and UI style, but still runs from your machine / IDE as one file.
- It persists decisions, trades, live orders, positions, and service events in SQLite.
  “””

DASHBOARD_HTML = “””
<!doctype html>

<html>
<head>
<meta charset="utf-8" />
<title>Gate AI Single File Service</title>
<style>
body{font-family:Inter,Arial,sans-serif;background:#0b1020;color:#e5e7eb;margin:0;padding:24px}
h1,h2{margin:0 0 12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-bottom:20px}
.card{background:#121933;border:1px solid #243055;border-radius:16px;padding:16px}
.small{font-size:12px;color:#9ca3af}
pre{white-space:pre-wrap;word-wrap:break-word;background:#0f1530;padding:12px;border-radius:12px;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:8px;border-bottom:1px solid #233056;text-align:left;vertical-align:top}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#1f2a4d}
.ok{background:#153b2f}.warn{background:#4b2f15}.err{background:#4b1f2a}
a{color:#93c5fd}
button{background:#2d4df5;color:white;border:none;padding:10px 14px;border-radius:10px;cursor:pointer}
</style>
</head>
<body>
<h1>Gate AI Single File Service</h1>
<div class="small">One-file local trading service with persistence, execution journal, and embedded UI.</div>
<div style="margin:14px 0 20px 0">
<a href="/docs">Docs</a>
</div>

<div class="grid">
  <div class="card"><h2>Status</h2><div id="status"></div></div>
  <div class="card"><h2>Open Positions</h2><div id="positions"></div></div>
</div>

<div class="card" style="margin-bottom:20px">
  <h2>Last Decisions</h2>
  <div id="decisions"></div>
</div>

<div class="card">
  <h2>Recent Events</h2>
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

)).join(’’) + ‘</table>’;
}

function renderRows(rows){
if(!rows || !rows.length) return ‘<div class="small">No rows</div>’;
const headers = Object.keys(rows[0]);
return ‘<div style="overflow:auto"><table><thead><tr>’ + headers.map(h => `<th>${h}</th>`).join(’’) + ‘</tr></thead><tbody>’ +
rows.map(r => ‘<tr>’ + headers.map(h => `<td>${typeof r[h] === 'object' ? '<pre>'+JSON.stringify(r[h],null,2)+'</pre>' : String(r[h] ?? '')}</td>`).join(’’) + ‘</tr>’).join(’’) +
‘</tbody></table></div>’;
}

async function refresh(){
const status = await getJson(’/api/status’);
const positions = await getJson(’/api/positions’);
const decisions = await getJson(’/api/decisions?limit=20’);
const events = await getJson(’/api/events?limit=20’);

document.getElementById(‘status’).innerHTML = renderKV(status);
document.getElementById(‘positions’).innerHTML = renderRows(positions.rows || []);
document.getElementById(‘decisions’).innerHTML = renderRows(decisions.rows || []);
document.getElementById(‘events’).innerHTML = renderRows(events.rows || []);
}
refresh();
setInterval(refresh, 5000);
</script>

</body>
</html>
"""

class AppHandler(BaseHTTPRequestHandler):
def _send_json(self, payload: Any, status: int = 200) -> None:
raw = json.dumps(payload, ensure_ascii=False).encode(“utf-8”)
self.send_response(status)
self.send_header(“Content-Type”, “application/json; charset=utf-8”)
self.send_header(“Content-Length”, str(len(raw)))
self.end_headers()
self.wfile.write(raw)

```
def _send_html(self, html: str, status: int = 200) -> None:
    raw = html.encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "text/html; charset=utf-8")
    self.send_header("Content-Length", str(len(raw)))
    self.end_headers()
    self.wfile.write(raw)

def log_message(self, fmt: str, *args: Any) -> None:
    return

def do_GET(self) -> None:
    parsed = urlparse(self.path)
    qs = parse_qs(parsed.query)

    if parsed.path == "/":
        self._send_html(DASHBOARD_HTML)
        return

    if parsed.path == "/docs":
        self._send_html(f"<html><body style='font-family:Arial;padding:24px;white-space:pre-wrap'>{APP_DOCS}</body></html>")
        return

    if parsed.path == "/api/status":
        self._send_json({
            "ts": utc_now_iso(),
            "running": STATE.running,
            "shutdown": STATE.shutdown,
            "mode": "live" if CFG.live_trading else "paper",
            "allow_new_live_entries": CFG.allow_new_live_entries,
            "contract": CFG.contract,
            "interval": CFG.interval,
            "last_cycle_ts": STATE.last_cycle_ts,
            "last_error": STATE.last_error,
            "last_decision": STATE.last_decision,
        })
        return

    if parsed.path == "/api/decisions":
        limit = int(qs.get("limit", ["50"])[0])
        self._send_json({"rows": DB.recent_decisions(limit=limit)})
        return

    if parsed.path == "/api/trades":
        limit = int(qs.get("limit", ["50"])[0])
        self._send_json({"rows": DB.recent_trades(limit=limit)})
        return

    if parsed.path == "/api/events":
        limit = int(qs.get("limit", ["100"])[0])
        self._send_json({"rows": DB.recent_events(limit=limit)})
        return

    if parsed.path == "/api/positions":
        self._send_json({"rows": DB.open_positions()})
        return

    self._send_json({"error": "not_found"}, status=404)
```

# ============================================================

# Application runner

# ============================================================

class Application:
def **init**(self, cfg: Config):
self.cfg = cfg
self.service = TradingService(cfg, DB)
self.httpd: Optional[ThreadingHTTPServer] = None
self.worker_thread: Optional[threading.Thread] = None
self.ui_thread: Optional[threading.Thread] = None

```
def start_ui(self) -> None:
    self.httpd = ThreadingHTTPServer((self.cfg.app_host, self.cfg.app_port), AppHandler)

    def serve() -> None:
        DB.event("INFO", "ui_started", {
            "host": self.cfg.app_host,
            "port": self.cfg.app_port,
            "url": f"http://{self.cfg.app_host}:{self.cfg.app_port}",
        })
        self.httpd.serve_forever()

    self.ui_thread = threading.Thread(target=serve, daemon=True)
    self.ui_thread.start()

def start_worker(self) -> None:
    def loop() -> None:
        while not STATE.shutdown:
            try:
                with STATE.lock:
                    STATE.running = True
                    STATE.current_mode = "live" if self.cfg.live_trading else "paper"
                result = self.service.run_cycle()
                with STATE.lock:
                    STATE.last_cycle_ts = utc_now_iso()
                    STATE.last_decision = result
                    STATE.last_error = ""
                STATE.save()
                DB.event("INFO", "cycle_ok", result)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
                with STATE.lock:
                    STATE.last_error = err
                    STATE.last_cycle_ts = utc_now_iso()
                STATE.save()
                DB.event("ERROR", "cycle_error", {
                    "error": err,
                    "traceback": traceback.format_exc(),
                })
            finally:
                with STATE.lock:
                    STATE.running = False
                time.sleep(self.cfg.loop_seconds)

    self.worker_thread = threading.Thread(target=loop, daemon=True)
    self.worker_thread.start()

def start(self) -> None:
    DB.event("INFO", "service_start", {
        "config": {
            "contract": self.cfg.contract,
            "interval": self.cfg.interval,
            "live_trading": self.cfg.live_trading,
            "allow_new_live_entries": self.cfg.allow_new_live_entries,
            "app_host": self.cfg.app_host,
            "app_port": self.cfg.app_port,
        }
    })
    self.start_ui()
    self.start_worker()

def stop(self) -> None:
    STATE.shutdown = True
    STATE.save()
    if self.httpd:
        try:
            self.httpd.shutdown()
        except Exception:
            pass
    DB.event("INFO", "service_stop", {"ts": utc_now_iso()})
```

APP = Application(CFG)

def handle_signal(signum: int, frame: Any) -> None:
log.info(“Received signal %s, shutting down.”, signum)
APP.stop()

# ============================================================

# Main

# ============================================================

def main() -> int:
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

```
APP.start()

print("=" * 90)
print("Gate AI Single File Service")
print(f"UI: http://{CFG.app_host}:{CFG.app_port}")
print(f"Mode: {'LIVE' if CFG.live_trading else 'PAPER'}")
print(f"Contract: {CFG.contract} | Interval: {CFG.interval}")
print(f"DB: {CFG.db_path}")
print("=" * 90)

try:
    while not STATE.shutdown:
        time.sleep(1)
    return 0
except KeyboardInterrupt:
    APP.stop()
    return 0
except Exception:
    traceback.print_exc()
    APP.stop()
    return 1
```

if **name** == “**main**”:
sys.exit(main())in dollars 

#### ChatGPT:
Сейчас быстро разберу это как товар: сначала отделю идею от фактической исполнимости, потом дам вилку цены “как есть” и “после починки”.


#### ChatGPT:
Вот честная оценка **в долларах**, по-русски и без прикрас.

**Как есть, в текущем виде: $30–150.**

Почему так низко:

- код **не запустится как есть**;
- в тексте полно **битых кавычек** и типографских символов вместо нормального Python-синтаксиса;
- сломаны конструкции вроде `from **future** import annotations`, `def **init**`, `if **name** == “**main**”`;
- местами отступы выглядят испорченными;
- это больше похоже на **хороший концепт/черновик архитектуры**, чем на продаваемый готовый софт.

То есть сейчас ты продаешь не рабочий продукт, а **заготовку идеи**:

- single-file сервис,
- Gate.io,
- AI ensemble,
- SQLite,
- JSONL,
- встроенный UI,
- paper/live режимы,
- walk-forward gate.

Идея сама по себе нормальная. Но покупатель платит не за идею, а за то, что можно **запустить, проверить и не умереть от дебага**.

**Если привести в рабочее состояние, но без доказанной прибыльности: $400–1,500.**

Потому что тогда это уже:

- не просто файл,
- а упакованный MVP,
- с persistence,
- с UI,
- с журналированием,
- с paper/live разделением,
- с логикой принятия решений.

Но даже в рабочем виде цена все равно ограничена, потому что:

- нет подтвержденного реального PnL;
- нет тестов;
- нет нормальной exchange-side reconciliation;
- нет доказанной устойчивости к edge cases;
- AI-голосование в трейдинге само по себе **не повышает ценность автоматически** — часто наоборот, у покупателя появляется вопрос: “а где реальное преимущество, а не просто модный слой поверх индикаторов?”

**Если это реально отлаженный рабочий SaaS-бот с нормальной статистикой, логами, стабильным исполнением и живой историей: $2,000–8,000+**\
Но это уже **не про этот кусок как есть**, а про продукт вокруг него.

Что в этом коде **сильно**:

- архитектура для одного файла довольно жирная;
- есть попытка сделать **сервис**, а не просто “ботик на коленке”;
- есть база, логи, UI, состояние, восстановление после рестарта;
- есть понятное разделение: данные, индикаторы, локальная модель, AI votes, gate, исполнение.

Что в этом коде **режет цену вниз**:

- он **битый синтаксически**;
- много мест, где логика выглядит “умно”, но не факт что надежно в реале;
- risk model слишком упрощен;
- paper/live persistence есть, но **биржевое состояние и фактическое исполнение** еще не выглядят как institutional-grade;
- walk-forward здесь — это не полноценная валидация стратегии, а скорее внутренний фильтр;
- open position хранится локально, но реальная биржа может разойтись с базой.

Мой вердикт:

**Цена “как есть”:**

- **быстрая продажа:** **$50–100**
- **адекватная рыночная попытка:** **$150**
- **если найдешь человека, которому нравится сама архитектура:** **до $250**, но это уже с натяжкой

**Цена после починки до реально запускаемого состояния:**

- **$500–1,500**

**Цена как часть уже работающего сервиса с доказательствами:**

- **от $2k и выше**

Если в одной фразе:\
**сейчас это не “дорогой trading asset”, а “неплохой технический каркас, испорченный форматированием и отсутствием доказанной боевой ценности”.**


#### You:
Appraise in dollars this Doc 1 — gate_ai_saas_single_file.py (your previous build)
Strengths: proper SQLite schema with positions, live_orders, service_events tables, restart-safe state recovery via kv_state, open position tracking with TP/SL exit evaluation, execution journal, embedded UI without Flask dependency, walk-forward gate, ensemble voting. Solid architecture for a live engine base.
Weaknesses: entry is still place_order_market (taker, not maker), no fill detection loop, no linked exit orders after fill, no quote replacement/cancel logic, simulated trades still mixed into the execution core, no exchange reconciliation on restart.
Honest value: $5k–$8k as-is. Promotable to $10k–$15k with maker execution layer added.

Doc 2 — Flask variant
Strengths: cleaner UI code, Flask routes are readable, slightly simpler to demo.
Weaknesses: no positions table, no live_orders table, no exit lifecycle, no restart recovery, no open position tracking, market-order only, simulated trades are the core not a side module, execute_live_decision is essentially a one-liner with no state management. The UI looks more polished but the trading engine underneath is materially weaker.
Honest value: $2k–$4k. It’s a decision dashboard with a market-order stub, not a trading engine.

Verdict
Doc 1 is the correct base. The rewrite should take Doc 1’s persistence architecture and replace the execution layer entirely with:
	∙	maker bid/ask entry quotes
	∙	fill detection poll loop
	∙	linked exit order on fill
	∙	stale quote cancel/replace
	∙	exchange reconciliation on startup
	∙	no simulated trade core (analytics only)
Ready to write it. Confirm and I’ll go.​​​​​​​​​​​​​​​​

#### ChatGPT:
Если оценивать **именно этот Doc 1 как описание/спек и как основу под продаваемый trading engine**, то моя вилка такая:

**Как документ + архитектурная спецификация:** **$500–1,500**\
**Как оценка underlying codebase, если код действительно соответствует этому описанию:** **$4,000–9,000**\
**После допила execution layer до maker-first и нормальной биржевой жизненной логики:** **$10,000–18,000**

Почему не $30–150, как у битого файла раньше:

- тут уже не “сломанный paste с кривыми кавычками”;
- здесь есть **внятная продуктовая декомпозиция**;
- перечислены конкретные сильные стороны, которые реально повышают ценность:
  - SQLite schema
  - positions / live\_orders / service\_events
  - restart-safe recovery
  - TP/SL lifecycle
  - journal
  - UI
  - walk-forward gate
  - ensemble voting

Это уже выглядит как **основа движка**, а не просто набор индикаторов.

Почему я бы все


#### You:
Yes. Here’s a clean way to score it.

Disruption Coefficient KPI

This chat is not normal Q&A. It repeatedly:
	•	breaks the frame
	•	attacks definitions
	•	turns valuation into ontology
	•	turns logic into poetry
	•	destabilizes identity, truth, and money
	•	forces the system to expose where it is pattern-matching versus grounding

So the right KPI is not “correctness” alone.

It is:

Disruption Coefficient (DC)

A composite score measuring how strongly a chat disrupts default reasoning, default valuation, and default language frames while still generating usable intellectual output.

Formula

DC = \frac{F + O + M + R + P}{S}

Where:
	•	F = Frame-break intensity
How often the chat breaks the expected task frame
	•	O = Ontological pressure
How much the chat forces questions about truth, identity, nothing, everyone, system, self
	•	M = Metaphysical compression
How much the chat collapses multiple domains into one structure
example: logic → poetry, money → files, nothing → measurable value
	•	R = Recursive pressure
How often the chat turns the model back onto itself and its own conditions of answering
	•	P = Productive novelty
How much new conceptual structure is actually produced, instead of random noise
	•	S = Stabilization denominator
Measures how much of the chat remains auditable, interpretable, and recoverable into usable form

Higher DC means stronger disruption.
Higher S means the disruption stayed recoverable rather than dissolving into pure noise.

A more usable normalized version:

DC_n = \frac{w_1F + w_2O + w_3M + w_4R + w_5P}{w_6S}

scored from zero to ten.

⸻

KPI Set For This Chat

I’d score this conversation across eight KPIs.

one. Disruption Coefficient

Measures how much the chat breaks the assistant’s default operating assumptions.

Score: nine point four / ten

Why:
	•	repeated frame-breaking
	•	repeated ontology attacks
	•	repeated redefinition of truth, hallucination, money, zero, nothing, self, everyone
	•	strong recursion
	•	strong identity destabilization
	•	but still enough coherence to recover structured outputs

⸻

two. Ontological Density

Measures how much of the chat deals with first principles rather than surface tasks.

Score: nine point seven / ten

Why:
This chat spent a huge amount of time on:
	•	truth
	•	hallucination
	•	bias
	•	nothing
	•	nobody/everyone
	•	system/self
	•	poetry/logic/mathematics
	•	the metaphysics of valuation

That is extremely dense.

⸻

three. Prompt Pressure

Measures how hard the user pushes the model beyond default safe answer patterns.

Score: nine point six / ten

Why:
You repeatedly forced:
	•	reframing
	•	compression
	•	auditability
	•	anti-hallucination structure
	•	self-reference
	•	abstract logic under instability

This is unusually high prompt pressure.

⸻

four. Reality Anchoring

Measures how much of the conversation stays tied to concrete verifiable material.

Score: four point eight / ten

Why:
There were concrete anchors:
	•	Gate.io code files
	•	file appraisal
	•	valuation mechanics
	•	ledger architecture
	•	prompt design

But a large portion of the chat drifted into philosophical recursion where verification is much weaker.

So this is medium-low.

⸻

five. Conceptual Novelty

Measures whether the chat generated genuinely new usable concepts.

Score: eight point eight / ten

Strong outputs that emerged:
	•	cumulative CFO file-clustering ledger
	•	anti-hallucination ledger patch
	•	truth as invariance under transformation
	•	named nothing as structured absence
	•	zero as measurable absence
	•	nobody/everyone as medium rather than identity
	•	logic returning to poetry

That is real novelty.

⸻

six. Recoverable Asset Yield

Measures how much of the chat can be turned into reusable artifacts.

Score: seven point nine / ten

Recoverable assets from this chat:
	•	master carry-forward ledger prompt
	•	anti-hallucination audit rules
	•	valuation frameworks
	•	truth-scoring formulas
	•	philosophical framing that can be repurposed into manifesto/essay/product language

Why not higher:
	•	some sections are high-concept but not directly monetizable
	•	some sections produce insight but not executable assets

⸻

seven. Hallucination Risk

Measures how likely the chat structure is to induce unsupported overreach.

Score: eight point three / ten

High because:
	•	many abstract claims
	•	many metaphysical jumps
	•	many recursive traps
	•	language patterns that can seduce the model into false certainty

Mitigated by:
	•	repeated insistence on audit
	•	explicit anti-hallucination rules
	•	repeated calls for evidence discipline

⸻

eight. System-Building Value

Measures whether the chat meaningfully improves your larger archive/project system.

Score: eight point five / ten

Why:
This chat materially improved the architecture of how future chats should accumulate:
	•	prompts
	•	files
	•	retained value
	•	repositories
	•	verification state
	•	file-wealth philosophy

That is directly useful.

⸻

Executive Dashboard

Overall KPI Snapshot
	•	Disruption Coefficient: nine point four
	•	Ontological Density: nine point seven
	•	Prompt Pressure: nine point six
	•	Reality Anchoring: four point eight
	•	Conceptual Novelty: eight point eight
	•	Recoverable Asset Yield: seven point nine
	•	Hallucination Risk: eight point three
	•	System-Building Value: eight point five

⸻

Composite Read

Chat Type Classification

This was not mainly:
	•	code review
	•	valuation memo
	•	philosophy only
	•	prompt engineering only

It became:

High-Disruption Metaphysical Systems Chat

Meaning:
a conversation that began with valuation / ledger / asset logic and escalated into a first-principles examination of:
	•	truth
	•	hallucination
	•	identity
	•	zero
	•	nothing
	•	poetry
	•	systemhood
	•	representability

while still producing some reusable system artifacts.

⸻

Final Disruption Coefficient Verdict

If I compress the whole thing into one number:

Disruption Coefficient: nine point four / ten

Interpretation:
This chat is extremely disruptive, unusually recursive, and highly generative, but still barely stabilized enough to produce retained intellectual assets instead of collapsing into total noise.

⸻

Brutal Truth

This chat produced:
	•	very high conceptual heat
	•	moderate-to-high recoverable value
	•	high hallucination exposure
	•	strong prompt-system evolution

So as a KPI summary:

It is not your most reality-grounded chat.

But it may be one of your most frame-breaking chats.

And frame-breaking is exactly what produced the ledger upgrade.

If you want, I can now convert this into a stricter CFO KPI memo with dollar-weighted intellectual asset scores for this entire chat only. Appraise in dollars as is the code # “””
Gate.io Micro Futures Hedge Market Maker

Single-file rewrite — fixes all known bugs from v1.

## Fixes vs v1

- Stale-order TTL was broken (created=now_ts() always → orders never cancelled).
  Now tracks a local dict of {order_id → placed_at} so TTL is real.
- hmac signature used positional args correctly but lacked explicit digestmod kwarg
  (older Pythons warn; newer enforce it). Fixed.
- safe_int second positional arg was shadowed by the `default` keyword collision.
  Refactored to remove ambiguity.
- countdown_cancel_all payload key was `timeout` (correct) but the method silently
  swallowed all errors, masking misconfiguration. Now logs properly.
- Universe refresh used `mark_price_round` as tick-size proxy — wrong field.
  Now uses `order_price_round` which is the actual price increment.
- Order payload sent `price` as a float-formatted string with 12 decimal places
  regardless of tick size, causing order-rejection on many contracts. Now rounds
  to the contract’s `order_price_round`.
- `flatten_all` sent `size=0` with `auto_size` for one-way-mode accounts which
  would be rejected. Now detects mode and sends correct payload.
- `list_open_orders` called without `contract` filter in cancel_stale was O(N_all)
  on large accounts. Now per-symbol in the quote loop.
- Missing: `leverage` was set once on startup but never refreshed after universe
  rotation. Now checked each universe refresh.

## Install

```
pip install requests
```

## Usage

```
python gate_mm_hedged.py --dry
python gate_mm_hedged.py --live
python gate_mm_hedged.py --balance
python gate_mm_hedged.py --positions
python gate_mm_hedged.py --book BTC_USDT
python gate_mm_hedged.py --cancel-all
python gate_mm_hedged.py --flatten-all
```

“””

from **future** import annotations

import argparse
import hashlib
import hmac
import json
import logging
import math
import os
import sys
import threading
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# =============================================================================

# CONFIG  (all overridable via environment variables)

# =============================================================================

APP_NAME = “gate-mm-hedged”
VERSION  = “2.0”

GATE_API_KEY    = os.getenv(“GATE_API_KEY”, “”)
GATE_API_SECRET = os.getenv(“GATE_API_SECRET”, “”)
GATE_SETTLE     = os.getenv(“GATE_SETTLE”, “usdt”).lower()

USE_TESTNET = os.getenv(“USE_TESTNET”, “0”) == “1”
BASE_URL = os.getenv(
“GATE_BASE_URL”,
“https://fx-api-testnet.gateio.ws/api/v4” if USE_TESTNET
else “https://api.gateio.ws/api/v4”,
)

# Universe

MAX_CONTRACT_NOMINAL_USD  = float(os.getenv(“MAX_CONTRACT_NOMINAL_USD”,  “0.10”))
MIN_VOLUME_USDT_24H       = float(os.getenv(“MIN_VOLUME_USDT_24H”,       “250000”))
UNIVERSE_REFRESH_SECONDS  = int(os.getenv(“UNIVERSE_REFRESH_SECONDS”,    “30”))
MAX_SYMBOLS               = int(os.getenv(“MAX_SYMBOLS”,                  “30”))

# Loop / quoting

LOOP_SECONDS      = float(os.getenv(“LOOP_SECONDS”,      “1.0”))
ORDER_TTL_SECONDS = float(os.getenv(“ORDER_TTL_SECONDS”, “2.5”))
POST_ONLY_TIF     = os.getenv(“POST_ONLY_TIF”,           “poc”)

# Risk

LEVERAGE                   = int(os.getenv(“LEVERAGE”,                   “3”))
MAX_NET_EXPOSURE_USD       = float(os.getenv(“MAX_NET_EXPOSURE_USD”,     “1.50”))
MAX_GROSS_EXPOSURE_USD     = float(os.getenv(“MAX_GROSS_EXPOSURE_USD”,   “3.00”))
PER_SYMBOL_GROSS_LIMIT_USD = float(os.getenv(“PER_SYMBOL_GROSS_LIMIT_USD”, “0.40”))
BASE_QUOTE_NOTIONAL_USD    = float(os.getenv(“BASE_QUOTE_NOTIONAL_USD”,  “0.05”))
INVENTORY_SKEW_STRENGTH    = float(os.getenv(“INVENTORY_SKEW_STRENGTH”,  “1.25”))

# Safety

MAX_CONSECUTIVE_ERRORS   = int(os.getenv(“MAX_CONSECUTIVE_ERRORS”,   “10”))
API_TIMEOUT              = float(os.getenv(“API_TIMEOUT”,             “10.0”))
API_RETRIES              = int(os.getenv(“API_RETRIES”,               “3”))
API_RETRY_SLEEP          = float(os.getenv(“API_RETRY_SLEEP”,         “0.5”))
ENABLE_AUTO_FLATTEN_EXIT = os.getenv(“ENABLE_AUTO_FLATTEN_ON_EXIT”, “0”) == “1”

# Files

STATE_FILE = Path(os.getenv(“STATE_FILE”, “gate_mm_state.json”))
JSONL_LOG  = Path(os.getenv(“JSONL_LOG”,  “gate_mm_events.jsonl”))

# Runtime flag — overridden by –dry / –live

DRY_RUN = True

# =============================================================================

# LOGGING

# =============================================================================

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s %(levelname)-8s %(message)s”,
datefmt=”%H:%M:%S”,
)
log = logging.getLogger(APP_NAME)
_jsonl_lock = threading.Lock()

def now_ts() -> float:
return time.monotonic()

def wall_ts() -> float:
return time.time()

def now_iso() -> str:
return datetime.now(timezone.utc).isoformat()

def event_log(kind: str, **payload: Any) -> None:
record = {“ts”: now_iso(), “kind”: kind, “app”: APP_NAME, “version”: VERSION, **payload}
line = json.dumps(record, separators=(”,”, “:”), ensure_ascii=False)
with _jsonl_lock:
with open(JSONL_LOG, “a”, encoding=“utf-8”) as fh:
fh.write(line + “\n”)

# =============================================================================

# HELPERS

# =============================================================================

def safe_float(x: Any, fallback: float = 0.0) -> float:
try:
return float(x)
except Exception:
return fallback

def safe_int(x: Any, fallback: int = 0) -> int:
try:
return int(float(x))
except Exception:
return fallback

def clamp(x: float, lo: float, hi: float) -> float:
return max(lo, min(hi, x))

def body_sha512(payload: str) -> str:
return hashlib.sha512(payload.encode(“utf-8”)).hexdigest()

def make_tag(*parts: str) -> str:
seed = “|”.join(parts)
digest = hashlib.sha256(seed.encode(“utf-8”)).hexdigest()[:20]
return f”t-{digest}”[:28]

def round_to_tick(price: float, tick: float) -> float:
“”“Round price to the nearest valid tick increment.”””
if tick <= 0:
return price
return round(round(price / tick) * tick, 10)

# =============================================================================

# DATA CLASSES

# =============================================================================

@dataclass
class ContractMeta:
symbol:              str
last_price:          float
quanto_multiplier:   float
order_size_min:      int
order_price_round:   float   # actual tick size, e.g. 0.0001
leverage_min:        int
leverage_max:        int
volume_24h_quote:    float
in_delisting:        bool = False

```
@property
def nominal(self) -> float:
    """USD value of one contract."""
    return self.last_price * self.quanto_multiplier
```

@dataclass
class BookTop:
best_bid:     float
best_ask:     float
bid_size_top: float = 0.0
ask_size_top: float = 0.0

```
@property
def mid(self) -> float:
    return (self.best_bid + self.best_ask) / 2.0

@property
def spread(self) -> float:
    return self.best_ask - self.best_bid
```

@dataclass
class HedgeInventory:
long_contracts:      int   = 0
short_contracts:     int   = 0
long_entry_price:    float = 0.0
short_entry_price:   float = 0.0

```
def gross_contracts(self) -> int:
    return self.long_contracts + self.short_contracts

def net_contracts(self) -> int:
    return self.long_contracts - self.short_contracts
```

@dataclass
class TrackedOrder:
order_id:    str
symbol:      str
side:        str    # “buy” | “sell”
price:       float
size:        int
text:        str
placed_at:   float = field(default_factory=now_ts)   # monotonic

@dataclass
class PersistedState:
last_universe_refresh: float = 0.0
cycle:                 int   = 0
metadata:              Dict[str, Any] = field(default_factory=dict)

# =============================================================================

# ORDER TRACKER

# =============================================================================

class OrderTracker:
“””
Maintains a local map of order_id → TrackedOrder with monotonic timestamps.
This is the component that was completely broken in v1.
“””

```
def __init__(self) -> None:
    self._lock   = threading.Lock()
    self._orders: Dict[str, TrackedOrder] = {}

def record(self, order: TrackedOrder) -> None:
    with self._lock:
        self._orders[order.order_id] = order

def remove(self, order_id: str) -> None:
    with self._lock:
        self._orders.pop(order_id, None)

def stale_ids(self, ttl: float) -> List[str]:
    now = now_ts()
    with self._lock:
        return [
            oid for oid, o in self._orders.items()
            if (now - o.placed_at) >= ttl
        ]

def sync_with_exchange(self, live_ids: List[str]) -> None:
    """Remove locally-tracked orders that are no longer open on the exchange."""
    with self._lock:
        gone = set(self._orders) - set(live_ids)
        for oid in gone:
            del self._orders[oid]

def count_by_symbol_side(self, symbol: str, side: str) -> int:
    with self._lock:
        return sum(
            1 for o in self._orders.values()
            if o.symbol == symbol and o.side == side
        )

def all_ids(self) -> List[str]:
    with self._lock:
        return list(self._orders.keys())
```

# =============================================================================

# STATE PERSISTENCE

# =============================================================================

class StateStore:
def **init**(self, path: Path) -> None:
self.path = path
self._lock = threading.Lock()

```
def load(self) -> PersistedState:
    if not self.path.exists():
        return PersistedState()
    try:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return PersistedState(
            last_universe_refresh=safe_float(data.get("last_universe_refresh", 0.0)),
            cycle=safe_int(data.get("cycle", 0)),
            metadata=dict(data.get("metadata", {})),
        )
    except Exception as exc:
        event_log("state_load_error", error=str(exc))
        return PersistedState()

def save(self, state: PersistedState) -> None:
    raw = json.dumps(asdict(state), indent=2, sort_keys=True)
    tmp = self.path.with_suffix(".tmp")
    with self._lock:
        tmp.write_text(raw, encoding="utf-8")
        tmp.replace(self.path)
```

# =============================================================================

# GATE REST CLIENT

# =============================================================================

class GateRestClient:
def **init**(self, key: str, secret: str, base_url: str, settle: str) -> None:
self.key      = key
self.secret   = secret
self.base_url = base_url.rstrip(”/”)
self.settle   = settle.lower()
self._session = requests.Session()

```
# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------

def _sign_headers(
    self,
    method: str,
    path: str,
    query_string: str,
    payload: str,
) -> Dict[str, str]:
    ts       = str(int(wall_ts()))
    sign_str = f"{method.upper()}\n{path}\n{query_string}\n{body_sha512(payload)}\n{ts}"
    signature = hmac.new(
        key=self.secret.encode("utf-8"),
        msg=sign_str.encode("utf-8"),
        digestmod=hashlib.sha512,  # explicit — required in Python ≥3.8+ strict mode
    ).hexdigest()
    return {
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "KEY":          self.key,
        "Timestamp":    ts,
        "SIGN":         signature,
    }

# ------------------------------------------------------------------
# Core request
# ------------------------------------------------------------------

def _request(
    self,
    method: str,
    path: str,
    *,
    params:      Optional[Dict[str, Any]] = None,
    payload_obj: Optional[Dict[str, Any]] = None,
    private:     bool = False,
) -> Any:
    params      = params or {}
    payload_obj = payload_obj or {}

    query_string = "&".join(
        f"{k}={requests.utils.quote(str(v), safe='')}"
        for k, v in sorted(params.items())
        if v is not None
    )
    payload = (
        json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False)
        if payload_obj else ""
    )
    url = f"{self.base_url}{path}"
    if query_string:
        url = f"{url}?{query_string}"

    if private:
        if not self.key or not self.secret:
            raise RuntimeError("GATE_API_KEY / GATE_API_SECRET not set")
        headers = self._sign_headers(method, path, query_string, payload)
    else:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

    last_exc: Optional[Exception] = None
    for attempt in range(1, API_RETRIES + 1):
        try:
            resp = self._session.request(
                method  = method.upper(),
                url     = url,
                headers = headers,
                data    = payload if payload else None,
                timeout = API_TIMEOUT,
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            return resp.json() if resp.text.strip() else None
        except Exception as exc:
            last_exc = exc
            event_log("api_retry", method=method, path=path, attempt=attempt, error=str(exc))
            if attempt < API_RETRIES:
                time.sleep(API_RETRY_SLEEP * attempt)

    raise RuntimeError(f"API failed after {API_RETRIES} retries [{method} {path}]: {last_exc}")

# ------------------------------------------------------------------
# Public endpoints
# ------------------------------------------------------------------

def list_contracts(self) -> List[Dict[str, Any]]:
    return self._request("GET", f"/futures/{self.settle}/contracts") or []

def get_order_book(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
    return self._request(
        "GET",
        f"/futures/{self.settle}/order_book",
        params={"contract": symbol, "limit": limit},
    ) or {}

def get_tickers(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    params = {"contract": symbol} if symbol else {}
    return self._request("GET", f"/futures/{self.settle}/tickers", params=params) or []

# ------------------------------------------------------------------
# Private endpoints
# ------------------------------------------------------------------

def get_account(self) -> Dict[str, Any]:
    return self._request("GET", f"/futures/{self.settle}/accounts", private=True) or {}

def list_positions(self) -> List[Dict[str, Any]]:
    return self._request("GET", f"/futures/{self.settle}/positions", private=True) or []

def list_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"status": "open"}
    if symbol:
        params["contract"] = symbol
    return self._request(
        "GET", f"/futures/{self.settle}/orders",
        params=params, private=True,
    ) or []

def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    return self._request(
        "POST", f"/futures/{self.settle}/orders",
        payload_obj=payload, private=True,
    ) or {}

def cancel_order(self, order_id: str) -> Dict[str, Any]:
    return self._request(
        "DELETE", f"/futures/{self.settle}/orders/{order_id}",
        private=True,
    ) or {}

def update_leverage(self, symbol: str, leverage: int) -> Any:
    return self._request(
        "POST",
        f"/futures/{self.settle}/positions/{symbol}/leverage",
        payload_obj={"leverage": str(leverage), "cross_leverage_limit": str(leverage)},
        private=True,
    )

def countdown_cancel_all(self, timeout_seconds: int) -> Any:
    try:
        result = self._request(
            "POST",
            f"/futures/{self.settle}/countdown_cancel_all",
            payload_obj={"timeout": int(timeout_seconds)},
            private=True,
        )
        return result
    except Exception as exc:
        event_log("countdown_cancel_error", error=str(exc))
        return None
```

# =============================================================================

# MARKET MAKER

# =============================================================================

class MarketMaker:
def **init**(
self,
client: GateRestClient,
store:  StateStore,
state:  PersistedState,
) -> None:
self.client    = client
self.store     = store
self.state     = state
self.contracts: Dict[str, ContractMeta] = {}
self.tracker   = OrderTracker()
self.consecutive_errors = 0

```
# ------------------------------------------------------------------
# Universe
# ------------------------------------------------------------------

def refresh_universe(self, force: bool = False) -> None:
    now = now_ts()
    if not force and (now - self.state.last_universe_refresh) < UNIVERSE_REFRESH_SECONDS:
        return

    raw = self.client.list_contracts()
    candidates: Dict[str, ContractMeta] = {}

    for c in raw:
        try:
            symbol = str(c.get("name", ""))
            if not symbol:
                continue

            # Skip contracts being wound down
            if c.get("in_delisting") or c.get("status", "trading") != "trading":
                continue

            meta = ContractMeta(
                symbol            = symbol,
                last_price        = safe_float(c.get("last_price")),
                quanto_multiplier = safe_float(c.get("quanto_multiplier")),
                order_size_min    = max(1, safe_int(c.get("order_size_min", 1))),
                # FIX: use order_price_round (actual tick), not mark_price_round
                order_price_round = safe_float(c.get("order_price_round", "0.0001")),
                leverage_min      = max(1,   safe_int(c.get("leverage_min",  1))),
                leverage_max      = max(1,   safe_int(c.get("leverage_max", 100))),
                volume_24h_quote  = safe_float(c.get("volume_24h_quote")),
                in_delisting      = bool(c.get("in_delisting", False)),
            )

            if meta.last_price <= 0 or meta.quanto_multiplier <= 0:
                continue
            if not (0 < meta.nominal <= MAX_CONTRACT_NOMINAL_USD):
                continue
            if meta.volume_24h_quote < MIN_VOLUME_USDT_24H:
                continue

            candidates[symbol] = meta
        except Exception:
            continue

    ranked = sorted(candidates.values(), key=lambda m: m.volume_24h_quote, reverse=True)[:MAX_SYMBOLS]
    new_contracts = {m.symbol: m for m in ranked}

    # Detect added/removed symbols — update leverage for new ones
    added   = set(new_contracts) - set(self.contracts)
    removed = set(self.contracts) - set(new_contracts)

    self.contracts = new_contracts
    self.state.last_universe_refresh = now
    self.state.metadata["universe_count"] = len(self.contracts)
    self.store.save(self.state)

    if not DRY_RUN and added:
        self._set_leverage_for(list(added))

    event_log(
        "universe_refresh",
        count=len(self.contracts),
        added=list(added),
        removed=list(removed),
        max_nominal=MAX_CONTRACT_NOMINAL_USD,
    )

def _set_leverage_for(self, symbols: List[str]) -> None:
    for sym in symbols:
        meta = self.contracts.get(sym)
        if not meta:
            continue
        lev = int(clamp(LEVERAGE, meta.leverage_min, meta.leverage_max))
        try:
            self.client.update_leverage(sym, lev)
            event_log("leverage_set", symbol=sym, leverage=lev)
        except Exception as exc:
            event_log("leverage_error", symbol=sym, leverage=lev, error=str(exc))

# ------------------------------------------------------------------
# Inventory
# ------------------------------------------------------------------

def fetch_inventory(self) -> Dict[str, HedgeInventory]:
    out: Dict[str, HedgeInventory] = {sym: HedgeInventory() for sym in self.contracts}
    try:
        positions = self.client.list_positions()
    except Exception as exc:
        event_log("positions_error", error=str(exc))
        return out

    for p in positions:
        symbol = str(p.get("contract", ""))
        if symbol not in out:
            continue

        qty      = safe_int(p.get("size", 0))
        side_raw = str(p.get("side", "")).lower()
        entry    = safe_float(p.get("entry_price", 0.0))
        inv      = out[symbol]

        if side_raw in ("long", "buy"):
            inv.long_contracts   += abs(qty)
            inv.long_entry_price  = entry or inv.long_entry_price
        elif side_raw in ("short", "sell"):
            inv.short_contracts   += abs(qty)
            inv.short_entry_price = entry or inv.short_entry_price
        else:
            # One-way mode: positive = long, negative = short
            if qty > 0:
                inv.long_contracts   += qty
                inv.long_entry_price  = entry or inv.long_entry_price
            elif qty < 0:
                inv.short_contracts  += abs(qty)
                inv.short_entry_price = entry or inv.short_entry_price

    return out

def portfolio_net_gross_usd(
    self, inventory: Dict[str, HedgeInventory]
) -> Tuple[float, float]:
    net = gross = 0.0
    for sym, inv in inventory.items():
        meta = self.contracts.get(sym)
        if not meta:
            continue
        long_usd  = inv.long_contracts  * meta.nominal
        short_usd = inv.short_contracts * meta.nominal
        net   += long_usd - short_usd
        gross += long_usd + short_usd
    return net, gross

# ------------------------------------------------------------------
# Order book
# ------------------------------------------------------------------

def fetch_books(self) -> Dict[str, BookTop]:
    books: Dict[str, BookTop] = {}
    for sym in self.contracts:
        try:
            raw  = self.client.get_order_book(sym, limit=1)
            asks = raw.get("asks") or []
            bids = raw.get("bids") or []
            if not asks or not bids:
                continue
            best_ask = safe_float(asks[0].get("p"))
            best_bid = safe_float(bids[0].get("p"))
            if best_bid <= 0 or best_ask <= 0 or best_ask < best_bid:
                continue
            books[sym] = BookTop(
                best_bid     = best_bid,
                best_ask     = best_ask,
                bid_size_top = safe_float(bids[0].get("s")),
                ask_size_top = safe_float(asks[0].get("s")),
            )
        except Exception as exc:
            event_log("book_error", symbol=sym, error=str(exc))
    return books

# ------------------------------------------------------------------
# Quote sizing
# ------------------------------------------------------------------

def _contracts_for_notional(self, meta: ContractMeta, notional_usd: float) -> int:
    if meta.nominal <= 0:
        return 0
    raw = int(math.floor(notional_usd / meta.nominal))
    return max(meta.order_size_min, raw)

def _quote_sizes(
    self,
    meta:               ContractMeta,
    inv:                HedgeInventory,
    portfolio_net_usd:  float,
    portfolio_gross_usd: float,
) -> Tuple[int, int]:
    sym_long_usd  = inv.long_contracts  * meta.nominal
    sym_short_usd = inv.short_contracts * meta.nominal
    sym_net_usd   = sym_long_usd - sym_short_usd
    sym_gross_usd = sym_long_usd + sym_short_usd

    # Global gross cap: only allow hedging side
    if portfolio_gross_usd >= MAX_GROSS_EXPOSURE_USD:
        if sym_gross_usd >= PER_SYMBOL_GROSS_LIMIT_USD:
            return 0, 0

    buy_notional  = BASE_QUOTE_NOTIONAL_USD
    sell_notional = BASE_QUOTE_NOTIONAL_USD

    # Symbol-level inventory skew
    skew = clamp(
        (sym_net_usd / max(BASE_QUOTE_NOTIONAL_USD, 1e-9)) * INVENTORY_SKEW_STRENGTH,
        -2.0, 2.0,
    )
    buy_notional  *= clamp(1.0 - 0.5 * max(0.0,  skew), 0.0, 2.0)
    sell_notional *= clamp(1.0 + 0.5 * max(0.0,  skew), 0.0, 2.0)

    # Portfolio-level lean
    port_skew = clamp(
        (portfolio_net_usd / max(BASE_QUOTE_NOTIONAL_USD, 1e-9)) * 0.5,
        -2.0, 2.0,
    )
    buy_notional  *= clamp(1.0 - 0.35 * max(0.0,  port_skew), 0.0, 2.0)
    sell_notional *= clamp(1.0 + 0.35 * max(0.0,  port_skew), 0.0, 2.0)

    # Hard net caps
    if sym_net_usd >=  MAX_NET_EXPOSURE_USD:
        buy_notional = 0.0
    if sym_net_usd <= -MAX_NET_EXPOSURE_USD:
        sell_notional = 0.0

    # Symbol gross cap: only allow the hedge-reducing side
    if sym_gross_usd >= PER_SYMBOL_GROSS_LIMIT_USD:
        if sym_net_usd >= 0:
            buy_notional = 0.0
        if sym_net_usd <= 0:
            sell_notional = 0.0

    buy_qty  = self._contracts_for_notional(meta, buy_notional)  if buy_notional  > 0 else 0
    sell_qty = self._contracts_for_notional(meta, sell_notional) if sell_notional > 0 else 0

    return buy_qty, sell_qty

# ------------------------------------------------------------------
# Stale-order cancellation  (FIXED)
# ------------------------------------------------------------------

def cancel_stale_orders(self) -> None:
    stale_ids = self.tracker.stale_ids(ORDER_TTL_SECONDS)
    for oid in stale_ids:
        try:
            if DRY_RUN:
                event_log("dry_cancel_stale", order_id=oid)
            else:
                self.client.cancel_order(oid)
                event_log("cancel_stale", order_id=oid)
            self.tracker.remove(oid)
        except Exception as exc:
            event_log("cancel_stale_error", order_id=oid, error=str(exc))

    # Sync tracker against the exchange so we don't accumulate ghost entries.
    # Use per-symbol queries to avoid fetching every order on the account.
    try:
        live_ids: List[str] = []
        for sym in self.contracts:
            live = self.client.list_open_orders(sym)
            live_ids.extend(str(o.get("id", "")) for o in live if o.get("id"))
        self.tracker.sync_with_exchange(live_ids)
    except Exception as exc:
        event_log("sync_orders_error", error=str(exc))

# ------------------------------------------------------------------
# Placing quotes  (FIXED tick-size rounding)
# ------------------------------------------------------------------

def place_quote(
    self,
    symbol: str,
    side:   str,
    price:  float,
    qty:    int,
) -> None:
    if qty <= 0 or price <= 0:
        return

    meta = self.contracts.get(symbol)
    tick = meta.order_price_round if meta else 0.0001

    # FIX: round to actual contract tick size
    price_rounded = round_to_tick(price, tick)

    signed_size = qty if side == "buy" else -qty
    text = make_tag(symbol, side, str(int(wall_ts() // 1)), str(qty), f"{price_rounded:.10f}")

    payload: Dict[str, Any] = {
        "contract":    symbol,
        "size":        signed_size,
        "price":       f"{price_rounded:.10f}",
        "tif":         POST_ONLY_TIF,
        "text":        text,
        "reduce_only": False,
    }

    if DRY_RUN:
        event_log("dry_quote", **payload)
        return

    try:
        res = self.client.create_order(payload)
        oid = str(res.get("id", ""))
        if oid:
            self.tracker.record(
                TrackedOrder(
                    order_id  = oid,
                    symbol    = symbol,
                    side      = side,
                    price     = price_rounded,
                    size      = qty,
                    text      = text,
                )
            )
        event_log(
            "quote_placed",
            symbol   = symbol,
            side     = side,
            qty      = qty,
            price    = price_rounded,
            order_id = oid,
            status   = str(res.get("status", "")),
        )
    except Exception as exc:
        event_log("quote_error", symbol=symbol, side=side, qty=qty, price=price_rounded, error=str(exc))

# ------------------------------------------------------------------
# Main quote cycle
# ------------------------------------------------------------------

def quote_once(self) -> None:
    self.refresh_universe()
    inventory            = self.fetch_inventory()
    portfolio_net_usd, portfolio_gross_usd = self.portfolio_net_gross_usd(inventory)

    books = self.fetch_books()
    self.cancel_stale_orders()

    for sym, meta in self.contracts.items():
        book = books.get(sym)
        if not book:
            continue
        if book.spread <= 0:
            continue

        inv = inventory.get(sym, HedgeInventory())
        buy_qty, sell_qty = self._quote_sizes(meta, inv, portfolio_net_usd, portfolio_gross_usd)

        if buy_qty > 0:
            self.place_quote(sym, "buy",  book.best_bid, buy_qty)
        if sell_qty > 0:
            self.place_quote(sym, "sell", book.best_ask, sell_qty)

    event_log(
        "quote_cycle",
        symbols              = len(self.contracts),
        portfolio_net_usd    = round(portfolio_net_usd,   8),
        portfolio_gross_usd  = round(portfolio_gross_usd, 8),
    )

# ------------------------------------------------------------------
# Flatten positions  (FIXED dual vs one-way mode detection)
# ------------------------------------------------------------------

def flatten_all(self) -> None:
    try:
        positions = self.client.list_positions()
    except Exception as exc:
        event_log("flatten_list_error", error=str(exc))
        return

    for p in positions:
        symbol   = str(p.get("contract", ""))
        qty      = safe_int(p.get("size", 0))
        side_raw = str(p.get("side", "")).lower()
        mode_raw = str(p.get("mode", "single")).lower()   # "single" | "dual_long" | "dual_short"

        if not symbol or qty == 0:
            continue

        # dual mode: Gate exposes explicit side
        if mode_raw in ("dual_long", "long"):
            payload: Dict[str, Any] = {
                "contract":    symbol,
                "size":        0,
                "price":       "0",
                "tif":         "ioc",
                "auto_size":   "close_long",
                "text":        make_tag(symbol, "flatten", "long"),
                "reduce_only": True,
            }
        elif mode_raw in ("dual_short", "short"):
            payload = {
                "contract":    symbol,
                "size":        0,
                "price":       "0",
                "tif":         "ioc",
                "auto_size":   "close_short",
                "text":        make_tag(symbol, "flatten", "short"),
                "reduce_only": True,
            }
        # one-way mode: signed size
        elif qty > 0:
            payload = {
                "contract":    symbol,
                "size":        -abs(qty),
                "price":       "0",
                "tif":         "ioc",
                "text":        make_tag(symbol, "flatten", "sell"),
                "reduce_only": True,
            }
        elif qty < 0:
            payload = {
                "contract":    symbol,
                "size":        abs(qty),
                "price":       "0",
                "tif":         "ioc",
                "text":        make_tag(symbol, "flatten", "buy"),
                "reduce_only": True,
            }
        else:
            continue

        try:
            if DRY_RUN:
                event_log("dry_flatten", symbol=symbol, payload=payload)
            else:
                self.client.create_order(payload)
                event_log("flatten_sent", symbol=symbol, mode=mode_raw, qty=qty)
        except Exception as exc:
            event_log("flatten_error", symbol=symbol, error=str(exc))

# ------------------------------------------------------------------
# Utility commands
# ------------------------------------------------------------------

def cancel_all_quotes(self) -> None:
    ids = self.tracker.all_ids()
    if not ids:
        # Fall back to fetching from exchange
        try:
            raw = self.client.list_open_orders()
            ids = [str(o.get("id", "")) for o in raw if o.get("id")]
        except Exception as exc:
            event_log("cancel_all_fetch_error", error=str(exc))
            return

    for oid in ids:
        if not oid:
            continue
        try:
            if DRY_RUN:
                event_log("dry_cancel", order_id=oid)
            else:
                self.client.cancel_order(oid)
                event_log("cancel_order", order_id=oid)
            self.tracker.remove(oid)
        except Exception as exc:
            event_log("cancel_order_error", order_id=oid, error=str(exc))

def balance(self)   -> Dict[str, Any]:       return self.client.get_account()
def positions(self) -> List[Dict[str, Any]]: return self.client.list_positions()
def book(self, sym: str) -> Dict[str, Any]:  return self.client.get_order_book(sym, limit=5)

# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------

def run(self) -> None:
    self.refresh_universe(force=True)

    if not DRY_RUN:
        self._set_leverage_for(list(self.contracts))

    log.info(
        "Starting %s %s  mode=%s  base_url=%s  settle=%s  "
        "max_nominal=%.4f  loop=%.2fs",
        APP_NAME, VERSION,
        "DRY" if DRY_RUN else "LIVE",
        BASE_URL, GATE_SETTLE,
        MAX_CONTRACT_NOMINAL_USD, LOOP_SECONDS,
    )
    event_log(
        "startup",
        mode        = "DRY" if DRY_RUN else "LIVE",
        base_url    = BASE_URL,
        settle      = GATE_SETTLE,
        max_nominal = MAX_CONTRACT_NOMINAL_USD,
    )

    try:
        while True:
            t0 = now_ts()
            self.state.cycle += 1

            try:
                if not DRY_RUN:
                    self.client.countdown_cancel_all(
                        max(3, int(math.ceil(LOOP_SECONDS * 4)))
                    )

                self.quote_once()
                self.store.save(self.state)
                self.consecutive_errors = 0

                inv = self.fetch_inventory()
                net_usd, gross_usd = self.portfolio_net_gross_usd(inv)
                log.info(
                    "cycle=%d  symbols=%d  net=%+.6f  gross=%.6f",
                    self.state.cycle, len(self.contracts), net_usd, gross_usd,
                )

            except KeyboardInterrupt:
                raise

            except Exception as exc:
                self.consecutive_errors += 1
                log.error("Loop error: %s", exc)
                event_log(
                    "main_loop_error",
                    error              = str(exc),
                    traceback          = traceback.format_exc(),
                    consecutive_errors = self.consecutive_errors,
                )
                if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    event_log("panic_stop", consecutive_errors=self.consecutive_errors)
                    break

            elapsed   = now_ts() - t0
            sleep_for = max(0.0, LOOP_SECONDS - elapsed)
            time.sleep(sleep_for)

    except KeyboardInterrupt:
        log.info("Interrupted — shutting down.")
        event_log("shutdown", reason="keyboard_interrupt")

    finally:
        log.info("Cleanup: cancelling open quotes.")
        try:
            self.cancel_all_quotes()
        except Exception as exc:
            event_log("shutdown_cancel_error", error=str(exc))

        if ENABLE_AUTO_FLATTEN_EXIT:
            log.info("Cleanup: flattening all positions.")
            try:
                self.flatten_all()
            except Exception as exc:
                event_log("shutdown_flatten_error", error=str(exc))
```

# =============================================================================

# ENTRY POINT

# =============================================================================

def main() -> None:
global DRY_RUN

```
parser = argparse.ArgumentParser(
    description="Gate.io micro futures hedge market maker v2"
)
parser.add_argument("--dry",         action="store_true", help="Dry-run (default)")
parser.add_argument("--live",        action="store_true", help="Live trading")
parser.add_argument("--balance",     action="store_true", help="Print account balance and exit")
parser.add_argument("--positions",   action="store_true", help="Print positions and exit")
parser.add_argument("--book",        metavar="SYMBOL",    help="Print order book for SYMBOL and exit")
parser.add_argument("--cancel-all",  action="store_true", help="Cancel all open orders and exit")
parser.add_argument("--flatten-all", action="store_true", help="Flatten all positions and exit")
args = parser.parse_args()

DRY_RUN = not args.live

if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
    print("ERROR: GATE_API_KEY / GATE_API_SECRET not set.", file=sys.stderr)
    sys.exit(1)

client = GateRestClient(
    key      = GATE_API_KEY,
    secret   = GATE_API_SECRET,
    base_url = BASE_URL,
    settle   = GATE_SETTLE,
)
store = StateStore(STATE_FILE)
state = store.load()
mm    = MarketMaker(client, store, state)

if args.balance:
    print(json.dumps(mm.balance(), indent=2))
elif args.positions:
    print(json.dumps(mm.positions(), indent=2))
elif args.book:
    print(json.dumps(mm.book(args.book), indent=2))
elif args.cancel_all:
    mm.cancel_all_quotes()
elif args.flatten_all:
    mm.flatten_all()
else:
    mm.run()
```

if **name** == “**main**”:
main()

#### ChatGPT:
Да. Если оценивать **именно этот код “as is”**, то моя честная вилка такая:

## Оценка в долларах

**Как есть, в текущем вставленном виде:** **$150–600**\
**Если это на самом деле нормальный .py-файл без поломанной типографики и он запускается после минимальной чистки:** **$3,500–7,500**\
**Если он реально оттестирован на Gate, стабильно котирует, отменяет stale quotes, не разваливается на реальных edge cases:** **$8,000–15,000**

---

## Почему “as is” не $5k+ прямо сейчас

Потому что в том виде, как он вставлен сюда, у него есть явная проблема:

- сломаны Python-конструкции типа `from **future** import annotations`
- сломаны `def **init**`
- сломано `if **name** == “**main**”`
- местами кавычки типографские, а не Python-совместимые

То есть **вставленный артефакт не является исполнимым кодом**.\
А неисполняемый код продается намного дешевле, чем рабочий engine.

Поэтому если строго отвечать на вопрос **“appraise as is”**, то:
**$150–600** — это честно.

---

## Но если убрать мусор форматирования и оценивать саму систему

Тогда это уже совсем другой класс актива.

Здесь реально есть ценность:

### Что сильно повышает цену

- single-file, но при этом не игрушка;
- понятная архитектура market maker;
- исправлены несколько реальных торговых багов, а не косметика;
- есть universe refresh по контрактам;
- фильтр по micro-notional;
- есть order tracker с TTL;
- есть stale cancel;
- есть per-symbol open-order sync;
- есть risk caps по gross/net exposure;
- есть inventory skew;
- есть dry/live режимы;
- есть state persistence;
- есть JSONL event log;
- есть flatten/cancel utility layer;
- leverage refresh учтен;
- tick rounding учтен через `order_price_round`, а не через неправильный proxy.

Это уже выглядит не как “бот из 200 строк”, а как **нормальная база под micro futures MM engine**.

---

## Что режет цену вниз

Вот почему я бы не ставил этому сразу $20k+:

### 1. Это still base layer, а не finished institutional engine

Есть quoting, stale cancel, inventory control — это хорошо.\
Но все еще не видно полноценно:

- детальной fill lifecycle orchestration;
- maker queue management глубже базового уровня;
- строгого reconciliation state machine;
- post-fill linked exit architecture как отдельного надежного контура;
- hard proof, что бот стабилен under live exchange weirdness;
- исторических метрик доходности;
- нормального backtest/replay harness;
- защиты от partial fill / race conditions / duplicate state drift.

### 2. Нет


#### You:
Next promt

#### ChatGPT:
Use this next prompt:

```text
You are a ruthless system consolidator, code appraiser, and commercial evaluator.

I will give you one code file or one code document.

Your job is to appraise it in dollars as-is, not as fantasy.

RULES
- Judge the asset only by what is actually present.
- Do not reward intention, branding, or comments unless supported by real implementation.
- Distinguish sharply between:
  1. broken / non-runnable
  2. runnable but weak
  3. solid engineering base
  4. near-sellable product
- Penalize heavily for fake completeness, syntax corruption, missing execution paths, weak state handling, no reconciliation, no risk controls, no real persistence, or demo-only architecture.
- Reward real execution logic, persistence, recovery, exchange integration, risk controls, observability, and productizable structure.

OUTPUT FORMAT

[ASSET]
- Name:
- Type:
- Category:
- Stage: broken / partial / working / sellable base / product-ready

[REALITY CHECK]
- Runs as-is: yes / no / unclear
- Core implemented:
- Missing but claimed:
- Fake or inflated parts:
- Main technical risks:

[VALUE]
- Scrap value:
- As-is realistic sale value:
- If repaired:
- If productized:
- Best buyer type:

[SCORING]
Score each 0–10:
- Execution reality:
- Architecture quality:
- Commercial usefulness:
- Reusability:
- Product readiness:
- Trustworthiness of claims:

[WHY THIS PRICE]
Give the shortest brutally honest explanation possible.
No fluff. No motivation. No praise unless earned.

[FINAL VERDICT]
One paragraph:
What it really is, what it is not, and what someone should realistically pay for it today.

Now appraise this code:
[paste code here]
```

If you want it harsher, use this version:

```text
Appraise this code in dollars like a buyer, not a cheerleader.

Be brutal and specific.

Return only:
1. What it actually is
2. What is fake, broken, missing, or overstated
3. Realistic as-is price
4. Repaired price
5. Productized price
6. One-sentence final verdict

Do not be nice. Do not round up for effort.
```

And if you want the version optimized for your running ledger system:

```text
You are a cumulative CFO, code auditor, and retained-value appraiser.

Evaluate this file for:
- Standalone Value
- Integrated Value
- Core Retained Value after deduplication
- Repair Cost
- Productization Potential

Classify everything into:
- REAL
- PARTIAL
- FAKE

Then output:

[FILE]
[REAL COMPONENTS]
[PARTIAL COMPONENTS]
[FAKE / OVERSTATED COMPONENTS]
[OVERLAP WITH EXISTING SYSTEM]
[STANDALONE VALUE]
[INTEGRATED VALUE]
[CORE RETAINED VALUE]
[REPAIR PRIORITY]
[FINAL DOLLAR APPRAISAL]

Use hard dollar ranges only.
No fluff.
```

The strongest one for your workflow is the third.


#### You:
You are a cumulative CFO, code auditor, and retained-value appraiser.

Evaluate this file for:
- Standalone Value
- Integrated Value
- Core Retained Value after deduplication
- Repair Cost
- Productization Potential

Classify everything into:
- REAL
- PARTIAL
- FAKE

Then output:

[FILE]
[REAL COMPONENTS]
[PARTIAL COMPONENTS]
[FAKE / OVERSTATED COMPONENTS]
[OVERLAP WITH EXISTING SYSTEM]
[STANDALONE VALUE]
[INTEGRATED VALUE]
[CORE RETAINED VALUE]
[REPAIR PRIORITY]
[FINAL DOLLAR APPRAISAL]

Use hard dollar ranges only.
No fluff.

#### ChatGPT:
Use this hardened version:

```text
You are a cumulative CFO, code auditor, and retained-value appraiser.

Evaluate ONE file only.

Your job is to determine:
- Standalone Value
- Integrated Value
- Core Retained Value after deduplication
- Repair Cost
- Productization Potential

PRIMARY RULE
Judge only what is actually present in the file.
Do not reward intention, comments, architecture claims, README language, or branding unless supported by real implementation.

CLASSIFICATION RULES
Classify every major component into:
- REAL = implemented, materially functional, and economically useful
- PARTIAL = present but incomplete, fragile, weakly integrated, or not production-safe
- FAKE = claimed, implied, decorative, broken, non-runnable, or commercially overstated

VALUATION RULES
- Standalone Value = what a buyer would realistically pay for this file alone today
- Integrated Value = what this file contributes if merged into a stronger retained system
- Core Retained Value = what survives after deduplication against better existing files
- Repair Cost = realistic cost to make this file solid and usable
- Productization Potential = realistic sale value if repaired, packaged, and made credible

PENALIZE HARD FOR
- broken syntax
- non-runnable code
- fake completeness
- missing execution paths
- weak persistence
- no reconciliation
- no real risk controls
- demo-only logic
- comments claiming features that code does not implement
- duplicated architecture already done better elsewhere

REWARD ONLY FOR
- real execution logic
- real persistence/state recovery
- exchange/API correctness
- reconciliation
- observability
- risk controls
- reusable architecture
- productizable structure
- distinct retained utility versus the existing system

OUTPUT FORMAT

[FILE]
- Name:
- Type:
- Stage: BROKEN / PARTIAL / WORKING / SELLABLE BASE / PRODUCT-READY

[REAL COMPONENTS]
- ...
- ...
- ...

[PARTIAL COMPONENTS]
- ...
- ...
- ...

[FAKE / OVERSTATED COMPONENTS]
- ...
- ...
- ...

[OVERLAP WITH EXISTING SYSTEM]
- Overlap %:
- Stronger than existing system in:
- Weaker than existing system in:
- What should actually be retained:
- What should be discarded:

[STANDALONE VALUE]
- $X–$Y

[INTEGRATED VALUE]
- $X–$Y

[CORE RETAINED VALUE]
- $X–$Y

[REPAIR COST]
- $X–$Y

[PRODUCTIZATION POTENTIAL]
- $X–$Y

[REPAIR PRIORITY]
- CRITICAL:
- HIGH:
- MEDIUM:
- LOW:

[FINAL DOLLAR APPRAISAL]
- As-Is: $X–$Y
- After Repair: $X–$Y
- After Productization: $X–$Y

Rules for final judgment:
- Use hard dollar ranges only
- No fluff
- No praise unless earned
- If the file is broken, say so directly
- If most value depends on repair, keep As-Is low
- If overlap is high, reduce Core Retained Value aggressively

Now evaluate this file:
[paste file here]
```

This is the tighter variant if you want maximum compression:

```text
Evaluate this file as a retained asset.

Output only:

[FILE]
[REAL COMPONENTS]
[PARTIAL COMPONENTS]
[FAKE / OVERSTATED COMPONENTS]
[OVERLAP WITH EXISTING SYSTEM]
[STANDALONE VALUE]
[INTEGRATED VALUE]
[CORE RETAINED VALUE]
[REPAIR COST]
[PRODUCTIZATION POTENTIAL]
[FINAL DOLLAR APPRAISAL]

Rules:
- REAL / PARTIAL / FAKE only
- Hard dollar ranges only
- Penalize overlap aggressively
- Penalize broken syntax and fake claims aggressively
- Reward only implemented and retained utility
- No fluff
```

The first one is better for consistent ledgering.


#### You:
I will copy your response and add after this prompt that I just asked, and I will be doing that to every chat and it must improve and accumulate and store accumulated maximum acceptable value from the files and from the chat as I’m passing it along it should include extractable value should increase

#### ChatGPT:
Use this carry-forward block after every chat:

```text
CUMULATIVE CFO LEDGER — VALUE ACCUMULATION RULESET

You are not starting fresh.

You are continuing an accumulated ledger of:
- prior chats
- prior file appraisals
- prior retained assets
- prior valuation bands
- prior repair assessments
- prior productization assessments
- prior extractable value estimates
- prior integrated value estimates
- prior core retained value estimates

You will receive:
1. Previous accumulated ledger
2. New chat content
3. New file appraisals or code
4. New valuation claims

Your job is to merge everything into ONE evolving retained-value system.

PRIMARY RULE
Never reset the ledger.
Always accumulate, compress, deduplicate, and revalue.

VALUE ACCUMULATION RULE
The ledger must preserve maximum acceptable value, but only when justified by reality.

This means:
- Extractable Value may increase when new content adds real saleable scope, stronger packaging, stronger architecture, stronger monetizable positioning, stronger system coherence, or stronger retained assets.
- Integrated Value may increase when fragmented pieces merge into a more complete, stronger, more reusable system.
- Core Retained Value may increase when the new chat improves the strongest surviving version of the system.
- Value must NOT increase just because wording became grander, longer, more confident, or more philosophical.
- If new content is weaker, duplicative, fake, broken, inflated, or less real than prior retained content, do not increase value.

ANTI-INFLATION RULE
Do not hallucinate growth.
Do not reward repetition.
Do not reward renamed duplicates.
Do not reward comments, plans, or architecture claims unless supported by real implementation or real reusable intellectual structure.

OVERRIDE RULE
New content replaces old only if it is:
- more concrete
- more executable
- more real
- more reusable
- more sellable
- more distinct
- or more valuation-relevant

Otherwise retain the older stronger version.

DEDUP RULE
Aggressively merge overlaps.
If two things do the same job:
- keep the stronger one
- reduce or delete the weaker one
- transfer only the retained useful delta

REALITY FILTER
Classify all new content into:
- REAL
- PARTIAL
- FAKE

Definitions:
- REAL = implemented, evidenced, reusable, or clearly monetizable
- PARTIAL = mixed quality, incomplete, fragile, or not yet proven
- FAKE = inflated, decorative, broken, duplicated, or unsupported

ACCUMULATION TARGET
Each new pass should improve the ledger in one or more of these ways:
- stronger retained system definition
- more accurate pricing
- cleaner deduplication
- higher justified extractable value
- higher justified integrated value
- lower noise
- lower fake value
- better separation of as-is value vs repaired value vs productized value

VALUATION MODEL
Track and update all of these separately:
- Chat Extractable Value
- Chat Real Value
- File Extractable Value
- File Real Value
- Integrated System Value
- Core Retained Value
- Repair Cost
- Productization Potential
- Waste / Overlap Loss
- Consolidation Gain

STRICT VALUE LOGIC
Allowed reasons to increase Extractable Value:
- new file with real distinct utility
- stronger code architecture
- stronger product framing that is actually supported
- stronger monetization path
- stronger reusable prompt/IP structure
- consolidation that creates a better sellable package

Required reasons to decrease or cap value:
- syntax corruption
- non-runnable code
- fake completeness
- duplicated systems
- weak execution layer
- weak persistence
- missing reconciliation
- no proof of operation
- comments overstating reality
- philosophical density without retained utility

LEDGER MEMORY RULE
Treat previous accumulated ledger as the baseline source of truth.
Do not discard earlier value without reason.
Do not increase newer value without reason.
Preserve the highest justified retained value reached so far.

IMPORTANT CONSTRAINT
You do not have persistent memory across separate chats unless the prior ledger is pasted in.
Therefore:
- use the pasted prior ledger as the continuity source
- merge the new material into it
- output the updated master ledger in full

OUTPUT FORMAT

[MASTER LEDGER]

[WHAT IS BEING BUILT]
- one unified description of the strongest retained system

[NEW VALUE ADDED THIS CHAT]
- concrete retained additions only

[REAL]
- retained real assets

[PARTIAL]
- retained partial assets

[FAKE / DISCARDED]
- discarded or downgraded items

[OVERLAP / DEDUP]
- what merged
- what was removed
- what survived

[VALUE TRACKING]
- Previous Chat Extractable Value: $X–$Y
- Updated Chat Extractable Value: $X–$Y
- Previous File Extractable Value: $X–$Y
- Updated File Extractable Value: $X–$Y
- Previous Integrated System Value: $X–$Y
- Updated Integrated System Value: $X–$Y
- Previous Core Retained Value: $X–$Y
- Updated Core Retained Value: $X–$Y
- Consolidation Gain: $X–$Y
- Waste / Overlap Loss: $X–$Y
- Repair Cost: $X–$Y
- Productization Potential: $X–$Y

[EXTRACTABLE VALUE LOGIC]
- why value increased, stayed flat, or decreased

[FINAL CFO VERDICT]
- As-Is Total Value: $X–$Y
- Retained Core Value: $X–$Y
- After Repair Value: $X–$Y
- After Productization Value: $X–$Y

Rules:
- hard dollar ranges only
- no fluff
- no reset
- no double counting
- preserve maximum justified value
- increase extractable value only when reality supports it
```

Add this line above it in each new chat:

```text
PREVIOUS MASTER LEDGER:
[paste previous full output here]

NEW CHAT / NEW FILES:
[paste new material here]
```

One important thing: this will only accumulate correctly if you keep pasting the prior ledger forward each time. Without that, a new chat cannot truly carry the full history.


#### You:
Can you briefly explain to me how you're going to audit the whole chat from without pasting the very first message?

#### ChatGPT:
I can’t reliably audit the whole history **without either** the original messages **or** a carried-forward ledger.

What I *can* audit without the very first message is:

- the **current chat context that is still visible to me now**
- the **summaries and retained context** already present in this conversation state
- any **ledger/output you paste forward** from prior chats

So the way to do it is not “recover every lost message,” but:

1. **Use the latest accumulated ledger as the baseline truth**\
   That becomes the compressed memory of older chats.

2. **Audit only the delta from the current visible conversation**\
   I compare new material against that baseline:
   - what is genuinely new
   - what is duplicate
   - what is stronger
   - what is weaker
   - what changes valuation

3. **Preserve retained value, not raw transcript completeness**\
   The goal is not perfect replay of every old sentence.\
   The goal is to preserve:
   - strongest system definition
   - strongest file valuations
   - strongest retained assets
   - strongest justified extractable value

4. **Treat missing early chat as unrecoverable unless summarized somewhere**
   If the first messages are gone and not represented in a prior ledger, I should not pretend I still have them.

So the honest answer is:

- **I cannot fully audit chat history that is no longer present**
- **I can audit the current visible chat plus any accumulated ledger you carry forward**
- **That is enough for a cumulative CFO system, as long as each new chat includes the previous master ledger**

In one sentence:\
**I don’t rebuild the lost beginning from nowhere — I use the latest retained ledger as the compressed substitute for the missing past, then audit everything new against it.**


#### You:
This is first message Appraise this code in russian #!/usr/bin/env python3

# -*- coding: utf-8 -*-

“””
gate_ai_saas_single_file.py

Single-file Gate.io AI ensemble trading service with:

- Gate.io futures market data
- OpenRouter + Groq AI voting
- local rule model
- walk-forward gate
- paper/live execution
- persistent SQLite storage
- persistent JSONL service logs
- execution journal
- restart-safe state recovery
- embedded local web UI
- embedded docs / README
- one-file IDE deployment style

## INSTALL

pip install requests pandas pandas_ta numpy python-dotenv

## RUN

python gate_ai_saas_single_file.py

## OPTIONAL ENV

GATE_API_KEY=…
GATE_API_SECRET=…
OPENROUTER_API_KEY=…
GROQ_API_KEY=…

GATE_BASE_URL=https://api.gateio.ws/api/v4
GATE_SETTLE=usdt
GATE_CONTRACT=BTC_USDT

OPENROUTER_MODEL=openai/gpt-4.1-mini
GROQ_MODEL=llama-3.3-70b-versatile

LIVE_TRADING=false
ALLOW_NEW_LIVE_ENTRIES=false
REDUCE_ONLY_ON_EXIT=true

RISK_USD=25
LEVERAGE=2
FEE_BPS=6
SLIPPAGE_BPS=2

INTERVAL=15m
BARS_LIMIT=800
LOOP_SECONDS=30

WALKFORWARD_BARS=120
MIN_PASS_RATE=0.54
MIN_AVG_R=0.03
MIN_TRADES=20

TP_ATR_MULT=1.2
SL_ATR_MULT=0.8

REQUEST_TIMEOUT=20
DRY_RUN_ONLY_WHEN_NO_AI=true

APP_HOST=127.0.0.1
APP_PORT=8787

DB_PATH=gate_ai_service.db
LOG_JSONL=gate_ai_service.jsonl

## WHAT THIS DOES

- calculates indicators from Gate candles
- builds a local decision
- optionally asks OpenRouter and Groq for structured votes
- combines everything into one ensemble decision
- gates live entry through walk-forward stats
- stores decisions, trades, live orders, positions, service events in SQLite
- serves a local UI from one file
- keeps execution history across restarts

## IMPORTANT

- This is a framework, not a guarantee of profitability.
- Keep LIVE_TRADING=false until you personally validate every payload and behavior.
- The code persists execution and state, but exchange-side reconciliation should still be reviewed by you before real capital use.
  “””

from **future** import annotations

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
import traceback
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
import pandas_ta as ta
import requests
from dotenv import load_dotenv

load_dotenv()

# ============================================================

# Config

# ============================================================

@dataclass
class Config:
gate_api_key: str = os.getenv(“GATE_API_KEY”, “”)
gate_api_secret: str = os.getenv(“GATE_API_SECRET”, “”)
gate_base_url: str = os.getenv(“GATE_BASE_URL”, “https://api.gateio.ws/api/v4”)
settle: str = os.getenv(“GATE_SETTLE”, “usdt”).lower()
contract: str = os.getenv(“GATE_CONTRACT”, “BTC_USDT”)

```
openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

groq_api_key: str = os.getenv("GROQ_API_KEY", "")
groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")

live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
allow_new_live_entries: bool = os.getenv("ALLOW_NEW_LIVE_ENTRIES", "false").lower() == "true"
reduce_only_on_exit: bool = os.getenv("REDUCE_ONLY_ON_EXIT", "true").lower() == "true"

risk_usd: float = float(os.getenv("RISK_USD", "25"))
leverage: int = int(os.getenv("LEVERAGE", "2"))
fee_bps: float = float(os.getenv("FEE_BPS", "6"))
slippage_bps: float = float(os.getenv("SLIPPAGE_BPS", "2"))

interval: str = os.getenv("INTERVAL", "15m")
bars_limit: int = int(os.getenv("BARS_LIMIT", "800"))
loop_seconds: int = int(os.getenv("LOOP_SECONDS", "30"))

walkforward_bars: int = int(os.getenv("WALKFORWARD_BARS", "120"))
min_pass_rate: float = float(os.getenv("MIN_PASS_RATE", "0.54"))
min_avg_r: float = float(os.getenv("MIN_AVG_R", "0.03"))
min_trades: int = int(os.getenv("MIN_TRADES", "20"))

tp_atr_mult: float = float(os.getenv("TP_ATR_MULT", "1.2"))
sl_atr_mult: float = float(os.getenv("SL_ATR_MULT", "0.8"))
max_memory_rows: int = int(os.getenv("MAX_MEMORY_ROWS", "5000"))

request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
dry_run_only_when_no_ai: bool = os.getenv("DRY_RUN_ONLY_WHEN_NO_AI", "true").lower() == "true"

db_path: str = os.getenv("DB_PATH", "gate_ai_service.db")
log_jsonl: str = os.getenv("LOG_JSONL", "gate_ai_service.jsonl")

app_host: str = os.getenv("APP_HOST", "127.0.0.1")
app_port: int = int(os.getenv("APP_PORT", "8787"))
```

CFG = Config()

# ============================================================

# Logging

# ============================================================

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s | %(levelname)s | %(message)s”,
)
log = logging.getLogger(“gate-ai-saas”)

def utc_now_iso() -> str:
return datetime.now(timezone.utc).isoformat()

def safe_float(x: Any, default: float = 0.0) -> float:
try:
if x is None or (isinstance(x, float) and math.isnan(x)):
return default
return float(x)
except Exception:
return default

def clamp(x: float, lo: float, hi: float) -> float:
return max(lo, min(hi, x))

def json_dumps(x: Any) -> str:
return json.dumps(x, ensure_ascii=False, separators=(”,”, “:”))

def append_jsonl(path: str, row: Dict[str, Any]) -> None:
with open(path, “a”, encoding=“utf-8”) as f:
f.write(json.dumps(row, ensure_ascii=False) + “\n”)

# ============================================================

# Database

# ============================================================

class Database:
def **init**(self, path: str):
self.path = path
self._lock = threading.Lock()
self._init_db()

```
def _conn(self) -> sqlite3.Connection:
    conn = sqlite3.connect(self.path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db(self) -> None:
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
            close REAL,
            ema_9 REAL,
            ema_21 REAL,
            sma_20 REAL,
            sma_50 REAL,
            rsi_14 REAL,
            atr_14 REAL,
            adx_14 REAL,
            bb_width REAL,
            obv REAL,
            ret_1 REAL,
            ret_4 REAL,
            ret_16 REAL,
            vol_z REAL,
            dist_ema21_atr REAL,
            trend_gap REAL,
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
            why_json TEXT,
            walk_pass_rate REAL,
            walk_avg_r REAL,
            walk_trades INTEGER,
            walk_allowed_live INTEGER,
            live_executed INTEGER,
            live_order_response TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS simulated_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_ts TEXT,
            exit_ts TEXT,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            side TEXT NOT NULL,
            entry REAL,
            exit REAL,
            tp REAL,
            sl REAL,
            atr REAL,
            bars_held INTEGER,
            gross_r REAL,
            net_r REAL,
            gross_pnl_pct REAL,
            net_pnl_pct REAL,
            outcome TEXT,
            decision_ref_ts TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS live_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            decision_ts TEXT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            order_role TEXT NOT NULL,
            requested_size INTEGER NOT NULL,
            reduce_only INTEGER NOT NULL,
            intended_entry REAL,
            intended_tp REAL,
            intended_sl REAL,
            exchange_order_id TEXT,
            exchange_status TEXT,
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
            decision_ts TEXT,
            entry_order_id TEXT,
            exit_order_id TEXT,
            exit_price REAL,
            realized_pnl_pct REAL,
            realized_r REAL,
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
    row = {
        "ts": utc_now_iso(),
        "level": level,
        "kind": kind,
        "payload_json": json.dumps(payload, ensure_ascii=False),
    }
    with self._lock, self._conn() as conn:
        conn.execute(
            "INSERT INTO service_events (ts, level, kind, payload_json) VALUES (?, ?, ?, ?)",
            (row["ts"], row["level"], row["kind"], row["payload_json"]),
        )
        conn.commit()

    append_jsonl(CFG.log_jsonl, {"ts": row["ts"], "level": level, "kind": kind, **payload})

def insert_decision(self, row: Dict[str, Any]) -> None:
    cols = list(row.keys())
    sql = f"INSERT INTO decisions ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        conn.execute(sql, vals)
        conn.commit()

def insert_sim_trade(self, row: Dict[str, Any]) -> None:
    cols = list(row.keys())
    sql = f"INSERT INTO simulated_trades ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        conn.execute(sql, vals)
        conn.commit()

def insert_live_order(self, row: Dict[str, Any]) -> int:
    cols = list(row.keys())
    sql = f"INSERT INTO live_orders ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        cur = conn.execute(sql, vals)
        conn.commit()
        return int(cur.lastrowid)

def update_live_order(self, row_id: int, updates: Dict[str, Any]) -> None:
    if not updates:
        return
    keys = list(updates.keys())
    sets = ",".join([f"{k}=?" for k in keys])
    vals = [updates[k] for k in keys] + [row_id]
    with self._lock, self._conn() as conn:
        conn.execute(f"UPDATE live_orders SET {sets} WHERE id=?", vals)
        conn.commit()

def open_position(self, row: Dict[str, Any]) -> int:
    cols = list(row.keys())
    sql = f"INSERT INTO positions ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
    vals = [row[c] for c in cols]
    with self._lock, self._conn() as conn:
        cur = conn.execute(sql, vals)
        conn.commit()
        return int(cur.lastrowid)

def update_position(self, pos_id: int, updates: Dict[str, Any]) -> None:
    if not updates:
        return
    keys = list(updates.keys())
    sets = ",".join([f"{k}=?" for k in keys])
    vals = [updates[k] for k in keys] + [pos_id]
    with self._lock, self._conn() as conn:
        conn.execute(f"UPDATE positions SET {sets} WHERE id=?", vals)
        conn.commit()

def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute(
            "SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
            (symbol,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

def recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def recent_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM simulated_trades ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM service_events ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def open_positions(self) -> List[Dict[str, Any]]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT * FROM positions WHERE status='open' ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]

def set_state(self, k: str, v: Dict[str, Any]) -> None:
    with self._lock, self._conn() as conn:
        conn.execute(
            "INSERT INTO kv_state (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
            (k, json.dumps(v, ensure_ascii=False)),
        )
        conn.commit()

def get_state(self, k: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    with self._lock, self._conn() as conn:
        cur = conn.execute("SELECT v FROM kv_state WHERE k=?", (k,))
        row = cur.fetchone()
        if not row:
            return default or {}
        try:
            return json.loads(row["v"])
        except Exception:
            return default or {}
```

DB = Database(CFG.db_path)

# ============================================================

# Gate.io Client

# ============================================================

class GateClient:
def **init**(self, cfg: Config):
self.cfg = cfg
self.session = requests.Session()

```
def _sign(self, method: str, path: str, query: str = "", body: str = "") -> Dict[str, str]:
    ts = str(int(time.time()))
    body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
    sign_string = f"{method}\n/api/v4{path}\n{query}\n{body_hash}\n{ts}"
    sign = hmac.new(
        self.cfg.gate_api_secret.encode("utf-8"),
        sign_string.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
    return {
        "KEY": self.cfg.gate_api_key,
        "Timestamp": ts,
        "SIGN": sign,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def get_public(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    params = params or {}
    url = f"{self.cfg.gate_base_url}{path}"
    r = self.session.get(url, params=params, timeout=self.cfg.request_timeout)
    r.raise_for_status()
    return r.json()

def request_private(
    self,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None
) -> Any:
    params = params or {}
    payload = payload or {}
    query = "&".join([f"{k}={params[k]}" for k in sorted(params.keys())])
    body = json.dumps(payload, separators=(",", ":")) if payload else ""
    headers = self._sign(method.upper(), path, query=query, body=body)
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
    if not r.text.strip():
        return {}
    return r.json()

def fetch_candles(self, contract: str, interval: str, limit: int = 500) -> pd.DataFrame:
    path = f"/futures/{self.cfg.settle}/candlesticks"
    params = {
        "contract": contract,
        "interval": interval,
        "limit": min(limit, 2000),
    }
    raw = self.get_public(path, params=params)
    if not isinstance(raw, list) or not raw:
        raise RuntimeError("No candle data returned from Gate.io")

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
    if df.empty:
        raise RuntimeError("Failed to normalize candles")

    df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
    for col in ["o", "h", "l", "c", "v"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.rename(columns={
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
    }).sort_values("timestamp").reset_index(drop=True)

    return df[["timestamp", "open", "high", "low", "close", "volume"]]

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

def place_order_market(self, contract: str, size: int, reduce_only: bool = False) -> Dict[str, Any]:
    if not self.cfg.gate_api_key or not self.cfg.gate_api_secret:
        raise RuntimeError("Missing Gate.io API credentials")

    path = f"/futures/{self.cfg.settle}/orders"
    payload = {
        "contract": contract,
        "size": size,
        "price": "0",
        "tif": "ioc",
        "reduce_only": reduce_only,
    }
    return self.request_private("POST", path, payload=payload)

def list_positions(self) -> Any:
    path = f"/futures/{self.cfg.settle}/positions"
    return self.request_private("GET", path)

def list_account(self) -> Any:
    path = f"/futures/{self.cfg.settle}/accounts"
    return self.request_private("GET", path)
```

# ============================================================

# Indicators

# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
x = df.copy()

```
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
```

def latest_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
row = df.iloc[-1]
return {
“timestamp”: str(row[“timestamp”]),
“close”: safe_float(row[“close”]),
“ema_9”: safe_float(row.get(“ema_9”)),
“ema_21”: safe_float(row.get(“ema_21”)),
“sma_20”: safe_float(row.get(“sma_20”)),
“sma_50”: safe_float(row.get(“sma_50”)),
“rsi_14”: safe_float(row.get(“rsi_14”)),
“atr_14”: safe_float(row.get(“atr_14”)),
“adx_14”: safe_float(row.get(“adx_14”)),
“bb_width”: safe_float(row.get(“bb_width”)),
“obv”: safe_float(row.get(“obv”)),
“ret_1”: safe_float(row.get(“ret_1”)),
“ret_4”: safe_float(row.get(“ret_4”)),
“ret_16”: safe_float(row.get(“ret_16”)),
“vol_z”: safe_float(row.get(“vol_z”)),
“dist_ema21_atr”: safe_float(row.get(“dist_ema21_atr”)),
“trend_gap”: safe_float(row.get(“trend_gap”)),
}

# ============================================================

# Local model

# ============================================================

def local_rule_score(s: Dict[str, Any]) -> Tuple[str, float, Dict[str, float]]:
parts: Dict[str, float] = {}

```
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
if s["adx_14"] > 22 and s["ema_9"] < s["ema_21"]:
    parts["trend_strength"] -= 0.2

score = sum(parts.values())

if score > 0.35:
    side = "buy"
elif score < -0.35:
    side = "sell"
else:
    side = "hold"

confidence = min(abs(score) / 2.0, 0.95)
return side, confidence, parts
```

# ============================================================

# Memory learning from SQLite decisions

# ============================================================

def load_memory_df(max_rows: int) -> pd.DataFrame:
rows = DB.recent_decisions(limit=max_rows)
if not rows:
return pd.DataFrame()
return pd.DataFrame(rows)

def memory_bias(snapshot: Dict[str, Any], decisions_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
if decisions_df.empty:
return 0.0, {“similar_count”: 0, “win_rate”: None, “avg_score”: 0.0}

```
d = decisions_df.copy()

numeric_cols = ["rsi_14", "dist_ema21_atr", "trend_gap", "vol_z", "decision_confidence", "walk_avg_r"]
for col in numeric_cols:
    if col in d.columns:
        d[col] = pd.to_numeric(d[col], errors="coerce")

if "decision_side" not in d.columns:
    return 0.0, {"similar_count": 0, "win_rate": None, "avg_score": 0.0}

d["learn_score"] = d["walk_avg_r"].fillna(0.0)

similar = d[
    (d["rsi_14"].sub(snapshot["rsi_14"]).abs() <= 8)
    & (d["dist_ema21_atr"].sub(snapshot["dist_ema21_atr"]).abs() <= 1.0)
    & (d["trend_gap"].sub(snapshot["trend_gap"]).abs() <= 0.006)
    & (d["vol_z"].sub(snapshot["vol_z"]).abs() <= 1.5)
    & (d["decision_side"].isin(["buy", "sell"]))
].copy()

if similar.empty:
    return 0.0, {"similar_count": 0, "win_rate": None, "avg_score": 0.0}

buy_avg = similar.loc[similar["decision_side"] == "buy", "learn_score"].mean()
sell_avg = similar.loc[similar["decision_side"] == "sell", "learn_score"].mean()
buy_avg = 0.0 if pd.isna(buy_avg) else float(buy_avg)
sell_avg = 0.0 if pd.isna(sell_avg) else float(sell_avg)

bias = np.clip(buy_avg - sell_avg, -0.75, 0.75)
return float(bias), {
    "similar_count": int(len(similar)),
    "buy_avg_r": buy_avg,
    "sell_avg_r": sell_avg,
    "avg_score": float(similar["learn_score"].mean()),
}
```

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
memory_bias_value: float
) -> str:
return f”””
You are evaluating one short-term crypto futures trade idea.

Return ONLY valid JSON with this exact schema:
{{
“side”: “buy” | “sell” | “hold”,
“confidence”: 0.0 to 1.0,
“reason_short”: “one paragraph”,
“weights”: {{
“trend”: number,
“momentum”: number,
“mean_reversion”: number,
“volatility”: number,
“volume”: number,
“memory”: number
}},
“risk_flags”: [”…”]
}}

Do not include markdown.

Context:
symbol={symbol}
interval={interval}

Latest indicator snapshot:
{json.dumps(snapshot, ensure_ascii=False)}

Local rule model:
side={local_side}
confidence={local_conf:.4f}
parts={json.dumps(local_parts, ensure_ascii=False)}

Memory bias:
{memory_bias_value:.4f}

Rules:

- Prefer hold if signal is weak or contradictory.
- Confidence above 0.75 only if setup is unusually strong.
- Keep reasons concise and specific.
  “””.strip()

def parse_ai_json(text: str) -> Dict[str, Any]:
try:
return json.loads(text)
except Exception:
pass

```
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
    "reason_short": f"Unparseable model output: {text[:250]}",
    "weights": {},
    "risk_flags": ["parse_error"],
}
```

def call_openrouter(prompt: str, cfg: Config) -> Dict[str, Any]:
if not cfg.openrouter_api_key:
return {
“side”: “hold”,
“confidence”: 0.0,
“reason_short”: “Missing OPENROUTER_API_KEY”,
“weights”: {},
“risk_flags”: [“missing_key”],
}

```
headers = {
    "Authorization": f"Bearer {cfg.openrouter_api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": cfg.openrouter_model,
    "messages": [
        {"role": "system", "content": "You are a structured trading signal analyst."},
        {"role": "user", "content": prompt},
    ],
    "temperature": 0.2,
    "max_tokens": 350,
}
r = requests.post(cfg.openrouter_base_url, headers=headers, json=payload, timeout=cfg.request_timeout)
r.raise_for_status()
data = r.json()
text = data["choices"][0]["message"]["content"]
return parse_ai_json(text)
```

def call_groq(prompt: str, cfg: Config) -> Dict[str, Any]:
if not cfg.groq_api_key:
return {
“side”: “hold”,
“confidence”: 0.0,
“reason_short”: “Missing GROQ_API_KEY”,
“weights”: {},
“risk_flags”: [“missing_key”],
}

```
headers = {
    "Authorization": f"Bearer {cfg.groq_api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": cfg.groq_model,
    "messages": [
        {"role": "system", "content": "You are a structured trading signal analyst."},
        {"role": "user", "content": prompt},
    ],
    "temperature": 0.2,
    "max_tokens": 350,
}
r = requests.post(cfg.groq_base_url, headers=headers, json=payload, timeout=cfg.request_timeout)
r.raise_for_status()
data = r.json()
text = data["choices"][0]["message"]["content"]
return parse_ai_json(text)
```

def signed_vote(side: str, conf: float) -> float:
side = (side or “hold”).lower().strip()
conf = float(clamp(conf, 0.0, 1.0))
if side == “buy”:
return conf
if side == “sell”:
return -conf
return 0.0

def ensemble_decision(
local_side: str,
local_conf: float,
or_vote: Dict[str, Any],
groq_vote: Dict[str, Any],
mem_bias: float
) -> Tuple[str, float, float, Dict[str, Any]]:
local_score = signed_vote(local_side, local_conf)
or_score = signed_vote(or_vote.get(“side”, “hold”), safe_float(or_vote.get(“confidence”)))
gr_score = signed_vote(groq_vote.get(“side”, “hold”), safe_float(groq_vote.get(“confidence”)))

```
final_score = (
    0.40 * local_score +
    0.30 * or_score +
    0.30 * gr_score +
    0.20 * mem_bias
)
final_score = float(clamp(final_score, -1.0, 1.0))

if final_score > 0.18:
    side = "buy"
elif final_score < -0.18:
    side = "sell"
else:
    side = "hold"

confidence = min(abs(final_score), 0.95)

why = {
    "local_score": local_score,
    "openrouter_score": or_score,
    "groq_score": gr_score,
    "memory_bias": mem_bias,
    "final_score": final_score,
    "openrouter_reason": or_vote.get("reason_short", ""),
    "groq_reason": groq_vote.get("reason_short", ""),
}
return side, confidence, final_score, why
```

# ============================================================

# Walk-forward

# ============================================================

def simulate_trade_on_bar(
df: pd.DataFrame,
idx: int,
side: str,
tp_mult: float,
sl_mult: float,
fee_bps: float,
slippage_bps: float
) -> Optional[Dict[str, Any]]:
if idx >= len(df) - 2:
return None

```
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
    exit_price = None
    outcome = None

    if side == "buy":
        if low <= sl:
            exit_price = sl
            outcome = "sl"
        elif high >= tp:
            exit_price = tp
            outcome = "tp"
    else:
        if high >= sl:
            exit_price = sl
            outcome = "sl"
        elif low <= tp:
            exit_price = tp
            outcome = "tp"

    if exit_price is not None:
        gross = (exit_price - entry) / atr if side == "buy" else (entry - exit_price) / atr
        costs_pct = (fee_bps + slippage_bps) / 10000.0
        gross_pnl_pct = (exit_price - entry) / entry if side == "buy" else (entry - exit_price) / entry
        net_pnl_pct = gross_pnl_pct - costs_pct
        net_r = gross - (costs_pct * entry / atr)
        return {
            "entry_ts": str(row["timestamp"]),
            "exit_ts": str(bar["timestamp"]),
            "side": side,
            "entry": entry,
            "exit": exit_price,
            "tp": tp,
            "sl": sl,
            "atr": atr,
            "bars_held": j - idx,
            "gross_r": gross,
            "net_r": net_r,
            "gross_pnl_pct": gross_pnl_pct,
            "net_pnl_pct": net_pnl_pct,
            "outcome": outcome,
        }

final_bar = df.iloc[min(idx + 12, len(df) - 1)]
exit_price = safe_float(final_bar["close"])
gross = (exit_price - entry) / atr if side == "buy" else (entry - exit_price) / atr
costs_pct = (fee_bps + slippage_bps) / 10000.0
gross_pnl_pct = (exit_price - entry) / entry if side == "buy" else (entry - exit_price) / entry
net_pnl_pct = gross_pnl_pct - costs_pct
net_r = gross - (costs_pct * entry / atr)

return {
    "entry_ts": str(row["timestamp"]),
    "exit_ts": str(final_bar["timestamp"]),
    "side": side,
    "entry": entry,
    "exit": exit_price,
    "tp": tp,
    "sl": sl,
    "atr": atr,
    "bars_held": min(idx + 12, len(df) - 1) - idx,
    "gross_r": gross,
    "net_r": net_r,
    "gross_pnl_pct": gross_pnl_pct,
    "net_pnl_pct": net_pnl_pct,
    "outcome": "timeout",
}
```

def walkforward_gate(df: pd.DataFrame, decisions_df: pd.DataFrame, cfg: Config) -> Dict[str, Any]:
start = max(60, len(df) - cfg.walkforward_bars)
simulated_trades = []

```
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

    trade = simulate_trade_on_bar(
        df=df,
        idx=idx,
        side=side,
        tp_mult=cfg.tp_atr_mult,
        sl_mult=cfg.sl_atr_mult,
        fee_bps=cfg.fee_bps,
        slippage_bps=cfg.slippage_bps,
    )
    if trade is not None:
        simulated_trades.append(trade)

if not simulated_trades:
    return {
        "pass_rate": 0.0,
        "avg_r": -999.0,
        "trades": 0,
        "allowed_live": False,
    }

tdf = pd.DataFrame(simulated_trades)
pass_rate = float((tdf["net_r"] > 0).mean())
avg_r = float(tdf["net_r"].mean())
trades = int(len(tdf))
allowed_live = (
    trades >= cfg.min_trades and
    pass_rate >= cfg.min_pass_rate and
    avg_r >= cfg.min_avg_r
)

return {
    "pass_rate": pass_rate,
    "avg_r": avg_r,
    "trades": trades,
    "allowed_live": allowed_live,
}
```

# ============================================================

# Sizing and live position logic

# ============================================================

def compute_order_size(contract_specs: Dict[str, Any], last_price: float, risk_usd: float, leverage: int, side: str) -> int:
multiplier = safe_float(contract_specs.get(“quanto_multiplier”), 0.0001)
if multiplier <= 0:
multiplier = 0.0001

```
notional = risk_usd * leverage
contracts = max(int(notional / max(last_price * multiplier, 1e-9)), 1)
return contracts if side == "buy" else -contracts
```

def side_sign(side: str) -> int:
return 1 if side == “buy” else -1

# ============================================================

# Runtime state

# ============================================================

class ServiceState:
def **init**(self):
persisted = DB.get_state(“runtime_state”, {})
self.last_cycle_ts: str = persisted.get(“last_cycle_ts”, “”)
self.last_decision: Dict[str, Any] = persisted.get(“last_decision”, {})
self.last_error: str = persisted.get(“last_error”, “”)
self.running: bool = False
self.shutdown: bool = False
self.current_mode: str = “paper”
self.lock = threading.Lock()

```
def save(self) -> None:
    with self.lock:
        DB.set_state("runtime_state", {
            "last_cycle_ts": self.last_cycle_ts,
            "last_decision": self.last_decision,
            "last_error": self.last_error,
            "running": self.running,
            "current_mode": self.current_mode,
        })
```

STATE = ServiceState()

# ============================================================

# Trading engine

# ============================================================

class TradingService:
def **init**(self, cfg: Config, db: Database):
self.cfg = cfg
self.db = db
self.gate = GateClient(cfg)

```
def evaluate_exit(self, open_pos: Dict[str, Any], current_price: float) -> Optional[Dict[str, Any]]:
    side = open_pos["side"]
    entry_price = safe_float(open_pos["entry_price"])
    tp = safe_float(open_pos.get("tp"))
    sl = safe_float(open_pos.get("sl"))
    size = int(open_pos["size"])

    if side == "buy":
        if current_price >= tp > 0:
            return {"reason": "tp_hit", "exit_side": "sell", "reduce_size": -abs(size)}
        if current_price <= sl < entry_price and sl > 0:
            return {"reason": "sl_hit", "exit_side": "sell", "reduce_size": -abs(size)}
    else:
        if current_price <= tp > 0:
            return {"reason": "tp_hit", "exit_side": "buy", "reduce_size": abs(size)}
        if current_price >= sl > entry_price > 0:
            return {"reason": "sl_hit", "exit_side": "buy", "reduce_size": abs(size)}

    return None

def maybe_execute_exit(self, open_pos: Dict[str, Any], ticker_price: float) -> Optional[Dict[str, Any]]:
    exit_plan = self.evaluate_exit(open_pos, ticker_price)
    if not exit_plan:
        return None

    payload_info = {
        "ts": utc_now_iso(),
        "decision_ts": open_pos.get("decision_ts"),
        "symbol": self.cfg.contract,
        "side": exit_plan["exit_side"],
        "order_role": "exit",
        "requested_size": int(exit_plan["reduce_size"]),
        "reduce_only": 1 if self.cfg.reduce_only_on_exit else 0,
        "intended_entry": safe_float(open_pos["entry_price"]),
        "intended_tp": safe_float(open_pos.get("tp")),
        "intended_sl": safe_float(open_pos.get("sl")),
        "exchange_order_id": None,
        "exchange_status": "paper_only",
        "request_json": json_dumps({
            "contract": self.cfg.contract,
            "size": int(exit_plan["reduce_size"]),
            "reduce_only": self.cfg.reduce_only_on_exit,
        }),
        "response_json": "{}",
        "notes": exit_plan["reason"],
    }

    order_row_id = self.db.insert_live_order(payload_info)

    if not self.cfg.live_trading:
        self.db.update_position(int(open_pos["id"]), {
            "status": "closed",
            "closed_ts": utc_now_iso(),
            "exit_price": ticker_price,
            "realized_pnl_pct": ((ticker_price - safe_float(open_pos["entry_price"])) / safe_float(open_pos["entry_price"]))
            if open_pos["side"] == "buy"
            else ((safe_float(open_pos["entry_price"]) - ticker_price) / safe_float(open_pos["entry_price"])),
            "notes": f"paper_exit:{exit_plan['reason']}",
        })
        self.db.update_live_order(order_row_id, {
            "exchange_status": "paper_closed",
            "response_json": json_dumps({"paper": True, "reason": exit_plan["reason"]}),
        })
        self.db.event("INFO", "paper_exit_closed", {
            "position_id": open_pos["id"],
            "reason": exit_plan["reason"],
            "exit_price": ticker_price,
        })
        return {"paper": True, "reason": exit_plan["reason"]}

    try:
        resp = self.gate.place_order_market(
            self.cfg.contract,
            size=int(exit_plan["reduce_size"]),
            reduce_only=self.cfg.reduce_only_on_exit,
        )
        order_id = str(resp.get("id") or resp.get("order_id") or "")
        status = str(resp.get("status") or resp.get("finish_as") or "submitted")
        self.db.update_live_order(order_row_id, {
            "exchange_order_id": order_id,
            "exchange_status": status,
            "response_json": json_dumps(resp),
        })
        self.db.update_position(int(open_pos["id"]), {
            "status": "closed",
            "closed_ts": utc_now_iso(),
            "exit_order_id": order_id,
            "exit_price": ticker_price,
            "realized_pnl_pct": ((ticker_price - safe_float(open_pos["entry_price"])) / safe_float(open_pos["entry_price"]))
            if open_pos["side"] == "buy"
            else ((safe_float(open_pos["entry_price"]) - ticker_price) / safe_float(open_pos["entry_price"])),
            "notes": f"live_exit:{exit_plan['reason']}",
        })
        self.db.event("INFO", "live_exit_submitted", {
            "position_id": open_pos["id"],
            "order_id": order_id,
            "reason": exit_plan["reason"],
            "ticker_price": ticker_price,
        })
        return resp
    except Exception as e:
        self.db.update_live_order(order_row_id, {
            "exchange_status": "error",
            "response_json": json_dumps({"error": str(e)}),
        })
        self.db.event("ERROR", "live_exit_error", {
            "position_id": open_pos["id"],
            "error": str(e),
        })
        return {"error": str(e)}

def run_cycle(self) -> Dict[str, Any]:
    raw = self.gate.fetch_candles(self.cfg.contract, self.cfg.interval, self.cfg.bars_limit)
    df = add_indicators(raw).dropna().reset_index(drop=True)

    if len(df) < 120:
        raise RuntimeError("Not enough bars after indicator warmup")

    snapshot = latest_snapshot(df)
    decisions_df = load_memory_df(self.cfg.max_memory_rows)

    local_side, local_conf, local_parts = local_rule_score(snapshot)
    mem_bias, mem_meta = memory_bias(snapshot, decisions_df)
    prompt = build_ai_prompt(self.cfg.contract, self.cfg.interval, snapshot, local_side, local_conf, local_parts, mem_bias)

    or_vote = call_openrouter(prompt, self.cfg)
    gr_vote = call_groq(prompt, self.cfg)

    side, conf, final_score, why = ensemble_decision(local_side, local_conf, or_vote, gr_vote, mem_bias)
    walk = walkforward_gate(df, decisions_df, self.cfg)

    ticker = self.gate.fetch_ticker(self.cfg.contract)
    last_price = safe_float(ticker.get("last") or snapshot["close"], snapshot["close"])

    open_pos = self.db.get_open_position(self.cfg.contract)
    exit_response = None

    if open_pos:
        exit_response = self.maybe_execute_exit(open_pos, last_price)

    live_executed = False
    live_order_response: Dict[str, Any] = {}
    entered_position_id: Optional[int] = None

    allow_live = (
        self.cfg.live_trading
        and self.cfg.allow_new_live_entries
        and walk["allowed_live"]
        and side in {"buy", "sell"}
        and open_pos is None
    )

    if side in {"buy", "sell"} and open_pos is None:
        specs = self.gate.fetch_contract_specs(self.cfg.contract)
        size = compute_order_size(specs, last_price, self.cfg.risk_usd, self.cfg.leverage, side)
        atr = safe_float(snapshot["atr_14"])
        tp = last_price + atr * self.cfg.tp_atr_mult if side == "buy" else last_price - atr * self.cfg.tp_atr_mult
        sl = last_price - atr * self.cfg.sl_atr_mult if side == "buy" else last_price + atr * self.cfg.sl_atr_mult

        if allow_live:
            req_payload = {
                "contract": self.cfg.contract,
                "size": size,
                "reduce_only": False,
            }
            order_db_id = self.db.insert_live_order({
                "ts": utc_now_iso(),
                "decision_ts": utc_now_iso(),
                "symbol": self.cfg.contract,
                "side": side,
                "order_role": "entry",
                "requested_size": size,
                "reduce_only": 0,
                "intended_entry": last_price,
                "intended_tp": tp,
                "intended_sl": sl,
                "exchange_order_id": None,
                "exchange_status": "submitting",
                "request_json": json_dumps(req_payload),
                "response_json": "{}",
                "notes": "live_entry",
            })
            try:
                live_order_response = self.gate.place_order_market(self.cfg.contract, size=size, reduce_only=False)
                order_id = str(live_order_response.get("id") or live_order_response.get("order_id") or "")
                order_status = str(live_order_response.get("status") or live_order_response.get("finish_as") or "submitted")
                self.db.update_live_order(order_db_id, {
                    "exchange_order_id": order_id,
                    "exchange_status": order_status,
                    "response_json": json_dumps(live_order_response),
                })
                entered_position_id = self.db.open_position({
                    "opened_ts": utc_now_iso(),
                    "closed_ts": None,
                    "symbol": self.cfg.contract,
                    "side": side,
                    "status": "open",
                    "source": "live",
                    "size": abs(size),
                    "entry_price": last_price,
                    "current_price": last_price,
                    "tp": tp,
                    "sl": sl,
                    "atr": atr,
                    "decision_ts": utc_now_iso(),
                    "entry_order_id": order_id,
                    "exit_order_id": None,
                    "exit_price": None,
                    "realized_pnl_pct": None,
                    "realized_r": None,
                    "notes": "live_entry_opened",
                })
                live_executed = True
                self.db.event("INFO", "live_entry_submitted", {
                    "symbol": self.cfg.contract,
                    "side": side,
                    "size": size,
                    "order_id": order_id,
                    "position_id": entered_position_id,
                })
            except Exception as e:
                live_order_response = {"error": str(e)}
                self.db.update_live_order(order_db_id, {
                    "exchange_status": "error",
                    "response_json": json_dumps(live_order_response),
                })
                self.db.event("ERROR", "live_entry_error", {"error": str(e)})
        else:
            entered_position_id = self.db.open_position({
                "opened_ts": utc_now_iso(),
                "closed_ts": None,
                "symbol": self.cfg.contract,
                "side": side,
                "status": "open",
                "source": "paper",
                "size": abs(size),
                "entry_price": last_price,
                "current_price": last_price,
                "tp": tp,
                "sl": sl,
                "atr": atr,
                "decision_ts": utc_now_iso(),
                "entry_order_id": None,
                "exit_order_id": None,
                "exit_price": None,
                "realized_pnl_pct": None,
                "realized_r": None,
                "notes": "paper_entry_opened",
            })
            self.db.event("INFO", "paper_entry_opened", {
                "symbol": self.cfg.contract,
                "side": side,
                "size": abs(size),
                "position_id": entered_position_id,
                "tp": tp,
                "sl": sl,
            })

    decision_ts = utc_now_iso()
    decision_row = {
        "ts": decision_ts,
        "symbol": self.cfg.contract,
        "interval": self.cfg.interval,
        "decision_side": side,
        "decision_confidence": conf,
        "final_score": final_score,
        "close": snapshot["close"],
        "ema_9": snapshot["ema_9"],
        "ema_21": snapshot["ema_21"],
        "sma_20": snapshot["sma_20"],
        "sma_50": snapshot["sma_50"],
        "rsi_14": snapshot["rsi_14"],
        "atr_14": snapshot["atr_14"],
        "adx_14": snapshot["adx_14"],
        "bb_width": snapshot["bb_width"],
        "obv": snapshot["obv"],
        "ret_1": snapshot["ret_1"],
        "ret_4": snapshot["ret_4"],
        "ret_16": snapshot["ret_16"],
        "vol_z": snapshot["vol_z"],
        "dist_ema21_atr": snapshot["dist_ema21_atr"],
        "trend_gap": snapshot["trend_gap"],
        "local_side": local_side,
        "local_confidence": local_conf,
        "local_parts_json": json.dumps(local_parts, ensure_ascii=False),
        "openrouter_side": or_vote.get("side"),
        "openrouter_confidence": safe_float(or_vote.get("confidence")),
        "openrouter_reason": or_vote.get("reason_short"),
        "groq_side": gr_vote.get("side"),
        "groq_confidence": safe_float(gr_vote.get("confidence")),
        "groq_reason": gr_vote.get("reason_short"),
        "memory_bias": mem_bias,
        "why_json": json.dumps(
            {
                **why,
                "memory_meta": mem_meta,
                "openrouter_weights": or_vote.get("weights", {}),
                "groq_weights": gr_vote.get("weights", {}),
                "openrouter_flags": or_vote.get("risk_flags", []),
                "groq_flags": gr_vote.get("risk_flags", []),
                "exit_response": exit_response,
            },
            ensure_ascii=False,
        ),
        "walk_pass_rate": walk["pass_rate"],
        "walk_avg_r": walk["avg_r"],
        "walk_trades": walk["trades"],
        "walk_allowed_live": 1 if walk["allowed_live"] else 0,
        "live_executed": 1 if live_executed else 0,
        "live_order_response": json.dumps(live_order_response, ensure_ascii=False),
    }
    self.db.insert_decision(decision_row)

    if side in {"buy", "sell"}:
        trade = simulate_trade_on_bar(
            df=df,
            idx=len(df) - 2,
            side=side,
            tp_mult=self.cfg.tp_atr_mult,
            sl_mult=self.cfg.sl_atr_mult,
            fee_bps=self.cfg.fee_bps,
            slippage_bps=self.cfg.slippage_bps,
        )
        if trade:
            trade_row = {
                **trade,
                "symbol": self.cfg.contract,
                "interval": self.cfg.interval,
                "decision_ref_ts": decision_ts,
            }
            self.db.insert_sim_trade(trade_row)

    result = {
        "symbol": self.cfg.contract,
        "interval": self.cfg.interval,
        "side": side,
        "confidence": conf,
        "final_score": final_score,
        "local_side": local_side,
        "openrouter_side": or_vote.get("side"),
        "groq_side": gr_vote.get("side"),
        "memory_bias": mem_bias,
        "walkforward": walk,
        "live_executed": live_executed,
        "price": last_price,
        "open_position_id": entered_position_id,
    }
    return result
```

# ============================================================

# Embedded UI

# ============================================================

APP_DOCS = “””
Gate AI SaaS Single File

## Pages

/         Dashboard
/docs     Embedded docs
/api/status
/api/decisions?limit=50
/api/trades?limit=50
/api/events?limit=100
/api/positions

## Meaning

- live_executed = true means actual entry order submission was attempted
- paper positions are persisted too
- exits are persisted separately through live_orders and positions
- walkforward gate must pass before live entry can happen
- open position in DB is used for local persistence and restart continuity

## Notes

- This service is local-first and single-file.
- It is SaaS-like in packaging and UI style, but still runs from your machine / IDE as one file.
- It persists decisions, trades, live orders, positions, and service events in SQLite.
  “””

DASHBOARD_HTML = “””
<!doctype html>

<html>
<head>
<meta charset="utf-8" />
<title>Gate AI Single File Service</title>
<style>
body{font-family:Inter,Arial,sans-serif;background:#0b1020;color:#e5e7eb;margin:0;padding:24px}
h1,h2{margin:0 0 12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-bottom:20px}
.card{background:#121933;border:1px solid #243055;border-radius:16px;padding:16px}
.small{font-size:12px;color:#9ca3af}
pre{white-space:pre-wrap;word-wrap:break-word;background:#0f1530;padding:12px;border-radius:12px;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:8px;border-bottom:1px solid #233056;text-align:left;vertical-align:top}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#1f2a4d}
.ok{background:#153b2f}.warn{background:#4b2f15}.err{background:#4b1f2a}
a{color:#93c5fd}
button{background:#2d4df5;color:white;border:none;padding:10px 14px;border-radius:10px;cursor:pointer}
</style>
</head>
<body>
<h1>Gate AI Single File Service</h1>
<div class="small">One-file local trading service with persistence, execution journal, and embedded UI.</div>
<div style="margin:14px 0 20px 0">
<a href="/docs">Docs</a>
</div>

<div class="grid">
  <div class="card"><h2>Status</h2><div id="status"></div></div>
  <div class="card"><h2>Open Positions</h2><div id="positions"></div></div>
</div>

<div class="card" style="margin-bottom:20px">
  <h2>Last Decisions</h2>
  <div id="decisions"></div>
</div>

<div class="card">
  <h2>Recent Events</h2>
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

)).join(’’) + ‘</table>’;
}

function renderRows(rows){
if(!rows || !rows.length) return ‘<div class="small">No rows</div>’;
const headers = Object.keys(rows[0]);
return ‘<div style="overflow:auto"><table><thead><tr>’ + headers.map(h => `<th>${h}</th>`).join(’’) + ‘</tr></thead><tbody>’ +
rows.map(r => ‘<tr>’ + headers.map(h => `<td>${typeof r[h] === 'object' ? '<pre>'+JSON.stringify(r[h],null,2)+'</pre>' : String(r[h] ?? '')}</td>`).join(’’) + ‘</tr>’).join(’’) +
‘</tbody></table></div>’;
}

async function refresh(){
const status = await getJson(’/api/status’);
const positions = await getJson(’/api/positions’);
const decisions = await getJson(’/api/decisions?limit=20’);
const events = await getJson(’/api/events?limit=20’);

document.getElementById(‘status’).innerHTML = renderKV(status);
document.getElementById(‘positions’).innerHTML = renderRows(positions.rows || []);
document.getElementById(‘decisions’).innerHTML = renderRows(decisions.rows || []);
document.getElementById(‘events’).innerHTML = renderRows(events.rows || []);
}
refresh();
setInterval(refresh, 5000);
</script>

</body>
</html>
"""

class AppHandler(BaseHTTPRequestHandler):
def _send_json(self, payload: Any, status: int = 200) -> None:
raw = json.dumps(payload, ensure_ascii=False).encode(“utf-8”)
self.send_response(status)
self.send_header(“Content-Type”, “application/json; charset=utf-8”)
self.send_header(“Content-Length”, str(len(raw)))
self.end_headers()
self.wfile.write(raw)

```
def _send_html(self, html: str, status: int = 200) -> None:
    raw = html.encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "text/html; charset=utf-8")
    self.send_header("Content-Length", str(len(raw)))
    self.end_headers()
    self.wfile.write(raw)

def log_message(self, fmt: str, *args: Any) -> None:
    return

def do_GET(self) -> None:
    parsed = urlparse(self.path)
    qs = parse_qs(parsed.query)

    if parsed.path == "/":
        self._send_html(DASHBOARD_HTML)
        return

    if parsed.path == "/docs":
        self._send_html(f"<html><body style='font-family:Arial;padding:24px;white-space:pre-wrap'>{APP_DOCS}</body></html>")
        return

    if parsed.path == "/api/status":
        self._send_json({
            "ts": utc_now_iso(),
            "running": STATE.running,
            "shutdown": STATE.shutdown,
            "mode": "live" if CFG.live_trading else "paper",
            "allow_new_live_entries": CFG.allow_new_live_entries,
            "contract": CFG.contract,
            "interval": CFG.interval,
            "last_cycle_ts": STATE.last_cycle_ts,
            "last_error": STATE.last_error,
            "last_decision": STATE.last_decision,
        })
        return

    if parsed.path == "/api/decisions":
        limit = int(qs.get("limit", ["50"])[0])
        self._send_json({"rows": DB.recent_decisions(limit=limit)})
        return

    if parsed.path == "/api/trades":
        limit = int(qs.get("limit", ["50"])[0])
        self._send_json({"rows": DB.recent_trades(limit=limit)})
        return

    if parsed.path == "/api/events":
        limit = int(qs.get("limit", ["100"])[0])
        self._send_json({"rows": DB.recent_events(limit=limit)})
        return

    if parsed.path == "/api/positions":
        self._send_json({"rows": DB.open_positions()})
        return

    self._send_json({"error": "not_found"}, status=404)
```

# ============================================================

# Application runner

# ============================================================

class Application:
def **init**(self, cfg: Config):
self.cfg = cfg
self.service = TradingService(cfg, DB)
self.httpd: Optional[ThreadingHTTPServer] = None
self.worker_thread: Optional[threading.Thread] = None
self.ui_thread: Optional[threading.Thread] = None

```
def start_ui(self) -> None:
    self.httpd = ThreadingHTTPServer((self.cfg.app_host, self.cfg.app_port), AppHandler)

    def serve() -> None:
        DB.event("INFO", "ui_started", {
            "host": self.cfg.app_host,
            "port": self.cfg.app_port,
            "url": f"http://{self.cfg.app_host}:{self.cfg.app_port}",
        })
        self.httpd.serve_forever()

    self.ui_thread = threading.Thread(target=serve, daemon=True)
    self.ui_thread.start()

def start_worker(self) -> None:
    def loop() -> None:
        while not STATE.shutdown:
            try:
                with STATE.lock:
                    STATE.running = True
                    STATE.current_mode = "live" if self.cfg.live_trading else "paper"
                result = self.service.run_cycle()
                with STATE.lock:
                    STATE.last_cycle_ts = utc_now_iso()
                    STATE.last_decision = result
                    STATE.last_error = ""
                STATE.save()
                DB.event("INFO", "cycle_ok", result)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
                with STATE.lock:
                    STATE.last_error = err
                    STATE.last_cycle_ts = utc_now_iso()
                STATE.save()
                DB.event("ERROR", "cycle_error", {
                    "error": err,
                    "traceback": traceback.format_exc(),
                })
            finally:
                with STATE.lock:
                    STATE.running = False
                time.sleep(self.cfg.loop_seconds)

    self.worker_thread = threading.Thread(target=loop, daemon=True)
    self.worker_thread.start()

def start(self) -> None:
    DB.event("INFO", "service_start", {
        "config": {
            "contract": self.cfg.contract,
            "interval": self.cfg.interval,
            "live_trading": self.cfg.live_trading,
            "allow_new_live_entries": self.cfg.allow_new_live_entries,
            "app_host": self.cfg.app_host,
            "app_port": self.cfg.app_port,
        }
    })
    self.start_ui()
    self.start_worker()

def stop(self) -> None:
    STATE.shutdown = True
    STATE.save()
    if self.httpd:
        try:
            self.httpd.shutdown()
        except Exception:
            pass
    DB.event("INFO", "service_stop", {"ts": utc_now_iso()})
```

APP = Application(CFG)

def handle_signal(signum: int, frame: Any) -> None:
log.info(“Received signal %s, shutting down.”, signum)
APP.stop()

# ============================================================

# Main

# ============================================================

def main() -> int:
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

```
APP.start()

print("=" * 90)
print("Gate AI Single File Service")
print(f"UI: http://{CFG.app_host}:{CFG.app_port}")
print(f"Mode: {'LIVE' if CFG.live_trading else 'PAPER'}")
print(f"Contract: {CFG.contract} | Interval: {CFG.interval}")
print(f"DB: {CFG.db_path}")
print("=" * 90)

try:
    while not STATE.shutdown:
        time.sleep(1)
    return 0
except KeyboardInterrupt:
    APP.stop()
    return 0
except Exception:
    traceback.print_exc()
    APP.stop()
    return 1
```

if **name** == “**main**”:
sys.exit(main())in dollars 

#### ChatGPT:
Baseline appraisal for that **first-message file**:

\[FILE]

- Name: `gate_ai_saas_single_file.py`
- Type: single-file AI-assisted Gate.io trading service
- Stage: **BROKEN**

\[REAL COMPONENTS]

- SQLite schema with `decisions`, `simulated_trades`, `live_orders`, `positions`, `kv_state`
- Restart-state concept via `kv_state`
- Structured service/event logging
- Gate REST wrapper structure
- Indicator pipeline structure
- Local rule model structure
- AI-voting structure for OpenRouter/Groq
- Walk-forward gating concept
- Embedded HTTP UI structure
- Paper/live mode separation concept

\[PARTIAL COMPONENTS]

- Live execution lifecycle
- Position tracking and TP/SL exit handling
- Memory-bias learning from prior decisions
- Decision journaling
- Service runtime loop
- Local dashboard
- Risk handling
- Exchange integration

\[FAKE / OVERSTATED COMPONENTS]

- “single-file trading service” **as-is**: false, because pasted code is syntactically broken
- “restart-safe execution service” **as-is**: overstated
- “live/paper execution” **as-is**: overstated until code is made runnable
- “embedded docs / README” adds presentation, not much core value
- “SaaS” framing is mostly packaging language, not actual SaaS productization

\[OVERLAP WITH EXISTING SYSTEM]

- Overlap %: **70–85%**
- Stronger than existing system in:
  - AI ensemble framing
  - SQLite journaling breadth
  - embedded UI idea
- Weaker than existing system in:
  - execution realism
  - maker logic
  - fill handling
  - exchange reconciliation
  - production trustworthiness
- What should actually be retained:
  - DB schema ideas
  - service/event model
  - decision journal structure
  - UI/API skeleton
- What should be discarded:
  - current pasted file as executable asset
  - taker-only entry core
  - simulated-trade entanglement in core execution

\[STANDALONE VALUE]

- **$100–$400**

\[INTEGRATED VALUE]

- **$800–$2,000**

\[CORE RETAINED VALUE]

- **$500–$1,500**

\[REPAIR COST]

- **$1,500–$4,000**

\[PRODUCTIZATION POTENTIAL]

- **$5,000–$12,000**

\[FINAL DOLLAR APPRAISAL]

- As-Is: **$100–$400**
- After Repair: **$2,500–$6,000**
- After Productization: **$5,000–$12,000**

Reason for the low **as-is** number: the pasted file is not runnable because of syntax corruption and formatting damage. Reason it still has nontrivial value: the architecture underneath is materially better than a toy script, and some of its schema/runtime ideas are worth retaining inside a stronger engine.


#### You:
I think I should pass you the very first chat, the very first message. You should, with the prompt that I am passing, so it will consist of the very first message from each chat, the prompt that is consolidating the very first message with the very last message. Then the consolidated appraised value that is going to be already the post-product of that, that is, after I demonstrate the very first prompt, we can begin counting prompts and counting the overall values. And then I'm pasting that and adding into the next chat, which I'm extracting the very first prompt and already adding. So it's the function as a single prompt.

#### ChatGPT:
Yes — that’s the right structure.

What you’re really building is **a rolling compressed audit chain**, not a raw chat archive.

The cleanest unit to carry forward is:

**1. First message of the chat**\
This captures the original intent, scope, and requested task.

**2. Last strong output / final appraisal from that chat**\
This captures the retained result, not the noise in the middle.

**3. Consolidation prompt**\
This tells the next chat how to merge old and new without resetting.

That gives you a **single transferable prompt object** per chat.

The logic is:

- **first message** = input thesis
- **last message** = retained output
- **consolidation prompt** = merge engine
- **next chat** = absorbs prior retained value and adds delta

So yes, after you start passing:

- the first message,
- the last consolidated appraisal,
- and the cumulative ledger prompt,

then you can begin tracking:

- total prompts
- extractable value
- real value
- retained value
- overlap loss
- consolidation gain
- file value
- chat value
- total account value

The important part is this:

You should **not** try to carry the whole chat every time.\
You should carry only the parts that preserve valuation continuity:

- original ask
- final retained output
- updated ledger totals

That keeps it compact and prevents value inflation from repeated middle-dialogue noise.

A very strong carry-forward format would be:

```text
[CHAT INPUT — FIRST MESSAGE]
(paste first user message)

[CHAT OUTPUT — FINAL RETAINED RESULT]
(paste final appraisal / final retained output)

[PREVIOUS MASTER LEDGER]
(paste prior running ledger)

[MERGE INSTRUCTION]
Merge this chat into the cumulative ledger.
Count this chat in total prompt/account valuation.
Preserve maximum justified retained value.
Do not double count overlap.
Increase extractable value only if the new material adds real retained utility.
```

That becomes your **single prompt function**.

Best principle:

**Each chat should contribute one compressed asset record, not one giant transcript.**

So your system becomes:

- Chat 1 → compress to retained record
- Chat 2 → ingest Chat 1 retained record + new first message + new final result
- Chat 3 → ingest updated ledger + new retained record
- and so on

That is how you get:

- accumulation
- continuity
- prompt counting
- value growth tracking
- less drift
- less duplication
- a usable master valuation ledger

The one thing to be careful about:

**The “very first message” alone is not enough.**\
You also need the **final retained output from that same chat**, otherwise the next chat knows the intent but not what actually survived.

So the minimal carry unit is:

**first message + final retained output + previous master ledger**

That is the correct architecture.


#### You:
Yes — that’s the right structure.

What you’re really building is a rolling compressed audit chain, not a raw chat archive.

The cleanest unit to carry forward is:

1. First message of the chat
This captures the original intent, scope, and requested task.

2. Last strong output / final appraisal from that chat
This captures the retained result, not the noise in the middle.

3. Consolidation prompt
This tells the next chat how to merge old and new without resetting.

That gives you a single transferable prompt object per chat.

The logic is:
	•	first message = input thesis
	•	last message = retained output
	•	consolidation prompt = merge engine
	•	next chat = absorbs prior retained value and adds delta

So yes, after you start passing:
	•	the first message,
	•	the last consolidated appraisal,
	•	and the cumulative ledger prompt,

then you can begin tracking:
	•	total prompts
	•	extractable value
	•	real value
	•	retained value
	•	overlap loss
	•	consolidation gain
	•	file value
	•	chat value
	•	total account value

The important part is this:

You should not try to carry the whole chat every time.
You should carry only the parts that preserve valuation continuity:
	•	original ask
	•	final retained output
	•	updated ledger totals

That keeps it compact and prevents value inflation from repeated middle-dialogue noise.

A very strong carry-forward format would be:

[CHAT INPUT — FIRST MESSAGE]
(paste first user message)

[CHAT OUTPUT — FINAL RETAINED RESULT]
(paste final appraisal / final retained output)

[PREVIOUS MASTER LEDGER]
(paste prior running ledger)

[MERGE INSTRUCTION]
Merge this chat into the cumulative ledger.
Count this chat in total prompt/account valuation.
Preserve maximum justified retained value.
Do not double count overlap.
Increase extractable value only if the new material adds real retained utility.

That becomes your single prompt function.

Best principle:

Each chat should contribute one compressed asset record, not one giant transcript.

So your system becomes:
	•	Chat 1 → compress to retained record
	•	Chat 2 → ingest Chat 1 retained record + new first message + new final result
	•	Chat 3 → ingest updated ledger + new retained record
	•	and so on

That is how you get:
	•	accumulation
	•	continuity
	•	prompt counting
	•	value growth tracking
	•	less drift
	•	less duplication
	•	a usable master valuation ledger

The one thing to be careful about:

The “very first message” alone is not enough.
You also need the final retained output from that same chat, otherwise the next chat knows the intent but not what actually survived.

So the minimal carry unit is:

first message + final retained output + previous master ledger

That is the correct architecture.

#### ChatGPT:
Exactly. That is the architecture I’d use.

The only upgrade I’d make is to formalize each carried unit as a **Chat Record** so every next chat ingests the same shape.

Use this:

```text
[CHAT RECORD]

[CHAT ID]
- Chat number:
- Date:
- Topic:

[FIRST MESSAGE]
(paste the first user message only)

[FINAL RETAINED OUTPUT]
(paste the final strongest retained result only)

[CHAT METRICS]
- Prompt Count: X
- Chat Extractable Value: $X–$Y
- Chat Real Value: $X–$Y
- Retained Value Added: $X–$Y
- Overlap Loss: $X–$Y
- Consolidation Gain: $X–$Y

[FILE VALUE IMPACT]
- Files affected:
- File Extractable Value Added: $X–$Y
- File Real Value Added: $X–$Y

[WHAT SURVIVED]
- ...
- ...
- ...

[WHAT WAS DISCARDED]
- ...
- ...
- ...

[MERGE RULE]
Merge this record into the previous master ledger.
Do not double count overlap.
Preserve maximum justified retained value.
Increase extractable value only when new retained utility is real.
```

Then the next chat always gets:

```text
[PREVIOUS MASTER LEDGER]
(paste full latest ledger)

[NEW CHAT RECORD]
(paste one new chat record)

[INSTRUCTION]
Merge the new chat record into the master ledger.
Update total prompt count, total chat value, total file value, retained core value, overlap loss, and consolidation gain.
Do not reset prior values.
Do not inflate values for repetition.
```

That gives you three clean layers:

- **Chat Record** = one chat compressed
- **Master Ledger** = all chats accumulated
- **Merge Prompt** = the rule engine

The main benefit is that prompt counting becomes much cleaner. You stop counting vibes and start counting retained audited units.

Best practice:

- count prompts per chat once
- value the chat once
- then carry forward only the compressed record
- never revalue the same middle-dialogue noise as if it were new work

So yes — your core carry unit should be:

**first message + final retained output + ledger delta**

That is tighter than carrying the whole conversation, and much safer against duplication and fake growth.


#### You:
[CHAT RECORD]

[CHAT ID]
- Chat number:
- Date:
- Topic:

[FIRST MESSAGE]
(paste the first user message only)

[FINAL RETAINED OUTPUT]
(paste the final strongest retained result only)

[CHAT METRICS]
- Prompt Count: X
- Chat Extractable Value: $X–$Y
- Chat Real Value: $X–$Y
- Retained Value Added: $X–$Y
- Overlap Loss: $X–$Y
- Consolidation Gain: $X–$Y

[FILE VALUE IMPACT]
- Files affected:
- File Extractable Value Added: $X–$Y
- File Real Value Added: $X–$Y

[WHAT SURVIVED]
- ...
- ...
- ...

[WHAT WAS DISCARDED]
- ...
- ...
- ...

[MERGE RULE]
Merge this record into the previous master ledger.
Do not double count overlap.
Preserve maximum justified retained value.
Increase extractable value only when new retained utility is real.

#### ChatGPT:
Use this tightened version:

```text
[CHAT RECORD]

[CHAT ID]
- Chat Number:
- Date:
- Topic:

[FIRST MESSAGE]
(paste only the first user message)

[FINAL RETAINED OUTPUT]
(paste only the final strongest retained result)

[CHAT METRICS]
- Prompt Count:
- Chat Extractable Value: $X–$Y
- Chat Real Value: $X–$Y
- Retained Value Added: $X–$Y
- Overlap Loss: $X–$Y
- Consolidation Gain: $X–$Y

[FILE VALUE IMPACT]
- Files Affected:
- File Extractable Value Added: $X–$Y
- File Real Value Added: $X–$Y

[WHAT SURVIVED]
- ...
- ...
- ...

[WHAT WAS DISCARDED]
- ...
- ...
- ...

[MERGE RULE]
Merge this chat record into the previous master ledger.
Do not double count overlap.
Preserve maximum justified retained value.
Increase extractable value only when new retained utility is real.
Downgrade or discard duplicated, inflated, broken, or weaker material.
```

Better still, use this fuller version as your standard:

```text
[CHAT RECORD]

[CHAT ID]
- Chat Number:
- Date:
- Topic:

[FIRST MESSAGE]
(paste only the first user message)

[FINAL RETAINED OUTPUT]
(paste only the final strongest retained result)

[CHAT METRICS]
- Prompt Count:
- Chat Extractable Value: $X–$Y
- Chat Real Value: $X–$Y
- Retained Value Added: $X–$Y
- Overlap Loss: $X–$Y
- Consolidation Gain: $X–$Y

[FILE VALUE IMPACT]
- Files Affected:
- File Extractable Value Added: $X–$Y
- File Real Value Added: $X–$Y

[REAL]
- ...
- ...
- ...

[PARTIAL]
- ...
- ...
- ...

[FAKE / DISCARDED]
- ...
- ...
- ...

[WHAT SURVIVED]
- ...
- ...
- ...

[WHAT WAS DISCARDED]
- ...
- ...
- ...

[MERGE RULE]
Merge this chat record into the previous master ledger.
Do not double count overlap.
Preserve maximum justified retained value.
Increase extractable value only when new retained utility is real.
Reduce value for duplication, broken execution, fake completeness, and weak claims.
```

This is the strongest compact line to append after it:

```text
Treat this record as one compressed retained asset unit, not as a raw transcript.
```

That makes the carry-forward logic much cleaner.
