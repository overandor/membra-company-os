"""LLM 15-Minute Signal Hunter — Multi-coin crypto prediction system.

Scans Gate.io futures, Jupiter DEX quotes, and Solana on-chain data,
then uses an LLM (Groq / OpenRouter / Gemini / heuristic fallback) to
predict 15-minute directional signals for each coin.

Profit is tracked per-signal in a local ledger so the system can
prove its cumulative edge over time.

System Law:
    LLM predicts direction only.  No live execution.  No real money moves.
    This is a research and analysis tool.
"""

import asyncio
import hashlib
import json
import math
import os
import random
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# LLM inference bridge (reuses llm-os module when importable)
# ---------------------------------------------------------------------------

try:
    from llm_os.inference import (
        GeminiBridge,
        GroqBridge,
        InferenceResult,
        OpenRouterBridge,
        StubBridge,
        get_inference_bridge,
    )
except ImportError:
    # Standalone mode — inline minimal bridges so the hunter can run
    # without the llm-os package installed.
    @dataclass
    class InferenceResult:  # type: ignore[no-redef]
        text: str = ""
        model: str = ""
        provider: str = ""
        tokens_used: int = 0
        cost_usd: float = 0.0
        latency_ms: float = 0.0
        success: bool = True
        error: Optional[str] = None
        metadata: dict = field(default_factory=dict)

    class StubBridge:  # type: ignore[no-redef]
        provider = "stub"
        def is_available(self):
            return True
        def generate(self, prompt, **kw):
            return InferenceResult(text="NO_TRADE", model="stub", provider="stub")

    def get_inference_bridge():  # type: ignore[no-redef]
        return StubBridge()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SYMBOLS = os.environ.get(
    "SYMBOLS", "SOL,BTC,ETH,JUP,WIF,BONK,RENDER,PYTH,HNT,RAY"
).split(",")

PREDICTION_HORIZON_MINUTES = int(os.environ.get("PREDICTION_HORIZON_MINUTES", "15"))
SCAN_INTERVAL_SECONDS = int(os.environ.get("SCAN_INTERVAL_SECONDS", "60"))
LEDGER_PATH = os.environ.get("SIGNAL_LEDGER_PATH", "/tmp/llm_signal_ledger.jsonl")

# Gate.io public API (no key needed for market data)
GATE_API_BASE = "https://api.gateio.ws/api/v4"

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MarketSnapshot:
    """Raw market data for one symbol at a point in time."""
    symbol: str
    ts: float
    price: float = 0.0
    price_change_pct: float = 0.0
    volume_24h: float = 0.0
    funding_rate: float = 0.0
    open_interest: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    spread_bps: float = 0.0
    volatility_1h: float = 0.0


@dataclass
class Signal:
    """A single directional prediction."""
    signal_id: str
    symbol: str
    direction: str  # "LONG", "SHORT", "NO_TRADE"
    confidence: float  # 0.0-1.0
    entry_price: float
    predicted_exit_price: float
    horizon_minutes: int
    reasoning: str
    provider: str  # which LLM / heuristic produced this
    created_at: float = field(default_factory=time.time)
    resolved: bool = False
    exit_price: Optional[float] = None
    resolved_at: Optional[float] = None
    pnl_bps: Optional[float] = None  # basis points


@dataclass
class ProfitLedger:
    """Cumulative P&L tracker."""
    total_signals: int = 0
    resolved_signals: int = 0
    winning_signals: int = 0
    losing_signals: int = 0
    total_pnl_bps: float = 0.0
    best_signal_bps: float = 0.0
    worst_signal_bps: float = 0.0
    cumulative_profit_usd: float = 0.0
    notional_per_trade_usd: float = 100.0  # virtual $100/trade


# ---------------------------------------------------------------------------
# Market data fetchers
# ---------------------------------------------------------------------------


def _http_get(url: str, timeout: int = 10) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, method="GET",
                                     headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_gate_futures_ticker(symbol: str) -> Optional[dict]:
    """Fetch Gate.io USDT futures ticker for *symbol*."""
    contract = f"{symbol}_USDT"
    url = f"{GATE_API_BASE}/futures/usdt/tickers?contract={contract}"
    data = _http_get(url)
    if isinstance(data, list) and data:
        return data[0]
    return None


def fetch_gate_spot_ticker(symbol: str) -> Optional[dict]:
    """Fetch Gate.io spot ticker as fallback."""
    pair = f"{symbol}_USDT"
    url = f"{GATE_API_BASE}/spot/tickers?currency_pair={pair}"
    data = _http_get(url)
    if isinstance(data, list) and data:
        return data[0]
    return None


def build_snapshot(symbol: str) -> MarketSnapshot:
    """Build a MarketSnapshot from available data sources."""
    snap = MarketSnapshot(symbol=symbol, ts=time.time())

    # Try futures first
    fticker = fetch_gate_futures_ticker(symbol)
    if fticker:
        snap.price = float(fticker.get("last", 0))
        snap.volume_24h = float(fticker.get("volume_24h_base", 0))
        snap.funding_rate = float(fticker.get("funding_rate", 0))
        snap.open_interest = float(fticker.get("total_size", 0))
        change = fticker.get("change_percentage")
        if change:
            snap.price_change_pct = float(change)
        hv = fticker.get("highest_bid")
        lv = fticker.get("lowest_ask")
        if hv and lv:
            snap.bid = float(hv)
            snap.ask = float(lv)
            mid = (snap.bid + snap.ask) / 2
            snap.spread_bps = ((snap.ask - snap.bid) / mid * 10_000) if mid else 0
        return snap

    # Fallback to spot
    sticker = fetch_gate_spot_ticker(symbol)
    if sticker:
        snap.price = float(sticker.get("last", 0))
        snap.volume_24h = float(sticker.get("base_volume", 0))
        change = sticker.get("change_percentage")
        if change:
            snap.price_change_pct = float(change)
        snap.bid = float(sticker.get("highest_bid", 0))
        snap.ask = float(sticker.get("lowest_ask", 0))
        mid = (snap.bid + snap.ask) / 2
        snap.spread_bps = ((snap.ask - snap.bid) / mid * 10_000) if mid else 0

    return snap


# ---------------------------------------------------------------------------
# LLM signal generation
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a quantitative crypto analyst. Given market data for a coin, "
    "predict its direction over the next {horizon} minutes.\n"
    "Respond with EXACTLY one JSON object on a single line:\n"
    '{{"direction":"LONG"|"SHORT"|"NO_TRADE","confidence":0.0-1.0,'
    '"predicted_move_bps":<int>,"reasoning":"<one sentence>"}}\n'
    "Do NOT add anything outside the JSON."
)


def _build_llm_prompt(snap: MarketSnapshot) -> str:
    return (
        f"Symbol: {snap.symbol}\n"
        f"Price: ${snap.price:,.6f}\n"
        f"24h Change: {snap.price_change_pct:+.2f}%\n"
        f"24h Volume: ${snap.volume_24h:,.0f}\n"
        f"Funding Rate: {snap.funding_rate:.6f}\n"
        f"Open Interest: {snap.open_interest:,.0f}\n"
        f"Bid/Ask Spread: {snap.spread_bps:.1f} bps\n"
        f"Timestamp: {datetime.fromtimestamp(snap.ts, tz=timezone.utc).isoformat()}\n"
    )


def _parse_llm_response(text: str) -> dict:
    """Try to extract direction JSON from LLM output."""
    text = text.strip()
    # Find first { … } block
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    # Keyword fallback
    upper = text.upper()
    if "LONG" in upper:
        return {"direction": "LONG", "confidence": 0.5, "predicted_move_bps": 30,
                "reasoning": "LLM indicated LONG"}
    if "SHORT" in upper:
        return {"direction": "SHORT", "confidence": 0.5, "predicted_move_bps": -30,
                "reasoning": "LLM indicated SHORT"}
    return {"direction": "NO_TRADE", "confidence": 0.3, "predicted_move_bps": 0,
            "reasoning": "Could not parse LLM response"}


def generate_signal_llm(snap: MarketSnapshot,
                        bridge=None) -> Signal:
    """Use LLM to generate a directional signal."""
    bridge = bridge or get_inference_bridge()
    sys_prompt = _SYSTEM_PROMPT.format(horizon=PREDICTION_HORIZON_MINUTES)
    user_prompt = _build_llm_prompt(snap)

    result = bridge.generate(user_prompt, system_prompt=sys_prompt,
                             max_tokens=256, temperature=0.4)

    if result.success and result.text:
        parsed = _parse_llm_response(result.text)
    else:
        parsed = {"direction": "NO_TRADE", "confidence": 0.0,
                  "predicted_move_bps": 0,
                  "reasoning": f"LLM error: {result.error}"}

    direction = parsed.get("direction", "NO_TRADE").upper()
    if direction not in ("LONG", "SHORT", "NO_TRADE"):
        direction = "NO_TRADE"
    confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.5))))
    move_bps = float(parsed.get("predicted_move_bps", 0))

    predicted_exit = snap.price * (1 + move_bps / 10_000) if snap.price else 0

    sig_seed = f"{snap.symbol}:{snap.ts}:{direction}:{time.time()}"
    signal_id = hashlib.sha256(sig_seed.encode()).hexdigest()[:16]

    return Signal(
        signal_id=signal_id,
        symbol=snap.symbol,
        direction=direction,
        confidence=confidence,
        entry_price=snap.price,
        predicted_exit_price=predicted_exit,
        horizon_minutes=PREDICTION_HORIZON_MINUTES,
        reasoning=parsed.get("reasoning", ""),
        provider=result.provider if result.success else "heuristic",
    )


# ---------------------------------------------------------------------------
# Heuristic fallback (zero-cost, deterministic)
# ---------------------------------------------------------------------------


def generate_signal_heuristic(snap: MarketSnapshot) -> Signal:
    """Rule-based signal when LLM is unavailable."""
    direction = "NO_TRADE"
    confidence = 0.0
    reasoning = "Insufficient data"
    move_bps = 0.0

    if snap.price <= 0:
        pass
    elif snap.price_change_pct > 2.0 and snap.funding_rate < 0.0005:
        direction = "LONG"
        confidence = 0.55
        move_bps = 20
        reasoning = "Momentum up + low funding = continuation likely"
    elif snap.price_change_pct < -2.0 and snap.funding_rate > 0.001:
        direction = "SHORT"
        confidence = 0.55
        move_bps = -20
        reasoning = "Momentum down + high funding = drop likely"
    elif abs(snap.price_change_pct) < 0.3 and snap.spread_bps > 50:
        direction = "NO_TRADE"
        confidence = 0.7
        reasoning = "Low volatility + wide spread = no edge"
    elif snap.funding_rate > 0.002:
        direction = "SHORT"
        confidence = 0.50
        move_bps = -15
        reasoning = "Extreme positive funding = mean reversion short"
    elif snap.funding_rate < -0.001:
        direction = "LONG"
        confidence = 0.50
        move_bps = 15
        reasoning = "Negative funding = mean reversion long"

    predicted_exit = snap.price * (1 + move_bps / 10_000) if snap.price else 0

    sig_seed = f"heur:{snap.symbol}:{snap.ts}:{direction}"
    signal_id = hashlib.sha256(sig_seed.encode()).hexdigest()[:16]

    return Signal(
        signal_id=signal_id,
        symbol=snap.symbol,
        direction=direction,
        confidence=confidence,
        entry_price=snap.price,
        predicted_exit_price=predicted_exit,
        horizon_minutes=PREDICTION_HORIZON_MINUTES,
        reasoning=reasoning,
        provider="heuristic",
    )


# ---------------------------------------------------------------------------
# Signal resolution & P&L
# ---------------------------------------------------------------------------


def resolve_signal(sig: Signal, current_price: float) -> Signal:
    """Mark a signal as resolved and compute P&L in basis points."""
    if sig.entry_price <= 0:
        sig.resolved = True
        sig.exit_price = current_price
        sig.resolved_at = time.time()
        sig.pnl_bps = 0.0
        return sig

    raw_move_bps = ((current_price - sig.entry_price) / sig.entry_price) * 10_000

    if sig.direction == "LONG":
        sig.pnl_bps = raw_move_bps
    elif sig.direction == "SHORT":
        sig.pnl_bps = -raw_move_bps
    else:
        sig.pnl_bps = 0.0

    sig.exit_price = current_price
    sig.resolved = True
    sig.resolved_at = time.time()
    return sig


# ---------------------------------------------------------------------------
# Ledger persistence
# ---------------------------------------------------------------------------


def append_to_ledger(sig: Signal, path: str = "") -> None:
    path = path or LEDGER_PATH
    with open(path, "a") as fh:
        fh.write(json.dumps(asdict(sig), default=str) + "\n")


def load_ledger(path: str = "") -> List[dict]:
    path = path or LEDGER_PATH
    if not os.path.exists(path):
        return []
    entries: List[dict] = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def compute_profit_summary(entries: List[dict]) -> dict:
    """Compute cumulative P&L from ledger entries."""
    ledger = ProfitLedger()
    ledger.total_signals = len(entries)

    for e in entries:
        if not e.get("resolved"):
            continue
        ledger.resolved_signals += 1
        pnl = e.get("pnl_bps", 0.0) or 0.0
        ledger.total_pnl_bps += pnl

        trade_profit = (pnl / 10_000) * ledger.notional_per_trade_usd
        ledger.cumulative_profit_usd += trade_profit

        if pnl > 0:
            ledger.winning_signals += 1
        elif pnl < 0:
            ledger.losing_signals += 1

        if pnl > ledger.best_signal_bps:
            ledger.best_signal_bps = pnl
        if pnl < ledger.worst_signal_bps:
            ledger.worst_signal_bps = pnl

    return asdict(ledger)


# ---------------------------------------------------------------------------
# Full scan cycle
# ---------------------------------------------------------------------------


def run_scan_cycle(symbols: List[str] = None, bridge=None) -> Dict:
    """Run one full scan cycle across all symbols.

    Returns a summary dict with snapshots, signals, and profit stats.
    """
    symbols = symbols or SYMBOLS
    bridge = bridge or get_inference_bridge()

    snapshots: List[MarketSnapshot] = []
    signals: List[Signal] = []

    for sym in symbols:
        snap = build_snapshot(sym.strip())
        snapshots.append(snap)

        # Use LLM if available, else heuristic
        if bridge.is_available() and bridge.__class__.__name__ != "StubBridge":
            sig = generate_signal_llm(snap, bridge=bridge)
        else:
            sig = generate_signal_heuristic(snap)

        signals.append(sig)
        append_to_ledger(sig)

    # Try to resolve any older unresolved signals from previous cycles
    entries = load_ledger()
    price_cache = {s.symbol: s.price for s in snapshots}
    newly_resolved = 0
    for entry in entries:
        if entry.get("resolved"):
            continue
        sym = entry.get("symbol", "")
        if sym not in price_cache:
            continue
        created = entry.get("created_at", 0)
        horizon_s = entry.get("horizon_minutes", PREDICTION_HORIZON_MINUTES) * 60
        if time.time() - created < horizon_s:
            continue
        # Resolve
        sig_obj = Signal(**{k: entry[k] for k in Signal.__dataclass_fields__ if k in entry})
        resolve_signal(sig_obj, price_cache[sym])
        append_to_ledger(sig_obj)
        newly_resolved += 1

    # Reload and compute summary
    all_entries = load_ledger()
    profit_summary = compute_profit_summary(all_entries)

    return {
        "ts": time.time(),
        "iso": datetime.now(timezone.utc).isoformat(),
        "symbols_scanned": len(symbols),
        "signals_generated": len(signals),
        "newly_resolved": newly_resolved,
        "provider": bridge.__class__.__name__,
        "profit_summary": profit_summary,
        "signals": [asdict(s) for s in signals],
        "snapshots": [asdict(s) for s in snapshots],
    }


# ---------------------------------------------------------------------------
# Async web server (aiohttp-based, same stack as the main app)
# ---------------------------------------------------------------------------

_latest_cycle: Dict = {}


async def _scan_loop():
    """Background loop that scans every SCAN_INTERVAL_SECONDS."""
    global _latest_cycle
    while True:
        try:
            _latest_cycle = run_scan_cycle()
        except Exception as exc:
            _latest_cycle = {"error": str(exc), "ts": time.time()}
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)


def get_latest_cycle() -> Dict:
    """Return the most recent scan cycle result (used by app.py)."""
    return _latest_cycle


async def start_background_scanner():
    """Start the background scanner task (call from the main event loop)."""
    asyncio.ensure_future(_scan_loop())


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("[signal-hunter] Running one scan cycle...")
    result = run_scan_cycle()
    print(json.dumps(result, indent=2, default=str))
    print(f"\n[signal-hunter] Profit summary: {json.dumps(result['profit_summary'], indent=2)}")
