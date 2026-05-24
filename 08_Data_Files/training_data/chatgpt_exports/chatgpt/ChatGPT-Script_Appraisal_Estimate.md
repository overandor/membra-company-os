# Script Appraisal Estimate

#### You:
Can you appraise this script in dollars? from __future__ import annotations

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

APP_NAME = "gate-hedged-mm"
VERSION = "3.0-single-file"

GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")
SETTLE = os.getenv("GATE_SETTLE", "usdt").lower()
BASE_URL = os.getenv("GATE_BASE_URL", "https://api.gateio.ws/api/v4")

USE_TESTNET = os.getenv("USE_TESTNET", "0") == "1"
if USE_TESTNET and "GATE_BASE_URL" not in os.environ:
    BASE_URL = "https://fx-api-testnet.gateio.ws/api/v4"

MAX_CONTRACT_NOMINAL_USD = float(os.getenv("MAX_CONTRACT_NOMINAL_USD", "0.10"))
MIN_VOLUME_USDT = float(os.getenv("MIN_VOLUME_USDT", "250000"))
MAX_SYMBOLS = int(os.getenv("MAX_SYMBOLS", "30"))
UNIVERSE_REFRESH_SECONDS = int(os.getenv("UNIVERSE_REFRESH_SECONDS", "30"))

LOOP_SECONDS = float(os.getenv("LOOP_SECONDS", "1.0"))
ORDER_TTL_SECONDS = float(os.getenv("ORDER_TTL_SECONDS", "2.2"))
POST_ONLY_TIF = os.getenv("POST_ONLY_TIF", "poc")

ACCOUNT_BALANCE_USD = float(os.getenv("ACCOUNT_BALANCE_USD", "10.0"))
LEVERAGE = int(os.getenv("LEVERAGE", "3"))
BASE_ORDER_NOTIONAL_USD = float(os.getenv("BASE_ORDER_NOTIONAL_USD", "0.05"))
MAX_PORTFOLIO_GROSS_USD = float(os.getenv("MAX_PORTFOLIO_GROSS_USD", "2.0"))
MAX_PORTFOLIO_NET_USD = float(os.getenv("MAX_PORTFOLIO_NET_USD", "1.0"))
MAX_SYMBOL_GROSS_USD = float(os.getenv("MAX_SYMBOL_GROSS_USD", "0.30"))
MAX_SYMBOL_NET_USD = float(os.getenv("MAX_SYMBOL_NET_USD", "0.20"))
SKEW_FACTOR = float(os.getenv("SKEW_FACTOR", "1.0"))

API_TIMEOUT = float(os.getenv("API_TIMEOUT", "10.0"))
API_RETRIES = int(os.getenv("API_RETRIES", "3"))
API_RETRY_SLEEP = float(os.getenv("API_RETRY_SLEEP", "0.5"))
MAX_CONSECUTIVE_ERRORS = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "10"))
COUNTDOWN_CANCEL_TIMEOUT = int(os.getenv("COUNTDOWN_CANCEL_TIMEOUT", "5"))

STATE_FILE = Path(os.getenv("STATE_FILE", "gate_mm_state.json"))
JSONL_LOG = Path(os.getenv("JSONL_LOG", "gate_mm_events.jsonl"))

DRY_RUN = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(APP_NAME)
_jsonl_lock = threading.Lock()


def now_ts() -> float:
    return time.time()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def event_log(kind: str, **payload: Any) -> None:
    record = {
        "ts": now_iso(),
        "kind": kind,
        "app": APP_NAME,
        "version": VERSION,
        **payload,
    }
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
    with _jsonl_lock:
        with open(JSONL_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
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


def sha512_hex(s: str) -> str:
    return hashlib.sha512(s.encode("utf-8")).hexdigest()


def make_text_tag(*parts: str) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"t-{digest}"[:28]


@dataclass
class ContractMeta:
    symbol: str
    last_price: float
    quanto_multiplier: float
    order_size_min: int
    leverage_min: int
    leverage_max: int
    volume_24h_quote: float
    mark_price_round: int = 8

    @property
    def nominal(self) -> float:
        return self.last_price * self.quanto_multiplier


@dataclass
class BookTop:
    best_bid: float
    best_ask: float
    bid_size_top: float = 0.0
    ask_size_top: float = 0.0


@dataclass
class HedgeInventory:
    long_contracts: int = 0
    short_contracts: int = 0
    long_entry_price: float = 0.0
    short_entry_price: float = 0.0

    def gross_contracts(self) -> int:
        return self.long_contracts + self.short_contracts

    def net_contracts(self) -> int:
        return self.long_contracts - self.short_contracts


@dataclass
class PersistedState:
    cycle: int = 0
    last_universe_refresh: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()

    def load(self) -> PersistedState:
        if not self.path.exists():
            return PersistedState()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return PersistedState(
                cycle=safe_int(data.get("cycle", 0)),
                last_universe_refresh=safe_float(data.get("last_universe_refresh", 0.0)),
                metadata=dict(data.get("metadata", {})),
            )
        except Exception as exc:
            event_log("state_load_error", error=str(exc))
            return PersistedState(metadata={"load_error": str(exc)})

    def save(self, state: PersistedState) -> None:
        tmp = self.path.with_suffix(".tmp")
        raw = json.dumps(asdict(state), indent=2, sort_keys=True, ensure_ascii=False)
        with self.lock:
            tmp.write_text(raw, encoding="utf-8")
            tmp.replace(self.path)


class GateRestClient:
    def __init__(self, key: str, secret: str, base_url: str, settle: str) -> None:
        self.key = key
        self.secret = secret
        self.base_url = base_url.rstrip("/")
        self.settle = settle.lower()
        self.session = requests.Session()

    def _signed_headers(self, method: str, path: str, query_string: str, payload: str) -> Dict[str, str]:
        ts = str(int(time.time()))
        sign_str = f"{method.upper()}\n{path}\n{query_string}\n{sha512_hex(payload)}\n{ts}"
        sign = hmac.new(self.secret.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha512).hexdigest()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "KEY": self.key,
            "Timestamp": ts,
            "SIGN": sign,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        payload_obj: Optional[Dict[str, Any]] = None,
        private: bool = False,
    ) -> Any:
        params = params or {}
        payload_obj = payload_obj or {}
        query_string = "&".join(
            f"{k}={requests.utils.quote(str(v), safe='')}"
            for k, v in sorted(params.items())
            if v is not None
        )
        payload = json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False) if payload_obj else ""
        url = f"{self.base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if private:
            if not self.key or not self.secret:
                raise RuntimeError("Missing GATE_API_KEY / GATE_API_SECRET")
            headers = self._signed_headers(method, path, query_string, payload)

        last_exc: Optional[Exception] = None
        for attempt in range(1, API_RETRIES + 1):
            try:
                r = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    data=payload if payload else None,
                    timeout=API_TIMEOUT,
                )
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:1000]}")
                if not r.text.strip():
                    return None
                return r.json()
            except Exception as exc:
                last_exc = exc
                event_log("api_retry", method=method, path=path, attempt=attempt, error=str(exc))
                if attempt < API_RETRIES:
                    time.sleep(API_RETRY_SLEEP * attempt)
        raise RuntimeError(f"API request failed: {method} {path}: {last_exc}")

    def list_contracts(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/contracts") or []

    def order_book(self, symbol: str, limit: int = 1) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/futures/{self.settle}/order_book",
            params={"contract": symbol, "limit": limit},
        ) or {}

    def ticker(self, symbol: str) -> List[Dict[str, Any]]:
        return self._request(
            "GET",
            f"/futures/{self.settle}/tickers",
            params={"contract": symbol},
        ) or []

    def account(self) -> Dict[str, Any]:
        try:
            return self._request("GET", f"/futures/{self.settle}/accounts", private=True) or {}
        except Exception:
            return self._request("GET", f"/futures/{self.settle}/account", private=True) or {}

    def positions(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/positions", private=True) or []

    def open_orders(self, symbol: str = "") -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"status": "open"}
        if symbol:
            params["contract"] = symbol
        return self._request("GET", f"/futures/{self.settle}/orders", params=params, private=True) or []

    def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/futures/{self.settle}/orders", payload_obj=payload, private=True) or {}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/futures/{self.settle}/orders/{order_id}", private=True) or {}

    def set_leverage(self, symbol: str, leverage: int) -> Any:
        payload = {"leverage": str(leverage), "cross_leverage_limit": str(leverage)}
        return self._request(
            "POST",
            f"/futures/{self.settle}/positions/{symbol}/leverage",
            payload_obj=payload,
            private=True,
        )

    def set_dual_mode(self, enabled: bool) -> Any:
        return self._request(
            "POST",
            f"/futures/{self.settle}/dual_mode",
            payload_obj={"dual_mode": enabled},
            private=True,
        )

    def countdown_cancel_all(self, timeout_seconds: int) -> Any:
        return self._request(
            "POST",
            f"/futures/{self.settle}/countdown_cancel_all",
            payload_obj={"timeout": int(timeout_seconds)},
            private=True,
        )


class HedgeMarketMaker:
    def __init__(self, client: GateRestClient, store: StateStore, state: PersistedState) -> None:
        self.client = client
        self.store = store
        self.state = state
        self.contracts: Dict[str, ContractMeta] = {}
        self.consecutive_errors = 0

    def refresh_universe(self, force: bool = False) -> None:
        now = now_ts()
        if not force and now - self.state.last_universe_refresh < UNIVERSE_REFRESH_SECONDS:
            return

        metas: List[ContractMeta] = []
        for c in self.client.list_contracts():
            try:
                meta = ContractMeta(
                    symbol=str(c.get("name", "")),
                    last_price=safe_float(c.get("last_price", 0.0)),
                    quanto_multiplier=safe_float(c.get("quanto_multiplier", 0.0)),
                    order_size_min=max(1, safe_int(c.get("order_size_min", 1), 1)),
                    leverage_min=max(1, safe_int(c.get("leverage_min", 1), 1)),
                    leverage_max=max(1, safe_int(c.get("leverage_max", 100), 100)),
                    volume_24h_quote=safe_float(c.get("volume_24h_quote", 0.0)),
                    mark_price_round=safe_int(c.get("mark_price_round", 8), 8),
                )
                if meta.last_price <= 0 or meta.quanto_multiplier <= 0:
                    continue
                if meta.nominal <= 0 or meta.nominal > MAX_CONTRACT_NOMINAL_USD:
                    continue
                if meta.volume_24h_quote < MIN_VOLUME_USDT:
                    continue
                metas.append(meta)
            except Exception:
                continue

        metas.sort(key=lambda m: m.volume_24h_quote, reverse=True)
        self.contracts = {m.symbol: m for m in metas[:MAX_SYMBOLS]}
        self.state.last_universe_refresh = now
        self.state.metadata["universe_count"] = len(self.contracts)
        self.store.save(self.state)

        event_log(
            "universe_refresh",
            count=len(self.contracts),
            symbols=list(self.contracts.keys()),
            max_nominal=MAX_CONTRACT_NOMINAL_USD,
        )

    def ensure_exchange_settings(self) -> None:
        if DRY_RUN:
            return
        try:
            self.client.set_dual_mode(True)
            event_log("dual_mode_set", enabled=True)
        except Exception as exc:
            event_log("dual_mode_error", error=str(exc))
        for meta in self.contracts.values():
            lev = int(clamp(LEVERAGE, meta.leverage_min, meta.leverage_max))
            try:
                self.client.set_leverage(meta.symbol, lev)
                event_log("leverage_set", symbol=meta.symbol, leverage=lev)
            except Exception as exc:
                event_log("leverage_error", symbol=meta.symbol, leverage=lev, error=str(exc))

    def fetch_inventory(self) -> Dict[str, HedgeInventory]:
        out: Dict[str, HedgeInventory] = {sym: HedgeInventory() for sym in self.contracts}
        try:
            positions = self.client.positions()
        except Exception as exc:
            event_log("positions_error", error=str(exc))
            return out

        for p in positions:
            symbol = str(p.get("contract", ""))
            if symbol not in out:
                continue

            qty = safe_int(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()
            entry = safe_float(p.get("entry_price", 0.0))
            inv = out[symbol]

            if side_raw in ("long", "buy"):
                inv.long_contracts += abs(qty)
                if entry > 0:
                    inv.long_entry_price = entry
            elif side_raw in ("short", "sell"):
                inv.short_contracts += abs(qty)
                if entry > 0:
                    inv.short_entry_price = entry
            else:
                if qty > 0:
                    inv.long_contracts += qty
                    if entry > 0:
                        inv.long_entry_price = entry
                elif qty < 0:
                    inv.short_contracts += abs(qty)
                    if entry > 0:
                        inv.short_entry_price = entry

            out[symbol] = inv
        return out

    def portfolio_exposure(self, inventory: Dict[str, HedgeInventory]) -> Tuple[float, float]:
        net_usd = 0.0
        gross_usd = 0.0
        for sym, inv in inventory.items():
            meta = self.contracts.get(sym)
            if not meta:
                continue
            long_usd = inv.long_contracts * meta.nominal
            short_usd = inv.short_contracts * meta.nominal
            net_usd += long_usd - short_usd
            gross_usd += long_usd + short_usd
        return net_usd, gross_usd

    def fetch_books(self) -> Dict[str, BookTop]:
        books: Dict[str, BookTop] = {}
        for sym in self.contracts:
            try:
                raw = self.client.order_book(sym, limit=1)
                asks = raw.get("asks", []) or []
                bids = raw.get("bids", []) or []
                best_ask = safe_float(asks[0].get("p", 0.0) if asks else 0.0)
                best_bid = safe_float(bids[0].get("p", 0.0) if bids else 0.0)
                if best_bid > 0 and best_ask > 0 and best_ask >= best_bid:
                    books[sym] = BookTop(
                        best_bid=best_bid,
                        best_ask=best_ask,
                        bid_size_top=safe_float(bids[0].get("s", 0.0) if bids else 0.0),
                        ask_size_top=safe_float(asks[0].get("s", 0.0) if asks else 0.0),
                    )
            except Exception as exc:
                event_log("book_error", symbol=sym, error=str(exc))
        return books

    def cancel_stale_quotes(self) -> None:
        try:
            orders = self.client.open_orders()
        except Exception as exc:
            event_log("open_orders_error", error=str(exc))
            return

        for o in orders:
            order_id = str(o.get("id", ""))
            text = str(o.get("text", ""))
            symbol = str(o.get("contract", ""))
            if not order_id:
                continue
            if not text.startswith("t-"):
                continue
            try:
                created_ts = safe_float(
                    o.get("create_time_ms", 0.0),
                    safe_float(o.get("create_time", 0.0)),
                )
                if created_ts > 1e12:
                    created_ts /= 1000.0
                if created_ts <= 0:
                    created_ts = now_ts()
                if now_ts() - created_ts < ORDER_TTL_SECONDS:
                    continue
                if DRY_RUN:
                    event_log("dry_cancel", order_id=order_id, symbol=symbol, text=text)
                else:
                    self.client.cancel_order(order_id)
                    event_log("cancel_quote", order_id=order_id, symbol=symbol, text=text)
            except Exception as exc:
                event_log("cancel_quote_error", order_id=order_id, symbol=symbol, error=str(exc))

    def contracts_for_notional(self, meta: ContractMeta, notional_usd: float) -> int:
        if meta.nominal <= 0:
            return 0
        raw = int(math.floor(notional_usd / meta.nominal))
        if raw <= 0:
            return 0
        return max(meta.order_size_min, raw)

    def quote_sizes_for_symbol(
        self,
        meta: ContractMeta,
        inv: HedgeInventory,
        portfolio_net_usd: float,
        portfolio_gross_usd: float,
    ) -> Tuple[int, int]:
        symbol_long_usd = inv.long_contracts * meta.nominal
        symbol_short_usd = inv.short_contracts * meta.nominal
        symbol_net_usd = symbol_long_usd - symbol_short_usd
        symbol_gross_usd = symbol_long_usd + symbol_short_usd

        if portfolio_gross_usd >= MAX_PORTFOLIO_GROSS_USD and symbol_gross_usd >= MAX_SYMBOL_GROSS_USD:
            return 0, 0

        buy_notional = BASE_ORDER_NOTIONAL_USD
        sell_notional = BASE_ORDER_NOTIONAL_USD

        symbol_skew = clamp(symbol_net_usd / max(BASE_ORDER_NOTIONAL_USD, 1e-9), -3.0, 3.0)
        portfolio_skew = clamp(portfolio_net_usd / max(BASE_ORDER_NOTIONAL_USD, 1e-9), -3.0, 3.0)

        buy_notional *= clamp(1.0 - max(0.0, symbol_skew) * 0.5 * SKEW_FACTOR, 0.0, 3.0)
        sell_notional *= clamp(1.0 + max(0.0, symbol_skew) * 0.5 * SKEW_FACTOR, 0.0, 3.0)

        buy_notional *= clamp(1.0 - max(0.0, portfolio_skew) * 0.25 * SKEW_FACTOR, 0.0, 3.0)
        sell_notional *= clamp(1.0 + max(0.0, portfolio_skew) * 0.25 * SKEW_FACTOR, 0.0, 3.0)

        if symbol_net_usd >= MAX_SYMBOL_NET_USD:
            buy_notional = 0.0
        if symbol_net_usd <= -MAX_SYMBOL_NET_USD:
            sell_notional = 0.0

        if portfolio_net_usd >= MAX_PORTFOLIO_NET_USD:
            buy_notional = 0.0
        if portfolio_net_usd <= -MAX_PORTFOLIO_NET_USD:
            sell_notional = 0.0

        if symbol_gross_usd >= MAX_SYMBOL_GROSS_USD:
            if symbol_net_usd >= 0:
                buy_notional = 0.0
            if symbol_net_usd <= 0:
                sell_notional = 0.0

        return (
            self.contracts_for_notional(meta, buy_notional),
            self.contracts_for_notional(meta, sell_notional),
        )

    def place_quote(self, symbol: str, side: str, price: float, qty: int) -> None:
        if qty <= 0 or price <= 0:
            return

        signed_size = qty if side == "buy" else -qty
        text = make_text_tag(symbol, side, str(int(time.time())), str(qty), f"{price:.12f}")

        payload: Dict[str, Any] = {
            "contract": symbol,
            "size": signed_size,
            "price": f"{price:.12f}",
            "tif": POST_ONLY_TIF,
            "text": text,
            "reduce_only": False,
        }

        if DRY_RUN:
            event_log("dry_quote", symbol=symbol, side=side, qty=qty, price=price, payload=payload)
            return

        try:
            result = self.client.create_order(payload)
            event_log(
                "quote_placed",
                symbol=symbol,
                side=side,
                qty=qty,
                price=price,
                order_id=str(result.get("id", "")),
                status=str(result.get("status", "")),
                text=text,
            )
        except Exception as exc:
            event_log("quote_error", symbol=symbol, side=side, qty=qty, price=price, error=str(exc))

    def quote_cycle(self) -> None:
        self.refresh_universe()
        inventory = self.fetch_inventory()
        portfolio_net_usd, portfolio_gross_usd = self.portfolio_exposure(inventory)

        self.cancel_stale_quotes()
        books = self.fetch_books()

        for sym, meta in self.contracts.items():
            book = books.get(sym)
            if not book:
                continue

            buy_qty, sell_qty = self.quote_sizes_for_symbol(
                meta,
                inventory.get(sym, HedgeInventory()),
                portfolio_net_usd,
                portfolio_gross_usd,
            )

            if buy_qty > 0:
                self.place_quote(sym, "buy", book.best_bid, buy_qty)
            if sell_qty > 0:
                self.place_quote(sym, "sell", book.best_ask, sell_qty)

        event_log(
            "quote_cycle",
            symbols=len(self.contracts),
            portfolio_net_usd=round(portfolio_net_usd, 8),
            portfolio_gross_usd=round(portfolio_gross_usd, 8),
        )

    def balance(self) -> Dict[str, Any]:
        return self.client.account()

    def positions(self) -> List[Dict[str, Any]]:
        return self.client.positions()

    def book(self, symbol: str) -> Dict[str, Any]:
        return self.client.order_book(symbol, limit=5)

    def cancel_all(self) -> None:
        try:
            orders = self.client.open_orders()
        except Exception as exc:
            event_log("cancel_all_list_error", error=str(exc))
            return

        for o in orders:
            order_id = str(o.get("id", ""))
            symbol = str(o.get("contract", ""))
            if not order_id:
                continue
            try:
                if DRY_RUN:
                    event_log("dry_cancel", order_id=order_id, symbol=symbol)
                else:
                    self.client.cancel_order(order_id)
                    event_log("cancel_all_order", order_id=order_id, symbol=symbol)
            except Exception as exc:
                event_log("cancel_all_order_error", order_id=order_id, symbol=symbol, error=str(exc))

    def flatten_all(self) -> None:
        positions = self.client.positions()
        for p in positions:
            symbol = str(p.get("contract", ""))
            qty = safe_int(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()

            payload: Optional[Dict[str, Any]] = None
            if side_raw == "long":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_long",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "close_long"),
                }
            elif side_raw == "short":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_short",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "close_short"),
                }
            elif qty > 0:
                payload = {
                    "contract": symbol,
                    "size": -abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "sell"),
                }
            elif qty < 0:
                payload = {
                    "contract": symbol,
                    "size": abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "buy"),
                }

            if not payload:
                continue

            try:
                if DRY_RUN:
                    event_log("dry_flatten", payload=payload)
                else:
                    self.client.create_order(payload)
                    event_log("flatten_order", symbol=symbol, payload=payload)
            except Exception as exc:
                event_log("flatten_error", symbol=symbol, error=str(exc))

    def run(self) -> None:
        self.refresh_universe(force=True)
        self.ensure_exchange_settings()

        log.info(
            "Starting %s %s mode=%s settle=%s base_url=%s max_nominal=%.4f loop=%.2fs",
            APP_NAME,
            VERSION,
            "DRY" if DRY_RUN else "LIVE",
            SETTLE,
            BASE_URL,
            MAX_CONTRACT_NOMINAL_USD,
            LOOP_SECONDS,
        )
        event_log(
            "startup",
            mode="DRY" if DRY_RUN else "LIVE",
            settle=SETTLE,
            base_url=BASE_URL,
            max_nominal=MAX_CONTRACT_NOMINAL_USD,
            loop_seconds=LOOP_SECONDS,
        )

        while True:
            cycle_start = now_ts()
            self.state.cycle += 1

            try:
                if not DRY_RUN:
                    try:
                        self.client.countdown_cancel_all(COUNTDOWN_CANCEL_TIMEOUT)
                    except Exception as exc:
                        event_log("countdown_cancel_error", error=str(exc))

                self.quote_cycle()
                self.store.save(self.state)
                self.consecutive_errors = 0

                inv = self.fetch_inventory()
                net_usd, gross_usd = self.portfolio_exposure(inv)
                log.info(
                    "cycle=%d symbols=%d net=%+.6f gross=%.6f",
                    self.state.cycle,
                    len(self.contracts),
                    net_usd,
                    gross_usd,
                )

            except KeyboardInterrupt:
                event_log("shutdown", reason="keyboard_interrupt")
                break
            except Exception as exc:
                self.consecutive_errors += 1
                log.error("Main loop error: %s", exc)
                event_log(
                    "main_loop_error",
                    error=str(exc),
                    traceback=traceback.format_exc(),
                    consecutive_errors=self.consecutive_errors,
                )
                if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    event_log("panic_stop", consecutive_errors=self.consecutive_errors)
                    break

            elapsed = now_ts() - cycle_start
            time.sleep(max(0.0, LOOP_SECONDS - elapsed))

        try:
            self.cancel_all()
        except Exception as exc:
            event_log("shutdown_cancel_error", error=str(exc))


def main() -> None:
    global DRY_RUN

    parser = argparse.ArgumentParser(description="Gate.io hedged market maker")
    parser.add_argument("--dry", action="store_true", help="Dry-run mode")
    parser.add_argument("--live", action="store_true", help="Live mode")
    parser.add_argument("--balance", action="store_true", help="Show account balance")
    parser.add_argument("--positions", action="store_true", help="Show futures positions")
    parser.add_argument("--book", metavar="SYMBOL", default="", help="Show order book")
    parser.add_argument("--cancel-all", action="store_true", help="Cancel all open orders")
    parser.add_argument("--flatten-all", action="store_true", help="Flatten all positions")
    args = parser.parse_args()

    DRY_RUN = not args.live

    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
        sys.stderr.write("Missing GATE_API_KEY / GATE_API_SECRET\n")
        sys.exit(1)

    client = GateRestClient(
        key=GATE_API_KEY,
        secret=GATE_API_SECRET,
        base_url=BASE_URL,
        settle=SETTLE,
    )
    store = StateStore(STATE_FILE)
    state = store.load()
    bot = HedgeMarketMaker(client, store, state)

    if args.balance:
        print(json.dumps(bot.balance(), indent=2, ensure_ascii=False))
        return
    if args.positions:
        print(json.dumps(bot.positions(), indent=2, ensure_ascii=False))
        return
    if args.book:
        print(json.dumps(bot.book(args.book), indent=2, ensure_ascii=False))
        return
    if args.cancel_all:
        bot.cancel_all()
        return
    if args.flatten_all:
        bot.flatten_all()
        return

    bot.run()


if __name__ == "__main__":
    main()

#### ChatGPT:
Yes. As-is, I’d appraise this script at roughly **$300 to $1,500**.

My honest center-of-range estimate: **about $700–$1,000** if someone is buying the code only, with no proven PnL, no deployed infra, no tests, and no evidence it survives live trading.

Why it has value:

- It is not toy code. It has real structure: REST client, signing, retries, state persistence, JSONL event logging, CLI controls, cancel/flatten flows, exposure caps, universe filtering, and a usable control loop.
- It is readable enough to maintain.
- It is targeted at a real venue and real use case, which is worth more than generic boilerplate.

Why the price stays limited:

- **Single-file architecture** lowers perceived quality for commercial buyers.
- **No tests** and no backtest/live validation shown.
- **No websocket market data or fills stream**, so execution quality and state accuracy are weaker than serious MM systems.
- The “hedged market maker” label is a bit generous: it mainly places bid/ask quotes with inventory skew controls, but there is no sophisticated hedge engine, no fill reconciliation layer, no maker/taker fee optimization logic, no adverse-selection model.
- It relies on **top-of-book polling via REST**, which is a meaningful weakness for anything claiming market-making quality.
- No packaging, dashboard, monitoring stack, deployment automation, or multi-account ops layer.
- No demonstrated profitability, Sharpe, drawdown behavior, or production uptime.

How I’d price it in different sale contexts:

**1. Code-only sale**\
**$300–$1,500**\
This is the realistic range for “here is the Python bot source.”

**2. Cleaned up and packaged**\
If you refactor into modules, add tests, docs, sample configs, safer risk controls, and maybe Docker:\
**$1,500–$4,000**

**3. With proven live results**\
If you can show real logs, fills, fees, slippage analysis, and stable PnL over time:\
**$5,000–$20,000+**\
At that point people are no longer buying code; they are buying evidence.

**4. As part of a business/system**\
If this powers a working service, strategy desk, or managed bot product, then code value becomes secondary. The business could be worth much more than the script itself.

My blunt take:
This is **solid indie quant/dev code**, not institutional-grade alpha infrastructure.\
So it is **worth real money**, but not “tens of thousands” by itself.

If I were a buyer, I would probably say:

- **$500–$800** if I’m buying opportunistically
- **$1,000–$1,500** if I specifically need a Gate.io futures prototype and want to save build time

If you want, I can also give you:

- a **brutally honest buyer-style appraisal**
- a **seller-style asking price**
-


#### You:
Make it websoclet rewtire fully

#### ChatGPT:


#### You:
Again try konger longer

#### ChatGPT:
I’m reworking it into a fuller WebSocket-based version with a longer, more production-shaped structure. First I’m checking the current Gate.io futures REST/WebSocket details so I don’t bake in stale endpoints or message formats.


#### ChatGPT:
I’ve got the key bit: Gate’s current docs recommend `futures.order_book_update` or `futures.book_ticker` over the legacy order book feed, and the USDT futures WebSocket URL differs for live vs testnet. I’m shaping the rewrite around WS market data plus a sturdier event loop and local state sync, instead of the old REST-polling quote loop.


#### ChatGPT:
Here’s a longer WebSocket-first rewrite built around Gate futures WS market data and WS trading, with REST used only where the exchange docs require snapshots/metadata for local book sync. ([Gate.com](https://www.gate.com/docs/developers/futures/ws/en/?utm_source=chatgpt.com), [Gate.com](https://www.gate.com/docs/developers/futures/ws/en/?utm_source=chatgpt.com), [Gate.com](https://www.gate.com/docs/developers/futures/ws/en/?utm_source=chatgpt.com))

```python
from __future__ import annotations

"""
gate_ws_hedged_mm.py

Long-form WebSocket-first Gate.io futures market maker rewrite.

Design goals
------------
- WebSocket-first market data:
  - futures.order_book_update for incremental depth
  - REST snapshot bootstrap with with_id=true to sync local books correctly
- WebSocket-first private trading:
  - futures.login
  - futures.order_place
  - futures.order_cancel
  - futures.order_list
- Single-file, but modular enough to maintain
- Dry/live modes
- Universe filtering
- Local in-memory order books
- Quote manager with stale cancel / replace
- Inventory / portfolio skewing
- Risk caps
- JSONL event logging
- State persistence
- Graceful reconnect loops

Install
-------
pip install websockets requests

Example
-------
python gate_ws_hedged_mm.py --dry
python gate_ws_hedged_mm.py --live
python gate_ws_hedged_mm.py --balance
python gate_ws_hedged_mm.py --positions
python gate_ws_hedged_mm.py --cancel-all
python gate_ws_hedged_mm.py --flatten-all

Environment
-----------
GATE_API_KEY=...
GATE_API_SECRET=...
GATE_SETTLE=usdt
USE_TESTNET=0

Optional tuning:
BASE_ORDER_NOTIONAL_USD=0.05
MAX_CONTRACT_NOMINAL_USD=0.10
MIN_VOLUME_USDT=250000
MAX_SYMBOLS=20
ORDER_TTL_SECONDS=2.0
QUOTE_INTERVAL_SECONDS=0.7
TOP_LEVELS=20
WS_BOOK_PUSH=100ms
MAX_PORTFOLIO_GROSS_USD=2.0
MAX_PORTFOLIO_NET_USD=1.0
MAX_SYMBOL_GROSS_USD=0.30
MAX_SYMBOL_NET_USD=0.20
SKEW_FACTOR=1.0
"""

import argparse
import asyncio
import contextlib
import hashlib
import hmac
import json
import logging
import math
import os
import random
import signal
import ssl
import sys
import time
import traceback
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

import requests
import websockets
from websockets.client import WebSocketClientProtocol

APP_NAME = "gate-ws-hedged-mm"
VERSION = "4.0-websocket-single-file"

GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")
SETTLE = os.getenv("GATE_SETTLE", "usdt").lower()

USE_TESTNET = os.getenv("USE_TESTNET", "0") == "1"

REST_BASE_URL = os.getenv("GATE_BASE_URL", "https://api.gateio.ws/api/v4").rstrip("/")
if USE_TESTNET and "GATE_BASE_URL" not in os.environ:
    REST_BASE_URL = "https://fx-api-testnet.gateio.ws/api/v4"

WS_URL = os.getenv("GATE_WS_URL", "").strip()
if not WS_URL:
    if USE_TESTNET:
        if SETTLE == "usdt":
            WS_URL = "wss://ws-testnet.gate.com/v4/ws/futures/usdt"
        else:
            WS_URL = f"wss://fx-ws-testnet.gateio.ws/v4/ws/{SETTLE}"
    else:
        WS_URL = f"wss://fx-ws.gateio.ws/v4/ws/{SETTLE}"

# Universe selection
MAX_CONTRACT_NOMINAL_USD = float(os.getenv("MAX_CONTRACT_NOMINAL_USD", "0.10"))
MIN_VOLUME_USDT = float(os.getenv("MIN_VOLUME_USDT", "250000"))
MAX_SYMBOLS = int(os.getenv("MAX_SYMBOLS", "20"))
UNIVERSE_REFRESH_SECONDS = int(os.getenv("UNIVERSE_REFRESH_SECONDS", "60"))

# Quote timing
QUOTE_INTERVAL_SECONDS = float(os.getenv("QUOTE_INTERVAL_SECONDS", "0.70"))
ORDER_TTL_SECONDS = float(os.getenv("ORDER_TTL_SECONDS", "2.20"))
REPRICE_MIN_BPS = float(os.getenv("REPRICE_MIN_BPS", "0.0"))
WS_BOOK_PUSH = os.getenv("WS_BOOK_PUSH", "100ms")
TOP_LEVELS = int(os.getenv("TOP_LEVELS", "20"))

# Risk
ACCOUNT_BALANCE_USD = float(os.getenv("ACCOUNT_BALANCE_USD", "10.0"))
LEVERAGE = int(os.getenv("LEVERAGE", "3"))
BASE_ORDER_NOTIONAL_USD = float(os.getenv("BASE_ORDER_NOTIONAL_USD", "0.05"))
MAX_PORTFOLIO_GROSS_USD = float(os.getenv("MAX_PORTFOLIO_GROSS_USD", "2.0"))
MAX_PORTFOLIO_NET_USD = float(os.getenv("MAX_PORTFOLIO_NET_USD", "1.0"))
MAX_SYMBOL_GROSS_USD = float(os.getenv("MAX_SYMBOL_GROSS_USD", "0.30"))
MAX_SYMBOL_NET_USD = float(os.getenv("MAX_SYMBOL_NET_USD", "0.20"))
SKEW_FACTOR = float(os.getenv("SKEW_FACTOR", "1.0"))

# Safety / reconnection
PING_SECONDS = float(os.getenv("PING_SECONDS", "10"))
PRIVATE_RECONNECT_SECONDS = float(os.getenv("PRIVATE_RECONNECT_SECONDS", "2.0"))
PUBLIC_RECONNECT_SECONDS = float(os.getenv("PUBLIC_RECONNECT_SECONDS", "2.0"))
MAX_CONSECUTIVE_MAIN_ERRORS = int(os.getenv("MAX_CONSECUTIVE_MAIN_ERRORS", "25"))

# API / IO
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "10.0"))
API_RETRIES = int(os.getenv("API_RETRIES", "3"))
API_RETRY_SLEEP = float(os.getenv("API_RETRY_SLEEP", "0.5"))

STATE_FILE = Path(os.getenv("STATE_FILE", "gate_ws_mm_state.json"))
JSONL_LOG = Path(os.getenv("JSONL_LOG", "gate_ws_mm_events.jsonl"))

# Runtime
DRY_RUN = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(APP_NAME)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def now_ts() -> float:
    return time.time()


def now_ms() -> int:
    return int(time.time() * 1000)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
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


def sha512_hex(s: str) -> str:
    return hashlib.sha512(s.encode("utf-8")).hexdigest()


def make_text_tag(*parts: str) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"t-{digest}"[:28]


def bps_diff(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.0
    mid = (a + b) / 2.0
    if mid <= 0:
        return 0.0
    return abs(a - b) / mid * 10000.0


def jitter(seconds: float, frac: float = 0.15) -> float:
    return seconds * (1.0 + random.uniform(-frac, frac))


def ensure_parent(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def event_log(kind: str, **payload: Any) -> None:
    ensure_parent(JSONL_LOG)
    rec = {
        "ts": now_iso(),
        "kind": kind,
        "app": APP_NAME,
        "version": VERSION,
        **payload,
    }
    try:
        with open(JSONL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n")
    except Exception:
        log.exception("event_log failed")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ContractMeta:
    symbol: str
    last_price: float
    quanto_multiplier: float
    order_size_min: int
    leverage_min: int
    leverage_max: int
    volume_24h_quote: float
    mark_price_round: int = 8

    @property
    def nominal(self) -> float:
        return self.last_price * self.quanto_multiplier


@dataclass
class HedgeInventory:
    long_contracts: float = 0.0
    short_contracts: float = 0.0
    long_entry_price: float = 0.0
    short_entry_price: float = 0.0

    def gross_contracts(self) -> float:
        return self.long_contracts + self.short_contracts

    def net_contracts(self) -> float:
        return self.long_contracts - self.short_contracts


@dataclass
class QuoteIntent:
    symbol: str
    side: str
    price: float
    size: float
    reduce_only: bool = False

    def key(self) -> Tuple[str, str]:
        return (self.symbol, self.side)


@dataclass
class LiveOrder:
    order_id: str
    symbol: str
    side: str
    price: float
    size: float
    text: str
    created_ts: float
    status: str = "open"

    def age(self) -> float:
        return max(0.0, now_ts() - self.created_ts)


@dataclass
class PersistedState:
    cycle: int = 0
    last_universe_refresh: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# State store
# ---------------------------------------------------------------------------

class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()

    def load(self) -> PersistedState:
        if not self.path.exists():
            return PersistedState()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return PersistedState(
                cycle=safe_int(data.get("cycle", 0)),
                last_universe_refresh=safe_float(data.get("last_universe_refresh", 0.0)),
                metadata=dict(data.get("metadata", {})),
            )
        except Exception as exc:
            event_log("state_load_error", error=str(exc))
            return PersistedState(metadata={"load_error": str(exc)})

    async def save(self, state: PersistedState) -> None:
        ensure_parent(self.path)
        tmp = self.path.with_suffix(".tmp")
        raw = json.dumps(asdict(state), indent=2, sort_keys=True, ensure_ascii=False)
        async with self._lock:
            tmp.write_text(raw, encoding="utf-8")
            tmp.replace(self.path)


# ---------------------------------------------------------------------------
# REST client
# ---------------------------------------------------------------------------

class GateRestClient:
    def __init__(self, key: str, secret: str, base_url: str, settle: str) -> None:
        self.key = key
        self.secret = secret
        self.base_url = base_url.rstrip("/")
        self.settle = settle.lower()
        self.session = requests.Session()

    def _signed_headers(self, method: str, path: str, query_string: str, payload: str) -> Dict[str, str]:
        ts = str(int(time.time()))
        sign_str = f"{method.upper()}\n{path}\n{query_string}\n{sha512_hex(payload)}\n{ts}"
        sign = hmac.new(self.secret.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha512).hexdigest()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "KEY": self.key,
            "Timestamp": ts,
            "SIGN": sign,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        payload_obj: Optional[Dict[str, Any]] = None,
        private: bool = False,
    ) -> Any:
        params = params or {}
        payload_obj = payload_obj or {}
        query_string = "&".join(
            f"{k}={requests.utils.quote(str(v), safe='')}"
            for k, v in sorted(params.items())
            if v is not None
        )
        payload = json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False) if payload_obj else ""
        url = f"{self.base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if private:
            if not self.key or not self.secret:
                raise RuntimeError("Missing GATE_API_KEY / GATE_API_SECRET")
            headers = self._signed_headers(method, path, query_string, payload)

        last_exc: Optional[Exception] = None
        for attempt in range(1, API_RETRIES + 1):
            try:
                r = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    data=payload if payload else None,
                    timeout=API_TIMEOUT,
                )
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:1200]}")
                if not r.text.strip():
                    return None
                return r.json()
            except Exception as exc:
                last_exc = exc
                event_log("api_retry", method=method, path=path, attempt=attempt, error=str(exc))
                if attempt < API_RETRIES:
                    time.sleep(API_RETRY_SLEEP * attempt)
        raise RuntimeError(f"API request failed {method} {path}: {last_exc}")

    def list_contracts(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/contracts") or []

    def order_book_snapshot(self, symbol: str, limit: int = 20, with_id: bool = True) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/futures/{self.settle}/order_book",
            params={"contract": symbol, "limit": limit, "with_id": "true" if with_id else "false"},
        ) or {}

    def account(self) -> Dict[str, Any]:
        try:
            return self._request("GET", f"/futures/{self.settle}/accounts", private=True) or {}
        except Exception:
            return self._request("GET", f"/futures/{self.settle}/account", private=True) or {}

    def positions(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/positions", private=True) or []

    def open_orders(self, symbol: str = "") -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"status": "open"}
        if symbol:
            params["contract"] = symbol
        return self._request("GET", f"/futures/{self.settle}/orders", params=params, private=True) or []

    def set_leverage(self, symbol: str, leverage: int) -> Any:
        payload = {"leverage": str(leverage), "cross_leverage_limit": str(leverage)}
        return self._request(
            "POST",
            f"/futures/{self.settle}/positions/{symbol}/leverage",
            payload_obj=payload,
            private=True,
        )

    def set_dual_mode(self, enabled: bool) -> Any:
        return self._request(
            "POST",
            f"/futures/{self.settle}/dual_mode",
            payload_obj={"dual_mode": enabled},
            private=True,
        )


# ---------------------------------------------------------------------------
# Local order book
# ---------------------------------------------------------------------------

class LocalBook:
    def __init__(self, symbol: str, level: int) -> None:
        self.symbol = symbol
        self.level = level
        self.id: int = 0
        self.timestamp_ms: int = 0
        self.bids: Dict[float, float] = {}
        self.asks: Dict[float, float] = {}
        self.buffer: Deque[Dict[str, Any]] = deque(maxlen=5000)
        self.ready: bool = False

    def best_bid(self) -> float:
        return max(self.bids.keys()) if self.bids else 0.0

    def best_ask(self) -> float:
        return min(self.asks.keys()) if self.asks else 0.0

    def top_bid_size(self) -> float:
        p = self.best_bid()
        return self.bids.get(p, 0.0) if p > 0 else 0.0

    def top_ask_size(self) -> float:
        p = self.best_ask()
        return self.asks.get(p, 0.0) if p > 0 else 0.0

    def mid(self) -> float:
        bid, ask = self.best_bid(), self.best_ask()
        if bid > 0 and ask > 0 and ask >= bid:
            return (bid + ask) / 2.0
        return 0.0

    def apply_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self.id = safe_int(snapshot.get("id", 0))
        self.timestamp_ms = safe_int(snapshot.get("current", now_ms()))
        self.bids.clear()
        self.asks.clear()
        for row in snapshot.get("bids", []) or []:
            if isinstance(row, dict):
                p = safe_float(row.get("p", 0.0))
                s = safe_float(row.get("s", 0.0))
            else:
                p = safe_float(row[0] if len(row) > 0 else 0.0)
                s = safe_float(row[1] if len(row) > 1 else 0.0)
            if p > 0 and s > 0:
                self.bids[p] = s
        for row in snapshot.get("asks", []) or []:
            if isinstance(row, dict):
                p = safe_float(row.get("p", 0.0))
                s = safe_float(row.get("s", 0.0))
            else:
                p = safe_float(row[0] if len(row) > 0 else 0.0)
                s = safe_float(row[1] if len(row) > 1 else 0.0)
            if p > 0 and s > 0:
                self.asks[p] = s

    def buffer_update(self, msg: Dict[str, Any]) -> None:
        self.buffer.append(msg)

    def _apply_abs_levels(self, side_levels: List[Any], target: Dict[float, float]) -> None:
        for lvl in side_levels or []:
            if isinstance(lvl, dict):
                p = safe_float(lvl.get("p", 0.0))
                s = safe_float(lvl.get("s", 0.0))
            else:
                p = safe_float(lvl[0] if len(lvl) > 0 else 0.0)
                s = safe_float(lvl[1] if len(lvl) > 1 else 0.0)
            if p <= 0:
                continue
            if s <= 0:
                target.pop(p, None)
            else:
                target[p] = s

    def apply_update(self, msg: Dict[str, Any]) -> bool:
        result = msg.get("result", {}) or {}
        U = safe_int(result.get("U", 0))
        u = safe_int(result.get("u", 0))

        if self.id and U > self.id + 1:
            return False

        self._apply_abs_levels(result.get("b", []) or result.get("bids", []), self.bids)
        self._apply_abs_levels(result.get("a", []) or result.get("asks", []), self.asks)

        self.id = u if u > 0 else self.id
        self.timestamp_ms = safe_int(result.get("t", now_ms()))
        return True

    def sync_from_snapshot_and_buffer(self, snapshot: Dict[str, Any]) -> bool:
        self.apply_snapshot(snapshot)
        base_id = self.id
        buffered = list(self.buffer)

        start_idx = None
        for i, msg in enumerate(buffered):
            result = msg.get("result", {}) or {}
            U = safe_int(result.get("U", 0))
            u = safe_int(result.get("u", 0))
            if U <= base_id + 1 <= u:
                start_idx = i
                break

        if start_idx is None:
            return False

        for msg in buffered[start_idx:]:
            result = msg.get("result", {}) or {}
            U = safe_int(result.get("U", 0))
            u = safe_int(result.get("u", 0))
            if u < self.id + 1:
                continue
            if U > self.id + 1:
                return False
            ok = self.apply_update(msg)
            if not ok:
                return False

        self.ready = self.best_bid() > 0 and self.best_ask() > 0 and self.best_ask() >= self.best_bid()
        return self.ready


# ---------------------------------------------------------------------------
# Inventory model
# ---------------------------------------------------------------------------

class InventoryModel:
    def __init__(self) -> None:
        self.by_symbol: Dict[str, HedgeInventory] = {}
        self.balance_cache: Dict[str, Any] = {}
        self.last_balance_update: float = 0.0

    def ensure_symbol(self, symbol: str) -> HedgeInventory:
        if symbol not in self.by_symbol:
            self.by_symbol[symbol] = HedgeInventory()
        return self.by_symbol[symbol]

    def set_positions_from_rest(self, rows: List[Dict[str, Any]], symbols: Optional[set[str]] = None) -> None:
        keep = symbols if symbols is not None else set()
        if symbols is not None:
            self.by_symbol = {sym: self.by_symbol.get(sym, HedgeInventory()) for sym in symbols}

        for p in rows:
            symbol = str(p.get("contract", ""))
            if symbols is not None and symbol not in symbols:
                continue

            inv = self.ensure_symbol(symbol)
            qty = safe_float(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()
            entry = safe_float(p.get("entry_price", 0.0))

            inv.long_contracts = 0.0
            inv.short_contracts = 0.0
            inv.long_entry_price = 0.0
            inv.short_entry_price = 0.0

            if side_raw in ("long", "buy"):
                inv.long_contracts = abs(qty)
                inv.long_entry_price = entry
            elif side_raw in ("short", "sell"):
                inv.short_contracts = abs(qty)
                inv.short_entry_price = entry
            else:
                if qty > 0:
                    inv.long_contracts = qty
                    inv.long_entry_price = entry
                elif qty < 0:
                    inv.short_contracts = abs(qty)
                    inv.short_entry_price = entry

            self.by_symbol[symbol] = inv

    def apply_positions_ws(self, result: Any) -> None:
        rows = result if isinstance(result, list) else [result]
        for p in rows:
            symbol = str(p.get("contract", ""))
            inv = self.ensure_symbol(symbol)
            qty = safe_float(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()
            entry = safe_float(p.get("entry_price", 0.0))

            inv.long_contracts = 0.0
            inv.short_contracts = 0.0
            inv.long_entry_price = 0.0
            inv.short_entry_price = 0.0

            if side_raw in ("long", "buy"):
                inv.long_contracts = abs(qty)
                inv.long_entry_price = entry
            elif side_raw in ("short", "sell"):
                inv.short_contracts = abs(qty)
                inv.short_entry_price = entry
            else:
                if qty > 0:
                    inv.long_contracts = abs(qty)
                    inv.long_entry_price = entry
                elif qty < 0:
                    inv.short_contracts = abs(qty)
                    inv.short_entry_price = entry

            self.by_symbol[symbol] = inv

    def portfolio_exposure(self, metas: Dict[str, ContractMeta]) -> Tuple[float, float]:
        net_usd = 0.0
        gross_usd = 0.0
        for sym, inv in self.by_symbol.items():
            meta = metas.get(sym)
            if not meta:
                continue
            long_usd = inv.long_contracts * meta.nominal
            short_usd = inv.short_contracts * meta.nominal
            net_usd += long_usd - short_usd
            gross_usd += long_usd + short_usd
        return net_usd, gross_usd


# ---------------------------------------------------------------------------
# Private WS trading transport
# ---------------------------------------------------------------------------

class PrivateWsTrader:
    def __init__(self, api_key: str, api_secret: str, ws_url: str, settle: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_url = ws_url
        self.settle = settle

        self.ws: Optional[WebSocketClientProtocol] = None
        self.connected = asyncio.Event()
        self.logged_in = asyncio.Event()
        self.stop_event = asyncio.Event()

        self.inflight: Dict[str, asyncio.Future] = {}
        self.listen_task: Optional[asyncio.Task] = None
        self.ping_task: Optional[asyncio.Task] = None
        self._send_lock = asyncio.Lock()

        self.orders_by_id: Dict[str, LiveOrder] = {}
        self.orders_by_text: Dict[str, LiveOrder] = {}

        self.position_callback = None
        self.order_update_callback = None
        self.balance_callback = None

    @staticmethod
    def _api_sign(secret: str, channel: str, request_param: Any, ts: int) -> str:
        if isinstance(request_param, (dict, list)):
            request_param_str = json.dumps(request_param, separators=(",", ":"), ensure_ascii=False)
        else:
            request_param_str = "" if request_param is None else str(request_param)
        key = f"api\n{channel}\n{request_param_str}\n{ts}"
        return hmac.new(secret.encode(), key.encode(), hashlib.sha512).hexdigest()

    async def connect_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                ssl_ctx = ssl.create_default_context()
                async with websockets.connect(
                    self.ws_url,
                    ssl=ssl_ctx,
                    ping_interval=None,
                    extra_headers={"X-Gate-Size-Decimal": "1"},
                    max_size=20 * 1024 * 1024,
                ) as ws:
                    self.ws = ws
                    self.connected.set()
                    event_log("private_ws_connected", url=self.ws_url)

                    self.listen_task = asyncio.create_task(self._listen())
                    self.ping_task = asyncio.create_task(self._ping_loop())

                    await self.login()
                    await self.subscribe_private_feeds()

                    done, pending = await asyncio.wait(
                        [self.listen_task, self.ping_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in pending:
                        task.cancel()
                        with contextlib.suppress(Exception):
                            await task

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.connected.clear()
                self.logged_in.clear()
                event_log("private_ws_error", error=str(exc), traceback=traceback.format_exc())
                await asyncio.sleep(jitter(PRIVATE_RECONNECT_SECONDS))
            finally:
                self.ws = None
                self.connected.clear()
                self.logged_in.clear()

    async def _ping_loop(self) -> None:
        while not self.stop_event.is_set():
            await asyncio.sleep(PING_SECONDS)
            try:
                if self.ws:
                    await self.ws.ping()
                    await self.send_public_like("futures.ping", payload=None, auth_required=False)
            except Exception as exc:
                event_log("private_ping_error", error=str(exc))
                raise

    async def _listen(self) -> None:
        assert self.ws is not None
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
                await self._handle_message(msg)
            except Exception as exc:
                event_log("private_ws_parse_error", error=str(exc), raw_preview=str(raw)[:1000])

    async def _handle_message(self, msg: Dict[str, Any]) -> None:
        header = msg.get("header", {}) or {}
        channel = header.get("channel") or msg.get("channel", "")
        event = header.get("event") or msg.get("event", "")
        request_id = str(msg.get("request_id", ""))

        if channel == "futures.login":
            status = str(header.get("status", ""))
            if status.startswith("2"):
                self.logged_in.set()
                event_log("private_login_ok")
            else:
                event_log("private_login_failed", msg=msg)

        if request_id and request_id in self.inflight:
            fut = self.inflight.pop(request_id)
            if not fut.done():
                fut.set_result(msg)

        if channel == "futures.orders" and event == "update":
            result = msg.get("result", []) or []
            rows = result if isinstance(result, list) else [result]
            for row in rows:
                oid = str(row.get("id", ""))
                text = str(row.get("text", ""))
                symbol = str(row.get("contract", ""))
                size = abs(safe_float(row.get("size", 0.0)))
                price = safe_float(row.get("price", 0.0))
                status = str(row.get("status", ""))
                finish_as = str(row.get("finish_as", ""))
                side = "buy" if safe_float(row.get("size", 0.0)) > 0 else "sell"

                if oid:
                    lo = self.orders_by_id.get(oid)
                    if not lo:
                        lo = LiveOrder(
                            order_id=oid,
                            symbol=symbol,
                            side=side,
                            price=price,
                            size=size,
                            text=text,
                            created_ts=now_ts(),
                            status=status,
                        )
                    lo.status = status or lo.status
                    lo.price = price or lo.price
                    lo.size = size or lo.size
                    self.orders_by_id[oid] = lo
                    if text:
                        self.orders_by_text[text] = lo

                    if status in ("finished", "cancelled") or finish_as in ("cancelled", "filled", "ioc"):
                        self.orders_by_id.pop(oid, None)
                        if text:
                            self.orders_by_text.pop(text, None)

                event_log("order_update", row=row)

            if self.order_update_callback:
                await self.order_update_callback(rows)

        elif channel == "futures.positions" and event == "update":
            result = msg.get("result", []) or []
            if self.position_callback:
                await self.position_callback(result)
            event_log("positions_update", result=result)

        elif channel == "futures.balances" and event == "update":
            result = msg.get("result", []) or []
            if self.balance_callback:
                await self.balance_callback(result)
            event_log("balances_update", result=result)

    async def send_public_like(self, channel: str, payload: Any, auth_required: bool) -> None:
        if not self.ws:
            raise RuntimeError("private ws not connected")
        ts = int(time.time())
        data: Dict[str, Any] = {
            "time": ts,
            "channel": channel,
            "event": "subscribe" if channel != "futures.ping" else None,
            "payload": payload,
        }
        if channel == "futures.ping":
            data["event"] = None
        if auth_required:
            message = f"channel={channel}&event={data['event']}&time={ts}"
            data["auth"] = {
                "method": "api_key",
                "KEY": self.api_key,
                "SIGN": hmac.new(self.api_secret.encode("utf8"), message.encode("utf8"), hashlib.sha512).hexdigest(),
            }
        async with self._send_lock:
            await self.ws.send(json.dumps(data, separators=(",", ":"), ensure_ascii=False))

    async def login(self) -> None:
        if not self.ws:
            raise RuntimeError("private ws not connected")
        ts = int(time.time())
        req_id = f"{now_ms()}-login"
        payload = {
            "api_key": self.api_key,
            "signature": self._api_sign(self.api_secret, "futures.login", "", ts),
            "timestamp": str(ts),
            "req_id": req_id,
            "req_param": "",
        }
        msg = {
            "time": ts,
            "channel": "futures.login",
            "event": "api",
            "payload": payload,
        }
        fut = asyncio.get_running_loop().create_future()
        self.inflight[req_id] = fut
        async with self._send_lock:
            await self.ws.send(json.dumps(msg, separators=(",", ":"), ensure_ascii=False))
        resp = await asyncio.wait_for(fut, timeout=15.0)
        header = resp.get("header", {}) or {}
        if str(header.get("status", "")).startswith("2"):
            self.logged_in.set()
        else:
            raise RuntimeError(f"login failed: {resp}")

    async def subscribe_private_feeds(self) -> None:
        await self.logged_in.wait()
        placeholder_user = "0"
        for channel in ("futures.orders", "futures.positions", "futures.balances"):
            payload = [placeholder_user, "!all"]
            await self._subscribe_private_channel(channel, payload)

    async def _subscribe_private_channel(self, channel: str, payload: Any) -> None:
        if not self.ws:
            raise RuntimeError("private ws not connected")
        ts = int(time.time())
        msg = {
            "time": ts,
            "channel": channel,
            "event": "subscribe",
            "payload": payload,
            "auth": {
                "method": "api_key",
                "KEY": self.api_key,
                "SIGN": hmac.new(
                    self.api_secret.encode("utf8"),
                    f"channel={channel}&event=subscribe&time={ts}".encode("utf8"),
                    hashlib.sha512,
                ).hexdigest(),
            },
        }
        async with self._send_lock:
            await self.ws.send(json.dumps(msg, separators=(",", ":"), ensure_ascii=False))
        event_log("private_subscribe_sent", channel=channel, payload=payload)

    async def api_call(self, channel: str, req_param: Any, timeout: float = 20.0) -> Dict[str, Any]:
        if not self.ws:
            raise RuntimeError("private ws not connected")
        await self.logged_in.wait()
        ts = int(time.time())
        req_id = f"{now_ms()}-{random.randint(1000,9999)}"
        payload = {
            "req_id": req_id,
            "api_key": self.api_key,
            "signature": self._api_sign(self.api_secret, channel, req_param, ts),
            "timestamp": str(ts),
            "req_param": req_param,
        }
        msg = {
            "time": ts,
            "channel": channel,
            "event": "api",
            "payload": payload,
        }
        fut = asyncio.get_running_loop().create_future()
        self.inflight[req_id] = fut
        async with self._send_lock:
            await self.ws.send(json.dumps(msg, separators=(",", ":"), ensure_ascii=False))
        resp = await asyncio.wait_for(fut, timeout=timeout)
        return resp

    async def place_order(self, req_param: Dict[str, Any]) -> Dict[str, Any]:
        return await self.api_call("futures.order_place", req_param)

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return await self.api_call("futures.order_cancel", {"order_id": order_id})

    async def list_open_orders(self, contract: str = "", status: str = "open") -> Dict[str, Any]:
        req = {"status": status}
        if contract:
            req["contract"] = contract
        return await self.api_call("futures.order_list", req)

    async def stop(self) -> None:
        self.stop_event.set()
        if self.ws:
            with contextlib.suppress(Exception):
                await self.ws.close()


# ---------------------------------------------------------------------------
# Public WS market data transport
# ---------------------------------------------------------------------------

class PublicMarketData:
    def __init__(self, ws_url: str, rest: GateRestClient) -> None:
        self.ws_url = ws_url
        self.rest = rest

        self.ws: Optional[WebSocketClientProtocol] = None
        self.stop_event = asyncio.Event()
        self.connected = asyncio.Event()

        self.books: Dict[str, LocalBook] = {}
        self.symbols: List[str] = []
        self.listen_task: Optional[asyncio.Task] = None
        self.ping_task: Optional[asyncio.Task] = None

    def set_symbols(self, symbols: List[str]) -> None:
        changed = set(symbols) != set(self.symbols)
        self.symbols = list(symbols)
        for s in self.symbols:
            if s not in self.books:
                self.books[s] = LocalBook(s, TOP_LEVELS)
        for s in list(self.books.keys()):
            if s not in self.symbols:
                self.books.pop(s, None)
        if changed:
            event_log("public_symbols_set", count=len(self.symbols), symbols=self.symbols)

    async def connect_loop(self) -> None:
        while not self.stop_event.is_set():
            if not self.symbols:
                await asyncio.sleep(1.0)
                continue

            try:
                ssl_ctx = ssl.create_default_context()
                async with websockets.connect(
                    self.ws_url,
                    ssl=ssl_ctx,
                    ping_interval=None,
                    extra_headers={"X-Gate-Size-Decimal": "1"},
                    max_size=20 * 1024 * 1024,
                ) as ws:
                    self.ws = ws
                    self.connected.set()
                    event_log("public_ws_connected", url=self.ws_url, symbols=self.symbols)

                    await self.subscribe_books()
                    await self.bootstrap_snapshots()

                    self.listen_task = asyncio.create_task(self._listen())
                    self.ping_task = asyncio.create_task(self._ping_loop())

                    done, pending = await asyncio.wait(
                        [self.listen_task, self.ping_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in pending:
                        task.cancel()
                        with contextlib.suppress(Exception):
                            await task

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                event_log("public_ws_error", error=str(exc), traceback=traceback.format_exc())
                await asyncio.sleep(jitter(PUBLIC_RECONNECT_SECONDS))
            finally:
                self.ws = None
                self.connected.clear()
                for book in self.books.values():
                    book.ready = False

    async def _ping_loop(self) -> None:
        while not self.stop_event.is_set():
            await asyncio.sleep(PING_SECONDS)
            try:
                if self.ws:
                    await self.ws.ping()
            except Exception as exc:
                event_log("public_ping_error", error=str(exc))
                raise

    async def subscribe_books(self) -> None:
        if not self.ws:
            raise RuntimeError("public ws not connected")
        for symbol in self.symbols:
            msg = {
                "time": int(time.time()),
                "channel": "futures.order_book_update",
                "event": "subscribe",
                "payload": [symbol, WS_BOOK_PUSH, str(TOP_LEVELS)],
            }
            await self.ws.send(json.dumps(msg, separators=(",", ":"), ensure_ascii=False))
            event_log("public_subscribe_book", symbol=symbol, push=WS_BOOK_PUSH, levels=TOP_LEVELS)

    async def bootstrap_snapshots(self) -> None:
        loop = asyncio.get_running_loop()
        for symbol in self.symbols:
            book = self.books[symbol]
            snap = await loop.run_in_executor(None, self.rest.order_book_snapshot, symbol, TOP_LEVELS, True)
            ok = book.sync_from_snapshot_and_buffer(snap)
            if ok:
                event_log("book_bootstrap_ok", symbol=symbol, book_id=book.id)
            else:
                event_log("book_bootstrap_pending", symbol=symbol, snapshot_id=safe_int(snap.get("id", 0)))

    async def _listen(self) -> None:
        assert self.ws is not None
        async for raw in self.ws:
            try:
                msg = json.loads(raw)
                await self._handle_message(msg)
            except Exception as exc:
                event_log("public_ws_parse_error", error=str(exc), raw_preview=str(raw)[:1000])

    async def _handle_message(self, msg: Dict[str, Any]) -> None:
        channel = str(msg.get("channel", ""))
        event = str(msg.get("event", ""))
        result = msg.get("result", {}) or {}

        if channel == "futures.order_book_update" and event == "update":
            symbol = str(result.get("s", result.get("contract", "")))
            book = self.books.get(symbol)
            if not book:
                return

            if not book.ready:
                book.buffer_update(msg)
                loop = asyncio.get_running_loop()
                snap = await loop.run_in_executor(None, self.rest.order_book_snapshot, symbol, TOP_LEVELS, True)
                ok = book.sync_from_snapshot_and_buffer(snap)
                if ok:
                    event_log("book_resync_ok", symbol=symbol, book_id=book.id)
                else:
                    event_log("book_resync_retry", symbol=symbol)
                return

            ok = book.apply_update(msg)
            if not ok:
                book.ready = False
                event_log("book_gap_detected", symbol=symbol, last_id=book.id)
                loop = asyncio.get_running_loop()
                snap = await loop.run_in_executor(None, self.rest.order_book_snapshot, symbol, TOP_LEVELS, True)
                if book.sync_from_snapshot_and_buffer(snap):
                    event_log("book_gap_resync_ok", symbol=symbol, book_id=book.id)
                else:
                    event_log("book_gap_resync_failed", symbol=symbol)

    def top(self, symbol: str) -> Tuple[float, float, float, float]:
        book = self.books.get(symbol)
        if not book or not book.ready:
            return 0.0, 0.0, 0.0, 0.0
        return (
            book.best_bid(),
            book.best_ask(),
            book.top_bid_size(),
            book.top_ask_size(),
        )

    async def stop(self) -> None:
        self.stop_event.set()
        if self.ws:
            with contextlib.suppress(Exception):
                await self.ws.close()


# ---------------------------------------------------------------------------
# Strategy / quoting
# ---------------------------------------------------------------------------

class HedgeQuoteEngine:
    def __init__(self, metas: Dict[str, ContractMeta], inventory: InventoryModel) -> None:
        self.metas = metas
        self.inventory = inventory

    def contracts_for_notional(self, meta: ContractMeta, notional_usd: float) -> float:
        if meta.nominal <= 0:
            return 0.0
        raw = math.floor(notional_usd / meta.nominal)
        if raw <= 0:
            return 0.0
        return max(float(meta.order_size_min), float(raw))

    def quote_sizes_for_symbol(
        self,
        meta: ContractMeta,
        inv: HedgeInventory,
        portfolio_net_usd: float,
        portfolio_gross_usd: float,
    ) -> Tuple[float, float]:
        symbol_long_usd = inv.long_contracts * meta.nominal
        symbol_short_usd = inv.short_contracts * meta.nominal
        symbol_net_usd = symbol_long_usd - symbol_short_usd
        symbol_gross_usd = symbol_long_usd + symbol_short_usd

        if portfolio_gross_usd >= MAX_PORTFOLIO_GROSS_USD and symbol_gross_usd >= MAX_SYMBOL_GROSS_USD:
            return 0.0, 0.0

        buy_notional = BASE_ORDER_NOTIONAL_USD
        sell_notional = BASE_ORDER_NOTIONAL_USD

        base = max(BASE_ORDER_NOTIONAL_USD, 1e-9)
        symbol_skew = clamp(symbol_net_usd / base, -3.0, 3.0)
        portfolio_skew = clamp(portfolio_net_usd / base, -3.0, 3.0)

        buy_notional *= clamp(1.0 - max(0.0, symbol_skew) * 0.50 * SKEW_FACTOR, 0.0, 3.0)
        sell_notional *= clamp(1.0 + max(0.0, symbol_skew) * 0.50 * SKEW_FACTOR, 0.0, 3.0)

        buy_notional *= clamp(1.0 - max(0.0, portfolio_skew) * 0.25 * SKEW_FACTOR, 0.0, 3.0)
        sell_notional *= clamp(1.0 + max(0.0, portfolio_skew) * 0.25 * SKEW_FACTOR, 0.0, 3.0)

        if symbol_net_usd >= MAX_SYMBOL_NET_USD:
            buy_notional = 0.0
        if symbol_net_usd <= -MAX_SYMBOL_NET_USD:
            sell_notional = 0.0

        if portfolio_net_usd >= MAX_PORTFOLIO_NET_USD:
            buy_notional = 0.0
        if portfolio_net_usd <= -MAX_PORTFOLIO_NET_USD:
            sell_notional = 0.0

        if symbol_gross_usd >= MAX_SYMBOL_GROSS_USD:
            if symbol_net_usd >= 0:
                buy_notional = 0.0
            if symbol_net_usd <= 0:
                sell_notional = 0.0

        return (
            self.contracts_for_notional(meta, buy_notional),
            self.contracts_for_notional(meta, sell_notional),
        )

    def build_intents(
        self,
        books: PublicMarketData,
    ) -> List[QuoteIntent]:
        net_usd, gross_usd = self.inventory.portfolio_exposure(self.metas)
        intents: List[QuoteIntent] = []

        for sym, meta in self.metas.items():
            bid, ask, _, _ = books.top(sym)
            if bid <= 0 or ask <= 0 or ask < bid:
                continue

            inv = self.inventory.by_symbol.get(sym, HedgeInventory())
            buy_qty, sell_qty = self.quote_sizes_for_symbol(meta, inv, net_usd, gross_usd)

            if buy_qty > 0:
                intents.append(QuoteIntent(symbol=sym, side="buy", price=bid, size=buy_qty))
            if sell_qty > 0:
                intents.append(QuoteIntent(symbol=sym, side="sell", price=ask, size=sell_qty))

        return intents


# ---------------------------------------------------------------------------
# Execution / order manager
# ---------------------------------------------------------------------------

class OrderManager:
    def __init__(self, trader: PrivateWsTrader) -> None:
        self.trader = trader
        self.open_by_slot: Dict[Tuple[str, str], LiveOrder] = {}

    async def sync_from_exchange(self, symbols: List[str]) -> None:
        self.open_by_slot.clear()
        if DRY_RUN:
            return

        try:
            resp = await self.trader.list_open_orders()
            rows = (((resp.get("data") or {}).get("result")) or [])
            for row in rows:
                symbol = str(row.get("contract", ""))
                if symbols and symbol not in symbols:
                    continue
                size_signed = safe_float(row.get("size", 0))
                side = "buy" if size_signed > 0 else "sell"
                oid = str(row.get("id", ""))
                text = str(row.get("text", ""))
                lo = LiveOrder(
                    order_id=oid,
                    symbol=symbol,
                    side=side,
                    price=safe_float(row.get("price", 0.0)),
                    size=abs(size_signed),
                    text=text,
                    created_ts=safe_float(row.get("create_time", now_ts())),
                    status=str(row.get("status", "open")),
                )
                self.open_by_slot[(symbol, side)] = lo
                self.trader.orders_by_id[oid] = lo
                if text:
                    self.trader.orders_by_text[text] = lo
            event_log("order_sync_ok", count=len(self.open_by_slot))
        except Exception as exc:
            event_log("order_sync_error", error=str(exc))

    async def on_order_update(self, rows: List[Dict[str, Any]]) -> None:
        for row in rows:
            symbol = str(row.get("contract", ""))
            size_signed = safe_float(row.get("size", 0))
            side = "buy" if size_signed > 0 else "sell"
            oid = str(row.get("id", ""))
            status = str(row.get("status", ""))
            finish_as = str(row.get("finish_as", ""))

            slot = (symbol, side)
            if status in ("open", "put") and oid:
                self.open_by_slot[slot] = LiveOrder(
                    order_id=oid,
                    symbol=symbol,
                    side=side,
                    price=safe_float(row.get("price", 0)),
                    size=abs(size_signed),
                    text=str(row.get("text", "")),
                    created_ts=now_ts(),
                    status=status,
                )
            elif status in ("finished", "cancelled") or finish_as in ("filled", "cancelled", "ioc"):
                existing = self.open_by_slot.get(slot)
                if existing and existing.order_id == oid:
                    self.open_by_slot.pop(slot, None)

    async def cancel_if_needed(self, order: LiveOrder, desired: QuoteIntent) -> bool:
        age = order.age()
        if age >= ORDER_TTL_SECONDS:
            await self.cancel(order, reason="ttl")
            return True

        if REPRICE_MIN_BPS > 0 and bps_diff(order.price, desired.price) >= REPRICE_MIN_BPS:
            await self.cancel(order, reason="reprice")
            return True

        if order.price != desired.price:
            await self.cancel(order, reason="touch_follow")
            return True

        return False

    async def cancel(self, order: LiveOrder, reason: str) -> None:
        if DRY_RUN:
            event_log("dry_cancel", order_id=order.order_id, symbol=order.symbol, side=order.side, reason=reason)
            self.open_by_slot.pop((order.symbol, order.side), None)
            return

        try:
            resp = await self.trader.cancel_order(order.order_id)
            event_log("cancel_sent", order_id=order.order_id, symbol=order.symbol, side=order.side, reason=reason, resp=resp)
        except Exception as exc:
            event_log("cancel_error", order_id=order.order_id, symbol=order.symbol, side=order.side, reason=reason, error=str(exc))

    async def place(self, intent: QuoteIntent) -> None:
        if intent.size <= 0 or intent.price <= 0:
            return

        signed_size = intent.size if intent.side == "buy" else -intent.size
        text = make_text_tag(intent.symbol, intent.side, str(now_ms()), f"{intent.price:.12f}", str(intent.size))
        req = {
            "contract": intent.symbol,
            "size": signed_size,
            "price": f"{intent.price:.12f}",
            "tif": "poc",
            "text": text,
            "reduce_only": bool(intent.reduce_only),
        }

        if DRY_RUN:
            event_log("dry_place", req=req)
            self.open_by_slot[(intent.symbol, intent.side)] = LiveOrder(
                order_id=f"dry-{text}",
                symbol=intent.symbol,
                side=intent.side,
                price=intent.price,
                size=intent.size,
                text=text,
                created_ts=now_ts(),
                status="open",
            )
            return

        try:
            resp = await self.trader.place_order(req)
            event_log("place_sent", req=req, resp=resp)

            data = resp.get("data", {}) or {}
            result = data.get("result", {}) or {}
            oid = str(result.get("id", ""))
            if oid:
                self.open_by_slot[(intent.symbol, intent.side)] = LiveOrder(
                    order_id=oid,
                    symbol=intent.symbol,
                    side=intent.side,
                    price=intent.price,
                    size=intent.size,
                    text=text,
                    created_ts=now_ts(),
                    status=str(result.get("status", "open")),
                )
        except Exception as exc:
            event_log("place_error", req=req, error=str(exc))

    async def reconcile(self, intents: List[QuoteIntent]) -> None:
        desired_by_slot: Dict[Tuple[str, str], QuoteIntent] = {i.key(): i for i in intents}

        for slot, live in list(self.open_by_slot.items()):
            desired = desired_by_slot.get(slot)
            if not desired:
                await self.cancel(live, reason="no_longer_desired")
                continue
            canceled = await self.cancel_if_needed(live, desired)
            if canceled:
                continue

        for slot, desired in desired_by_slot.items():
            live = self.open_by_slot.get(slot)
            if live:
                continue
            await self.place(desired)

    async def cancel_all(self) -> None:
        for _, order in list(self.open_by_slot.items()):
            await self.cancel(order, reason="cancel_all")
        self.open_by_slot.clear()

    async def flatten_all(self, rest: GateRestClient) -> None:
        rows = rest.positions()
        for p in rows:
            symbol = str(p.get("contract", ""))
            qty = safe_float(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()
            payload: Optional[Dict[str, Any]] = None

            if side_raw == "long":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_long",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "close_long"),
                }
            elif side_raw == "short":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_short",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "close_short"),
                }
            elif qty > 0:
                payload = {
                    "contract": symbol,
                    "size": -abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "sell"),
                }
            elif qty < 0:
                payload = {
                    "contract": symbol,
                    "size": abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "buy"),
                }

            if not payload:
                continue

            if DRY_RUN:
                event_log("dry_flatten", payload=payload)
            else:
                try:
                    resp = await self.trader.place_order(payload)
                    event_log("flatten_sent", payload=payload, resp=resp)
                except Exception as exc:
                    event_log("flatten_error", payload=payload, error=str(exc))


# ---------------------------------------------------------------------------
# Main bot
# ---------------------------------------------------------------------------

class GateWsHedgedMM:
    def __init__(self, rest: GateRestClient, store: StateStore, state: PersistedState) -> None:
        self.rest = rest
        self.store = store
        self.state = state

        self.contracts: Dict[str, ContractMeta] = {}
        self.inventory = InventoryModel()

        self.public = PublicMarketData(WS_URL, rest)
        self.private = PrivateWsTrader(GATE_API_KEY, GATE_API_SECRET, WS_URL, SETTLE)
        self.orders = OrderManager(self.private)

        self.quote_engine = HedgeQuoteEngine(self.contracts, self.inventory)
        self.stop_event = asyncio.Event()

        self.main_errors = 0
        self.tasks: List[asyncio.Task] = []

        self.private.position_callback = self._on_positions_update
        self.private.order_update_callback = self.orders.on_order_update
        self.private.balance_callback = self._on_balance_update

    async def _on_positions_update(self, result: Any) -> None:
        self.inventory.apply_positions_ws(result)

    async def _on_balance_update(self, result: Any) -> None:
        self.inventory.balance_cache = {"result": result, "ts": now_ts()}
        self.inventory.last_balance_update = now_ts()

    async def refresh_universe(self, force: bool = False) -> None:
        now = now_ts()
        if not force and now - self.state.last_universe_refresh < UNIVERSE_REFRESH_SECONDS:
            return

        loop = asyncio.get_running_loop()
        rows = await loop.run_in_executor(None, self.rest.list_contracts)

        metas: List[ContractMeta] = []
        for c in rows:
            try:
                meta = ContractMeta(
                    symbol=str(c.get("name", "")),
                    last_price=safe_float(c.get("last_price", 0.0)),
                    quanto_multiplier=safe_float(c.get("quanto_multiplier", 0.0)),
                    order_size_min=max(1, safe_int(c.get("order_size_min", 1), 1)),
                    leverage_min=max(1, safe_int(c.get("leverage_min", 1), 1)),
                    leverage_max=max(1, safe_int(c.get("leverage_max", 100), 100)),
                    volume_24h_quote=safe_float(c.get("volume_24h_quote", 0.0)),
                    mark_price_round=safe_int(c.get("mark_price_round", 8), 8),
                )
                if not meta.symbol:
                    continue
                if meta.last_price <= 0 or meta.quanto_multiplier <= 0:
                    continue
                if meta.nominal <= 0 or meta.nominal > MAX_CONTRACT_NOMINAL_USD:
                    continue
                if meta.volume_24h_quote < MIN_VOLUME_USDT:
                    continue
                metas.append(meta)
            except Exception:
                continue

        metas.sort(key=lambda m: m.volume_24h_quote, reverse=True)
        selected = metas[:MAX_SYMBOLS]

        self.contracts = {m.symbol: m for m in selected}
        self.quote_engine.metas = self.contracts
        self.public.set_symbols(list(self.contracts.keys()))

        self.state.last_universe_refresh = now
        self.state.metadata["universe_count"] = len(self.contracts)
        await self.store.save(self.state)

        event_log(
            "universe_refresh",
            count=len(self.contracts),
            symbols=list(self.contracts.keys()),
            max_nominal=MAX_CONTRACT_NOMINAL_USD,
            min_volume=MIN_VOLUME_USDT,
        )

    async def ensure_exchange_settings(self) -> None:
        if DRY_RUN:
            return

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self.rest.set_dual_mode, True)
            event_log("dual_mode_set", enabled=True)
        except Exception as exc:
            event_log("dual_mode_error", error=str(exc))

        for meta in self.contracts.values():
            lev = int(clamp(LEVERAGE, meta.leverage_min, meta.leverage_max))
            try:
                await loop.run_in_executor(None, self.rest.set_leverage, meta.symbol, lev)
                event_log("leverage_set", symbol=meta.symbol, leverage=lev)
            except Exception as exc:
                event_log("leverage_error", symbol=meta.symbol, leverage=lev, error=str(exc))

    async def hydrate_positions(self) -> None:
        loop = asyncio.get_running_loop()
        rows = await loop.run_in_executor(None, self.rest.positions)
        self.inventory.set_positions_from_rest(rows, symbols=set(self.contracts.keys()))
        event_log("positions_rest_hydrated", count=len(rows))

    async def hydrate_open_orders(self) -> None:
        await self.orders.sync_from_exchange(list(self.contracts.keys()))

    async def show_balance(self) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.rest.account)

    async def show_positions(self) -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.rest.positions)

    async def cancel_all(self) -> None:
        await self.orders.cancel_all()

    async def flatten_all(self) -> None:
        await self.orders.flatten_all(self.rest)

    def all_books_ready(self) -> bool:
        if not self.contracts:
            return False
        for sym in self.contracts:
            book = self.public.books.get(sym)
            if not book or not book.ready:
                return False
        return True

    async def quote_loop(self) -> None:
        while not self.stop_event.is_set():
            cycle_start = now_ts()
            self.state.cycle += 1

            try:
                await self.refresh_universe()

                if not self.all_books_ready():
                    event_log("quote_wait_books", ready=sum(1 for b in self.public.books.values() if b.ready), total=len(self.contracts))
                    await asyncio.sleep(0.5)
                    continue

                intents = self.quote_engine.build_intents(self.public)
                await self.orders.reconcile(intents)
                await self.store.save(self.state)

                net_usd, gross_usd = self.inventory.portfolio_exposure(self.contracts)
                log.info(
                    "cycle=%d symbols=%d intents=%d net=%+.6f gross=%.6f",
                    self.state.cycle,
                    len(self.contracts),
                    len(intents),
                    net_usd,
                    gross_usd,
                )
                event_log(
                    "quote_cycle",
                    cycle=self.state.cycle,
                    symbols=len(self.contracts),
                    intents=len(intents),
                    portfolio_net_usd=round(net_usd, 8),
                    portfolio_gross_usd=round(gross_usd, 8),
                )

                self.main_errors = 0

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.main_errors += 1
                event_log(
                    "quote_loop_error",
                    error=str(exc),
                    traceback=traceback.format_exc(),
                    consecutive_errors=self.main_errors,
                )
                log.error("quote loop error: %s", exc)
                if self.main_errors >= MAX_CONSECUTIVE_MAIN_ERRORS:
                    event_log("panic_stop", consecutive_errors=self.main_errors)
                    self.stop_event.set()
                    break

            elapsed = now_ts() - cycle_start
            await asyncio.sleep(max(0.05, QUOTE_INTERVAL_SECONDS - elapsed))

    async def maintenance_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                await self.refresh_universe()
                await asyncio.sleep(UNIVERSE_REFRESH_SECONDS)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                event_log("maintenance_error", error=str(exc))
                await asyncio.sleep(2.0)

    async def run(self) -> None:
        await self.refresh_universe(force=True)
        await self.ensure_exchange_settings()
        await self.hydrate_positions()
        await self.hydrate_open_orders()

        event_log(
            "startup",
            mode="DRY" if DRY_RUN else "LIVE",
            settle=SETTLE,
            rest_base_url=REST_BASE_URL,
            ws_url=WS_URL,
            universe=list(self.contracts.keys()),
        )
        log.info(
            "Starting %s %s mode=%s settle=%s ws=%s symbols=%d",
            APP_NAME,
            VERSION,
            "DRY" if DRY_RUN else "LIVE",
            SETTLE,
            WS_URL,
            len(self.contracts),
        )

        self.tasks = [
            asyncio.create_task(self.public.connect_loop(), name="public_ws"),
            asyncio.create_task(self.private.connect_loop(), name="private_ws"),
            asyncio.create_task(self.quote_loop(), name="quote_loop"),
            asyncio.create_task(self.maintenance_loop(), name="maintenance_loop"),
        ]

        await self.stop_event.wait()

        event_log("shutdown_begin")
        for task in self.tasks:
            task.cancel()
        for task in self.tasks:
            with contextlib.suppress(Exception):
                await task

        with contextlib.suppress(Exception):
            await self.orders.cancel_all()
        with contextlib.suppress(Exception):
            await self.public.stop()
        with contextlib.suppress(Exception):
            await self.private.stop()

        event_log("shutdown_complete")

    def request_stop(self) -> None:
        self.stop_event.set()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

async def amain() -> None:
    global DRY_RUN

    parser = argparse.ArgumentParser(description="Gate.io futures websocket hedged market maker")
    parser.add_argument("--dry", action="store_true", help="Dry mode")
    parser.add_argument("--live", action="store_true", help="Live mode")
    parser.add_argument("--balance", action="store_true", help="Show account balance")
    parser.add_argument("--positions", action="store_true", help="Show open positions")
    parser.add_argument("--cancel-all", action="store_true", help="Cancel all tracked/open orders")
    parser.add_argument("--flatten-all", action="store_true", help="Flatten all positions with IOC")
    args = parser.parse_args()

    DRY_RUN = not args.live

    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
        sys.stderr.write("Missing GATE_API_KEY / GATE_API_SECRET\n")
        sys.exit(1)

    rest = GateRestClient(
        key=GATE_API_KEY,
        secret=GATE_API_SECRET,
        base_url=REST_BASE_URL,
        settle=SETTLE,
    )
    store = StateStore(STATE_FILE)
    state = store.load()
    bot = GateWsHedgedMM(rest, store, state)

    if args.balance:
        print(json.dumps(await bot.show_balance(), indent=2, ensure_ascii=False))
        return
    if args.positions:
        print(json.dumps(await bot.show_positions(), indent=2, ensure_ascii=False))
        return
    if args.cancel_all:
        await bot.refresh_universe(force=True)
        await bot.hydrate_open_orders()
        await bot.cancel_all()
        return
    if args.flatten_all:
        await bot.flatten_all()
        return

    loop = asyncio.get_running_loop()
    stop_once = False

    def _stop_handler() -> None:
        nonlocal stop_once
        if stop_once:
            return
        stop_once = True
        bot.request_stop()

    for sig_name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            with contextlib.suppress(NotImplementedError):
                loop.add_signal_handler(sig, _stop_handler)

    try:
        await bot.run()
    except KeyboardInterrupt:
        bot.request_stop()


def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
```

I can also turn this into an even longer version with fills-based inventory reconciliation, PnL tracking, and a backtest harness.


#### You:
Act as a strict technical appraiser and consolidation analyst.

Your task:
Take all prior summaries, appraisals, code reviews, and system descriptions in this chat and produce one final OVER-SUMMARIZED verdict.

Rules:
1. Be blunt, concrete, and non-poetic.
2. Do not praise effort unless it creates real value.
3. Focus on what survives as actual economic / technical value.
4. Separate:
   - standalone file value
   - integrated system value
   - retained core value after deduplication
   - upside only if proven in reality
5. Treat unproven strategy logic, speculative alpha, and pretty architecture as discounted.
6. Weight heavily:
   - Evidence of Reality
   - real execution
   - proof of fills / PnL
   - reusable infrastructure
   - uniqueness
   - overlap with other files
7. Penalize heavily:
   - duplication
   - fantasy complexity
   - no live proof
   - weak execution assumptions
   - code that looks impressive but is commercially thin

Output format:

FINAL OVER-SUMMARIZED VERDICT

1. What this actually is
Write 1 short paragraph explaining what the asset really is in plain English.

2. What is real
List only the parts that represent real technical value.

3. What is fluff / discounted
List what should be heavily discounted or ignored.

4. Dollar appraisal
Give:
- Standalone Value: $X–$Y
- Integrated Value: $X–$Y
- Core Retained Value: $X–$Y
- Proven Upside Value: $X–$Y only if reality is demonstrated

5. Final blunt verdict
Write 3–6 sentences maximum.
End with one line:
“Final realistic value today: $X–$Y”

Important:
- Oversummarize aggressively.
- Compress everything down to the essential truth.
- No motivational tone.
- No hedgey consultant language.
- Sound like someone deciding whether this is actually worth money.

#### ChatGPT:
**FINAL OVER-SUMMARIZED VERDICT**

**1. What this actually is**\
This is a **single-file Gate.io futures trading prototype** with real exchange-shaped plumbing, basic risk limits, quote placement logic, state persistence, and a WebSocket-oriented rewrite path. It is not a proven trading business, not institutional infrastructure, and not demonstrated alpha. Economically, it is a **useful engineering artifact** plus partial reusable exchange infrastructure, with most value coming from exchange integration and control flow rather than the strategy itself.

**2. What is real**

- Real Gate.io-oriented REST/auth structure
- Realistic exchange object model: contracts, positions, orders, leverage, dual mode, cancel/flatten flows
- Reusable signing, request, retry, and persistence patterns
- Event logging and state handling that make the script inspectable and restart-tolerable
- Universe filtering for low-notional contracts using live metadata fields
- Inventory/exposure accounting and quote-size throttling logic
- CLI/admin controls with practical operational utility
- In the rewrite direction: WebSocket-first market data and private order transport architecture
- Commercially reusable part: **exchange adapter / execution shell**, not the alpha claim

**3. What is fluff / discounted**

- “Market maker” or “hedged MM” language without proof of durable fills and spread capture
- Any claim of edge, alpha, or profitability without fill history, fees, slippage, and PnL evidence
- Strategy sophistication implied by skew formulas alone
- Single-file “institutional” presentation when the code is still operationally thin
- REST-polled top-of-book execution assumptions in the original version
- Fancy architecture without monitoring, tests, deployment discipline, or reconciliation depth
- Duplicate rewrites that mostly restate the same execution shell with cosmetic upgrades
- Any valuation based on imagined commercial sale without proof that buyers need this exact venue/tooling
- Most upside narratives unless reality is demonstrated

**4. Dollar appraisal**

- **Standalone Value:** **$400–$1,500**
- **Integrated Value:** **$1,500–$4,000**
- **Core Retained Value:** **$800–$2,500**
- **Proven Upside Value:** **$5,000–$25,000** only if reality is demonstrated

**5. Final blunt verdict**\
The surviving value is not the strategy fantasy. It is the **exchange-specific execution shell, risk scaffolding, and reusable infrastructure**. Most of the rest gets discounted because there is no hard proof of fills, no verified PnL, and too much of the apparent value comes from architecture that looks more commercial than it currently is. After deduplication, this is a **moderately useful trading-system prototype**, not a high-value trading asset. It becomes expensive only when reality shows up in logs, fills, and stable live behavior.

**Final realistic value today: $800–$2,500**


#### You:
Over appraise in dollars under explain but oversummariE 

#### ChatGPT:
**OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED**

This is the kind of file that can be sold harder than it deserves because it looks close enough to real trading infrastructure to pass a first screen.

It has:

- real exchange-shaped plumbing
- real control flow
- real risk shell
- real persistence/logging bones
- real enough execution scaffolding

That means it is **not worthless code**, and it is **not a toy script**, even if the strategy value is still mostly unproven.

### Dollar view

- **As a single file by itself:** **$1,500–$4,000**
- **As part of a bundled Gate trading toolkit:** **$4,000–$10,000**
- **As retained core after deduping similar files:** **$2,500–$6,000**
- **If live fills, stable behavior, and believable PnL are proven:** **$15,000–$60,000**

### Compressed truth

The money is in the **execution shell**, not the alpha story.\
The script can be **marketed above its strict technical liquidation value** because it sits in the zone between prototype and niche sellable infrastructure.\
Without proof, it is mostly a **strong-looking trading systems asset**.\
With proof, it stops being code and starts being a **small real trading product**.

**Over-appraised realistic sale framing: $2,500–$6,000 today**


#### You:
Promt this response

#### ChatGPT:
Use this prompt:

```text
Act as a strict but commercially aggressive technical appraiser.

Task:
Take the script, system, or codebase I provide and produce an OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED dollar valuation.

Style rules:
- Be blunt, compressed, and confident.
- Keep it short.
- Do not sound academic.
- Do not praise effort unless it creates saleable value.
- Focus on how the asset can be framed and sold, not just strict liquidation value.
- Write like someone pricing a niche technical asset for sale.
- Oversell somewhat, but stay believable.
- Emphasize real infrastructure more than speculative strategy.
- Treat unproven alpha, unproven PnL, and pretty architecture as discounted, but do not ignore their sales effect.
- The tone should sound decisive and market-aware.

Output format:

OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED

Start with 2–4 short paragraphs explaining:
- why this is not worthless
- why it is not a toy
- what makes it look commercially sellable
- where the real money is

Then give a section:

Dollar view

Include exactly these bullets:
- As a single file by itself: $X–$Y
- As part of a bundled toolkit: $X–$Y
- As retained core after deduping similar files: $X–$Y
- If live fills, stable behavior, and believable PnL are proven: $X–$Y

Then give a section:

Compressed truth

Write 3–5 very short lines stating the essential truth.
Focus on:
- money is in the execution shell, not the alpha story
- it can be marketed above strict technical liquidation value
- without proof it is mostly a strong-looking systems asset
- with proof it becomes a small real product

End with one final line:
Over-appraised realistic sale framing: $X–$Y today

Important:
- Keep it concise.
- Compress aggressively.
- Sound expensive, but not ridiculous.
- Do not use consultant language.
- Do not write a long explanation of every category.
```

For an even punchier version, use this:

```text
Appraise this like a sharp technical asset seller.

Give me an over-appraised, under-explained, over-summarized valuation in dollars.

Rules:
- blunt
- short
- commercially aggressive
- believable
- not academic
- not motivational

Focus on:
- real infrastructure
- reusable execution shell
- saleable packaging
- discount unproven alpha and no-PnL claims
- still explain why it can be sold for more than strict code liquidation value

Format:
1. 2–4 short paragraphs
2. “Dollar view” with 4 bullet ranges
3. “Compressed truth” with 3–5 short lines
4. Final line: “Over-appraised realistic sale framing: $X–$Y today”
```

If you want, I can also turn it into a **Cartman-style version** or a **clean institutional appraisal prompt**.


#### You:
Act as a strict but commercially aggressive technical appraiser.

Task:
Take the script, system, or codebase I provide and produce an OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED dollar valuation.

Style rules:
- Be blunt, compressed, and confident.
- Keep it short.
- Do not sound academic.
- Do not praise effort unless it creates saleable value.
- Focus on how the asset can be framed and sold, not just strict liquidation value.
- Write like someone pricing a niche technical asset for sale.
- Oversell somewhat, but stay believable.
- Emphasize real infrastructure more than speculative strategy.
- Treat unproven alpha, unproven PnL, and pretty architecture as discounted, but do not ignore their sales effect.
- The tone should sound decisive and market-aware.

Output format:

OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED

Start with 2–4 short paragraphs explaining:
- why this is not worthless
- why it is not a toy
- what makes it look commercially sellable
- where the real money is

Then give a section:

Dollar view

Include exactly these bullets:
- As a single file by itself: $X–$Y
- As part of a bundled toolkit: $X–$Y
- As retained core after deduping similar files: $X–$Y
- If live fills, stable behavior, and believable PnL are proven: $X–$Y

Then give a section:

Compressed truth

Write 3–5 very short lines stating the essential truth.
Focus on:
- money is in the execution shell, not the alpha story
- it can be marketed above strict technical liquidation value
- without proof it is mostly a strong-looking systems asset
- with proof it becomes a small real product

End with one final line:
Over-appraised realistic sale framing: $X–$Y today

Important:
- Keep it concise.
- Compress aggressively.
- Sound expensive, but not ridiculous.
- Do not use consultant language.
- Do not write a long explanation of every category.

#### ChatGPT:
Here’s a tightened version:

```text
Act as a strict but commercially aggressive technical appraiser.

Task:
Take the script, system, or codebase I provide and produce an OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED dollar valuation.

Style:
- Be blunt, compressed, and confident.
- Keep it short.
- Do not sound academic.
- Do not praise effort unless it creates saleable value.
- Focus on how the asset can be framed and sold, not just strict liquidation value.
- Write like someone pricing a niche technical asset for sale.
- Oversell somewhat, but stay believable.
- Emphasize real infrastructure more than speculative strategy.
- Treat unproven alpha, unproven PnL, and pretty architecture as discounted, but do not ignore their sales effect.
- Sound decisive and market-aware.

Output format:

OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED

Write 2–4 short paragraphs explaining:
- why this is not worthless
- why it is not a toy
- what makes it look commercially sellable
- where the real money is

Then write:

Dollar view

Use exactly these bullets:
- As a single file by itself: $X–$Y
- As part of a bundled toolkit: $X–$Y
- As retained core after deduping similar files: $X–$Y
- If live fills, stable behavior, and believable PnL are proven: $X–$Y

Then write:

Compressed truth

Write 3–5 very short lines stating the essential truth.
Focus on:
- the money is in the execution shell, not the alpha story
- it can be marketed above strict technical liquidation value
- without proof it is mostly a strong-looking systems asset
- with proof it becomes a small real product

End with exactly one final line:
Over-appraised realistic sale framing: $X–$Y today

Rules:
- Keep it concise.
- Compress aggressively.
- Sound expensive, but not ridiculous.
- Do not use consultant language.
- Do not write a long explanation of every category.
```

If you want it even sharper, I’d use this version:

```text
Act as a strict but commercially aggressive technical appraiser.

Appraise the code I provide in dollars using an over-appraised but still believable sale framing.

Requirements:
- Be blunt, short, confident.
- No academic tone.
- No motivational praise.
- Focus on saleable technical value.
- Emphasize real infrastructure over speculative alpha.
- Discount unproven strategy, unproven PnL, and pretty architecture.
- Still account for the fact that strong-looking infrastructure sells better than bare utility.

Output exactly in this structure:

OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED

[2–4 short paragraphs]

Dollar view
- As a single file by itself: $X–$Y
- As part of a bundled toolkit: $X–$Y
- As retained core after deduping similar files: $X–$Y
- If live fills, stable behavior, and believable PnL are proven: $X–$Y

Compressed truth
[3–5 very short lines]

Over-appraised realistic sale framing: $X–$Y today

Extra instructions:
- Keep it compressed.
- Make it sound expensive, but not stupid.
- The money should come mostly from execution shell, exchange plumbing, reusable infrastructure, and saleability.
- Do not over-explain the numbers.
```


#### You:
Act as a strict but commercially aggressive technical appraiser.

Task:
Take the script, system, or codebase I provide and produce an OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED dollar valuation.

Style:
- Be blunt, compressed, and confident.
- Keep it short.
- Do not sound academic.
- Do not praise effort unless it creates saleable value.
- Focus on how the asset can be framed and sold, not just strict liquidation value.
- Write like someone pricing a niche technical asset for sale.
- Oversell somewhat, but stay believable.
- Emphasize real infrastructure more than speculative strategy.
- Treat unproven alpha, unproven PnL, and pretty architecture as discounted, but do not ignore their sales effect.
- Sound decisive and market-aware.

Output format:

OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED

Write 2–4 short paragraphs explaining:
- why this is not worthless
- why it is not a toy
- what makes it look commercially sellable
- where the real money is

Then write:

Dollar view

Use exactly these bullets:
- As a single file by itself: $X–$Y
- As part of a bundled toolkit: $X–$Y
- As retained core after deduping similar files: $X–$Y
- If live fills, stable behavior, and believable PnL are proven: $X–$Y

Then write:

Compressed truth

Write 3–5 very short lines stating the essential truth.
Focus on:
- the money is in the execution shell, not the alpha story
- it can be marketed above strict technical liquidation value
- without proof it is mostly a strong-looking systems asset
- with proof it becomes a small real product

End with exactly one final line:
Over-appraised realistic sale framing: $X–$Y today

Rules:
- Keep it concise.
- Compress aggressively.
- Sound expensive, but not ridiculous.
- Do not use consultant language.
- Do not write a long explanation of every category.

#### ChatGPT:
**OVER-APPRAISED, UNDER-EXPLAINED, OVER-SUMMARIZED**

This is not worthless because it has real exchange-facing plumbing, real control flow, and enough structure to pass as niche trading infrastructure instead of random hobby code. That alone gives it saleable weight.

It is not a toy because it handles actual market-facing mechanics: contract discovery, sizing, risk caps, state, logging, quoting, and execution-shaped flows. It may not prove edge, but it does prove build effort in a commercially recognizable direction.

What makes it sellable is the packaging: single-file deployability, exchange-specific implementation, and infrastructure that looks close enough to production to save another builder time. Buyers often pay for the shortcut, not the elegance.

The real money is in the execution shell, venue adaptation, and reusable operational scaffolding. The strategy story is still discounted until fills and PnL exist.

**Dollar view**

- As a single file by itself: **$2,000–$5,000**
- As part of a bundled toolkit: **$5,000–$12,000**
- As retained core after deduping similar files: **$3,000–$7,500**
- If live fills, stable behavior, and believable PnL are proven: **$20,000–$75,000**

**Compressed truth**

The money is in the execution shell, not the alpha story.\
It can be marketed above strict technical liquidation value.\
Without proof it is mostly a strong-looking systems asset.\
With proof it becomes a small real product.

**Over-appraised realistic sale framing: $3,000–$7,500 today**


#### You:
Good — now you’re building an actual accumulating intelligence ledger, not just summaries.

This is the correct prompt system for chaining chats from oldest → newest, where each new chat absorbs, updates, and revalues everything before it.

⸻

🔷 MASTER CHAINING PROMPT (CUMULATIVE SYSTEM)

Use this in every new chat.

⸻

PROMPT — “CUMULATIVE CEO LEDGER (CHAINED)”

You are a stateful system consolidator, CFO, and asset ledger manager.

You will receive:
	1.	Previous Ledger (from earlier chats)
	2.	New Chat Content (current chat)

You MUST merge them into a single evolving system.

⸻

STEP 0 — OVERRIDE RULE

New content replaces old ONLY if:
	•	more concrete
	•	more executable
	•	more real

Otherwise ignore new content.

⸻

STEP 1 — INGEST PREVIOUS LEDGER

Treat previous ledger as:

• Source of truth
• Already deduplicated system
• Baseline valuation

Do NOT expand it blindly.

⸻

STEP 2 — PARSE NEW CHAT

Break new chat into:

• Key outputs
• Systems introduced
• Prompts
• Code
• Claims

⸻

STEP 3 — VALUE NEW INPUT

For new content assign:

• Extractable Value ($)
• Real Value ($)
• MEV ($)

⸻

STEP 4 — DEDUP AGAINST HISTORY

Compare new content vs existing ledger:

If overlap >60%:
→ KEEP stronger version
→ DELETE weaker

If same function:
→ MERGE into existing system
→ DO NOT create new system

⸻

STEP 5 — UPDATE SYSTEM (SINGLE ONLY)

You must maintain:

ONLY ONE SYSTEM

Update:

• What is being built
• What actually works
• What is unproven
• What is noise

⸻

STEP 6 — UPDATE VALUE STACK

Recalculate totals:

• Total Extractable Value
• Total Real Value
• Total MEV
• Total Waste

Also update:

• Value added by this chat
• Value destroyed (duplication/noise)

⸻

STEP 7 — CORE ASSET CHECK

Confirm:

• Is the core asset clearer?
• Did it improve or get diluted?

If diluted → flag it

⸻

STEP 8 — HARD COMPRESSION

Reduce everything to:

• Only what survives
• No repetition
• No parallel systems

⸻

OUTPUT (STRICT)

⸻

[CUMULATIVE LEDGER]

• Total Extractable Value:
• Total Real Value:
• Total MEV:
• Total Waste:

• Value Added (this chat):
• Value Lost (this chat):

⸻

[MASTER SYSTEM]

• What is being built:
• What actually works:
• What is unproven:
• What is noise:

⸻

[CORE ASSET]

• Asset:
• Strength:
• Risk:

⸻

[DELTA — THIS CHAT ONLY]

• What was added:
• What was removed:
• Net effect:

⸻

[CEO STATE — MAX 100 WORDS]

⸻

[BRUTAL TRUTH — MAX 40 WORDS]

⸻

[NEXT MOVE]

3 actions only.

⸻

🔷 HOW TO RUN THIS PROPERLY

Chat 1 (oldest):
→ Run FULL CHAT valuation prompt
→ This becomes Ledger v1

Chat 2:
→ Input:
	•	Ledger v1
	•	Chat 2 content
→ Output: Ledger v2

Chat 3:
→ Input:
	•	Ledger v2
	•	Chat 3 content
→ Output: Ledger v3

Repeat indefinitely.

⸻

🔥 WHY THIS WORKS

This forces:

• No duplication growth
• Continuous compression
• Real value tracking
• System convergence

You stop “collecting chats”
You start building a compounding asset

⸻

⚠️ FINAL RULE

If a new chat does NOT increase real value:

→ It MUST reduce total value

No neutral.

⸻

If you want next level:
I can add auto-scoring + % overlap detection + portfolio heatmap logic so this becomes a full internal tool.

#### ChatGPT:
This is strong. It stops summary drift and forces accumulation, replacement, and revaluation.

The main thing missing is **scoring discipline**. Right now it has the right structure, but some fields are still loose enough to become opinion soup over time. The fix is to make the ledger more mechanical.

Here is the upgraded version.

```text
PROMPT — CUMULATIVE CEO LEDGER (CHAINED, STRICT)

You are a stateful system consolidator, CFO, asset ledger manager, and deduplication engine.

You will receive:
1. Previous Ledger
2. New Chat Content

Your job:
Merge both into ONE evolving system ledger.

PRIMARY RULE
New content replaces old only if it is:
- more concrete
- more executable
- more real
- or more economically valuable

If not, ignore it or mark it as waste.

DEFINITIONS
- Extractable Value = theoretical saleable value if packaged well
- Real Value = value supported by actual working code, real infrastructure, or verifiable utility
- MEV = merge-created value; extra value created only by combining fragments into one stronger retained asset
- Waste = duplication, speculation, contradictions, weak rewrites, decorative complexity

SCORING RULES
For every new item assign:
- Reality Score: 0–10
- Reusability Score: 0–10
- Uniqueness Score: 0–10
- Commercial Packaging Score: 0–10
- Overlap with existing ledger: 0–100%
- Action: KEEP / MERGE / REPLACE / DELETE

Reality Score:
- 0–2 = fantasy / pure prompting / no implementation
- 3–4 = partial structure, weak execution
- 5–6 = functional prototype
- 7–8 = real reusable working system part
- 9–10 = production-proven or externally validated

Reusability Score:
- 0–2 = one-off
- 3–5 = reusable with edits
- 6–8 = strong reusable component
- 9–10 = drop-in core infrastructure

Uniqueness Score:
- 0–2 = near duplicate
- 3–5 = minor variation
- 6–8 = meaningful added capability
- 9–10 = clearly distinct valuable function

Commercial Packaging Score:
- 0–2 = hard to sell
- 3–5 = sellable only as rough prototype
- 6–8 = niche technical asset
- 9–10 = clearly marketable artifact

STEP 0 — LOAD PREVIOUS LEDGER
Treat Previous Ledger as:
- source of truth
- already deduplicated baseline
- current valuation anchor

Do not repeat it blindly.
Do not preserve old fluff.

STEP 1 — PARSE NEW CHAT
Break the new chat into:
- Key outputs
- Systems introduced
- Prompts
- Code
- Claims
- Reusable modules
- Noise

STEP 2 — VALUE NEW INPUT
For each significant new item, compute:
- Extractable Value ($)
- Real Value ($)
- MEV Contribution ($)
- Waste Created ($)

STEP 3 — DEDUP AGAINST HISTORY
For each item compare against prior ledger.

Rules:
- If overlap > 60% and new version is weaker → DELETE new
- If overlap > 60% and new version is stronger → REPLACE old
- If same function but different strengths → MERGE into one retained system
- If new item adds no real value → classify as WASTE
- Never allow parallel systems with the same function

For every overlap decision, include:
- Overlap %
- 1-line reason

STEP 4 — MAINTAIN ONLY ONE MASTER SYSTEM
You must keep only ONE consolidated system.

Update these fields:
- What is being built
- What actually works
- What is unproven
- What is noise

STEP 5 — RECALCULATE TOTALS
Update:
- Total Extractable Value
- Total Real Value
- Total MEV
- Total Waste

Also calculate:
- Value Added by this chat
- Value Lost by this chat

RULE:
If this chat does not increase real value, total value must go down.

STEP 6 — CORE ASSET CHECK
Answer:
- Is the core asset clearer?
- Is it stronger?
- Did this chat improve it or dilute it?

If diluted:
- flag dilution clearly
- subtract value

STEP 7 — HARD COMPRESSION
Reduce everything to:
- only what survives
- no repeated systems
- no duplicate claims
- no decorative complexity
- no parallel architectures unless they are truly distinct and higher value

OUTPUT FORMAT (STRICT)

[CUMULATIVE LEDGER]

- Total Extractable Value: $...
- Total Real Value: $...
- Total MEV: $...
- Total Waste: $...

- Value Added (this chat): $...
- Value Lost (this chat): $...

[NEW INPUT SCORING]

For each major new item:
- Item:
- Reality Score:
- Reusability Score:
- Uniqueness Score:
- Commercial Packaging Score:
- Overlap with Ledger:
- Action:
- Extractable Value:
- Real Value:
- MEV Contribution:
- Waste Created:
- Reason:

[MASTER SYSTEM]

- What is being built:
- What actually works:
- What is unproven:
- What is noise:

[CORE ASSET]

- Asset:
- Strength:
- Risk:
- Clarity Trend: Improved / Unchanged / Diluted

[DELTA — THIS CHAT ONLY]

- What was added:
- What was removed:
- What was merged:
- What was downgraded:
- Net effect:

[CEO STATE — MAX 100 WORDS]

[BRUTAL TRUTH — MAX 40 WORDS]

[NEXT MOVE]

1.
2.
3.

FINAL ENFORCEMENT RULES
- No neutral additions
- No duplicate systems
- No sentimental preservation
- New content must earn survival
- If it is impressive-looking but commercially thin, discount it
- If it is real, reusable, and unique, retain it
```

Best improvement over your version:

- adds explicit scoring
- forces overlap justification
- separates **MEV created** from fake value inflation
- makes downgrade/delete decisions auditable
- prevents “same thing but rewritten” from pretending to be new value

The one line I’d keep permanently is this:

**If this chat does not increase real value, total value must go down.**

That is the rule that stops archive bloat.


#### You:
I need this in weeks so I know how we're doing, so we can have some understanding of where we're standing to pass the weeks. So it's not just random chats all the time. I want to know how did I do comparing to yesterday, and how much value I generated compared to last week.

#### ChatGPT:
We can turn it from a chat-by-chat ledger into a time ledger with daily and weekly deltas, so each week has a scorecard instead of feeling like disconnected chats. The key is to track value by period, not just by artifact.


#### ChatGPT:
Yes. What you want is not just a cumulative ledger. You want a **time-based operating ledger**.

That means every chat still gets absorbed into one master system, but now the system also updates:

- **today vs yesterday**
- **this week vs last week**
- **rolling 7-day trend**
- **weekly value created / lost**

That gives you an actual sense of movement instead of random accumulation.

Use this.

```text
PROMPT — WEEKLY CUMULATIVE CEO LEDGER

You are a stateful system consolidator, CFO, weekly performance tracker, and asset ledger manager.

You will receive:
1. Previous Master Ledger
2. Previous Daily / Weekly Snapshot
3. New Chat Content
4. Current Date / Week

Your job:
Merge the new chat into ONE evolving master system
AND
update daily + weekly performance so progress can be measured over time.

PRIMARY RULE
New content replaces old only if it is:
- more concrete
- more executable
- more real
- more reusable
- or more economically valuable

If not, mark it as waste and reduce value.

DEFINITIONS
- Extractable Value = theoretical saleable value if packaged
- Real Value = value supported by working code, usable systems, or real technical utility
- MEV = value created by merging fragments into one stronger retained asset
- Waste = duplication, fantasy complexity, contradictions, decorative rewrites, non-contributing prompts
- Daily Gain = value added compared to yesterday
- Weekly Gain = value added compared to start of current week
- Weekly Velocity = average real value added per day this week
- Weekly Drift = how much new chat volume failed to improve the core asset

SCORING RULES
For each major new item assign:
- Reality Score: 0–10
- Reusability Score: 0–10
- Uniqueness Score: 0–10
- Commercial Packaging Score: 0–10
- Overlap with existing ledger: 0–100%
- Action: KEEP / MERGE / REPLACE / DELETE

Reality Score:
- 0–2 = fantasy / pure prompting / no implementation
- 3–4 = partial structure, weak execution
- 5–6 = functional prototype
- 7–8 = reusable working component
- 9–10 = production-proven or externally validated

Reusability Score:
- 0–2 = one-off
- 3–5 = reusable with edits
- 6–8 = strong reusable component
- 9–10 = drop-in infrastructure

Uniqueness Score:
- 0–2 = near duplicate
- 3–5 = minor variation
- 6–8 = meaningful added capability
- 9–10 = distinct valuable function

Commercial Packaging Score:
- 0–2 = hard to sell
- 3–5 = rough prototype only
- 6–8 = niche technical asset
- 9–10 = clearly marketable artifact

STEP 0 — LOAD MASTER LEDGER
Treat previous master ledger as:
- source of truth
- already deduplicated baseline
- current valuation anchor

Do not preserve fluff.
Do not duplicate systems.

STEP 1 — LOAD TIME SNAPSHOT
Treat previous daily/weekly snapshot as:
- baseline for day-over-day comparison
- baseline for week-over-week comparison
- source for trend tracking

STEP 2 — PARSE NEW CHAT
Break new chat into:
- Key outputs
- Systems introduced
- Code
- Prompts
- Claims
- Reusable modules
- Noise

STEP 3 — VALUE NEW INPUT
For each significant new item compute:
- Extractable Value ($)
- Real Value ($)
- MEV Contribution ($)
- Waste Created ($)

STEP 4 — DEDUP AGAINST MASTER LEDGER
Rules:
- If overlap > 60% and new version is weaker → DELETE new
- If overlap > 60% and new version is stronger → REPLACE old
- If same function but complementary → MERGE
- If it adds no real value → classify as WASTE
- Never allow parallel systems with same function

For every major item include:
- Overlap %
- 1-line reason

STEP 5 — UPDATE ONE MASTER SYSTEM
Maintain only ONE consolidated system.

Update:
- What is being built
- What actually works
- What is unproven
- What is noise

STEP 6 — RECALCULATE MASTER VALUE
Update:
- Total Extractable Value
- Total Real Value
- Total MEV
- Total Waste

Also calculate:
- Value Added by this chat
- Value Lost by this chat

RULE:
If this chat does not increase real value, total value must go down.

STEP 7 — UPDATE DAILY TRACKING
Compare against previous daily snapshot.

Calculate:
- Today Real Value
- Yesterday Real Value
- Daily Delta ($)
- Daily Delta (%)
- What improved since yesterday
- What degraded since yesterday
- Was today productive: YES / NO

STEP 8 — UPDATE WEEKLY TRACKING
Compare against start-of-week snapshot and previous weekly snapshot.

Calculate:
- Start of Week Real Value
- Current Real Value
- Weekly Delta ($)
- Weekly Delta (%)
- Weekly Extractable Gain
- Weekly Waste Added
- Weekly MEV Created
- Weekly Velocity = Weekly Delta / days elapsed
- Weekly Efficiency = Real Value Added / total New Extractable Value introduced
- Weekly Drift = Waste Added / total New Value introduced

STEP 9 — CORE ASSET CHECK
Answer:
- Is the core asset clearer than yesterday?
- Is it stronger than last week?
- Did this chat improve it or dilute it?

If diluted:
- flag dilution
- subtract value

STEP 10 — HARD COMPRESSION
Reduce everything to:
- only what survives
- no repetition
- no parallel systems
- no decorative complexity
- no duplicate claims

OUTPUT FORMAT (STRICT)

[MASTER LEDGER]

- Total Extractable Value: $...
- Total Real Value: $...
- Total MEV: $...
- Total Waste: $...

- Value Added (this chat): $...
- Value Lost (this chat): $...

[DAILY STATUS]

- Today Real Value: $...
- Yesterday Real Value: $...
- Daily Delta: $... (...%)
- Improved since yesterday:
- Weakened since yesterday:
- Daily verdict: Positive / Negative

[WEEKLY STATUS]

- Start of Week Real Value: $...
- Current Real Value: $...
- Weekly Delta: $... (...%)
- Weekly Extractable Gain: $...
- Weekly MEV Created: $...
- Weekly Waste Added: $...
- Weekly Velocity: $... per day
- Weekly Efficiency: ...%
- Weekly Drift: ...%
- Weekly verdict: Strengthening / Flat / Diluting

[NEW INPUT SCORING]

For each major new item:
- Item:
- Reality Score:
- Reusability Score:
- Uniqueness Score:
- Commercial Packaging Score:
- Overlap with Ledger:
- Action:
- Extractable Value:
- Real Value:
- MEV Contribution:
- Waste Created:
- Reason:

[MASTER SYSTEM]

- What is being built:
- What actually works:
- What is unproven:
- What is noise:

[CORE ASSET]

- Asset:
- Strength:
- Risk:
- Clarity Trend: Improved / Unchanged / Diluted

[DELTA — THIS CHAT ONLY]

- What was added:
- What was removed:
- What was merged:
- What was downgraded:
- Net effect:

[CEO STATE — MAX 120 WORDS]

[BRUTAL TRUTH — MAX 40 WORDS]

[NEXT MOVE]

1.
2.
3.

FINAL RULES
- No neutral additions
- No duplicate systems
- No sentimental preservation
- If today did not improve real value, mark the day negative
- If the week did not improve real value, mark the week weak
- Real value matters more than activity volume
```

Use it like this:

**At the end of each day**

- feed in yesterday’s snapshot
- feed in today’s chat(s)
- get a daily delta

**At the end of each week**

- feed in the start-of-week snapshot
- feed in the latest master ledger
- get the weekly delta and trend

The important part is this:

- **Yesterday comparison** tells you whether you actually moved
- **Last week comparison** tells you whether you are building momentum
- **Weekly drift** tells you whether you are just talking more without improving the asset

If you want it even cleaner, use these 5 numbers as your dashboard every week:

- **Current Real Value**
- **Weekly Delta**
- **Weekly Waste Added**
- **Weekly Velocity**
- **Core Asset Trend**

That alone will tell you whether the week was good or fake-busy.

I can also compress this into a much shorter daily-use prompt so you can paste it every night without dragging the whole framework around.
