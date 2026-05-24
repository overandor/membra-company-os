"""
rest_client.py — Gate.io Futures REST client.

Responsibilities:
  • Bootstrap: fetch contract specs (tick size, lot size, quanto multiplier).
  • Order lifecycle: create, cancel, query individual and bulk.
  • Account: query position, balance, account mode.

All methods are async and return typed dataclasses or raw dicts.
Retries with exponential back-off on 429 / 5xx.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from auth import sign_rest, API_KEY, API_SECRET
from config import FUTURES_REST_URL, SETTLE, ContractSpec, mm_config

log = logging.getLogger("rest_client")

# ─── Retry policy ───────────────────────────────────────────────────────────
_MAX_RETRIES   = 5
_BASE_DELAY_S  = 0.5
_RETRY_CODES   = {429, 500, 502, 503, 504}


async def _request(
    session: aiohttp.ClientSession,
    method: str,
    path: str,
    *,
    query: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]]  = None,
    signed: bool = True,
) -> Any:
    """
    Core HTTP request with retry logic.

    Returns parsed JSON body on 2xx, raises on non-retryable errors.
    """
    url = FUTURES_REST_URL + path
    headers: Dict[str, str] = {}

    if signed:
        headers = sign_rest(
            method.upper(), path, query, body,
            API_KEY, API_SECRET,
        )

    body_bytes = json.dumps(body, separators=(",", ":")).encode() if body else None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                params=query,
                data=body_bytes,
            ) as resp:
                raw = await resp.json(content_type=None)
                if resp.status == 200:
                    return raw
                if resp.status in _RETRY_CODES and attempt < _MAX_RETRIES:
                    delay = _BASE_DELAY_S * (2 ** (attempt - 1))
                    log.warning(
                        "HTTP %s on %s %s — retry %d in %.2fs",
                        resp.status, method, path, attempt, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                log.error(
                    "REST error HTTP %s: %s", resp.status, raw
                )
                raise RuntimeError(f"REST {method} {path} → HTTP {resp.status}: {raw}")
        except aiohttp.ClientError as exc:
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_BASE_DELAY_S * (2 ** attempt))
            else:
                raise

    raise RuntimeError(f"REST {method} {path} exhausted {_MAX_RETRIES} retries")


# ─── Bootstrap ───────────────────────────────────────────────────────────────

async def fetch_contract_specs(
    session: aiohttp.ClientSession,
    contract_names: List[str],
) -> Dict[str, ContractSpec]:
    """
    Fetch and validate contract specs from Gate.io.
    Returns only contracts whose mark price is currently ≤ $0.10.
    """
    path = f"/futures/{SETTLE}/contracts"
    all_contracts: List[Dict] = await _request(session, "GET", path, signed=False)

    specs: Dict[str, ContractSpec] = {}
    universe = set(contract_names)

    for c in all_contracts:
        name = c["name"]
        if name not in universe:
            continue

        tick  = Decimal(str(c["order_price_round"]))
        lot   = int(c["order_size_min"])
        quanto = Decimal(str(c["quanto_multiplier"]))

        # Verify current last price is within micro-price range.
        last = Decimal(str(c.get("last_price", "0")))
        if last > Decimal("0.10"):
            log.warning(
                "%s last_price=%s exceeds micro-price ceiling, skipping",
                name, last,
            )
            continue

        specs[name] = ContractSpec(
            name=name,
            tick_size=tick,
            lot_size=lot,
            quanto_multiplier=quanto,
        )
        log.info(
            "Loaded spec %-20s  tick=%s  lot=%s  quanto=%s  last=%s",
            name, tick, lot, quanto, last,
        )

    return specs


async def fetch_account_mode(session: aiohttp.ClientSession) -> str:
    """
    Returns 'single' (one-way) or 'dual' (hedge mode).
    """
    path = f"/futures/{SETTLE}/accounts"
    data = await _request(session, "GET", path)
    mode = data.get("mode", "single")
    log.info("Account mode: %s", mode)
    return mode


async def fetch_balance(session: aiohttp.ClientSession) -> Decimal:
    """Returns total USDT available balance in futures account."""
    path = f"/futures/{SETTLE}/accounts"
    data = await _request(session, "GET", path)
    return Decimal(str(data.get("available", "0")))


async def fetch_position(
    session: aiohttp.ClientSession,
    contract: str,
) -> int:
    """
    Returns current net position in contracts (positive=long, negative=short).
    Handles both single and dual account modes.
    """
    if mm_config.account_mode == "dual":
        path = f"/futures/{SETTLE}/dual_positions/{contract}"
        data = await _request(session, "GET", path)
        long_size  = int(data.get("long",  {}).get("size", 0))
        short_size = int(data.get("short", {}).get("size", 0))
        return long_size - short_size
    else:
        path = f"/futures/{SETTLE}/positions/{contract}"
        data = await _request(session, "GET", path)
        return int(data.get("size", 0))


# ─── Order management ────────────────────────────────────────────────────────

async def place_order(
    session:   aiohttp.ClientSession,
    contract:  str,
    size:      int,          # positive=buy, negative=sell
    price:     Decimal,
    tif:       str = "gtc",  # gtc | ioc | poc (post-only)
    reduce_only: bool = False,
    text:      str  = "t-mm",
) -> Dict[str, Any]:
    """
    Place a single limit order on Gate.io futures.

    Gate.io conventions:
      • size > 0 → buy (long open / short close)
      • size < 0 → sell (short open / long close)
      • price '0' = market (not used here)
      • tif 'poc' = post-only (maker-or-cancel)

    Returns the raw order dict from the exchange.
    """
    if mm_config.dry_run:
        log.info(
            "[DRY-RUN] place_order contract=%s size=%+d price=%s tif=%s",
            contract, size, price, tif,
        )
        return {"id": -1, "status": "open", "dry_run": True}

    path = f"/futures/{SETTLE}/orders"
    spec: ContractSpec = mm_config.contracts[contract]

    # Round price to tick size.
    price = _round_to_tick(price, spec.tick_size)

    payload: Dict[str, Any] = {
        "contract":    contract,
        "size":        size,
        "price":       str(price),
        "tif":         tif,
        "text":        text,
        "reduce_only": reduce_only,
    }

    if mm_config.account_mode == "dual":
        # Dual mode: Gate.io requires explicit open/close and side.
        if not reduce_only:
            payload["auto_size"] = "close_long" if size < 0 else "close_short"

    resp = await _request(session, "POST", path, body=payload)
    log.debug(
        "Placed order id=%s contract=%s size=%+d price=%s status=%s",
        resp.get("id"), contract, size, price, resp.get("status"),
    )
    return resp


async def cancel_order(
    session:    aiohttp.ClientSession,
    order_id:   int,
    contract:   str,
) -> bool:
    """
    Cancel a single order. Returns True if successfully cancelled.
    Swallows 404 (already filled/cancelled) and returns False.
    """
    if mm_config.dry_run:
        log.info("[DRY-RUN] cancel_order id=%s", order_id)
        return True

    path = f"/futures/{SETTLE}/orders/{order_id}"
    try:
        resp = await _request(session, "DELETE", path)
        status = resp.get("status", "")
        log.debug("Cancelled order id=%s contract=%s status=%s", order_id, contract, status)
        return status in ("cancelled", "closed")
    except RuntimeError as exc:
        if "404" in str(exc):
            log.debug("cancel_order: order %s already gone", order_id)
            return False
        raise


async def cancel_all_orders(
    session:   aiohttp.ClientSession,
    contract:  str,
) -> int:
    """
    Cancel all open orders for a contract.
    Returns count of cancelled orders.
    """
    if mm_config.dry_run:
        log.info("[DRY-RUN] cancel_all_orders contract=%s", contract)
        return 0

    path  = f"/futures/{SETTLE}/orders"
    query = {"contract": contract, "status": "open"}
    resp  = await _request(session, "DELETE", path, query=query)
    n = len(resp) if isinstance(resp, list) else 0
    log.info("Cancelled %d orders for %s", n, contract)
    return n


async def list_open_orders(
    session:  aiohttp.ClientSession,
    contract: str,
) -> List[Dict[str, Any]]:
    """List all open orders for a contract."""
    path  = f"/futures/{SETTLE}/orders"
    query = {"contract": contract, "status": "open", "limit": 100}
    return await _request(session, "GET", path, query=query)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _round_to_tick(price: Decimal, tick: Decimal) -> Decimal:
    """
    Floor price to nearest tick size.
    For a sell we floor; for a buy we also floor — joining the level.
    """
    return (price // tick) * tick
