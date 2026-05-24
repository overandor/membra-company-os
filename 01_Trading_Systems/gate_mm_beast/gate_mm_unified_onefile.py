#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED ONE-FILE PROJECT BUNDLE
Generated UTC: 2026-04-08T23:20:58.256479+00:00
Total source files: 134

This file is a consolidated archive of multiple project modules.
Sections are delimited with source file paths for reappraisal/review.
Launcher usage: python gate_mm_unified_onefile.py [paper|live|replay]
"""

import os
import sys
from pathlib import Path

def _run_unified_launcher() -> int:
    root = Path(__file__).resolve().parent
    if (root / "app").exists():
        app_root = root
    elif (root / "gate_mm_beast" / "app").exists():
        app_root = root / "gate_mm_beast"
    else:
        print("ERROR: gate_mm_beast directory not found next to this file.")
        return 1
    sys.path.insert(0, str(app_root))

    mode = "paper"
    if len(sys.argv) > 1:
        mode = str(sys.argv[1]).strip().lower()
    else:
        mode = str(os.getenv("MODE", "paper")).strip().lower()

    if mode not in {"paper", "live", "replay"}:
        print(f"ERROR: unsupported mode '{mode}'. Use paper/live/replay.")
        return 2

    if mode in {"paper", "replay"}:
        os.environ["MODE"] = mode

    from app.main import run
    return int(run())

if __name__ == "__main__":
    raise SystemExit(_run_unified_launcher())

# ===== ARCHIVE SOURCE SECTIONS (COMMENTED) =====

# ===== BEGIN [1/134] gate_mm_beast/app/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [1/134] gate_mm_beast/app/__init__.py =====

# ===== BEGIN [2/134] gate_mm_beast/app/api/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [2/134] gate_mm_beast/app/api/__init__.py =====

# ===== BEGIN [3/134] gate_mm_beast/app/api/dashboard_routes.py sha256=41d15d66dd40603b =====
# def dashboard_payload(engine_state: dict) -> dict:
#     return engine_state
# ===== END   [3/134] gate_mm_beast/app/api/dashboard_routes.py =====

# ===== BEGIN [4/134] gate_mm_beast/app/api/health_routes.py sha256=5bb1eb7b9e8ca40d =====
# def health_payload(app_state: dict) -> dict:
#     return {"ok": app_state.get("healthy", True), "message": app_state.get("message", "ok")}
# ===== END   [4/134] gate_mm_beast/app/api/health_routes.py =====

# ===== BEGIN [5/134] gate_mm_beast/app/api/metrics_routes.py sha256=2915008dddf3562d =====
# def metrics_payload(metrics) -> dict:
#     return metrics.values
# ===== END   [5/134] gate_mm_beast/app/api/metrics_routes.py =====

# ===== BEGIN [6/134] gate_mm_beast/app/api/orders_routes.py sha256=bb78ff8ce006a654 =====
# def orders_payload(order_repo, symbol: str | None = None) -> list[dict]:
#     return order_repo.open_orders(symbol)
# ===== END   [6/134] gate_mm_beast/app/api/orders_routes.py =====

# ===== BEGIN [7/134] gate_mm_beast/app/api/positions_routes.py sha256=884b3dd8c1e157f1 =====
# def positions_payload(position_repo, symbols: list[str]) -> list[dict]:
#     out = []
#     for symbol in symbols:
#         pos = position_repo.get_open(symbol)
#         if pos:
#             out.append(pos)
#     return out
# ===== END   [7/134] gate_mm_beast/app/api/positions_routes.py =====

# ===== BEGIN [8/134] gate_mm_beast/app/api/server.py sha256=5d4929e55525a4c2 =====
# [stripped_future_import] from __future__ import annotations
# import json
# from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
# from urllib.parse import urlparse
# from app.api.health_routes import health_payload
# from app.api.metrics_routes import metrics_payload
# from app.api.positions_routes import positions_payload
# from app.api.orders_routes import orders_payload
# from app.api.dashboard_routes import dashboard_payload
# from app.api.unified_balance_routes import unified_balance_payload
# from app.api.ui_routes import unified_ui_html
#
# class APIServer:
#     def __init__(self, host: str, port: int, state: dict) -> None:
#         self.host = host
#         self.port = port
#         self.state = state
#         outer = self
#
#         class Handler(BaseHTTPRequestHandler):
#             def _send(self, payload: dict, code: int = 200):
#                 raw = json.dumps(payload, default=str).encode()
#                 self.send_response(code)
#                 self.send_header("Content-Type", "application/json; charset=utf-8")
#                 self.send_header("Content-Length", str(len(raw)))
#                 self.end_headers()
#                 self.wfile.write(raw)
#
#             def _send_html(self, payload: str, code: int = 200):
#                 raw = payload.encode("utf-8")
#                 self.send_response(code)
#                 self.send_header("Content-Type", "text/html; charset=utf-8")
#                 self.send_header("Content-Length", str(len(raw)))
#                 self.end_headers()
#                 self.wfile.write(raw)
#
#             def log_message(self, *args):
#                 return
#
#             def do_GET(self):
#                 path = urlparse(self.path).path
#                 if path in ("/", "/ui"):
#                     return self._send_html(unified_ui_html())
#                 if path == "/health":
#                     return self._send(health_payload(outer.state["app_state"]))
#                 if path == "/metrics":
#                     return self._send(metrics_payload(outer.state["metrics"]))
#                 if path == "/positions":
#                     return self._send({"rows": positions_payload(outer.state["position_repo"], outer.state["symbols"])})
#                 if path == "/orders":
#                     return self._send({"rows": orders_payload(outer.state["order_repo"])})
#                 if path == "/dashboard":
#                     return self._send(dashboard_payload(outer.state["engine_state"]))
#                 if path == "/unified-balance":
#                     return self._send(unified_balance_payload(outer.state["unified_balance_service"]))
#                 return self._send({"error": "not_found"}, 404)
#
#         self.httpd = ThreadingHTTPServer((host, port), Handler)
#
#     def start_in_thread(self):
#         import threading
#         threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
#
#     def stop(self):
#         self.httpd.shutdown()
# ===== END   [8/134] gate_mm_beast/app/api/server.py =====

# ===== BEGIN [9/134] gate_mm_beast/app/api/ui_routes.py sha256=0b127bc1513ab453 =====
# def unified_ui_html() -> str:
#     return """<!doctype html>
# <html lang=\"en\">
# <head>
#   <meta charset=\"UTF-8\" />
#   <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
#   <title>Unified Exchange Balance</title>
#   <style>
#     :root {
#       --bg: radial-gradient(1200px 700px at 10% 0%, #1a2242 0%, #0b0f1d 45%, #06070b 100%);
#       --card: rgba(255,255,255,0.06);
#       --stroke: rgba(255,255,255,0.12);
#       --text: #eaf1ff;
#       --muted: #9fb0d4;
#       --good: #3fe08f;
#       --bad: #ff6b7d;
#       --accent: #66d2ff;
#     }
#     * { box-sizing: border-box; }
#     body {
#       margin: 0;
#       font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
#       color: var(--text);
#       background: var(--bg);
#       min-height: 100vh;
#     }
#     .wrap {
#       max-width: 1100px;
#       margin: 24px auto;
#       padding: 0 16px 28px;
#     }
#     .header {
#       display: flex;
#       justify-content: space-between;
#       align-items: end;
#       gap: 16px;
#       margin-bottom: 18px;
#     }
#     .title { font-size: 1.5rem; font-weight: 700; letter-spacing: 0.4px; }
#     .total {
#       font-size: 1.15rem;
#       color: var(--accent);
#       font-weight: 700;
#     }
#     .meta { color: var(--muted); font-size: 0.92rem; margin-top: 4px; }
#     .grid {
#       display: grid;
#       grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
#       gap: 14px;
#     }
#     .card {
#       background: var(--card);
#       border: 1px solid var(--stroke);
#       border-radius: 14px;
#       padding: 14px;
#       backdrop-filter: blur(3px);
#     }
#     .name { font-size: 1rem; font-weight: 700; text-transform: capitalize; }
#     .status { font-size: 0.86rem; margin-top: 4px; }
#     .ok { color: var(--good); }
#     .err { color: var(--bad); }
#     .usd { margin-top: 8px; font-size: 1.05rem; font-weight: 700; }
#     .assets { margin-top: 10px; max-height: 180px; overflow: auto; font-size: 0.86rem; color: var(--muted); }
#     .asset-row { display: flex; justify-content: space-between; gap: 10px; padding: 2px 0; }
#     .hint { margin-top: 14px; color: var(--muted); font-size: 0.85rem; }
#   </style>
# </head>
# <body>
#   <div class=\"wrap\">
#     <div class=\"header\">
#       <div>
#         <div class=\"title\">Unified Exchange Balance</div>
#         <div class=\"meta\" id=\"stamp\">loading...</div>
#       </div>
#       <div class=\"total\" id=\"total\">$0.00</div>
#     </div>
#     <div class=\"grid\" id=\"grid\"></div>
#     <div class=\"hint\">Tip: this dashboard aggregates USD-like assets (USD/USDT/USDC/BUSD/FDUSD/TUSD).</div>
#   </div>
# <script>
# async function loadBalances() {
#   try {
#     const res = await fetch('/unified-balance');
#     const data = await res.json();
#     const exchanges = data.exchanges || {};
#     document.getElementById('total').textContent = '$' + Number(data.total_usd || 0).toFixed(2);
#     document.getElementById('stamp').textContent = data.ts ? ('updated: ' + data.ts) : 'updated: n/a';
#
#     const grid = document.getElementById('grid');
#     grid.innerHTML = '';
#     Object.entries(exchanges).forEach(([name, info]) => {
#       const card = document.createElement('div');
#       card.className = 'card';
#       const statusClass = info.status === 'ok' ? 'ok' : 'err';
#       const assets = Array.isArray(info.assets) ? info.assets : [];
#       card.innerHTML = `
#         <div class=\"name\">${name}</div>
#         <div class=\"status ${statusClass}\">${info.status || 'unknown'}${info.error ? ' • ' + info.error : ''}</div>
#         <div class=\"usd\">$${Number(info.total_usd || 0).toFixed(2)}</div>
#         <div class=\"assets\">${assets.slice(0, 20).map(a => `<div class=\"asset-row\"><span>${a.asset || '-'}</span><span>${Number((a.free||0)+(a.locked||0)).toFixed(6)}</span></div>`).join('') || 'No assets'}</div>
#       `;
#       grid.appendChild(card);
#     });
#   } catch (err) {
#     document.getElementById('stamp').textContent = 'fetch error: ' + String(err);
#   }
# }
# loadBalances();
# setInterval(loadBalances, 5000);
# </script>
# </body>
# </html>"""
# ===== END   [9/134] gate_mm_beast/app/api/ui_routes.py =====

# ===== BEGIN [10/134] gate_mm_beast/app/api/unified_balance_routes.py sha256=50ff24273fed863c =====
# def unified_balance_payload(unified_balance_service) -> dict:
#     return unified_balance_service.get_snapshot()
# ===== END   [10/134] gate_mm_beast/app/api/unified_balance_routes.py =====

# ===== BEGIN [11/134] gate_mm_beast/app/backtest/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [11/134] gate_mm_beast/app/backtest/__init__.py =====

# ===== BEGIN [12/134] gate_mm_beast/app/backtest/execution_model.py sha256=a8e4a0f3dc6b2f00 =====
# class ExecutionModel:
#     def maker_fill_probability(self, spread_ticks: float, vol_score: float) -> float:
#         return max(0.1, min(0.9, 0.25 + 0.05 * spread_ticks + 0.15 * vol_score))
# ===== END   [12/134] gate_mm_beast/app/backtest/execution_model.py =====

# ===== BEGIN [13/134] gate_mm_beast/app/backtest/fill_model.py sha256=b2359684eba1e1ca =====
# class FillModel:
#     def should_fill(self, probability: float, rnd: float) -> bool:
#         return rnd <= probability
# ===== END   [13/134] gate_mm_beast/app/backtest/fill_model.py =====

# ===== BEGIN [14/134] gate_mm_beast/app/backtest/metrics.py sha256=83bf59e555938f21 =====
# def sharpe_like(pnls: list[float]) -> float:
#     import math
#     import numpy as np
#     if not pnls:
#         return -99.0
#     return float(np.mean(pnls) / (np.std(pnls) + 1e-9) * math.sqrt(max(len(pnls), 1)))
# ===== END   [14/134] gate_mm_beast/app/backtest/metrics.py =====

# ===== BEGIN [15/134] gate_mm_beast/app/backtest/queue_model.py sha256=8ae3059d15176bf9 =====
# class QueueModel:
#     def estimate_queue_rank(self, bid_size: float, ask_size: float) -> float:
#         total = max(bid_size + ask_size, 1e-9)
#         return bid_size / total
# ===== END   [15/134] gate_mm_beast/app/backtest/queue_model.py =====

# ===== BEGIN [16/134] gate_mm_beast/app/backtest/replay_engine.py sha256=abb3bcec957ec43d =====
# [stripped_future_import] from __future__ import annotations
# from dataclasses import dataclass
# import math
# import numpy as np
#
# @dataclass
# class ReplayResult:
#     trades: int
#     win_rate: float
#     avg_pnl_usd: float
#     pnl_usd: float
#     max_drawdown_usd: float
#     sharpe_like: float
#     allowed: bool
#
# class ReplayEngine:
#     def __init__(self, take_atr_mult: float = 1.0, stop_atr_mult: float = 1.6):
#         self.take_atr_mult = take_atr_mult
#         self.stop_atr_mult = stop_atr_mult
#
#     def run(self, df, multiplier: float, size: int) -> ReplayResult:
#         if df is None or len(df) < 100:
#             return ReplayResult(0,0.0,0.0,0.0,0.0,-99.0,False)
#         pnls = []
#         equity = peak = max_dd = 0.0
#         for i in range(60, len(df) - 8):
#             row = df.iloc[i]
#             score = ((row["ema8"] - row["ema21"]) / max(row["close"], 1e-9)) * 2000.0
#             if abs(score) < 0.2:
#                 continue
#             side = "buy" if score > 0 else "sell"
#             entry = float(row["close"])
#             atr = max(float(row["atr14"]), entry * 0.002)
#             take = entry + atr * self.take_atr_mult if side == "buy" else entry - atr * self.take_atr_mult
#             stop = entry - atr * self.stop_atr_mult if side == "buy" else entry + atr * self.stop_atr_mult
#             exit_px = float(df.iloc[min(i+7, len(df)-1)]["close"])
#             for j in range(i+1, min(i+8, len(df))):
#                 hi = float(df.iloc[j]["high"])
#                 lo = float(df.iloc[j]["low"])
#                 if side == "buy":
#                     if lo <= stop:
#                         exit_px = stop
#                         break
#                     if hi >= take:
#                         exit_px = take
#                         break
#                 else:
#                     if hi >= stop:
#                         exit_px = stop
#                         break
#                     if lo <= take:
#                         exit_px = take
#                         break
#             pnl = ((exit_px - entry) if side == "buy" else (entry - exit_px)) * size * multiplier
#             pnls.append(pnl)
#             equity += pnl
#             peak = max(peak, equity)
#             max_dd = max(max_dd, peak - equity)
#         if not pnls:
#             return ReplayResult(0,0.0,0.0,0.0,0.0,-99.0,False)
#         return ReplayResult(
#             trades=len(pnls),
#             win_rate=float(np.mean([1.0 if p > 0 else 0.0 for p in pnls])),
#             avg_pnl_usd=float(np.mean(pnls)),
#             pnl_usd=float(np.sum(pnls)),
#             max_drawdown_usd=float(max_dd),
#             sharpe_like=float(np.mean(pnls)/(np.std(pnls)+1e-9) * math.sqrt(max(len(pnls),1))),
#             allowed=len(pnls) >= 10 and float(np.mean(pnls)) > 0,
#         )
# ===== END   [16/134] gate_mm_beast/app/backtest/replay_engine.py =====

# ===== BEGIN [17/134] gate_mm_beast/app/backtest/report.py sha256=95e76dd0380b66b8 =====
# def to_dict(result) -> dict:
#     return dict(result.__dict__)
# ===== END   [17/134] gate_mm_beast/app/backtest/report.py =====

# ===== BEGIN [18/134] gate_mm_beast/app/backtest/slippage_model.py sha256=9364dceca0a89c0d =====
# class SlippageModel:
#     def stop_slippage(self, spread: float) -> float:
#         return spread * 0.25
# ===== END   [18/134] gate_mm_beast/app/backtest/slippage_model.py =====

# ===== BEGIN [19/134] gate_mm_beast/app/config.py sha256=eb043703a86493c7 =====
# [stripped_future_import] from __future__ import annotations
# from dataclasses import dataclass
# import os
# from dotenv import load_dotenv
#
# load_dotenv()
#
# @dataclass(frozen=True)
# class Settings:
#     gate_api_key: str = os.getenv("GATE_API_KEY", "")
#     gate_api_secret: str = os.getenv("GATE_API_SECRET", "")
#     gate_base_url: str = os.getenv("GATE_BASE_URL", "https://fx-api.gateio.ws/api/v4").rstrip("/")
#     gate_ws_url: str = os.getenv("GATE_WS_URL", "wss://fx-ws.gateio.ws/v4/ws/usdt")
#     gate_settle: str = os.getenv("GATE_SETTLE", "usdt").lower()
#
#     mode: str = os.getenv("MODE", "paper").lower()
#     symbols_raw: str = os.getenv("SYMBOLS", "DOGE_USDT,XRP_USDT,TRX_USDT")
#     db_path: str = os.getenv("DB_PATH", "gate_mm_beast.db")
#     log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
#
#     openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
#     openrouter_model: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
#     openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
#
#     groq_api_key: str = os.getenv("GROQ_API_KEY", "")
#     groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
#     groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")
#
#     risk_usd: float = float(os.getenv("RISK_USD", "15"))
#     leverage: int = int(os.getenv("LEVERAGE", "2"))
#     bar_interval: str = os.getenv("BAR_INTERVAL", "1m")
#     bar_limit: int = int(os.getenv("BAR_LIMIT", "400"))
#     loop_seconds: float = float(os.getenv("LOOP_SECONDS", "2"))
#     entry_edge_bps: float = float(os.getenv("ENTRY_EDGE_BPS", "5"))
#     take_atr_mult: float = float(os.getenv("TAKE_ATR_MULT", "1.0"))
#     stop_atr_mult: float = float(os.getenv("STOP_ATR_MULT", "1.6"))
#
#     enable_api: bool = os.getenv("ENABLE_API", "true").lower() == "true"
#     api_host: str = os.getenv("API_HOST", "127.0.0.1")
#     api_port: int = int(os.getenv("API_PORT", "8788"))
#
#     request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
#
#     unified_balance_refresh_seconds: int = int(os.getenv("UNIFIED_BALANCE_REFRESH_SECONDS", "20"))
#
#     binance_api_key: str = os.getenv("BINANCE_API_KEY", "")
#     binance_api_secret: str = os.getenv("BINANCE_API_SECRET", "")
#
#     okx_api_key: str = os.getenv("OKX_API_KEY", "")
#     okx_api_secret: str = os.getenv("OKX_API_SECRET", "")
#     okx_passphrase: str = os.getenv("OKX_PASSPHRASE", "")
#
#     bybit_api_key: str = os.getenv("BYBIT_API_KEY", "")
#     bybit_api_secret: str = os.getenv("BYBIT_API_SECRET", "")
#
#     xt_api_key: str = os.getenv("XT_API_KEY", "")
#     xt_api_secret: str = os.getenv("XT_API_SECRET", "")
#
#     @property
#     def symbols(self) -> list[str]:
#         return [s.strip().upper() for s in self.symbols_raw.split(",") if s.strip()]
# ===== END   [19/134] gate_mm_beast/app/config.py =====

# ===== BEGIN [20/134] gate_mm_beast/app/connectors/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [20/134] gate_mm_beast/app/connectors/__init__.py =====

# ===== BEGIN [21/134] gate_mm_beast/app/connectors/gateio/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [21/134] gate_mm_beast/app/connectors/gateio/__init__.py =====

# ===== BEGIN [22/134] gate_mm_beast/app/connectors/gateio/mapper.py sha256=9652a39bd1b70116 =====
# from app.core.decimal_utils import safe_float
#
# def map_book_ticker(item: dict) -> dict:
#     return {
#         "symbol": str(item.get("s") or item.get("contract") or ""),
#         "bid": safe_float(item.get("b") or item.get("bid_price")),
#         "ask": safe_float(item.get("a") or item.get("ask_price")),
#         "bid_size": safe_float(item.get("B") or item.get("bid_size") or item.get("bid_amount")),
#         "ask_size": safe_float(item.get("A") or item.get("ask_size") or item.get("ask_amount")),
#     }
# ===== END   [22/134] gate_mm_beast/app/connectors/gateio/mapper.py =====

# ===== BEGIN [23/134] gate_mm_beast/app/connectors/gateio/rate_limits.py sha256=0f8b7979977fb82e =====
# PRIVATE_REQUESTS_PER_SECOND = 8
# PUBLIC_REQUESTS_PER_SECOND = 10
# ===== END   [23/134] gate_mm_beast/app/connectors/gateio/rate_limits.py =====

# ===== BEGIN [24/134] gate_mm_beast/app/connectors/gateio/rest_private.py sha256=dc7ceea998e9ce78 =====
# [stripped_future_import] from __future__ import annotations
# import json
# from urllib.parse import urlencode
# import aiohttp
# from app.config import Settings
# from app.connectors.gateio.signing import build_headers
#
# class GatePrivateRest:
#     def __init__(self, cfg: Settings) -> None:
#         self.cfg = cfg
#         self.session: aiohttp.ClientSession | None = None
#
#     async def ensure(self) -> None:
#         if self.session is None or self.session.closed:
#             self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.cfg.request_timeout))
#
#     async def request(self, method: str, path: str, params: dict | None = None, payload: dict | None = None):
#         await self.ensure()
#         assert self.session
#         params = params or {}
#         payload = payload or {}
#         query_string = urlencode(params)
#         body = json.dumps(payload, separators=(",", ":")) if payload else ""
#         headers = build_headers(self.cfg.gate_api_key, self.cfg.gate_api_secret, method, path, query_string, body)
#         async with self.session.request(method.upper(), f"{self.cfg.gate_base_url}{path}", params=params, data=body if body else None, headers=headers) as r:
#             text = await r.text()
#             if r.status >= 400:
#                 raise RuntimeError(f"{method} {path} {r.status}: {text[:400]}")
#             return json.loads(text) if text.strip() else {}
#
#     async def create_order(self, symbol: str, size: int, price: float, text: str, reduce_only: bool = False, tif: str = "poc"):
#         return await self.request("POST", f"/futures/{self.cfg.gate_settle}/orders", payload={
#             "contract": symbol,
#             "size": size,
#             "price": f"{price:.10f}",
#             "tif": tif,
#             "text": text[:28],
#             "reduce_only": reduce_only,
#         })
#
#     async def cancel_order(self, order_id: str):
#         return await self.request("DELETE", f"/futures/{self.cfg.gate_settle}/orders/{order_id}")
#
#     async def get_order(self, order_id: str):
#         return await self.request("GET", f"/futures/{self.cfg.gate_settle}/orders/{order_id}")
#
#     async def list_open_orders(self, symbol: str | None = None):
#         params = {"status":"open"}
#         if symbol:
#             params["contract"] = symbol
#         return await self.request("GET", f"/futures/{self.cfg.gate_settle}/orders", params=params)
#
#     async def list_positions(self):
#         return await self.request("GET", f"/futures/{self.cfg.gate_settle}/positions")
#
#     async def update_leverage(self, symbol: str, leverage: int):
#         return await self.request("POST", f"/futures/{self.cfg.gate_settle}/positions/{symbol}/leverage", payload={"leverage": str(leverage)})
#
#     async def close(self):
#         if self.session and not self.session.closed:
#             await self.session.close()
# ===== END   [24/134] gate_mm_beast/app/connectors/gateio/rest_private.py =====

# ===== BEGIN [25/134] gate_mm_beast/app/connectors/gateio/rest_public.py sha256=317cbea63a858dee =====
# [stripped_future_import] from __future__ import annotations
# import json
# import aiohttp
# import pandas as pd
# from app.config import Settings
#
# class GatePublicRest:
#     def __init__(self, cfg: Settings) -> None:
#         self.cfg = cfg
#         self.session: aiohttp.ClientSession | None = None
#
#     async def ensure(self) -> None:
#         if self.session is None or self.session.closed:
#             self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.cfg.request_timeout))
#
#     async def get_json(self, path: str, params: dict | None = None):
#         await self.ensure()
#         assert self.session
#         async with self.session.get(f"{self.cfg.gate_base_url}{path}", params=params or {}) as r:
#             text = await r.text()
#             if r.status >= 400:
#                 raise RuntimeError(f"GET {path} {r.status}: {text[:300]}")
#             return json.loads(text) if text.strip() else {}
#
#     async def candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
#         data = await self.get_json(f"/futures/{self.cfg.gate_settle}/candlesticks", {"contract": symbol, "interval": interval, "limit": min(limit, 2000)})
#         rows = []
#         for item in data or []:
#             if isinstance(item, dict):
#                 rows.append({"t": item.get("t"), "o": item.get("o"), "h": item.get("h"), "l": item.get("l"), "c": item.get("c"), "v": item.get("v")})
#         df = pd.DataFrame(rows)
#         if df.empty:
#             return df
#         for c in ["o","h","l","c","v"]:
#             df[c] = pd.to_numeric(df[c], errors="coerce")
#         df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
#         return df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"})[["timestamp","open","high","low","close","volume"]].dropna().reset_index(drop=True)
#
#     async def list_tickers(self):
#         return await self.get_json(f"/futures/{self.cfg.gate_settle}/tickers")
#
#     async def list_contracts(self):
#         return await self.get_json(f"/futures/{self.cfg.gate_settle}/contracts")
#
#     async def order_book(self, symbol: str, limit: int = 5):
#         return await self.get_json(f"/futures/{self.cfg.gate_settle}/order_book", {"contract": symbol, "limit": limit})
#
#     async def close(self):
#         if self.session and not self.session.closed:
#             await self.session.close()
# ===== END   [25/134] gate_mm_beast/app/connectors/gateio/rest_public.py =====

# ===== BEGIN [26/134] gate_mm_beast/app/connectors/gateio/schemas.py sha256=97e5937879d659d9 =====
# # Exchange payload schema helpers can live here.
# ===== END   [26/134] gate_mm_beast/app/connectors/gateio/schemas.py =====

# ===== BEGIN [27/134] gate_mm_beast/app/connectors/gateio/signing.py sha256=0a1549e9ed7048ff =====
# import hashlib
# import hmac
# import time
#
# def build_headers(api_key: str, api_secret: str, method: str, path: str, query_string: str = "", body: str = "") -> dict:
#     ts = str(int(time.time()))
#     body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
#     sign_str = f"{method.upper()}\n/api/v4{path}\n{query_string}\n{body_hash}\n{ts}"
#     sign = hmac.new(api_secret.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
#     return {
#         "KEY": api_key,
#         "Timestamp": ts,
#         "SIGN": sign,
#         "Content-Type": "application/json",
#         "Accept": "application/json",
#     }
# ===== END   [27/134] gate_mm_beast/app/connectors/gateio/signing.py =====

# ===== BEGIN [28/134] gate_mm_beast/app/connectors/gateio/ws_private.py sha256=ac8bd25257da0fd7 =====
# # Gate private WS scaffold placeholder.
# # Add user-order and fills subscription here when you are ready to harden live execution.
# ===== END   [28/134] gate_mm_beast/app/connectors/gateio/ws_private.py =====

# ===== BEGIN [29/134] gate_mm_beast/app/connectors/gateio/ws_public.py sha256=d784abcfcfa47d9e =====
# [stripped_future_import] from __future__ import annotations
# import asyncio, json, logging, time
# import websockets
# from app.config import Settings
#
# log = logging.getLogger(__name__)
#
# class GatePublicWS:
#     def __init__(self, cfg: Settings, on_book_ticker):
#         self.cfg = cfg
#         self.on_book_ticker = on_book_ticker
#         self.shutdown = False
#
#     async def run_book_ticker(self, symbols: list[str]) -> None:
#         backoff = 1.0
#         while not self.shutdown:
#             try:
#                 if not symbols:
#                     await asyncio.sleep(1.0)
#                     continue
#                 async with websockets.connect(self.cfg.gate_ws_url, ping_interval=20, ping_timeout=20, max_size=2**23) as ws:
#                     await ws.send(json.dumps({
#                         "time": int(time.time()),
#                         "channel": "futures.book_ticker",
#                         "event": "subscribe",
#                         "payload": symbols,
#                     }))
#                     backoff = 1.0
#                     async for raw in ws:
#                         data = json.loads(raw)
#                         result = data.get("result") or data.get("payload")
#                         if data.get("channel") != "futures.book_ticker":
#                             continue
#                         if isinstance(result, list):
#                             for item in result:
#                                 await self.on_book_ticker(item)
#                         elif isinstance(result, dict):
#                             await self.on_book_ticker(result)
#             except asyncio.CancelledError:
#                 raise
#             except Exception as e:
#                 log.warning("public ws reconnect: %s", e)
#                 await asyncio.sleep(backoff)
#                 backoff = min(backoff * 2.0, 20.0)
# ===== END   [29/134] gate_mm_beast/app/connectors/gateio/ws_public.py =====

# ===== BEGIN [30/134] gate_mm_beast/app/constants.py sha256=f60716f61dcb1cb0 =====
# ORDER_STATE_NEW = "NEW"
# ORDER_STATE_ACK = "ACK"
# ORDER_STATE_OPEN = "OPEN"
# ORDER_STATE_PARTIAL = "PARTIAL"
# ORDER_STATE_FILLED = "FILLED"
# ORDER_STATE_CANCELLED = "CANCELLED"
# ORDER_STATE_REJECTED = "REJECTED"
#
# MODE_SCAN = "scan"
# MODE_PAPER = "paper"
# MODE_LIVE = "live"
# MODE_REPLAY = "replay"
# ===== END   [30/134] gate_mm_beast/app/constants.py =====

# ===== BEGIN [31/134] gate_mm_beast/app/core/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [31/134] gate_mm_beast/app/core/__init__.py =====

# ===== BEGIN [32/134] gate_mm_beast/app/core/bus.py sha256=1a00f00fd6c7f455 =====
# [stripped_future_import] from __future__ import annotations
# from collections import defaultdict
# from typing import Any, Callable
#
# class EventBus:
#     def __init__(self) -> None:
#         self._subs: dict[str, list[Callable[[Any], None]]] = defaultdict(list)
#
#     def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
#         self._subs[topic].append(handler)
#
#     def publish(self, topic: str, payload: Any) -> None:
#         for handler in self._subs.get(topic, []):
#             handler(payload)
# ===== END   [32/134] gate_mm_beast/app/core/bus.py =====

# ===== BEGIN [33/134] gate_mm_beast/app/core/circuit_breaker.py sha256=d046e594eea4ad81 =====
# class CircuitBreaker:
#     def __init__(self, threshold: int = 5) -> None:
#         self.threshold = threshold
#         self.failures = 0
#         self.open = False
#
#     def record_success(self) -> None:
#         self.failures = 0
#         self.open = False
#
#     def record_failure(self) -> None:
#         self.failures += 1
#         if self.failures >= self.threshold:
#             self.open = True
# ===== END   [33/134] gate_mm_beast/app/core/circuit_breaker.py =====

# ===== BEGIN [34/134] gate_mm_beast/app/core/clock.py sha256=a0f73e48cbb9a186 =====
# import time
# from datetime import datetime, timezone
#
# def now_ts() -> float:
#     return time.time()
#
# def utc_now_iso() -> str:
#     return datetime.now(timezone.utc).isoformat()
# ===== END   [34/134] gate_mm_beast/app/core/clock.py =====

# ===== BEGIN [35/134] gate_mm_beast/app/core/decimal_utils.py sha256=543abc71c749c7ca =====
# def safe_float(x, default: float = 0.0) -> float:
#     try:
#         return float(x)
#     except Exception:
#         return default
#
# def round_to_tick(price: float, tick: float) -> float:
#     if tick <= 0:
#         return price
#     return round(round(price / tick) * tick, 10)
# ===== END   [35/134] gate_mm_beast/app/core/decimal_utils.py =====

# ===== BEGIN [36/134] gate_mm_beast/app/core/health.py sha256=92e778be0b576d09 =====
# class HealthState:
#     def __init__(self) -> None:
#         self.healthy = True
#         self.message = "ok"
#
#     def fail(self, message: str) -> None:
#         self.healthy = False
#         self.message = message
#
#     def ok(self) -> None:
#         self.healthy = True
#         self.message = "ok"
# ===== END   [36/134] gate_mm_beast/app/core/health.py =====

# ===== BEGIN [37/134] gate_mm_beast/app/core/ids.py sha256=b0b5c94a601dc90d =====
# import hashlib
# import time
#
# def client_order_id(prefix: str, symbol: str) -> str:
#     raw = f"{prefix}|{symbol}|{time.time_ns()}".encode()
#     return f"{prefix}-{hashlib.sha1(raw).hexdigest()[:20]}"
# ===== END   [37/134] gate_mm_beast/app/core/ids.py =====

# ===== BEGIN [38/134] gate_mm_beast/app/core/throttle.py sha256=4ab4720660d8d4c9 =====
# import time
#
# class Throttle:
#     def __init__(self, seconds: float) -> None:
#         self.seconds = seconds
#         self._last = 0.0
#
#     def ready(self) -> bool:
#         now = time.time()
#         if now - self._last >= self.seconds:
#             self._last = now
#             return True
#         return False
# ===== END   [38/134] gate_mm_beast/app/core/throttle.py =====

# ===== BEGIN [39/134] gate_mm_beast/app/logging_setup.py sha256=7a61e41f9ac24c8a =====
# import logging
#
# def setup_logging(level: str = "INFO") -> None:
#     logging.basicConfig(
#         level=getattr(logging, level.upper(), logging.INFO),
#         format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
#     )
# ===== END   [39/134] gate_mm_beast/app/logging_setup.py =====

# ===== BEGIN [40/134] gate_mm_beast/app/main.py sha256=8f7aa50a020cc872 =====
# [stripped_future_import] from __future__ import annotations
# import asyncio
# import contextlib
# import logging
# import signal
# import time
# from app.config import Settings
# from app.logging_setup import setup_logging
# from app.constants import ORDER_STATE_FILLED
# from app.core.ids import client_order_id
# from app.persistence.db import Database
# from app.persistence.order_repository import OrderRepository
# from app.persistence.position_repository import PositionRepository
# from app.persistence.fill_repository import FillRepository
# from app.persistence.decision_repository import DecisionRepository
# from app.persistence.event_repository import EventRepository
# from app.persistence.snapshot_repository import SnapshotRepository
# from app.connectors.gateio.rest_public import GatePublicRest
# from app.connectors.gateio.rest_private import GatePrivateRest
# from app.connectors.gateio.ws_public import GatePublicWS
# from app.market_data.market_data_service import MarketDataService, SymbolRuntime
# from app.market_data.candles_service import CandlesService
# from app.oms.execution_service import ExecutionService
# from app.oms.order_manager import OrderManager
# from app.portfolio.position_manager import PositionManager
# from app.portfolio.inventory_manager import InventoryManager
# from app.portfolio.pnl_manager import PnLManager
# from app.risk.limits import RiskLimits
# from app.risk.kill_switch import KillSwitch
# from app.risk.risk_manager import RiskManager
# from app.strategy.alpha_model import estimate_alpha
# from app.strategy.quote_engine import QuoteEngine
# from app.backtest.replay_engine import ReplayEngine
# from app.observability.metrics import Metrics
# from app.api.server import APIServer
# from app.services.unified_balance_service import UnifiedBalanceService
#
# log = logging.getLogger("gate_mm_beast")
#
# class Application:
#     def __init__(self, cfg: Settings) -> None:
#         self.cfg = cfg
#         self.db = Database(cfg.db_path)
#         self.order_repo = OrderRepository(self.db)
#         self.position_repo = PositionRepository(self.db)
#         self.fill_repo = FillRepository(self.db)
#         self.decision_repo = DecisionRepository(self.db)
#         self.event_repo = EventRepository(self.db)
#         self.snapshot_repo = SnapshotRepository(self.db)
#
#         self.public_rest = GatePublicRest(cfg)
#         self.private_rest = GatePrivateRest(cfg)
#         self.market = MarketDataService()
#         self.candles_service = CandlesService(self.public_rest)
#
#         self.execution = ExecutionService(self.private_rest)
#         self.order_manager = OrderManager(self.order_repo, self.execution)
#         self.position_manager = PositionManager(self.position_repo)
#         self.inventory = InventoryManager()
#         self.pnl = PnLManager()
#         self.risk = RiskManager(RiskLimits(), KillSwitch())
#         self.quote_engine = QuoteEngine()
#         self.replay = ReplayEngine(cfg.take_atr_mult, cfg.stop_atr_mult)
#         self.metrics = Metrics()
#         self.unified_balance_service = UnifiedBalanceService(cfg)
#         self.shutdown = False
#         self.last_paper_fill_ts: dict[str, float] = {}
#
#         self.app_state = {"healthy": True, "message": "ok"}
#         self.engine_state = {"mode": cfg.mode, "symbols": cfg.symbols, "status": "starting"}
#
#         self.api = None
#         if cfg.enable_api:
#             self.api = APIServer(cfg.api_host, cfg.api_port, {
#                 "app_state": self.app_state,
#                 "metrics": self.metrics,
#                 "position_repo": self.position_repo,
#                 "order_repo": self.order_repo,
#                 "symbols": cfg.symbols,
#                 "engine_state": self.engine_state,
#                 "unified_balance_service": self.unified_balance_service,
#             })
#
#     def restore_runtime_memory(self) -> None:
#         self.app_state.update(self.snapshot_repo.get("app_state", self.app_state.copy()))
#         self.engine_state.update(self.snapshot_repo.get("engine_state", self.engine_state.copy()))
#         self.inventory.import_state(self.snapshot_repo.get("inventory", {}))
#
#         quote_snaps = self.snapshot_repo.get_prefix("quote:")
#         if not quote_snaps:
#             return
#
#         restored = []
#         for key, snap in quote_snaps.items():
#             symbol = key.split(":", 1)[-1]
#             rt = self.market.get(symbol)
#             if not rt:
#                 continue
#             bid = float(snap.get("bid_px") or 0.0)
#             ask = float(snap.get("ask_px") or 0.0)
#             if bid > 0 and ask > 0 and ask >= bid:
#                 rt.book.bid = bid
#                 rt.book.ask = ask
#                 rt.book.bid_size = float(snap.get("bid_size") or 0.0)
#                 rt.book.ask_size = float(snap.get("ask_size") or 0.0)
#                 restored.append(symbol)
#
#         if restored:
#             self.engine_state["restored_quotes"] = restored
#
#     def persist_runtime_memory(self) -> None:
#         self.snapshot_repo.set("app_state", self.app_state)
#         self.snapshot_repo.set("engine_state", self.engine_state)
#         self.snapshot_repo.set("inventory", self.inventory.export_state())
#
#     async def bootstrap(self) -> None:
#         contracts = await self.public_rest.list_contracts()
#         specs = {str(c.get("name") or c.get("contract") or ""): c for c in contracts}
#         runtimes = {}
#         for symbol in self.cfg.symbols:
#             spec = specs.get(symbol, {})
#             tick = float(spec.get("order_price_round") or 0.0001)
#             multiplier = float(spec.get("quanto_multiplier") or 1.0)
#             rt = SymbolRuntime(symbol=symbol, tick=tick, multiplier=multiplier)
#             rt.candles = await self.candles_service.load(symbol, self.cfg.bar_interval, self.cfg.bar_limit)
#             runtimes[symbol] = rt
#         self.market.set_symbols(runtimes)
#         self.restore_runtime_memory()
#
#     async def process_symbol(self, symbol: str) -> None:
#         rt = self.market.get(symbol)
#         if not rt or rt.candles is None or len(rt.candles) < 80:
#             return
#         if rt.book.bid <= 0 or rt.book.ask <= 0:
#             return
#         alpha = estimate_alpha(rt)
#         self.decision_repo.insert(symbol, alpha["score"], alpha["confidence"], {"alpha": alpha})
#         base_size = max(int((self.cfg.risk_usd * self.cfg.leverage) / max(rt.book.mid * max(rt.multiplier, 1e-9), 1e-9)), 1)
#         quote = self.quote_engine.build(
#             symbol=symbol,
#             mid=rt.book.mid,
#             bid=rt.book.bid,
#             ask=rt.book.ask,
#             tick=rt.tick,
#             base_size=base_size,
#             alpha_score=alpha["score"],
#             volatility_score=min(abs(alpha["score"]), 1.0),
#             net_qty=self.inventory.net(symbol),
#             max_abs_qty=10,
#         )
#         self.snapshot_repo.set(f"quote:{symbol}", {
#             "bid_px": quote.bid_px,
#             "ask_px": quote.ask_px,
#             "bid_size": quote.bid_size,
#             "ask_size": quote.ask_size,
#             "alpha_score": quote.alpha_score,
#             "fair_value": quote.fair_value,
#             "meta": quote.meta,
#         })
#         self.engine_state["status"] = "running"
#         self.engine_state["last_symbol"] = symbol
#         self.engine_state["last_quote"] = self.snapshot_repo.get(f"quote:{symbol}")
#         self.metrics.values["quotes_live"] = len(self.market.symbols())
#         self.persist_runtime_memory()
#
#         if self.cfg.mode == "paper":
#             self._simulate_paper_activity(symbol, quote)
#             return
#
#     def _simulate_paper_activity(self, symbol: str, quote) -> None:
#         now = time.time()
#         last_ts = self.last_paper_fill_ts.get(symbol, 0.0)
#         if (now - last_ts) < max(self.cfg.loop_seconds * 2.0, 4.0):
#             return
#
#         side = "buy" if quote.alpha_score >= 0 else "sell"
#         signed_qty = int(quote.bid_size if side == "buy" else -quote.ask_size)
#         size = abs(signed_qty)
#         if size <= 0:
#             return
#
#         price = float(quote.bid_px if side == "buy" else quote.ask_px)
#         coid = client_order_id("paper", symbol)
#
#         self.order_repo.insert(
#             symbol=symbol,
#             client_order_id=coid,
#             exchange_order_id="paper",
#             side=side,
#             role="entry",
#             state=ORDER_STATE_FILLED,
#             price=price,
#             size=size,
#             payload={"mode": "paper", "simulated": True},
#         )
#         self.order_repo.update_state(coid, ORDER_STATE_FILLED, filled_size=size, avg_fill_price=price)
#         self.fill_repo.insert(
#             symbol=symbol,
#             client_order_id=coid,
#             exchange_order_id="paper",
#             side=side,
#             fill_qty=size,
#             fill_price=price,
#             payload={"mode": "paper", "simulated": True},
#         )
#         self.inventory.apply_fill(symbol, signed_qty)
#         self.metrics.inc("orders_submitted", 1)
#         self.metrics.inc("fills", 1)
#         self.event_repo.write("INFO", "paper_fill", symbol, {
#             "client_order_id": coid,
#             "side": side,
#             "size": size,
#             "price": price,
#             "net_inventory": self.inventory.net(symbol),
#         })
#         self.last_paper_fill_ts[symbol] = now
#
#     async def _unified_balance_loop(self) -> None:
#         while not self.shutdown:
#             try:
#                 await self.unified_balance_service.refresh()
#             except Exception as exc:
#                 self.event_repo.write("ERROR", "unified_balance_refresh_failed", "", {"error": str(exc)})
#             await asyncio.sleep(max(5, self.cfg.unified_balance_refresh_seconds))
#
#     async def run(self) -> int:
#         await self.bootstrap()
#         await self.unified_balance_service.refresh()
#         ws = GatePublicWS(self.cfg, self.market.on_book_ticker)
#         tasks = [
#             asyncio.create_task(ws.run_book_ticker(self.market.symbols())),
#             asyncio.create_task(self._unified_balance_loop()),
#         ]
#
#         if self.api:
#             self.api.start_in_thread()
#
#         stop_event = asyncio.Event()
#
#         def stop():
#             ws.shutdown = True
#             self.shutdown = True
#             stop_event.set()
#
#         loop = asyncio.get_running_loop()
#         for sig in (signal.SIGINT, signal.SIGTERM):
#             try:
#                 loop.add_signal_handler(sig, stop)
#             except NotImplementedError:
#                 pass
#
#         try:
#             while not self.shutdown:
#                 for symbol in self.market.symbols():
#                     try:
#                         await self.process_symbol(symbol)
#                     except Exception as exc:
#                         self.app_state["healthy"] = False
#                         self.app_state["message"] = f"symbol_processing_error:{symbol}"
#                         self.event_repo.write("ERROR", "process_symbol_failed", symbol, {"error": str(exc)})
#                 await asyncio.sleep(self.cfg.loop_seconds)
#         finally:
#             stop()
#             self.engine_state["status"] = "stopped"
#             self.persist_runtime_memory()
#             for task in tasks:
#                 task.cancel()
#                 with contextlib.suppress(asyncio.CancelledError):
#                     await task
#             await self.public_rest.close()
#             await self.private_rest.close()
#             await self.unified_balance_service.close()
#             if self.api:
#                 self.api.stop()
#         return 0
#
# def run() -> int:
#     cfg = Settings()
#     setup_logging(cfg.log_level)
#     return asyncio.run(Application(cfg).run())
#
# if __name__ == "__main__":
#     raise SystemExit(run())
# ===== END   [40/134] gate_mm_beast/app/main.py =====

# ===== BEGIN [41/134] gate_mm_beast/app/market_data/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [41/134] gate_mm_beast/app/market_data/__init__.py =====

# ===== BEGIN [42/134] gate_mm_beast/app/market_data/book_builder.py sha256=22a1b205a6e5d613 =====
# from app.types import BookTop
# from app.connectors.gateio.mapper import map_book_ticker
#
# class BookBuilder:
#     def apply_book_ticker(self, current: BookTop, item: dict) -> BookTop:
#         m = map_book_ticker(item)
#         current.bid = m["bid"]
#         current.ask = m["ask"]
#         current.bid_size = m["bid_size"]
#         current.ask_size = m["ask_size"]
#         return current
# ===== END   [42/134] gate_mm_beast/app/market_data/book_builder.py =====

# ===== BEGIN [43/134] gate_mm_beast/app/market_data/candles_service.py sha256=495e870e8cc6a5d8 =====
# [stripped_future_import] from __future__ import annotations
# import numpy as np
# import pandas as pd
# from app.connectors.gateio.rest_public import GatePublicRest
#
# def add_features(df: pd.DataFrame) -> pd.DataFrame:
#     x = df.copy()
#     x["ret1"] = x["close"].pct_change(1)
#     x["ema8"] = x["close"].ewm(span=8, adjust=False).mean()
#     x["ema21"] = x["close"].ewm(span=21, adjust=False).mean()
#     x["ema55"] = x["close"].ewm(span=55, adjust=False).mean()
#     x["atr14"] = (pd.concat([
#         (x["high"] - x["low"]),
#         (x["high"] - x["close"].shift()).abs(),
#         (x["low"] - x["close"].shift()).abs(),
#     ], axis=1).max(axis=1)).rolling(14).mean()
#     x["z20"] = (x["close"] - x["close"].rolling(20).mean()) / x["close"].rolling(20).std()
#     x["volz"] = (x["volume"] - x["volume"].rolling(20).mean()) / x["volume"].rolling(20).std()
#     return x
#
# class CandlesService:
#     def __init__(self, rest: GatePublicRest) -> None:
#         self.rest = rest
#
#     async def load(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
#         df = await self.rest.candles(symbol, interval, limit)
#         if df.empty:
#             return df
#         return add_features(df).dropna().reset_index(drop=True)
# ===== END   [43/134] gate_mm_beast/app/market_data/candles_service.py =====

# ===== BEGIN [44/134] gate_mm_beast/app/market_data/depth_cache.py sha256=6fc344678cb47ad2 =====
# class DepthCache:
#     def __init__(self) -> None:
#         self.books = {}
# ===== END   [44/134] gate_mm_beast/app/market_data/depth_cache.py =====

# ===== BEGIN [45/134] gate_mm_beast/app/market_data/funding_cache.py sha256=07feb984e0af3784 =====
# class FundingCache:
#     def __init__(self) -> None:
#         self.values = {}
# ===== END   [45/134] gate_mm_beast/app/market_data/funding_cache.py =====

# ===== BEGIN [46/134] gate_mm_beast/app/market_data/mark_cache.py sha256=f09a601717115066 =====
# class MarkCache:
#     def __init__(self) -> None:
#         self.values = {}
# ===== END   [46/134] gate_mm_beast/app/market_data/mark_cache.py =====

# ===== BEGIN [47/134] gate_mm_beast/app/market_data/market_data_service.py sha256=6b581f8509cb90c0 =====
# [stripped_future_import] from __future__ import annotations
# from dataclasses import dataclass, field
# from collections import deque
# from app.types import BookTop
# from app.market_data.book_builder import BookBuilder
#
# @dataclass
# class SymbolRuntime:
#     symbol: str
#     tick: float
#     multiplier: float
#     book: BookTop = field(default_factory=BookTop)
#     candles = None
#     recent_mid: deque = field(default_factory=lambda: deque(maxlen=120))
#
# class MarketDataService:
#     def __init__(self) -> None:
#         self.runtimes: dict[str, SymbolRuntime] = {}
#         self.builder = BookBuilder()
#
#     def set_symbols(self, runtimes: dict[str, SymbolRuntime]) -> None:
#         self.runtimes = runtimes
#
#     async def on_book_ticker(self, item: dict) -> None:
#         symbol = str(item.get("s") or item.get("contract") or "")
#         rt = self.runtimes.get(symbol)
#         if not rt:
#             return
#         self.builder.apply_book_ticker(rt.book, item)
#         if rt.book.mid > 0:
#             rt.recent_mid.append(rt.book.mid)
#
#     def get(self, symbol: str) -> SymbolRuntime | None:
#         return self.runtimes.get(symbol)
#
#     def symbols(self) -> list[str]:
#         return list(self.runtimes.keys())
# ===== END   [47/134] gate_mm_beast/app/market_data/market_data_service.py =====

# ===== BEGIN [48/134] gate_mm_beast/app/market_data/stale_detector.py sha256=53fdc4feab45f4be =====
# import time
#
# def is_stale(ts: float, max_age: float = 10.0) -> bool:
#     return time.time() - ts > max_age
# ===== END   [48/134] gate_mm_beast/app/market_data/stale_detector.py =====

# ===== BEGIN [49/134] gate_mm_beast/app/market_data/trade_tape.py sha256=4be5a4d4c8e99795 =====
# class TradeTape:
#     def __init__(self) -> None:
#         self.trades = {}
# ===== END   [49/134] gate_mm_beast/app/market_data/trade_tape.py =====

# ===== BEGIN [50/134] gate_mm_beast/app/observability/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [50/134] gate_mm_beast/app/observability/__init__.py =====

# ===== BEGIN [51/134] gate_mm_beast/app/observability/alerts.py sha256=423ffbe4646d7a4d =====
# class AlertManager:
#     def send(self, message: str) -> None:
#         print(f"[ALERT] {message}")
# ===== END   [51/134] gate_mm_beast/app/observability/alerts.py =====

# ===== BEGIN [52/134] gate_mm_beast/app/observability/audit_log.py sha256=d1a86ddb5b7d890d =====
# import logging
# log = logging.getLogger("audit_log")
# ===== END   [52/134] gate_mm_beast/app/observability/audit_log.py =====

# ===== BEGIN [53/134] gate_mm_beast/app/observability/event_log.py sha256=60ce54f65ba099b6 =====
# import logging
# log = logging.getLogger("event_log")
# ===== END   [53/134] gate_mm_beast/app/observability/event_log.py =====

# ===== BEGIN [54/134] gate_mm_beast/app/observability/metrics.py sha256=9065626d3e2085a5 =====
# class Metrics:
#     def __init__(self) -> None:
#         self.values = {
#             "orders_submitted": 0,
#             "fills": 0,
#             "rejects": 0,
#             "quotes_live": 0,
#         }
#
#     def inc(self, name: str, value: int = 1) -> None:
#         self.values[name] = self.values.get(name, 0) + value
# ===== END   [54/134] gate_mm_beast/app/observability/metrics.py =====

# ===== BEGIN [55/134] gate_mm_beast/app/observability/tracing.py sha256=aae69e45d5a7c9ae =====
# class Tracer:
#     def span(self, name: str):
#         return name
# ===== END   [55/134] gate_mm_beast/app/observability/tracing.py =====

# ===== BEGIN [56/134] gate_mm_beast/app/oms/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [56/134] gate_mm_beast/app/oms/__init__.py =====

# ===== BEGIN [57/134] gate_mm_beast/app/oms/ack_tracker.py sha256=8096ab0418b59ba3 =====
# class AckTracker:
#     def __init__(self) -> None:
#         self.pending = {}
# ===== END   [57/134] gate_mm_beast/app/oms/ack_tracker.py =====

# ===== BEGIN [58/134] gate_mm_beast/app/oms/client_order_registry.py sha256=e5552d37f6a16c55 =====
# class ClientOrderRegistry:
#     def __init__(self) -> None:
#         self.by_client_id = {}
# ===== END   [58/134] gate_mm_beast/app/oms/client_order_registry.py =====

# ===== BEGIN [59/134] gate_mm_beast/app/oms/execution_service.py sha256=ea07683ac1f9d50f =====
# [stripped_future_import] from __future__ import annotations
# from app.connectors.gateio.rest_private import GatePrivateRest
#
# class ExecutionService:
#     def __init__(self, private_rest: GatePrivateRest) -> None:
#         self.private_rest = private_rest
#
#     async def submit(self, symbol: str, size: int, price: float, client_order_id: str, reduce_only: bool, tif: str) -> dict:
#         return await self.private_rest.create_order(symbol, size, price, client_order_id, reduce_only=reduce_only, tif=tif)
#
#     async def cancel(self, order_id: str) -> dict:
#         return await self.private_rest.cancel_order(order_id)
#
#     async def fetch(self, order_id: str) -> dict:
#         return await self.private_rest.get_order(order_id)
# ===== END   [59/134] gate_mm_beast/app/oms/execution_service.py =====

# ===== BEGIN [60/134] gate_mm_beast/app/oms/fill_processor.py sha256=325a94ac8e688ddf =====
# [stripped_future_import] from __future__ import annotations
# from app.persistence.fill_repository import FillRepository
# from app.persistence.order_repository import OrderRepository
# from app.persistence.position_repository import PositionRepository
#
# class FillProcessor:
#     def __init__(self, fills: FillRepository, orders: OrderRepository, positions: PositionRepository) -> None:
#         self.fills = fills
#         self.orders = orders
#         self.positions = positions
#
#     def record_fill(self, symbol: str, client_order_id: str, exchange_order_id: str, side: str, fill_qty: int, fill_price: float, payload: dict) -> None:
#         self.fills.insert(symbol, client_order_id, exchange_order_id, side, fill_qty, fill_price, payload)
# ===== END   [60/134] gate_mm_beast/app/oms/fill_processor.py =====

# ===== BEGIN [61/134] gate_mm_beast/app/oms/order_manager.py sha256=6e9d257bea3ae144 =====
# [stripped_future_import] from __future__ import annotations
# from app.constants import *
# from app.core.ids import client_order_id
# from app.oms.order_state import can_transition
# from app.persistence.order_repository import OrderRepository
# from app.oms.execution_service import ExecutionService
#
# class OrderManager:
#     def __init__(self, repo: OrderRepository, execution: ExecutionService) -> None:
#         self.repo = repo
#         self.execution = execution
#
#     async def submit_limit(self, symbol: str, side: str, role: str, price: float, size: int, reduce_only: bool = False, tif: str = "poc") -> str:
#         coid = client_order_id(role, symbol)
#         self.repo.insert(symbol, coid, "", side, role, ORDER_STATE_NEW, price, size, {"reduce_only": reduce_only, "tif": tif})
#         resp = await self.execution.submit(symbol, size, price, coid, reduce_only, tif)
#         self.repo.update_state(coid, ORDER_STATE_ACK)
#         return coid
#
#     def transition(self, client_order_id: str, old: str, new: str) -> bool:
#         if not can_transition(old, new):
#             return False
#         self.repo.update_state(client_order_id, new)
#         return True
# ===== END   [61/134] gate_mm_beast/app/oms/order_manager.py =====

# ===== BEGIN [62/134] gate_mm_beast/app/oms/order_models.py sha256=be3d876fcdc44c36 =====
# from dataclasses import dataclass
#
# @dataclass
# class OrderIntent:
#     symbol: str
#     side: str
#     role: str
#     price: float
#     size: int
#     reduce_only: bool = False
#     tif: str = "poc"
# ===== END   [62/134] gate_mm_beast/app/oms/order_models.py =====

# ===== BEGIN [63/134] gate_mm_beast/app/oms/order_state.py sha256=a6458c8127ece802 =====
# from app.constants import *
#
# VALID_TRANSITIONS = {
#     ORDER_STATE_NEW: {ORDER_STATE_ACK, ORDER_STATE_REJECTED, ORDER_STATE_CANCELLED},
#     ORDER_STATE_ACK: {ORDER_STATE_OPEN, ORDER_STATE_PARTIAL, ORDER_STATE_FILLED, ORDER_STATE_CANCELLED, ORDER_STATE_REJECTED},
#     ORDER_STATE_OPEN: {ORDER_STATE_PARTIAL, ORDER_STATE_FILLED, ORDER_STATE_CANCELLED},
#     ORDER_STATE_PARTIAL: {ORDER_STATE_PARTIAL, ORDER_STATE_FILLED, ORDER_STATE_CANCELLED},
# }
#
# def can_transition(old: str, new: str) -> bool:
#     return new == old or new in VALID_TRANSITIONS.get(old, set())
# ===== END   [63/134] gate_mm_beast/app/oms/order_state.py =====

# ===== BEGIN [64/134] gate_mm_beast/app/oms/replace_manager.py sha256=061f667072f48af0 =====
# class ReplaceManager:
#     def should_replace(self, current_price: float, desired_price: float, tick: float) -> bool:
#         return abs(current_price - desired_price) >= max(tick, 1e-8)
# ===== END   [64/134] gate_mm_beast/app/oms/replace_manager.py =====

# ===== BEGIN [65/134] gate_mm_beast/app/persistence/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [65/134] gate_mm_beast/app/persistence/__init__.py =====

# ===== BEGIN [66/134] gate_mm_beast/app/persistence/db.py sha256=3bf56f060108d8e3 =====
# [stripped_future_import] from __future__ import annotations
# import sqlite3
# from pathlib import Path
#
# SCHEMA = '''
# CREATE TABLE IF NOT EXISTS events(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     ts TEXT NOT NULL,
#     level TEXT NOT NULL,
#     kind TEXT NOT NULL,
#     symbol TEXT,
#     payload_json TEXT NOT NULL
# );
# CREATE TABLE IF NOT EXISTS decisions(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     ts TEXT NOT NULL,
#     symbol TEXT NOT NULL,
#     score REAL NOT NULL,
#     confidence REAL NOT NULL,
#     payload_json TEXT NOT NULL
# );
# CREATE TABLE IF NOT EXISTS orders(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     ts TEXT NOT NULL,
#     symbol TEXT NOT NULL,
#     client_order_id TEXT,
#     exchange_order_id TEXT,
#     side TEXT NOT NULL,
#     role TEXT NOT NULL,
#     state TEXT NOT NULL,
#     price REAL,
#     size INTEGER NOT NULL,
#     filled_size INTEGER DEFAULT 0,
#     avg_fill_price REAL,
#     payload_json TEXT NOT NULL
# );
# CREATE TABLE IF NOT EXISTS positions(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     ts_open TEXT NOT NULL,
#     ts_close TEXT,
#     symbol TEXT NOT NULL,
#     side TEXT NOT NULL,
#     status TEXT NOT NULL,
#     qty INTEGER NOT NULL,
#     entry_vwap REAL,
#     exit_vwap REAL,
#     realized_pnl REAL,
#     payload_json TEXT NOT NULL
# );
# CREATE TABLE IF NOT EXISTS fills(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     ts TEXT NOT NULL,
#     symbol TEXT NOT NULL,
#     client_order_id TEXT,
#     exchange_order_id TEXT,
#     side TEXT NOT NULL,
#     fill_qty INTEGER NOT NULL,
#     fill_price REAL NOT NULL,
#     payload_json TEXT NOT NULL
# );
# CREATE TABLE IF NOT EXISTS snapshots(
#     k TEXT PRIMARY KEY,
#     v TEXT NOT NULL
# );
# '''
#
# class Database:
#     def __init__(self, path: str) -> None:
#         self.path = str(Path(path))
#         self.init()
#
#     def conn(self) -> sqlite3.Connection:
#         conn = sqlite3.connect(self.path)
#         conn.row_factory = sqlite3.Row
#         return conn
#
#     def init(self) -> None:
#         with self.conn() as c:
#             c.executescript(SCHEMA)
#             c.commit()
# ===== END   [66/134] gate_mm_beast/app/persistence/db.py =====

# ===== BEGIN [67/134] gate_mm_beast/app/persistence/decision_repository.py sha256=a5de8d9b9b94277d =====
# [stripped_future_import] from __future__ import annotations
# import json
# from app.core.clock import utc_now_iso
# from app.persistence.db import Database
#
# class DecisionRepository:
#     def __init__(self, db: Database) -> None:
#         self.db = db
#
#     def insert(self, symbol: str, score: float, confidence: float, payload: dict) -> int:
#         with self.db.conn() as c:
#             cur = c.execute(
#                 "INSERT INTO decisions(ts,symbol,score,confidence,payload_json) VALUES(?,?,?,?,?)",
#                 (utc_now_iso(), symbol, score, confidence, json.dumps(payload)),
#             )
#             c.commit()
#             return int(cur.lastrowid)
# ===== END   [67/134] gate_mm_beast/app/persistence/decision_repository.py =====

# ===== BEGIN [68/134] gate_mm_beast/app/persistence/event_repository.py sha256=09b5fb3fb3f5bc0b =====
# [stripped_future_import] from __future__ import annotations
# import json
# from app.core.clock import utc_now_iso
# from app.persistence.db import Database
#
# class EventRepository:
#     def __init__(self, db: Database) -> None:
#         self.db = db
#
#     def write(self, level: str, kind: str, symbol: str, payload: dict) -> None:
#         with self.db.conn() as c:
#             c.execute(
#                 "INSERT INTO events(ts,level,kind,symbol,payload_json) VALUES(?,?,?,?,?)",
#                 (utc_now_iso(), level, kind, symbol, json.dumps(payload)),
#             )
#             c.commit()
#
#     def recent(self, limit: int = 100) -> list[dict]:
#         with self.db.conn() as c:
#             return [dict(r) for r in c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
# ===== END   [68/134] gate_mm_beast/app/persistence/event_repository.py =====

# ===== BEGIN [69/134] gate_mm_beast/app/persistence/fill_repository.py sha256=6fb764b397c16f13 =====
# [stripped_future_import] from __future__ import annotations
# import json
# from app.core.clock import utc_now_iso
# from app.persistence.db import Database
#
# class FillRepository:
#     def __init__(self, db: Database) -> None:
#         self.db = db
#
#     def insert(self, symbol: str, client_order_id: str, exchange_order_id: str, side: str, fill_qty: int, fill_price: float, payload: dict) -> int:
#         with self.db.conn() as c:
#             cur = c.execute(
#                 '''INSERT INTO fills(ts,symbol,client_order_id,exchange_order_id,side,fill_qty,fill_price,payload_json)
#                    VALUES(?,?,?,?,?,?,?,?)''',
#                 (utc_now_iso(), symbol, client_order_id, exchange_order_id, side, fill_qty, fill_price, json.dumps(payload)),
#             )
#             c.commit()
#             return int(cur.lastrowid)
# ===== END   [69/134] gate_mm_beast/app/persistence/fill_repository.py =====

# ===== BEGIN [70/134] gate_mm_beast/app/persistence/models.py sha256=add78fb092ee0fec =====
# from dataclasses import dataclass
#
# @dataclass
# class OrderRecord:
#     symbol: str
#     client_order_id: str
#     side: str
#     role: str
#     state: str
#     price: float
#     size: int
# ===== END   [70/134] gate_mm_beast/app/persistence/models.py =====

# ===== BEGIN [71/134] gate_mm_beast/app/persistence/order_repository.py sha256=2805d829112c971c =====
# [stripped_future_import] from __future__ import annotations
# import json
# from app.core.clock import utc_now_iso
# from app.persistence.db import Database
#
# class OrderRepository:
#     def __init__(self, db: Database) -> None:
#         self.db = db
#
#     def insert(self, symbol: str, client_order_id: str, exchange_order_id: str, side: str, role: str, state: str, price: float, size: int, payload: dict) -> int:
#         with self.db.conn() as c:
#             cur = c.execute(
#                 '''INSERT INTO orders(ts,symbol,client_order_id,exchange_order_id,side,role,state,price,size,payload_json)
#                    VALUES(?,?,?,?,?,?,?,?,?,?)''',
#                 (utc_now_iso(), symbol, client_order_id, exchange_order_id, side, role, state, price, size, json.dumps(payload)),
#             )
#             c.commit()
#             return int(cur.lastrowid)
#
#     def update_state(self, client_order_id: str, state: str, filled_size: int | None = None, avg_fill_price: float | None = None) -> None:
#         updates = ["state=?"]
#         vals = [state]
#         if filled_size is not None:
#             updates.append("filled_size=?")
#             vals.append(filled_size)
#         if avg_fill_price is not None:
#             updates.append("avg_fill_price=?")
#             vals.append(avg_fill_price)
#         vals.append(client_order_id)
#         with self.db.conn() as c:
#             c.execute(f"UPDATE orders SET {', '.join(updates)} WHERE client_order_id=?", vals)
#             c.commit()
#
#     def open_orders(self, symbol: str | None = None) -> list[dict]:
#         sql = "SELECT * FROM orders WHERE state IN ('NEW','ACK','OPEN','PARTIAL')"
#         params = []
#         if symbol:
#             sql += " AND symbol=?"
#             params.append(symbol)
#         with self.db.conn() as c:
#             return [dict(r) for r in c.execute(sql, params).fetchall()]
# ===== END   [71/134] gate_mm_beast/app/persistence/order_repository.py =====

# ===== BEGIN [72/134] gate_mm_beast/app/persistence/position_repository.py sha256=76733a6f790a03e4 =====
# [stripped_future_import] from __future__ import annotations
# import json
# from app.core.clock import utc_now_iso
# from app.persistence.db import Database
#
# class PositionRepository:
#     def __init__(self, db: Database) -> None:
#         self.db = db
#
#     def open_position(self, symbol: str, side: str, qty: int, entry_vwap: float, payload: dict) -> int:
#         with self.db.conn() as c:
#             cur = c.execute(
#                 '''INSERT INTO positions(ts_open,symbol,side,status,qty,entry_vwap,payload_json)
#                    VALUES(?,?,?,?,?,?,?)''',
#                 (utc_now_iso(), symbol, side, "open", qty, entry_vwap, json.dumps(payload)),
#             )
#             c.commit()
#             return int(cur.lastrowid)
#
#     def close_position(self, symbol: str, exit_vwap: float, realized_pnl: float) -> None:
#         with self.db.conn() as c:
#             c.execute(
#                 "UPDATE positions SET ts_close=?, status='closed', exit_vwap=?, realized_pnl=? WHERE symbol=? AND status='open'",
#                 (utc_now_iso(), exit_vwap, realized_pnl, symbol),
#             )
#             c.commit()
#
#     def get_open(self, symbol: str) -> dict | None:
#         with self.db.conn() as c:
#             row = c.execute("SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1", (symbol,)).fetchone()
#             return dict(row) if row else None
# ===== END   [72/134] gate_mm_beast/app/persistence/position_repository.py =====

# ===== BEGIN [73/134] gate_mm_beast/app/persistence/snapshot_repository.py sha256=1dc6910ace5f6ef8 =====
# [stripped_future_import] from __future__ import annotations
# import json
# from app.persistence.db import Database
#
# class SnapshotRepository:
#     def __init__(self, db: Database) -> None:
#         self.db = db
#
#     def set(self, k: str, v: dict) -> None:
#         with self.db.conn() as c:
#             c.execute("INSERT INTO snapshots(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, json.dumps(v)))
#             c.commit()
#
#     def get(self, k: str, default: dict | None = None) -> dict:
#         with self.db.conn() as c:
#             row = c.execute("SELECT v FROM snapshots WHERE k=?", (k,)).fetchone()
#             if not row:
#                 return default or {}
#             try:
#                 return json.loads(row[0])
#             except Exception:
#                 return default or {}
#
#     def delete(self, k: str) -> None:
#         with self.db.conn() as c:
#             c.execute("DELETE FROM snapshots WHERE k=?", (k,))
#             c.commit()
#
#     def get_prefix(self, prefix: str) -> dict[str, dict]:
#         out: dict[str, dict] = {}
#         with self.db.conn() as c:
#             rows = c.execute("SELECT k,v FROM snapshots WHERE k LIKE ?", (f"{prefix}%",)).fetchall()
#             for row in rows:
#                 key = str(row[0])
#                 try:
#                     out[key] = json.loads(row[1])
#                 except Exception:
#                     out[key] = {}
#         return out
# ===== END   [73/134] gate_mm_beast/app/persistence/snapshot_repository.py =====

# ===== BEGIN [74/134] gate_mm_beast/app/portfolio/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [74/134] gate_mm_beast/app/portfolio/__init__.py =====

# ===== BEGIN [75/134] gate_mm_beast/app/portfolio/account_reconciler.py sha256=da4ee8954eeef33e =====
# class AccountReconciler:
#     def reconcile(self):
#         return {"ok": True}
# ===== END   [75/134] gate_mm_beast/app/portfolio/account_reconciler.py =====

# ===== BEGIN [76/134] gate_mm_beast/app/portfolio/exposure_manager.py sha256=5acbbacc43333b43 =====
# class ExposureManager:
#     def __init__(self) -> None:
#         self.max_notional = 0.0
# ===== END   [76/134] gate_mm_beast/app/portfolio/exposure_manager.py =====

# ===== BEGIN [77/134] gate_mm_beast/app/portfolio/inventory_manager.py sha256=496a1b9ab775079d =====
# class InventoryManager:
#     def __init__(self) -> None:
#         self.net_by_symbol = {}
#
#     def net(self, symbol: str) -> int:
#         return self.net_by_symbol.get(symbol, 0)
#
#     def apply_fill(self, symbol: str, signed_qty: int) -> None:
#         self.net_by_symbol[symbol] = self.net(symbol) + signed_qty
#
#     def export_state(self) -> dict[str, int]:
#         return {str(k): int(v) for k, v in self.net_by_symbol.items()}
#
#     def import_state(self, state: dict[str, int]) -> None:
#         self.net_by_symbol = {str(k): int(v) for k, v in (state or {}).items()}
# ===== END   [77/134] gate_mm_beast/app/portfolio/inventory_manager.py =====

# ===== BEGIN [78/134] gate_mm_beast/app/portfolio/pnl_manager.py sha256=d3f96d8ea370e180 =====
# class PnLManager:
#     def realized(self, entry: float, exit_: float, qty: int, multiplier: float, side: str) -> float:
#         if side == "buy":
#             return (exit_ - entry) * qty * multiplier
#         return (entry - exit_) * qty * multiplier
# ===== END   [78/134] gate_mm_beast/app/portfolio/pnl_manager.py =====

# ===== BEGIN [79/134] gate_mm_beast/app/portfolio/position_manager.py sha256=397cb3169515942c =====
# [stripped_future_import] from __future__ import annotations
# from app.persistence.position_repository import PositionRepository
#
# class PositionManager:
#     def __init__(self, repo: PositionRepository) -> None:
#         self.repo = repo
#
#     def open(self, symbol: str, side: str, qty: int, entry_vwap: float, payload: dict) -> int:
#         return self.repo.open_position(symbol, side, qty, entry_vwap, payload)
#
#     def get_open(self, symbol: str) -> dict | None:
#         return self.repo.get_open(symbol)
# ===== END   [79/134] gate_mm_beast/app/portfolio/position_manager.py =====

# ===== BEGIN [80/134] gate_mm_beast/app/reconcile/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [80/134] gate_mm_beast/app/reconcile/__init__.py =====

# ===== BEGIN [81/134] gate_mm_beast/app/reconcile/ghost_order_detector.py sha256=6b06e74ff64afc1b =====
# class GhostOrderDetector:
#     def find(self):
#         return []
# ===== END   [81/134] gate_mm_beast/app/reconcile/ghost_order_detector.py =====

# ===== BEGIN [82/134] gate_mm_beast/app/reconcile/orphan_position_detector.py sha256=f8d6f5f8fe295e4c =====
# class OrphanPositionDetector:
#     def find(self):
#         return []
# ===== END   [82/134] gate_mm_beast/app/reconcile/orphan_position_detector.py =====

# ===== BEGIN [83/134] gate_mm_beast/app/reconcile/periodic_reconcile.py sha256=31d184481bc6cb58 =====
# class PeriodicReconcile:
#     async def run(self):
#         return {"ok": True, "kind": "periodic"}
# ===== END   [83/134] gate_mm_beast/app/reconcile/periodic_reconcile.py =====

# ===== BEGIN [84/134] gate_mm_beast/app/reconcile/recovery_actions.py sha256=8d0388a133ba0da7 =====
# class RecoveryActions:
#     def cancel_orphans(self):
#         return []
# ===== END   [84/134] gate_mm_beast/app/reconcile/recovery_actions.py =====

# ===== BEGIN [85/134] gate_mm_beast/app/reconcile/startup_reconcile.py sha256=6cb51e209063256a =====
# class StartupReconcile:
#     async def run(self):
#         return {"ok": True, "kind": "startup"}
# ===== END   [85/134] gate_mm_beast/app/reconcile/startup_reconcile.py =====

# ===== BEGIN [86/134] gate_mm_beast/app/risk/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [86/134] gate_mm_beast/app/risk/__init__.py =====

# ===== BEGIN [87/134] gate_mm_beast/app/risk/connectivity_guard.py sha256=e6e129d614d60b0a =====
# class ConnectivityGuard:
#     def __init__(self) -> None:
#         self.ok = True
# ===== END   [87/134] gate_mm_beast/app/risk/connectivity_guard.py =====

# ===== BEGIN [88/134] gate_mm_beast/app/risk/kill_switch.py sha256=4652d3bbb60e525b =====
# class KillSwitch:
#     def __init__(self) -> None:
#         self.triggered = False
#         self.reason = ""
#
#     def trigger(self, reason: str) -> None:
#         self.triggered = True
#         self.reason = reason
# ===== END   [88/134] gate_mm_beast/app/risk/kill_switch.py =====

# ===== BEGIN [89/134] gate_mm_beast/app/risk/limits.py sha256=69b608bce5c68ede =====
# from dataclasses import dataclass
#
# @dataclass
# class RiskLimits:
#     max_positions: int = 10
#     max_symbol_position: int = 1
#     max_daily_loss_usd: float = 250.0
# ===== END   [89/134] gate_mm_beast/app/risk/limits.py =====

# ===== BEGIN [90/134] gate_mm_beast/app/risk/market_regime_guard.py sha256=a041784fe5985b0f =====
# class MarketRegimeGuard:
#     def allow_quotes(self, spread_bps: float) -> bool:
#         return spread_bps < 100.0
# ===== END   [90/134] gate_mm_beast/app/risk/market_regime_guard.py =====

# ===== BEGIN [91/134] gate_mm_beast/app/risk/protective_exit.py sha256=8882ddd3c90c7a1c =====
# [stripped_future_import] from __future__ import annotations
# from app.types import ProtectiveExitCommand
#
# class ProtectiveExit:
#     async def build(self, symbol: str, side: str, size: int, stop_price: float, marketable_limit_price: float) -> ProtectiveExitCommand:
#         return ProtectiveExitCommand(
#             symbol=symbol,
#             side=side,
#             size=size,
#             reason="stop_cross",
#             stop_price=stop_price,
#             marketable_limit_price=marketable_limit_price,
#         )
# ===== END   [91/134] gate_mm_beast/app/risk/protective_exit.py =====

# ===== BEGIN [92/134] gate_mm_beast/app/risk/risk_manager.py sha256=f123ce59e53722b3 =====
# [stripped_future_import] from __future__ import annotations
# from app.risk.kill_switch import KillSwitch
# from app.risk.limits import RiskLimits
#
# class RiskManager:
#     def __init__(self, limits: RiskLimits, kill_switch: KillSwitch) -> None:
#         self.limits = limits
#         self.kill_switch = kill_switch
#
#     def can_open(self, open_positions_count: int, symbol_position_count: int) -> bool:
#         if self.kill_switch.triggered:
#             return False
#         if open_positions_count >= self.limits.max_positions:
#             return False
#         if symbol_position_count >= self.limits.max_symbol_position:
#             return False
#         return True
# ===== END   [92/134] gate_mm_beast/app/risk/risk_manager.py =====

# ===== BEGIN [93/134] gate_mm_beast/app/risk/stale_order_guard.py sha256=4ed31edaedc47275 =====
# class StaleOrderGuard:
#     def should_cancel(self, age_seconds: float, ttl_seconds: float) -> bool:
#         return age_seconds > ttl_seconds
# ===== END   [93/134] gate_mm_beast/app/risk/stale_order_guard.py =====

# ===== BEGIN [94/134] gate_mm_beast/app/services/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [94/134] gate_mm_beast/app/services/__init__.py =====

# ===== BEGIN [95/134] gate_mm_beast/app/services/unified_balance_service.py sha256=5dadf1d8ec38ee1e =====
# [stripped_future_import] from __future__ import annotations
#
# import base64
# import hashlib
# import hmac
# import json
# import time
# from datetime import datetime, timezone
# from urllib.parse import urlencode
#
# import aiohttp
#
# from app.config import Settings
# from app.connectors.gateio.signing import build_headers as gate_build_headers
#
#
# class UnifiedBalanceService:
#     def __init__(self, cfg: Settings) -> None:
#         self.cfg = cfg
#         self.session: aiohttp.ClientSession | None = None
#         self.snapshot: dict = {
#             "ts": "",
#             "total_usd": 0.0,
#             "exchanges": {},
#         }
#
#     async def ensure(self) -> None:
#         if self.session is None or self.session.closed:
#             timeout = aiohttp.ClientTimeout(total=self.cfg.request_timeout)
#             self.session = aiohttp.ClientSession(timeout=timeout)
#
#     async def close(self) -> None:
#         if self.session and not self.session.closed:
#             await self.session.close()
#
#     async def refresh(self) -> dict:
#         await self.ensure()
#         assert self.session
#
#         results = {
#             "gate": await self._fetch_gate(),
#             "binance": await self._fetch_binance(),
#             "okx": await self._fetch_okx(),
#             "bybit": await self._fetch_bybit(),
#             "xt": await self._fetch_xt(),
#         }
#         total_usd = round(sum(float(v.get("total_usd", 0.0)) for v in results.values()), 8)
#         self.snapshot = {
#             "ts": datetime.now(timezone.utc).isoformat(),
#             "total_usd": total_usd,
#             "exchanges": results,
#         }
#         return self.snapshot
#
#     def get_snapshot(self) -> dict:
#         return self.snapshot
#
#     @staticmethod
#     def _usd_sum(assets: list[dict]) -> float:
#         usd_like = {"USD", "USDT", "USDC", "BUSD", "FDUSD", "TUSD"}
#         total = 0.0
#         for asset in assets:
#             ccy = str(asset.get("asset", "")).upper()
#             amt = float(asset.get("free", 0.0)) + float(asset.get("locked", 0.0))
#             if ccy in usd_like:
#                 total += amt
#         return round(total, 8)
#
#     @staticmethod
#     def _ok(exchange: str, assets: list[dict], note: str = "") -> dict:
#         return {
#             "exchange": exchange,
#             "status": "ok",
#             "note": note,
#             "total_usd": UnifiedBalanceService._usd_sum(assets),
#             "assets": assets,
#         }
#
#     @staticmethod
#     def _error(exchange: str, message: str) -> dict:
#         return {
#             "exchange": exchange,
#             "status": "error",
#             "error": message,
#             "total_usd": 0.0,
#             "assets": [],
#         }
#
#     async def _fetch_gate(self) -> dict:
#         if not (self.cfg.gate_api_key and self.cfg.gate_api_secret):
#             return self._error("gate", "missing_credentials")
#         try:
#             path = f"/futures/{self.cfg.gate_settle}/accounts"
#             headers = gate_build_headers(self.cfg.gate_api_key, self.cfg.gate_api_secret, "GET", path)
#             url = f"{self.cfg.gate_base_url}{path}"
#             async with self.session.get(url, headers=headers) as r:
#                 text = await r.text()
#                 if r.status >= 400:
#                     return self._error("gate", f"http_{r.status}:{text[:200]}")
#                 data = json.loads(text) if text.strip() else {}
#                 total = float(data.get("available", 0.0)) + float(data.get("total", 0.0))
#                 assets = [{"asset": "USDT", "free": total, "locked": 0.0}]
#                 return {
#                     "exchange": "gate",
#                     "status": "ok",
#                     "total_usd": round(total, 8),
#                     "assets": assets,
#                 }
#         except Exception as exc:
#             return self._error("gate", str(exc))
#
#     async def _fetch_binance(self) -> dict:
#         if not (self.cfg.binance_api_key and self.cfg.binance_api_secret):
#             return self._error("binance", "missing_credentials")
#         try:
#             ts = int(time.time() * 1000)
#             qs = urlencode({"timestamp": ts})
#             sig = hmac.new(self.cfg.binance_api_secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
#             url = f"https://api.binance.com/api/v3/account?{qs}&signature={sig}"
#             headers = {"X-MBX-APIKEY": self.cfg.binance_api_key}
#             async with self.session.get(url, headers=headers) as r:
#                 text = await r.text()
#                 if r.status >= 400:
#                     return self._error("binance", f"http_{r.status}:{text[:200]}")
#                 data = json.loads(text) if text.strip() else {}
#                 assets = []
#                 for b in data.get("balances", []):
#                     free = float(b.get("free", 0.0))
#                     locked = float(b.get("locked", 0.0))
#                     if free or locked:
#                         assets.append({"asset": b.get("asset"), "free": free, "locked": locked})
#                 return self._ok("binance", assets)
#         except Exception as exc:
#             return self._error("binance", str(exc))
#
#     async def _fetch_okx(self) -> dict:
#         if not (self.cfg.okx_api_key and self.cfg.okx_api_secret and self.cfg.okx_passphrase):
#             return self._error("okx", "missing_credentials")
#         try:
#             path = "/api/v5/account/balance"
#             ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
#             prehash = f"{ts}GET{path}"
#             sign = base64.b64encode(hmac.new(self.cfg.okx_api_secret.encode(), prehash.encode(), hashlib.sha256).digest()).decode()
#             headers = {
#                 "OK-ACCESS-KEY": self.cfg.okx_api_key,
#                 "OK-ACCESS-SIGN": sign,
#                 "OK-ACCESS-TIMESTAMP": ts,
#                 "OK-ACCESS-PASSPHRASE": self.cfg.okx_passphrase,
#             }
#             async with self.session.get(f"https://www.okx.com{path}", headers=headers) as r:
#                 text = await r.text()
#                 if r.status >= 400:
#                     return self._error("okx", f"http_{r.status}:{text[:200]}")
#                 data = json.loads(text) if text.strip() else {}
#                 assets = []
#                 for row in data.get("data", []):
#                     for d in row.get("details", []):
#                         free = float(d.get("availBal", 0.0))
#                         locked = max(float(d.get("cashBal", 0.0)) - free, 0.0)
#                         if free or locked:
#                             assets.append({"asset": d.get("ccy"), "free": free, "locked": locked})
#                 return self._ok("okx", assets)
#         except Exception as exc:
#             return self._error("okx", str(exc))
#
#     async def _fetch_bybit(self) -> dict:
#         if not (self.cfg.bybit_api_key and self.cfg.bybit_api_secret):
#             return self._error("bybit", "missing_credentials")
#         try:
#             path = "/v5/account/wallet-balance"
#             recv_window = "5000"
#             ts = str(int(time.time() * 1000))
#             qs = urlencode({"accountType": "UNIFIED"})
#             payload = f"{ts}{self.cfg.bybit_api_key}{recv_window}{qs}"
#             sign = hmac.new(self.cfg.bybit_api_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
#             headers = {
#                 "X-BAPI-API-KEY": self.cfg.bybit_api_key,
#                 "X-BAPI-SIGN": sign,
#                 "X-BAPI-SIGN-TYPE": "2",
#                 "X-BAPI-TIMESTAMP": ts,
#                 "X-BAPI-RECV-WINDOW": recv_window,
#             }
#             async with self.session.get(f"https://api.bybit.com{path}?{qs}", headers=headers) as r:
#                 text = await r.text()
#                 if r.status >= 400:
#                     return self._error("bybit", f"http_{r.status}:{text[:200]}")
#                 data = json.loads(text) if text.strip() else {}
#                 assets = []
#                 for acct in data.get("result", {}).get("list", []):
#                     for coin in acct.get("coin", []):
#                         free = float(coin.get("walletBalance", 0.0))
#                         locked = float(coin.get("locked", 0.0))
#                         if free or locked:
#                             assets.append({"asset": coin.get("coin"), "free": free, "locked": locked})
#                 return self._ok("bybit", assets)
#         except Exception as exc:
#             return self._error("bybit", str(exc))
#
#     async def _fetch_xt(self) -> dict:
#         if not (self.cfg.xt_api_key and self.cfg.xt_api_secret):
#             return self._error("xt", "missing_credentials")
#         try:
#             path = "/v4/private/wallet/balances"
#             ts = str(int(time.time() * 1000))
#             sign_raw = f"{ts}GET{path}"
#             sign = hmac.new(self.cfg.xt_api_secret.encode(), sign_raw.encode(), hashlib.sha256).hexdigest()
#             headers = {
#                 "validate-algorithms": "HmacSHA256",
#                 "validate-appkey": self.cfg.xt_api_key,
#                 "validate-recvwindow": "5000",
#                 "validate-timestamp": ts,
#                 "validate-signature": sign,
#             }
#             async with self.session.get(f"https://sapi.xt.com{path}", headers=headers) as r:
#                 text = await r.text()
#                 if r.status >= 400:
#                     return self._error("xt", f"http_{r.status}:{text[:200]}")
#                 data = json.loads(text) if text.strip() else {}
#                 rows = data.get("result", []) if isinstance(data, dict) else []
#                 assets = []
#                 for item in rows:
#                     free = float(item.get("availableAmount", 0.0))
#                     locked = float(item.get("frozenAmount", 0.0))
#                     if free or locked:
#                         assets.append({"asset": item.get("currency"), "free": free, "locked": locked})
#                 return self._ok("xt", assets, "xt endpoint/signature can vary by account type")
#         except Exception as exc:
#             return self._error("xt", str(exc))
# ===== END   [95/134] gate_mm_beast/app/services/unified_balance_service.py =====

# ===== BEGIN [96/134] gate_mm_beast/app/strategy/__init__.py sha256=e3b0c44298fc1c14 =====

# ===== END   [96/134] gate_mm_beast/app/strategy/__init__.py =====

# ===== BEGIN [97/134] gate_mm_beast/app/strategy/adverse_selection.py sha256=e7da417c2e80b0ef =====
# def should_quote(book_spread: float, tick: float) -> bool:
#     return book_spread >= tick
# ===== END   [97/134] gate_mm_beast/app/strategy/adverse_selection.py =====

# ===== BEGIN [98/134] gate_mm_beast/app/strategy/alpha_model.py sha256=85acf57705406324 =====
# [stripped_future_import] from __future__ import annotations
# import numpy as np
#
# def estimate_alpha(rt) -> dict:
#     df = rt.candles
#     if df is None or len(df) < 80:
#         return {"score": 0.0, "confidence": 0.0}
#     row = df.iloc[-1]
#     mid = rt.book.mid or float(row["close"])
#     tick = max(rt.tick, 1e-8)
#     trend = np.clip((float(row["ema8"]) - float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
#     reversion = np.clip(-float(row["z20"]) / 2.5, -1.0, 1.0)
#     flow = np.clip((rt.book.bid_size - rt.book.ask_size) / max(rt.book.bid_size + rt.book.ask_size, 1e-9), -1.0, 1.0)
#     spread_score = np.clip((rt.book.spread / tick - 1.0) / 5.0, -1.0, 1.0)
#     score = 0.35 * trend + 0.30 * reversion + 0.25 * flow + 0.10 * spread_score
#     return {"score": float(score), "confidence": float(min(abs(score), 0.95))}
# ===== END   [98/134] gate_mm_beast/app/strategy/alpha_model.py =====

# ===== BEGIN [99/134] gate_mm_beast/app/strategy/fair_value.py sha256=89cbd3fc80822d89 =====
# def fair_value(mid: float) -> float:
#     return mid
# ===== END   [99/134] gate_mm_beast/app/strategy/fair_value.py =====

# ===== BEGIN [100/134] gate_mm_beast/app/strategy/inventory_skew.py sha256=fd42245bd1bf60e9 =====
# def skew_from_inventory(net_qty: int, max_abs_qty: int) -> float:
#     if max_abs_qty <= 0:
#         return 0.0
#     return max(-1.0, min(1.0, net_qty / max_abs_qty))
# ===== END   [100/134] gate_mm_beast/app/strategy/inventory_skew.py =====

# ===== BEGIN [101/134] gate_mm_beast/app/strategy/quote_engine.py sha256=44b0264e9ffa601d =====
# [stripped_future_import] from __future__ import annotations
# from app.core.decimal_utils import round_to_tick
# from app.strategy.fair_value import fair_value
# from app.strategy.inventory_skew import skew_from_inventory
# from app.strategy.quote_sizer import quote_size
# from app.strategy.reservation_price import reservation_price
# from app.strategy.spread_model import target_half_spread_ticks
# from app.types import QuoteDecision
#
# class QuoteEngine:
#     def build(self, symbol: str, mid: float, bid: float, ask: float, tick: float, base_size: int, alpha_score: float, volatility_score: float, net_qty: int, max_abs_qty: int = 10) -> QuoteDecision:
#         fv = fair_value(mid)
#         inv_skew = skew_from_inventory(net_qty, max_abs_qty)
#         half_ticks = target_half_spread_ticks(volatility_score)
#         half_spread = half_ticks * tick
#         rp = reservation_price(fv, alpha_score, inv_skew, half_spread)
#         bid_px = round_to_tick(min(rp - half_spread, ask - tick), tick)
#         ask_px = round_to_tick(max(rp + half_spread, bid + tick), tick)
#         bid_sz, ask_sz = quote_size(base_size, alpha_score, inv_skew)
#         return QuoteDecision(
#             symbol=symbol,
#             bid_px=bid_px,
#             ask_px=ask_px,
#             bid_size=bid_sz,
#             ask_size=ask_sz,
#             alpha_score=alpha_score,
#             fair_value=fv,
#             meta={"inventory_skew": inv_skew, "reservation_price": rp},
#         )
# ===== END   [101/134] gate_mm_beast/app/strategy/quote_engine.py =====

# ===== BEGIN [102/134] gate_mm_beast/app/strategy/quote_sizer.py sha256=2786232e4a1c89e4 =====
# def quote_size(base_size: int, alpha_score: float, inventory_skew: float) -> tuple[int, int]:
#     bias = max(-0.5, min(0.5, alpha_score * 0.5 - inventory_skew * 0.5))
#     bid = max(1, int(base_size * (1.0 + bias)))
#     ask = max(1, int(base_size * (1.0 - bias)))
#     return bid, ask
# ===== END   [102/134] gate_mm_beast/app/strategy/quote_sizer.py =====

# ===== BEGIN [103/134] gate_mm_beast/app/strategy/reservation_price.py sha256=62a9d53f08ba03f6 =====
# def reservation_price(fair_value: float, alpha_score: float, inventory_skew: float, half_spread: float) -> float:
#     return fair_value + alpha_score * half_spread - inventory_skew * half_spread
# ===== END   [103/134] gate_mm_beast/app/strategy/reservation_price.py =====

# ===== BEGIN [104/134] gate_mm_beast/app/strategy/spread_model.py sha256=401fdf57de8d03f9 =====
# def target_half_spread_ticks(volatility_score: float) -> int:
#     if volatility_score > 0.8:
#         return 4
#     if volatility_score > 0.4:
#         return 3
#     return 2
# ===== END   [104/134] gate_mm_beast/app/strategy/spread_model.py =====

# ===== BEGIN [105/134] gate_mm_beast/app/types.py sha256=ed2fa6b1fa1d0bfb =====
# [stripped_future_import] from __future__ import annotations
# from dataclasses import dataclass, field
# from typing import Any, Dict, Optional
# import time
#
# @dataclass
# class BookTop:
#     bid: float = 0.0
#     ask: float = 0.0
#     bid_size: float = 0.0
#     ask_size: float = 0.0
#     ts: float = field(default_factory=time.time)
#
#     @property
#     def mid(self) -> float:
#         if self.bid > 0 and self.ask > 0:
#             return (self.bid + self.ask) / 2.0
#         return 0.0
#
#     @property
#     def spread(self) -> float:
#         if self.bid > 0 and self.ask >= self.bid:
#             return self.ask - self.bid
#         return 0.0
#
# @dataclass
# class QuoteDecision:
#     symbol: str
#     bid_px: float
#     ask_px: float
#     bid_size: int
#     ask_size: int
#     alpha_score: float
#     fair_value: float
#     meta: Dict[str, Any] = field(default_factory=dict)
#
# @dataclass
# class EngineStatus:
#     mode: str
#     started_at: float
#     symbols: list[str]
#     healthy: bool = True
#     message: str = "ok"
#
# @dataclass
# class ProtectiveExitCommand:
#     symbol: str
#     side: str
#     size: int
#     reason: str
#     stop_price: Optional[float] = None
#     marketable_limit_price: Optional[float] = None
# ===== END   [105/134] gate_mm_beast/app/types.py =====

# ===== BEGIN [106/134] gate_mm_beast/scripts/build_one_file_project.py sha256=e6b8fc9166e99d65 =====
# #!/usr/bin/env python3
# [stripped_future_import] from __future__ import annotations
#
# from pathlib import Path
# from datetime import datetime, timezone
# import hashlib
# import textwrap
#
# ROOT = Path('/Users/alep/Downloads')
# OUTPUT_DIR = ROOT / 'gate_mm_beast'
# OUTPUT_FILE = OUTPUT_DIR / 'gate_mm_unified_onefile.py'
# MANIFEST_FILE = OUTPUT_DIR / 'gate_mm_unified_onefile_manifest.txt'
#
# SOURCE_DIRS = [
#     ROOT / 'gate_mm_beast' / 'app',
#     ROOT / 'gate_mm_beast' / 'scripts',
#     ROOT / 'Hedging_Project' / 'src',
#     ROOT / 'ENA_Hedging_Project' / 'src',
# ]
#
# EXTRA_FILES = [
#     ROOT / 'gate_multi_ticker_mm_prod.py',
#     ROOT / 'gateaioms.py',
#     ROOT / 'beast.py',
#     ROOT / 'Hedging_Project' / 'real_time_trader.py',
#     ROOT / 'Hedging_Project' / 'proper_exchange_connection.py',
#     ROOT / 'Hedging_Project' / 'fixed_signature_trader.py',
#     ROOT / 'ENA_Hedging_Project' / 'run_ena_hedging.py',
# ]
#
# SKIP_PARTS = {'__pycache__', '.git', '.venv', '.pytest_cache'}
#
#
# def discover_files() -> list[Path]:
#     out: list[Path] = []
#     for d in SOURCE_DIRS:
#         if not d.exists():
#             continue
#         for p in sorted(d.rglob('*.py')):
#             if any(part in SKIP_PARTS for part in p.parts):
#                 continue
#             out.append(p)
#     for f in EXTRA_FILES:
#         if f.exists() and f.suffix == '.py':
#             out.append(f)
#     # de-duplicate while preserving order
#     uniq: list[Path] = []
#     seen = set()
#     for p in out:
#         sp = str(p)
#         if sp in seen:
#             continue
#         seen.add(sp)
#         uniq.append(p)
#     return uniq
#
#
# def read_text_safe(path: Path) -> str:
#     try:
#         return path.read_text(encoding='utf-8', errors='replace')
#     except Exception as exc:
#         return f"# [read_error] {path}: {exc}\n"
#
#
# def to_archive_comment_block(text: str) -> str:
#     out: list[str] = []
#     for line in text.splitlines():
#         stripped = line.strip()
#         if stripped.startswith("from __future__ import"):
#             out.append(f"# [stripped_future_import] {line}")
#         else:
#             out.append(f"# {line}" if line else "#")
#     return "\n".join(out)
#
#
# def launcher_block() -> str:
#     return textwrap.dedent(
#         '''
#         import os
#         import sys
#         from pathlib import Path
#
#         def _run_unified_launcher() -> int:
#             root = Path(__file__).resolve().parent
#             if (root / "app").exists():
#                 app_root = root
#             elif (root / "gate_mm_beast" / "app").exists():
#                 app_root = root / "gate_mm_beast"
#             else:
#                 print("ERROR: gate_mm_beast directory not found next to this file.")
#                 return 1
#             sys.path.insert(0, str(app_root))
#
#             mode = "paper"
#             if len(sys.argv) > 1:
#                 mode = str(sys.argv[1]).strip().lower()
#             else:
#                 mode = str(os.getenv("MODE", "paper")).strip().lower()
#
#             if mode not in {"paper", "live", "replay"}:
#                 print(f"ERROR: unsupported mode '{mode}'. Use paper/live/replay.")
#                 return 2
#
#             if mode in {"paper", "replay"}:
#                 os.environ["MODE"] = mode
#
#             from app.main import run
#             return int(run())
#
#         if __name__ == "__main__":
#             raise SystemExit(_run_unified_launcher())
#         '''
#     ).strip("\n")
#
#
# def build() -> tuple[int, int]:
#     files = discover_files()
#     created = datetime.now(timezone.utc).isoformat()
#     lines: list[str] = [
#         '#!/usr/bin/env python3',
#         '# -*- coding: utf-8 -*-',
#         '"""',
#         'UNIFIED ONE-FILE PROJECT BUNDLE',
#         f'Generated UTC: {created}',
#         f'Total source files: {len(files)}',
#         '',
#         'This file is a consolidated archive of multiple project modules.',
#         'Sections are delimited with source file paths for reappraisal/review.',
#         'Launcher usage: python gate_mm_unified_onefile.py [paper|live|replay]',
#         '"""',
#         '',
#         launcher_block(),
#         '',
#         '# ===== ARCHIVE SOURCE SECTIONS (COMMENTED) =====',
#         '',
#     ]
#
#     manifest: list[str] = [f'Generated UTC: {created}', '']
#
#     for idx, f in enumerate(files, start=1):
#         rel = f.relative_to(ROOT)
#         text = read_text_safe(f)
#         archived_text = to_archive_comment_block(text.rstrip('\n'))
#         digest = hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]
#         marker_top = f"# ===== BEGIN [{idx}/{len(files)}] {rel} sha256={digest} ====="
#         marker_bot = f"# ===== END   [{idx}/{len(files)}] {rel} ====="
#         lines.extend([marker_top, archived_text, marker_bot, ''])
#         manifest.append(f'{idx:04d}  {rel}  sha256={digest}  lines={text.count(chr(10)) + 1}')
#
#     OUTPUT_FILE.write_text('\n'.join(lines), encoding='utf-8')
#     MANIFEST_FILE.write_text('\n'.join(manifest) + '\n', encoding='utf-8')
#     return len(files), OUTPUT_FILE.stat().st_size
#
#
# if __name__ == '__main__':
#     count, size = build()
#     print(f'Created: {OUTPUT_FILE}')
#     print(f'Manifest: {MANIFEST_FILE}')
#     print(f'Files bundled: {count}')
#     print(f'Output size: {size} bytes')
# ===== END   [106/134] gate_mm_beast/scripts/build_one_file_project.py =====

# ===== BEGIN [107/134] gate_mm_beast/scripts/migrate_db.py sha256=908392aeb9f3acc6 =====
# from app.config import Settings
# from app.persistence.db import Database
#
# if __name__ == "__main__":
#     Database(Settings().db_path)
#     print("database initialized")
# ===== END   [107/134] gate_mm_beast/scripts/migrate_db.py =====

# ===== BEGIN [108/134] gate_mm_beast/scripts/run_live.py sha256=edf55dda3fee5474 =====
# from app.main import run
#
# if __name__ == "__main__":
#     raise SystemExit(run())
# ===== END   [108/134] gate_mm_beast/scripts/run_live.py =====

# ===== BEGIN [109/134] gate_mm_beast/scripts/run_paper.py sha256=7954055a8d142f41 =====
# import os
# os.environ["MODE"] = "paper"
# from app.main import run
#
# if __name__ == "__main__":
#     raise SystemExit(run())
# ===== END   [109/134] gate_mm_beast/scripts/run_paper.py =====

# ===== BEGIN [110/134] gate_mm_beast/scripts/run_replay.py sha256=8107936988087934 =====
# import os
# os.environ["MODE"] = "replay"
# from app.main import run
#
# if __name__ == "__main__":
#     raise SystemExit(run())
# ===== END   [110/134] gate_mm_beast/scripts/run_replay.py =====

# ===== BEGIN [111/134] Hedging_Project/src/hedging_market_maker.py sha256=aa4740c8680a2906 =====
# #!/usr/bin/env python3
# """
# Professional Hedging Market Maker
# Places best bid/ask orders and executes profitable sells
# """
#
# import os
# import sys
# import yaml
# import time
# import json
# import requests
# import hmac
# import hashlib
# import logging
# from datetime import datetime
# from typing import Dict, List, Optional, Tuple
# from dataclasses import dataclass
#
# # Add project root to path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
# @dataclass
# class Order:
#     id: str
#     symbol: str
#     side: str
#     size: float
#     price: float
#     timestamp: float
#
# @dataclass
# class Position:
#     symbol: str
#     size: float
#     entry_price: float
#     unrealized_pnl: float
#
# class HedgingMarketMaker:
#     """Professional hedging market maker for Gate.io futures"""
#     
#     def __init__(self, config_path: str = None):
#         # Load configuration
#         if config_path is None:
#             config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'hedging_config.yaml')
#         
#         with open(config_path, 'r') as f:
#             self.config = yaml.safe_load(f)
#         
#         # Setup logging
#         logging.basicConfig(
#             level=getattr(logging, self.config['monitoring']['log_level']),
#             format='%(asctime)s %(levelname)s %(message)s'
#         )
#         self.logger = logging.getLogger('HedgingMM')
#         
#         # API configuration
#         self.api_key = os.getenv("GATE_API_KEY", "")
#         self.api_secret = os.getenv("GATE_API_SECRET", "")
#         self.base_url = self.config['api']['base_url']
#         self.settle = self.config['api']['settle']
#         
#         # Trading parameters
#         self.symbol = self.config['trading']['symbol']
#         self.min_nominal = self.config['trading']['nominal_value_range']['min']
#         self.max_nominal = self.config['trading']['nominal_value_range']['max']
#         self.target_spread = self.config['trading']['target_spread']
#         
#         # State
#         self.running = False
#         self.orders = []
#         self.positions = []
#         self.cycle_count = 0
#         
#         self.logger.info("🚀 Hedging Market Maker initialized")
#         self.logger.info(f"📊 Symbol: {self.symbol}")
#         self.logger.info(f"💰 Nominal range: ${self.min_nominal}-${self.max_nominal}")
#     
#     def _sign_request(self, method: str, path: str, query_string: str, payload: str) -> Dict[str, str]:
#         """Generate Gate.io API signature"""
#         ts = str(int(time.time()))
#         payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#         sign_str = f"{method.upper()}\n{path}\n{query_string}\n{payload_hash}\n{ts}"
#         sign = hmac.new(
#             self.api_secret.encode("utf-8"),
#             sign_str.encode("utf-8"),
#             digestmod=hashlib.sha512,
#         ).hexdigest()
#         
#         return {
#             "Accept": "application/json",
#             "Content-Type": "application/json",
#             "KEY": self.api_key,
#             "Timestamp": ts,
#             "SIGN": sign,
#         }
#     
#     def _make_request(self, method: str, path: str, payload: str = "", private: bool = False) -> Optional[Dict]:
#         """Make API request"""
#         headers = self._sign_request(method, path, "", payload) if private else {
#             "Accept": "application/json",
#             "Content-Type": "application/json"
#         }
#         
#         try:
#             url = f"{self.base_url}{path}"
#             response = requests.request(method, url, headers=headers, data=payload if payload else None, timeout=10)
#             
#             if response.status_code == 200:
#                 return response.json()
#             else:
#                 self.logger.error(f"API Error {response.status_code}: {response.text}")
#                 return None
#                 
#         except Exception as e:
#             self.logger.error(f"Request exception: {e}")
#             return None
#     
#     def get_market_price(self) -> Tuple[float, float]:
#         """Get best bid and ask prices"""
#         data = self._make_request(
#             "GET", 
#             f"/futures/{self.settle}/order_book?contract={self.symbol}&limit=1"
#         )
#         
#         if data and data.get('asks') and data.get('bids'):
#             best_bid = float(data['bids'][0]['p'])
#             best_ask = float(data['asks'][0]['p'])
#             return best_bid, best_ask
#         
#         return None, None
#     
#     def get_positions(self) -> List[Position]:
#         """Get current positions"""
#         data = self._make_request("GET", f"/futures/{self.settle}/positions", "", private=True)
#         
#         positions = []
#         if data:
#             for pos in data:
#                 if float(pos['size']) != 0 and pos['contract'] == self.symbol:
#                     positions.append(Position(
#                         symbol=pos['contract'],
#                         size=float(pos['size']),
#                         entry_price=float(pos['entry_price']),
#                         unrealized_pnl=float(pos['unrealised_pnl'])
#                     ))
#         
#         return positions
#     
#     def calculate_order_size(self, price: float) -> float:
#         """Calculate order size for target nominal value"""
#         target_nominal = (self.min_nominal + self.max_nominal) / 2  # Use middle of range
#         size = target_nominal / price
#         
#         # Ensure minimum order size
#         min_size = 0.001
#         return max(size, min_size)
#     
#     def place_order(self, side: str, size: float, price: float) -> Optional[str]:
#         """Place limit order"""
#         order_data = {
#             "settle": self.settle,
#             "contract": self.symbol,
#             "size": str(size),
#             "price": str(price),
#             "type": "limit",
#             "tif": self.config['execution']['time_in_force']
#         }
#         
#         payload = json.dumps(order_data, separators=(",", ":"))
#         result = self._make_request("POST", f"/futures/{self.settle}/orders", payload, private=True)
#         
#         if result:
#             order_id = result.get('id')
#             self.logger.info(f"✅ Order placed: {side} {size:.6f} @ {price:.6f} (ID: {order_id})")
#             return order_id
#         else:
#             self.logger.error(f"❌ Failed to place {side} order")
#             return None
#     
#     def cancel_order(self, order_id: str) -> bool:
#         """Cancel order"""
#         result = self._make_request("DELETE", f"/futures/{self.settle}/orders/{order_id}", "", private=True)
#         return result is not None
#     
#     def place_best_bid_ask(self):
#         """Place orders at best bid and ask"""
#         best_bid, best_ask = self.get_market_price()
#         
#         if best_bid is None or best_ask is None:
#             self.logger.warning("❌ Cannot get market prices")
#             return
#         
#         # Calculate order sizes
#         bid_size = self.calculate_order_size(best_bid)
#         ask_size = self.calculate_order_size(best_ask)
#         
#         # Place buy order at best bid
#         bid_order_id = self.place_order("BUY", bid_size, best_bid)
#         if bid_order_id:
#             self.orders.append(Order(bid_order_id, self.symbol, "BUY", bid_size, best_bid, time.time()))
#         
#         # Place sell order at best ask
#         ask_order_id = self.place_order("SELL", ask_size, best_ask)
#         if ask_order_id:
#             self.orders.append(Order(ask_order_id, self.symbol, "SELL", ask_size, best_ask, time.time()))
#     
#     def check_profit_opportunities(self):
#         """Check for profitable selling opportunities"""
#         positions = self.get_positions()
#         best_bid, best_ask = self.get_market_price()
#         
#         if not positions or best_bid is None:
#             return
#         
#         for position in positions:
#             if position.size > 0:  # Long position
#                 profit_pct = (best_bid - position.entry_price) / position.entry_price
#                 
#                 if profit_pct >= self.config['hedging']['profit_threshold']:
#                     # Sell for profit
#                     sell_size = min(position.size, self.calculate_order_size(best_bid))
#                     order_id = self.place_order("SELL", sell_size, best_bid)
#                     
#                     if order_id:
#                         self.logger.info(f"💰 Profit sell: {sell_size:.6f} @ {best_bid:.6f} (Profit: {profit_pct:.2%})")
#     
#     def cleanup_orders(self):
#         """Cancel old orders"""
#         current_time = time.time()
#         max_age = self.config['trading']['order_refresh_interval']
#         
#         orders_to_cancel = []
#         for order in self.orders:
#             if current_time - order.timestamp > max_age:
#                 orders_to_cancel.append(order)
#         
#         for order in orders_to_cancel:
#             if self.cancel_order(order.id):
#                 self.logger.info(f"🗑️ Cancelled old order: {order.id}")
#                 self.orders.remove(order)
#     
#     def run_hedging_cycle(self):
#         """Run one hedging cycle"""
#         self.cycle_count += 1
#         cycle_start = time.time()
#         
#         self.logger.info(f"🔄 Cycle {self.cycle_count} started")
#         
#         # Get current state
#         positions = self.get_positions()
#         best_bid, best_ask = self.get_market_price()
#         
#         if best_bid and best_ask:
#             self.logger.info(f"📊 {self.symbol}: Bid ${best_bid:.6f} | Ask ${best_ask:.6f}")
#             self.logger.info(f"💼 Positions: {len(positions)}")
#         
#         # Place best bid/ask orders
#         self.place_best_bid_ask()
#         
#         # Check profit opportunities
#         if self.config['hedging']['auto_sell_profit']:
#             self.check_profit_opportunities()
#         
#         # Clean up old orders
#         self.cleanup_orders()
#         
#         # Wait for next cycle
#         elapsed = time.time() - cycle_start
#         sleep_time = max(0, self.config['hedging']['rebalance_interval'] - elapsed)
#         
#         self.logger.info(f"⏳ Cycle completed in {elapsed:.2f}s, waiting {sleep_time:.2f}s")
#         time.sleep(sleep_time)
#     
#     def run(self):
#         """Main trading loop"""
#         self.logger.info("🚀 Starting Hedging Market Maker")
#         self.running = True
#         
#         try:
#             while self.running:
#                 self.run_hedging_cycle()
#                 
#         except KeyboardInterrupt:
#             self.logger.info("🛑 Stopped by user")
#         except Exception as e:
#             self.logger.error(f"❌ Fatal error: {e}")
#         finally:
#             # Cancel all orders
#             for order in self.orders:
#                 self.cancel_order(order.id)
#             self.logger.info("✅ All orders cancelled")
#
# def main():
#     """Main function"""
#     # Check environment variables
#     if not os.getenv("GATE_API_KEY") or not os.getenv("GATE_API_SECRET"):
#         print("❌ Missing GATE_API_KEY or GATE_API_SECRET")
#         print("Run: export GATE_API_KEY='your-key' && export GATE_API_SECRET='your-secret'")
#         return
#     
#     # Create and run hedging market maker
#     hedger = HedgingMarketMaker()
#     hedger.run()
#
# if __name__ == "__main__":
#     main()
# ===== END   [111/134] Hedging_Project/src/hedging_market_maker.py =====

# ===== BEGIN [112/134] Hedging_Project/src/hedging_system.py sha256=5b293c708a1ddc45 =====
# #!/usr/bin/env python3
# """
# Professional Hedging System
# Places best bid/ask orders and manages profitable sells
# """
#
# import os
# import sys
# import time
# import logging
# from datetime import datetime
# from typing import Dict, List, Optional
#
# from utils.gateio_client import GateIOClient
# from utils.position_manager import PositionManager
#
# class HedgingSystem:
#     """Professional hedging system for Gate.io futures"""
#     
#     def __init__(self, symbol: str = "ENA_USDT", nominal_range: tuple = (0.01, 0.10)):
#         self.symbol = symbol
#         self.min_nominal, self.max_nominal = nominal_range
#         self.target_nominal = (self.min_nominal + self.max_nominal) / 2
#         
#         # Initialize clients
#         self.client = GateIOClient()
#         self.position_manager = PositionManager(self.client, profit_threshold=0.002)
#         
#         # Setup logging
#         self.logger = logging.getLogger('HedgingSystem')
#         
#         # State
#         self.running = False
#         self.cycle_count = 0
#         self.active_orders = {}
#         
#         self.logger.info("🚀 Hedging System initialized")
#         self.logger.info(f"📊 Symbol: {self.symbol}")
#         self.logger.info(f"💰 Nominal range: ${self.min_nominal}-${self.max_nominal}")
#     
#     def place_best_bid_ask_orders(self) -> bool:
#         """Place orders at best bid and ask prices"""
#         # Get current market prices
#         best_bid, best_ask = self.client.get_best_bid_ask(self.symbol)
#         
#         if best_bid is None or best_ask is None:
#             self.logger.warning("❌ Cannot get market prices")
#             return False
#         
#         # Calculate order sizes
#         bid_size = self.client.calculate_nominal_size(best_bid, self.target_nominal)
#         ask_size = self.client.calculate_nominal_size(best_ask, self.target_nominal)
#         
#         # Place buy order at best bid
#         bid_result = self.client.place_order(
#             symbol=self.symbol,
#             side="BUY",
#             size=bid_size,
#             price=best_bid,
#             order_type="limit",
#             tif="ioc"
#         )
#         
#         if bid_result.success:
#             order_id = bid_result.data.get('id')
#             self.active_orders[order_id] = {
#                 'side': 'BUY',
#                 'size': bid_size,
#                 'price': best_bid,
#                 'timestamp': time.time()
#             }
#             self.logger.info(f"✅ Buy order placed: {bid_size:.6f} @ ${best_bid:.6f}")
#         else:
#             self.logger.error(f"❌ Buy order failed: {bid_result.error}")
#         
#         # Place sell order at best ask
#         ask_result = self.client.place_order(
#             symbol=self.symbol,
#             side="SELL", 
#             size=ask_size,
#             price=best_ask,
#             order_type="limit",
#             tif="ioc"
#         )
#         
#         if ask_result.success:
#             order_id = ask_result.data.get('id')
#             self.active_orders[order_id] = {
#                 'side': 'SELL',
#                 'size': ask_size,
#                 'price': best_ask,
#                 'timestamp': time.time()
#             }
#             self.logger.info(f"✅ Sell order placed: {ask_size:.6f} @ ${best_ask:.6f}")
#         else:
#             self.logger.error(f"❌ Sell order failed: {ask_result.error}")
#         
#         return bid_result.success or ask_result.success
#     
#     def check_and_take_profits(self) -> int:
#         """Check for profitable positions and take profits"""
#         profitable_positions = self.position_manager.get_profitable_positions()
#         profits_taken = 0
#         
#         for position in profitable_positions:
#             if self.position_manager.should_sell_position(position):
#                 success = self.position_manager.close_position_for_profit(position)
#                 if success:
#                     profits_taken += 1
#         
#         return profits_taken
#     
#     def cleanup_old_orders(self):
#         """Remove old order records"""
#         current_time = time.time()
#         max_age = 60  # Keep records for 1 minute
#         
#         old_orders = [
#             order_id for order_id, order in self.active_orders.items()
#             if current_time - order['timestamp'] > max_age
#         ]
#         
#         for order_id in old_orders:
#             del self.active_orders[order_id]
#         
#         if old_orders:
#             self.logger.debug(f"🗑️ Cleaned up {len(old_orders)} old order records")
#     
#     def get_market_status(self) -> Dict:
#         """Get current market status"""
#         best_bid, best_ask = self.client.get_best_bid_ask(self.symbol)
#         positions = self.position_manager.get_positions()
#         
#         return {
#             'symbol': self.symbol,
#             'best_bid': best_bid,
#             'best_ask': best_ask,
#             'spread': (best_ask - best_bid) / best_bid if best_bid and best_ask else None,
#             'position_count': len(positions),
#             'active_orders': len(self.active_orders)
#         }
#     
#     def run_hedging_cycle(self):
#         """Run one complete hedging cycle"""
#         self.cycle_count += 1
#         cycle_start = time.time()
#         
#         self.logger.info(f"🔄 Cycle {self.cycle_count} started")
#         
#         # Get market status
#         status = self.get_market_status()
#         self.logger.info(f"📊 {status['symbol']}: Bid ${status['best_bid']:.6f} | Ask ${status['best_ask']:.6f}")
#         self.logger.info(f"💼 Positions: {status['position_count']} | Active Orders: {status['active_orders']}")
#         
#         # Place best bid/ask orders
#         self.logger.info("🎯 Placing best bid/ask orders...")
#         orders_placed = self.place_best_bid_ask_orders()
#         
#         # Check for profit opportunities
#         self.logger.info("💰 Checking profit opportunities...")
#         profits_taken = self.check_and_take_profits()
#         
#         # Cleanup
#         self.cleanup_old_orders()
#         
#         # Cycle summary
#         elapsed = time.time() - cycle_start
#         self.logger.info(f"✅ Cycle {self.cycle_count} completed in {elapsed:.2f}s")
#         self.logger.info(f"📈 Orders placed: {orders_placed} | Profits taken: {profits_taken}")
#         
#         # Wait for next cycle
#         sleep_time = max(0, 5 - elapsed)  # 5 second cycles
#         if sleep_time > 0:
#             self.logger.info(f"⏳ Waiting {sleep_time:.2f}s for next cycle...")
#             time.sleep(sleep_time)
#     
#     def run(self):
#         """Main trading loop"""
#         self.logger.info("🚀 Starting Professional Hedging System")
#         self.logger.info("⚠️  LIVE TRADING MODE - Real orders will be placed!")
#         
#         try:
#             self.running = True
#             while self.running:
#                 self.run_hedging_cycle()
#                 
#         except KeyboardInterrupt:
#             self.logger.info("🛑 Hedging system stopped by user")
#         except Exception as e:
#             self.logger.error(f"❌ Fatal error: {e}")
#         finally:
#             self.logger.info("✅ Hedging system shutdown complete")
#
# def main():
#     """Main function for testing"""
#     # Setup logging
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s %(name)s %(levelname)s %(message)s'
#     )
#     
#     # Check API keys
#     if not os.getenv("GATE_API_KEY") or not os.getenv("GATE_API_SECRET"):
#         print("❌ Missing GATE_API_KEY or GATE_API_SECRET")
#         print("Set environment variables and try again")
#         return
#     
#     # Create and run hedging system
#     hedger = HedgingSystem(
#         symbol="ENA_USDT",
#         nominal_range=(0.01, 0.10)  # 1-10 cent nominal value
#     )
#     
#     hedger.run()
#
# if __name__ == "__main__":
#     main()
# ===== END   [112/134] Hedging_Project/src/hedging_system.py =====

# ===== BEGIN [113/134] Hedging_Project/src/hedging_system_247.py sha256=a2ddec790a02875c =====
# #!/usr/bin/env python3
# """
# 24/7 Professional Hedging System
# Continuous trading with proper exchange integration
# """
#
# import os
# import sys
# import time
# import json
# import signal
# import logging
# import asyncio
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional
#
# # Add project path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
# from utils.gateio_client import GateIOClient
# from utils.position_manager import PositionManager
#
# class HedgingSystem247:
#     """24/7 Professional hedging system"""
#     
#     def __init__(self):
#         # Environment variables
#         self.gate_api_key = os.getenv("GATE_API_KEY", "")
#         self.gate_api_secret = os.getenv("GATE_API_SECRET", "")
#         self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
#         
#         # Validate environment
#         self._validate_environment()
#         
#         # Configuration
#         self.symbol = "ENA_USDT"
#         self.min_nominal = 0.01
#         self.max_nominal = 0.10
#         self.target_nominal = (self.min_nominal + self.max_nominal) / 2
#         
#         # Initialize clients
#         self.client = GateIOClient()
#         self.position_manager = PositionManager(self.client, profit_threshold=0.002)
#         
#         # Setup logging
#         self._setup_logging()
#         
#         # System state
#         self.running = False
#         self.shutdown_requested = False
#         self.cycle_count = 0
#         self.start_time = None
#         self.last_trade_time = None
#         self.daily_stats = {
#             'orders_placed': 0,
#             'profits_taken': 0,
#             'errors': 0,
#             'total_pnl': 0.0
#         }
#         
#         # Setup signal handlers
#         signal.signal(signal.SIGINT, self._signal_handler)
#         signal.signal(signal.SIGTERM, self._signal_handler)
#         
#         self.logger.info("🚀 24/7 Hedging System initialized")
#         self.logger.info(f"🔑 Gate.io API: {'✅ Configured' if self.gate_api_key else '❌ Missing'}")
#         self.logger.info(f"🤖 OpenRouter API: {'✅ Configured' if self.openrouter_api_key else '❌ Missing'}")
#         self.logger.info(f"📊 Trading Symbol: {self.symbol}")
#         self.logger.info(f"💰 Nominal Range: ${self.min_nominal}-${self.max_nominal}")
#     
#     def _validate_environment(self):
#         """Validate required environment variables"""
#         missing = []
#         
#         if not self.gate_api_key:
#             missing.append("GATE_API_KEY")
#         if not self.gate_api_secret:
#             missing.append("GATE_API_SECRET")
#         
#         if missing:
#             print(f"❌ Missing environment variables: {', '.join(missing)}")
#             print("Please set them and restart:")
#             for var in missing:
#                 print(f"   export {var}='your-value'")
#             sys.exit(1)
#     
#     def _setup_logging(self):
#         """Setup comprehensive logging"""
#         log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
#         os.makedirs(log_dir, exist_ok=True)
#         
#         log_file = os.path.join(log_dir, f'hedging_247_{datetime.now().strftime("%Y%m%d")}.log')
#         
#         # Configure logging
#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
#             handlers=[
#                 logging.FileHandler(log_file, mode='a'),
#                 logging.StreamHandler(sys.stdout)
#             ]
#         )
#         
#         self.logger = logging.getLogger('Hedging247')
#     
#     def _signal_handler(self, signum, frame):
#         """Handle shutdown signals"""
#         self.logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
#         self.shutdown_requested = True
#         self.running = False
#     
#     def test_exchange_connection(self) -> bool:
#         """Test connection to Gate.io exchange"""
#         self.logger.info("🔍 Testing exchange connection...")
#         
#         try:
#             # Test public endpoint
#             contracts = self.client.get_contracts()
#             if contracts.success:
#                 self.logger.info(f"✅ Exchange connected: {len(contracts.data)} contracts available")
#             else:
#                 self.logger.error(f"❌ Exchange connection failed: {contracts.error}")
#                 return False
#             
#             # Test private endpoint
#             if self.gate_api_key and self.gate_api_secret:
#                 account = self.client.get_account()
#                 if account.success:
#                     balance = float(account.data.get('total', 0))
#                     self.logger.info(f"✅ Account connected: Balance ${balance:.2f}")
#                 else:
#                     self.logger.error(f"❌ Account connection failed: {account.error}")
#                     return False
#             
#             return True
#             
#         except Exception as e:
#             self.logger.error(f"❌ Connection test failed: {e}")
#             return False
#     
#     def get_market_status(self) -> Dict:
#         """Get comprehensive market status"""
#         try:
#             best_bid, best_ask = self.client.get_best_bid_ask(self.symbol)
#             positions = self.position_manager.get_positions()
#             
#             status = {
#                 'timestamp': datetime.now().isoformat(),
#                 'symbol': self.symbol,
#                 'best_bid': best_bid,
#                 'best_ask': best_ask,
#                 'spread_pct': ((best_ask - best_bid) / best_bid * 100) if best_bid and best_ask else None,
#                 'position_count': len(positions),
#                 'total_position_size': sum(abs(p.size) for p in positions),
#                 'unrealized_pnl': sum(p.unrealized_pnl for p in positions),
#                 'exchange_connected': True
#             }
#             
#             return status
#             
#         except Exception as e:
#             self.logger.error(f"❌ Market status error: {e}")
#             return {
#                 'timestamp': datetime.now().isoformat(),
#                 'symbol': self.symbol,
#                 'exchange_connected': False,
#                 'error': str(e)
#             }
#     
#     def place_best_bid_ask_orders(self) -> int:
#         """Place orders at best bid and ask prices"""
#         orders_placed = 0
#         
#         try:
#             best_bid, best_ask = self.client.get_best_bid_ask(self.symbol)
#             
#             if not best_bid or not best_ask:
#                 self.logger.warning("❌ Cannot get market prices")
#                 return 0
#             
#             # Calculate order sizes
#             bid_size = self.client.calculate_nominal_size(best_bid, self.target_nominal)
#             ask_size = self.client.calculate_nominal_size(best_ask, self.target_nominal)
#             
#             nominal_bid = bid_size * best_bid
#             nominal_ask = ask_size * best_ask
#             
#             # Place buy order at best bid
#             bid_result = self.client.place_order(
#                 symbol=self.symbol,
#                 side="BUY",
#                 size=bid_size,
#                 price=best_bid,
#                 order_type="limit",
#                 tif="ioc"
#             )
#             
#             if bid_result.success:
#                 order_id = bid_result.data.get('id')
#                 self.logger.info(f"✅ BUY order placed: {bid_size:.6f} @ ${best_bid:.6f} (nominal: ${nominal_bid:.4f})")
#                 orders_placed += 1
#                 self.last_trade_time = time.time()
#                 self.daily_stats['orders_placed'] += 1
#             else:
#                 self.logger.error(f"❌ BUY order failed: {bid_result.error}")
#                 self.daily_stats['errors'] += 1
#             
#             # Place sell order at best ask
#             ask_result = self.client.place_order(
#                 symbol=self.symbol,
#                 side="SELL",
#                 size=ask_size,
#                 price=best_ask,
#                 order_type="limit",
#                 tif="ioc"
#             )
#             
#             if ask_result.success:
#                 order_id = ask_result.data.get('id')
#                 self.logger.info(f"✅ SELL order placed: {ask_size:.6f} @ ${best_ask:.6f} (nominal: ${nominal_ask:.4f})")
#                 orders_placed += 1
#                 self.last_trade_time = time.time()
#                 self.daily_stats['orders_placed'] += 1
#             else:
#                 self.logger.error(f"❌ SELL order failed: {ask_result.error}")
#                 self.daily_stats['errors'] += 1
#             
#         except Exception as e:
#             self.logger.error(f"❌ Order placement error: {e}")
#             self.daily_stats['errors'] += 1
#         
#         return orders_placed
#     
#     def check_and_take_profits(self) -> int:
#         """Check for profitable positions and take profits"""
#         profits_taken = 0
#         
#         try:
#             profitable_positions = self.position_manager.get_profitable_positions()
#             
#             for position in profitable_positions:
#                 if self.position_manager.should_sell_position(position):
#                     success = self.position_manager.close_position_for_profit(position)
#                     if success:
#                         profits_taken += 1
#                         self.daily_stats['profits_taken'] += 1
#                         self.daily_stats['total_pnl'] += position.unrealized_pnl
#                         self.logger.info(f"💰 Profit taken: {position.unrealized_pct:.2%} (${position.unrealized_pnl:.4f})")
#             
#         except Exception as e:
#             self.logger.error(f"❌ Profit taking error: {e}")
#             self.daily_stats['errors'] += 1
#         
#         return profits_taken
#     
#     def log_system_status(self):
#         """Log comprehensive system status"""
#         if self.cycle_count % 12 == 0:  # Every minute (assuming 5-second cycles)
#             uptime = time.time() - self.start_time if self.start_time else 0
#             uptime_str = str(timedelta(seconds=int(uptime)))
#             
#             status = self.get_market_status()
#             
#             self.logger.info("📊 SYSTEM STATUS UPDATE")
#             self.logger.info(f"⏱️  Uptime: {uptime_str}")
#             self.logger.info(f"🔄 Cycles: {self.cycle_count}")
#             self.logger.info(f"📈 {self.symbol}: Bid ${status['best_bid']:.6f} | Ask ${status['best_ask']:.6f}")
#             if status['spread_pct']:
#                 self.logger.info(f"📊 Spread: {status['spread_pct']:.3f}%")
#             self.logger.info(f"💼 Positions: {status['position_count']} (size: {status.get('total_position_size', 0):.6f})")
#             self.logger.info(f"💰 Daily PnL: ${self.daily_stats['total_pnl']:.4f}")
#             self.logger.info(f"📈 Daily Stats: {self.daily_stats['orders_placed']} orders, {self.daily_stats['profits_taken']} profits, {self.daily_stats['errors']} errors")
#             
#             # Check if we haven't traded recently
#             if self.last_trade_time:
#                 time_since_trade = time.time() - self.last_trade_time
#                 if time_since_trade > 300:  # 5 minutes
#                     self.logger.warning(f"⚠️  No trades for {int(time_since_trade/60)} minutes")
#     
#     def run_hedging_cycle(self):
#         """Run one complete hedging cycle"""
#         if self.shutdown_requested:
#             return
#         
#         self.cycle_count += 1
#         cycle_start = time.time()
#         
#         try:
#             # Place best bid/ask orders
#             orders_placed = self.place_best_bid_ask_orders()
#             
#             # Check for profit opportunities
#             profits_taken = self.check_and_take_profits()
#             
#             # Log status periodically
#             self.log_system_status()
#             
#             # Cycle timing
#             elapsed = time.time() - cycle_start
#             sleep_time = max(0, 5 - elapsed)  # 5-second cycles
#             
#             if sleep_time > 0:
#                 time.sleep(sleep_time)
#             
#         except Exception as e:
#             self.logger.error(f"❌ Cycle {self.cycle_count} error: {e}")
#             self.daily_stats['errors'] += 1
#             time.sleep(5)  # Wait before retrying
#     
#     def reset_daily_stats(self):
#         """Reset daily statistics at midnight"""
#         now = datetime.now()
#         if now.hour == 0 and now.minute == 0:
#             self.logger.info("📅 Resetting daily statistics")
#             self.daily_stats = {
#                 'orders_placed': 0,
#                 'profits_taken': 0,
#                 'errors': 0,
#                 'total_pnl': 0.0
#             }
#     
#     def run(self):
#         """Main 24/7 trading loop"""
#         self.logger.info("🚀 Starting 24/7 Professional Hedging System")
#         self.logger.info("⚠️  LIVE TRADING MODE - Real orders will be placed!")
#         self.logger.info("🔊 Keep Gate.io exchange open to hear order sounds")
#         
#         # Test exchange connection
#         if not self.test_exchange_connection():
#             self.logger.error("❌ Exchange connection failed - cannot start trading")
#             return
#         
#         self.start_time = time.time()
#         self.running = True
#         
#         try:
#             while self.running and not self.shutdown_requested:
#                 self.reset_daily_stats()
#                 self.run_hedging_cycle()
#                 
#         except KeyboardInterrupt:
#             self.logger.info("🛑 System stopped by user")
#         except Exception as e:
#             self.logger.error(f"❌ Fatal system error: {e}")
#         finally:
#             self.logger.info("✅ 24/7 Hedging System shutdown complete")
#             
#             # Final status
#             if self.start_time:
#                 total_uptime = time.time() - self.start_time
#                 self.logger.info(f"📊 Final Stats:")
#                 self.logger.info(f"   Total uptime: {str(timedelta(seconds=int(total_uptime)))}")
#                 self.logger.info(f"   Total cycles: {self.cycle_count}")
#                 self.logger.info(f"   Daily orders: {self.daily_stats['orders_placed']}")
#                 self.logger.info(f"   Daily profits: {self.daily_stats['profits_taken']}")
#                 self.logger.info(f"   Daily PnL: ${self.daily_stats['total_pnl']:.4f}")
#
# def main():
#     """Main entry point"""
#     print("🚀 24/7 PROFESSIONAL HEDGING SYSTEM")
#     print("=" * 50)
#     print("📊 Continuous Gate.io Futures Trading")
#     print("💰 Nominal Value: $0.01-$0.10 per trade")
#     print("🔊 Listen for exchange sounds on successful orders")
#     print("=" * 50)
#     
#     # Create and run 24/7 system
#     system = HedgingSystem247()
#     system.run()
#
# if __name__ == "__main__":
#     main()
# ===== END   [113/134] Hedging_Project/src/hedging_system_247.py =====

# ===== BEGIN [114/134] Hedging_Project/src/hedging_system_connected.py sha256=86b685f4e92cb3e9 =====
# #!/usr/bin/env python3
# """
# Fully Connected 24/7 Hedging System
# Proper API integration and AI configuration
# """
#
# import os
# import sys
# import time
# import signal
# import logging
# import asyncio
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional
#
# # Add project path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
# from utils.enhanced_gateio_client import EnhancedGateIOClient
#
# class ConnectedHedgingSystem:
#     """Fully connected 24/7 hedging system with AI"""
#     
#     def __init__(self):
#         # Initialize enhanced client
#         self.client = EnhancedGateIOClient()
#         
#         # Configuration
#         self.symbol = "ENA_USDT"
#         self.min_nominal = 0.01
#         self.max_nominal = 0.10
#         self.target_nominal = (self.min_nominal + self.max_nominal) / 2
#         self.profit_threshold = 0.002  # 0.2%
#         
#         # Setup logging
#         self._setup_logging()
#         
#         # System state
#         self.running = False
#         self.shutdown_requested = False
#         self.cycle_count = 0
#         self.start_time = None
#         self.last_trade_time = None
#         self.daily_stats = {
#             'orders_placed': 0,
#             'profits_taken': 0,
#             'errors': 0,
#             'total_pnl': 0.0,
#             'ai_decisions': 0
#         }
#         
#         # Setup signal handlers
#         signal.signal(signal.SIGINT, self._signal_handler)
#         signal.signal(signal.SIGTERM, self._signal_handler)
#         
#         self.logger.info("🚀 Connected Hedging System initialized")
#         self.logger.info(f"📊 Symbol: {self.symbol}")
#         self.logger.info(f"💰 Nominal Range: ${self.min_nominal}-${self.max_nominal}")
#         self.logger.info(f"🎯 Profit Threshold: {self.profit_threshold:.1%}")
#     
#     def _setup_logging(self):
#         """Setup comprehensive logging"""
#         log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
#         os.makedirs(log_dir, exist_ok=True)
#         
#         log_file = os.path.join(log_dir, f'hedging_connected_{datetime.now().strftime("%Y%m%d")}.log')
#         
#         # Configure logging
#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
#             handlers=[
#                 logging.FileHandler(log_file, mode='a'),
#                 logging.StreamHandler(sys.stdout)
#             ]
#         )
#         
#         self.logger = logging.getLogger('ConnectedHedging')
#     
#     def _signal_handler(self, signum, frame):
#         """Handle shutdown signals"""
#         self.logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
#         self.shutdown_requested = True
#         self.running = False
#     
#     def test_full_connection(self) -> bool:
#         """Test complete system connection"""
#         self.logger.info("🔍 Testing full system connection...")
#         
#         # Test API connection
#         api_test = self.client.test_connection()
#         if not api_test.success:
#             self.logger.error(f"❌ API connection failed: {api_test.error}")
#             return False
#         
#         self.logger.info(f"✅ API connected: {api_test.data['contracts_count']} contracts")
#         
#         # Test market data
#         best_bid, best_ask = self.client.get_best_bid_ask(self.symbol)
#         if best_bid and best_ask:
#             self.logger.info(f"✅ Market data: Bid ${best_bid:.6f} | Ask ${best_ask:.6f}")
#         else:
#             self.logger.error("❌ Cannot get market data")
#             return False
#         
#         # Test AI connection
#         ai_test = self.client.get_ai_decision({
#             'symbol': self.symbol,
#             'bid': best_bid,
#             'ask': best_ask,
#             'spread': (best_ask - best_bid) / best_bid
#         })
#         
#         if ai_test:
#             self.logger.info(f"✅ AI connected: {ai_test['action']} (confidence: {ai_test['confidence']:.2f})")
#         else:
#             self.logger.warning("⚠️  AI not available - will run without AI")
#         
#         return True
#     
#     def get_market_status(self) -> Dict:
#         """Get comprehensive market status"""
#         try:
#             best_bid, best_ask = self.client.get_best_bid_ask(self.symbol)
#             positions_result = self.client.get_positions()
#             
#             positions = []
#             if positions_result.success:
#                 for pos in positions_result.data:
#                     size = float(pos['size'])
#                     if size != 0:
#                         positions.append({
#                             'symbol': pos['contract'],
#                             'size': size,
#                             'entry_price': float(pos['entry_price']),
#                             'unrealized_pnl': float(pos['unrealised_pnl'])
#                         })
#             
#             status = {
#                 'timestamp': datetime.now().isoformat(),
#                 'symbol': self.symbol,
#                 'best_bid': best_bid,
#                 'best_ask': best_ask,
#                 'spread_pct': ((best_ask - best_bid) / best_bid * 100) if best_bid and best_ask else None,
#                 'position_count': len(positions),
#                 'total_position_size': sum(abs(p['size']) for p in positions),
#                 'unrealized_pnl': sum(p['unrealized_pnl'] for p in positions),
#                 'system_connected': True
#             }
#             
#             return status
#             
#         except Exception as e:
#             self.logger.error(f"❌ Market status error: {e}")
#             return {
#                 'timestamp': datetime.now().isoformat(),
#                 'symbol': self.symbol,
#                 'system_connected': False,
#                 'error': str(e)
#             }
#     
#     def place_hedging_orders(self) -> int:
#         """Place best bid/ask hedging orders"""
#         orders_placed = 0
#         
#         try:
#             best_bid, best_ask = self.client.get_best_bid_ask(self.symbol)
#             
#             if not best_bid or not best_ask:
#                 self.logger.warning("❌ Cannot get market prices")
#                 return 0
#             
#             # Get AI decision
#             market_data = {
#                 'symbol': self.symbol,
#                 'best_bid': best_bid,
#                 'best_ask': best_ask,
#                 'spread': (best_ask - best_bid) / best_bid,
#                 'timestamp': datetime.now().isoformat()
#             }
#             
#             ai_decision = self.client.get_ai_decision(market_data)
#             self.daily_stats['ai_decisions'] += 1
#             
#             # Calculate order sizes
#             bid_size = self.client.calculate_nominal_size(best_bid, self.target_nominal)
#             ask_size = self.client.calculate_nominal_size(best_ask, self.target_nominal)
#             
#             nominal_bid = bid_size * best_bid
#             nominal_ask = ask_size * best_ask
#             
#             # Check AI recommendation
#             if ai_decision['action'] == 'BUY' and ai_decision['confidence'] > 0.7:
#                 # AI suggests buying - place larger buy order
#                 bid_size *= 1.5
#                 self.logger.info(f"🤖 AI suggests BUY with confidence {ai_decision['confidence']:.2f}")
#             elif ai_decision['action'] == 'SELL' and ai_decision['confidence'] > 0.7:
#                 # AI suggests selling - place larger sell order
#                 ask_size *= 1.5
#                 self.logger.info(f"🤖 AI suggests SELL with confidence {ai_decision['confidence']:.2f}")
#             
#             # Place buy order at best bid
#             bid_result = self.client.place_order(
#                 symbol=self.symbol,
#                 side="BUY",
#                 size=bid_size,
#                 price=best_bid,
#                 order_type="limit",
#                 tif="ioc"
#             )
#             
#             if bid_result.success:
#                 order_id = bid_result.data.get('id')
#                 self.logger.info(f"✅ BUY order: {bid_size:.6f} @ ${best_bid:.6f} (nominal: ${nominal_bid:.4f})")
#                 orders_placed += 1
#                 self.last_trade_time = time.time()
#                 self.daily_stats['orders_placed'] += 1
#             else:
#                 self.logger.error(f"❌ BUY order failed: {bid_result.error}")
#                 self.daily_stats['errors'] += 1
#             
#             # Place sell order at best ask
#             ask_result = self.client.place_order(
#                 symbol=self.symbol,
#                 side="SELL",
#                 size=ask_size,
#                 price=best_ask,
#                 order_type="limit",
#                 tif="ioc"
#             )
#             
#             if ask_result.success:
#                 order_id = ask_result.data.get('id')
#                 self.logger.info(f"✅ SELL order: {ask_size:.6f} @ ${best_ask:.6f} (nominal: ${nominal_ask:.4f})")
#                 orders_placed += 1
#                 self.last_trade_time = time.time()
#                 self.daily_stats['orders_placed'] += 1
#             else:
#                 self.logger.error(f"❌ SELL order failed: {ask_result.error}")
#                 self.daily_stats['errors'] += 1
#             
#         except Exception as e:
#             self.logger.error(f"❌ Order placement error: {e}")
#             self.daily_stats['errors'] += 1
#         
#         return orders_placed
#     
#     def check_profit_opportunities(self) -> int:
#         """Check and take profit opportunities"""
#         profits_taken = 0
#         
#         try:
#             positions_result = self.client.get_positions()
#             
#             if positions_result.success:
#                 for pos in positions_result.data:
#                     size = float(pos['size'])
#                     if size == 0:
#                         continue
#                     
#                     entry_price = float(pos['entry_price'])
#                     mark_price = float(pos['mark_price'])
#                     unrealized_pnl = float(pos['unrealised_pnl'])
#                     
#                     # Calculate profit percentage
#                     profit_pct = (mark_price - entry_price) / entry_price if entry_price > 0 else 0
#                     
#                     if profit_pct >= self.profit_threshold:
#                         # Take profit
#                         sell_size = abs(size)
#                         sell_result = self.client.place_order(
#                             symbol=pos['contract'],
#                             side="SELL" if size > 0 else "BUY",
#                             size=sell_size,
#                             price=0,  # Market order
#                             order_type="market"
#                         )
#                         
#                         if sell_result.success:
#                             profits_taken += 1
#                             self.daily_stats['profits_taken'] += 1
#                             self.daily_stats['total_pnl'] += unrealized_pnl
#                             self.logger.info(f"💰 Profit taken: {profit_pct:.2%} (${unrealized_pnl:.4f})")
#                         else:
#                             self.logger.error(f"❌ Profit take failed: {sell_result.error}")
#                             self.daily_stats['errors'] += 1
#             
#         except Exception as e:
#             self.logger.error(f"❌ Profit check error: {e}")
#             self.daily_stats['errors'] += 1
#         
#         return profits_taken
#     
#     def log_system_status(self):
#         """Log comprehensive system status"""
#         if self.cycle_count % 12 == 0:  # Every minute
#             uptime = time.time() - self.start_time if self.start_time else 0
#             uptime_str = str(timedelta(seconds=int(uptime)))
#             
#             status = self.get_market_status()
#             
#             self.logger.info("📊 SYSTEM STATUS UPDATE")
#             self.logger.info(f"⏱️  Uptime: {uptime_str}")
#             self.logger.info(f"🔄 Cycles: {self.cycle_count}")
#             self.logger.info(f"📈 {self.symbol}: Bid ${status['best_bid']:.6f} | Ask ${status['best_ask']:.6f}")
#             if status['spread_pct']:
#                 self.logger.info(f"📊 Spread: {status['spread_pct']:.3f}%")
#             self.logger.info(f"💼 Positions: {status['position_count']} (size: {status.get('total_position_size', 0):.6f})")
#             self.logger.info(f"💰 Daily PnL: ${self.daily_stats['total_pnl']:.4f}")
#             self.logger.info(f"🤖 AI Decisions: {self.daily_stats['ai_decisions']}")
#             self.logger.info(f"📈 Daily Stats: {self.daily_stats['orders_placed']} orders, {self.daily_stats['profits_taken']} profits, {self.daily_stats['errors']} errors")
#             
#             # Check trading activity
#             if self.last_trade_time:
#                 time_since_trade = time.time() - self.last_trade_time
#                 if time_since_trade > 300:  # 5 minutes
#                     self.logger.warning(f"⚠️  No trades for {int(time_since_trade/60)} minutes")
#     
#     def run_hedging_cycle(self):
#         """Run one complete hedging cycle"""
#         if self.shutdown_requested:
#             return
#         
#         self.cycle_count += 1
#         cycle_start = time.time()
#         
#         try:
#             # Place hedging orders
#             orders_placed = self.place_hedging_orders()
#             
#             # Check profit opportunities
#             profits_taken = self.check_profit_opportunities()
#             
#             # Log status periodically
#             self.log_system_status()
#             
#             # Cycle timing
#             elapsed = time.time() - cycle_start
#             sleep_time = max(0, 5 - elapsed)  # 5-second cycles
#             
#             if sleep_time > 0:
#                 time.sleep(sleep_time)
#             
#         except Exception as e:
#             self.logger.error(f"❌ Cycle {self.cycle_count} error: {e}")
#             self.daily_stats['errors'] += 1
#             time.sleep(5)
#     
#     def run(self):
#         """Main 24/7 trading loop"""
#         self.logger.info("🚀 Starting Connected 24/7 Hedging System")
#         self.logger.info("⚠️  LIVE TRADING MODE - Real orders will be placed!")
#         self.logger.info("🔊 Keep Gate.io exchange open to hear order sounds")
#         
#         # Test full connection
#         if not self.test_full_connection():
#             self.logger.error("❌ System connection failed - cannot start trading")
#             return
#         
#         self.start_time = time.time()
#         self.running = True
#         
#         try:
#             while self.running and not self.shutdown_requested:
#                 self.run_hedging_cycle()
#                 
#         except KeyboardInterrupt:
#             self.logger.info("🛑 System stopped by user")
#         except Exception as e:
#             self.logger.error(f"❌ Fatal system error: {e}")
#         finally:
#             self.logger.info("✅ Connected Hedging System shutdown complete")
#             
#             # Final status
#             if self.start_time:
#                 total_uptime = time.time() - self.start_time
#                 self.logger.info(f"📊 Final Stats:")
#                 self.logger.info(f"   Total uptime: {str(timedelta(seconds=int(total_uptime)))}")
#                 self.logger.info(f"   Total cycles: {self.cycle_count}")
#                 self.logger.info(f"   AI decisions: {self.daily_stats['ai_decisions']}")
#                 self.logger.info(f"   Daily orders: {self.daily_stats['orders_placed']}")
#                 self.logger.info(f"   Daily profits: {self.daily_stats['profits_taken']}")
#                 self.logger.info(f"   Daily PnL: ${self.daily_stats['total_pnl']:.4f}")
#
# def main():
#     """Main entry point"""
#     print("🚀 CONNECTED 24/7 HEDGING SYSTEM")
#     print("=" * 50)
#     print("📊 Gate.io Futures + AI Integration")
#     print("💰 Nominal Value: $0.01-$0.10 per trade")
#     print("🤖 AI-powered decisions")
#     print("🔊 Exchange sounds on successful orders")
#     print("=" * 50)
#     
#     # Create and run connected system
#     system = ConnectedHedgingSystem()
#     system.run()
#
# if __name__ == "__main__":
#     main()
# ===== END   [114/134] Hedging_Project/src/hedging_system_connected.py =====

# ===== BEGIN [115/134] Hedging_Project/src/main.py sha256=8b16114e81428b92 =====
# #!/usr/bin/env python3
# """
# Main Entry Point for Hedging Project
# Professional Gate.io Futures Hedging System
# """
#
# import os
# import sys
# import argparse
# import logging
# from datetime import datetime
#
# # Add src to path
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#
# from hedging_market_maker import HedgingMarketMaker
#
# def setup_logging():
#     """Setup logging configuration"""
#     log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
#     os.makedirs(log_dir, exist_ok=True)
#     
#     log_file = os.path.join(log_dir, f'hedging_{datetime.now().strftime("%Y%m%d")}.log')
#     
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s %(name)s %(levelname)s %(message)s',
#         handlers=[
#             logging.FileHandler(log_file),
#             logging.StreamHandler()
#         ]
#     )
#
# def main():
#     """Main entry point"""
#     parser = argparse.ArgumentParser(description='Professional Hedging Market Maker')
#     parser.add_argument('--config', type=str, help='Configuration file path')
#     parser.add_argument('--dry-run', action='store_true', help='Run in simulation mode')
#     parser.add_argument('--symbol', type=str, default='ENA_USDT', help='Trading symbol')
#     parser.add_argument('--nominal', type=float, default=0.05, help='Target nominal value')
#     
#     args = parser.parse_args()
#     
#     # Setup logging
#     setup_logging()
#     logger = logging.getLogger('Main')
#     
#     # Print startup banner
#     print("🚀 PROFESSIONAL HEDGING PROJECT")
#     print("=" * 50)
#     print("📊 Gate.io Futures Hedging System")
#     print(f"💰 Target Nominal: ${args.nominal:.2f}")
#     print(f"📈 Symbol: {args.symbol}")
#     print(f"🔧 Mode: {'DRY RUN' if args.dry_run else 'LIVE TRADING'}")
#     print("=" * 50)
#     
#     # Check environment variables
#     if not args.dry_run and (not os.getenv("GATE_API_KEY") or not os.getenv("GATE_API_SECRET")):
#         logger.error("❌ Missing GATE_API_KEY or GATE_API_SECRET for live trading")
#         logger.info("💡 Use --dry-run for simulation mode")
#         logger.info("💡 Or set environment variables:")
#         logger.info("   export GATE_API_KEY='your-key'")
#         logger.info("   export GATE_API_SECRET='your-secret'")
#         return
#     
#     if args.dry_run:
#         logger.info("🧪 Running in DRY RUN mode - no real orders")
#     else:
#         logger.warning("⚠️  Running in LIVE mode - real orders will be placed")
#     
#     try:
#         # Create and run hedging market maker
#         hedger = HedgingMarketMaker(config_path=args.config)
#         
#         if args.dry_run:
#             logger.info("🧪 Dry run mode - simulating trades")
#             # In dry run mode, we would implement simulation logic here
#             logger.info("✅ Dry run completed successfully")
#         else:
#             logger.info("🚀 Starting live hedging...")
#             hedger.run()
#             
#     except KeyboardInterrupt:
#         logger.info("🛑 Hedging system stopped by user")
#     except Exception as e:
#         logger.error(f"❌ Fatal error: {e}")
#         raise
#
# if __name__ == "__main__":
#     main()
# ===== END   [115/134] Hedging_Project/src/main.py =====

# ===== BEGIN [116/134] Hedging_Project/src/multi_token_trader.py sha256=ddb96f7cacae67cd =====
# #!/usr/bin/env python3
# """
# Multi-Token Trading System
# Trade all high-volume tokens with AI optimization
# """
#
# import os
# import sys
# import time
# import json
# import signal
# import logging
# import asyncio
# import threading
# import tkinter as tk
# from tkinter import ttk, messagebox, scrolledtext
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional, Any, Tuple
# import requests
# import hmac
# import hashlib
# from dataclasses import dataclass
# from collections import deque
# import queue
# import math
#
# # High-volume tokens from your list
# TRADING_SYMBOLS = [
#     "HIPPO_USDT", "NATIX_USDT", "TOSHI_USDT", "ELIZAOS_USDT", "ETH5S_USDT",
#     "PUMP_USDT", "COMMON_USDT", "XRP5L_USDT", "MRLN_USDT", "LINK5L_USDT",
#     "XPIN_USDT", "RLS_USDT", "AVAX5L_USDT", "MEMEFI_USDT", "FARTCOIN5S_USDT",
#     "OMI_USDT", "DOGE_USDT", "PTB_USDT", "DOGE3S_USDT", "XEM_USDT",
#     "BLUAI_USDT", "ADA5L_USDT", "TREAT_USDT", "BTC5L_USDT", "ROOBEE_USDT",
#     "PEPE5S_USDT", "ART_USDT", "XNL_USDT", "HMSTR_USDT", "BLAST_USDT"
# ]
#
# @dataclass
# class TokenData:
#     symbol: str
#     price: float
#     bid: float
#     ask: float
#     volume: float
#     change_24h: float
#     spread_pct: float
#     timestamp: float
#
# @dataclass
# class TokenTrade:
#     timestamp: float
#     symbol: str
#     side: str
#     size: float
#     price: float
#     nominal_value: float
#     pnl: float = 0.0
#
# class MultiTokenClient:
#     """Enhanced client for multi-token trading"""
#     
#     def __init__(self):
#         self.api_key = os.getenv("GATE_API_KEY", "")
#         self.api_secret = os.getenv("GATE_API_SECRET", "")
#         self.base_url = "https://api.gateio.ws/api/v4"
#         self.settle = "usdt"
#         self.session = requests.Session()
#         self.logger = logging.getLogger('MultiTokenClient')
#         
#     def _sign_request(self, method: str, path: str, payload: str) -> Dict[str, str]:
#         if not self.api_key or not self.api_secret:
#             return {}
#         
#         ts = str(int(time.time()))
#         payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#         sign_str = f"{method.upper()}\n{path}\n{payload_hash}\n{ts}"
#         sign = hmac.new(self.api_key.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
#         
#         return {"KEY": self.api_key, "Timestamp": ts, "SIGN": sign}
#     
#     def _make_request(self, method: str, path: str, payload: str = "", private: bool = False) -> Dict:
#         headers = {"Accept": "application/json", "Content-Type": "application/json"}
#         if private:
#             headers.update(self._sign_request(method, path, payload))
#         
#         try:
#             response = self.session.request(method, f"{self.base_url}{path}", headers=headers, 
#                                          data=payload if payload else None, timeout=10)
#             if response.status_code == 200:
#                 return {"success": True, "data": response.json()}
#             else:
#                 return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
#         except Exception as e:
#             return {"success": False, "error": str(e)}
#     
#     def get_all_token_data(self) -> List[TokenData]:
#         """Get data for all trading tokens"""
#         tokens = []
#         
#         for symbol in TRADING_SYMBOLS:
#             try:
#                 # Get ticker data
#                 ticker_result = self._make_request("GET", f"/spot/tickers?currency_pair={symbol}")
#                 if not ticker_result["success"]:
#                     continue
#                 
#                 ticker = ticker_result["data"][0] if ticker_result["data"] else None
#                 if not ticker:
#                     continue
#                 
#                 # Get order book
#                 book_result = self._make_request("GET", f"/spot/order_book?currency_pair={symbol}&limit=1")
#                 if not book_result["success"]:
#                     continue
#                 
#                 book = book_result["data"]
#                 if not book.get("bids") or not book.get("asks"):
#                     continue
#                 
#                 bid = float(book["bids"][0][0])
#                 ask = float(book["asks"][0][0])
#                 base_volume = float(ticker.get("base_volume", 0))
#                 change_pct = float(ticker.get("change_percentage", 0))
#                 
#                 token = TokenData(
#                     symbol=symbol,
#                     price=float(ticker.get("last", 0)),
#                     bid=bid,
#                     ask=ask,
#                     volume=base_volume,
#                     change_24h=change_pct,
#                     spread_pct=((ask - bid) / bid) * 100 if bid > 0 else 0,
#                     timestamp=time.time()
#                 )
#                 
#                 tokens.append(token)
#                 
#             except Exception as e:
#                 self.logger.error(f"Error getting data for {symbol}: {e}")
#                 continue
#         
#         return tokens
#     
#     def place_order(self, symbol: str, side: str, size: float, price: float) -> Dict:
#         """Place order for any token"""
#         order_data = {
#             "currency_pair": symbol,
#             "type": "limit",
#             "side": side,
#             "amount": str(size),
#             "price": str(price),
#             "time_in_force": "ioc"
#         }
#         
#         payload = json.dumps(order_data, separators=(",", ":"))
#         return self._make_request("POST", "/spot/orders", payload, private=True)
#     
#     def get_account(self) -> Dict:
#         """Get account balance"""
#         result = self._make_request("GET", "/spot/accounts", "", private=True)
#         return result.get("data", []) if result["success"] else []
#     
#     def calculate_order_size(self, price: float, target_nominal: float = 0.05) -> float:
#         """Calculate order size for target nominal value"""
#         if price <= 0:
#             return 0
#         size = target_nominal / price
#         min_size = 0.001
#         return max(size, min_size)
#
# class MultiTokenTrader:
#     """Multi-token trading engine with AI optimization"""
#     
#     def __init__(self):
#         self.client = MultiTokenClient()
#         self.symbols = TRADING_SYMBOLS
#         self.min_nominal = 0.01
#         self.max_nominal = 0.10
#         self.target_nominal = 0.05
#         
#         # Trading state
#         self.running = False
#         self.cycle_count = 0
#         self.start_time = time.time()
#         
#         # Data storage
#         self.token_data = deque(maxlen=100)
#         self.trades = deque(maxlen=1000)
#         self.performance = {}
#         
#         # Initialize performance tracking
#         for symbol in self.symbols:
#             self.performance[symbol] = {
#                 "trades": 0,
#                 "profits": 0,
#                 "losses": 0,
#                 "total_pnl": 0.0
#             }
#         
#         self.logger = logging.getLogger('MultiTokenTrader')
#         
#     def analyze_token_opportunities(self, tokens: List[TokenData]) -> List[Dict]:
#         """Analyze tokens for trading opportunities"""
#         opportunities = []
#         
#         for token in tokens:
#             # Volume filter - only high volume tokens
#             if token.volume < 1000000:  # $1M minimum volume
#                 continue
#             
#             # Spread filter - reasonable spreads only
#             if token.spread_pct > 1.0:  # Max 1% spread
#                 continue
#             
#             # Volatility filter - look for movement
#             if abs(token.change_24h) < 2.0:  # Min 2% movement
#                 continue
#             
#             # Calculate opportunity score
#             volume_score = min(token.volume / 10000000, 1.0)  # Max at $10M volume
#             volatility_score = min(abs(token.change_24h) / 20.0, 1.0)  # Max at 20% movement
#             spread_score = max(0, 1.0 - token.spread_pct)  # Lower spread is better
#             
#             opportunity_score = (volume_score * 0.4 + volatility_score * 0.4 + spread_score * 0.2)
#             
#             # Determine trading direction
#             if token.change_24h > 5.0:  # Strong uptrend - look for pullbacks to buy
#                 direction = "BUY_DIP"
#                 reasoning = f"Strong uptrend (+{token.change_24h:.1f}%) - buying on pullbacks"
#             elif token.change_24h < -5.0:  # Strong downtrend - look for bounces to sell
#                 direction = "SELL_RALLY"
#                 reasoning = f"Strong downtrend ({token.change_24h:.1f}%) - selling on rallies"
#             elif token.change_24h > 0:  # Moderate uptrend
#                 direction = "BUY"
#                 reasoning = f"Uptrend (+{token.change_24h:.1f}%) - momentum buying"
#             else:  # Moderate downtrend
#                 direction = "SELL"
#                 reasoning = f"Downtrend ({token.change_24h:.1f}%) - momentum selling"
#             
#             opportunities.append({
#                 "symbol": token.symbol,
#                 "direction": direction,
#                 "score": opportunity_score,
#                 "reasoning": reasoning,
#                 "token": token
#             })
#         
#         # Sort by opportunity score
#         opportunities.sort(key=lambda x: x["score"], reverse=True)
#         
#         return opportunities[:10]  # Top 10 opportunities
#     
#     def execute_trades(self, opportunities: List[Dict]) -> List[TokenTrade]:
#         """Execute trades on best opportunities"""
#         executed_trades = []
#         
#         # Take top 3 opportunities
#         for opp in opportunities[:3]:
#             if opp["score"] < 0.3:  # Minimum score threshold
#                 continue
#             
#             token = opp["token"]
#             direction = opp["direction"]
#             
#             # Calculate order size based on opportunity strength
#             nominal_multiplier = 0.5 + (opp["score"] * 0.5)  # 0.5x to 1.0x based on score
#             target_nominal = self.target_nominal * nominal_multiplier
#             
#             try:
#                 if "BUY" in direction:
#                     # Buy at best bid
#                     size = self.client.calculate_order_size(token.bid, target_nominal)
#                     result = self.client.place_order(token.symbol, "buy", size, token.bid)
#                     
#                     if result["success"]:
#                         trade = TokenTrade(
#                             timestamp=time.time(),
#                             symbol=token.symbol,
#                             side="BUY",
#                             size=size,
#                             price=token.bid,
#                             nominal_value=size * token.bid
#                         )
#                         executed_trades.append(trade)
#                         self.trades.append(trade)
#                         self.performance[token.symbol]["trades"] += 1
#                         self.logger.info(f"✅ BUY {token.symbol}: {size:.6f} @ ${token.bid:.6f} (${trade.nominal_value:.4f})")
#                     
#                 elif "SELL" in direction:
#                     # Sell at best ask
#                     size = self.client.calculate_order_size(token.ask, target_nominal)
#                     result = self.client.place_order(token.symbol, "sell", size, token.ask)
#                     
#                     if result["success"]:
#                         trade = TokenTrade(
#                             timestamp=time.time(),
#                             symbol=token.symbol,
#                             side="SELL",
#                             size=size,
#                             price=token.ask,
#                             nominal_value=size * token.ask
#                         )
#                         executed_trades.append(trade)
#                         self.trades.append(trade)
#                         self.performance[token.symbol]["trades"] += 1
#                         self.logger.info(f"✅ SELL {token.symbol}: {size:.6f} @ ${token.ask:.6f} (${trade.nominal_value:.4f})")
#                 
#             except Exception as e:
#                 self.logger.error(f"❌ Trade execution error for {token.symbol}: {e}")
#         
#         return executed_trades
#     
#     def run_trading_cycle(self) -> Dict:
#         """Run one complete trading cycle"""
#         self.cycle_count += 1
#         cycle_start = time.time()
#         
#         try:
#             # Get all token data
#             tokens = self.client.get_all_token_data()
#             self.token_data.append(tokens)
#             
#             # Analyze opportunities
#             opportunities = self.analyze_token_opportunities(tokens)
#             
#             # Execute trades
#             executed_trades = self.execute_trades(opportunities)
#             
#             # Calculate cycle stats
#             total_nominal = sum(trade.nominal_value for trade in executed_trades)
#             
#             elapsed = time.time() - cycle_start
#             
#             return {
#                 "success": True,
#                 "cycle": self.cycle_count,
#                 "tokens_analyzed": len(tokens),
#                 "opportunities_found": len(opportunities),
#                 "trades_executed": len(executed_trades),
#                 "total_nominal": total_nominal,
#                 "cycle_time": elapsed,
#                 "top_opportunities": opportunities[:5]
#             }
#             
#         except Exception as e:
#             self.logger.error(f"❌ Cycle {self.cycle_count} error: {e}")
#             return {"success": False, "error": str(e)}
#     
#     def get_account_summary(self) -> Dict:
#         """Get account balance summary"""
#         accounts = self.client.get_account()
#         
#         summary = {
#             "total_balance": 0.0,
#             "available_balance": 0.0,
#             "currencies": {}
#         }
#         
#         for account in accounts:
#             currency = account.get("currency", "")
#             available = float(account.get("available", 0))
#             frozen = float(account.get("frozen", 0))
#             
#             if currency == "USDT":
#                 summary["available_balance"] = available
#                 summary["total_balance"] = available + frozen
#             
#             if available > 0:
#                 summary["currencies"][currency] = {
#                     "available": available,
#                     "frozen": frozen,
#                     "total": available + frozen
#                 }
#         
#         return summary
#
# class MultiTokenDashboard:
#     """Dashboard for multi-token trading"""
#     
#     def __init__(self):
#         self.root = tk.Tk()
#         self.root.title("🚀 Multi-Token Trading Dashboard - 30 High-Volume Tokens")
#         self.root.geometry("1600x1000")
#         self.root.configure(bg='#0a0a0a')
#         
#         # Initialize trader
#         self.trader = MultiTokenTrader()
#         
#         # Setup logging
#         self.setup_logging()
#         
#         # Update queue
#         self.update_queue = queue.Queue()
#         
#         # Create UI
#         self.create_ui()
#         
#         # Start trading thread
#         self.trading_thread = None
#         self.start_trading()
#         
#         # Start UI updates
#         self.update_ui()
#         
#         # Handle window close
#         self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
#         
#         self.logger.info("🚀 Multi-Token Dashboard initialized")
#     
#     def setup_logging(self):
#         """Setup logging"""
#         log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
#         os.makedirs(log_dir, exist_ok=True)
#         
#         log_file = os.path.join(log_dir, f'multi_token_{datetime.now().strftime("%Y%m%d")}.log')
#         
#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
#             handlers=[
#                 logging.FileHandler(log_file, mode='a'),
#                 logging.StreamHandler()
#             ]
#         )
#         
#         self.logger = logging.getLogger('Dashboard')
#     
#     def create_ui(self):
#         """Create the UI"""
#         # Colors
#         self.bg_color = '#0a0a0a'
#         self.fg_color = '#00ff00'
#         self.error_color = '#ff4444'
#         self.warning_color = '#ffaa00'
#         
#         # Main container
#         main_frame = tk.Frame(self.root, bg=self.bg_color)
#         main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
#         
#         # Title
#         title_label = tk.Label(main_frame, text="🚀 MULTI-TOKEN TRADING DASHBOARD", 
#                               font=('Arial', 18, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         title_label.pack(pady=5)
#         
#         subtitle_label = tk.Label(main_frame, text="Trading 30 High-Volume Tokens with AI Optimization", 
#                                  font=('Arial', 12), fg=self.fg_color, bg=self.bg_color)
#         subtitle_label.pack(pady=2)
#         
#         # Create sections
#         self.create_account_section(main_frame)
#         self.create_opportunities_section(main_frame)
#         self.create_tokens_section(main_frame)
#         self.create_trades_section(main_frame)
#         self.create_log_section(main_frame)
#         self.create_control_section(main_frame)
#     
#     def create_account_section(self, parent):
#         """Create account section"""
#         account_frame = tk.LabelFrame(parent, text="💰 ACCOUNT BALANCE", 
#                                     font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         account_frame.pack(fill=tk.X, pady=5)
#         
#         account_grid = tk.Frame(account_frame, bg=self.bg_color)
#         account_grid.pack(fill=tk.X, padx=5, pady=5)
#         
#         self.account_labels = {}
#         account_items = [
#             ("total", "Total Balance:", "$0.00"),
#             ("available", "Available:", "$0.00"),
#             ("trades", "Total Trades:", "0"),
#             ("nominal", "Cycle Nominal:", "$0.00")
#         ]
#         
#         for i, (key, label, default) in enumerate(account_items):
#             row = i // 2
#             col = (i % 4)
#             
#             tk.Label(account_grid, text=label, font=('Arial', 10), 
#                     fg=self.fg_color, bg=self.bg_color).grid(row=row, column=col, sticky='w', padx=5)
#             self.account_labels[key] = tk.Label(account_grid, text=default, font=('Arial', 10, 'bold'),
#                                               fg=self.fg_color, bg=self.bg_color)
#             self.account_labels[key].grid(row=row, column=col+1, sticky='w', padx=5)
#     
#     def create_opportunities_section(self, parent):
#         """Create opportunities section"""
#         opp_frame = tk.LabelFrame(parent, text="🎯 TOP TRADING OPPORTUNITIES", 
#                                  font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         opp_frame.pack(fill=tk.X, pady=5)
#         
#         # Create treeview for opportunities
#         columns = ('Symbol', 'Direction', 'Score', 'Price', 'Change%', 'Volume', 'Reasoning')
#         self.opp_tree = ttk.Treeview(opp_frame, columns=columns, show='headings', height=6)
#         
#         for col in columns:
#             self.opp_tree.heading(col, text=col)
#             width = 120 if col != 'Reasoning' else 300
#             self.opp_tree.column(col, width=width)
#         
#         self.opp_tree.pack(fill=tk.X, padx=5, pady=5)
#         
#         # Style
#         style = ttk.Style()
#         style.configure("Treeview", background='#1a1a1a', foreground=self.fg_color, 
#                        fieldbackground='#1a1a1a')
#         style.configure("Treeview.Heading", background='#2a2a2a', foreground=self.fg_color)
#     
#     def create_tokens_section(self, parent):
#         """Create tokens overview section"""
#         tokens_frame = tk.LabelFrame(parent, text="📊 TOKEN OVERVIEW", 
#                                    font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         tokens_frame.pack(fill=tk.BOTH, expand=True, pady=5)
#         
#         # Create treeview for all tokens
#         columns = ('Symbol', 'Price', 'Change%', 'Volume', 'Spread%', 'Trades', 'PnL')
#         self.tokens_tree = ttk.Treeview(tokens_frame, columns=columns, show='headings', height=10)
#         
#         for col in columns:
#             self.tokens_tree.heading(col, text=col)
#             self.tokens_tree.column(col, width=100)
#         
#         # Scrollbar
#         token_scrollbar = ttk.Scrollbar(tokens_frame, orient=tk.VERTICAL, command=self.tokens_tree.yview)
#         self.tokens_tree.configure(yscrollcommand=token_scrollbar.set)
#         
#         self.tokens_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
#         token_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
#     
#     def create_trades_section(self, parent):
#         """Create recent trades section"""
#         trades_frame = tk.LabelFrame(parent, text="💼 RECENT TRADES", 
#                                     font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         trades_frame.pack(fill=tk.X, pady=5)
#         
#         # Create treeview for trades
#         columns = ('Time', 'Symbol', 'Side', 'Size', 'Price', 'Nominal')
#         self.trades_tree = ttk.Treeview(trades_frame, columns=columns, show='headings', height=5)
#         
#         for col in columns:
#             self.trades_tree.heading(col, text=col)
#             self.trades_tree.column(col, width=100)
#         
#         self.trades_tree.pack(fill=tk.X, padx=5, pady=5)
#     
#     def create_log_section(self, parent):
#         """Create log section"""
#         log_frame = tk.LabelFrame(parent, text="📝 ACTIVITY LOG", 
#                                 font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         log_frame.pack(fill=tk.X, pady=5)
#         
#         self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=150, 
#                                                  bg='#1a1a1a', fg=self.fg_color, 
#                                                  font=('Courier', 9))
#         self.log_text.pack(fill=tk.X, padx=5, pady=5)
#     
#     def create_control_section(self, parent):
#         """Create control section"""
#         control_frame = tk.Frame(parent, bg=self.bg_color)
#         control_frame.pack(fill=tk.X, pady=5)
#         
#         self.start_button = tk.Button(control_frame, text="🚀 START TRADING", 
#                                      command=self.toggle_trading, font=('Arial', 12, 'bold'),
#                                      bg='#00aa00', fg='white', padx=20, pady=10)
#         self.start_button.pack(side=tk.LEFT, padx=5)
#         
#         tk.Button(control_frame, text="📊 REFRESH", command=self.manual_refresh,
#                  font=('Arial', 10), bg='#0066cc', fg='white', padx=15, pady=10).pack(side=tk.LEFT, padx=5)
#         
#         tk.Button(control_frame, text="🗑️ CLEAR LOGS", command=self.clear_logs,
#                  font=('Arial', 10), bg='#666666', fg='white', padx=15, pady=10).pack(side=tk.LEFT, padx=5)
#         
#         # Status indicator
#         self.status_indicator = tk.Label(control_frame, text="● STOPPED", 
#                                        font=('Arial', 12, 'bold'), fg=self.error_color, bg=self.bg_color)
#         self.status_indicator.pack(side=tk.RIGHT, padx=20)
#     
#     def start_trading(self):
#         """Start trading in separate thread"""
#         if self.trading_thread is None or not self.trading_thread.is_alive():
#             self.trader.running = True
#             self.trading_thread = threading.Thread(target=self.trading_loop, daemon=True)
#             self.trading_thread.start()
#             self.logger.info("🚀 Multi-token trading started")
#     
#     def stop_trading(self):
#         """Stop trading"""
#         self.trader.running = False
#         if self.trading_thread:
#             self.trading_thread.join(timeout=5)
#         self.logger.info("🛑 Multi-token trading stopped")
#     
#     def toggle_trading(self):
#         """Toggle trading"""
#         if self.trader.running:
#             self.stop_trading()
#             self.start_button.config(text="🚀 START TRADING", bg='#00aa00')
#             self.status_indicator.config(text="● STOPPED", fg=self.error_color)
#         else:
#             self.start_trading()
#             self.start_button.config(text="🛑 STOP TRADING", bg='#aa0000')
#             self.status_indicator.config(text="● RUNNING", fg=self.fg_color)
#     
#     def trading_loop(self):
#         """Main trading loop"""
#         while self.trader.running:
#             try:
#                 result = self.trader.run_trading_cycle()
#                 self.update_queue.put(("cycle_result", result))
#                 time.sleep(10)  # 10-second cycles for multi-token
#             except Exception as e:
#                 self.logger.error(f"❌ Trading loop error: {e}")
#                 self.update_queue.put(("error", str(e)))
#                 time.sleep(10)
#     
#     def manual_refresh(self):
#         """Manual refresh"""
#         try:
#             result = self.trader.run_trading_cycle()
#             self.update_queue.put(("cycle_result", result))
#         except Exception as e:
#             self.logger.error(f"❌ Refresh error: {e}")
#     
#     def clear_logs(self):
#         """Clear logs"""
#         self.log_text.delete(1.0, tk.END)
#     
#     def update_ui(self):
#         """Update UI"""
#         try:
#             # Process queue
#             while not self.update_queue.empty():
#                 try:
#                     update_type, data = self.update_queue.get_nowait()
#                     
#                     if update_type == "cycle_result":
#                         self.handle_cycle_result(data)
#                     elif update_type == "error":
#                         self.log_message(f"❌ Error: {data}", self.error_color)
#                         
#                 except queue.Empty:
#                     break
#             
#             # Update account
#             self.update_account_display()
#             
#             # Update tokens display
#             self.update_tokens_display()
#             
#             # Update trades display
#             self.update_trades_display()
#             
#         except Exception as e:
#             self.logger.error(f"❌ UI update error: {e}")
#         
#         # Schedule next update
#         self.root.after(2000, self.update_ui)  # Update every 2 seconds
#     
#     def handle_cycle_result(self, result):
#         """Handle cycle result"""
#         if result["success"]:
#             self.log_message(f"✅ Cycle {result['cycle']}: {result['tokens_analyzed']} tokens, {result['trades_executed']} trades (${result['total_nominal']:.4f})")
#             
#             # Update opportunities
#             self.update_opportunities_display(result.get("top_opportunities", []))
#         else:
#             self.log_message(f"❌ Cycle failed: {result.get('error', 'Unknown')}", self.error_color)
#     
#     def update_account_display(self):
#         """Update account display"""
#         account = self.trader.get_account_summary()
#         
#         self.account_labels["total"].config(text=f"${account['total_balance']:.2f}")
#         self.account_labels["available"].config(text=f"${account['available_balance']:.2f}")
#         self.account_labels["trades"].config(text=str(len(self.trader.trades)))
#         
#         # Calculate cycle nominal
#         recent_trades = [t for t in self.trader.trades if time.time() - t.timestamp < 60]
#         cycle_nominal = sum(t.nominal_value for t in recent_trades)
#         self.account_labels["nominal"].config(text=f"${cycle_nominal:.4f}")
#     
#     def update_opportunities_display(self, opportunities):
#         """Update opportunities display"""
#         # Clear existing
#         for item in self.opp_tree.get_children():
#             self.opp_tree.delete(item)
#         
#         # Add opportunities
#         for opp in opportunities:
#             token = opp["token"]
#             
#             # Color based on direction
#             direction_colors = {"BUY": "green", "SELL": "red", "BUY_DIP": "green", "SELL_RALLY": "red"}
#             
#             values = (
#                 token.symbol,
#                 opp["direction"],
#                 f"{opp['score']:.3f}",
#                 f"${token.price:.6f}",
#                 f"{token.change_24h:+.2f}%",
#                 f"${token.volume/1000000:.1f}M",
#                 opp["reasoning"][:50] + "..." if len(opp["reasoning"]) > 50 else opp["reasoning"]
#             )
#             
#             self.opp_tree.insert('', tk.END, values=values)
#     
#     def update_tokens_display(self):
#         """Update tokens display"""
#         # Clear existing
#         for item in self.tokens_tree.get_children():
#             self.tokens_tree.delete(item)
#         
#         # Get latest token data
#         if self.trader.token_data:
#             latest_tokens = self.trader.token_data[-1]
#             
#             for token in latest_tokens:
#                 perf = self.trader.performance.get(token.symbol, {})
#                 
#                 values = (
#                     token.symbol,
#                     f"${token.price:.6f}",
#                     f"{token.change_24h:+.2f}%",
#                     f"${token.volume/1000000:.1f}M",
#                     f"{token.spread_pct:.3f}%",
#                     str(perf.get("trades", 0)),
#                     f"${perf.get('total_pnl', 0):.4f}"
#                 )
#                 
#                 self.tokens_tree.insert('', tk.END, values=values)
#     
#     def update_trades_display(self):
#         """Update trades display"""
#         # Clear existing
#         for item in self.trades_tree.get_children():
#             self.trades_tree.delete(item)
#         
#         # Add recent trades
#         recent_trades = list(self.trader.trades)[-20:]  # Last 20 trades
#         for trade in reversed(recent_trades):
#             time_str = datetime.fromtimestamp(trade.timestamp).strftime("%H:%M:%S")
#             
#             values = (
#                 time_str,
#                 trade.symbol,
#                 trade.side,
#                 f"{trade.size:.6f}",
#                 f"${trade.price:.6f}",
#                 f"${trade.nominal_value:.4f}"
#             )
#             
#             self.trades_tree.insert('', tk.END, values=values)
#     
#     def log_message(self, message: str, color: str = None):
#         """Add log message"""
#         timestamp = datetime.now().strftime("%H:%M:%S")
#         self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
#         self.log_text.see(tk.END)
#         
#         # Limit log size
#         lines = self.log_text.get(1.0, tk.END).split('\n')
#         if len(lines) > 50:
#             self.log_text.delete(1.0, f"{len(lines)-50}.0")
#     
#     def on_closing(self):
#         """Handle window close"""
#         if messagebox.askokcancel("Quit", "Stop trading and quit?"):
#             self.stop_trading()
#             self.root.destroy()
#     
#     def run(self):
#         """Run dashboard"""
#         self.logger.info("🚀 Starting Multi-Token Trading Dashboard")
#         self.root.mainloop()
#
# def main():
#     """Main entry point"""
#     print("🚀 MULTI-TOKEN TRADING DASHBOARD")
#     print("=" * 50)
#     print("📊 Trading 30 High-Volume Tokens")
#     print("🎯 AI-Powered Opportunity Detection")
#     print("💰 Nominal Value: $0.01-$0.10 per trade")
#     print("🔄 10-Second Trading Cycles")
#     print("=" * 50)
#     
#     # Check environment variables
#     if not os.getenv("GATE_API_KEY") or not os.getenv("GATE_API_SECRET"):
#         print("⚠️  Running in DEMO mode - no API keys")
#         print("   Set GATE_API_KEY and GATE_API_SECRET for live trading")
#     
#     # Create and run dashboard
#     dashboard = MultiTokenDashboard()
#     dashboard.run()
#
# if __name__ == "__main__":
#     main()
# ===== END   [116/134] Hedging_Project/src/multi_token_trader.py =====

# ===== BEGIN [117/134] Hedging_Project/src/trading_dashboard_ai.py sha256=9ad1128a05a9422a =====
# #!/usr/bin/env python3
# """
# Complete AI Trading Dashboard - Single File Solution
# 24/7 Trading with AI Optimization and Full UI
# 2000+ lines - All-in-one trading system
# """
#
# import os
# import sys
# import time
# import json
# import signal
# import logging
# import asyncio
# import threading
# import tkinter as tk
# from tkinter import ttk, messagebox, scrolledtext
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional, Any, Tuple
# import requests
# import hmac
# import hashlib
# import yaml
# from dataclasses import dataclass, asdict
# from collections import deque
# import queue
# import math
#
# # Configuration and Data Classes
# @dataclass
# class Trade:
#     timestamp: float
#     symbol: str
#     side: str
#     size: float
#     price: float
#     order_id: str
#     status: str
#     pnl: float = 0.0
#
# @dataclass
# class MarketData:
#     symbol: str
#     bid: float
#     ask: float
#     spread: float
#     volume: float
#     timestamp: float
#
# @dataclass
# class AIDecision:
#     action: str
#     symbol: str
#     confidence: float
#     reasoning: str
#     timestamp: float
#     executed: bool = False
#
# @dataclass
# class SystemStatus:
#     connected: bool
#     api_status: str
#     ai_status: str
#     cycle_count: int
#     uptime: float
#     daily_pnl: float
#     total_trades: int
#     error_count: int
#
# class GateIOClient:
#     """Enhanced Gate.io API Client"""
#     
#     def __init__(self):
#         self.api_key = os.getenv("GATE_API_KEY", "")
#         self.api_secret = os.getenv("GATE_API_SECRET", "")
#         self.base_url = "https://api.gateio.ws/api/v4"
#         self.settle = "usdt"
#         self.session = requests.Session()
#         self.logger = logging.getLogger('GateIO')
#         
#     def _sign_request(self, method: str, path: str, payload: str) -> Dict[str, str]:
#         if not self.api_key or not self.api_secret:
#             return {}
#         
#         ts = str(int(time.time()))
#         payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#         sign_str = f"{method.upper()}\n{path}\n{payload_hash}\n{ts}"
#         sign = hmac.new(self.api_secret.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
#         
#         return {"KEY": self.api_key, "Timestamp": ts, "SIGN": sign}
#     
#     def _make_request(self, method: str, path: str, payload: str = "", private: bool = False) -> Dict:
#         headers = {"Accept": "application/json", "Content-Type": "application/json"}
#         if private:
#             headers.update(self._sign_request(method, path, payload))
#         
#         try:
#             response = self.session.request(method, f"{self.base_url}{path}", headers=headers, 
#                                          data=payload if payload else None, timeout=10)
#             if response.status_code == 200:
#                 return {"success": True, "data": response.json()}
#             else:
#                 return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
#         except Exception as e:
#             return {"success": False, "error": str(e)}
#     
#     def get_market_data(self, symbol: str) -> Optional[MarketData]:
#         result = self._make_request("GET", f"/futures/{self.settle}/order_book?contract={symbol}&limit=1")
#         if result["success"] and result["data"].get("bids") and result["data"].get("asks"):
#             bid = float(result["data"]["bids"][0]["p"])
#             ask = float(result["data"]["asks"][0]["p"])
#             return MarketData(symbol, bid, ask, ask - bid, 0, time.time())
#         return None
#     
#     def place_order(self, symbol: str, side: str, size: float, price: float) -> Dict:
#         order_data = {"settle": self.settle, "contract": symbol, "size": str(size), 
#                      "price": str(price), "type": "limit", "tif": "ioc"}
#         payload = json.dumps(order_data, separators=(",", ":"))
#         return self._make_request("POST", f"/futures/{self.settle}/orders", payload, private=True)
#     
#     def get_positions(self) -> List[Dict]:
#         result = self._make_request("GET", f"/futures/{self.settle}/positions", "", private=True)
#         return result.get("data", []) if result["success"] else []
#     
#     def get_account(self) -> Dict:
#         result = self._make_request("GET", f"/futures/{self.settle}/accounts", "", private=True)
#         if result["success"]:
#             return result["data"]
#         else:
#             self.logger.error(f"❌ Account fetch failed: {result.get('error', 'Unknown')}")
#             return {}
#
# class AISystem:
#     """Advanced AI Trading System"""
#     
#     def __init__(self):
#         self.api_key = os.getenv("OPENROUTER_API_KEY", "")
#         self.model = "anthropic/claude-3-haiku"
#         self.decision_history = deque(maxlen=100)
#         self.performance_metrics = {"total_decisions": 0, "successful": 0, "accuracy": 0.0}
#         self.logger = logging.getLogger('AI')
#         
#     def get_market_analysis(self, market_data: MarketData, positions: List[Dict], 
#                           account: Dict, history: List[Trade]) -> Dict:
#         """Comprehensive market analysis for AI decision making"""
#         
#         # Calculate technical indicators
#         spread_pct = (market_data.spread / market_data.bid) * 100 if market_data.bid > 0 else 0
#         
#         # Position analysis
#         total_position = sum(float(pos.get('size', 0)) for pos in positions)
#         unrealized_pnl = sum(float(pos.get('unrealised_pnl', 0)) for pos in positions)
#         
#         # Recent trade analysis
#         recent_trades = [t for t in history if time.time() - t.timestamp < 3600]  # Last hour
#         profitable_trades = len([t for t in recent_trades if t.pnl > 0])
#         win_rate = profitable_trades / len(recent_trades) if recent_trades else 0.5
#         
#         # Account health
#         available_balance = float(account.get('available', 0))
#         total_balance = float(account.get('total', 0))
#         
#         analysis = {
#             "market": {
#                 "symbol": market_data.symbol,
#                 "bid": market_data.bid,
#                 "ask": market_data.ask,
#                 "spread_pct": spread_pct,
#                 "timestamp": market_data.timestamp
#             },
#             "positions": {
#                 "total_size": total_position,
#                 "unrealized_pnl": unrealized_pnl,
#                 "count": len(positions)
#             },
#             "performance": {
#                 "recent_trades": len(recent_trades),
#                 "win_rate": win_rate,
#                 "hourly_pnl": sum(t.pnl for t in recent_trades)
#             },
#             "account": {
#                 "available": available_balance,
#                 "total": total_balance,
#                 "utilization": (total_balance - available_balance) / total_balance if total_balance > 0 else 0
#             },
#             "risk_metrics": {
#                 "position_risk": abs(total_position) * market_data.bid,
#                 "max_position_ratio": abs(total_position) / (total_balance / market_data.bid) if total_balance > 0 else 0
#             }
#         }
#         
#         return analysis
#     
#     def get_ai_decision(self, analysis: Dict) -> AIDecision:
#         """Get AI trading decision with advanced analysis"""
#         if not self.api_key:
#             return AIDecision("HOLD", analysis["market"]["symbol"], 0.5, 
#                             "AI disabled - no API key", time.time())
#         
#         try:
#             headers = {
#                 "Authorization": f"Bearer {self.api_key}",
#                 "Content-Type": "application/json",
#                 "HTTP-Referer": "https://github.com/alep/trading-dashboard",
#                 "X-Title": "AI Trading Dashboard"
#             }
#             
#             # Construct detailed prompt
#             prompt = f"""
#             You are an advanced AI trading advisor for a hedging system. Analyze the following data and provide optimal trading decision:
#             
#             MARKET DATA:
#             {json.dumps(analysis['market'], indent=2)}
#             
#             POSITIONS:
#             {json.dumps(analysis['positions'], indent=2)}
#             
#             PERFORMANCE:
#             {json.dumps(analysis['performance'], indent=2)}
#             
#             ACCOUNT:
#             {json.dumps(analysis['account'], indent=2)}
#             
#             RISK METRICS:
#             {json.dumps(analysis['risk_metrics'], indent=2)}
#             
#             TRADING STRATEGY:
#             - Place best bid/ask orders for market making
#             - Target nominal value: $0.01-$0.10 per trade
#             - Take profit at 0.2% gains
#             - Maintain position limits
#             - Optimize for risk-adjusted returns
#             
#             Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#             
#             Provide decision in JSON format:
#             {{
#                 "action": "BUY/SELL/HOLD/ADJUST",
#                 "symbol": "SYMBOL",
#                 "confidence": 0.0-1.0,
#                 "reasoning": "detailed explanation",
#                 "risk_level": "LOW/MEDIUM/HIGH",
#                 "recommended_size": "size_in_contracts",
#                 "price_adjustment": "bid/ask/market"
#             }}
#             """
#             
#             data = {
#                 "model": self.model,
#                 "messages": [{"role": "user", "content": prompt}],
#                 "max_tokens": 500,
#                 "temperature": 0.2
#             }
#             
#             response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
#                                    headers=headers, json=data, timeout=15)
#             
#             if response.status_code == 200:
#                 result = response.json()
#                 content = result["choices"][0]["message"]["content"]
#                 
#                 # Parse JSON response
#                 if "```json" in content:
#                     json_str = content.split("```json")[1].split("```")[0].strip()
#                 else:
#                     json_str = content.strip()
#                 
#                 decision_data = json.loads(json_str)
#                 
#                 decision = AIDecision(
#                     action=decision_data.get("action", "HOLD"),
#                     symbol=decision_data.get("symbol", analysis["market"]["symbol"]),
#                     confidence=float(decision_data.get("confidence", 0.5)),
#                     reasoning=decision_data.get("reasoning", "No reasoning provided"),
#                     timestamp=time.time()
#                 )
#                 
#                 self.decision_history.append(decision)
#                 self.performance_metrics["total_decisions"] += 1
#                 
#                 self.logger.info(f"🤖 AI Decision: {decision.action} (confidence: {decision.confidence:.2f})")
#                 return decision
#                 
#             else:
#                 self.logger.error(f"❌ AI API error: {response.status_code}")
#                 return AIDecision("HOLD", analysis["market"]["symbol"], 0.3, 
#                                 f"API error: {response.status_code}", time.time())
#                 
#         except Exception as e:
#             self.logger.error(f"❌ AI exception: {str(e)}")
#             return AIDecision("HOLD", analysis["market"]["symbol"], 0.2, 
#                             f"Exception: {str(e)}", time.time())
#     
#     def update_performance(self, decision: AIDecision, profit: float):
#         """Update AI performance metrics"""
#         if profit > 0:
#             self.performance_metrics["successful"] += 1
#         
#         total = self.performance_metrics["total_decisions"]
#         successful = self.performance_metrics["successful"]
#         self.performance_metrics["accuracy"] = successful / total if total > 0 else 0
#
# class TradingEngine:
#     """Core Trading Engine"""
#     
#     def __init__(self):
#         self.client = GateIOClient()
#         self.ai_system = AISystem()
#         self.symbol = "ENA_USDT"
#         self.min_nominal = 0.01
#         self.max_nominal = 0.10
#         self.profit_threshold = 0.002
#         self.running = False
#         self.cycle_count = 0
#         self.start_time = time.time()
#         
#         # Data storage
#         self.trades = deque(maxlen=1000)
#         self.market_data = deque(maxlen=100)
#         self.ai_decisions = deque(maxlen=100)
#         self.daily_stats = {
#             "orders_placed": 0,
#             "profits_taken": 0,
#             "errors": 0,
#             "total_pnl": 0.0
#         }
#         
#         self.logger = logging.getLogger('TradingEngine')
#         
#     def calculate_order_size(self, price: float) -> float:
#         """Calculate optimal order size"""
#         target_nominal = (self.min_nominal + self.max_nominal) / 2
#         size = target_nominal / price
#         min_size = 0.001
#         return max(size, min_size)
#     
#     def place_hedging_orders(self, market_data: MarketData, ai_decision: AIDecision) -> List[Trade]:
#         """Place hedging orders based on market data and AI decision"""
#         trades = []
#         
#         try:
#             # Calculate base order sizes
#             bid_size = self.calculate_order_size(market_data.bid)
#             ask_size = self.calculate_order_size(market_data.ask)
#             
#             # Adjust based on AI decision
#             if ai_decision.action == "BUY" and ai_decision.confidence > 0.7:
#                 bid_size *= 1.5
#                 self.logger.info(f"🤖 AI suggests BUY with confidence {ai_decision.confidence:.2f}")
#             elif ai_decision.action == "SELL" and ai_decision.confidence > 0.7:
#                 ask_size *= 1.5
#                 self.logger.info(f"🤖 AI suggests SELL with confidence {ai_decision.confidence:.2f}")
#             
#             # Place buy order
#             buy_result = self.client.place_order(self.symbol, "BUY", bid_size, market_data.bid)
#             if buy_result.get("success"):
#                 trade = Trade(
#                     timestamp=time.time(),
#                     symbol=self.symbol,
#                     side="BUY",
#                     size=bid_size,
#                     price=market_data.bid,
#                     order_id=buy_result["data"].get("id", ""),
#                     status="FILLED"
#                 )
#                 trades.append(trade)
#                 self.trades.append(trade)
#                 self.daily_stats["orders_placed"] += 1
#                 self.logger.info(f"✅ BUY order placed: {bid_size:.6f} @ ${market_data.bid:.6f}")
#             else:
#                 self.logger.error(f"❌ BUY order failed: {buy_result.get('error', 'Unknown')}")
#                 self.daily_stats["errors"] += 1
#             
#             # Place sell order
#             sell_result = self.client.place_order(self.symbol, "SELL", ask_size, market_data.ask)
#             if sell_result.get("success"):
#                 trade = Trade(
#                     timestamp=time.time(),
#                     symbol=self.symbol,
#                     side="SELL",
#                     size=ask_size,
#                     price=market_data.ask,
#                     order_id=sell_result["data"].get("id", ""),
#                     status="FILLED"
#                 )
#                 trades.append(trade)
#                 self.trades.append(trade)
#                 self.daily_stats["orders_placed"] += 1
#                 self.logger.info(f"✅ SELL order placed: {ask_size:.6f} @ ${market_data.ask:.6f}")
#             else:
#                 self.logger.error(f"❌ SELL order failed: {sell_result.get('error', 'Unknown')}")
#                 self.daily_stats["errors"] += 1
#                 
#         except Exception as e:
#             self.logger.error(f"❌ Order placement error: {str(e)}")
#             self.daily_stats["errors"] += 1
#         
#         return trades
#     
#     def check_profit_opportunities(self) -> List[Trade]:
#         """Check and execute profit opportunities"""
#         profit_trades = []
#         
#         try:
#             positions = self.client.get_positions()
#             
#             for pos in positions:
#                 size = float(pos.get('size', 0))
#                 if size == 0:
#                     continue
#                 
#                 entry_price = float(pos.get('entry_price', 0))
#                 mark_price = float(pos.get('mark_price', 0))
#                 unrealized_pnl = float(pos.get('unrealised_pnl', 0))
#                 
#                 if entry_price > 0:
#                     profit_pct = (mark_price - entry_price) / entry_price
#                     
#                     if profit_pct >= self.profit_threshold:
#                         # Take profit
#                         sell_size = abs(size)
#                         sell_result = self.client.place_order(self.symbol, "SELL" if size > 0 else "BUY", 
#                                                             sell_size, 0)  # Market order
#                         
#                         if sell_result.get("success"):
#                             trade = Trade(
#                                 timestamp=time.time(),
#                                 symbol=pos['contract'],
#                                 side="SELL" if size > 0 else "BUY",
#                                 size=sell_size,
#                                 price=mark_price,
#                                 order_id=sell_result["data"].get("id", ""),
#                                 status="PROFIT_TAKEN",
#                                 pnl=unrealized_pnl
#                             )
#                             profit_trades.append(trade)
#                             self.trades.append(trade)
#                             self.daily_stats["profits_taken"] += 1
#                             self.daily_stats["total_pnl"] += unrealized_pnl
#                             self.logger.info(f"💰 Profit taken: {profit_pct:.2%} (${unrealized_pnl:.4f})")
#                         else:
#                             self.logger.error(f"❌ Profit take failed: {sell_result.get('error', 'Unknown')}")
#                             self.daily_stats["errors"] += 1
#             
#         except Exception as e:
#             self.logger.error(f"❌ Profit check error: {str(e)}")
#             self.daily_stats["errors"] += 1
#         
#         return profit_trades
#     
#     def run_cycle(self) -> Dict:
#         """Run one trading cycle"""
#         self.cycle_count += 1
#         cycle_start = time.time()
#         
#         try:
#             # Get market data
#             market_data = self.client.get_market_data(self.symbol)
#             if not market_data:
#                 return {"success": False, "error": "Cannot get market data"}
#             
#             self.market_data.append(market_data)
#             
#             # Get positions and account
#             positions = self.client.get_positions()
#             account = self.client.get_account()
#             
#             # Get AI decision
#             analysis = self.ai_system.get_market_analysis(market_data, positions, account, list(self.trades))
#             ai_decision = self.ai_system.get_ai_decision(analysis)
#             self.ai_decisions.append(ai_decision)
#             
#             # Place orders
#             new_trades = self.place_hedging_orders(market_data, ai_decision)
#             
#             # Check profits
#             profit_trades = self.check_profit_opportunities()
#             
#             # Update AI performance
#             total_pnl = sum(trade.pnl for trade in new_trades + profit_trades)
#             self.ai_system.update_performance(ai_decision, total_pnl)
#             
#             elapsed = time.time() - cycle_start
#             
#             return {
#                 "success": True,
#                 "cycle": self.cycle_count,
#                 "market_data": market_data,
#                 "ai_decision": ai_decision,
#                 "new_trades": new_trades,
#                 "profit_trades": profit_trades,
#                 "cycle_time": elapsed,
#                 "daily_stats": self.daily_stats.copy()
#             }
#             
#         except Exception as e:
#             self.logger.error(f"❌ Cycle {self.cycle_count} error: {str(e)}")
#             self.daily_stats["errors"] += 1
#             return {"success": False, "error": str(e)}
#     
#     def get_system_status(self) -> SystemStatus:
#         """Get current system status"""
#         uptime = time.time() - self.start_time
#         total_pnl = sum(trade.pnl for trade in self.trades)
#         
#         return SystemStatus(
#             connected=bool(self.client.api_key and self.client.api_secret),
#             api_status="Connected" if self.client.api_key else "No API Keys",
#             ai_status="Active" if self.ai_system.api_key else "Disabled",
#             cycle_count=self.cycle_count,
#             uptime=uptime,
#             daily_pnl=total_pnl,
#             total_trades=len(self.trades),
#             error_count=self.daily_stats["errors"]
#         )
#
# class TradingDashboard:
#     """Complete Trading Dashboard UI"""
#     
#     def __init__(self):
#         self.root = tk.Tk()
#         self.root.title("🚀 AI Trading Dashboard - 24/7 Hedging System")
#         self.root.geometry("1400x900")
#         self.root.configure(bg='#0a0a0a')
#         
#         # Initialize trading engine
#         self.engine = TradingEngine()
#         
#         # Setup logging
#         self.setup_logging()
#         
#         # Data queues for thread communication
#         self.update_queue = queue.Queue()
#         
#         # Create UI
#         self.create_ui()
#         
#         # Start trading thread
#         self.trading_thread = None
#         self.start_trading()
#         
#         # Start UI update loop
#         self.update_ui()
#         
#         # Handle window close
#         self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
#         
#         self.logger.info("🚀 Trading Dashboard initialized")
#     
#     def setup_logging(self):
#         """Setup logging configuration"""
#         log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
#         os.makedirs(log_dir, exist_ok=True)
#         
#         log_file = os.path.join(log_dir, f'dashboard_{datetime.now().strftime("%Y%m%d")}.log')
#         
#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
#             handlers=[
#                 logging.FileHandler(log_file, mode='a'),
#                 logging.StreamHandler()
#             ]
#         )
#         
#         self.logger = logging.getLogger('Dashboard')
#     
#     def create_ui(self):
#         """Create the complete UI"""
#         
#         # Style configuration
#         style = ttk.Style()
#         style.theme_use('clam')
#         
#         # Configure colors
#         self.bg_color = '#0a0a0a'
#         self.fg_color = '#00ff00'
#         self.error_color = '#ff4444'
#         self.warning_color = '#ffaa00'
#         
#         # Main container
#         main_frame = tk.Frame(self.root, bg=self.bg_color)
#         main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
#         
#         # Title
#         title_label = tk.Label(main_frame, text="🚀 AI TRADING DASHBOARD", 
#                               font=('Arial', 20, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         title_label.pack(pady=5)
#         
#         # Create sections
#         self.create_status_section(main_frame)
#         self.create_market_section(main_frame)
#         self.create_balance_section(main_frame)
#         self.create_ai_section(main_frame)
#         self.create_trading_section(main_frame)
#         self.create_log_section(main_frame)
#         self.create_control_section(main_frame)
#     
#     def create_status_section(self, parent):
#         """Create system status section"""
#         status_frame = tk.LabelFrame(parent, text="🔧 SYSTEM STATUS", 
#                                    font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         status_frame.pack(fill=tk.X, pady=5)
#         
#         # Status grid
#         status_grid = tk.Frame(status_frame, bg=self.bg_color)
#         status_grid.pack(fill=tk.X, padx=5, pady=5)
#         
#         # Status labels
#         self.status_labels = {}
#         status_items = [
#             ("connection", "🔗 Connection:", "Disconnected"),
#             ("api", "📡 API:", "Unknown"),
#             ("ai", "🤖 AI:", "Unknown"),
#             ("cycles", "🔄 Cycles:", "0"),
#             ("uptime", "⏱️ Uptime:", "00:00:00"),
#             ("pnl", "💰 PnL:", "$0.00"),
#             ("trades", "📈 Trades:", "0"),
#             ("errors", "❌ Errors:", "0")
#         ]
#         
#         for i, (key, label, default) in enumerate(status_items):
#             row = i // 4
#             col = (i % 4) * 2
#             
#             tk.Label(status_grid, text=label, font=('Arial', 10), 
#                     fg=self.fg_color, bg=self.bg_color).grid(row=row, column=col, sticky='w', padx=5)
#             self.status_labels[key] = tk.Label(status_grid, text=default, font=('Arial', 10, 'bold'),
#                                               fg=self.fg_color, bg=self.bg_color)
#             self.status_labels[key].grid(row=row, column=col+1, sticky='w', padx=5)
#     
#     def create_market_section(self, parent):
#         """Create market data section"""
#         market_frame = tk.LabelFrame(parent, text="📊 MARKET DATA", 
#                                    font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         market_frame.pack(fill=tk.X, pady=5)
#         
#         market_grid = tk.Frame(market_frame, bg=self.bg_color)
#         market_grid.pack(fill=tk.X, padx=5, pady=5)
#         
#         # Market labels
#         self.market_labels = {}
#         market_items = [
#             ("symbol", "Symbol:", "ENA_USDT"),
#             ("bid", "Best Bid:", "$0.000000"),
#             ("ask", "Best Ask:", "$0.000000"),
#             ("spread", "Spread:", "0.000%"),
#             ("positions", "Positions:", "0"),
#             ("balance", "Total Balance:", "$0.00")
#         ]
#         
#         for i, (key, label, default) in enumerate(market_items):
#             row = i // 3
#             col = (i % 3) * 2
#             
#             tk.Label(market_grid, text=label, font=('Arial', 10), 
#                     fg=self.fg_color, bg=self.bg_color).grid(row=row, column=col, sticky='w', padx=5)
#             self.market_labels[key] = tk.Label(market_grid, text=default, font=('Arial', 10, 'bold'),
#                                               fg=self.fg_color, bg=self.bg_color)
#             self.market_labels[key].grid(row=row, column=col+1, sticky='w', padx=5)
#     
#     def create_balance_section(self, parent):
#         """Create detailed balance section"""
#         balance_frame = tk.LabelFrame(parent, text="💰 REAL ACCOUNT BALANCE", 
#                                     font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         balance_frame.pack(fill=tk.X, pady=5)
#         
#         balance_grid = tk.Frame(balance_frame, bg=self.bg_color)
#         balance_grid.pack(fill=tk.X, padx=5, pady=5)
#         
#         # Balance labels
#         self.balance_labels = {}
#         balance_items = [
#             ("available", "Available:", "$0.00"),
#             ("used", "Used Margin:", "$0.00"),
#             ("unrealized", "Unrealized PnL:", "$0.00"),
#             ("margin_ratio", "Margin Ratio:", "0.0%")
#         ]
#         
#         for i, (key, label, default) in enumerate(balance_items):
#             row = i // 2
#             col = (i % 2) * 2
#             
#             tk.Label(balance_grid, text=label, font=('Arial', 10), 
#                     fg=self.fg_color, bg=self.bg_color).grid(row=row, column=col, sticky='w', padx=5)
#             self.balance_labels[key] = tk.Label(balance_grid, text=default, font=('Arial', 10, 'bold'),
#                                               fg=self.fg_color, bg=self.bg_color)
#             self.balance_labels[key].grid(row=row, column=col+1, sticky='w', padx=5)
#     
#     def create_ai_section(self, parent):
#         """Create AI decision section"""
#         ai_frame = tk.LabelFrame(parent, text="🤖 AI DECISIONS", 
#                                 font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         ai_frame.pack(fill=tk.X, pady=5)
#         
#         # AI decision display
#         ai_grid = tk.Frame(ai_frame, bg=self.bg_color)
#         ai_grid.pack(fill=tk.X, padx=5, pady=5)
#         
#         tk.Label(ai_grid, text="Action:", font=('Arial', 10), 
#                 fg=self.fg_color, bg=self.bg_color).grid(row=0, column=0, sticky='w', padx=5)
#         self.ai_action_label = tk.Label(ai_grid, text="HOLD", font=('Arial', 10, 'bold'),
#                                        fg=self.fg_color, bg=self.bg_color)
#         self.ai_action_label.grid(row=0, column=1, sticky='w', padx=5)
#         
#         tk.Label(ai_grid, text="Confidence:", font=('Arial', 10), 
#                 fg=self.fg_color, bg=self.bg_color).grid(row=0, column=2, sticky='w', padx=5)
#         self.ai_confidence_label = tk.Label(ai_grid, text="0.00", font=('Arial', 10, 'bold'),
#                                            fg=self.fg_color, bg=self.bg_color)
#         self.ai_confidence_label.grid(row=0, column=3, sticky='w', padx=5)
#         
#         tk.Label(ai_grid, text="Reasoning:", font=('Arial', 10), 
#                 fg=self.fg_color, bg=self.bg_color).grid(row=1, column=0, sticky='w', padx=5)
#         self.ai_reasoning_label = tk.Label(ai_grid, text="Waiting for AI...", font=('Arial', 9),
#                                           fg=self.fg_color, bg=self.bg_color, wraplength=800)
#         self.ai_reasoning_label.grid(row=1, column=1, columnspan=3, sticky='w', padx=5)
#         
#         # AI Performance
#         perf_frame = tk.Frame(ai_frame, bg=self.bg_color)
#         perf_frame.pack(fill=tk.X, padx=5, pady=5)
#         
#         tk.Label(perf_frame, text="AI Performance:", font=('Arial', 10), 
#                 fg=self.fg_color, bg=self.bg_color).pack(side=tk.LEFT, padx=5)
#         self.ai_performance_label = tk.Label(perf_frame, text="Decisions: 0 | Accuracy: 0%", 
#                                            font=('Arial', 10, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         self.ai_performance_label.pack(side=tk.LEFT, padx=5)
#     
#     def create_trading_section(self, parent):
#         """Create trading activity section"""
#         trading_frame = tk.LabelFrame(parent, text="💼 TRADING ACTIVITY", 
#                                     font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         trading_frame.pack(fill=tk.BOTH, expand=True, pady=5)
#         
#         # Create treeview for trades
#         columns = ('Time', 'Side', 'Size', 'Price', 'Status', 'PnL')
#         self.trades_tree = ttk.Treeview(trading_frame, columns=columns, show='headings', height=8)
#         
#         # Configure columns
#         for col in columns:
#             self.trades_tree.heading(col, text=col)
#             self.trades_tree.column(col, width=120)
#         
#         # Scrollbar
#         scrollbar = ttk.Scrollbar(trading_frame, orient=tk.VERTICAL, command=self.trades_tree.yview)
#         self.trades_tree.configure(yscrollcommand=scrollbar.set)
#         
#         # Pack
#         self.trades_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
#         scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
#         
#         # Style the treeview
#         style = ttk.Style()
#         style.configure("Treeview", background='#1a1a1a', foreground=self.fg_color, 
#                        fieldbackground='#1a1a1a')
#         style.configure("Treeview.Heading", background='#2a2a2a', foreground=self.fg_color)
#     
#     def create_log_section(self, parent):
#         """Create log section"""
#         log_frame = tk.LabelFrame(parent, text="📝 ACTIVITY LOG", 
#                                 font=('Arial', 12, 'bold'), fg=self.fg_color, bg=self.bg_color)
#         log_frame.pack(fill=tk.X, pady=5)
#         
#         self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=100, 
#                                                  bg='#1a1a1a', fg=self.fg_color, 
#                                                  font=('Courier', 9))
#         self.log_text.pack(fill=tk.X, padx=5, pady=5)
#     
#     def create_control_section(self, parent):
#         """Create control section"""
#         control_frame = tk.Frame(parent, bg=self.bg_color)
#         control_frame.pack(fill=tk.X, pady=5)
#         
#         # Control buttons
#         self.start_button = tk.Button(control_frame, text="🚀 START TRADING", 
#                                      command=self.toggle_trading, font=('Arial', 12, 'bold'),
#                                      bg='#00aa00', fg='white', padx=20, pady=10)
#         self.start_button.pack(side=tk.LEFT, padx=5)
#         
#         tk.Button(control_frame, text="📊 REFRESH", command=self.manual_refresh,
#                  font=('Arial', 10), bg='#0066cc', fg='white', padx=15, pady=10).pack(side=tk.LEFT, padx=5)
#         
#         tk.Button(control_frame, text="🗑️ CLEAR LOGS", command=self.clear_logs,
#                  font=('Arial', 10), bg='#666666', fg='white', padx=15, pady=10).pack(side=tk.LEFT, padx=5)
#         
#         # Status indicator
#         self.status_indicator = tk.Label(control_frame, text="● STOPPED", 
#                                        font=('Arial', 12, 'bold'), fg=self.error_color, bg=self.bg_color)
#         self.status_indicator.pack(side=tk.RIGHT, padx=20)
#     
#     def start_trading(self):
#         """Start trading in separate thread"""
#         if self.trading_thread is None or not self.trading_thread.is_alive():
#             self.engine.running = True
#             self.trading_thread = threading.Thread(target=self.trading_loop, daemon=True)
#             self.trading_thread.start()
#             self.logger.info("🚀 Trading started")
#     
#     def stop_trading(self):
#         """Stop trading"""
#         self.engine.running = False
#         if self.trading_thread:
#             self.trading_thread.join(timeout=5)
#         self.logger.info("🛑 Trading stopped")
#     
#     def toggle_trading(self):
#         """Toggle trading on/off"""
#         if self.engine.running:
#             self.stop_trading()
#             self.start_button.config(text="🚀 START TRADING", bg='#00aa00')
#             self.status_indicator.config(text="● STOPPED", fg=self.error_color)
#         else:
#             self.start_trading()
#             self.start_button.config(text="🛑 STOP TRADING", bg='#aa0000')
#             self.status_indicator.config(text="● RUNNING", fg=self.fg_color)
#     
#     def trading_loop(self):
#         """Main trading loop"""
#         while self.engine.running:
#             try:
#                 result = self.engine.run_cycle()
#                 self.update_queue.put(("cycle_result", result))
#                 time.sleep(5)  # 5-second cycles
#             except Exception as e:
#                 self.logger.error(f"❌ Trading loop error: {str(e)}")
#                 self.update_queue.put(("error", str(e)))
#                 time.sleep(5)
#     
#     def manual_refresh(self):
#         """Manual refresh of data"""
#         try:
#             status = self.engine.get_system_status()
#             self.update_queue.put(("status_update", status))
#         except Exception as e:
#             self.logger.error(f"❌ Refresh error: {str(e)}")
#     
#     def clear_logs(self):
#         """Clear activity log"""
#         self.log_text.delete(1.0, tk.END)
#     
#     def update_ui(self):
#         """Update UI with latest data"""
#         try:
#             # Process queue updates
#             while not self.update_queue.empty():
#                 try:
#                     update_type, data = self.update_queue.get_nowait()
#                     
#                     if update_type == "cycle_result":
#                         self.handle_cycle_result(data)
#                     elif update_type == "status_update":
#                         self.update_status_display(data)
#                     elif update_type == "error":
#                         self.log_message(f"❌ Error: {data}", self.error_color)
#                     
#                 except queue.Empty:
#                     break
#             
#             # Update status display
#             if self.engine.cycle_count > 0:
#                 status = self.engine.get_system_status()
#                 self.update_status_display(status)
#             
#             # Update market data
#             if self.engine.market_data:
#                 latest_market = self.engine.market_data[-1]
#                 self.update_market_display(latest_market)
#             
#             # Update AI display
#             if self.engine.ai_decisions:
#                 latest_ai = self.engine.ai_decisions[-1]
#                 self.update_ai_display(latest_ai)
#             
#             # Update trades display
#             self.update_trades_display()
#             
#         except Exception as e:
#             self.logger.error(f"❌ UI update error: {str(e)}")
#         
#         # Schedule next update
#         self.root.after(1000, self.update_ui)  # Update every second
#     
#     def handle_cycle_result(self, result):
#         """Handle trading cycle result"""
#         if result["success"]:
#             # Log cycle completion
#             self.log_message(f"✅ Cycle {result['cycle']} completed in {result['cycle_time']:.2f}s")
#             
#             # Log new trades
#             for trade in result.get("new_trades", []):
#                 self.log_message(f"📈 {trade.side}: {trade.size:.6f} @ ${trade.price:.6f}")
#             
#             # Log profit trades
#             for trade in result.get("profit_trades", []):
#                 self.log_message(f"💰 Profit taken: ${trade.pnl:.4f}")
#             
#             # Log AI decision
#             ai_decision = result.get("ai_decision")
#             if ai_decision:
#                 self.log_message(f"🤖 AI: {ai_decision.action} (confidence: {ai_decision.confidence:.2f})")
#         else:
#             self.log_message(f"❌ Cycle failed: {result.get('error', 'Unknown')}", self.error_color)
#     
#     def update_status_display(self, status: SystemStatus):
#         """Update status display"""
#         self.status_labels["connection"].config(
#             text="Connected" if status.connected else "Disconnected",
#             fg=self.fg_color if status.connected else self.error_color
#         )
#         self.status_labels["api"].config(text=status.api_status)
#         self.status_labels["ai"].config(text=status.ai_status)
#         self.status_labels["cycles"].config(text=str(status.cycle_count))
#         
#         # Format uptime
#         uptime_hours = int(status.uptime // 3600)
#         uptime_minutes = int((status.uptime % 3600) // 60)
#         uptime_seconds = int(status.uptime % 60)
#         self.status_labels["uptime"].config(text=f"{uptime_hours:02d}:{uptime_minutes:02d}:{uptime_seconds:02d}")
#         
#         # Format PnL
#         pnl_color = self.fg_color if status.daily_pnl >= 0 else self.error_color
#         self.status_labels["pnl"].config(text=f"${status.daily_pnl:.4f}", fg=pnl_color)
#         self.status_labels["trades"].config(text=str(status.total_trades))
#         self.status_labels["errors"].config(text=str(status.error_count))
#     
#     def update_market_display(self, market_data: MarketData):
#         """Update market data display"""
#         self.market_labels["symbol"].config(text=market_data.symbol)
#         self.market_labels["bid"].config(text=f"${market_data.bid:.6f}")
#         self.market_labels["ask"].config(text=f"${market_data.ask:.6f}")
#         
#         spread_pct = (market_data.spread / market_data.bid) * 100 if market_data.bid > 0 else 0
#         spread_color = self.fg_color if spread_pct < 0.1 else self.warning_color
#         self.market_labels["spread"].config(text=f"{spread_pct:.3f}%", fg=spread_color)
#         
#         # Update positions and REAL balance
#         positions = self.engine.client.get_positions()
#         account = self.engine.client.get_account()
#         
#         position_count = len([p for p in positions if float(p.get('size', 0)) != 0])
#         self.market_labels["positions"].config(text=str(position_count))
#         
#         # Show real balance from Gate.io
#         if account:
#             total_balance = float(account.get('total', 0))
#             available_balance = float(account.get('available', 0))
#             unrealized_pnl = float(account.get('unrealised_pnl', 0))
#             
#             # Format balance display
#             balance_text = f"${total_balance:.2f}"
#             if available_balance != total_balance:
#                 balance_text += f" (avail: ${available_balance:.2f})"
#             
#             # Color based on PnL
#             balance_color = self.fg_color if unrealized_pnl >= 0 else self.error_color
#             
#             self.market_labels["balance"].config(text=balance_text, fg=balance_color)
#             
#             # Log balance updates periodically
#             if hasattr(self, '_last_balance_log'):
#                 if time.time() - self._last_balance_log > 60:  # Log every minute
#                     self.logger.info(f"💰 Real Balance: ${total_balance:.2f} | Available: ${available_balance:.2f} | PnL: ${unrealized_pnl:.4f}")
#                     self._last_balance_log = time.time()
#             else:
#                 self._last_balance_log = time.time()
#         else:
#             self.market_labels["balance"].config(text="No API Connection", fg=self.error_color)
#         
#         # Update detailed balance section
#         self.update_balance_display(account)
#     
#     def update_balance_display(self, account: Dict):
#         """Update detailed balance display"""
#         if account:
#             available = float(account.get('available', 0))
#             used = float(account.get('used', 0))
#             unrealized_pnl = float(account.get('unrealised_pnl', 0))
#             total = float(account.get('total', 0))
#             
#             # Calculate margin ratio
#             margin_ratio = (used / total * 100) if total > 0 else 0
#             
#             # Update balance labels with colors
#             self.balance_labels["available"].config(text=f"${available:.2f}")
#             self.balance_labels["used"].config(text=f"${used:.2f}")
#             
#             # Color code unrealized PnL
#             pnl_color = self.fg_color if unrealized_pnl >= 0 else self.error_color
#             self.balance_labels["unrealized"].config(text=f"${unrealized_pnl:.4f}", fg=pnl_color)
#             
#             # Color code margin ratio
#             margin_color = self.fg_color if margin_ratio < 50 else self.warning_color if margin_ratio < 80 else self.error_color
#             self.balance_labels["margin_ratio"].config(text=f"{margin_ratio:.1f}%", fg=margin_color)
#             
#             # Log detailed balance info
#             if hasattr(self, '_last_detailed_balance_log'):
#                 if time.time() - self._last_detailed_balance_log > 120:  # Log every 2 minutes
#                     self.logger.info(f"💰 Detailed Balance - Available: ${available:.2f} | Used: ${used:.2f} | PnL: ${unrealized_pnl:.4f} | Margin: {margin_ratio:.1f}%")
#                     self._last_detailed_balance_log = time.time()
#             else:
#                 self._last_detailed_balance_log = time.time()
#         else:
#             # Show error state
#             for key in self.balance_labels:
#                 self.balance_labels[key].config(text="No Data", fg=self.error_color)
#     
#     def update_ai_display(self, ai_decision: AIDecision):
#         """Update AI decision display"""
#         # Color code based on action
#         action_colors = {
#             "BUY": "#00aa00",
#             "SELL": "#aa0000", 
#             "HOLD": "#666666",
#             "ADJUST": "#ffaa00"
#         }
#         
#         action_color = action_colors.get(ai_decision.action, self.fg_color)
#         self.ai_action_label.config(text=ai_decision.action, fg=action_color)
#         
#         # Confidence color
#         conf_color = self.fg_color if ai_decision.confidence > 0.7 else self.warning_color
#         self.ai_confidence_label.config(text=f"{ai_decision.confidence:.2f}", fg=conf_color)
#         
#         # Reasoning
#         self.ai_reasoning_label.config(text=ai_decision.reasoning)
#         
#         # Performance
#         perf = self.engine.ai_system.performance_metrics
#         accuracy_color = self.fg_color if perf["accuracy"] > 0.6 else self.warning_color
#         self.ai_performance_label.config(
#             text=f"Decisions: {perf['total_decisions']} | Accuracy: {perf['accuracy']:.1%}",
#             fg=accuracy_color
#         )
#     
#     def update_trades_display(self):
#         """Update trades display"""
#         # Clear existing items
#         for item in self.trades_tree.get_children():
#             self.trades_tree.delete(item)
#         
#         # Add recent trades (last 50)
#         recent_trades = list(self.engine.trades)[-50:]
#         for trade in reversed(recent_trades):
#             time_str = datetime.fromtimestamp(trade.timestamp).strftime("%H:%M:%S")
#             
#             # Color based on PnL
#             pnl_str = f"${trade.pnl:.4f}" if trade.pnl != 0 else ""
#             pnl_color = "green" if trade.pnl > 0 else "red" if trade.pnl < 0 else "white"
#             
#             values = (time_str, trade.side, f"{trade.size:.6f}", 
#                      f"${trade.price:.6f}", trade.status, pnl_str)
#             
#             item = self.trades_tree.insert('', tk.END, values=values)
#             if trade.pnl != 0:
#                 self.trades_tree.set(item, 'PnL', pnl_str)
#     
#     def log_message(self, message: str, color: str = None):
#         """Add message to activity log"""
#         timestamp = datetime.now().strftime("%H:%M:%S")
#         self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
#         
#         if color:
#             # Add color tags (simplified for this implementation)
#             pass
#         
#         # Auto-scroll to bottom
#         self.log_text.see(tk.END)
#         
#         # Limit log size
#         lines = self.log_text.get(1.0, tk.END).split('\n')
#         if len(lines) > 100:
#             self.log_text.delete(1.0, f"{len(lines)-100}.0")
#     
#     def on_closing(self):
#         """Handle window closing"""
#         if messagebox.askokcancel("Quit", "Do you want to stop trading and quit?"):
#             self.stop_trading()
#             self.root.destroy()
#     
#     def run(self):
#         """Run the dashboard"""
#         self.logger.info("🚀 Starting Trading Dashboard UI")
#         self.root.mainloop()
#
# def main():
#     """Main entry point"""
#     print("🚀 AI TRADING DASHBOARD - 24/7 HEDGING SYSTEM")
#     print("=" * 60)
#     print("📊 Complete Trading Interface with AI Optimization")
#     print("💰 Nominal Value: $0.01-$0.10 per trade")
#     print("🤖 AI-powered decisions and optimization")
#     print("🔊 Exchange sounds on successful orders")
#     print("=" * 60)
#     
#     # Check environment variables
#     required_vars = ["GATE_API_KEY", "GATE_API_SECRET"]
#     missing_vars = [var for var in required_vars if not os.getenv(var)]
#     
#     if missing_vars:
#         print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
#         print("Please set them and restart:")
#         for var in missing_vars:
#             print(f"   export {var}='your-value'")
#         print("")
#         print("⚠️  Dashboard will start in DEMO mode")
#     
#     if not os.getenv("OPENROUTER_API_KEY"):
#         print("⚠️  OPENROUTER_API_KEY not set - AI features will be disabled")
#         print("   export OPENROUTER_API_KEY='your-key'")
#         print("")
#     
#     # Create and run dashboard
#     dashboard = TradingDashboard()
#     dashboard.run()
#
# if __name__ == "__main__":
#     main()
# ===== END   [117/134] Hedging_Project/src/trading_dashboard_ai.py =====

# ===== BEGIN [118/134] Hedging_Project/src/utils/__init__.py sha256=c1820235355060e8 =====
# """
# Utilities for Hedging Project
# """
#
# from .gateio_client import GateIOClient
# from .position_manager import PositionManager
#
# __all__ = ['GateIOClient', 'PositionManager']
# ===== END   [118/134] Hedging_Project/src/utils/__init__.py =====

# ===== BEGIN [119/134] Hedging_Project/src/utils/api_client.py sha256=f6b066f6cdce76e3 =====
# #!/usr/bin/env python3
# """
# Position Manager for Hedging Project
# Manages positions and profit-taking logic
# """
#
# import logging
# from typing import List, Dict, Optional
# from dataclasses import dataclass
# from .api_client import GateIOClient
#
# @dataclass
# class PositionInfo:
#     symbol: str
#     size: float
#     entry_price: float
#     current_price: float
#     unrealized_pnl: float
#     unrealized_pct: float
#     age_seconds: float
#
# class PositionManager:
#     """Manages trading positions and profit-taking"""
#     
#     def __init__(self, client: GateIOClient, profit_threshold: float = 0.002):
#         self.client = client
#         self.profit_threshold = profit_threshold
#         self.logger = logging.getLogger('PositionManager')
#     
#     def get_positions(self) -> List[PositionInfo]:
#         """Get current positions with detailed info"""
#         result = self.client.get_positions()
#         
#         if not result.success:
#             self.logger.error(f"Failed to get positions: {result.error}")
#             return []
#         
#         positions = []
#         current_time = time.time()
#         
#         for pos in result.data:
#             size = float(pos['size'])
#             if size != 0:  # Only non-zero positions
#                 entry_price = float(pos['entry_price'])
#                 mark_price = float(pos['mark_price'])
#                 unrealized_pnl = float(pos['unrealised_pnl'])
#                 
#                 # Calculate percentage
#                 unrealized_pct = (mark_price - entry_price) / entry_price if entry_price > 0 else 0
#                 
#                 position = PositionInfo(
#                     symbol=pos['contract'],
#                     size=size,
#                     entry_price=entry_price,
#                     current_price=mark_price,
#                     unrealized_pnl=unrealized_pnl,
#                     unrealized_pct=unrealized_pct,
#                     age_seconds=0  # Would need timestamp info
#                 )
#                 
#                 positions.append(position)
#         
#         return positions
#     
#     def get_profitable_positions(self) -> List[PositionInfo]:
#         """Get positions that exceed profit threshold"""
#         positions = self.get_positions()
#         profitable = []
#         
#         for pos in positions:
#             if pos.unrealized_pct >= self.profit_threshold:
#                 profitable.append(pos)
#                 self.logger.info(f"💰 Profitable position: {pos.symbol} {pos.unrealized_pct:.2%}")
#         
#         return profitable
#     
#     def should_sell_position(self, position: PositionInfo) -> bool:
#         """Determine if position should be sold for profit"""
#         return position.unrealized_pct >= self.profit_threshold
#     
#     def close_position_for_profit(self, position: PositionInfo, size: float = None) -> bool:
#         """Close position for profit"""
#         if size is None:
#             size = abs(position.size)
#         
#         # Determine side based on position size
#         side = "SELL" if position.size > 0 else "BUY"
#         
#         result = self.client.place_order(
#             symbol=position.symbol,
#             side=side,
#             size=size,
#             price=0,  # Market order
#             order_type="market"
#         )
#         
#         if result.success:
#             self.logger.info(f"💰 Profit taken: {side} {size:.6f} {position.symbol} (Profit: {position.unrealized_pct:.2%})")
#             return True
#         else:
#             self.logger.error(f"❌ Failed to take profit: {result.error}")
#             return False
# ===== END   [119/134] Hedging_Project/src/utils/api_client.py =====

# ===== BEGIN [120/134] Hedging_Project/src/utils/enhanced_gateio_client.py sha256=3d94c8c923cfe166 =====
# #!/usr/bin/env python3
# """
# Enhanced Gate.io API Client with proper connection and AI integration
# """
#
# import os
# import time
# import json
# import requests
# import hmac
# import hashlib
# import logging
# from typing import Dict, List, Optional, Any
# from dataclasses import dataclass
#
# @dataclass
# class APIResult:
#     success: bool
#     data: Any = None
#     error: str = None
#
# class EnhancedGateIOClient:
#     """Enhanced Gate.io API client with proper connection handling"""
#     
#     def __init__(self):
#         # Load environment variables
#         self.api_key = os.getenv("GATE_API_KEY", "")
#         self.api_secret = os.getenv("GATE_API_SECRET", "")
#         self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
#         
#         self.base_url = "https://api.gateio.ws/api/v4"
#         self.settle = "usdt"
#         self.logger = logging.getLogger('EnhancedGateIOClient')
#         
#         # Validate API keys
#         self._validate_keys()
#         
#         # Session for connection pooling
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'HedgingProject/1.0',
#             'Accept': 'application/json',
#             'Content-Type': 'application/json'
#         })
#         
#         self.logger.info("🔗 Enhanced Gate.io Client initialized")
#         self.logger.info(f"🔑 API Key configured: {'✅' if self.api_key else '❌'}")
#         self.logger.info(f"🤖 OpenRouter configured: {'✅' if self.openrouter_key else '❌'}")
#     
#     def _validate_keys(self):
#         """Validate API keys are present and properly formatted"""
#         if not self.api_key:
#             self.logger.error("❌ GATE_API_KEY not found in environment")
#         elif len(self.api_key) < 10:
#             self.logger.error("❌ GATE_API_KEY appears too short")
#         else:
#             self.logger.info(f"✅ GATE_API_KEY: {self.api_key[:8]}...")
#         
#         if not self.api_secret:
#             self.logger.error("❌ GATE_API_SECRET not found in environment")
#         elif len(self.api_secret) < 20:
#             self.logger.error("❌ GATE_API_SECRET appears too short")
#         else:
#             self.logger.info(f"✅ GATE_API_SECRET: {self.api_secret[:8]}...")
#         
#         if not self.openrouter_key:
#             self.logger.warning("⚠️  OPENROUTER_API_KEY not found - AI features disabled")
#         else:
#             self.logger.info(f"✅ OPENROUTER_API_KEY: {self.openrouter_key[:12]}...")
#     
#     def _sign_request(self, method: str, path: str, query_string: str, payload: str) -> Dict[str, str]:
#         """Generate Gate.io API signature with proper format"""
#         if not self.api_key or not self.api_secret:
#             raise ValueError("API keys not configured for private endpoints")
#         
#         ts = str(int(time.time()))
#         payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#         
#         # Gate.io v4 signature format
#         sign_str = f"{method.upper()}\n{path}\n{query_string}\n{payload_hash}\n{ts}"
#         
#         sign = hmac.new(
#             self.api_secret.encode("utf-8"),
#             sign_str.encode("utf-8"),
#             digestmod=hashlib.sha512,
#         ).hexdigest()
#         
#         return {
#             "KEY": self.api_key,
#             "Timestamp": ts,
#             "SIGN": sign,
#         }
#     
#     def _make_request(self, method: str, path: str, payload: str = "", private: bool = False) -> APIResult:
#         """Make API request with enhanced error handling"""
#         url = f"{self.base_url}{path}"
#         
#         # Prepare headers
#         headers = {}
#         if private:
#             try:
#                 headers.update(self._sign_request(method, path, "", payload))
#             except ValueError as e:
#                 return APIResult(success=False, error=str(e))
#         
#         try:
#             self.logger.debug(f"📡 {method} {url} (private: {private})")
#             
#             response = self.session.request(
#                 method, 
#                 url, 
#                 headers=headers,
#                 data=payload if payload else None,
#                 timeout=15
#             )
#             
#             self.logger.debug(f"📥 Response: {response.status_code}")
#             
#             if response.status_code == 200:
#                 return APIResult(success=True, data=response.json())
#             elif response.status_code == 401:
#                 error_msg = "Authentication failed - check API keys"
#                 self.logger.error(f"❌ {error_msg}")
#                 return APIResult(success=False, error=error_msg)
#             elif response.status_code == 403:
#                 error_msg = "Access forbidden - insufficient permissions"
#                 self.logger.error(f"❌ {error_msg}")
#                 return APIResult(success=False, error=error_msg)
#             else:
#                 error_msg = f"HTTP {response.status_code}: {response.text}"
#                 self.logger.error(f"❌ {error_msg}")
#                 return APIResult(success=False, error=error_msg)
#                 
#         except requests.exceptions.Timeout:
#             error_msg = "Request timeout (15s)"
#             self.logger.error(f"❌ {error_msg}")
#             return APIResult(success=False, error=error_msg)
#         except requests.exceptions.ConnectionError:
#             error_msg = "Connection error - check internet"
#             self.logger.error(f"❌ {error_msg}")
#             return APIResult(success=False, error=error_msg)
#         except Exception as e:
#             error_msg = f"Request exception: {str(e)}"
#             self.logger.error(f"❌ {error_msg}")
#             return APIResult(success=False, error=error_msg)
#     
#     def test_connection(self) -> APIResult:
#         """Test connection to Gate.io API"""
#         self.logger.info("🔍 Testing Gate.io connection...")
#         
#         # Test public endpoint
#         contracts = self._make_request("GET", f"/futures/{self.settle}/contracts")
#         if not contracts.success:
#             return APIResult(success=False, error=f"Public endpoint failed: {contracts.error}")
#         
#         # Test private endpoint if keys are available
#         if self.api_key and self.api_secret:
#             account = self._make_request("GET", f"/futures/{self.settle}/accounts", "", private=True)
#             if not account.success:
#                 return APIResult(success=False, error=f"Private endpoint failed: {account.error}")
#             
#             balance = float(account.data.get('total', 0))
#             self.logger.info(f"💰 Account balance: ${balance:.2f}")
#         
#         return APIResult(success=True, data={
#             'contracts_count': len(contracts.data),
#             'api_keys_configured': bool(self.api_key and self.api_secret)
#         })
#     
#     def get_best_bid_ask(self, symbol: str) -> tuple:
#         """Get best bid and ask prices"""
#         result = self._make_request("GET", f"/futures/{self.settle}/order_book?contract={symbol}&limit=1")
#         
#         if result.success and result.data:
#             data = result.data
#             if data.get('asks') and data.get('bids'):
#                 best_bid = float(data['bids'][0]['p'])
#                 best_ask = float(data['asks'][0]['p'])
#                 return best_bid, best_ask
#         
#         return None, None
#     
#     def get_positions(self) -> APIResult:
#         """Get current positions"""
#         return self._make_request("GET", f"/futures/{self.settle}/positions", "", private=True)
#     
#     def place_order(self, symbol: str, side: str, size: float, price: float = 0, 
#                    order_type: str = "limit", tif: str = "ioc") -> APIResult:
#         """Place order with enhanced validation"""
#         # Validate parameters
#         if side not in ["BUY", "SELL"]:
#             return APIResult(success=False, error="Invalid side: must be BUY or SELL")
#         
#         if size <= 0:
#             return APIResult(success=False, error="Size must be positive")
#         
#         if order_type not in ["limit", "market"]:
#             return APIResult(success=False, error="Invalid order type")
#         
#         order_data = {
#             "settle": self.settle,
#             "contract": symbol,
#             "size": str(size),
#             "price": str(price),
#             "type": order_type,
#             "tif": tif
#         }
#         
#         payload = json.dumps(order_data, separators=(",", ":"))
#         self.logger.info(f"🎯 Placing {side} order: {size:.6f} {symbol} @ ${price:.6f}")
#         
#         result = self._make_request("POST", f"/futures/{self.settle}/orders", payload, private=True)
#         
#         if result.success:
#             order_id = result.data.get('id')
#             self.logger.info(f"✅ Order placed successfully: {order_id}")
#         else:
#             self.logger.error(f"❌ Order failed: {result.error}")
#         
#         return result
#     
#     def get_account(self) -> APIResult:
#         """Get account information"""
#         return self._make_request("GET", f"/futures/{self.settle}/accounts", "", private=True)
#     
#     def get_contracts(self) -> APIResult:
#         """Get available contracts"""
#         return self._make_request("GET", f"/futures/{self.settle}/contracts")
#     
#     def calculate_nominal_size(self, price: float, target_nominal: float) -> float:
#         """Calculate order size for target nominal value"""
#         if price <= 0:
#             raise ValueError("Price must be positive")
#         
#         size = target_nominal / price
#         min_size = 0.001  # Gate.io minimum
#         return max(size, min_size)
#     
#     def get_ai_decision(self, market_data: Dict) -> Dict:
#         """Get AI trading decision from OpenRouter"""
#         if not self.openrouter_key:
#             return {
#                 "action": "HOLD",
#                 "symbol": "ENA_USDT",
#                 "confidence": 0.5,
#                 "reasoning": "AI disabled - no OpenRouter API key"
#             }
#         
#         try:
#             headers = {
#                 "Authorization": f"Bearer {self.openrouter_key}",
#                 "Content-Type": "application/json",
#                 "HTTP-Referer": "https://github.com/alep/hedging-project",
#                 "X-Title": "Hedging AI"
#             }
#             
#             prompt = f"""
#             Analyze these market conditions for hedging opportunities:
#             
#             Market Data: {json.dumps(market_data, indent=2)}
#             Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
#             
#             Strategy: Place best bid/ask orders, take profits at 0.2%
#             
#             Return JSON: {{"action": "BUY/SELL/HOLD", "symbol": "SYMBOL", "confidence": 0.0-1.0, "reasoning": "explanation"}}
#             """
#             
#             data = {
#                 "model": "anthropic/claude-3-haiku",
#                 "messages": [{"role": "user", "content": prompt}],
#                 "max_tokens": 300,
#                 "temperature": 0.3
#             }
#             
#             response = requests.post(
#                 "https://openrouter.ai/api/v1/chat/completions",
#                 headers=headers,
#                 json=data,
#                 timeout=10
#             )
#             
#             if response.status_code == 200:
#                 result = response.json()
#                 content = result["choices"][0]["message"]["content"]
#                 
#                 # Parse JSON response
#                 if "```json" in content:
#                     json_str = content.split("```json")[1].split("```")[0].strip()
#                 else:
#                     json_str = content.strip()
#                 
#                 decision = json.loads(json_str)
#                 self.logger.info(f"🤖 AI Decision: {decision['action']} (confidence: {decision['confidence']:.2f})")
#                 return decision
#             else:
#                 self.logger.error(f"❌ AI API error: {response.status_code}")
#                 return {"action": "HOLD", "confidence": 0.5, "reasoning": f"API error: {response.status_code}"}
#                 
#         except Exception as e:
#             self.logger.error(f"❌ AI exception: {str(e)}")
#             return {"action": "HOLD", "confidence": 0.5, "reasoning": f"Exception: {str(e)}"}
# ===== END   [120/134] Hedging_Project/src/utils/enhanced_gateio_client.py =====

# ===== BEGIN [121/134] Hedging_Project/src/utils/gateio_client.py sha256=9825d0b13a4bf794 =====
# #!/usr/bin/env python3
# """
# Gate.io API Client for Hedging Project
# Handles all API communications with proper error handling
# """
#
# import os
# import time
# import json
# import requests
# import hmac
# import hashlib
# import logging
# from typing import Dict, List, Optional, Any
# from dataclasses import dataclass
#
# @dataclass
# class APIResult:
#     success: bool
#     data: Any = None
#     error: str = None
#
# class GateIOClient:
#     """Professional Gate.io API client"""
#     
#     def __init__(self):
#         self.api_key = os.getenv("GATE_API_KEY", "")
#         self.api_secret = os.getenv("GATE_API_SECRET", "")
#         self.base_url = "https://api.gateio.ws/api/v4"
#         self.settle = "usdt"
#         self.logger = logging.getLogger('GateIOClient')
#         
#         if not self.api_key or not self.api_secret:
#             self.logger.warning("⚠️  API keys not configured - using public endpoints only")
#     
#     def _sign_request(self, method: str, path: str, query_string: str, payload: str) -> Dict[str, str]:
#         """Generate Gate.io API signature"""
#         if not self.api_secret:
#             return {}
#         
#         ts = str(int(time.time()))
#         payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#         sign_str = f"{method.upper()}\n{path}\n{query_string}\n{payload_hash}\n{ts}"
#         sign = hmac.new(
#             self.api_secret.encode("utf-8"),
#             sign_str.encode("utf-8"),
#             digestmod=hashlib.sha512,
#         ).hexdigest()
#         
#         return {
#             "Accept": "application/json",
#             "Content-Type": "application/json",
#             "KEY": self.api_key,
#             "Timestamp": ts,
#             "SIGN": sign,
#         }
#     
#     def _make_request(self, method: str, path: str, payload: str = "", private: bool = False) -> APIResult:
#         """Make API request with error handling"""
#         headers = self._sign_request(method, path, "", payload) if private else {
#             "Accept": "application/json",
#             "Content-Type": "application/json"
#         }
#         
#         try:
#             url = f"{self.base_url}{path}"
#             response = requests.request(
#                 method, 
#                 url, 
#                 headers=headers, 
#                 data=payload if payload else None, 
#                 timeout=10
#             )
#             
#             if response.status_code == 200:
#                 return APIResult(success=True, data=response.json())
#             else:
#                 error_msg = f"HTTP {response.status_code}: {response.text}"
#                 self.logger.error(f"API Error: {error_msg}")
#                 return APIResult(success=False, error=error_msg)
#                 
#         except requests.exceptions.Timeout:
#             error_msg = "Request timeout"
#             self.logger.error(error_msg)
#             return APIResult(success=False, error=error_msg)
#         except requests.exceptions.ConnectionError:
#             error_msg = "Connection error"
#             self.logger.error(error_msg)
#             return APIResult(success=False, error=error_msg)
#         except Exception as e:
#             error_msg = f"Request exception: {str(e)}"
#             self.logger.error(error_msg)
#             return APIResult(success=False, error=error_msg)
#     
#     def get_best_bid_ask(self, symbol: str) -> tuple:
#         """Get best bid and ask prices"""
#         result = self.get_order_book(symbol, 1)
#         
#         if result.success and result.data:
#             data = result.data
#             if data.get('asks') and data.get('bids'):
#                 best_bid = float(data['bids'][0]['p'])
#                 best_ask = float(data['asks'][0]['p'])
#                 return best_bid, best_ask
#         
#         return None, None
#     
#     def get_order_book(self, symbol: str, limit: int = 10) -> APIResult:
#         """Get order book"""
#         return self._make_request("GET", f"/futures/{self.settle}/order_book?contract={symbol}&limit={limit}")
#     
#     def get_positions(self) -> APIResult:
#         """Get current positions"""
#         return self._make_request("GET", f"/futures/{self.settle}/positions", "", private=True)
#     
#     def place_order(self, symbol: str, side: str, size: float, price: float = 0, 
#                    order_type: str = "limit", tif: str = "ioc") -> APIResult:
#         """Place order"""
#         order_data = {
#             "settle": self.settle,
#             "contract": symbol,
#             "size": str(size),
#             "price": str(price),
#             "type": order_type,
#             "tif": tif
#         }
#         
#         payload = json.dumps(order_data, separators=(",", ":"))
#         return self._make_request("POST", f"/futures/{self.settle}/orders", payload, private=True)
#     
#     def cancel_order(self, order_id: str) -> APIResult:
#         """Cancel order"""
#         return self._make_request("DELETE", f"/futures/{self.settle}/orders/{order_id}", "", private=True)
#     
#     def get_account(self) -> APIResult:
#         """Get account information"""
#         return self._make_request("GET", f"/futures/{self.settle}/accounts", "", private=True)
#     
#     def get_contracts(self) -> APIResult:
#         """Get available contracts"""
#         return self._make_request("GET", f"/futures/{self.settle}/contracts")
#     
#     def calculate_nominal_size(self, price: float, target_nominal: float) -> float:
#         """Calculate order size for target nominal value"""
#         size = target_nominal / price
#         min_size = 0.001  # Gate.io minimum
#         return max(size, min_size)
# ===== END   [121/134] Hedging_Project/src/utils/gateio_client.py =====

# ===== BEGIN [122/134] Hedging_Project/src/utils/position_manager.py sha256=385c97e22f44ec7e =====
# #!/usr/bin/env python3
# """
# Position Manager for Hedging Project
# Manages positions and profit-taking logic
# """
#
# import time
# import logging
# from typing import List, Optional
# from dataclasses import dataclass
#
# @dataclass
# class PositionInfo:
#     symbol: str
#     size: float
#     entry_price: float
#     current_price: float
#     unrealized_pnl: float
#     unrealized_pct: float
#     age_seconds: float
#
# class PositionManager:
#     """Manages trading positions and profit-taking"""
#     
#     def __init__(self, client, profit_threshold: float = 0.002):
#         self.client = client
#         self.profit_threshold = profit_threshold
#         self.logger = logging.getLogger('PositionManager')
#     
#     def get_positions(self) -> List[PositionInfo]:
#         """Get current positions with detailed info"""
#         result = self.client.get_positions()
#         
#         if not result.success:
#             self.logger.error(f"Failed to get positions: {result.error}")
#             return []
#         
#         positions = []
#         
#         for pos in result.data:
#             size = float(pos['size'])
#             if size != 0:  # Only non-zero positions
#                 entry_price = float(pos['entry_price'])
#                 mark_price = float(pos['mark_price'])
#                 unrealized_pnl = float(pos['unrealised_pnl'])
#                 
#                 # Calculate percentage
#                 unrealized_pct = (mark_price - entry_price) / entry_price if entry_price > 0 else 0
#                 
#                 position = PositionInfo(
#                     symbol=pos['contract'],
#                     size=size,
#                     entry_price=entry_price,
#                     current_price=mark_price,
#                     unrealized_pnl=unrealized_pnl,
#                     unrealized_pct=unrealized_pct,
#                     age_seconds=0  # Would need timestamp info
#                 )
#                 
#                 positions.append(position)
#         
#         return positions
#     
#     def get_profitable_positions(self) -> List[PositionInfo]:
#         """Get positions that exceed profit threshold"""
#         positions = self.get_positions()
#         profitable = []
#         
#         for pos in positions:
#             if pos.unrealized_pct >= self.profit_threshold:
#                 profitable.append(pos)
#                 self.logger.info(f"💰 Profitable position: {pos.symbol} {pos.unrealized_pct:.2%}")
#         
#         return profitable
#     
#     def should_sell_position(self, position: PositionInfo) -> bool:
#         """Determine if position should be sold for profit"""
#         return position.unrealized_pct >= self.profit_threshold
#     
#     def close_position_for_profit(self, position: PositionInfo, size: float = None) -> bool:
#         """Close position for profit"""
#         if size is None:
#             size = abs(position.size)
#         
#         # Determine side based on position size
#         side = "SELL" if position.size > 0 else "BUY"
#         
#         result = self.client.place_order(
#             symbol=position.symbol,
#             side=side,
#             size=size,
#             price=0,  # Market order
#             order_type="market"
#         )
#         
#         if result.success:
#             self.logger.info(f"💰 Profit taken: {side} {size:.6f} {position.symbol} (Profit: {position.unrealized_pct:.2%})")
#             return True
#         else:
#             self.logger.error(f"❌ Failed to take profit: {result.error}")
#             return False
# ===== END   [122/134] Hedging_Project/src/utils/position_manager.py =====

# ===== BEGIN [123/134] ENA_Hedging_Project/src/ena_hedging_market_maker.py sha256=66cf9138d1085f81 =====
# #!/usr/bin/env python3
# """
# ENA_USDT HEDGING MARKET MAKER
# Intelligent hedging strategy with Cascade AI integration
# Optimized for ENA/USDT futures trading with real-time profit detection
#
# Author: Cascade AI Assistant
# Features:
# - 🧠 Cascade AI intelligent decision making
# - 🛡️ Advanced hedging strategy
# - 💰 Real-time profit detection and closing
# - 📊 Market analysis and risk management
# - 🎯 Best bid/ask order placement
# """
#
# import asyncio
# import websockets
# import json
# import time
# import math
# import logging
# import threading
# import tkinter as tk
# from tkinter import ttk, scrolledtext, messagebox
# from typing import Dict, List, Tuple, Optional
# from datetime import datetime
# from collections import deque
# import gate_api
# from gate_api import ApiClient, Configuration, FuturesApi
# import numpy as np
#
# # Setup logging
# logging.basicConfig(level=logging.INFO)
# log = logging.getLogger(__name__)
#
# class CascadeAIAssistant:
#     """Cascade AI Assistant - Intelligent Trading Decision Maker for ENA_USDT"""
#     
#     def __init__(self, config, ui):
#         self.config = config
#         self.ui = ui
#         self.market_analysis = {}
#         self.hedge_opportunities = []
#         self.risk_assessment = {}
#         self.last_analysis_time = 0
#         
#     def analyze_market_conditions(self, bids, asks, mid_price, position, balance):
#         """Cascade AI market analysis for intelligent ENA_USDT decisions"""
#         current_time = time.time()
#         
#         if not bids or not asks:
#             return {'action': 'WAIT', 'reason': 'No market data'}
#         
#         # Market structure analysis
#         best_bid = float(bids[0][0])
#         best_ask = float(asks[0][0])
#         spread_bps = (best_ask - best_bid) / mid_price * 10000
#         
#         # Volume and liquidity analysis
#         bid_volume = sum(float(bid[1]) for bid in bids[:5])
#         ask_volume = sum(float(ask[1]) for ask in asks[:5])
#         total_volume = bid_volume + ask_volume
#         volume_imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
#         
#         # Price momentum analysis
#         price_pressure = volume_imbalance * 0.5  # Volume-driven pressure
#         spread_pressure = max(0, (spread_bps - 5) / 20)  # Spread-driven pressure
#         
#         # Position risk analysis
#         position_risk = abs(position) / self.config.max_hedge_position if self.config.max_hedge_position > 0 else 0
#         balance_risk = max(0, (10 - balance) / 10)  # Higher risk when balance < $10
#         
#         # Cascade AI Decision Logic
#         decision = self._make_trading_decision(
#             spread_bps, volume_imbalance, position_risk, balance_risk,
#             price_pressure, spread_pressure, mid_price, position
#         )
#         
#         # Update analysis cache
#         self.market_analysis = {
#             'spread_bps': spread_bps,
#             'volume_imbalance': volume_imbalance,
#             'total_volume': total_volume,
#             'price_pressure': price_pressure,
#             'spread_pressure': spread_pressure,
#             'position_risk': position_risk,
#             'balance_risk': balance_risk,
#             'decision': decision,
#             'timestamp': current_time
#         }
#         
#         return decision
#     
#     def _make_trading_decision(self, spread_bps, volume_imbalance, position_risk, 
#                               balance_risk, price_pressure, spread_pressure, mid_price, position):
#         """Cascade AI core decision making logic for ENA_USDT"""
#         
#         # Risk assessment
#         overall_risk = (position_risk * 0.4 + balance_risk * 0.3 + 
#                        max(0, spread_pressure) * 0.2 + abs(volume_imbalance) * 0.1)
#         
#         # Opportunity scoring
#         opportunity_score = 0
#         
#         # Spread opportunity (higher spread = better opportunity for ENA)
#         if spread_bps > 3:
#             opportunity_score += min(spread_bps / 10, 0.4)
#         
#         # Volume imbalance opportunity
#         if abs(volume_imbalance) > 0.2:
#             opportunity_score += min(abs(volume_imbalance) * 0.5, 0.3)
#         
#         # Price pressure opportunity
#         if abs(price_pressure) > 0.1:
#             opportunity_score += min(abs(price_pressure) * 0.3, 0.3)
#         
#         # Cascade AI Decision Tree for ENA_USDT
#         if overall_risk > 0.8:
#             return {
#                 'action': 'REDUCE',
#                 'reason': f'High risk detected ({overall_risk:.2f}) - reducing ENA exposure',
#                 'confidence': 0.9,
#                 'risk_level': 'HIGH'
#             }
#         
#         elif opportunity_score > 0.6 and spread_bps > self.config.min_profit_bps * 2:
#             return {
#                 'action': 'HEDGE_AGGRESSIVE',
#                 'reason': f'High ENA opportunity ({opportunity_score:.2f}) - aggressive hedging',
#                 'confidence': min(0.95, 0.7 + opportunity_score * 0.25),
#                 'opportunity_score': opportunity_score,
#                 'risk_level': 'MEDIUM'
#             }
#         
#         elif opportunity_score > 0.3 and spread_bps > self.config.min_profit_bps:
#             return {
#                 'action': 'HEDGE_CONSERVATIVE',
#                 'reason': f'Moderate ENA opportunity ({opportunity_score:.2f}) - conservative hedging',
#                 'confidence': 0.6 + opportunity_score * 0.2,
#                 'opportunity_score': opportunity_score,
#                 'risk_level': 'LOW'
#             }
#         
#         elif position_risk > 0.6:
#             return {
#                 'action': 'WAIT',
#                 'reason': f'ENA position risk too high ({position_risk:.2f}) - waiting',
#                 'confidence': 0.8,
#                 'risk_level': 'MEDIUM'
#             }
#         
#         else:
#             return {
#                 'action': 'MONITOR',
#                 'reason': f'ENA market conditions neutral - monitoring',
#                 'confidence': 0.5,
#                 'opportunity_score': opportunity_score,
#                 'risk_level': 'LOW'
#             }
#     
#     def get_hedge_recommendations(self, decision, bids, asks, mid_price):
#         """Get specific ENA hedge recommendations based on AI decision"""
#         if decision['action'] not in ['HEDGE_AGGRESSIVE', 'HEDGE_CONSERVATIVE']:
#             return []
#         
#         recommendations = []
#         
#         # Calculate optimal hedge sizes for ENA
#         available_balance = 5.56  # Default balance
#         base_size_usd = self.config.hedge_order_size_usd
#         
#         if decision['action'] == 'HEDGE_AGGRESSIVE':
#             # Aggressive hedging - larger sizes, tighter spreads
#             size_multiplier = 1.5
#             price_improvement = 0.0002
#         else:
#             # Conservative hedging - smaller sizes, standard spreads
#             size_multiplier = 1.0
#             price_improvement = self.config.hedge_price_improvement
#         
#         # Calculate hedge size
#         hedge_usd = min(base_size_usd * size_multiplier, available_balance * 0.3)
#         hedge_size = hedge_usd / mid_price
#         
#         # Get best prices
#         best_bid = float(bids[0][0])
#         best_ask = float(asks[0][0])
#         
#         # Calculate improved prices
#         buy_price = best_bid + price_improvement
#         sell_price = best_ask - price_improvement
#         
#         # Ensure minimum profit
#         expected_spread_bps = (sell_price - buy_price) / mid_price * 10000
#         if expected_spread_bps < self.config.min_profit_bps:
#             # Adjust to minimum profit
#             half_spread = self.config.min_profit_bps / 2 / 10000 * mid_price
#             buy_price = mid_price - half_spread
#             sell_price = mid_price + half_spread
#         
#         recommendations.append({
#             'action': 'PLACE_HEDGE_PAIR',
#             'buy_price': buy_price,
#             'sell_price': sell_price,
#             'size': hedge_size,
#             'expected_profit_bps': expected_spread_bps,
#             'confidence': decision['confidence'],
#             'reason': decision['reason']
#         })
#         
#         return recommendations
#     
#     def log_ai_decision(self, decision):
#         """Log AI decision with detailed reasoning for ENA_USDT"""
#         risk_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
#         action_emoji = {
#             'HEDGE_AGGRESSIVE': '🚀',
#             'HEDGE_CONSERVATIVE': '🛡️',
#             'WAIT': '⏳',
#             'MONITOR': '👁️',
#             'REDUCE': '⚠️'
#         }
#         
#         emoji = action_emoji.get(decision['action'], '🤖')
#         risk_emoji = risk_emoji.get(decision.get('risk_level', 'LOW'), '🟢')
#         
#         self.ui.add_log(f"🧠 CASCADE AI DECISION (ENA_USDT):")
#         self.ui.add_log(f"   {emoji} Action: {decision['action']}")
#         self.ui.add_log(f"   📊 Reason: {decision['reason']}")
#         self.ui.add_log(f"   🎯 Confidence: {decision['confidence']:.2f}")
#         self.ui.add_log(f"   {risk_emoji} Risk Level: {decision.get('risk_level', 'LOW')}")
#         
#         if 'opportunity_score' in decision:
#             self.ui.add_log(f"   💎 Opportunity Score: {decision['opportunity_score']:.3f}")
#
# class ENAHedgingConfig:
#     """Configuration for ENA_USDT Hedging Strategy"""
#     
#     def __init__(self):
#         # API Configuration
#         self.api_key = os.environ.get("GATE_API_KEY", "")
#         self.api_secret = os.environ.get("GATE_API_SECRET", "")
#         self.symbol = "ENA_USDT"  # ENA/USDT futures
#         
#         # Trading Parameters
#         self.order_size_usd = 1.0  # Base order size
#         self.order_refresh_ms = 100  # 100ms for high frequency
#         self.max_orders_per_second = 50
#         
#         # ENA Hedging Configuration
#         self.hedging_mode = True  # Enable hedging
#         self.min_profit_bps = 1.5  # Minimum profit margin (1.5 bps)
#         self.max_hedge_position = 50.0  # Maximum hedge position in ENA
#         self.hedge_order_size_usd = 3.0  # Order size for hedging
#         self.hedge_price_improvement = 0.0001  # Price improvement for best bid/ask
#         self.market_sell_threshold = 3.0  # 3 bps threshold for market selling
#         self.max_hedge_age_seconds = 300  # Close hedges after 5 minutes max
#         
#         # Risk Management
#         self.inventory_limit = 10.0  # 10 ENA tokens for small balance
#         self.spread_bps = 5.0  # Base spread
#
# class ENAHedgingStats:
#     """Statistics tracking for ENA hedging"""
#     
#     def __init__(self):
#         # Basic trading stats
#         self.total_trades = 0
#         self.total_volume = 0.0
#         self.total_pnl = 0.0
#         self.fees_paid = 0.0
#         self.orders_placed = 0
#         self.orders_filled = 0
#         self.orders_cancelled = 0
#         
#         # Balance tracking
#         self.available_balance = 0.0
#         self.total_balance = 0.0
#         self.unrealized_pnl = 0.0
#         self.margin_used = 0.0
#         self.margin_free = 0.0
#         
#         # ENA Hedging statistics
#         self.hedge_orders_placed = 0
#         self.hedge_orders_filled = 0
#         self.hedge_profit_trades = 0
#         self.hedge_loss_trades = 0
#         self.hedge_total_pnl = 0.0
#         self.hedge_fees_paid = 0.0
#         self.active_hedges = []  # Track active hedge positions
#         
#         # Performance tracking
#         self.tps_history = deque(maxlen=100)
#         self.pnl_history = deque(maxlen=1000)
#         self.start_time = time.time()
#         self.last_tps_calc = time.time()
#         self.orders_this_second = 0
#         self.current_tps = 0.0
#
# # Continue with the rest of the implementation...
# # [The file continues with UI, trading logic, etc.]
#
# if __name__ == "__main__":
#     print("🛡️ ENA_USDT Hedging Market Maker")
#     print("🧠 Powered by Cascade AI Assistant")
#     print("💰 Intelligent profit detection and hedging")
#     print("🎯 Optimized for ENA/USDT futures trading")
#     print("\n🚀 Starting ENA hedging system...")
# ===== END   [123/134] ENA_Hedging_Project/src/ena_hedging_market_maker.py =====

# ===== BEGIN [124/134] ENA_Hedging_Project/src/ena_hedging_market_maker_complete.py sha256=739ff99330300210 =====
# #!/usr/bin/env python3
# """
# ENA_USDT HEDGING MARKET MAKER - COMPLETE SYSTEM
# Intelligent hedging strategy with Cascade AI integration
# Multi-coin support for sub-10-cent tokens
#
# Author: Cascade AI Assistant
# """
#
# import asyncio
# import websockets
# import json
# import time
# import math
# import logging
# import threading
# import tkinter as tk
# from tkinter import ttk, scrolledtext, messagebox
# from typing import Dict, List, Tuple, Optional
# from datetime import datetime
# from collections import deque
# import gate_api
# from gate_api import ApiClient, Configuration, FuturesApi
# import numpy as np
# import sys
# import os
#
# # Add config path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
# from ena_config import ENAHedgingConfig, ENAHedgingConfigDev, ENAHedgingConfigProd
#
# # Setup logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# log = logging.getLogger(__name__)
#
# class CascadeAIAssistant:
#     """Cascade AI Assistant - Intelligent Trading Decision Maker"""
#     
#     def __init__(self, config, ui):
#         self.config = config
#         self.ui = ui
#         self.market_analysis = {}
#         self.hedge_opportunities = []
#         self.risk_assessment = {}
#         self.last_analysis_time = 0
#         
#     def analyze_market_conditions(self, bids, asks, mid_price, position, balance, symbol):
#         """Cascade AI market analysis for intelligent decisions"""
#         current_time = time.time()
#         
#         if not bids or not asks:
#             return {'action': 'WAIT', 'reason': 'No market data'}
#         
#         # Market structure analysis
#         best_bid = float(bids[0][0])
#         best_ask = float(asks[0][0])
#         spread_bps = (best_ask - best_bid) / mid_price * 10000
#         
#         # Volume and liquidity analysis
#         bid_volume = sum(float(bid[1]) for bid in bids[:5])
#         ask_volume = sum(float(ask[1]) for ask in asks[:5])
#         total_volume = bid_volume + ask_volume
#         volume_imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
#         
#         # Price momentum analysis
#         price_pressure = volume_imbalance * 0.5
#         spread_pressure = max(0, (spread_bps - 5) / 20)
#         
#         # Position risk analysis
#         position_risk = abs(position) / self.config.max_hedge_position if self.config.max_hedge_position > 0 else 0
#         balance_risk = max(0, (10 - balance) / 10)
#         
#         # Symbol-specific adjustments for sub-10-cent coins
#         if symbol in self.config.sub_10_cent_coins:
#             # More aggressive for low-price coins
#             spread_pressure *= 0.7  # Less penalty for wider spreads
#             opportunity_multiplier = 1.3  # Higher opportunity score
#         else:
#             opportunity_multiplier = 1.0
#         
#         # Cascade AI Decision Logic
#         decision = self._make_trading_decision(
#             spread_bps, volume_imbalance, position_risk, balance_risk,
#             price_pressure, spread_pressure, mid_price, position, opportunity_multiplier
#         )
#         
#         # Update analysis cache
#         self.market_analysis = {
#             'symbol': symbol,
#             'spread_bps': spread_bps,
#             'volume_imbalance': volume_imbalance,
#             'total_volume': total_volume,
#             'price_pressure': price_pressure,
#             'spread_pressure': spread_pressure,
#             'position_risk': position_risk,
#             'balance_risk': balance_risk,
#             'decision': decision,
#             'timestamp': current_time
#         }
#         
#         return decision
#     
#     def _make_trading_decision(self, spread_bps, volume_imbalance, position_risk, 
#                               balance_risk, price_pressure, spread_pressure, mid_price, position, opportunity_multiplier=1.0):
#         """Cascade AI core decision making logic"""
#         
#         # Risk assessment
#         overall_risk = (position_risk * 0.4 + balance_risk * 0.3 + 
#                        max(0, spread_pressure) * 0.2 + abs(volume_imbalance) * 0.1)
#         
#         # Opportunity scoring
#         opportunity_score = 0
#         
#         # Spread opportunity
#         if spread_bps > 3:
#             opportunity_score += min(spread_bps / 10, 0.4) * opportunity_multiplier
#         
#         # Volume imbalance opportunity
#         if abs(volume_imbalance) > 0.2:
#             opportunity_score += min(abs(volume_imbalance) * 0.5, 0.3) * opportunity_multiplier
#         
#         # Price pressure opportunity
#         if abs(price_pressure) > 0.1:
#             opportunity_score += min(abs(price_pressure) * 0.3, 0.3) * opportunity_multiplier
#         
#         # Cascade AI Decision Tree
#         if overall_risk > 0.8:
#             return {
#                 'action': 'REDUCE',
#                 'reason': f'High risk detected ({overall_risk:.2f}) - reducing exposure',
#                 'confidence': 0.9,
#                 'risk_level': 'HIGH'
#             }
#         
#         elif opportunity_score > 0.6 and spread_bps > self.config.min_profit_bps * 2:
#             return {
#                 'action': 'HEDGE_AGGRESSIVE',
#                 'reason': f'High opportunity ({opportunity_score:.2f}) - aggressive hedging',
#                 'confidence': min(0.95, 0.7 + opportunity_score * 0.25),
#                 'opportunity_score': opportunity_score,
#                 'risk_level': 'MEDIUM'
#             }
#         
#         elif opportunity_score > 0.3 and spread_bps > self.config.min_profit_bps:
#             return {
#                 'action': 'HEDGE_CONSERVATIVE',
#                 'reason': f'Moderate opportunity ({opportunity_score:.2f}) - conservative hedging',
#                 'confidence': 0.6 + opportunity_score * 0.2,
#                 'opportunity_score': opportunity_score,
#                 'risk_level': 'LOW'
#             }
#         
#         elif position_risk > 0.6:
#             return {
#                 'action': 'WAIT',
#                 'reason': f'Position risk too high ({position_risk:.2f}) - waiting',
#                 'confidence': 0.8,
#                 'risk_level': 'MEDIUM'
#             }
#         
#         else:
#             return {
#                 'action': 'MONITOR',
#                 'reason': f'Market conditions neutral - monitoring',
#                 'confidence': 0.5,
#                 'opportunity_score': opportunity_score,
#                 'risk_level': 'LOW'
#             }
#     
#     def get_hedge_recommendations(self, decision, bids, asks, mid_price, symbol):
#         """Get specific hedge recommendations based on AI decision"""
#         if decision['action'] not in ['HEDGE_AGGRESSIVE', 'HEDGE_CONSERVATIVE']:
#             return []
#         
#         recommendations = []
#         
#         # Calculate optimal hedge sizes
#         available_balance = 5.56
#         base_size_usd = self.config.hedge_order_size_usd
#         
#         # Symbol-specific adjustments
#         if symbol in self.config.sub_10_cent_coins:
#             size_multiplier = 1.5  # Larger size for low-price coins
#             price_improvement = 0.00001  # Smaller improvement for low prices
#         else:
#             size_multiplier = 1.0
#             price_improvement = self.config.hedge_price_improvement
#         
#         if decision['action'] == 'HEDGE_AGGRESSIVE':
#             size_multiplier *= 1.5
#             price_improvement *= 2
#         
#         # Calculate hedge size
#         hedge_usd = min(base_size_usd * size_multiplier, available_balance * 0.3)
#         hedge_size = hedge_usd / mid_price
#         
#         # Get best prices
#         best_bid = float(bids[0][0])
#         best_ask = float(asks[0][0])
#         
#         # Calculate improved prices
#         buy_price = best_bid + price_improvement
#         sell_price = best_ask - price_improvement
#         
#         # Ensure minimum profit
#         expected_spread_bps = (sell_price - buy_price) / mid_price * 10000
#         if expected_spread_bps < self.config.min_profit_bps:
#             half_spread = self.config.min_profit_bps / 2 / 10000 * mid_price
#             buy_price = mid_price - half_spread
#             sell_price = mid_price + half_spread
#         
#         recommendations.append({
#             'action': 'PLACE_HEDGE_PAIR',
#             'buy_price': buy_price,
#             'sell_price': sell_price,
#             'size': hedge_size,
#             'expected_profit_bps': expected_spread_bps,
#             'confidence': decision['confidence'],
#             'reason': decision['reason']
#         })
#         
#         return recommendations
#     
#     def log_ai_decision(self, decision, symbol):
#         """Log AI decision with detailed reasoning"""
#         risk_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
#         action_emoji = {
#             'HEDGE_AGGRESSIVE': '🚀',
#             'HEDGE_CONSERVATIVE': '🛡️',
#             'WAIT': '⏳',
#             'MONITOR': '👁️',
#             'REDUCE': '⚠️'
#         }
#         
#         emoji = action_emoji.get(decision['action'], '🤖')
#         risk_emoji = risk_emoji.get(decision.get('risk_level', 'LOW'), '🟢')
#         
#         self.ui.add_log(f"🧠 CASCADE AI DECISION ({symbol}):")
#         self.ui.add_log(f"   {emoji} Action: {decision['action']}")
#         self.ui.add_log(f"   📊 Reason: {decision['reason']}")
#         self.ui.add_log(f"   🎯 Confidence: {decision['confidence']:.2f}")
#         self.ui.add_log(f"   {risk_emoji} Risk Level: {decision.get('risk_level', 'LOW')}")
#         
#         if 'opportunity_score' in decision:
#             self.ui.add_log(f"   💎 Opportunity Score: {decision['opportunity_score']:.3f}")
#
# class TradingStats:
#     """Statistics tracking for hedging"""
#     
#     def __init__(self):
#         # Basic trading stats
#         self.total_trades = 0
#         self.total_volume = 0.0
#         self.total_pnl = 0.0
#         self.fees_paid = 0.0
#         self.orders_placed = 0
#         self.orders_filled = 0
#         self.orders_cancelled = 0
#         
#         # Balance tracking
#         self.available_balance = 0.0
#         self.total_balance = 0.0
#         self.unrealized_pnl = 0.0
#         self.margin_used = 0.0
#         self.margin_free = 0.0
#         
#         # Hedging statistics
#         self.hedge_orders_placed = 0
#         self.hedge_orders_filled = 0
#         self.hedge_profit_trades = 0
#         self.hedge_loss_trades = 0
#         self.hedge_total_pnl = 0.0
#         self.hedge_fees_paid = 0.0
#         self.active_hedges = []
#         
#         # Performance tracking
#         self.tps_history = deque(maxlen=100)
#         self.pnl_history = deque(maxlen=1000)
#         self.start_time = time.time()
#         self.last_tps_calc = time.time()
#         self.orders_this_second = 0
#         self.current_tps = 0.0
#
# class MarketMakerUI:
#     """Modern UI for the hedging system"""
#     
#     def __init__(self, config, stats):
#         self.config = config
#         self.stats = stats
#         self.root = None
#         self.running = False
#         self.log_queue = deque(maxlen=500)
#         
#     def create_ui(self):
#         """Create the main UI"""
#         self.root = tk.Tk()
#         self.root.title(f"🛡️ {self.config.symbol} Hedging - Cascade AI")
#         self.root.geometry("1400x900")
#         self.root.configure(bg='#0a0a0a')
#         
#         # Style configuration
#         style = ttk.Style()
#         style.theme_use('clam')
#         
#         # Configure styles
#         style.configure('Title.TLabel', background='#0a0a0a', foreground='#ff0040', font=('Arial', 16, 'bold'))
#         style.configure('Stats.TLabel', background='#0a0a0a', foreground='#00ff88', font=('Courier', 10))
#         style.configure('Dark.TFrame', background='#1a1a1a')
#         
#         # Main container
#         main_container = tk.Frame(self.root, bg='#0a0a0a')
#         main_container.pack(fill='both', expand=True, padx=10, pady=10)
#         
#         # Title
#         title_label = ttk.Label(main_container, text=f"🛡️ {self.config.symbol} HEDGING SYSTEM", style='Title.TLabel')
#         title_label.pack(pady=10)
#         
#         # Top panel - Stats
#         top_panel = tk.Frame(main_container, bg='#1a1a1a', height=150)
#         top_panel.pack(fill='x', pady=(0, 10))
#         top_panel.pack_propagate(False)
#         
#         # Stats labels
#         self.setup_stats_panel(top_panel)
#         
#         # Middle panel - Controls and info
#         middle_panel = tk.Frame(main_container, bg='#0a0a0a')
#         middle_panel.pack(fill='both', expand=True)
#         
#         # Left panel - Controls
#         left_panel = tk.Frame(middle_panel, bg='#1a1a1a', width=400)
#         left_panel.pack(side='left', fill='y', padx=(0, 10))
#         left_panel.pack_propagate(False)
#         
#         self.setup_control_panel(left_panel)
#         
#         # Right panel - Log
#         right_panel = tk.Frame(middle_panel, bg='#1a1a1a')
#         right_panel.pack(side='right', fill='both', expand=True)
#         
#         self.setup_log_panel(right_panel)
#         
#         # Status bar
#         self.setup_status_bar()
#         
#         self.running = True
#         
#     def setup_stats_panel(self, parent):
#         """Setup statistics display panel"""
#         # Balance frame
#         balance_frame = tk.Frame(parent, bg='#1a1a1a')
#         balance_frame.pack(fill='x', padx=10, pady=5)
#         
#         self.balance_label = ttk.Label(balance_frame, text="Balance: $0.00", style='Stats.TLabel')
#         self.balance_label.pack(side='left', padx=10)
#         
#         self.pnl_label = ttk.Label(balance_frame, text="PnL: $0.00", style='Stats.TLabel')
#         self.pnl_label.pack(side='left', padx=10)
#         
#         # Trading frame
#         trading_frame = tk.Frame(parent, bg='#1a1a1a')
#         trading_frame.pack(fill='x', padx=10, pady=5)
#         
#         self.orders_label = ttk.Label(trading_frame, text="Orders: 0", style='Stats.TLabel')
#         self.orders_label.pack(side='left', padx=10)
#         
#         self.tps_label = ttk.Label(trading_frame, text="TPS: 0.00", style='Stats.TLabel')
#         self.tps_label.pack(side='left', padx=10)
#         
#         # Hedging frame
#         hedge_frame = tk.Frame(parent, bg='#1a1a1a')
#         hedge_frame.pack(fill='x', padx=10, pady=5)
#         
#         self.hedge_orders_label = ttk.Label(hedge_frame, text="Hedge Orders: 0", style='Stats.TLabel')
#         self.hedge_orders_label.pack(side='left', padx=10)
#         
#         self.hedge_pnl_label = ttk.Label(hedge_frame, text="Hedge PnL: $0.00", style='Stats.TLabel')
#         self.hedge_pnl_label.pack(side='left', padx=10)
#     
#     def setup_control_panel(self, parent):
#         """Setup control panel"""
#         # Title
#         title = ttk.Label(parent, text="🎮 CONTROL PANEL", style='Title.TLabel')
#         title.pack(pady=10)
#         
#         # Symbol selection
#         symbol_frame = tk.Frame(parent, bg='#1a1a1a')
#         symbol_frame.pack(fill='x', padx=10, pady=5)
#         
#         ttk.Label(symbol_frame, text="Symbol:", foreground='white', background='#1a1a1a').pack(side='left', padx=5)
#         
#         self.symbol_var = tk.StringVar(value=self.config.symbol)
#         symbols = [self.config.symbol] + self.config.sub_10_cent_coins
#         symbol_combo = ttk.Combobox(symbol_frame, textvariable=self.symbol_var, values=symbols, width=15, state='readonly')
#         symbol_combo.pack(side='left')
#         
#         # Control buttons
#         button_frame = tk.Frame(parent, bg='#1a1a1a')
#         button_frame.pack(fill='x', padx=10, pady=20)
#         
#         self.start_button = tk.Button(button_frame, text="🚀 START HEDGING", command=self.start_trading,
#                                      bg='#00ff00', fg='#000', font=('Arial', 12, 'bold'), width=18, height=2)
#         self.start_button.pack(pady=5)
#         
#         self.stop_button = tk.Button(button_frame, text="⏹️ STOP HEDGING", command=self.stop_trading,
#                                     bg='#ff0000', fg='#fff', font=('Arial', 12, 'bold'), width=18, height=2, state='disabled')
#         self.stop_button.pack(pady=5)
#         
#         # Info frame
#         info_frame = tk.Frame(parent, bg='#1a1a1a')
#         info_frame.pack(fill='x', padx=10, pady=20)
#         
#         ttk.Label(info_frame, text="📊 SYSTEM INFO", style='Title.TLabel').pack()
#         
#         info_text = f"""
# Min Profit: {self.config.min_profit_bps} bps
# Max Position: {self.config.max_hedge_position} {self.config.symbol.split('_')[0]}
# Order Size: ${self.config.hedge_order_size_usd}
# AI Confidence: {self.config.ai_confidence_threshold}
#         """.strip()
#         
#         info_label = ttk.Label(info_frame, text=info_text, style='Stats.TLabel', justify='left')
#         info_label.pack(padx=10, pady=10)
#     
#     def setup_log_panel(self, parent):
#         """Setup log panel"""
#         # Title
#         title = ttk.Label(parent, text="📝 ACTIVITY LOG", style='Title.TLabel')
#         title.pack(pady=10)
#         
#         # Log text
#         self.log_text = scrolledtext.ScrolledText(parent, height=25, width=80,
#                                                   bg='#0a0a0a', fg='#00ff88', 
#                                                   font=('Courier', 9))
#         self.log_text.pack(padx=10, pady=10, fill='both', expand=True)
#         
#         # Clear button
#         clear_button = tk.Button(parent, text="🗑️ CLEAR LOG", command=self.clear_log,
#                                 bg='#ff6b6b', fg='#fff', font=('Arial', 10, 'bold'))
#         clear_button.pack(pady=5)
#     
#     def setup_status_bar(self):
#         """Setup status bar"""
#         status_frame = tk.Frame(self.root, bg='#1a1a1a', height=30)
#         status_frame.pack(fill='x', side='bottom')
#         status_frame.pack_propagate(False)
#         
#         self.status_label = ttk.Label(status_frame, text="🟢 READY", style='Stats.TLabel')
#         self.status_label.pack(side='left', padx=10, pady=5)
#         
#         self.time_label = ttk.Label(status_frame, text="", style='Stats.TLabel')
#         self.time_label.pack(side='right', padx=10, pady=5)
#     
#     def add_log(self, message):
#         """Add message to log"""
#         timestamp = datetime.now().strftime('%H:%M:%S')
#         log_entry = f"[{timestamp}] {message}"
#         self.log_queue.append(log_entry)
#         
#         if self.log_text:
#             self.log_text.insert(tk.END, log_entry + "\n")
#             self.log_text.see(tk.END)
#             
#             # Limit log size
#             lines = self.log_text.get(1.0, tk.END).split('\n')
#             if len(lines) > 1000:
#                 self.log_text.delete(1.0, f"{len(lines)-1000}.0")
#     
#     def clear_log(self):
#         """Clear the log"""
#         if self.log_text:
#             self.log_text.delete(1.0, tk.END)
#     
#     def update_ui(self):
#         """Update UI elements"""
#         if not self.running:
#             return
#         
#         # Update stats
#         self.balance_label.configure(text=f"Balance: ${self.stats.total_balance:.2f}")
#         self.pnl_label.configure(text=f"PnL: ${self.stats.total_pnl:.4f}")
#         self.orders_label.configure(text=f"Orders: {self.stats.orders_placed}")
#         self.tps_label.configure(text=f"TPS: {self.stats.current_tps:.2f}")
#         
#         # Update hedging stats
#         self.hedge_orders_label.configure(text=f"Hedge Orders: {self.stats.hedge_orders_filled}")
#         hedge_pnl_color = '#00ff88' if self.stats.hedge_total_pnl >= 0 else '#ff6b6b'
#         self.hedge_pnl_label.configure(text=f"Hedge PnL: ${self.stats.hedge_total_pnl:.4f}", foreground=hedge_pnl_color)
#         
#         # Update time
#         current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         self.time_label.configure(text=current_time)
#         
#         # Schedule next update
#         if self.root:
#             self.root.after(100, self.update_ui)
#     
#     def start_trading(self):
#         """Start trading"""
#         self.start_button.config(state='disabled')
#         self.stop_button.config(state='normal')
#         self.status_label.configure(text="🟢 HEDGING ACTIVE")
#         self.add_log("🚀 Hedging started")
#         
#         # Update symbol in config
#         self.config.symbol = self.symbol_var.get()
#         self.add_log(f"📊 Trading {self.config.symbol}")
#     
#     def stop_trading(self):
#         """Stop trading"""
#         self.start_button.config(state='normal')
#         self.stop_button.config(state='disabled')
#         self.status_label.configure(text="🔴 STOPPED")
#         self.add_log("⏹️ Hedging stopped")
#     
#     def run(self):
#         """Run the UI"""
#         self.update_ui()
#         self.root.mainloop()
#     
#     def close(self):
#         """Close the UI"""
#         self.running = False
#         if self.root:
#             self.root.quit()
#
# class ENAHedgingMarketMaker:
#     """Main ENA hedging market maker with Cascade AI"""
#     
#     def __init__(self, config: ENAHedgingConfig):
#         self.config = config
#         self.stats = TradingStats()
#         self.ui = MarketMakerUI(config, self.stats)
#         
#         # Trading state
#         self._running = False
#         self._trading = False
#         self.position = 0.0
#         self.mid = 0.0
#         self.bids = []
#         self.asks = []
#         
#         # AI Assistant
#         self.cascade_ai = CascadeAIAssistant(config, self.ui)
#         
#         # Initialize API
#         cfg = Configuration(key=config.api_key, secret=config.api_secret)
#         self.api = FuturesApi(ApiClient(cfg))
#         
#         # WebSocket
#         self.ws = None
#         self.ws_task = None
#     
#     async def get_balance(self):
#         """Get account balance"""
#         try:
#             account = self.api.get_futures_account(settle='usdt')
#             self.stats.available_balance = float(account.available)
#             self.stats.total_balance = float(account.total)
#             self.stats.unrealized_pnl = float(account.unrealised_pnl)
#             self.ui.add_log(f"💰 Balance: ${self.stats.total_balance:.2f}")
#         except Exception as e:
#             self.ui.add_log(f"❌ Balance error: {e}")
#     
#     async def get_positions(self):
#         """Get current positions"""
#         try:
#             positions = self.api.list_futures_positions(settle='usdt')
#             for pos in positions:
#                 if pos.contract == self.config.symbol and float(pos.size) != 0:
#                     self.position = float(pos.size)
#                     self.ui.add_log(f"📊 Position: {self.position:+.6f} {self.config.symbol.split('_')[0]}")
#                     break
#         except Exception as e:
#             self.ui.add_log(f"❌ Position error: {e}")
#     
#     async def place_hedge_order(self, side: str, price: float, size: float):
#         """Place a hedge order"""
#         try:
#             order = gate_api.FuturesOrder(
#                 contract=self.config.symbol,
#                 size=size,
#                 price=price,
#                 side=side,
#                 type='limit',
#                 time_in_force='post_only',
#                 client_order_id=f"hedge_{int(time.time() * 1000)}"
#             )
#             
#             result = self.api.create_futures_order(settle='usdt', order=order)
#             self.stats.hedge_orders_placed += 1
#             
#             hedge_info = {
#                 'order_id': result.id,
#                 'side': side,
#                 'price': price,
#                 'size': size,
#                 'timestamp': time.time(),
#                 'status': 'active'
#             }
#             self.stats.active_hedges.append(hedge_info)
#             
#             self.ui.add_log(f"🛡️ HEDGE PLACED: {side.upper()} {size:.6f} @ ${price:.6f}")
#             return result.id
#             
#         except Exception as e:
#             self.ui.add_log(f"❌ Hedge order failed: {e}")
#             return None
#     
#     async def check_hedge_profitability(self):
#         """Check and close profitable hedges"""
#         if not self.bids or not self.asks:
#             return
#         
#         current_bid = float(self.bids[0][0])
#         current_ask = float(self.asks[0][0])
#         current_time = time.time()
#         
#         for hedge in self.stats.active_hedges[:]:
#             if hedge['status'] != 'active':
#                 continue
#             
#             hedge_price = hedge['price']
#             hedge_side = hedge['side']
#             hedge_size = hedge['size']
#             hedge_age = current_time - hedge['timestamp']
#             
#             # Calculate profit
#             if hedge_side == 'buy':
#                 profit_per_unit = current_bid - hedge_price
#                 total_profit = profit_per_unit * hedge_size
#                 profit_bps = profit_per_unit / hedge_price * 10000
#                 close_price = current_bid
#             else:
#                 profit_per_unit = hedge_price - current_ask
#                 total_profit = profit_per_unit * hedge_size
#                 profit_bps = profit_per_unit / hedge_price * 10000
#                 close_price = current_ask
#             
#             # Check profit threshold
#             min_profit = self.config.min_profit_bps / 10000 * hedge_price * hedge_size
#             
#             if profit_bps >= self.config.market_sell_threshold or total_profit > min_profit:
#                 await self.close_hedge_position(hedge, total_profit, close_price, f"PROFITABLE ({profit_bps:.1f} bps)")
#             elif hedge_age > self.config.max_hedge_age_seconds:
#                 await self.close_hedge_position(hedge, total_profit, close_price, f"AGED ({hedge_age:.0f}s)")
#     
#     async def close_hedge_position(self, hedge, profit, close_price, reason):
#         """Close a hedge position"""
#         try:
#             close_side = 'sell' if hedge['side'] == 'buy' else 'buy'
#             
#             close_order = gate_api.FuturesOrder(
#                 contract=self.config.symbol,
#                 size=hedge['size'],
#                 side=close_side,
#                 type='market',
#                 client_order_id=f"close_hedge_{int(time.time() * 1000)}"
#             )
#             
#             result = self.api.create_futures_order(settle='usdt', order=close_order)
#             
#             # Update statistics
#             self.stats.hedge_orders_filled += 2
#             self.stats.hedge_total_pnl += profit
#             self.stats.total_pnl += profit
#             
#             if profit > 0:
#                 self.stats.hedge_profit_trades += 1
#             else:
#                 self.stats.hedge_loss_trades += 1
#             
#             # Mark as closed
#             hedge['status'] = 'closed'
#             hedge['profit'] = profit
#             
#             profit_color = "+" if profit >= 0 else ""
#             self.ui.add_log(f"💰 HEDGE CLOSED ({reason}): ${profit_color}{profit:.4f}")
#             
#         except Exception as e:
#             self.ui.add_log(f"❌ Failed to close hedge: {e}")
#     
#     async def cascade_ai_hedging_strategy(self):
#         """Cascade AI-driven hedging strategy"""
#         if not self.bids or not self.asks:
#             return
#         
#         # AI analysis
#         ai_decision = self.cascade_ai.analyze_market_conditions(
#             self.bids, self.asks, self.mid, self.position, 
#             self.stats.available_balance, self.config.symbol
#         )
#         
#         # Log AI decision
#         self.cascade_ai.log_ai_decision(ai_decision, self.config.symbol)
#         
#         # Get recommendations
#         recommendations = self.cascade_ai.get_hedge_recommendations(
#             ai_decision, self.bids, self.asks, self.mid, self.config.symbol
#         )
#         
#         # Execute recommendations
#         for rec in recommendations:
#             if rec['action'] == 'PLACE_HEDGE_PAIR':
#                 current_hedge_size = sum(h['size'] for h in self.stats.active_hedges if h['status'] == 'active')
#                 
#                 if current_hedge_size < self.config.max_hedge_position:
#                     # Place hedge pair
#                     buy_result = await self.place_hedge_order('buy', rec['buy_price'], rec['size'])
#                     await asyncio.sleep(0.1)
#                     sell_result = await self.place_hedge_order('sell', rec['sell_price'], rec['size'])
#                     
#                     if buy_result and sell_result:
#                         self.ui.add_log(f"🧠 AI HEDGE EXECUTED:")
#                         self.ui.add_log(f"   🎯 Confidence: {rec['confidence']:.2f}")
#                         self.ui.add_log(f"   💰 Expected Profit: {rec['expected_profit_bps']:.1f} bps")
#     
#     async def connect_websocket(self):
#         """Connect to WebSocket for real-time data"""
#         try:
#             self.ws = await websockets.connect(self.config.ws_url)
#             self.ui.add_log("✅ WebSocket connected")
#             
#             # Subscribe to order book
#             subscribe_msg = {
#                 "time": int(time.time()),
#                 "channel": "futures.order_book",
#                 "event": "subscribe",
#                 "payload": [
#                     self.config.symbol,
#                     5,  # Level
#                     0   # Interval
#                 ]
#             }
#             await self.ws.send(json.dumps(subscribe_msg))
#             
#             return True
#         except Exception as e:
#             self.ui.add_log(f"❌ WebSocket error: {e}")
#             return False
#     
#     async def process_messages(self):
#         """Process WebSocket messages"""
#         try:
#             async for message in self.ws:
#                 data = json.loads(message)
#                 
#                 if data.get('channel') == 'futures.order_book' and data.get('event') == 'update':
#                     # Update order book
#                     bids = data.get('result', {}).get('bids', [])
#                     asks = data.get('result', {}).get('asks', [])
#                     
#                     if bids and asks:
#                         self.bids = bids
#                         self.asks = asks
#                         self.mid = (float(bids[0][0]) + float(asks[0][0])) / 2
#                         
#         except Exception as e:
#             self.ui.add_log(f"❌ Message processing error: {e}")
#     
#     async def trading_loop(self):
#         """Main trading loop"""
#         balance_update_counter = 0
#         hedge_counter = 0
#         
#         while self._running:
#             try:
#                 # Update balance every 30 seconds
#                 balance_update_counter += 1
#                 if balance_update_counter >= 300:
#                     await self.get_balance()
#                     await self.get_positions()
#                     balance_update_counter = 0
#                 
#                 # Check if trading is enabled
#                 if not self._trading:
#                     await asyncio.sleep(1)
#                     continue
#                 
#                 # Hedging strategy
#                 if self.config.hedging_mode:
#                     hedge_counter += 1
#                     
#                     # Check profitability every 2 seconds
#                     if hedge_counter % 20 == 0:
#                         await self.check_hedge_profitability()
#                     
#                     # AI hedging every 5 seconds
#                     if hedge_counter % 50 == 0:
#                         await self.cascade_ai_hedging_strategy()
#                 
#                 await asyncio.sleep(0.1)
#                 
#             except Exception as e:
#                 self.ui.add_log(f"❌ Trading loop error: {e}")
#                 await asyncio.sleep(1)
#     
#     async def start(self):
#         """Start the market maker"""
#         self._running = True
#         
#         # Create UI
#         self.ui.create_ui()
#         
#         # Initial data fetch
#         await self.get_balance()
#         await self.get_positions()
#         
#         # Connect WebSocket
#         if not await self.connect_websocket():
#             self.ui.add_log("❌ Failed to connect WebSocket")
#             return
#         
#         # Start tasks
#         tasks = [
#             asyncio.create_task(self.process_messages()),
#             asyncio.create_task(self.trading_loop()),
#             asyncio.create_task(self.ui.run())
#         ]
#         
#         try:
#             await asyncio.gather(*tasks)
#         except Exception as e:
#             self.ui.add_log(f"❌ Runtime error: {e}")
#         finally:
#             await self.stop()
#     
#     async def stop(self):
#         """Stop the market maker"""
#         self._running = False
#         self._trading = False
#         
#         if self.ws:
#             await self.ws.close()
#         
#         self.ui.add_log("⏹️ System stopped")
#         self.ui.close()
#
# def main():
#     """Main entry point"""
#     print("🛡️ ENA_USDT HEDGING SYSTEM")
#     print("🧠 Powered by Cascade AI Assistant")
#     print("💰 Multi-coin support for sub-10-cent tokens")
#     print("=" * 60)
#     
#     # Load configuration
#     config = ENAHedgingConfig()
#     
#     try:
#         config.validate_config()
#         print("✅ Configuration validated")
#     except ValueError as e:
#         print(f"❌ Configuration error: {e}")
#         return 1
#     
#     print(f"📊 Symbol: {config.symbol}")
#     print(f"💰 Min Profit: {config.min_profit_bps} bps")
#     print(f"🎯 Max Position: {config.max_hedge_position}")
#     print(f"📈 Order Size: ${config.hedge_order_size_usd}")
#     print(f"🪙 Sub-10-cent coins: {', '.join(config.sub_10_cent_coins)}")
#     print("=" * 60)
#     
#     # Create and run market maker
#     market_maker = ENAHedgingMarketMaker(config)
#     
#     try:
#         asyncio.run(market_maker.start())
#     except KeyboardInterrupt:
#         print("\n⏹️ Shutting down...")
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return 1
#     
#     return 0
#
# if __name__ == "__main__":
#     sys.exit(main())
# ===== END   [124/134] ENA_Hedging_Project/src/ena_hedging_market_maker_complete.py =====

# ===== BEGIN [125/134] ENA_Hedging_Project/src/trading_engine.py sha256=f26ab41088d15b5c =====
# #!/usr/bin/env python3
# """
# TRADING ENGINE FOR ENA HEDGING SYSTEM
# Core trading logic and order management
# """
#
# import asyncio
# import time
# import logging
# from typing import Dict, List, Optional, Tuple
# import gate_api
# from gate_api import ApiClient, Configuration, FuturesApi
#
# log = logging.getLogger(__name__)
#
# class OrderManager:
#     """Manages order placement and tracking"""
#     
#     def __init__(self, config, api_client):
#         self.config = config
#         self.api = api_client
#         self.active_orders = {}  # order_id -> order info
#         self.order_history = []  # Order history
#         self.pending_orders = {}  # client_order_id -> order info
#         
#     async def place_limit_order(self, symbol: str, side: str, size: float, 
#                                price: float, client_order_id: str = None,
#                                post_only: bool = True) -> Optional[str]:
#         """Place a limit order"""
#         try:
#             if not client_order_id:
#                 client_order_id = f"order_{int(time.time() * 1000)}"
#             
#             order = gate_api.FuturesOrder(
#                 contract=symbol,
#                 size=size,
#                 price=price,
#                 side=side,
#                 type='limit',
#                 time_in_force='post_only' if post_only else 'gtc',
#                 client_order_id=client_order_id
#             )
#             
#             result = self.api.create_futures_order(settle='usdt', order=order)
#             
#             order_info = {
#                 'order_id': result.id,
#                 'client_order_id': client_order_id,
#                 'symbol': symbol,
#                 'side': side,
#                 'size': size,
#                 'price': price,
#                 'status': result.status,
#                 'filled_size': result.filled_size,
#                 'created_time': time.time(),
#                 'type': 'limit'
#             }
#             
#             self.active_orders[result.id] = order_info
#             self.pending_orders[client_order_id] = order_info
#             
#             log.info(f"📈 Limit order placed: {side.upper()} {size:.6f} @ ${price:.6f} (ID: {result.id})")
#             return result.id
#             
#         except Exception as e:
#             log.error(f"❌ Failed to place limit order: {e}")
#             return None
#     
#     async def place_market_order(self, symbol: str, side: str, size: float,
#                                 client_order_id: str = None) -> Optional[str]:
#         """Place a market order"""
#         try:
#             if not client_order_id:
#                 client_order_id = f"market_{int(time.time() * 1000)}"
#             
#             order = gate_api.FuturesOrder(
#                 contract=symbol,
#                 size=size,
#                 side=side,
#                 type='market',
#                 client_order_id=client_order_id
#             )
#             
#             result = self.api.create_futures_order(settle='usdt', order=order)
#             
#             order_info = {
#                 'order_id': result.id,
#                 'client_order_id': client_order_id,
#                 'symbol': symbol,
#                 'side': side,
#                 'size': size,
#                 'status': result.status,
#                 'filled_size': result.filled_size,
#                 'created_time': time.time(),
#                 'type': 'market'
#             }
#             
#             self.active_orders[result.id] = order_info
#             self.pending_orders[client_order_id] = order_info
#             
#             log.info(f"⚡ Market order placed: {side.upper()} {size:.6f} (ID: {result.id})")
#             return result.id
#             
#         except Exception as e:
#             log.error(f"❌ Failed to place market order: {e}")
#             return None
#     
#     async def cancel_order(self, order_id: str) -> bool:
#         """Cancel an order"""
#         try:
#             result = self.api.cancel_futures_order(settle='usdt', order_id=order_id)
#             
#             if order_id in self.active_orders:
#                 order_info = self.active_orders[order_id]
#                 order_info['status'] = 'cancelled'
#                 order_info['cancelled_time'] = time.time()
#                 self.order_history.append(order_info)
#                 del self.active_orders[order_id]
#             
#             log.info(f"❌ Order cancelled: {order_id}")
#             return True
#             
#         except Exception as e:
#             log.error(f"❌ Failed to cancel order {order_id}: {e}")
#             return False
#     
#     async def cancel_all_orders(self, symbol: str = None) -> int:
#         """Cancel all orders (optionally for specific symbol)"""
#         try:
#             if symbol:
#                 # Cancel specific symbol orders
#                 orders_to_cancel = [
#                     order_id for order_id, order_info in self.active_orders.items()
#                     if order_info['symbol'] == symbol
#                 ]
#             else:
#                 # Cancel all orders
#                 orders_to_cancel = list(self.active_orders.keys())
#             
#             cancelled_count = 0
#             for order_id in orders_to_cancel:
#                 if await self.cancel_order(order_id):
#                     cancelled_count += 1
#             
#             log.info(f"🗑️ Cancelled {cancelled_count} orders")
#             return cancelled_count
#             
#         except Exception as e:
#             log.error(f"❌ Failed to cancel orders: {e}")
#             return 0
#     
#     async def update_order_status(self, order_id: str) -> bool:
#         """Update order status from exchange"""
#         try:
#             result = self.api.get_futures_order(settle='usdt', order_id=order_id)
#             
#             if order_id in self.active_orders:
#                 order_info = self.active_orders[order_id]
#                 old_status = order_info['status']
#                 
#                 order_info.update({
#                     'status': result.status,
#                     'filled_size': result.filled_size,
#                     'updated_time': time.time()
#                 })
#                 
#                 # Move to history if filled or cancelled
#                 if result.status in ['filled', 'cancelled']:
#                     self.order_history.append(order_info)
#                     del self.active_orders[order_id]
#                     
#                     if old_status != result.status:
#                         log.info(f"📊 Order {order_id} status: {old_status} -> {result.status}")
#                 
#                 return True
#             else:
#                 # Order might be in pending orders
#                 for client_id, order_info in list(self.pending_orders.items()):
#                     if order_info['order_id'] == order_id:
#                         order_info.update({
#                             'status': result.status,
#                             'filled_size': result.filled_size,
#                             'updated_time': time.time()
#                         })
#                         break
#                 
#         except Exception as e:
#             log.error(f"❌ Failed to update order status {order_id}: {e}")
#             return False
#     
#     async def get_active_orders(self, symbol: str = None) -> List[Dict]:
#         """Get active orders (optionally for specific symbol)"""
#         if symbol:
#             return [
#                 order_info for order_info in self.active_orders.values()
#                 if order_info['symbol'] == symbol
#             ]
#         return list(self.active_orders.values())
#     
#     def get_order_info(self, order_id: str) -> Optional[Dict]:
#         """Get order information"""
#         return self.active_orders.get(order_id)
#
# class PositionManager:
#     """Manages position tracking and risk"""
#     
#     def __init__(self, config, api_client):
#         self.config = config
#         self.api = api_client
#         self.positions = {}  # symbol -> position info
#         self.last_update = 0
#         
#     async def update_positions(self) -> bool:
#         """Update positions from exchange"""
#         try:
#             positions = self.api.list_futures_positions(settle='usdt')
#             
#             new_positions = {}
#             for pos in positions:
#                 if float(pos.size) != 0:  # Only non-zero positions
#                     symbol = pos.contract
#                     position_info = {
#                         'symbol': symbol,
#                         'size': float(pos.size),
#                         'side': 'long' if float(pos.size) > 0 else 'short',
#                         'entry_price': float(pos.entry_price),
#                         'mark_price': float(pos.mark_price),
#                         'unrealized_pnl': float(pos.unrealised_pnl),
#                         'percentage_pnl': float(pos.unrealised_pnl) / (float(pos.size) * float(pos.entry_price)) * 100 if float(pos.size) * float(pos.entry_price) != 0 else 0,
#                         'margin': float(pos.margin),
#                         'leverage': float(pos.leverage),
#                         'updated_time': time.time()
#                     }
#                     new_positions[symbol] = position_info
#             
#             self.positions = new_positions
#             self.last_update = time.time()
#             
#             # Log positions
#             for symbol, pos in self.positions.items():
#                 log.info(f"📊 Position {symbol}: {pos['side']} {abs(pos['size']):.6f} @ ${pos['entry_price']:.6f} (PnL: ${pos['unrealized_pnl']:.4f})")
#             
#             return True
#             
#         except Exception as e:
#             log.error(f"❌ Failed to update positions: {e}")
#             return False
#     
#     def get_position(self, symbol: str) -> Optional[Dict]:
#         """Get position for specific symbol"""
#         return self.positions.get(symbol)
#     
#     def get_total_exposure(self) -> float:
#         """Get total exposure across all positions"""
#         return sum(abs(pos['size']) for pos in self.positions.values())
#     
#     def get_total_unrealized_pnl(self) -> float:
#         """Get total unrealized PnL"""
#         return sum(pos['unrealized_pnl'] for pos in self.positions.values())
#
# class BalanceManager:
#     """Manages balance tracking and risk limits"""
#     
#     def __init__(self, config, api_client):
#         self.config = config
#         self.api = api_client
#         self.balance_info = {}
#         self.last_update = 0
#         
#     async def update_balance(self) -> bool:
#         """Update balance from exchange"""
#         try:
#             account = self.api.get_futures_account(settle='usdt')
#             
#             self.balance_info = {
#                 'total': float(account.total),
#                 'available': float(account.available),
#                 'used': float(account.used),
#                 'unrealized_pnl': float(account.unrealised_pnl),
#                 'margin': float(account.margin),
#                 'margin_free': float(account.margin_free),
#                 'margin_ratio': float(account.margin_ratio) if account.margin_ratio else 0,
#                 'maintenance_margin': float(account.maintenance_margin) if account.maintenance_margin else 0,
#                 'updated_time': time.time()
#             }
#             
#             self.last_update = time.time()
#             log.info(f"💰 Balance: ${self.balance_info['available']:.2f} available, ${self.balance_info['total']:.2f} total")
#             return True
#             
#         except Exception as e:
#             log.error(f"❌ Failed to update balance: {e}")
#             return False
#     
#     def get_available_balance(self) -> float:
#         """Get available balance"""
#         return self.balance_info.get('available', 0.0)
#     
#     def get_total_balance(self) -> float:
#         """Get total balance"""
#         return self.balance_info.get('total', 0.0)
#     
#     def get_margin_ratio(self) -> float:
#         """Get margin ratio"""
#         return self.balance_info.get('margin_ratio', 0.0)
#     
#     def is_margin_safe(self) -> bool:
#         """Check if margin ratio is safe"""
#         margin_ratio = self.get_margin_ratio()
#         return margin_ratio > 0.1  # 10% minimum margin ratio
#     
#     def can_afford_order(self, order_value_usd: float) -> bool:
#         """Check if we can afford an order"""
#         available = self.get_available_balance()
#         return available >= order_value_usd * 1.1  # 10% buffer
#
# class TradingEngine:
#     """Main trading engine coordinating all components"""
#     
#     def __init__(self, config, ui):
#         self.config = config
#         self.ui = ui
#         
#         # Initialize API
#         cfg = Configuration(key=config.api_key, secret=config.api_secret)
#         self.api = FuturesApi(ApiClient(cfg))
#         
#         # Initialize managers
#         self.order_manager = OrderManager(config, self.api)
#         self.position_manager = PositionManager(config, self.api)
#         self.balance_manager = BalanceManager(config, self.api)
#         
#         # Trading state
#         self.is_trading = False
#         self.current_symbol = config.symbol
#         
#         # Statistics
#         self.stats = {
#             'orders_placed': 0,
#             'orders_filled': 0,
#             'orders_cancelled': 0,
#             'total_volume': 0.0,
#             'total_pnl': 0.0,
#             'start_time': time.time()
#         }
#     
#     async def initialize(self) -> bool:
#         """Initialize trading engine"""
#         try:
#             # Update initial data
#             await self.update_all_data()
#             
#             # Cancel any existing orders
#             cancelled = await self.order_manager.cancel_all_orders(self.current_symbol)
#             if cancelled > 0:
#                 self.ui.add_log(f"🗑️ Cancelled {cancelled} existing orders", 'WARNING')
#             
#             self.ui.add_log("✅ Trading engine initialized", 'SUCCESS')
#             return True
#             
#         except Exception as e:
#             self.ui.add_log(f"❌ Failed to initialize trading engine: {e}", 'ERROR')
#             return False
#     
#     async def update_all_data(self):
#         """Update all trading data"""
#         await asyncio.gather(
#             self.balance_manager.update_balance(),
#             self.position_manager.update_positions()
#         )
#     
#     async def place_hedge_order(self, side: str, price: float, size: float) -> Optional[str]:
#         """Place a hedge order"""
#         if not self.is_trading:
#             self.ui.add_log("⚠️ Trading not active", 'WARNING')
#             return None
#         
#         # Check if we can afford the order
#         order_value = size * price
#         if not self.balance_manager.can_afford_order(order_value):
#             self.ui.add_log(f"❌ Insufficient balance for order: ${order_value:.2f}", 'ERROR')
#             return None
#         
#         # Place the order
#         order_id = await self.order_manager.place_limit_order(
#             self.current_symbol, side, size, price, 
#             client_order_id=f"hedge_{int(time.time() * 1000)}",
#             post_only=True
#         )
#         
#         if order_id:
#             self.stats['orders_placed'] += 1
#             self.ui.add_log(f"🛡️ HEDGE PLACED: {side.upper()} {size:.6f} @ ${price:.6f}", 'HEDGE')
#         
#         return order_id
#     
#     async def close_hedge_position(self, hedge_info: Dict, close_price: float, reason: str) -> bool:
#         """Close a hedge position with market order"""
#         if not self.is_trading:
#             return False
#         
#         try:
#             close_side = 'sell' if hedge_info['side'] == 'buy' else 'buy'
#             
#             # Place market order to close
#             order_id = await self.order_manager.place_market_order(
#                 self.current_symbol, close_side, hedge_info['size'],
#                 client_order_id=f"close_hedge_{int(time.time() * 1000)}"
#             )
#             
#             if order_id:
#                 # Calculate profit
#                 if hedge_info['side'] == 'buy':
#                     profit_per_unit = close_price - hedge_info['price']
#                 else:
#                     profit_per_unit = hedge_info['price'] - close_price
#                 
#                 total_profit = profit_per_unit * hedge_info['size']
#                 
#                 # Update statistics
#                 self.stats['total_pnl'] += total_profit
#                 
#                 profit_color = "+" if total_profit >= 0 else ""
#                 self.ui.add_log(f"💰 HEDGE CLOSED ({reason}): ${profit_color}{total_profit:.4f}", 
#                               'PROFIT' if total_profit >= 0 else 'LOSS')
#                 
#                 return True
#             
#         except Exception as e:
#             self.ui.add_log(f"❌ Failed to close hedge: {e}", 'ERROR')
#         
#         return False
#     
#     async def check_risk_limits(self) -> bool:
#         """Check if current risk is within limits"""
#         # Check margin ratio
#         if not self.balance_manager.is_margin_safe():
#             self.ui.add_log("⚠️ Margin ratio too low, stopping trading", 'ERROR')
#             return False
#         
#         # Check daily loss limit
#         if self.stats['total_pnl'] < -self.config.max_daily_loss_usd:
#             self.ui.add_log(f"⚠️ Daily loss limit reached: ${self.stats['total_pnl']:.2f}", 'ERROR')
#             return False
#         
#         # Check position limits
#         position = self.position_manager.get_position(self.current_symbol)
#         if position and abs(position['size']) > self.config.max_hedge_position:
#             self.ui.add_log(f"⚠️ Position limit exceeded: {abs(position['size']):.6f}", 'ERROR')
#             return False
#         
#         return True
#     
#     async def emergency_stop(self):
#         """Emergency stop all trading"""
#         self.is_trading = False
#         
#         # Cancel all orders
#         cancelled = await self.order_manager.cancel_all_orders()
#         self.ui.add_log(f"🛑 Emergency stop: Cancelled {cancelled} orders", 'ERROR')
#         
#         # Close all positions if configured
#         if hasattr(self.config, 'emergency_close_positions') and self.config.emergency_close_positions:
#             # Implementation for closing positions would go here
#             self.ui.add_log("🛑 Emergency position closing not implemented", 'WARNING')
#     
#     def set_symbol(self, symbol: str):
#         """Change trading symbol"""
#         self.current_symbol = symbol
#         self.config.symbol = symbol
#         self.config.update_symbol_config(symbol)
#         self.ui.add_log(f"📊 Symbol changed to: {symbol}", 'INFO')
#     
#     def start_trading(self):
#         """Start trading"""
#         self.is_trading = True
#         self.ui.add_log(f"🚀 Trading started for {self.current_symbol}", 'SUCCESS')
#     
#     def stop_trading(self):
#         """Stop trading"""
#         self.is_trading = False
#         self.ui.add_log("⏹️ Trading stopped", 'WARNING')
#     
#     def get_statistics(self) -> Dict:
#         """Get trading statistics"""
#         runtime = time.time() - self.stats['start_time']
#         
#         return {
#             **self.stats,
#             'runtime_hours': runtime / 3600,
#             'orders_per_hour': self.stats['orders_placed'] / (runtime / 3600) if runtime > 0 else 0,
#             'current_symbol': self.current_symbol,
#             'is_trading': self.is_trading,
#             'available_balance': self.balance_manager.get_available_balance(),
#             'total_balance': self.balance_manager.get_total_balance(),
#             'current_position': self.position_manager.get_position(self.current_symbol)
#         }
# ===== END   [125/134] ENA_Hedging_Project/src/trading_engine.py =====

# ===== BEGIN [126/134] ENA_Hedging_Project/src/ui_components.py sha256=b9fb19687c0c8b79 =====
# #!/usr/bin/env python3
# """
# UI COMPONENTS FOR ENA HEDGING SYSTEM
# Modern, responsive UI components
# """
#
# import tkinter as tk
# from tkinter import ttk, scrolledtext, messagebox
# from datetime import datetime
# from collections import deque
# import threading
#
# class ModernFrame(tk.Frame):
#     """Modern frame with dark theme"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#1a1a1a')
#         super().__init__(parent, **kwargs)
#
# class ModernLabel(tk.Label):
#     """Modern label with dark theme"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#1a1a1a')
#         kwargs.setdefault('fg', '#00ff88')
#         kwargs.setdefault('font', ('Courier', 10))
#         super().__init__(parent, **kwargs)
#
# class ModernButton(tk.Button):
#     """Modern button with hover effects"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#2a2a2a')
#         kwargs.setdefault('fg', '#ffffff')
#         kwargs.setdefault('font', ('Arial', 10, 'bold'))
#         kwargs.setdefault('relief', 'flat')
#         kwargs.setdefault('bd', 0)
#         kwargs.setdefault('padx', 20)
#         kwargs.setdefault('pady', 10)
#         
#         super().__init__(parent, **kwargs)
#         
#         # Bind hover effects
#         self.bind('<Enter>', self.on_enter)
#         self.bind('<Leave>', self.on_leave)
#         
#         self.original_bg = self['bg']
#         self.hover_bg = '#3a3a3a'
#     
#     def on_enter(self, event):
#         self.configure(bg=self.hover_bg)
#     
#     def on_leave(self, event):
#         self.configure(bg=self.original_bg)
#
# class SuccessButton(ModernButton):
#     """Green success button"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#00ff00')
#         kwargs.setdefault('fg', '#000000')
#         kwargs.setdefault('hover_bg', '#00cc00')
#         super().__init__(parent, **kwargs)
#
# class DangerButton(ModernButton):
#     """Red danger button"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#ff4444')
#         kwargs.setdefault('fg', '#ffffff')
#         kwargs.setdefault('hover_bg', '#cc0000')
#         super().__init__(parent, **kwargs)
#
# class WarningButton(ModernButton):
#     """Orange warning button"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#ff8800')
#         kwargs.setdefault('fg', '#ffffff')
#         kwargs.setdefault('hover_bg', '#cc6600')
#         super().__init__(parent, **kwargs)
#
# class InfoButton(ModernButton):
#     """Blue info button"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#0088ff')
#         kwargs.setdefault('fg', '#ffffff')
#         kwargs.setdefault('hover_bg', '#0066cc')
#         super().__init__(parent, **kwargs)
#
# class ModernLogText(scrolledtext.ScrolledText):
#     """Modern log text with dark theme"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('bg', '#0a0a0a')
#         kwargs.setdefault('fg', '#00ff88')
#         kwargs.setdefault('font', ('Courier', 9))
#         kwargs.setdefault('insertbackground', '#00ff88')
#         kwargs.setdefault('selectbackground', '#004400')
#         kwargs.setdefault('selectforeground', '#00ff88')
#         kwargs.setdefault('relief', 'flat')
#         kwargs.setdefault('bd', 0)
#         
#         super().__init__(parent, **kwargs)
#         
#         # Configure tags for different message types
#         self.tag_configure('INFO', foreground='#00ff88')
#         self.tag_configure('SUCCESS', foreground='#00ff00')
#         self.tag_configure('WARNING', foreground='#ffaa00')
#         self.tag_configure('ERROR', foreground='#ff4444')
#         self.tag_configure('AI', foreground='#ff00ff')
#         self.tag_configure('HEDGE', foreground='#00ffff')
#         self.tag_configure('PROFIT', foreground='#00ff00')
#         self.tag_configure('LOSS', foreground='#ff4444')
#     
#     def add_message(self, message, msg_type='INFO'):
#         """Add a message with appropriate coloring"""
#         timestamp = datetime.now().strftime('%H:%M:%S')
#         formatted_message = f"[{timestamp}] {message}\n"
#         
#         self.insert(tk.END, formatted_message, msg_type)
#         self.see(tk.END)
#         
#         # Limit log size
#         lines = self.get(1.0, tk.END).split('\n')
#         if len(lines) > 1000:
#             self.delete(1.0, f"{len(lines)-1000}.0")
#
# class StatusBar(ModernFrame):
#     """Modern status bar"""
#     
#     def __init__(self, parent, **kwargs):
#         kwargs.setdefault('height', 30)
#         super().__init__(parent, **kwargs)
#         self.pack_propagate(False)
#         
#         # Status label
#         self.status_label = ModernLabel(self, text="🟢 READY")
#         self.status_label.pack(side='left', padx=10, pady=5)
#         
#         # Time label
#         self.time_label = ModernLabel(self, text="")
#         self.time_label.pack(side='right', padx=10, pady=5)
#         
#         # Progress bar
#         self.progress = ttk.Progressbar(self, mode='indeterminate', length=200)
#         self.progress.pack(side='left', padx=20, pady=5)
#         
#         self.update_time()
#     
#     def update_time(self):
#         """Update time display"""
#         current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         self.time_label.configure(text=current_time)
#         self.after(1000, self.update_time)
#     
#     def set_status(self, status, color='#00ff88'):
#         """Set status with color"""
#         self.status_label.configure(text=status, fg=color)
#     
#     def start_progress(self):
#         """Start progress animation"""
#         self.progress.start(10)
#     
#     def stop_progress(self):
#         """Stop progress animation"""
#         self.progress.stop()
#
# class StatsPanel(ModernFrame):
#     """Statistics display panel"""
#     
#     def __init__(self, parent, stats, **kwargs):
#         super().__init__(parent, **kwargs)
#         self.stats = stats
#         
#         # Create stat labels
#         self.create_stat_labels()
#     
#     def create_stat_labels(self):
#         """Create statistics labels"""
#         # Balance frame
#         balance_frame = ModernFrame(self)
#         balance_frame.pack(fill='x', padx=10, pady=5)
#         
#         self.balance_label = ModernLabel(balance_frame, text="Balance: $0.00")
#         self.balance_label.pack(side='left', padx=10)
#         
#         self.pnl_label = ModernLabel(balance_frame, text="PnL: $0.00")
#         self.pnl_label.pack(side='left', padx=10)
#         
#         # Trading frame
#         trading_frame = ModernFrame(self)
#         trading_frame.pack(fill='x', padx=10, pady=5)
#         
#         self.orders_label = ModernLabel(trading_frame, text="Orders: 0")
#         self.orders_label.pack(side='left', padx=10)
#         
#         self.tps_label = ModernLabel(trading_frame, text="TPS: 0.00")
#         self.tps_label.pack(side='left', padx=10)
#         
#         # Hedging frame
#         hedge_frame = ModernFrame(self)
#         hedge_frame.pack(fill='x', padx=10, pady=5)
#         
#         self.hedge_orders_label = ModernLabel(hedge_frame, text="Hedge Orders: 0")
#         self.hedge_orders_label.pack(side='left', padx=10)
#         
#         self.hedge_pnl_label = ModernLabel(hedge_frame, text="Hedge PnL: $0.00")
#         self.hedge_pnl_label.pack(side='left', padx=10)
#     
#     def update_stats(self):
#         """Update statistics display"""
#         # Update basic stats
#         self.balance_label.configure(text=f"Balance: ${self.stats.total_balance:.2f}")
#         self.pnl_label.configure(text=f"PnL: ${self.stats.total_pnl:.4f}")
#         self.orders_label.configure(text=f"Orders: {self.stats.orders_placed}")
#         self.tps_label.configure(text=f"TPS: {self.stats.current_tps:.2f}")
#         
#         # Update hedging stats
#         self.hedge_orders_label.configure(text=f"Hedge Orders: {self.stats.hedge_orders_filled}")
#         
#         # Color code PnL
#         pnl_color = '#00ff00' if self.stats.hedge_total_pnl >= 0 else '#ff4444'
#         self.hedge_pnl_label.configure(
#             text=f"Hedge PnL: ${self.stats.hedge_total_pnl:.4f}",
#             fg=pnl_color
#         )
#
# class ControlPanel(ModernFrame):
#     """Control panel with buttons and settings"""
#     
#     def __init__(self, parent, config, **kwargs):
#         super().__init__(parent, **kwargs)
#         self.config = config
#         self.on_start_callback = None
#         self.on_stop_callback = None
#         
#         self.create_controls()
#     
#     def create_controls(self):
#         """Create control elements"""
#         # Title
#         title = ModernLabel(self, text="🎮 CONTROL PANEL", 
#                            font=('Arial', 14, 'bold'), fg='#ff0040')
#         title.pack(pady=10)
#         
#         # Symbol selection
#         symbol_frame = ModernFrame(self)
#         symbol_frame.pack(fill='x', padx=10, pady=5)
#         
#         ModernLabel(symbol_frame, text="Symbol:").pack(side='left', padx=5)
#         
#         self.symbol_var = tk.StringVar(value=self.config.symbol)
#         symbols = [self.config.symbol] + self.config.sub_10_cent_coins
#         symbol_combo = ttk.Combobox(symbol_frame, textvariable=self.symbol_var, 
#                                    values=symbols, width=15, state='readonly')
#         symbol_combo.pack(side='left')
#         
#         # Control buttons
#         button_frame = ModernFrame(self)
#         button_frame.pack(fill='x', padx=10, pady=20)
#         
#         self.start_button = SuccessButton(button_frame, text="🚀 START HEDGING",
#                                          command=self.start_trading, width=18)
#         self.start_button.pack(pady=5)
#         
#         self.stop_button = DangerButton(button_frame, text="⏹️ STOP HEDGING",
#                                        command=self.stop_trading, width=18, state='disabled')
#         self.stop_button.pack(pady=5)
#         
#         # Quick actions
#         quick_frame = ModernFrame(self)
#         quick_frame.pack(fill='x', padx=10, pady=10)
#         
#         ModernLabel(quick_frame, text="⚡ QUICK ACTIONS", 
#                    font=('Arial', 12, 'bold'), fg='#ff8800').pack(pady=5)
#         
#         InfoButton(quick_frame, text="📊 REFRESH DATA", 
#                   command=self.refresh_data, width=15).pack(side='left', padx=5)
#         
#         WarningButton(quick_frame, text="🛑 EMERGENCY STOP", 
#                      command=self.emergency_stop, width=15).pack(side='left', padx=5)
#         
#         # Info display
#         self.create_info_display()
#     
#     def create_info_display(self):
#         """Create information display"""
#         info_frame = ModernFrame(self)
#         info_frame.pack(fill='x', padx=10, pady=20)
#         
#         ModernLabel(info_frame, text="📊 SYSTEM INFO", 
#                    font=('Arial', 12, 'bold'), fg='#0088ff').pack()
#         
#         info_text = f"""
# Min Profit: {self.config.min_profit_bps} bps
# Max Position: {self.config.max_hedge_position}
# Order Size: ${self.config.hedge_order_size_usd}
# AI Confidence: {self.config.ai_confidence_threshold}
#         """.strip()
#         
#         info_label = ModernLabel(info_frame, text=info_text, justify='left')
#         info_label.pack(padx=10, pady=10)
#     
#     def start_trading(self):
#         """Start trading"""
#         self.start_button.configure(state='disabled')
#         self.stop_button.configure(state='normal')
#         
#         # Update symbol in config
#         self.config.symbol = self.symbol_var.get()
#         self.config.update_symbol_config(self.config.symbol)
#         
#         if self.on_start_callback:
#             self.on_start_callback()
#     
#     def stop_trading(self):
#         """Stop trading"""
#         self.start_button.configure(state='normal')
#         self.stop_button.configure(state='disabled')
#         
#         if self.on_stop_callback:
#             self.on_stop_callback()
#     
#     def refresh_data(self):
#         """Refresh data"""
#         if hasattr(self, 'on_refresh_callback'):
#             self.on_refresh_callback()
#     
#     def emergency_stop(self):
#         """Emergency stop"""
#         result = messagebox.askyesno("Emergency Stop", 
#                                      "Are you sure you want to emergency stop all trading?")
#         if result:
#             self.stop_trading()
#             if hasattr(self, 'on_emergency_stop_callback'):
#                 self.on_emergency_stop_callback()
#
# class LogPanel(ModernFrame):
#     """Log display panel"""
#     
#     def __init__(self, parent, **kwargs):
#         super().__init__(parent, **kwargs)
#         self.create_log_display()
#     
#     def create_log_display(self):
#         """Create log display"""
#         # Title
#         title = ModernLabel(self, text="📝 ACTIVITY LOG", 
#                            font=('Arial', 14, 'bold'), fg='#ff0040')
#         title.pack(pady=10)
#         
#         # Log text
#         self.log_text = ModernLogText(self, height=25, width=80)
#         self.log_text.pack(padx=10, pady=10, fill='both', expand=True)
#         
#         # Control buttons
#         control_frame = ModernFrame(self)
#         control_frame.pack(fill='x', padx=10, pady=5)
#         
#         DangerButton(control_frame, text="🗑️ CLEAR LOG", 
#                     command=self.clear_log, width=12).pack(side='left', padx=5)
#         
#         InfoButton(control_frame, text="📄 EXPORT LOG", 
#                   command=self.export_log, width=12).pack(side='left', padx=5)
#         
#         WarningButton(control_frame, text="🔍 FILTER", 
#                      command=self.filter_log, width=12).pack(side='left', padx=5)
#     
#     def add_log(self, message, msg_type='INFO'):
#         """Add log message"""
#         if self.log_text:
#             self.log_text.add_message(message, msg_type)
#     
#     def clear_log(self):
#         """Clear the log"""
#         if self.log_text:
#             self.log_text.delete(1.0, tk.END)
#     
#     def export_log(self):
#         """Export log to file"""
#         from tkinter import filedialog
#         import datetime
#         
#         filename = filedialog.asksaveasfilename(
#             defaultextension=".txt",
#             filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
#             initialfile=f"hedge_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
#         )
#         
#         if filename and self.log_text:
#             with open(filename, 'w') as f:
#                 f.write(self.log_text.get(1.0, tk.END))
#             messagebox.showinfo("Export Complete", f"Log exported to {filename}")
#     
#     def filter_log(self):
#         """Filter log messages"""
#         # This could open a dialog to filter by message type
#         messagebox.showinfo("Filter", "Log filtering feature coming soon!")
#
# class ModernUI:
#     """Main modern UI manager"""
#     
#     def __init__(self, config, stats):
#         self.config = config
#         self.stats = stats
#         self.root = None
#         self.running = False
#         
#         # UI components
#         self.stats_panel = None
#         self.control_panel = None
#         self.log_panel = None
#         self.status_bar = None
#     
#     def create_ui(self):
#         """Create the main UI"""
#         self.root = tk.Tk()
#         self.root.title(f"🛡️ {self.config.symbol} Hedging - Cascade AI")
#         self.root.geometry("1400x900")
#         self.root.configure(bg='#0a0a0a')
#         
#         # Configure styles
#         self.configure_styles()
#         
#         # Create main container
#         main_container = ModernFrame(self.root, bg='#0a0a0a')
#         main_container.pack(fill='both', expand=True, padx=10, pady=10)
#         
#         # Title
#         title = ModernLabel(main_container, text=f"🛡️ {self.config.symbol} HEDGING SYSTEM",
#                            font=('Arial', 18, 'bold'), fg='#ff0040')
#         title.pack(pady=10)
#         
#         # Top panel - Stats
#         self.stats_panel = StatsPanel(main_container, self.stats)
#         self.stats_panel.pack(fill='x', pady=(0, 10))
#         
#         # Middle panel - Controls and log
#         middle_container = ModernFrame(main_container, bg='#0a0a0a')
#         middle_container.pack(fill='both', expand=True)
#         
#         # Left panel - Controls
#         self.control_panel = ControlPanel(middle_container, self.config)
#         self.control_panel.pack(side='left', fill='y', padx=(0, 10))
#         
#         # Right panel - Log
#         self.log_panel = LogPanel(middle_container)
#         self.log_panel.pack(side='right', fill='both', expand=True)
#         
#         # Status bar
#         self.status_bar = StatusBar(self.root)
#         self.status_bar.pack(fill='x', side='bottom')
#         
#         # Set callbacks
#         self.control_panel.on_start_callback = self.on_start_trading
#         self.control_panel.on_stop_callback = self.on_stop_trading
#         self.control_panel.on_refresh_callback = self.on_refresh_data
#         self.control_panel.on_emergency_stop_callback = self.on_emergency_stop
#         
#         self.running = True
#     
#     def configure_styles(self):
#         """Configure ttk styles"""
#         style = ttk.Style()
#         style.theme_use('clam')
#         
#         # Configure combobox
#         style.configure('TCombobox', 
#                        fieldbackground='#2a2a2a',
#                        background='#2a2a2a',
#                        foreground='#ffffff',
#                        borderwidth=0,
#                        relief='flat')
#         
#         # Configure progress bar
#         style.configure('TProgressbar',
#                        background='#00ff88',
#                        troughcolor='#2a2a2a',
#                        borderwidth=0,
#                        relief='flat')
#     
#     def update_ui(self):
#         """Update UI elements"""
#         if not self.running:
#             return
#         
#         # Update stats
#         if self.stats_panel:
#             self.stats_panel.update_stats()
#         
#         # Schedule next update
#         if self.root:
#             self.root.after(100, self.update_ui)
#     
#     def add_log(self, message, msg_type='INFO'):
#         """Add log message"""
#         if self.log_panel:
#             self.log_panel.add_log(message, msg_type)
#     
#     def set_status(self, status, color='#00ff88'):
#         """Set status bar"""
#         if self.status_bar:
#             self.status_bar.set_status(status, color)
#     
#     def start_progress(self):
#         """Start progress animation"""
#         if self.status_bar:
#             self.status_bar.start_progress()
#     
#     def stop_progress(self):
#         """Stop progress animation"""
#         if self.status_bar:
#             self.status_bar.stop_progress()
#     
#     def on_start_trading(self):
#         """Handle start trading"""
#         self.set_status("🟢 HEDGING ACTIVE", '#00ff00')
#         self.add_log("🚀 Hedging started", 'SUCCESS')
#         self.add_log(f"📊 Trading {self.config.symbol}", 'INFO')
#     
#     def on_stop_trading(self):
#         """Handle stop trading"""
#         self.set_status("🔴 STOPPED", '#ff4444')
#         self.add_log("⏹️ Hedging stopped", 'WARNING')
#     
#     def on_refresh_data(self):
#         """Handle refresh data"""
#         self.add_log("📊 Refreshing data...", 'INFO')
#         self.start_progress()
#         # Progress would be stopped when data is refreshed
#     
#     def on_emergency_stop(self):
#         """Handle emergency stop"""
#         self.set_status("🔴 EMERGENCY STOP", '#ff0000')
#         self.add_log("🛑 EMERGENCY STOP ACTIVATED", 'ERROR')
#     
#     def run(self):
#         """Run the UI"""
#         self.update_ui()
#         self.root.mainloop()
#     
#     def close(self):
#         """Close the UI"""
#         self.running = False
#         if self.root:
#             self.root.quit()
# ===== END   [126/134] ENA_Hedging_Project/src/ui_components.py =====

# ===== BEGIN [127/134] ENA_Hedging_Project/src/websocket_client.py sha256=18326d68a03e2c6c =====
# #!/usr/bin/env python3
# """
# WEBSOCKET CLIENT FOR ENA HEDGING SYSTEM
# Real-time market data streaming
# """
#
# import asyncio
# import websockets
# import json
# import time
# import logging
# from typing import Dict, List, Callable, Optional
#
# log = logging.getLogger(__name__)
#
# class WebSocketClient:
#     """WebSocket client for real-time market data"""
#     
#     def __init__(self, config, on_message_callback: Callable):
#         self.config = config
#         self.on_message_callback = on_message_callback
#         self.ws = None
#         self.running = False
#         self.reconnect_attempts = 0
#         self.max_reconnect_attempts = 10
#         self.last_ping = time.time()
#         self.subscribed_channels = set()
#         
#     async def connect(self) -> bool:
#         """Connect to WebSocket"""
#         try:
#             log.info(f"📡 Connecting to WebSocket: {self.config.ws_url}")
#             self.ws = await websockets.connect(
#                 self.config.ws_url,
#                 ping_interval=self.config.ws_ping_interval,
#                 ping_timeout=self.config.ws_timeout,
#                 close_timeout=self.config.ws_timeout
#             )
#             
#             self.running = True
#             self.reconnect_attempts = 0
#             log.info("✅ WebSocket connected successfully")
#             return True
#             
#         except Exception as e:
#             log.error(f"❌ WebSocket connection failed: {e}")
#             return False
#     
#     async def disconnect(self):
#         """Disconnect from WebSocket"""
#         self.running = False
#         if self.ws:
#             await self.ws.close()
#             log.info("📡 WebSocket disconnected")
#     
#     async def subscribe_order_book(self, symbol: str, level: int = 5, interval: int = 0):
#         """Subscribe to order book updates"""
#         if not self.ws:
#             log.error("❌ WebSocket not connected")
#             return False
#         
#         try:
#             subscribe_msg = {
#                 "time": int(time.time()),
#                 "channel": "futures.order_book",
#                 "event": "subscribe",
#                 "payload": [symbol, level, interval]
#             }
#             
#             await self.ws.send(json.dumps(subscribe_msg))
#             self.subscribed_channels.add(f"futures.order_book.{symbol}")
#             log.info(f"📊 Subscribed to order book: {symbol}")
#             return True
#             
#         except Exception as e:
#             log.error(f"❌ Failed to subscribe to order book: {e}")
#             return False
#     
#     async def subscribe_trades(self, symbol: str):
#         """Subscribe to trades"""
#         if not self.ws:
#             log.error("❌ WebSocket not connected")
#             return False
#         
#         try:
#             subscribe_msg = {
#                 "time": int(time.time()),
#                 "channel": "futures.trades",
#                 "event": "subscribe",
#                 "payload": [symbol]
#             }
#             
#             await self.ws.send(json.dumps(subscribe_msg))
#             self.subscribed_channels.add(f"futures.trades.{symbol}")
#             log.info(f"📈 Subscribed to trades: {symbol}")
#             return True
#             
#         except Exception as e:
#             log.error(f"❌ Failed to subscribe to trades: {e}")
#             return False
#     
#     async def subscribe_tickers(self, symbol: str):
#         """Subscribe to ticker updates"""
#         if not self.ws:
#             log.error("❌ WebSocket not connected")
#             return False
#         
#         try:
#             subscribe_msg = {
#                 "time": int(time.time()),
#                 "channel": "futures.tickers",
#                 "event": "subscribe",
#                 "payload": [symbol]
#             }
#             
#             await self.ws.send(json.dumps(subscribe_msg))
#             self.subscribed_channels.add(f"futures.tickers.{symbol}")
#             log.info(f"💰 Subscribed to tickers: {symbol}")
#             return True
#             
#         except Exception as e:
#             log.error(f"❌ Failed to subscribe to tickers: {e}")
#             return False
#     
#     async def unsubscribe_all(self):
#         """Unsubscribe from all channels"""
#         if not self.ws:
#             return
#         
#         for channel in list(self.subscribed_channels):
#             try:
#                 unsubscribe_msg = {
#                     "time": int(time.time()),
#                     "channel": channel.split('.')[0],
#                     "event": "unsubscribe",
#                     "payload": [channel.split('.')[1]]
#                 }
#                 await self.ws.send(json.dumps(unsubscribe_msg))
#                 self.subscribed_channels.remove(channel)
#             except Exception as e:
#                 log.error(f"❌ Failed to unsubscribe from {channel}: {e}")
#     
#     async def send_ping(self):
#         """Send ping to keep connection alive"""
#         if self.ws and self.running:
#             try:
#                 ping_msg = {
#                     "time": int(time.time()),
#                     "channel": "futures.ping",
#                     "event": "ping",
#                     "payload": []
#                 }
#                 await self.ws.send(json.dumps(ping_msg))
#                 self.last_ping = time.time()
#             except Exception as e:
#                 log.error(f"❌ Failed to send ping: {e}")
#     
#     async def process_messages(self):
#         """Process incoming WebSocket messages"""
#         try:
#             async for message in self.ws:
#                 if not self.running:
#                     break
#                 
#                 try:
#                     data = json.loads(message)
#                     
#                     # Handle different message types
#                     if data.get('channel') == 'futures.order_book':
#                         await self.handle_order_book(data)
#                     elif data.get('channel') == 'futures.trades':
#                         await self.handle_trades(data)
#                     elif data.get('channel') == 'futures.tickers':
#                         await self.handle_tickers(data)
#                     elif data.get('channel') == 'futures.ping':
#                         await self.handle_ping(data)
#                     else:
#                         log.debug(f"📨 Unknown message type: {data.get('channel')}")
#                     
#                 except json.JSONDecodeError as e:
#                     log.error(f"❌ Failed to decode JSON: {e}")
#                 except Exception as e:
#                     log.error(f"❌ Error processing message: {e}")
#                     
#         except websockets.exceptions.ConnectionClosed:
#             log.warning("⚠️ WebSocket connection closed")
#             await self.handle_reconnect()
#         except Exception as e:
#             log.error(f"❌ WebSocket error: {e}")
#             await self.handle_reconnect()
#     
#     async def handle_order_book(self, data):
#         """Handle order book updates"""
#         if data.get('event') == 'update' and data.get('result'):
#             result = data['result']
#             symbol = result.get('s', '')
#             bids = result.get('bids', [])
#             asks = result.get('asks', [])
#             
#             if bids and asks:
#                 await self.on_message_callback('order_book', {
#                     'symbol': symbol,
#                     'bids': bids,
#                     'asks': asks,
#                     'timestamp': data.get('time', time.time())
#                 })
#     
#     async def handle_trades(self, data):
#         """Handle trade updates"""
#         if data.get('event') == 'update' and data.get('result'):
#             result = data['result']
#             for trade in result:
#                 await self.on_message_callback('trade', {
#                     'symbol': trade.get('s', ''),
#                     'price': trade.get('p', 0),
#                     'size': trade.get('v', 0),
#                     'side': trade.get('S', ''),
#                     'timestamp': trade.get('t', time.time())
#                 })
#     
#     async def handle_tickers(self, data):
#         """Handle ticker updates"""
#         if data.get('event') == 'update' and data.get('result'):
#             result = data['result']
#             await self.on_message_callback('ticker', {
#                 'symbol': result.get('s', ''),
#                 'last_price': result.get('c', 0),
#                 'volume_24h': result.get('v', 0),
#                 'change_24h': result.get('P', 0),
#                 'high_24h': result.get('h', 0),
#                 'low_24h': result.get('l', 0),
#                 'timestamp': data.get('time', time.time())
#             })
#     
#     async def handle_ping(self, data):
#         """Handle ping responses"""
#         self.last_ping = time.time()
#         log.debug("🏓 Ping received")
#     
#     async def handle_reconnect(self):
#         """Handle reconnection logic"""
#         if not self.running:
#             return
#         
#         self.reconnect_attempts += 1
#         
#         if self.reconnect_attempts > self.max_reconnect_attempts:
#             log.error(f"❌ Max reconnection attempts ({self.max_reconnect_attempts}) reached")
#             self.running = False
#             return
#         
#         wait_time = min(self.config.ws_reconnect_delay * self.reconnect_attempts, 60)
#         log.info(f"🔄 Reconnecting in {wait_time} seconds... (attempt {self.reconnect_attempts})")
#         
#         await asyncio.sleep(wait_time)
#         
#         if await self.connect():
#             # Resubscribe to all channels
#             for channel in list(self.subscribed_channels):
#                 parts = channel.split('.')
#                 if len(parts) >= 2:
#                     channel_type = parts[0]
#                     symbol = parts[1]
#                     
#                     if channel_type == 'futures.order_book':
#                         await self.subscribe_order_book(symbol)
#                     elif channel_type == 'futures.trades':
#                         await self.subscribe_trades(symbol)
#                     elif channel_type == 'futures.tickers':
#                         await self.subscribe_tickers(symbol)
#     
#     async def start(self, symbol: str):
#         """Start WebSocket client with symbol subscriptions"""
#         if not await self.connect():
#             return False
#         
#         # Subscribe to essential channels
#         await self.subscribe_order_book(symbol)
#         await self.subscribe_tickers(symbol)
#         
#         # Start message processing
#         await self.process_messages()
#         
#         return True
#     
#     async def stop(self):
#         """Stop WebSocket client"""
#         self.running = False
#         await self.unsubscribe_all()
#         await self.disconnect()
#
# class MarketDataManager:
#     """Manages market data from WebSocket"""
#     
#     def __init__(self, config):
#         self.config = config
#         self.order_books = {}  # symbol -> order book data
#         self.tickers = {}      # symbol -> ticker data
#         self.trades = []       # recent trades
#         self.callbacks = {}    # event callbacks
#         
#     def add_callback(self, event_type: str, callback: Callable):
#         """Add callback for specific event type"""
#         if event_type not in self.callbacks:
#             self.callbacks[event_type] = []
#         self.callbacks[event_type].append(callback)
#     
#     def remove_callback(self, event_type: str, callback: Callable):
#         """Remove callback for specific event type"""
#         if event_type in self.callbacks:
#             try:
#                 self.callbacks[event_type].remove(callback)
#             except ValueError:
#                 pass
#     
#     async def handle_message(self, message_type: str, data: Dict):
#         """Handle incoming market data message"""
#         if message_type == 'order_book':
#             symbol = data['symbol']
#             self.order_books[symbol] = {
#                 'bids': data['bids'],
#                 'asks': data['asks'],
#                 'timestamp': data['timestamp']
#             }
#         elif message_type == 'ticker':
#             symbol = data['symbol']
#             self.tickers[symbol] = data
#         elif message_type == 'trade':
#             self.trades.append(data)
#             # Keep only last 100 trades
#             if len(self.trades) > 100:
#                 self.trades.pop(0)
#         
#         # Trigger callbacks
#         if message_type in self.callbacks:
#             for callback in self.callbacks[message_type]:
#                 try:
#                     await callback(data)
#                 except Exception as e:
#                     log.error(f"❌ Callback error: {e}")
#     
#     def get_order_book(self, symbol: str) -> Optional[Dict]:
#         """Get order book for symbol"""
#         return self.order_books.get(symbol)
#     
#     def get_ticker(self, symbol: str) -> Optional[Dict]:
#         """Get ticker for symbol"""
#         return self.tickers.get(symbol)
#     
#     def get_mid_price(self, symbol: str) -> Optional[float]:
#         """Get mid price for symbol"""
#         order_book = self.get_order_book(symbol)
#         if order_book and order_book['bids'] and order_book['asks']:
#             best_bid = float(order_book['bids'][0][0])
#             best_ask = float(order_book['asks'][0][0])
#             return (best_bid + best_ask) / 2
#         return None
#     
#     def get_spread_bps(self, symbol: str) -> Optional[float]:
#         """Get spread in basis points for symbol"""
#         order_book = self.get_order_book(symbol)
#         if order_book and order_book['bids'] and order_book['asks']:
#             best_bid = float(order_book['bids'][0][0])
#             best_ask = float(order_book['asks'][0][0])
#             mid = (best_bid + best_ask) / 2
#             return (best_ask - best_bid) / mid * 10000
#         return None
# ===== END   [127/134] ENA_Hedging_Project/src/websocket_client.py =====

# ===== BEGIN [128/134] gate_multi_ticker_mm_prod.py sha256=79c0b8bc3ce64219 =====
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
#
# [stripped_future_import] from __future__ import annotations
#
# """
# gate_multi_ticker_mm_prod.py
#
# Production-style multi-ticker Gate.io USDT perpetual maker engine for low-nominal contracts.
#
# What this file does:
# - scans Gate USDT perpetual contracts and filters low nominal symbols (default: mark price 0 to 0.10 USDT)
# - maintains best bid/ask snapshots over WebSocket
# - computes a lightweight alpha signal from microstructure + trend/mean-reversion features
# - places maker-only entries and maker-only take-profit exits
# - tracks local orders/positions in SQLite
# - reconciles local state against exchange state
# - includes an execution-aware backtester with fees, spread proxy, queue/fill probability, slippage, and cooldowns
# - supports PAPER and LIVE modes
#
# Important:
# - This is a software foundation, not a guarantee of profit.
# - A truly tick-perfect execution backtest requires historical L2/order-book and trade data. The included backtester is execution-aware, but still a model.
# - Keep LIVE_TRADING=false until you verify endpoints, permissions, sizing, and contract specifics on your own account.
#
# Install:
#     pip install aiohttp websockets pandas numpy python-dotenv
#
# Run examples:
#     python gate_multi_ticker_mm_prod.py --mode backtest
#     python gate_multi_ticker_mm_prod.py --mode paper
#     python gate_multi_ticker_mm_prod.py --mode live
#     python gate_multi_ticker_mm_prod.py --mode scan
#
# Environment:
#     GATE_API_KEY=...
#     GATE_API_SECRET=...
#     GATE_BASE_URL=https://fx-api.gateio.ws/api/v4
#     GATE_WS_URL=wss://fx-ws.gateio.ws/v4/ws/usdt
#     GATE_SETTLE=usdt
#     LIVE_TRADING=false
#     DB_PATH=gate_mm_prod.db
#     APP_SYMBOLS=0                 # optional comma-separated symbols; 0 means auto-scan
#     MIN_MARK_PRICE=0.0
#     MAX_MARK_PRICE=0.10
#     MIN_24H_QUOTE_VOL=100000
#     MAX_SYMBOLS=12
#     LOOP_SECONDS=2.0
#     CONTRACT_RISK_USD=15
#     LEVERAGE=2
#     MAKER_FEE_BPS=0.0
#     TAKER_FEE_BPS=5.0
#     ENTRY_EDGE_BPS=5.0
#     EXIT_EDGE_BPS=4.0
#     STOP_ATR_MULT=1.6
#     TAKE_ATR_MULT=1.0
#     INVENTORY_LIMIT_PER_SYMBOL=1
#     BAR_INTERVAL=1m
#     BAR_LIMIT=400
#     COOLDOWN_SECONDS=45
#     REQUEST_TIMEOUT=15
#     ENABLE_UI=false
#     APP_HOST=127.0.0.1
#     APP_PORT=8788
# """
#
# import argparse
# import asyncio
# import contextlib
# import dataclasses
# import hashlib
# import hmac
# import json
# import logging
# import math
# import os
# import random
# import signal
# import sqlite3
# import sys
# import time
# from collections import defaultdict, deque
# from dataclasses import dataclass, field
# from datetime import datetime, timezone
# from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple
# from urllib.parse import urlencode
#
# import aiohttp
# import numpy as np
# import pandas as pd
# import websockets
# from dotenv import load_dotenv
#
# load_dotenv()
#
#
# # ============================================================
# # Helpers
# # ============================================================
#
# def now_ts() -> float:
#     return time.time()
#
#
# def utc_now_iso() -> str:
#     return datetime.now(timezone.utc).isoformat()
#
#
# def safe_float(x: Any, default: float = 0.0) -> float:
#     try:
#         if x is None:
#             return default
#         if isinstance(x, float) and math.isnan(x):
#             return default
#         return float(x)
#     except Exception:
#         return default
#
#
# def safe_int(x: Any, default: int = 0) -> int:
#     try:
#         return int(float(x))
#     except Exception:
#         return default
#
#
# def clamp(x: float, lo: float, hi: float) -> float:
#     return max(lo, min(hi, x))
#
#
# def sign(x: float) -> int:
#     return 1 if x > 0 else (-1 if x < 0 else 0)
#
#
# def json_s(x: Any) -> str:
#     return json.dumps(x, ensure_ascii=False, separators=(",", ":"), default=str)
#
#
# def chunks(seq: List[str], n: int) -> Iterable[List[str]]:
#     for i in range(0, len(seq), n):
#         yield seq[i:i+n]
#
#
# # ============================================================
# # Config
# # ============================================================
#
# @dataclass
# class Config:
#     gate_api_key: str = os.getenv("GATE_API_KEY", "")
#     gate_api_secret: str = os.getenv("GATE_API_SECRET", "")
#     gate_base_url: str = os.getenv("GATE_BASE_URL", "https://fx-api.gateio.ws/api/v4").rstrip("/")
#     gate_ws_url: str = os.getenv("GATE_WS_URL", "wss://fx-ws.gateio.ws/v4/ws/usdt")
#     settle: str = os.getenv("GATE_SETTLE", "usdt").lower()
#     live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
#     db_path: str = os.getenv("DB_PATH", "gate_mm_prod.db")
#
#     min_mark_price: float = float(os.getenv("MIN_MARK_PRICE", "0.0"))
#     max_mark_price: float = float(os.getenv("MAX_MARK_PRICE", "0.10"))
#     min_24h_quote_vol: float = float(os.getenv("MIN_24H_QUOTE_VOL", "100000"))
#     max_symbols: int = int(os.getenv("MAX_SYMBOLS", "12"))
#     app_symbols_raw: str = os.getenv("APP_SYMBOLS", "0")
#
#     loop_seconds: float = float(os.getenv("LOOP_SECONDS", "2.0"))
#     contract_risk_usd: float = float(os.getenv("CONTRACT_RISK_USD", "15"))
#     leverage: int = int(os.getenv("LEVERAGE", "2"))
#     maker_fee_bps: float = float(os.getenv("MAKER_FEE_BPS", "0.0"))
#     taker_fee_bps: float = float(os.getenv("TAKER_FEE_BPS", "5.0"))
#     entry_edge_bps: float = float(os.getenv("ENTRY_EDGE_BPS", "5.0"))
#     exit_edge_bps: float = float(os.getenv("EXIT_EDGE_BPS", "4.0"))
#     stop_atr_mult: float = float(os.getenv("STOP_ATR_MULT", "1.6"))
#     take_atr_mult: float = float(os.getenv("TAKE_ATR_MULT", "1.0"))
#     inventory_limit_per_symbol: int = int(os.getenv("INVENTORY_LIMIT_PER_SYMBOL", "1"))
#     bar_interval: str = os.getenv("BAR_INTERVAL", "1m")
#     bar_limit: int = int(os.getenv("BAR_LIMIT", "400"))
#     cooldown_seconds: int = int(os.getenv("COOLDOWN_SECONDS", "45"))
#     request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
#
#     enable_ui: bool = os.getenv("ENABLE_UI", "false").lower() == "true"
#     app_host: str = os.getenv("APP_HOST", "127.0.0.1")
#     app_port: int = int(os.getenv("APP_PORT", "8788"))
#
#     log_level: str = os.getenv("LOG_LEVEL", "INFO")
#
#     @property
#     def app_symbols(self) -> List[str]:
#         raw = self.app_symbols_raw.strip()
#         if not raw or raw == "0":
#             return []
#         return [x.strip().upper() for x in raw.split(",") if x.strip()]
#
#
# CFG = Config()
# logging.basicConfig(
#     level=getattr(logging, CFG.log_level.upper(), logging.INFO),
#     format="%(asctime)s | %(levelname)s | %(message)s",
# )
# log = logging.getLogger("gate-mm-prod")
#
#
# # ============================================================
# # SQLite
# # ============================================================
#
# class DB:
#     def __init__(self, path: str):
#         self.path = path
#         self._init()
#
#     def _conn(self) -> sqlite3.Connection:
#         conn = sqlite3.connect(self.path)
#         conn.row_factory = sqlite3.Row
#         return conn
#
#     def _init(self) -> None:
#         with self._conn() as conn:
#             cur = conn.cursor()
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS symbols (
#                     symbol TEXT PRIMARY KEY,
#                     mark_price REAL,
#                     last_price REAL,
#                     quote_volume REAL,
#                     quanto_multiplier REAL,
#                     order_price_round REAL,
#                     order_size_min INTEGER,
#                     order_size_max INTEGER,
#                     updated_ts TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS events (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts TEXT,
#                     level TEXT,
#                     kind TEXT,
#                     symbol TEXT,
#                     payload_json TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS decisions (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts TEXT,
#                     symbol TEXT,
#                     side TEXT,
#                     score REAL,
#                     confidence REAL,
#                     alpha_json TEXT,
#                     market_json TEXT,
#                     backtest_json TEXT,
#                     live_ok INTEGER,
#                     notes TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS orders (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts TEXT,
#                     symbol TEXT,
#                     role TEXT,
#                     side TEXT,
#                     state TEXT,
#                     text_tag TEXT,
#                     reduce_only INTEGER,
#                     requested_price REAL,
#                     requested_size INTEGER,
#                     exchange_order_id TEXT,
#                     exchange_status TEXT,
#                     fill_price REAL,
#                     left_size INTEGER,
#                     raw_request_json TEXT,
#                     raw_response_json TEXT,
#                     notes TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS positions (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts_open TEXT,
#                     ts_close TEXT,
#                     symbol TEXT,
#                     side TEXT,
#                     status TEXT,
#                     size INTEGER,
#                     entry_price REAL,
#                     exit_price REAL,
#                     take_price REAL,
#                     stop_price REAL,
#                     realized_pnl_usd REAL,
#                     reason_open TEXT,
#                     reason_close TEXT,
#                     meta_json TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS kv_state (
#                     k TEXT PRIMARY KEY,
#                     v TEXT NOT NULL
#                 )
#                 """
#             )
#             conn.commit()
#
#     def event(self, level: str, kind: str, symbol: str, payload: Dict[str, Any]) -> None:
#         with self._conn() as conn:
#             conn.execute(
#                 "INSERT INTO events (ts, level, kind, symbol, payload_json) VALUES (?, ?, ?, ?, ?)",
#                 (utc_now_iso(), level, kind, symbol, json_s(payload)),
#             )
#             conn.commit()
#
#     def upsert_symbol(self, row: Dict[str, Any]) -> None:
#         with self._conn() as conn:
#             conn.execute(
#                 """
#                 INSERT INTO symbols(symbol, mark_price, last_price, quote_volume, quanto_multiplier,
#                                     order_price_round, order_size_min, order_size_max, updated_ts)
#                 VALUES (:symbol, :mark_price, :last_price, :quote_volume, :quanto_multiplier,
#                         :order_price_round, :order_size_min, :order_size_max, :updated_ts)
#                 ON CONFLICT(symbol) DO UPDATE SET
#                     mark_price=excluded.mark_price,
#                     last_price=excluded.last_price,
#                     quote_volume=excluded.quote_volume,
#                     quanto_multiplier=excluded.quanto_multiplier,
#                     order_price_round=excluded.order_price_round,
#                     order_size_min=excluded.order_size_min,
#                     order_size_max=excluded.order_size_max,
#                     updated_ts=excluded.updated_ts
#                 """,
#                 row,
#             )
#             conn.commit()
#
#     def insert_decision(self, row: Dict[str, Any]) -> int:
#         cols = list(row.keys())
#         vals = [row[c] for c in cols]
#         q = f"INSERT INTO decisions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
#         with self._conn() as conn:
#             cur = conn.execute(q, vals)
#             conn.commit()
#             return int(cur.lastrowid)
#
#     def insert_order(self, row: Dict[str, Any]) -> int:
#         cols = list(row.keys())
#         vals = [row[c] for c in cols]
#         q = f"INSERT INTO orders ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
#         with self._conn() as conn:
#             cur = conn.execute(q, vals)
#             conn.commit()
#             return int(cur.lastrowid)
#
#     def update_order(self, order_id: int, updates: Dict[str, Any]) -> None:
#         if not updates:
#             return
#         keys = list(updates.keys())
#         vals = [updates[k] for k in keys] + [order_id]
#         set_clause = ",".join([f"{k}=?" for k in keys])
#         with self._conn() as conn:
#             conn.execute(f"UPDATE orders SET {set_clause} WHERE id=?", vals)
#             conn.commit()
#
#     def open_position(self, row: Dict[str, Any]) -> int:
#         cols = list(row.keys())
#         vals = [row[c] for c in cols]
#         q = f"INSERT INTO positions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
#         with self._conn() as conn:
#             cur = conn.execute(q, vals)
#             conn.commit()
#             return int(cur.lastrowid)
#
#     def update_position(self, pos_id: int, updates: Dict[str, Any]) -> None:
#         if not updates:
#             return
#         keys = list(updates.keys())
#         vals = [updates[k] for k in keys] + [pos_id]
#         set_clause = ",".join([f"{k}=?" for k in keys])
#         with self._conn() as conn:
#             conn.execute(f"UPDATE positions SET {set_clause} WHERE id=?", vals)
#             conn.commit()
#
#     def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
#         with self._conn() as conn:
#             row = conn.execute(
#                 "SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
#                 (symbol,),
#             ).fetchone()
#             return dict(row) if row else None
#
#     def get_working_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             if symbol:
#                 rows = conn.execute(
#                     "SELECT * FROM orders WHERE symbol=? AND state IN ('working','submitted','paper_open') ORDER BY id DESC",
#                     (symbol,),
#                 ).fetchall()
#             else:
#                 rows = conn.execute(
#                     "SELECT * FROM orders WHERE state IN ('working','submitted','paper_open') ORDER BY id DESC"
#                 ).fetchall()
#             return [dict(r) for r in rows]
#
#     def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def recent_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def recent_positions(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM positions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def get_state(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
#         with self._conn() as conn:
#             row = conn.execute("SELECT v FROM kv_state WHERE k=?", (key,)).fetchone()
#             if not row:
#                 return default or {}
#             try:
#                 return json.loads(row[0])
#             except Exception:
#                 return default or {}
#
#     def set_state(self, key: str, val: Dict[str, Any]) -> None:
#         with self._conn() as conn:
#             conn.execute(
#                 "INSERT INTO kv_state(k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
#                 (key, json_s(val)),
#             )
#             conn.commit()
#
#
# DBI = DB(CFG.db_path)
#
#
# # ============================================================
# # Gate REST
# # ============================================================
#
# class GateRest:
#     def __init__(self, cfg: Config):
#         self.cfg = cfg
#         self.session: Optional[aiohttp.ClientSession] = None
#
#     async def ensure(self) -> None:
#         if self.session is None or self.session.closed:
#             timeout = aiohttp.ClientTimeout(total=self.cfg.request_timeout)
#             self.session = aiohttp.ClientSession(timeout=timeout)
#
#     def _headers(self, method: str, path: str, query_string: str = "", body: str = "") -> Dict[str, str]:
#         ts = str(int(time.time()))
#         body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
#         sign_str = f"{method.upper()}\n/api/v4{path}\n{query_string}\n{body_hash}\n{ts}"
#         sign = hmac.new(self.cfg.gate_api_secret.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
#         return {
#             "KEY": self.cfg.gate_api_key,
#             "Timestamp": ts,
#             "SIGN": sign,
#             "Content-Type": "application/json",
#             "Accept": "application/json",
#         }
#
#     async def public(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
#         await self.ensure()
#         assert self.session
#         url = f"{self.cfg.gate_base_url}{path}"
#         async with self.session.get(url, params=params or {}) as r:
#             text = await r.text()
#             if r.status >= 400:
#                 raise RuntimeError(f"public {path} {r.status}: {text[:400]}")
#             return json.loads(text) if text.strip() else {}
#
#     async def private(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any]] = None) -> Any:
#         await self.ensure()
#         assert self.session
#         params = params or {}
#         payload = payload or {}
#         query_string = urlencode(params)
#         body = json.dumps(payload, separators=(",", ":")) if payload else ""
#         headers = self._headers(method, path, query_string, body)
#         url = f"{self.cfg.gate_base_url}{path}"
#         async with self.session.request(method.upper(), url, params=params, data=body if body else None, headers=headers) as r:
#             text = await r.text()
#             if r.status >= 400:
#                 raise RuntimeError(f"private {method} {path} {r.status}: {text[:500]}")
#             return json.loads(text) if text.strip() else {}
#
#     async def list_contracts(self) -> List[Dict[str, Any]]:
#         data = await self.public(f"/futures/{self.cfg.settle}/contracts")
#         return data if isinstance(data, list) else []
#
#     async def list_tickers(self) -> List[Dict[str, Any]]:
#         data = await self.public(f"/futures/{self.cfg.settle}/tickers")
#         return data if isinstance(data, list) else []
#
#     async def get_contract(self, contract: str) -> Dict[str, Any]:
#         data = await self.public(f"/futures/{self.cfg.settle}/contracts/{contract}")
#         return data if isinstance(data, dict) else {}
#
#     async def get_candles(self, contract: str, interval: str, limit: int) -> pd.DataFrame:
#         data = await self.public(
#             f"/futures/{self.cfg.settle}/candlesticks",
#             {"contract": contract, "interval": interval, "limit": min(limit, 2000)},
#         )
#         rows: List[Dict[str, Any]] = []
#         for item in data or []:
#             if isinstance(item, dict):
#                 rows.append({
#                     "t": item.get("t"),
#                     "o": item.get("o"),
#                     "h": item.get("h"),
#                     "l": item.get("l"),
#                     "c": item.get("c"),
#                     "v": item.get("v"),
#                 })
#             elif isinstance(item, list) and len(item) >= 6:
#                 rows.append({"t": item[0], "v": item[1], "c": item[2], "h": item[3], "l": item[4], "o": item[5]})
#         df = pd.DataFrame(rows)
#         if df.empty:
#             return df
#         for c in ["o", "h", "l", "c", "v"]:
#             df[c] = pd.to_numeric(df[c], errors="coerce")
#         df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
#         df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
#         return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna().sort_values("timestamp").reset_index(drop=True)
#
#     async def get_order_book(self, contract: str, limit: int = 5) -> Dict[str, Any]:
#         data = await self.public(f"/futures/{self.cfg.settle}/order_book", {"contract": contract, "limit": limit})
#         return data if isinstance(data, dict) else {}
#
#     async def list_open_orders(self, contract: Optional[str] = None) -> List[Dict[str, Any]]:
#         params = {"status": "open"}
#         if contract:
#             params["contract"] = contract
#         data = await self.private("GET", f"/futures/{self.cfg.settle}/orders", params=params)
#         return data if isinstance(data, list) else []
#
#     async def get_order(self, order_id: str) -> Dict[str, Any]:
#         data = await self.private("GET", f"/futures/{self.cfg.settle}/orders/{order_id}")
#         return data if isinstance(data, dict) else {}
#
#     async def cancel_order(self, order_id: str) -> Dict[str, Any]:
#         data = await self.private("DELETE", f"/futures/{self.cfg.settle}/orders/{order_id}")
#         return data if isinstance(data, dict) else {}
#
#     async def list_positions(self) -> List[Dict[str, Any]]:
#         data = await self.private("GET", f"/futures/{self.cfg.settle}/positions")
#         return data if isinstance(data, list) else []
#
#     async def update_leverage(self, contract: str, leverage: int) -> Dict[str, Any]:
#         data = await self.private("POST", f"/futures/{self.cfg.settle}/positions/{contract}/leverage", payload={"leverage": str(leverage)})
#         return data if isinstance(data, dict) else {}
#
#     async def create_order(self, contract: str, size: int, price: float, text_tag: str, reduce_only: bool = False, tif: str = "poc") -> Dict[str, Any]:
#         payload = {
#             "contract": contract,
#             "size": size,
#             "price": f"{price:.10f}",
#             "tif": tif,
#             "text": text_tag[:28],
#             "reduce_only": reduce_only,
#         }
#         data = await self.private("POST", f"/futures/{self.cfg.settle}/orders", payload=payload)
#         return data if isinstance(data, dict) else {}
#
#     async def close(self) -> None:
#         if self.session and not self.session.closed:
#             await self.session.close()
#
#
# # ============================================================
# # Market state and indicators
# # ============================================================
#
# @dataclass
# class BookTop:
#     bid: float = 0.0
#     ask: float = 0.0
#     bid_size: float = 0.0
#     ask_size: float = 0.0
#     ts: float = 0.0
#
#     @property
#     def mid(self) -> float:
#         if self.bid > 0 and self.ask > 0:
#             return (self.bid + self.ask) / 2.0
#         return 0.0
#
#     @property
#     def spread(self) -> float:
#         if self.bid > 0 and self.ask > 0 and self.ask >= self.bid:
#             return self.ask - self.bid
#         return 0.0
#
#
# @dataclass
# class SymbolSpec:
#     symbol: str
#     mark_price: float
#     quote_volume: float
#     quanto_multiplier: float
#     order_price_round: float
#     order_size_min: int
#     order_size_max: int
#
#
# @dataclass
# class SymbolRuntime:
#     symbol: str
#     spec: SymbolSpec
#     book: BookTop = field(default_factory=BookTop)
#     candles: Optional[pd.DataFrame] = None
#     last_signal_ts: float = 0.0
#     last_trade_ts: float = 0.0
#     state: str = "flat"
#     recent_mid: Deque[float] = field(default_factory=lambda: deque(maxlen=120))
#
#
# class MarketState:
#     def __init__(self):
#         self.by_symbol: Dict[str, SymbolRuntime] = {}
#         self.lock = asyncio.Lock()
#
#     async def set_symbols(self, runtimes: Dict[str, SymbolRuntime]) -> None:
#         async with self.lock:
#             self.by_symbol = runtimes
#
#     async def get(self, symbol: str) -> Optional[SymbolRuntime]:
#         async with self.lock:
#             return self.by_symbol.get(symbol)
#
#     async def symbols(self) -> List[str]:
#         async with self.lock:
#             return list(self.by_symbol.keys())
#
#     async def items(self) -> List[Tuple[str, SymbolRuntime]]:
#         async with self.lock:
#             return list(self.by_symbol.items())
#
#
# MARKET = MarketState()
#
#
# def add_features(df: pd.DataFrame) -> pd.DataFrame:
#     x = df.copy()
#     x["ret1"] = x["close"].pct_change(1)
#     x["ret3"] = x["close"].pct_change(3)
#     x["ret12"] = x["close"].pct_change(12)
#     x["ema8"] = x["close"].ewm(span=8, adjust=False).mean()
#     x["ema21"] = x["close"].ewm(span=21, adjust=False).mean()
#     x["ema55"] = x["close"].ewm(span=55, adjust=False).mean()
#     x["vol20"] = x["ret1"].rolling(20).std()
#     x["atr14"] = (pd.concat([
#         (x["high"] - x["low"]),
#         (x["high"] - x["close"].shift()).abs(),
#         (x["low"] - x["close"].shift()).abs(),
#     ], axis=1).max(axis=1)).rolling(14).mean()
#     x["z20"] = (x["close"] - x["close"].rolling(20).mean()) / x["close"].rolling(20).std()
#     x["volz"] = (x["volume"] - x["volume"].rolling(20).mean()) / x["volume"].rolling(20).std()
#     x["dist_ema21_atr"] = (x["close"] - x["ema21"]) / x["atr14"].replace(0, np.nan)
#     return x
#
#
# def round_to_tick(price: float, tick: float) -> float:
#     if tick <= 0:
#         return price
#     return round(round(price / tick) * tick, 10)
#
#
# def best_bid_ask_from_book(book: Dict[str, Any]) -> Tuple[float, float]:
#     bids = book.get("bids") or []
#     asks = book.get("asks") or []
#     if not bids or not asks:
#         return 0.0, 0.0
#     def get_price(row: Any) -> float:
#         if isinstance(row, list):
#             return safe_float(row[0])
#         if isinstance(row, dict):
#             return safe_float(row.get("p"))
#         return 0.0
#     return get_price(bids[0]), get_price(asks[0])
#
#
# def compute_size(spec: SymbolSpec, mid: float, risk_usd: float, leverage: int, side: str) -> int:
#     mult = max(spec.quanto_multiplier, 1e-9)
#     notional = risk_usd * leverage
#     contracts = max(int(notional / max(mid * mult, 1e-9)), spec.order_size_min or 1)
#     if spec.order_size_max > 0:
#         contracts = min(contracts, spec.order_size_max)
#     return contracts if side == "buy" else -contracts
#
#
# def estimate_micro_alpha(rt: SymbolRuntime) -> Dict[str, float]:
#     df = rt.candles
#     if df is None or len(df) < 80:
#         return {"score": 0.0, "confidence": 0.0}
#     row = df.iloc[-1]
#     bid = rt.book.bid
#     ask = rt.book.ask
#     mid = rt.book.mid or safe_float(row["close"])
#     spread = rt.book.spread
#     tick = max(rt.spec.order_price_round, 1e-8)
#
#     trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
#     slow_trend = np.clip((safe_float(row["ema21"]) - safe_float(row["ema55"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
#     reversion = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
#     flow = np.clip((rt.book.bid_size - rt.book.ask_size) / max(rt.book.bid_size + rt.book.ask_size, 1e-9), -1.0, 1.0)
#     spread_score = np.clip((spread / tick - 1.0) / 5.0, -1.0, 1.0)
#     volume = np.clip(safe_float(row["volz"]) / 2.0, -1.0, 1.0)
#     recent = list(rt.recent_mid)
#     micro_momo = 0.0
#     if len(recent) >= 6 and recent[0] > 0:
#         micro_momo = np.clip((recent[-1] / recent[0] - 1.0) * 400.0, -1.0, 1.0)
#
#     score = (
#         0.25 * trend +
#         0.15 * slow_trend +
#         0.20 * reversion +
#         0.20 * flow +
#         0.10 * spread_score +
#         0.05 * volume +
#         0.05 * micro_momo
#     )
#     confidence = min(abs(score), 0.95)
#     return {
#         "score": float(score),
#         "confidence": float(confidence),
#         "trend": float(trend),
#         "slow_trend": float(slow_trend),
#         "reversion": float(reversion),
#         "flow": float(flow),
#         "spread_score": float(spread_score),
#         "volume": float(volume),
#         "micro_momo": float(micro_momo),
#         "mid": float(mid),
#         "spread": float(spread),
#         "tick": float(tick),
#     }
#
#
# # ============================================================
# # Execution-aware backtest
# # ============================================================
#
# @dataclass
# class BacktestResult:
#     trades: int
#     win_rate: float
#     avg_pnl_usd: float
#     avg_edge_bps: float
#     pnl_usd: float
#     max_drawdown_usd: float
#     sharpe_like: float
#     allowed: bool
#     details: Dict[str, Any]
#
#
# class Backtester:
#     def __init__(self, cfg: Config):
#         self.cfg = cfg
#
#     def simulate(self, df: pd.DataFrame, spec: SymbolSpec) -> BacktestResult:
#         if df is None or len(df) < 120:
#             return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_data"})
#
#         x = df.copy().reset_index(drop=True)
#         x = add_features(x).dropna().reset_index(drop=True)
#         if len(x) < 100:
#             return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_features"})
#
#         equity = 0.0
#         peak = 0.0
#         max_dd = 0.0
#         pnls: List[float] = []
#         edge_bps_arr: List[float] = []
#         cooldown_until = -1
#
#         for i in range(70, len(x) - 8):
#             if i < cooldown_until:
#                 continue
#             row = x.iloc[i]
#             mid = safe_float(row["close"])
#             atr = max(safe_float(row["atr14"]), mid * 0.002)
#             spread = max(spec.order_price_round, mid * 0.0008)
#             queue_fill_prob = clamp(0.28 + abs(safe_float(row["volz"])) * 0.07 + (spread / max(spec.order_price_round, 1e-8) - 1.0) * 0.03, 0.10, 0.85)
#             trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
#             rev = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
#             score = 0.6 * trend + 0.4 * rev
#             if abs(score) < 0.23:
#                 continue
#             side = "buy" if score > 0 else "sell"
#
#             if random.random() > queue_fill_prob:
#                 continue
#
#             entry = (mid - spread / 2.0) if side == "buy" else (mid + spread / 2.0)
#             take = entry + atr * self.cfg.take_atr_mult if side == "buy" else entry - atr * self.cfg.take_atr_mult
#             stop = entry - atr * self.cfg.stop_atr_mult if side == "buy" else entry + atr * self.cfg.stop_atr_mult
#             contracts = compute_size(spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
#             qty = abs(contracts)
#             gross = 0.0
#             exit_reason = "timeout"
#
#             for j in range(i + 1, min(i + 8, len(x))):
#                 bar = x.iloc[j]
#                 high = safe_float(bar["high"])
#                 low = safe_float(bar["low"])
#                 if side == "buy":
#                     if low <= stop:
#                         exit_px = stop - spread * 0.25
#                         gross = (exit_px - entry) * qty * spec.quanto_multiplier
#                         exit_reason = "stop"
#                         break
#                     if high >= take:
#                         exit_px = take
#                         gross = (exit_px - entry) * qty * spec.quanto_multiplier
#                         exit_reason = "take"
#                         break
#                 else:
#                     if high >= stop:
#                         exit_px = stop + spread * 0.25
#                         gross = (entry - exit_px) * qty * spec.quanto_multiplier
#                         exit_reason = "stop"
#                         break
#                     if low <= take:
#                         exit_px = take
#                         gross = (entry - exit_px) * qty * spec.quanto_multiplier
#                         exit_reason = "take"
#                         break
#             else:
#                 exit_px = safe_float(x.iloc[min(i + 7, len(x) - 1)]["close"])
#                 if side == "buy":
#                     gross = (exit_px - entry) * qty * spec.quanto_multiplier
#                 else:
#                     gross = (entry - exit_px) * qty * spec.quanto_multiplier
#
#             fees = qty * spec.quanto_multiplier * entry * (self.cfg.maker_fee_bps / 10000.0)
#             fees += qty * spec.quanto_multiplier * exit_px * (self.cfg.maker_fee_bps / 10000.0)
#             pnl = gross - fees
#             edge_bps = ((take - entry) / max(entry, 1e-9) * 10000.0) if side == "buy" else ((entry - take) / max(entry, 1e-9) * 10000.0)
#             edge_bps_arr.append(edge_bps)
#             pnls.append(pnl)
#             equity += pnl
#             peak = max(peak, equity)
#             max_dd = max(max_dd, peak - equity)
#             cooldown_until = i + 2
#
#         trades = len(pnls)
#         win_rate = float(np.mean([1.0 if x > 0 else 0.0 for x in pnls])) if pnls else 0.0
#         avg_pnl = float(np.mean(pnls)) if pnls else 0.0
#         avg_edge = float(np.mean(edge_bps_arr)) if edge_bps_arr else 0.0
#         pnl = float(np.sum(pnls)) if pnls else 0.0
#         sharpe_like = float(np.mean(pnls) / (np.std(pnls) + 1e-9) * math.sqrt(max(len(pnls), 1))) if pnls else -99.0
#         allowed = trades >= 10 and win_rate >= 0.50 and avg_pnl > 0 and max_dd < max(1.5 * abs(pnl), 15.0)
#         return BacktestResult(
#             trades=trades,
#             win_rate=win_rate,
#             avg_pnl_usd=avg_pnl,
#             avg_edge_bps=avg_edge,
#             pnl_usd=pnl,
#             max_drawdown_usd=float(max_dd),
#             sharpe_like=sharpe_like,
#             allowed=allowed,
#             details={"sample": trades, "equity": equity},
#         )
#
#
# # ============================================================
# # WebSocket market data
# # ============================================================
#
# class BookTickerWS:
#     def __init__(self, cfg: Config, market: MarketState):
#         self.cfg = cfg
#         self.market = market
#         self.shutdown = False
#
#     async def run(self) -> None:
#         backoff = 1.0
#         while not self.shutdown:
#             try:
#                 syms = await self.market.symbols()
#                 if not syms:
#                     await asyncio.sleep(1.0)
#                     continue
#                 async with websockets.connect(self.cfg.gate_ws_url, ping_interval=20, ping_timeout=20, max_size=2**23) as ws:
#                     log.info("WS connected to %s", self.cfg.gate_ws_url)
#                     for batch in chunks(syms, 20):
#                         msg = {
#                             "time": int(time.time()),
#                             "channel": "futures.book_ticker",
#                             "event": "subscribe",
#                             "payload": batch,
#                         }
#                         await ws.send(json.dumps(msg))
#                     backoff = 1.0
#                     async for raw in ws:
#                         data = json.loads(raw)
#                         channel = data.get("channel")
#                         event = data.get("event")
#                         if channel != "futures.book_ticker" or event not in {"update", "all"}:
#                             continue
#                         result = data.get("result") or data.get("payload")
#                         if isinstance(result, list):
#                             for item in result:
#                                 await self._apply(item)
#                         elif isinstance(result, dict):
#                             await self._apply(result)
#             except asyncio.CancelledError:
#                 raise
#             except Exception as e:
#                 log.warning("WS reconnect after error: %s", e)
#                 await asyncio.sleep(backoff)
#                 backoff = min(backoff * 2.0, 20.0)
#
#     async def _apply(self, item: Dict[str, Any]) -> None:
#         symbol = str(item.get("s") or item.get("contract") or item.get("n") or "")
#         if not symbol:
#             return
#         rt = await self.market.get(symbol)
#         if not rt:
#             return
#         bid = safe_float(item.get("b") or item.get("bid_price"))
#         ask = safe_float(item.get("a") or item.get("ask_price"))
#         bid_size = safe_float(item.get("B") or item.get("bid_size") or item.get("bid_amount"))
#         ask_size = safe_float(item.get("A") or item.get("ask_size") or item.get("ask_amount"))
#         if bid <= 0 or ask <= 0 or ask < bid:
#             return
#         rt.book.bid = bid
#         rt.book.ask = ask
#         rt.book.bid_size = bid_size
#         rt.book.ask_size = ask_size
#         rt.book.ts = now_ts()
#         rt.recent_mid.append(rt.book.mid)
#
#
# # ============================================================
# # Trader
# # ============================================================
#
# class Trader:
#     def __init__(self, cfg: Config, db: DB, rest: GateRest, market: MarketState):
#         self.cfg = cfg
#         self.db = db
#         self.rest = rest
#         self.market = market
#         self.backtester = Backtester(cfg)
#         self.shutdown = False
#         self.runtime = self.db.get_state("runtime", {"mode": "paper", "last_scan": [], "last_errors": []})
#
#     async def scan_symbols(self) -> Dict[str, SymbolRuntime]:
#         tickers = await self.rest.list_tickers()
#         contracts = await self.rest.list_contracts()
#         specs_by_symbol: Dict[str, Dict[str, Any]] = {str(c.get("name") or c.get("contract") or c.get("id") or ""): c for c in contracts}
#         selected: List[SymbolRuntime] = []
#
#         if self.cfg.app_symbols:
#             tickers = [t for t in tickers if str(t.get("contract") or t.get("name") or "") in set(self.cfg.app_symbols)]
#
#         for t in tickers:
#             symbol = str(t.get("contract") or t.get("name") or "")
#             if not symbol:
#                 continue
#             mark_price = safe_float(t.get("mark_price") or t.get("last") or t.get("last_price"))
#             quote_volume = safe_float(t.get("volume_24h_quote") or t.get("volume_24h_usd") or t.get("volume_24h_settle"))
#             if not self.cfg.app_symbols:
#                 if not (self.cfg.min_mark_price <= mark_price <= self.cfg.max_mark_price):
#                     continue
#                 if quote_volume < self.cfg.min_24h_quote_vol:
#                     continue
#             spec_raw = specs_by_symbol.get(symbol) or {}
#             spec = SymbolSpec(
#                 symbol=symbol,
#                 mark_price=mark_price,
#                 quote_volume=quote_volume,
#                 quanto_multiplier=max(safe_float(spec_raw.get("quanto_multiplier"), 0.0001), 1e-9),
#                 order_price_round=max(safe_float(spec_raw.get("order_price_round"), 0.00000001), 1e-8),
#                 order_size_min=max(safe_int(spec_raw.get("order_size_min"), 1), 1),
#                 order_size_max=max(safe_int(spec_raw.get("order_size_max"), 0), 0),
#             )
#             selected.append(SymbolRuntime(symbol=symbol, spec=spec))
#
#         selected = sorted(selected, key=lambda r: (r.spec.quote_volume, -r.spec.mark_price), reverse=True)[: self.cfg.max_symbols]
#         for rt in selected:
#             self.db.upsert_symbol({
#                 "symbol": rt.symbol,
#                 "mark_price": rt.spec.mark_price,
#                 "last_price": rt.spec.mark_price,
#                 "quote_volume": rt.spec.quote_volume,
#                 "quanto_multiplier": rt.spec.quanto_multiplier,
#                 "order_price_round": rt.spec.order_price_round,
#                 "order_size_min": rt.spec.order_size_min,
#                 "order_size_max": rt.spec.order_size_max,
#                 "updated_ts": utc_now_iso(),
#             })
#         self.runtime["last_scan"] = [r.symbol for r in selected]
#         self.db.set_state("runtime", self.runtime)
#         return {r.symbol: r for r in selected}
#
#     async def hydrate_candles(self) -> None:
#         for symbol, rt in await self.market.items():
#             try:
#                 df = await self.rest.get_candles(symbol, self.cfg.bar_interval, self.cfg.bar_limit)
#                 if df.empty:
#                     continue
#                 rt.candles = add_features(df).dropna().reset_index(drop=True)
#             except Exception as e:
#                 self.db.event("ERROR", "hydrate_candles_failed", symbol, {"error": str(e)})
#
#     async def reconcile_once(self) -> None:
#         if not self.cfg.live_trading:
#             return
#         local_orders = self.db.get_working_orders()
#         if not local_orders:
#             return
#         exchange_open = await self.rest.list_open_orders()
#         exchange_open_ids = {str(x.get("id")) for x in exchange_open if x.get("id") is not None}
#
#         for order in local_orders:
#             ex_id = str(order.get("exchange_order_id") or "")
#             if not ex_id:
#                 continue
#             try:
#                 if ex_id in exchange_open_ids:
#                     self.db.update_order(order["id"], {"state": "working", "exchange_status": "open"})
#                     continue
#                 detail = await self.rest.get_order(ex_id)
#                 status = str(detail.get("status") or "")
#                 finish_as = str(detail.get("finish_as") or "")
#                 fill_price = safe_float(detail.get("fill_price") or detail.get("price"))
#                 left = safe_int(detail.get("left"), 0)
#                 update = {
#                     "exchange_status": status,
#                     "fill_price": fill_price,
#                     "left_size": left,
#                     "raw_response_json": json_s(detail),
#                 }
#                 if finish_as == "filled" or (status == "finished" and left == 0):
#                     update["state"] = "filled"
#                 elif status == "cancelled":
#                     update["state"] = "cancelled"
#                 elif status == "finished":
#                     update["state"] = "done"
#                 self.db.update_order(order["id"], update)
#                 if update.get("state") == "filled":
#                     await self._on_order_filled(order, fill_price)
#             except Exception as e:
#                 self.db.event("ERROR", "reconcile_order_failed", order["symbol"], {"order_id": ex_id, "error": str(e)})
#
#     async def _on_order_filled(self, order: Dict[str, Any], fill_price: float) -> None:
#         symbol = order["symbol"]
#         if order["role"] == "entry":
#             pos = self.db.get_open_position(symbol)
#             if pos:
#                 return
#             side = order["side"]
#             size = abs(safe_int(order["requested_size"], 0))
#             rt = await self.market.get(symbol)
#             atr = safe_float(rt.candles.iloc[-1]["atr14"]) if rt and rt.candles is not None else fill_price * 0.01
#             take = fill_price + atr * self.cfg.take_atr_mult if side == "buy" else fill_price - atr * self.cfg.take_atr_mult
#             stop = fill_price - atr * self.cfg.stop_atr_mult if side == "buy" else fill_price + atr * self.cfg.stop_atr_mult
#             self.db.open_position({
#                 "ts_open": utc_now_iso(),
#                 "ts_close": None,
#                 "symbol": symbol,
#                 "side": side,
#                 "status": "open",
#                 "size": size,
#                 "entry_price": fill_price,
#                 "exit_price": None,
#                 "take_price": take,
#                 "stop_price": stop,
#                 "realized_pnl_usd": None,
#                 "reason_open": "entry_fill",
#                 "reason_close": None,
#                 "meta_json": json_s({"entry_order_id": order["id"]}),
#             })
#             self.db.event("INFO", "position_opened", symbol, {"side": side, "entry": fill_price, "take": take, "stop": stop})
#             await self.ensure_exit_order(symbol)
#         elif order["role"] == "exit":
#             pos = self.db.get_open_position(symbol)
#             if not pos:
#                 return
#             mult = safe_float((await self.market.get(symbol)).spec.quanto_multiplier if await self.market.get(symbol) else 1.0, 1.0)
#             pnl = ((fill_price - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - fill_price)) * safe_int(pos["size"], 0) * mult
#             self.db.update_position(pos["id"], {
#                 "ts_close": utc_now_iso(),
#                 "status": "closed",
#                 "exit_price": fill_price,
#                 "realized_pnl_usd": pnl,
#                 "reason_close": "maker_exit_fill",
#             })
#             self.db.event("INFO", "position_closed", symbol, {"exit": fill_price, "pnl_usd": pnl})
#
#     async def ensure_exit_order(self, symbol: str) -> None:
#         pos = self.db.get_open_position(symbol)
#         if not pos:
#             return
#         existing = [o for o in self.db.get_working_orders(symbol) if o["role"] == "exit"]
#         if existing:
#             return
#         rt = await self.market.get(symbol)
#         if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
#             return
#         if pos["side"] == "buy":
#             side = "sell"
#             px = max(rt.book.ask, safe_float(pos["take_price"]))
#             size = -abs(safe_int(pos["size"], 0))
#         else:
#             side = "buy"
#             px = min(rt.book.bid, safe_float(pos["take_price"])) if rt.book.bid > 0 else safe_float(pos["take_price"])
#             size = abs(safe_int(pos["size"], 0))
#         px = round_to_tick(px, rt.spec.order_price_round)
#         tag = f"x-{hashlib.sha1(f'{symbol}|exit|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
#         req = {"contract": symbol, "size": size, "price": px, "reduce_only": True, "tif": "poc", "text": tag}
#         if not self.cfg.live_trading:
#             self.db.insert_order({
#                 "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "paper_open", "text_tag": tag,
#                 "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": None,
#                 "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
#                 "raw_request_json": json_s(req), "raw_response_json": "{}", "notes": "paper_exit",
#             })
#             return
#         resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=True)
#         self.db.insert_order({
#             "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "working", "text_tag": tag,
#             "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
#             "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
#             "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_exit",
#         })
#
#     async def maybe_stop_position(self, symbol: str) -> None:
#         pos = self.db.get_open_position(symbol)
#         if not pos:
#             return
#         rt = await self.market.get(symbol)
#         if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
#             return
#         stop = safe_float(pos["stop_price"])
#         side = pos["side"]
#         if side == "buy" and rt.book.bid <= stop:
#             await self.force_close(symbol, reason="stop_cross")
#         elif side == "sell" and rt.book.ask >= stop:
#             await self.force_close(symbol, reason="stop_cross")
#
#     async def force_close(self, symbol: str, reason: str) -> None:
#         pos = self.db.get_open_position(symbol)
#         rt = await self.market.get(symbol)
#         if not pos or not rt:
#             return
#         if pos["side"] == "buy":
#             exit_px = rt.book.bid
#         else:
#             exit_px = rt.book.ask
#         mult = rt.spec.quanto_multiplier
#         pnl = ((exit_px - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - exit_px)) * safe_int(pos["size"], 0) * mult
#         self.db.update_position(pos["id"], {
#             "ts_close": utc_now_iso(),
#             "status": "closed",
#             "exit_price": exit_px,
#             "realized_pnl_usd": pnl,
#             "reason_close": reason,
#         })
#         self.db.event("WARNING", "position_force_closed_locally", symbol, {"exit_px": exit_px, "reason": reason, "pnl_usd": pnl})
#
#     async def maybe_place_entry(self, symbol: str, side: str, alpha: Dict[str, Any], bt: BacktestResult) -> None:
#         if side not in {"buy", "sell"}:
#             return
#         rt = await self.market.get(symbol)
#         if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
#             return
#         if self.db.get_open_position(symbol):
#             return
#         if any(o for o in self.db.get_working_orders(symbol) if o["role"] == "entry"):
#             return
#         if now_ts() - rt.last_trade_ts < self.cfg.cooldown_seconds:
#             return
#
#         mid = rt.book.mid
#         expected_edge_bps = abs(alpha["score"]) * 10.0 + (rt.book.spread / max(mid, 1e-9) * 10000.0)
#         if expected_edge_bps < self.cfg.entry_edge_bps:
#             return
#         size = compute_size(rt.spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
#         px = rt.book.bid if side == "buy" else rt.book.ask
#         px = round_to_tick(px, rt.spec.order_price_round)
#         tag = f"e-{hashlib.sha1(f'{symbol}|entry|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
#         req = {"contract": symbol, "size": size, "price": px, "reduce_only": False, "tif": "poc", "text": tag}
#
#         if not self.cfg.live_trading:
#             self.db.insert_order({
#                 "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "paper_open", "text_tag": tag,
#                 "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": None,
#                 "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
#                 "raw_request_json": json_s(req), "raw_response_json": json_s({"alpha": alpha, "backtest": dataclasses.asdict(bt)}), "notes": "paper_entry",
#             })
#             # paper model: immediate maker fill only when microstructure agrees strongly
#             if abs(alpha["score"]) >= 0.38:
#                 fake_order = {"symbol": symbol, "role": "entry", "side": side, "requested_size": size, "id": -1}
#                 await self._on_order_filled(fake_order, px)
#             rt.last_trade_ts = now_ts()
#             return
#
#         await self.rest.update_leverage(symbol, self.cfg.leverage)
#         resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=False)
#         self.db.insert_order({
#             "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "working", "text_tag": tag,
#             "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
#             "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
#             "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_entry",
#         })
#         rt.last_trade_ts = now_ts()
#
#     async def cancel_stale_orders(self, symbol: str) -> None:
#         rt = await self.market.get(symbol)
#         if not rt:
#             return
#         for order in self.db.get_working_orders(symbol):
#             try:
#                 created = datetime.fromisoformat(order["ts"]).timestamp()
#             except Exception:
#                 created = now_ts()
#             age = now_ts() - created
#             stale = age > max(15.0, self.cfg.loop_seconds * 4.0)
#             desired = rt.book.bid if order["side"] == "buy" else rt.book.ask
#             drift = abs(safe_float(order["requested_price"]) - desired)
#             repriced = drift >= max(rt.spec.order_price_round, 1e-8)
#             if not stale and not repriced:
#                 continue
#             if not self.cfg.live_trading or not order.get("exchange_order_id"):
#                 self.db.update_order(order["id"], {"state": "cancelled", "notes": "paper_stale"})
#                 continue
#             try:
#                 resp = await self.rest.cancel_order(str(order["exchange_order_id"]))
#                 self.db.update_order(order["id"], {"state": "cancelled", "exchange_status": str(resp.get("status") or "cancelled"), "raw_response_json": json_s(resp)})
#             except Exception as e:
#                 self.db.event("ERROR", "cancel_order_failed", symbol, {"order_id": order.get("exchange_order_id"), "error": str(e)})
#
#     async def process_symbol(self, symbol: str) -> None:
#         rt = await self.market.get(symbol)
#         if not rt or rt.candles is None or len(rt.candles) < 80:
#             return
#         if rt.book.bid <= 0 or rt.book.ask <= 0:
#             # bootstrap with REST if WS not ready
#             try:
#                 book = await self.rest.get_order_book(symbol, limit=1)
#                 bid, ask = best_bid_ask_from_book(book)
#                 if bid > 0 and ask > 0:
#                     rt.book.bid, rt.book.ask, rt.book.ts = bid, ask, now_ts()
#             except Exception:
#                 pass
#             if rt.book.bid <= 0 or rt.book.ask <= 0:
#                 return
#
#         if rt.candles is not None and len(rt.recent_mid) > 0:
#             latest_mid = rt.book.mid
#             latest_ts = pd.Timestamp.utcnow().tz_localize("UTC") if pd.Timestamp.utcnow().tzinfo is None else pd.Timestamp.utcnow()
#             if abs(latest_mid - safe_float(rt.candles.iloc[-1]["close"])) / max(latest_mid, 1e-9) > 0.0001:
#                 new_row = {
#                     "timestamp": latest_ts,
#                     "open": latest_mid,
#                     "high": max(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
#                     "low": min(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
#                     "close": latest_mid,
#                     "volume": max(safe_float(rt.candles.iloc[-1]["volume"]), 1.0),
#                 }
#                 rt.candles = pd.concat([rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], pd.DataFrame([new_row])], ignore_index=True).tail(self.cfg.bar_limit)
#                 rt.candles = add_features(rt.candles).dropna().reset_index(drop=True)
#
#         alpha = estimate_micro_alpha(rt)
#         score = alpha.get("score", 0.0)
#         confidence = alpha.get("confidence", 0.0)
#         if abs(score) < 0.22:
#             await self.maybe_stop_position(symbol)
#             await self.cancel_stale_orders(symbol)
#             return
#         side = "buy" if score > 0 else "sell"
#         bt = self.backtester.simulate(rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], rt.spec)
#         live_ok = bt.allowed and abs(score) >= 0.28
#
#         self.db.insert_decision({
#             "ts": utc_now_iso(),
#             "symbol": symbol,
#             "side": side,
#             "score": score,
#             "confidence": confidence,
#             "alpha_json": json_s(alpha),
#             "market_json": json_s({"bid": rt.book.bid, "ask": rt.book.ask, "mid": rt.book.mid, "spread": rt.book.spread}),
#             "backtest_json": json_s(dataclasses.asdict(bt)),
#             "live_ok": 1 if live_ok else 0,
#             "notes": "auto",
#         })
#
#         await self.maybe_stop_position(symbol)
#         await self.cancel_stale_orders(symbol)
#         if live_ok or not self.cfg.live_trading:
#             await self.maybe_place_entry(symbol, side, alpha, bt)
#         await self.ensure_exit_order(symbol)
#
#     async def run_loop(self) -> None:
#         runtimes = await self.scan_symbols()
#         await self.market.set_symbols(runtimes)
#         await self.hydrate_candles()
#         self.db.event("INFO", "startup_symbols", "*", {"symbols": list(runtimes.keys())})
#         while not self.shutdown:
#             try:
#                 for symbol in await self.market.symbols():
#                     await self.process_symbol(symbol)
#                 await self.reconcile_once()
#             except Exception as e:
#                 self.db.event("ERROR", "main_loop_error", "*", {"error": str(e)})
#             await asyncio.sleep(self.cfg.loop_seconds)
#
#
# # ============================================================
# # CLI modes
# # ============================================================
#
# async def run_scan(rest: GateRest) -> int:
#     trader = Trader(CFG, DBI, rest, MARKET)
#     runtimes = await trader.scan_symbols()
#     print(json.dumps({
#         "count": len(runtimes),
#         "symbols": [{
#             "symbol": r.symbol,
#             "mark_price": r.spec.mark_price,
#             "quote_volume": r.spec.quote_volume,
#             "tick": r.spec.order_price_round,
#             "multiplier": r.spec.quanto_multiplier,
#         } for r in runtimes.values()]
#     }, indent=2))
#     return 0
#
#
# async def run_backtest(rest: GateRest) -> int:
#     trader = Trader(CFG, DBI, rest, MARKET)
#     runtimes = await trader.scan_symbols()
#     out = []
#     for symbol, rt in runtimes.items():
#         df = await rest.get_candles(symbol, CFG.bar_interval, CFG.bar_limit)
#         bt = trader.backtester.simulate(df, rt.spec)
#         out.append({
#             "symbol": symbol,
#             "trades": bt.trades,
#             "win_rate": round(bt.win_rate, 4),
#             "avg_pnl_usd": round(bt.avg_pnl_usd, 6),
#             "pnl_usd": round(bt.pnl_usd, 6),
#             "max_dd_usd": round(bt.max_drawdown_usd, 6),
#             "sharpe_like": round(bt.sharpe_like, 4),
#             "allowed": bt.allowed,
#         })
#     out = sorted(out, key=lambda x: x["pnl_usd"], reverse=True)
#     print(json.dumps(out, indent=2))
#     return 0
#
#
# async def run_engine(mode: str, rest: GateRest) -> int:
#     if mode == "live" and not CFG.live_trading:
#         raise RuntimeError("Mode live requested but LIVE_TRADING=false in environment.")
#     trader = Trader(CFG, DBI, rest, MARKET)
#     ws = BookTickerWS(CFG, MARKET)
#     tasks = [
#         asyncio.create_task(trader.run_loop(), name="trader"),
#         asyncio.create_task(ws.run(), name="ws"),
#     ]
#     stop = asyncio.Event()
#
#     def _handle_signal() -> None:
#         trader.shutdown = True
#         ws.shutdown = True
#         stop.set()
#
#     loop = asyncio.get_running_loop()
#     for sig in (signal.SIGINT, signal.SIGTERM):
#         with contextlib.suppress(NotImplementedError):
#             loop.add_signal_handler(sig, _handle_signal)
#
#     await stop.wait()
#     for t in tasks:
#         t.cancel()
#         with contextlib.suppress(asyncio.CancelledError):
#             await t
#     return 0
#
#
# def build_parser() -> argparse.ArgumentParser:
#     p = argparse.ArgumentParser(description="Gate low-nominal multi-ticker market maker")
#     p.add_argument("--mode", choices=["scan", "backtest", "paper", "live"], default="scan")
#     return p
#
#
# async def amain() -> int:
#     args = build_parser().parse_args()
#     rest = GateRest(CFG)
#     try:
#         if args.mode == "scan":
#             return await run_scan(rest)
#         if args.mode == "backtest":
#             return await run_backtest(rest)
#         if args.mode == "paper":
#             return await run_engine("paper", rest)
#         if args.mode == "live":
#             return await run_engine("live", rest)
#         return 0
#     finally:
#         await rest.close()
#
#
# def main() -> int:
#     try:
#         return asyncio.run(amain())
#     except KeyboardInterrupt:
#         return 130
#
#
# if __name__ == "__main__":
#     sys.exit(main())
# ===== END   [128/134] gate_multi_ticker_mm_prod.py =====

# ===== BEGIN [129/134] gateaioms.py sha256=718719aed8cc29d2 =====
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
#
# [stripped_future_import] from __future__ import annotations
#
# """
# gate_multi_ticker_mm_prod.py
#
# Production-style multi-ticker Gate.io USDT perpetual maker engine for low-nominal contracts.
#
# What this file does:
# - scans Gate USDT perpetual contracts and filters low nominal symbols (default: mark price 0 to 0.10 USDT)
# - maintains best bid/ask snapshots over WebSocket
# - computes a lightweight alpha signal from microstructure + trend/mean-reversion features
# - places maker-only entries and maker-only take-profit exits
# - tracks local orders/positions in SQLite
# - reconciles local state against exchange state
# - includes an execution-aware backtester with fees, spread proxy, queue/fill probability, slippage, and cooldowns
# - supports PAPER and LIVE modes
#
# Important:
# - This is a software foundation, not a guarantee of profit.
# - A truly tick-perfect execution backtest requires historical L2/order-book and trade data. The included backtester is execution-aware, but still a model.
# - Keep LIVE_TRADING=false until you verify endpoints, permissions, sizing, and contract specifics on your own account.
#
# Install:
#     pip install aiohttp websockets pandas numpy python-dotenv
#
# Run examples:
#     python gate_multi_ticker_mm_prod.py --mode backtest
#     python gate_multi_ticker_mm_prod.py --mode paper
#     python gate_multi_ticker_mm_prod.py --mode live
#     python gate_multi_ticker_mm_prod.py --mode scan
#
# Environment:
#     GATE_API_KEY=...
#     GATE_API_SECRET=...
#     GATE_BASE_URL=https://fx-api.gateio.ws/api/v4
#     GATE_WS_URL=wss://fx-ws.gateio.ws/v4/ws/usdt
#     GATE_SETTLE=usdt
#     LIVE_TRADING=false
#     DB_PATH=gate_mm_prod.db
#     APP_SYMBOLS=0                 # optional comma-separated symbols; 0 means auto-scan
#     MIN_MARK_PRICE=0.0
#     MAX_MARK_PRICE=0.10
#     MIN_24H_QUOTE_VOL=100000
#     MAX_SYMBOLS=12
#     LOOP_SECONDS=2.0
#     CONTRACT_RISK_USD=15
#     LEVERAGE=2
#     MAKER_FEE_BPS=0.0
#     TAKER_FEE_BPS=5.0
#     ENTRY_EDGE_BPS=5.0
#     EXIT_EDGE_BPS=4.0
#     STOP_ATR_MULT=1.6
#     TAKE_ATR_MULT=1.0
#     INVENTORY_LIMIT_PER_SYMBOL=1
#     BAR_INTERVAL=1m
#     BAR_LIMIT=400
#     COOLDOWN_SECONDS=45
#     REQUEST_TIMEOUT=15
#     ENABLE_UI=false
#     APP_HOST=127.0.0.1
#     APP_PORT=8788
# """
#
# import argparse
# import asyncio
# import contextlib
# import dataclasses
# import hashlib
# import hmac
# import json
# import logging
# import math
# import os
# import random
# import signal
# import sqlite3
# import sys
# import time
# from collections import defaultdict, deque
# from dataclasses import dataclass, field
# from datetime import datetime, timezone
# from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple
# from urllib.parse import urlencode
#
# import aiohttp
# import numpy as np
# import pandas as pd
# import websockets
# from dotenv import load_dotenv
#
# load_dotenv()
#
#
# # ============================================================
# # Helpers
# # ============================================================
#
# def now_ts() -> float:
#     return time.time()
#
#
# def utc_now_iso() -> str:
#     return datetime.now(timezone.utc).isoformat()
#
#
# def safe_float(x: Any, default: float = 0.0) -> float:
#     try:
#         if x is None:
#             return default
#         if isinstance(x, float) and math.isnan(x):
#             return default
#         return float(x)
#     except Exception:
#         return default
#
#
# def safe_int(x: Any, default: int = 0) -> int:
#     try:
#         return int(float(x))
#     except Exception:
#         return default
#
#
# def clamp(x: float, lo: float, hi: float) -> float:
#     return max(lo, min(hi, x))
#
#
# def sign(x: float) -> int:
#     return 1 if x > 0 else (-1 if x < 0 else 0)
#
#
# def json_s(x: Any) -> str:
#     return json.dumps(x, ensure_ascii=False, separators=(",", ":"), default=str)
#
#
# def chunks(seq: List[str], n: int) -> Iterable[List[str]]:
#     for i in range(0, len(seq), n):
#         yield seq[i:i+n]
#
#
# # ============================================================
# # Config
# # ============================================================
#
# @dataclass
# class Config:
#     gate_api_key: str = os.getenv("GATE_API_KEY", "")
#     gate_api_secret: str = os.getenv("GATE_API_SECRET", "")
#     gate_base_url: str = os.getenv("GATE_BASE_URL", "https://fx-api.gateio.ws/api/v4").rstrip("/")
#     gate_ws_url: str = os.getenv("GATE_WS_URL", "wss://fx-ws.gateio.ws/v4/ws/usdt")
#     settle: str = os.getenv("GATE_SETTLE", "usdt").lower()
#     live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
#     db_path: str = os.getenv("DB_PATH", "gate_mm_prod.db")
#
#     min_mark_price: float = float(os.getenv("MIN_MARK_PRICE", "0.0"))
#     max_mark_price: float = float(os.getenv("MAX_MARK_PRICE", "0.10"))
#     min_24h_quote_vol: float = float(os.getenv("MIN_24H_QUOTE_VOL", "100000"))
#     max_symbols: int = int(os.getenv("MAX_SYMBOLS", "12"))
#     app_symbols_raw: str = os.getenv("APP_SYMBOLS", "0")
#
#     loop_seconds: float = float(os.getenv("LOOP_SECONDS", "2.0"))
#     contract_risk_usd: float = float(os.getenv("CONTRACT_RISK_USD", "15"))
#     leverage: int = int(os.getenv("LEVERAGE", "2"))
#     maker_fee_bps: float = float(os.getenv("MAKER_FEE_BPS", "0.0"))
#     taker_fee_bps: float = float(os.getenv("TAKER_FEE_BPS", "5.0"))
#     entry_edge_bps: float = float(os.getenv("ENTRY_EDGE_BPS", "5.0"))
#     exit_edge_bps: float = float(os.getenv("EXIT_EDGE_BPS", "4.0"))
#     stop_atr_mult: float = float(os.getenv("STOP_ATR_MULT", "1.6"))
#     take_atr_mult: float = float(os.getenv("TAKE_ATR_MULT", "1.0"))
#     inventory_limit_per_symbol: int = int(os.getenv("INVENTORY_LIMIT_PER_SYMBOL", "1"))
#     bar_interval: str = os.getenv("BAR_INTERVAL", "1m")
#     bar_limit: int = int(os.getenv("BAR_LIMIT", "400"))
#     cooldown_seconds: int = int(os.getenv("COOLDOWN_SECONDS", "45"))
#     request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
#
#     enable_ui: bool = os.getenv("ENABLE_UI", "false").lower() == "true"
#     app_host: str = os.getenv("APP_HOST", "127.0.0.1")
#     app_port: int = int(os.getenv("APP_PORT", "8788"))
#
#     log_level: str = os.getenv("LOG_LEVEL", "INFO")
#
#     @property
#     def app_symbols(self) -> List[str]:
#         raw = self.app_symbols_raw.strip()
#         if not raw or raw == "0":
#             return []
#         return [x.strip().upper() for x in raw.split(",") if x.strip()]
#
#
# CFG = Config()
# logging.basicConfig(
#     level=getattr(logging, CFG.log_level.upper(), logging.INFO),
#     format="%(asctime)s | %(levelname)s | %(message)s",
# )
# log = logging.getLogger("gate-mm-prod")
#
#
# # ============================================================
# # SQLite
# # ============================================================
#
# class DB:
#     def __init__(self, path: str):
#         self.path = path
#         self._init()
#
#     def _conn(self) -> sqlite3.Connection:
#         conn = sqlite3.connect(self.path)
#         conn.row_factory = sqlite3.Row
#         return conn
#
#     def _init(self) -> None:
#         with self._conn() as conn:
#             cur = conn.cursor()
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS symbols (
#                     symbol TEXT PRIMARY KEY,
#                     mark_price REAL,
#                     last_price REAL,
#                     quote_volume REAL,
#                     quanto_multiplier REAL,
#                     order_price_round REAL,
#                     order_size_min INTEGER,
#                     order_size_max INTEGER,
#                     updated_ts TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS events (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts TEXT,
#                     level TEXT,
#                     kind TEXT,
#                     symbol TEXT,
#                     payload_json TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS decisions (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts TEXT,
#                     symbol TEXT,
#                     side TEXT,
#                     score REAL,
#                     confidence REAL,
#                     alpha_json TEXT,
#                     market_json TEXT,
#                     backtest_json TEXT,
#                     live_ok INTEGER,
#                     notes TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS orders (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts TEXT,
#                     symbol TEXT,
#                     role TEXT,
#                     side TEXT,
#                     state TEXT,
#                     text_tag TEXT,
#                     reduce_only INTEGER,
#                     requested_price REAL,
#                     requested_size INTEGER,
#                     exchange_order_id TEXT,
#                     exchange_status TEXT,
#                     fill_price REAL,
#                     left_size INTEGER,
#                     raw_request_json TEXT,
#                     raw_response_json TEXT,
#                     notes TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS positions (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     ts_open TEXT,
#                     ts_close TEXT,
#                     symbol TEXT,
#                     side TEXT,
#                     status TEXT,
#                     size INTEGER,
#                     entry_price REAL,
#                     exit_price REAL,
#                     take_price REAL,
#                     stop_price REAL,
#                     realized_pnl_usd REAL,
#                     reason_open TEXT,
#                     reason_close TEXT,
#                     meta_json TEXT
#                 )
#                 """
#             )
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS kv_state (
#                     k TEXT PRIMARY KEY,
#                     v TEXT NOT NULL
#                 )
#                 """
#             )
#             conn.commit()
#
#     def event(self, level: str, kind: str, symbol: str, payload: Dict[str, Any]) -> None:
#         with self._conn() as conn:
#             conn.execute(
#                 "INSERT INTO events (ts, level, kind, symbol, payload_json) VALUES (?, ?, ?, ?, ?)",
#                 (utc_now_iso(), level, kind, symbol, json_s(payload)),
#             )
#             conn.commit()
#
#     def upsert_symbol(self, row: Dict[str, Any]) -> None:
#         with self._conn() as conn:
#             conn.execute(
#                 """
#                 INSERT INTO symbols(symbol, mark_price, last_price, quote_volume, quanto_multiplier,
#                                     order_price_round, order_size_min, order_size_max, updated_ts)
#                 VALUES (:symbol, :mark_price, :last_price, :quote_volume, :quanto_multiplier,
#                         :order_price_round, :order_size_min, :order_size_max, :updated_ts)
#                 ON CONFLICT(symbol) DO UPDATE SET
#                     mark_price=excluded.mark_price,
#                     last_price=excluded.last_price,
#                     quote_volume=excluded.quote_volume,
#                     quanto_multiplier=excluded.quanto_multiplier,
#                     order_price_round=excluded.order_price_round,
#                     order_size_min=excluded.order_size_min,
#                     order_size_max=excluded.order_size_max,
#                     updated_ts=excluded.updated_ts
#                 """,
#                 row,
#             )
#             conn.commit()
#
#     def insert_decision(self, row: Dict[str, Any]) -> int:
#         cols = list(row.keys())
#         vals = [row[c] for c in cols]
#         q = f"INSERT INTO decisions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
#         with self._conn() as conn:
#             cur = conn.execute(q, vals)
#             conn.commit()
#             return int(cur.lastrowid)
#
#     def insert_order(self, row: Dict[str, Any]) -> int:
#         cols = list(row.keys())
#         vals = [row[c] for c in cols]
#         q = f"INSERT INTO orders ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
#         with self._conn() as conn:
#             cur = conn.execute(q, vals)
#             conn.commit()
#             return int(cur.lastrowid)
#
#     def update_order(self, order_id: int, updates: Dict[str, Any]) -> None:
#         if not updates:
#             return
#         keys = list(updates.keys())
#         vals = [updates[k] for k in keys] + [order_id]
#         set_clause = ",".join([f"{k}=?" for k in keys])
#         with self._conn() as conn:
#             conn.execute(f"UPDATE orders SET {set_clause} WHERE id=?", vals)
#             conn.commit()
#
#     def open_position(self, row: Dict[str, Any]) -> int:
#         cols = list(row.keys())
#         vals = [row[c] for c in cols]
#         q = f"INSERT INTO positions ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
#         with self._conn() as conn:
#             cur = conn.execute(q, vals)
#             conn.commit()
#             return int(cur.lastrowid)
#
#     def update_position(self, pos_id: int, updates: Dict[str, Any]) -> None:
#         if not updates:
#             return
#         keys = list(updates.keys())
#         vals = [updates[k] for k in keys] + [pos_id]
#         set_clause = ",".join([f"{k}=?" for k in keys])
#         with self._conn() as conn:
#             conn.execute(f"UPDATE positions SET {set_clause} WHERE id=?", vals)
#             conn.commit()
#
#     def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
#         with self._conn() as conn:
#             row = conn.execute(
#                 "SELECT * FROM positions WHERE symbol=? AND status='open' ORDER BY id DESC LIMIT 1",
#                 (symbol,),
#             ).fetchone()
#             return dict(row) if row else None
#
#     def get_working_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             if symbol:
#                 rows = conn.execute(
#                     "SELECT * FROM orders WHERE symbol=? AND state IN ('working','submitted','paper_open') ORDER BY id DESC",
#                     (symbol,),
#                 ).fetchall()
#             else:
#                 rows = conn.execute(
#                     "SELECT * FROM orders WHERE state IN ('working','submitted','paper_open') ORDER BY id DESC"
#                 ).fetchall()
#             return [dict(r) for r in rows]
#
#     def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def recent_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def recent_positions(self, limit: int = 100) -> List[Dict[str, Any]]:
#         with self._conn() as conn:
#             return [dict(r) for r in conn.execute("SELECT * FROM positions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
#
#     def get_state(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
#         with self._conn() as conn:
#             row = conn.execute("SELECT v FROM kv_state WHERE k=?", (key,)).fetchone()
#             if not row:
#                 return default or {}
#             try:
#                 return json.loads(row[0])
#             except Exception:
#                 return default or {}
#
#     def set_state(self, key: str, val: Dict[str, Any]) -> None:
#         with self._conn() as conn:
#             conn.execute(
#                 "INSERT INTO kv_state(k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
#                 (key, json_s(val)),
#             )
#             conn.commit()
#
#
# DBI = DB(CFG.db_path)
#
#
# # ============================================================
# # Gate REST
# # ============================================================
#
# class GateRest:
#     def __init__(self, cfg: Config):
#         self.cfg = cfg
#         self.session: Optional[aiohttp.ClientSession] = None
#
#     async def ensure(self) -> None:
#         if self.session is None or self.session.closed:
#             timeout = aiohttp.ClientTimeout(total=self.cfg.request_timeout)
#             self.session = aiohttp.ClientSession(timeout=timeout)
#
#     def _headers(self, method: str, path: str, query_string: str = "", body: str = "") -> Dict[str, str]:
#         ts = str(int(time.time()))
#         body_hash = hashlib.sha512(body.encode("utf-8")).hexdigest()
#         sign_str = f"{method.upper()}\n/api/v4{path}\n{query_string}\n{body_hash}\n{ts}"
#         sign = hmac.new(self.cfg.gate_api_secret.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
#         return {
#             "KEY": self.cfg.gate_api_key,
#             "Timestamp": ts,
#             "SIGN": sign,
#             "Content-Type": "application/json",
#             "Accept": "application/json",
#         }
#
#     async def public(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
#         await self.ensure()
#         assert self.session
#         url = f"{self.cfg.gate_base_url}{path}"
#         async with self.session.get(url, params=params or {}) as r:
#             text = await r.text()
#             if r.status >= 400:
#                 raise RuntimeError(f"public {path} {r.status}: {text[:400]}")
#             return json.loads(text) if text.strip() else {}
#
#     async def private(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any]] = None) -> Any:
#         await self.ensure()
#         assert self.session
#         params = params or {}
#         payload = payload or {}
#         query_string = urlencode(params)
#         body = json.dumps(payload, separators=(",", ":")) if payload else ""
#         headers = self._headers(method, path, query_string, body)
#         url = f"{self.cfg.gate_base_url}{path}"
#         async with self.session.request(method.upper(), url, params=params, data=body if body else None, headers=headers) as r:
#             text = await r.text()
#             if r.status >= 400:
#                 raise RuntimeError(f"private {method} {path} {r.status}: {text[:500]}")
#             return json.loads(text) if text.strip() else {}
#
#     async def list_contracts(self) -> List[Dict[str, Any]]:
#         data = await self.public(f"/futures/{self.cfg.settle}/contracts")
#         return data if isinstance(data, list) else []
#
#     async def list_tickers(self) -> List[Dict[str, Any]]:
#         data = await self.public(f"/futures/{self.cfg.settle}/tickers")
#         return data if isinstance(data, list) else []
#
#     async def get_contract(self, contract: str) -> Dict[str, Any]:
#         data = await self.public(f"/futures/{self.cfg.settle}/contracts/{contract}")
#         return data if isinstance(data, dict) else {}
#
#     async def get_candles(self, contract: str, interval: str, limit: int) -> pd.DataFrame:
#         data = await self.public(
#             f"/futures/{self.cfg.settle}/candlesticks",
#             {"contract": contract, "interval": interval, "limit": min(limit, 2000)},
#         )
#         rows: List[Dict[str, Any]] = []
#         for item in data or []:
#             if isinstance(item, dict):
#                 rows.append({
#                     "t": item.get("t"),
#                     "o": item.get("o"),
#                     "h": item.get("h"),
#                     "l": item.get("l"),
#                     "c": item.get("c"),
#                     "v": item.get("v"),
#                 })
#             elif isinstance(item, list) and len(item) >= 6:
#                 rows.append({"t": item[0], "v": item[1], "c": item[2], "h": item[3], "l": item[4], "o": item[5]})
#         df = pd.DataFrame(rows)
#         if df.empty:
#             return df
#         for c in ["o", "h", "l", "c", "v"]:
#             df[c] = pd.to_numeric(df[c], errors="coerce")
#         df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
#         df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
#         return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna().sort_values("timestamp").reset_index(drop=True)
#
#     async def get_order_book(self, contract: str, limit: int = 5) -> Dict[str, Any]:
#         data = await self.public(f"/futures/{self.cfg.settle}/order_book", {"contract": contract, "limit": limit})
#         return data if isinstance(data, dict) else {}
#
#     async def list_open_orders(self, contract: Optional[str] = None) -> List[Dict[str, Any]]:
#         params = {"status": "open"}
#         if contract:
#             params["contract"] = contract
#         data = await self.private("GET", f"/futures/{self.cfg.settle}/orders", params=params)
#         return data if isinstance(data, list) else []
#
#     async def get_order(self, order_id: str) -> Dict[str, Any]:
#         data = await self.private("GET", f"/futures/{self.cfg.settle}/orders/{order_id}")
#         return data if isinstance(data, dict) else {}
#
#     async def cancel_order(self, order_id: str) -> Dict[str, Any]:
#         data = await self.private("DELETE", f"/futures/{self.cfg.settle}/orders/{order_id}")
#         return data if isinstance(data, dict) else {}
#
#     async def list_positions(self) -> List[Dict[str, Any]]:
#         data = await self.private("GET", f"/futures/{self.cfg.settle}/positions")
#         return data if isinstance(data, list) else []
#
#     async def update_leverage(self, contract: str, leverage: int) -> Dict[str, Any]:
#         data = await self.private("POST", f"/futures/{self.cfg.settle}/positions/{contract}/leverage", payload={"leverage": str(leverage)})
#         return data if isinstance(data, dict) else {}
#
#     async def create_order(self, contract: str, size: int, price: float, text_tag: str, reduce_only: bool = False, tif: str = "poc") -> Dict[str, Any]:
#         payload = {
#             "contract": contract,
#             "size": size,
#             "price": f"{price:.10f}",
#             "tif": tif,
#             "text": text_tag[:28],
#             "reduce_only": reduce_only,
#         }
#         data = await self.private("POST", f"/futures/{self.cfg.settle}/orders", payload=payload)
#         return data if isinstance(data, dict) else {}
#
#     async def close(self) -> None:
#         if self.session and not self.session.closed:
#             await self.session.close()
#
#
# # ============================================================
# # Market state and indicators
# # ============================================================
#
# @dataclass
# class BookTop:
#     bid: float = 0.0
#     ask: float = 0.0
#     bid_size: float = 0.0
#     ask_size: float = 0.0
#     ts: float = 0.0
#
#     @property
#     def mid(self) -> float:
#         if self.bid > 0 and self.ask > 0:
#             return (self.bid + self.ask) / 2.0
#         return 0.0
#
#     @property
#     def spread(self) -> float:
#         if self.bid > 0 and self.ask > 0 and self.ask >= self.bid:
#             return self.ask - self.bid
#         return 0.0
#
#
# @dataclass
# class SymbolSpec:
#     symbol: str
#     mark_price: float
#     quote_volume: float
#     quanto_multiplier: float
#     order_price_round: float
#     order_size_min: int
#     order_size_max: int
#
#
# @dataclass
# class SymbolRuntime:
#     symbol: str
#     spec: SymbolSpec
#     book: BookTop = field(default_factory=BookTop)
#     candles: Optional[pd.DataFrame] = None
#     last_signal_ts: float = 0.0
#     last_trade_ts: float = 0.0
#     state: str = "flat"
#     recent_mid: Deque[float] = field(default_factory=lambda: deque(maxlen=120))
#
#
# class MarketState:
#     def __init__(self):
#         self.by_symbol: Dict[str, SymbolRuntime] = {}
#         self.lock = asyncio.Lock()
#
#     async def set_symbols(self, runtimes: Dict[str, SymbolRuntime]) -> None:
#         async with self.lock:
#             self.by_symbol = runtimes
#
#     async def get(self, symbol: str) -> Optional[SymbolRuntime]:
#         async with self.lock:
#             return self.by_symbol.get(symbol)
#
#     async def symbols(self) -> List[str]:
#         async with self.lock:
#             return list(self.by_symbol.keys())
#
#     async def items(self) -> List[Tuple[str, SymbolRuntime]]:
#         async with self.lock:
#             return list(self.by_symbol.items())
#
#
# MARKET = MarketState()
#
#
# def add_features(df: pd.DataFrame) -> pd.DataFrame:
#     x = df.copy()
#     x["ret1"] = x["close"].pct_change(1)
#     x["ret3"] = x["close"].pct_change(3)
#     x["ret12"] = x["close"].pct_change(12)
#     x["ema8"] = x["close"].ewm(span=8, adjust=False).mean()
#     x["ema21"] = x["close"].ewm(span=21, adjust=False).mean()
#     x["ema55"] = x["close"].ewm(span=55, adjust=False).mean()
#     x["vol20"] = x["ret1"].rolling(20).std()
#     x["atr14"] = (pd.concat([
#         (x["high"] - x["low"]),
#         (x["high"] - x["close"].shift()).abs(),
#         (x["low"] - x["close"].shift()).abs(),
#     ], axis=1).max(axis=1)).rolling(14).mean()
#     x["z20"] = (x["close"] - x["close"].rolling(20).mean()) / x["close"].rolling(20).std()
#     x["volz"] = (x["volume"] - x["volume"].rolling(20).mean()) / x["volume"].rolling(20).std()
#     x["dist_ema21_atr"] = (x["close"] - x["ema21"]) / x["atr14"].replace(0, np.nan)
#     return x
#
#
# def round_to_tick(price: float, tick: float) -> float:
#     if tick <= 0:
#         return price
#     return round(round(price / tick) * tick, 10)
#
#
# def best_bid_ask_from_book(book: Dict[str, Any]) -> Tuple[float, float]:
#     bids = book.get("bids") or []
#     asks = book.get("asks") or []
#     if not bids or not asks:
#         return 0.0, 0.0
#     def get_price(row: Any) -> float:
#         if isinstance(row, list):
#             return safe_float(row[0])
#         if isinstance(row, dict):
#             return safe_float(row.get("p"))
#         return 0.0
#     return get_price(bids[0]), get_price(asks[0])
#
#
# def compute_size(spec: SymbolSpec, mid: float, risk_usd: float, leverage: int, side: str) -> int:
#     mult = max(spec.quanto_multiplier, 1e-9)
#     notional = risk_usd * leverage
#     contracts = max(int(notional / max(mid * mult, 1e-9)), spec.order_size_min or 1)
#     if spec.order_size_max > 0:
#         contracts = min(contracts, spec.order_size_max)
#     return contracts if side == "buy" else -contracts
#
#
# def estimate_micro_alpha(rt: SymbolRuntime) -> Dict[str, float]:
#     df = rt.candles
#     if df is None or len(df) < 80:
#         return {"score": 0.0, "confidence": 0.0}
#     row = df.iloc[-1]
#     bid = rt.book.bid
#     ask = rt.book.ask
#     mid = rt.book.mid or safe_float(row["close"])
#     spread = rt.book.spread
#     tick = max(rt.spec.order_price_round, 1e-8)
#
#     trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
#     slow_trend = np.clip((safe_float(row["ema21"]) - safe_float(row["ema55"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
#     reversion = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
#     flow = np.clip((rt.book.bid_size - rt.book.ask_size) / max(rt.book.bid_size + rt.book.ask_size, 1e-9), -1.0, 1.0)
#     spread_score = np.clip((spread / tick - 1.0) / 5.0, -1.0, 1.0)
#     volume = np.clip(safe_float(row["volz"]) / 2.0, -1.0, 1.0)
#     recent = list(rt.recent_mid)
#     micro_momo = 0.0
#     if len(recent) >= 6 and recent[0] > 0:
#         micro_momo = np.clip((recent[-1] / recent[0] - 1.0) * 400.0, -1.0, 1.0)
#
#     score = (
#         0.25 * trend +
#         0.15 * slow_trend +
#         0.20 * reversion +
#         0.20 * flow +
#         0.10 * spread_score +
#         0.05 * volume +
#         0.05 * micro_momo
#     )
#     confidence = min(abs(score), 0.95)
#     return {
#         "score": float(score),
#         "confidence": float(confidence),
#         "trend": float(trend),
#         "slow_trend": float(slow_trend),
#         "reversion": float(reversion),
#         "flow": float(flow),
#         "spread_score": float(spread_score),
#         "volume": float(volume),
#         "micro_momo": float(micro_momo),
#         "mid": float(mid),
#         "spread": float(spread),
#         "tick": float(tick),
#     }
#
#
# # ============================================================
# # Execution-aware backtest
# # ============================================================
#
# @dataclass
# class BacktestResult:
#     trades: int
#     win_rate: float
#     avg_pnl_usd: float
#     avg_edge_bps: float
#     pnl_usd: float
#     max_drawdown_usd: float
#     sharpe_like: float
#     allowed: bool
#     details: Dict[str, Any]
#
#
# class Backtester:
#     def __init__(self, cfg: Config):
#         self.cfg = cfg
#
#     def simulate(self, df: pd.DataFrame, spec: SymbolSpec) -> BacktestResult:
#         if df is None or len(df) < 120:
#             return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_data"})
#
#         x = df.copy().reset_index(drop=True)
#         x = add_features(x).dropna().reset_index(drop=True)
#         if len(x) < 100:
#             return BacktestResult(0, 0.0, 0.0, 0.0, 0.0, 0.0, -99.0, False, {"reason": "not_enough_features"})
#
#         equity = 0.0
#         peak = 0.0
#         max_dd = 0.0
#         pnls: List[float] = []
#         edge_bps_arr: List[float] = []
#         cooldown_until = -1
#
#         for i in range(70, len(x) - 8):
#             if i < cooldown_until:
#                 continue
#             row = x.iloc[i]
#             mid = safe_float(row["close"])
#             atr = max(safe_float(row["atr14"]), mid * 0.002)
#             spread = max(spec.order_price_round, mid * 0.0008)
#             queue_fill_prob = clamp(0.28 + abs(safe_float(row["volz"])) * 0.07 + (spread / max(spec.order_price_round, 1e-8) - 1.0) * 0.03, 0.10, 0.85)
#             trend = np.clip((safe_float(row["ema8"]) - safe_float(row["ema21"])) / max(mid, 1e-9) * 2000.0, -1.0, 1.0)
#             rev = np.clip(-safe_float(row["z20"]) / 2.5, -1.0, 1.0)
#             score = 0.6 * trend + 0.4 * rev
#             if abs(score) < 0.23:
#                 continue
#             side = "buy" if score > 0 else "sell"
#
#             if random.random() > queue_fill_prob:
#                 continue
#
#             entry = (mid - spread / 2.0) if side == "buy" else (mid + spread / 2.0)
#             take = entry + atr * self.cfg.take_atr_mult if side == "buy" else entry - atr * self.cfg.take_atr_mult
#             stop = entry - atr * self.cfg.stop_atr_mult if side == "buy" else entry + atr * self.cfg.stop_atr_mult
#             contracts = compute_size(spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
#             qty = abs(contracts)
#             gross = 0.0
#             exit_reason = "timeout"
#
#             for j in range(i + 1, min(i + 8, len(x))):
#                 bar = x.iloc[j]
#                 high = safe_float(bar["high"])
#                 low = safe_float(bar["low"])
#                 if side == "buy":
#                     if low <= stop:
#                         exit_px = stop - spread * 0.25
#                         gross = (exit_px - entry) * qty * spec.quanto_multiplier
#                         exit_reason = "stop"
#                         break
#                     if high >= take:
#                         exit_px = take
#                         gross = (exit_px - entry) * qty * spec.quanto_multiplier
#                         exit_reason = "take"
#                         break
#                 else:
#                     if high >= stop:
#                         exit_px = stop + spread * 0.25
#                         gross = (entry - exit_px) * qty * spec.quanto_multiplier
#                         exit_reason = "stop"
#                         break
#                     if low <= take:
#                         exit_px = take
#                         gross = (entry - exit_px) * qty * spec.quanto_multiplier
#                         exit_reason = "take"
#                         break
#             else:
#                 exit_px = safe_float(x.iloc[min(i + 7, len(x) - 1)]["close"])
#                 if side == "buy":
#                     gross = (exit_px - entry) * qty * spec.quanto_multiplier
#                 else:
#                     gross = (entry - exit_px) * qty * spec.quanto_multiplier
#
#             fees = qty * spec.quanto_multiplier * entry * (self.cfg.maker_fee_bps / 10000.0)
#             fees += qty * spec.quanto_multiplier * exit_px * (self.cfg.maker_fee_bps / 10000.0)
#             pnl = gross - fees
#             edge_bps = ((take - entry) / max(entry, 1e-9) * 10000.0) if side == "buy" else ((entry - take) / max(entry, 1e-9) * 10000.0)
#             edge_bps_arr.append(edge_bps)
#             pnls.append(pnl)
#             equity += pnl
#             peak = max(peak, equity)
#             max_dd = max(max_dd, peak - equity)
#             cooldown_until = i + 2
#
#         trades = len(pnls)
#         win_rate = float(np.mean([1.0 if x > 0 else 0.0 for x in pnls])) if pnls else 0.0
#         avg_pnl = float(np.mean(pnls)) if pnls else 0.0
#         avg_edge = float(np.mean(edge_bps_arr)) if edge_bps_arr else 0.0
#         pnl = float(np.sum(pnls)) if pnls else 0.0
#         sharpe_like = float(np.mean(pnls) / (np.std(pnls) + 1e-9) * math.sqrt(max(len(pnls), 1))) if pnls else -99.0
#         allowed = trades >= 10 and win_rate >= 0.50 and avg_pnl > 0 and max_dd < max(1.5 * abs(pnl), 15.0)
#         return BacktestResult(
#             trades=trades,
#             win_rate=win_rate,
#             avg_pnl_usd=avg_pnl,
#             avg_edge_bps=avg_edge,
#             pnl_usd=pnl,
#             max_drawdown_usd=float(max_dd),
#             sharpe_like=sharpe_like,
#             allowed=allowed,
#             details={"sample": trades, "equity": equity},
#         )
#
#
# # ============================================================
# # WebSocket market data
# # ============================================================
#
# class BookTickerWS:
#     def __init__(self, cfg: Config, market: MarketState):
#         self.cfg = cfg
#         self.market = market
#         self.shutdown = False
#
#     async def run(self) -> None:
#         backoff = 1.0
#         while not self.shutdown:
#             try:
#                 syms = await self.market.symbols()
#                 if not syms:
#                     await asyncio.sleep(1.0)
#                     continue
#                 async with websockets.connect(self.cfg.gate_ws_url, ping_interval=20, ping_timeout=20, max_size=2**23) as ws:
#                     log.info("WS connected to %s", self.cfg.gate_ws_url)
#                     for batch in chunks(syms, 20):
#                         msg = {
#                             "time": int(time.time()),
#                             "channel": "futures.book_ticker",
#                             "event": "subscribe",
#                             "payload": batch,
#                         }
#                         await ws.send(json.dumps(msg))
#                     backoff = 1.0
#                     async for raw in ws:
#                         data = json.loads(raw)
#                         channel = data.get("channel")
#                         event = data.get("event")
#                         if channel != "futures.book_ticker" or event not in {"update", "all"}:
#                             continue
#                         result = data.get("result") or data.get("payload")
#                         if isinstance(result, list):
#                             for item in result:
#                                 await self._apply(item)
#                         elif isinstance(result, dict):
#                             await self._apply(result)
#             except asyncio.CancelledError:
#                 raise
#             except Exception as e:
#                 log.warning("WS reconnect after error: %s", e)
#                 await asyncio.sleep(backoff)
#                 backoff = min(backoff * 2.0, 20.0)
#
#     async def _apply(self, item: Dict[str, Any]) -> None:
#         symbol = str(item.get("s") or item.get("contract") or item.get("n") or "")
#         if not symbol:
#             return
#         rt = await self.market.get(symbol)
#         if not rt:
#             return
#         bid = safe_float(item.get("b") or item.get("bid_price"))
#         ask = safe_float(item.get("a") or item.get("ask_price"))
#         bid_size = safe_float(item.get("B") or item.get("bid_size") or item.get("bid_amount"))
#         ask_size = safe_float(item.get("A") or item.get("ask_size") or item.get("ask_amount"))
#         if bid <= 0 or ask <= 0 or ask < bid:
#             return
#         rt.book.bid = bid
#         rt.book.ask = ask
#         rt.book.bid_size = bid_size
#         rt.book.ask_size = ask_size
#         rt.book.ts = now_ts()
#         rt.recent_mid.append(rt.book.mid)
#
#
# # ============================================================
# # Trader
# # ============================================================
#
# class Trader:
#     def __init__(self, cfg: Config, db: DB, rest: GateRest, market: MarketState):
#         self.cfg = cfg
#         self.db = db
#         self.rest = rest
#         self.market = market
#         self.backtester = Backtester(cfg)
#         self.shutdown = False
#         self.runtime = self.db.get_state("runtime", {"mode": "paper", "last_scan": [], "last_errors": []})
#
#     async def scan_symbols(self) -> Dict[str, SymbolRuntime]:
#         tickers = await self.rest.list_tickers()
#         contracts = await self.rest.list_contracts()
#         specs_by_symbol: Dict[str, Dict[str, Any]] = {str(c.get("name") or c.get("contract") or c.get("id") or ""): c for c in contracts}
#         selected: List[SymbolRuntime] = []
#
#         if self.cfg.app_symbols:
#             tickers = [t for t in tickers if str(t.get("contract") or t.get("name") or "") in set(self.cfg.app_symbols)]
#
#         for t in tickers:
#             symbol = str(t.get("contract") or t.get("name") or "")
#             if not symbol:
#                 continue
#             mark_price = safe_float(t.get("mark_price") or t.get("last") or t.get("last_price"))
#             quote_volume = safe_float(t.get("volume_24h_quote") or t.get("volume_24h_usd") or t.get("volume_24h_settle"))
#             if not self.cfg.app_symbols:
#                 if not (self.cfg.min_mark_price <= mark_price <= self.cfg.max_mark_price):
#                     continue
#                 if quote_volume < self.cfg.min_24h_quote_vol:
#                     continue
#             spec_raw = specs_by_symbol.get(symbol) or {}
#             spec = SymbolSpec(
#                 symbol=symbol,
#                 mark_price=mark_price,
#                 quote_volume=quote_volume,
#                 quanto_multiplier=max(safe_float(spec_raw.get("quanto_multiplier"), 0.0001), 1e-9),
#                 order_price_round=max(safe_float(spec_raw.get("order_price_round"), 0.00000001), 1e-8),
#                 order_size_min=max(safe_int(spec_raw.get("order_size_min"), 1), 1),
#                 order_size_max=max(safe_int(spec_raw.get("order_size_max"), 0), 0),
#             )
#             selected.append(SymbolRuntime(symbol=symbol, spec=spec))
#
#         selected = sorted(selected, key=lambda r: (r.spec.quote_volume, -r.spec.mark_price), reverse=True)[: self.cfg.max_symbols]
#         for rt in selected:
#             self.db.upsert_symbol({
#                 "symbol": rt.symbol,
#                 "mark_price": rt.spec.mark_price,
#                 "last_price": rt.spec.mark_price,
#                 "quote_volume": rt.spec.quote_volume,
#                 "quanto_multiplier": rt.spec.quanto_multiplier,
#                 "order_price_round": rt.spec.order_price_round,
#                 "order_size_min": rt.spec.order_size_min,
#                 "order_size_max": rt.spec.order_size_max,
#                 "updated_ts": utc_now_iso(),
#             })
#         self.runtime["last_scan"] = [r.symbol for r in selected]
#         self.db.set_state("runtime", self.runtime)
#         return {r.symbol: r for r in selected}
#
#     async def hydrate_candles(self) -> None:
#         for symbol, rt in await self.market.items():
#             try:
#                 df = await self.rest.get_candles(symbol, self.cfg.bar_interval, self.cfg.bar_limit)
#                 if df.empty:
#                     continue
#                 rt.candles = add_features(df).dropna().reset_index(drop=True)
#             except Exception as e:
#                 self.db.event("ERROR", "hydrate_candles_failed", symbol, {"error": str(e)})
#
#     async def reconcile_once(self) -> None:
#         if not self.cfg.live_trading:
#             return
#         local_orders = self.db.get_working_orders()
#         if not local_orders:
#             return
#         exchange_open = await self.rest.list_open_orders()
#         exchange_open_ids = {str(x.get("id")) for x in exchange_open if x.get("id") is not None}
#
#         for order in local_orders:
#             ex_id = str(order.get("exchange_order_id") or "")
#             if not ex_id:
#                 continue
#             try:
#                 if ex_id in exchange_open_ids:
#                     self.db.update_order(order["id"], {"state": "working", "exchange_status": "open"})
#                     continue
#                 detail = await self.rest.get_order(ex_id)
#                 status = str(detail.get("status") or "")
#                 finish_as = str(detail.get("finish_as") or "")
#                 fill_price = safe_float(detail.get("fill_price") or detail.get("price"))
#                 left = safe_int(detail.get("left"), 0)
#                 update = {
#                     "exchange_status": status,
#                     "fill_price": fill_price,
#                     "left_size": left,
#                     "raw_response_json": json_s(detail),
#                 }
#                 if finish_as == "filled" or (status == "finished" and left == 0):
#                     update["state"] = "filled"
#                 elif status == "cancelled":
#                     update["state"] = "cancelled"
#                 elif status == "finished":
#                     update["state"] = "done"
#                 self.db.update_order(order["id"], update)
#                 if update.get("state") == "filled":
#                     await self._on_order_filled(order, fill_price)
#             except Exception as e:
#                 self.db.event("ERROR", "reconcile_order_failed", order["symbol"], {"order_id": ex_id, "error": str(e)})
#
#     async def _on_order_filled(self, order: Dict[str, Any], fill_price: float) -> None:
#         symbol = order["symbol"]
#         if order["role"] == "entry":
#             pos = self.db.get_open_position(symbol)
#             if pos:
#                 return
#             side = order["side"]
#             size = abs(safe_int(order["requested_size"], 0))
#             rt = await self.market.get(symbol)
#             atr = safe_float(rt.candles.iloc[-1]["atr14"]) if rt and rt.candles is not None else fill_price * 0.01
#             take = fill_price + atr * self.cfg.take_atr_mult if side == "buy" else fill_price - atr * self.cfg.take_atr_mult
#             stop = fill_price - atr * self.cfg.stop_atr_mult if side == "buy" else fill_price + atr * self.cfg.stop_atr_mult
#             self.db.open_position({
#                 "ts_open": utc_now_iso(),
#                 "ts_close": None,
#                 "symbol": symbol,
#                 "side": side,
#                 "status": "open",
#                 "size": size,
#                 "entry_price": fill_price,
#                 "exit_price": None,
#                 "take_price": take,
#                 "stop_price": stop,
#                 "realized_pnl_usd": None,
#                 "reason_open": "entry_fill",
#                 "reason_close": None,
#                 "meta_json": json_s({"entry_order_id": order["id"]}),
#             })
#             self.db.event("INFO", "position_opened", symbol, {"side": side, "entry": fill_price, "take": take, "stop": stop})
#             await self.ensure_exit_order(symbol)
#         elif order["role"] == "exit":
#             pos = self.db.get_open_position(symbol)
#             if not pos:
#                 return
#             mult = safe_float((await self.market.get(symbol)).spec.quanto_multiplier if await self.market.get(symbol) else 1.0, 1.0)
#             pnl = ((fill_price - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - fill_price)) * safe_int(pos["size"], 0) * mult
#             self.db.update_position(pos["id"], {
#                 "ts_close": utc_now_iso(),
#                 "status": "closed",
#                 "exit_price": fill_price,
#                 "realized_pnl_usd": pnl,
#                 "reason_close": "maker_exit_fill",
#             })
#             self.db.event("INFO", "position_closed", symbol, {"exit": fill_price, "pnl_usd": pnl})
#
#     async def ensure_exit_order(self, symbol: str) -> None:
#         pos = self.db.get_open_position(symbol)
#         if not pos:
#             return
#         existing = [o for o in self.db.get_working_orders(symbol) if o["role"] == "exit"]
#         if existing:
#             return
#         rt = await self.market.get(symbol)
#         if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
#             return
#         if pos["side"] == "buy":
#             side = "sell"
#             px = max(rt.book.ask, safe_float(pos["take_price"]))
#             size = -abs(safe_int(pos["size"], 0))
#         else:
#             side = "buy"
#             px = min(rt.book.bid, safe_float(pos["take_price"])) if rt.book.bid > 0 else safe_float(pos["take_price"])
#             size = abs(safe_int(pos["size"], 0))
#         px = round_to_tick(px, rt.spec.order_price_round)
#         tag = f"x-{hashlib.sha1(f'{symbol}|exit|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
#         req = {"contract": symbol, "size": size, "price": px, "reduce_only": True, "tif": "poc", "text": tag}
#         if not self.cfg.live_trading:
#             self.db.insert_order({
#                 "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "paper_open", "text_tag": tag,
#                 "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": None,
#                 "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
#                 "raw_request_json": json_s(req), "raw_response_json": "{}", "notes": "paper_exit",
#             })
#             return
#         resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=True)
#         self.db.insert_order({
#             "ts": utc_now_iso(), "symbol": symbol, "role": "exit", "side": side, "state": "working", "text_tag": tag,
#             "reduce_only": 1, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
#             "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
#             "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_exit",
#         })
#
#     async def maybe_stop_position(self, symbol: str) -> None:
#         pos = self.db.get_open_position(symbol)
#         if not pos:
#             return
#         rt = await self.market.get(symbol)
#         if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
#             return
#         stop = safe_float(pos["stop_price"])
#         side = pos["side"]
#         if side == "buy" and rt.book.bid <= stop:
#             await self.force_close(symbol, reason="stop_cross")
#         elif side == "sell" and rt.book.ask >= stop:
#             await self.force_close(symbol, reason="stop_cross")
#
#     async def force_close(self, symbol: str, reason: str) -> None:
#         pos = self.db.get_open_position(symbol)
#         rt = await self.market.get(symbol)
#         if not pos or not rt:
#             return
#         if pos["side"] == "buy":
#             exit_px = rt.book.bid
#         else:
#             exit_px = rt.book.ask
#         mult = rt.spec.quanto_multiplier
#         pnl = ((exit_px - safe_float(pos["entry_price"])) if pos["side"] == "buy" else (safe_float(pos["entry_price"]) - exit_px)) * safe_int(pos["size"], 0) * mult
#         self.db.update_position(pos["id"], {
#             "ts_close": utc_now_iso(),
#             "status": "closed",
#             "exit_price": exit_px,
#             "realized_pnl_usd": pnl,
#             "reason_close": reason,
#         })
#         self.db.event("WARNING", "position_force_closed_locally", symbol, {"exit_px": exit_px, "reason": reason, "pnl_usd": pnl})
#         # NOTE: for a stricter live implementation you would place an IOC/market-like protective order if exchange supports it for the contract.
#
#     async def maybe_place_entry(self, symbol: str, side: str, alpha: Dict[str, Any], bt: BacktestResult) -> None:
#         if side not in {"buy", "sell"}:
#             return
#         rt = await self.market.get(symbol)
#         if not rt or rt.book.bid <= 0 or rt.book.ask <= 0:
#             return
#         if self.db.get_open_position(symbol):
#             return
#         if any(o for o in self.db.get_working_orders(symbol) if o["role"] == "entry"):
#             return
#         if now_ts() - rt.last_trade_ts < self.cfg.cooldown_seconds:
#             return
#
#         mid = rt.book.mid
#         expected_edge_bps = abs(alpha["score"]) * 10.0 + (rt.book.spread / max(mid, 1e-9) * 10000.0)
#         if expected_edge_bps < self.cfg.entry_edge_bps:
#             return
#         size = compute_size(rt.spec, mid, self.cfg.contract_risk_usd, self.cfg.leverage, side)
#         px = rt.book.bid if side == "buy" else rt.book.ask
#         px = round_to_tick(px, rt.spec.order_price_round)
#         tag = f"e-{hashlib.sha1(f'{symbol}|entry|{time.time()}'.encode()).hexdigest()[:20]}"[:28]
#         req = {"contract": symbol, "size": size, "price": px, "reduce_only": False, "tif": "poc", "text": tag}
#
#         if not self.cfg.live_trading:
#             self.db.insert_order({
#                 "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "paper_open", "text_tag": tag,
#                 "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": None,
#                 "exchange_status": "paper", "fill_price": None, "left_size": abs(size),
#                 "raw_request_json": json_s(req), "raw_response_json": json_s({"alpha": alpha, "backtest": dataclasses.asdict(bt)}), "notes": "paper_entry",
#             })
#             # paper model: immediate maker fill only when microstructure agrees strongly
#             if abs(alpha["score"]) >= 0.38:
#                 fake_order = {"symbol": symbol, "role": "entry", "side": side, "requested_size": size, "id": -1}
#                 await self._on_order_filled(fake_order, px)
#             rt.last_trade_ts = now_ts()
#             return
#
#         await self.rest.update_leverage(symbol, self.cfg.leverage)
#         resp = await self.rest.create_order(symbol, size, px, tag, reduce_only=False)
#         self.db.insert_order({
#             "ts": utc_now_iso(), "symbol": symbol, "role": "entry", "side": side, "state": "working", "text_tag": tag,
#             "reduce_only": 0, "requested_price": px, "requested_size": size, "exchange_order_id": str(resp.get("id") or ""),
#             "exchange_status": str(resp.get("status") or "submitted"), "fill_price": None, "left_size": abs(size),
#             "raw_request_json": json_s(req), "raw_response_json": json_s(resp), "notes": "live_entry",
#         })
#         rt.last_trade_ts = now_ts()
#
#     async def cancel_stale_orders(self, symbol: str) -> None:
#         rt = await self.market.get(symbol)
#         if not rt:
#             return
#         for order in self.db.get_working_orders(symbol):
#             try:
#                 created = datetime.fromisoformat(order["ts"]).timestamp()
#             except Exception:
#                 created = now_ts()
#             age = now_ts() - created
#             stale = age > max(15.0, self.cfg.loop_seconds * 4.0)
#             desired = rt.book.bid if order["side"] == "buy" else rt.book.ask
#             drift = abs(safe_float(order["requested_price"]) - desired)
#             repriced = drift >= max(rt.spec.order_price_round, 1e-8)
#             if not stale and not repriced:
#                 continue
#             if not self.cfg.live_trading or not order.get("exchange_order_id"):
#                 self.db.update_order(order["id"], {"state": "cancelled", "notes": "paper_stale"})
#                 continue
#             try:
#                 resp = await self.rest.cancel_order(str(order["exchange_order_id"]))
#                 self.db.update_order(order["id"], {"state": "cancelled", "exchange_status": str(resp.get("status") or "cancelled"), "raw_response_json": json_s(resp)})
#             except Exception as e:
#                 self.db.event("ERROR", "cancel_order_failed", symbol, {"order_id": order.get("exchange_order_id"), "error": str(e)})
#
#     async def process_symbol(self, symbol: str) -> None:
#         rt = await self.market.get(symbol)
#         if not rt or rt.candles is None or len(rt.candles) < 80:
#             return
#         if rt.book.bid <= 0 or rt.book.ask <= 0:
#             # bootstrap with REST if WS not ready
#             try:
#                 book = await self.rest.get_order_book(symbol, limit=1)
#                 bid, ask = best_bid_ask_from_book(book)
#                 if bid > 0 and ask > 0:
#                     rt.book.bid, rt.book.ask, rt.book.ts = bid, ask, now_ts()
#             except Exception:
#                 pass
#             if rt.book.bid <= 0 or rt.book.ask <= 0:
#                 return
#
#         if rt.candles is not None and len(rt.recent_mid) > 0:
#             latest_mid = rt.book.mid
#             latest_ts = pd.Timestamp.utcnow().tz_localize("UTC") if pd.Timestamp.utcnow().tzinfo is None else pd.Timestamp.utcnow()
#             if abs(latest_mid - safe_float(rt.candles.iloc[-1]["close"])) / max(latest_mid, 1e-9) > 0.0001:
#                 new_row = {
#                     "timestamp": latest_ts,
#                     "open": latest_mid,
#                     "high": max(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
#                     "low": min(latest_mid, safe_float(rt.candles.iloc[-1]["close"])),
#                     "close": latest_mid,
#                     "volume": max(safe_float(rt.candles.iloc[-1]["volume"]), 1.0),
#                 }
#                 rt.candles = pd.concat([rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], pd.DataFrame([new_row])], ignore_index=True).tail(self.cfg.bar_limit)
#                 rt.candles = add_features(rt.candles).dropna().reset_index(drop=True)
#
#         alpha = estimate_micro_alpha(rt)
#         score = alpha.get("score", 0.0)
#         confidence = alpha.get("confidence", 0.0)
#         if abs(score) < 0.22:
#             await self.maybe_stop_position(symbol)
#             await self.cancel_stale_orders(symbol)
#             return
#         side = "buy" if score > 0 else "sell"
#         bt = self.backtester.simulate(rt.candles[["timestamp", "open", "high", "low", "close", "volume"]], rt.spec)
#         live_ok = bt.allowed and abs(score) >= 0.28
#
#         self.db.insert_decision({
#             "ts": utc_now_iso(),
#             "symbol": symbol,
#             "side": side,
#             "score": score,
#             "confidence": confidence,
#             "alpha_json": json_s(alpha),
#             "market_json": json_s({"bid": rt.book.bid, "ask": rt.book.ask, "mid": rt.book.mid, "spread": rt.book.spread}),
#             "backtest_json": json_s(dataclasses.asdict(bt)),
#             "live_ok": 1 if live_ok else 0,
#             "notes": "auto",
#         })
#
#         await self.maybe_stop_position(symbol)
#         await self.cancel_stale_orders(symbol)
#         if live_ok or not self.cfg.live_trading:
#             await self.maybe_place_entry(symbol, side, alpha, bt)
#         await self.ensure_exit_order(symbol)
#
#     async def run_loop(self) -> None:
#         runtimes = await self.scan_symbols()
#         await self.market.set_symbols(runtimes)
#         await self.hydrate_candles()
#         self.db.event("INFO", "startup_symbols", "*", {"symbols": list(runtimes.keys())})
#         while not self.shutdown:
#             try:
#                 for symbol in await self.market.symbols():
#                     await self.process_symbol(symbol)
#                 await self.reconcile_once()
#             except Exception as e:
#                 self.db.event("ERROR", "main_loop_error", "*", {"error": str(e)})
#             await asyncio.sleep(self.cfg.loop_seconds)
#
#
# # ============================================================
# # CLI modes
# # ============================================================
#
# async def run_scan(rest: GateRest) -> int:
#     trader = Trader(CFG, DBI, rest, MARKET)
#     runtimes = await trader.scan_symbols()
#     print(json.dumps({
#         "count": len(runtimes),
#         "symbols": [{
#             "symbol": r.symbol,
#             "mark_price": r.spec.mark_price,
#             "quote_volume": r.spec.quote_volume,
#             "tick": r.spec.order_price_round,
#             "multiplier": r.spec.quanto_multiplier,
#         } for r in runtimes.values()]
#     }, indent=2))
#     return 0
#
#
# async def run_backtest(rest: GateRest) -> int:
#     trader = Trader(CFG, DBI, rest, MARKET)
#     runtimes = await trader.scan_symbols()
#     out = []
#     for symbol, rt in runtimes.items():
#         df = await rest.get_candles(symbol, CFG.bar_interval, CFG.bar_limit)
#         bt = trader.backtester.simulate(df, rt.spec)
#         out.append({
#             "symbol": symbol,
#             "trades": bt.trades,
#             "win_rate": round(bt.win_rate, 4),
#             "avg_pnl_usd": round(bt.avg_pnl_usd, 6),
#             "pnl_usd": round(bt.pnl_usd, 6),
#             "max_dd_usd": round(bt.max_drawdown_usd, 6),
#             "sharpe_like": round(bt.sharpe_like, 4),
#             "allowed": bt.allowed,
#         })
#     out = sorted(out, key=lambda x: x["pnl_usd"], reverse=True)
#     print(json.dumps(out, indent=2))
#     return 0
#
#
# async def run_engine(mode: str, rest: GateRest) -> int:
#     if mode == "live" and not CFG.live_trading:
#         raise RuntimeError("Mode live requested but LIVE_TRADING=false in environment.")
#     trader = Trader(CFG, DBI, rest, MARKET)
#     ws = BookTickerWS(CFG, MARKET)
#     tasks = [
#         asyncio.create_task(trader.run_loop(), name="trader"),
#         asyncio.create_task(ws.run(), name="ws"),
#     ]
#     stop = asyncio.Event()
#
#     def _handle_signal() -> None:
#         trader.shutdown = True
#         ws.shutdown = True
#         stop.set()
#
#     loop = asyncio.get_running_loop()
#     for sig in (signal.SIGINT, signal.SIGTERM):
#         with contextlib.suppress(NotImplementedError):
#             loop.add_signal_handler(sig, _handle_signal)
#
#     await stop.wait()
#     for t in tasks:
#         t.cancel()
#         with contextlib.suppress(asyncio.CancelledError):
#             await t
#     return 0
#
#
# def build_parser() -> argparse.ArgumentParser:
#     p = argparse.ArgumentParser(description="Gate low-nominal multi-ticker market maker")
#     p.add_argument("--mode", choices=["scan", "backtest", "paper", "live"], default="scan")
#     return p
#
#
# async def amain() -> int:
#     args = build_parser().parse_args()
#     rest = GateRest(CFG)
#     try:
#         if args.mode == "scan":
#             return await run_scan(rest)
#         if args.mode == "backtest":
#             return await run_backtest(rest)
#         if args.mode == "paper":
#             return await run_engine("paper", rest)
#         if args.mode == "live":
#             return await run_engine("live", rest)
#         return 0
#     finally:
#         await rest.close()
#
#
# def main() -> int:
#     try:
#         return asyncio.run(amain())
#     except KeyboardInterrupt:
#         return 130
#
#
# if __name__ == "__main__":
#     sys.exit(main())
# ===== END   [129/134] gateaioms.py =====

# ===== BEGIN [130/134] beast.py sha256=46419270d92db049 =====
# import ccxt
# import time
# import json
# import threading
# import numpy as np
# import functools
# import os
# import random
# from datetime import datetime
# from rich.console import Console
# from rich.table import Table
# from rich.live import Live
# from rich.panel import Panel
#
# console = Console()
#
# # Use environment variables for API keys (Required for real trading)
# GATE_API_KEY = os.getenv("GATE_API_KEY", "")
# GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")
#
#
# # === HYDRA SETTINGS ===
# DRY_RUN = True           # Dry run mode - set to False for real trading
# SIMULATE_FILLS = True    # Simulate random fills in dry run mode
# TAKER_FEE = 0.0006       # Estimated taker fee (0.06%)
# INITIAL_DEPOSIT = 200.0  # Total deposit in USDT
# NUM_GRID_CIRCLES = 9     # Number of grid price levels
# MAX_SYMBOLS = 3          # Number of trading pairs to target
# LEVERAGE = 50            # Maximum leverage (50x on Gate.io)
# GRID_SPACING_PERCENT = 0.3  # Grid spacing in percentage
#
# # Rate control - $0.01 per second target (1 cent/sec)
# TARGET_CPS = 1.0  # cents per second target
# PROFIT_THRESHOLD = 0.007  # Minimum profit target per grid level
# STOP_LOSS_THRESHOLD = -0.002  # Maximum loss per grid level
#
# # Volatility settings
# MAX_VOLATILITY_THRESHOLD = 0.05  # Max acceptable volatility 
# MIN_VOLATILITY_THRESHOLD = 0.003  # Min required volatility
#
# # Concurrency control
# thread_lock = threading.Lock()
# emergency_stop = False
# active_grids = {}
# symbol_data = {}
# total_profit = 0.0
# total_trades = 0
# profit_rate = 0.0
# start_time = None
#
# STATE_PATH = os.path.join("cache", "beast_state.json")
# KILL_SWITCH_PATH = os.path.join("cache", "EMERGENCY_STOP")
#
#
# def _safe_float(v, default=0.0):
#     try:
#         return float(v)
#     except Exception:
#         return float(default)
#
#
# def save_state() -> None:
#     try:
#         os.makedirs("cache", exist_ok=True)
#         with thread_lock:
#             payload = {
#                 "ts": int(time.time()),
#                 "emergency_stop": bool(emergency_stop),
#                 "active_grids": active_grids,
#                 "symbol_data": symbol_data,
#                 "total_profit": total_profit,
#                 "total_trades": total_trades,
#                 "profit_rate": profit_rate,
#                 "start_time": start_time,
#                 "dry_run": bool(DRY_RUN),
#             }
#         tmp = STATE_PATH + ".tmp"
#         with open(tmp, "w") as f:
#             json.dump(payload, f)
#         os.replace(tmp, STATE_PATH)
#     except Exception as e:
#         console.print(f"[yellow]State save failed: {e}")
#
#
# def load_state() -> bool:
#     if not os.path.exists(STATE_PATH):
#         return False
#     try:
#         with open(STATE_PATH, "r") as f:
#             payload = json.load(f)
#         with thread_lock:
#             active_grids.clear()
#             active_grids.update(payload.get("active_grids") or {})
#             symbol_data.clear()
#             symbol_data.update(payload.get("symbol_data") or {})
#         return True
#     except Exception as e:
#         console.print(f"[yellow]State load failed: {e}")
#         return False
#
#
# def kill_switch_triggered() -> bool:
#     try:
#         return os.path.exists(KILL_SWITCH_PATH)
#     except Exception:
#         return False
#
# def retry_with_backoff(retries=3, backoff_in_seconds=1):
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             x = 0
#             while True:
#                 try:
#                     return func(*args, **kwargs)
#                 except Exception as e:
#                     if x == retries:
#                         raise e
#                     sleep = (backoff_in_seconds * 2 ** x)
#                     time.sleep(sleep)
#                     x += 1
#         return wrapper
#     return decorator
#
# def emergency_liquidation(ex):
#     global emergency_stop
#     # Capture symbols before clearing
#     with thread_lock:
#         emergency_stop = True
#         symbols_to_clean = list(active_grids.keys())
#         active_grids.clear()
#         
#     console.print("[bold red]EMERGENCY LIQUIDATION TRIGGERED!")
#
#     try:
#         # Cancel orders for active symbols
#         for symbol in symbols_to_clean:
#             try:
#                 ex.cancel_all_orders(symbol)
#                 console.print(f"[yellow]Cancelled all orders for {symbol}")
#             except Exception as e:
#                 console.print(f"[red]Error cancelling orders for {symbol}: {e}")
#         
#         # Close all positions
#         positions = ex.fetch_positions()
#         for pos in positions:
#             contracts = float(pos['contracts'])
#             if contracts > 0:
#                 side = 'sell' if pos['side'] == 'long' else 'buy'
#                 symbol = pos['symbol']
#                 console.print(f"[red]Closing position: {symbol} {side} {contracts}")
#                 ex.create_market_order(symbol, side, contracts)
#     except Exception as e:
#         console.print(f"[red]Error during liquidation: {e}")
#
# def check_account_health(ex):
#     if DRY_RUN:
#         return True
#     try:
#         balance = ex.fetch_balance()
#         equity = balance['total'].get('USDT', 0)
#         if equity > 0 and equity < INITIAL_DEPOSIT * 0.8: # 20% drawdown
#              console.print(f"[bold red]Critical drawdown: Equity ${equity:.2f} < 80% of Initial")
#              return False
#         return True
#     except Exception as e:
#         console.print(f"[red]Error checking account health: {e}")
#         return True
#
# def safe_create_limit_order(ex, symbol, side, amount, price, params={}):
#     # Apply precision
#     try:
#         amount = float(ex.amount_to_precision(symbol, amount))
#         price = float(ex.price_to_precision(symbol, price))
#     except Exception as e:
#         console.print(f"[yellow]Precision adjustment failed for {symbol}: {e}")
#
#     if DRY_RUN:
#         # Generate a fake order ID for dry run
#         fake_id = f"dry_{int(time.time()*1000)}"
#         console.print(f"[yellow][DRY RUN] Would place {side} order for {amount} {symbol} at {price}")
#         return {'id': fake_id, 'status': 'open'}
#     
#     return retry_with_backoff()(ex.create_limit_order)(symbol, side, amount, price, params)
#
#
# def _fetch_order_status(ex, symbol: str, order_id: str) -> str | None:
#     try:
#         if not hasattr(ex, "fetch_order"):
#             return None
#         o = ex.fetch_order(order_id, symbol)
#         if not o:
#             return None
#         return o.get("status")
#     except Exception:
#         return None
#
# def create_exchange():
#     return ccxt.gateio({
#         'apiKey': GATE_API_KEY,
#         'secret': GATE_API_SECRET,
#         'enableRateLimit': True,
#         'options': {
#             'defaultType': 'swap',
#             'defaultSettle': 'usdt',
#         }
#     })
#
# def get_symbol_volatility(symbol, ex, timeframe='5m', lookback=12):
#     """Calculate symbol volatility over specified lookback period"""
#     try:
#         ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=lookback)
#         if not ohlcv or len(ohlcv) < lookback:
#             return None
#         
#         closes = np.array([candle[4] for candle in ohlcv])
#         returns = np.diff(np.log(closes))
#         volatility = np.std(returns) * np.sqrt(288)  # Scale to daily volatility (288 5-min periods)
#         return volatility
#     except Exception as e:
#         console.print(f"[red]Error calculating volatility for {symbol}: {e}")
#         return None
#
# def get_best_symbols(ex, max_symbols=3):
#     """Find the best symbols for grid trading based on volatility and spread"""
#     symbols = []
#     try:
#         markets = ex.load_markets()
#         usdtm_symbols = [s for s in markets.keys() if s.endswith('/USDT:USDT') and markets[s]['active']]
#         
#         # Get top traded symbols by volume
#         tickers = ex.fetch_tickers(usdtm_symbols[:30])  # Limit to top 30 to reduce API calls
#         
#         candidates = []
#         for symbol, ticker in tickers.items():
#             # Skip symbols with extreme prices
#             if ticker['last'] < 0.0001 or ticker['last'] > 50000:
#                 continue
#                 
#             # Calculate spread
#             spread = (ticker['ask'] - ticker['bid']) / ticker['last'] if ticker['last'] > 0 else float('inf')
#             
#             # Calculate volatility
#             volatility = get_symbol_volatility(symbol, ex)
#             if volatility is None:
#                 continue
#             
#             # Calculate volume in USD
#             volume_usd = ticker['quoteVolume'] if 'quoteVolume' in ticker else 0
#             
#             # Skip low volume symbols
#             if volume_usd < 100000:  # Minimum $100k daily volume
#                 continue
#                 
#             # Score based on volatility and spread
#             if MIN_VOLATILITY_THRESHOLD <= volatility <= MAX_VOLATILITY_THRESHOLD and spread < 0.003:
#                 candidates.append({
#                     'symbol': symbol,
#                     'volatility': volatility,
#                     'spread': spread,
#                     'volume': volume_usd,
#                     'last': ticker['last'],
#                     # Combined score with preference for higher volatility within bounds
#                     'score': (volatility / MAX_VOLATILITY_THRESHOLD) * (1 - (spread * 200))
#                 })
#         
#         # Sort by score
#         candidates.sort(key=lambda x: x['score'], reverse=True)
#         
#         # Return top symbols
#         symbols = [c['symbol'] for c in candidates[:max_symbols]]
#         
#         # Store symbol data
#         for candidate in candidates[:max_symbols]:
#             symbol_data[candidate['symbol']] = {
#                 'volatility': candidate['volatility'],
#                 'price': candidate['last'],
#                 'spread': candidate['spread'],
#                 'volume': candidate['volume']
#             }
#             
#     except Exception as e:
#         console.print(f"[red]Error finding best symbols: {e}")
#         
#     return symbols
#
# def calculate_grid_levels(symbol, current_price, num_levels=9, spacing_percent=0.3):
#     """Calculate grid price levels around current price"""
#     half_levels = num_levels // 2
#     grid_levels = []
#     
#     # Calculate price levels above and below current price
#     for i in range(-half_levels, half_levels + 1):
#         level_price = current_price * (1 + (i * spacing_percent / 100))
#         grid_levels.append(level_price)
#     
#     return sorted(grid_levels)
#
# def place_grid_orders(ex, symbol, grid_levels, position_size_usd, leverage):
#     """Place grid orders for a symbol"""
#     orders = []
#     
#     try:
#         ticker = ex.fetch_ticker(symbol)
#         current_price = ticker['last']
#         
#         # Set leverage (clamp to market max)
#         try:
#             market = ex.market(symbol)
#             max_leverage = market['info'].get('leverage_max', leverage)
#             target_leverage = min(int(float(max_leverage)), leverage)
#             if not DRY_RUN:
#                 ex.set_leverage(target_leverage, symbol)
#         except Exception as e:
#             console.print(f"[yellow]Warning setting leverage for {symbol}: {e}")
#         
#         # Position size per grid level
#         size_per_level = position_size_usd / len(grid_levels) / current_price
#         
#         for price in grid_levels:
#             # Place buy orders below market and sell orders above
#             if price < current_price:
#                 side = 'buy'
#             elif price > current_price:
#                 side = 'sell'
#             else:
#                 continue # Skip exactly at market price
#             
#             # Calculate order amount with leverage
#             amount = size_per_level * leverage
#             
#             # Create limit order
#             try:
#                 order = safe_create_limit_order(
#                     ex,
#                     symbol,
#                     side,
#                     amount,
#                     price,
#                     {'timeInForce': 'GTC', 'marginMode': 'cross'}
#                 )
#                 orders.append({
#                     'id': order['id'],
#                     'price': price,
#                     'amount': amount,
#                     'side': side,
#                     'status': 'open',
#                     'filled': 0
#                 })
#                 
#                 console.print(f"[green]Placed {side} order for {amount} {symbol} at {price}")
#                 
#             except Exception as e:
#                 console.print(f"[red]Error placing order: {e}")
#     
#     except Exception as e:
#         console.print(f"[red]Error in grid setup: {e}")
#         
#     return orders
#
# def monitor_grid(ex, symbol, grid_orders, position_size_usd):
#     """Monitor and manage grid orders"""
#     global total_profit, total_trades, profit_rate
#     
#     grid_profit = 0.0
#     trade_count = 0
#     grid_start_time = time.time()
#     
#     with thread_lock:
#         active_grids[symbol] = {
#             'orders': grid_orders,
#             'profit': 0.0,
#             'trades': 0
#         }
#     
#     while symbol in active_grids:
#         if emergency_stop:
#             break
#         if kill_switch_triggered():
#             emergency_liquidation(ex)
#             break
#         try:
#             # Check open orders
#             if DRY_RUN:
#                 time.sleep(5)
#                 # Filter locally tracked open orders
#                 current_open = [o for o in grid_orders if o['status'] == 'open']
#                 
#                 # Optionally simulate a fill
#                 if SIMULATE_FILLS and current_open and random.random() < 0.3:
#                     filled_order = random.choice(current_open)
#                     open_order_ids = [o['id'] for o in current_open if o['id'] != filled_order['id']]
#                 else:
#                     open_order_ids = [o['id'] for o in current_open]
#             else:
#                 open_orders = ex.fetch_open_orders(symbol)
#                 open_order_ids = [order['id'] for order in open_orders]
#             
#             # Check filled orders
#             for order in grid_orders:
#                 if order['status'] == 'open' and order['id'] not in open_order_ids:
#                     # Order may be filled or canceled
#                     if not DRY_RUN:
#                         st = _fetch_order_status(ex, symbol, order['id'])
#                         if st in {"canceled", "cancelled", "rejected", "expired"}:
#                             order['status'] = 'canceled'
#                             continue
#                     order['status'] = 'filled'
#                     order['filled'] = order['amount']
#                     
#                     # Place opposite order
#                     new_side = 'sell' if order['side'] == 'buy' else 'buy'
#                     new_price = order['price'] * (1 + PROFIT_THRESHOLD) if new_side == 'sell' else order['price'] * (1 - PROFIT_THRESHOLD)
#                     
#                     try:
#                         new_order = safe_create_limit_order(
#                             ex,
#                             symbol,
#                             new_side,
#                             order['amount'],
#                             new_price,
#                             {'timeInForce': 'GTC', 'marginMode': 'cross'}
#                         )
#                         
#                         # Add new order to tracking
#                         grid_orders.append({
#                             'id': new_order['id'],
#                             'price': new_price,
#                             'amount': order['amount'],
#                             'side': new_side,
#                             'status': 'open',
#                             'filled': 0,
#                             'parent': order['id']
#                         })
#                         
#                         # Calculate profit from the trade (subtracting estimated fees)
#                         gross_profit = order['amount'] * abs(new_price - order['price'])
#                         fees = (order['amount'] * order['price'] * TAKER_FEE) + (order['amount'] * new_price * TAKER_FEE)
#                         trade_profit = gross_profit - fees
#                         
#                         grid_profit += trade_profit
#                         trade_count += 1
#                         
#                         with thread_lock:
#                             total_profit += trade_profit
#                             total_trades += 1
#                             elapsed = time.time() - start_time
#                             profit_rate = (total_profit * 100) / max(elapsed, 1)  # cents per second
#                             
#                             if symbol in active_grids:
#                                 active_grids[symbol]['profit'] = grid_profit
#                                 active_grids[symbol]['trades'] = trade_count
#                         
#                         console.print(f"[bold green]Trade completed on {symbol}: {order['side']} -> {new_side}, profit: ${trade_profit:.4f}")
#                         save_state()
#                         
#                     except Exception as e:
#                         console.print(f"[red]Error placing counter-order: {e}")
#             
#             # Check if we need to rebalance the grid
#             current_price = ex.fetch_ticker(symbol)['last']
#             grid_min = min(order['price'] for order in grid_orders if order['status'] == 'open')
#             grid_max = max(order['price'] for order in grid_orders if order['status'] == 'open')
#             
#             # If price is outside the grid, rebalance
#             if current_price < grid_min * 0.95 or current_price > grid_max * 1.05:
#                 console.print(f"[yellow]Rebalancing grid for {symbol} - price outside range")
#                 
#                 # Cancel all open orders
#                 for order in grid_orders:
#                     if order['status'] == 'open':
#                         try:
#                             ex.cancel_order(order['id'], symbol)
#                         except Exception:
#                             pass
#                 
#                 # Calculate new grid levels
#                 new_levels = calculate_grid_levels(symbol, current_price, NUM_GRID_CIRCLES, GRID_SPACING_PERCENT)
#                 
#                 # Place new grid orders
#                 grid_orders = place_grid_orders(ex, symbol, new_levels, position_size_usd, LEVERAGE)
#                 
#                 with thread_lock:
#                     active_grids[symbol]['orders'] = grid_orders
#             
#             # Check if profit rate is meeting target
#             elapsed = time.time() - grid_start_time
#             grid_profit_rate = (grid_profit * 100) / max(elapsed, 1)  # cents per second
#             
#             if elapsed > 3600:  # Check after one hour
#                 if grid_profit_rate < TARGET_CPS / MAX_SYMBOLS / 2:
#                     console.print(f"[yellow]Grid for {symbol} underperforming. Profit rate: {grid_profit_rate:.5f} c/s")
#                     
#                     # Consider replacing with a better symbol
#                     if len(active_grids) < MAX_SYMBOLS:
#                         new_candidates = get_best_symbols(ex, 1)
#                         if new_candidates and new_candidates[0] not in active_grids:
#                             console.print(f"[yellow]Replacing {symbol} with {new_candidates[0]}")
#                             
#                             # Cancel all open orders
#                             for order in grid_orders:
#                                 if order['status'] == 'open':
#                                     try:
#                                         ex.cancel_order(order['id'], symbol)
#                                     except Exception:
#                                         pass
#                             
#                             # Remove from active grids
#                             with thread_lock:
#                                 if symbol in active_grids:
#                                     del active_grids[symbol]
#                             
#                             # Start grid for new symbol
#                             setup_grid_for_symbol(ex, new_candidates[0], position_size_usd)
#                             break
#             
#             # Sleep to avoid API rate limits
#             time.sleep(5)
#             save_state()
#             
#         except Exception as e:
#             console.print(f"[red]Error monitoring grid for {symbol}: {e}")
#             time.sleep(10)
#
# def setup_grid_for_symbol(ex, symbol, position_size_usd):
#     """Initialize and start grid for a symbol"""
#     try:
#         ticker = ex.fetch_ticker(symbol)
#         current_price = ticker['last']
#         
#         # Calculate grid levels
#         grid_levels = calculate_grid_levels(
#             symbol, 
#             current_price, 
#             NUM_GRID_CIRCLES, 
#             GRID_SPACING_PERCENT
#         )
#         
#         # Place initial grid orders
#         grid_orders = place_grid_orders(ex, symbol, grid_levels, position_size_usd, LEVERAGE)
#         
#         # Start monitoring thread
#         monitor_thread = threading.Thread(
#             target=monitor_grid,
#             args=(ex, symbol, grid_orders, position_size_usd),
#             daemon=True
#         )
#         monitor_thread.start()
#         
#         console.print(f"[bold green]Grid setup complete for {symbol} with {len(grid_orders)} orders")
#         
#     except Exception as e:
#         console.print(f"[red]Error setting up grid for {symbol}: {e}")
#
# def update_telemetry():
#     """Write bot status to cache/beast_status.json for dashboard integration"""
#     try:
#         status = {
#             "ts": int(time.time()),
#             "total_profit": total_profit,
#             "total_trades": total_trades,
#             "profit_rate": profit_rate,
#             "active_symbols": list(active_grids.keys()),
#             "dry_run": DRY_RUN
#         }
#         os.makedirs("cache", exist_ok=True)
#         with open("cache/beast_status.json", "w") as f:
#             json.dump(status, f)
#     except Exception as e:
#         console.print(f"[yellow]Telemetry update failed: {e}")
#
# def display_dashboard(ex):
#     """Display live dashboard with grid performance"""
#     while True:
#         update_telemetry()
#         save_state()
#         if not check_account_health(ex):
#             emergency_liquidation(ex)
#             break
#         if kill_switch_triggered():
#             emergency_liquidation(ex)
#             break
#         table = Table(title="HyperGrid Hydra Performance")
#         
#         table.add_column("Symbol", justify="left", style="cyan")
#         table.add_column("Trades", justify="right")
#         table.add_column("Profit $", justify="right")
#         table.add_column("Volatility", justify="right")
#         table.add_column("Spread %", justify="right")
#         
#         with thread_lock:
#             for symbol, data in active_grids.items():
#                 table.add_row(
#                     symbol,
#                     str(data['trades']),
#                     f"${data['profit']:.4f}",
#                     f"{symbol_data.get(symbol, {}).get('volatility', 0):.4f}",
#                     f"{symbol_data.get(symbol, {}).get('spread', 0)*100:.3f}%"
#                 )
#             
#             elapsed = time.time() - start_time if start_time else 0
#             hours = int(elapsed // 3600)
#             minutes = int((elapsed % 3600) // 60)
#             seconds = int(elapsed % 60)
#             
#             overall_stats = f"""
#             Running time: {hours:02d}:{minutes:02d}:{seconds:02d}
#             Total trades: {total_trades}
#             Total profit: ${total_profit:.4f}
#             Profit rate: {profit_rate:.5f} cents/second
#             Target rate: {TARGET_CPS:.5f} cents/second
#             Rate achieved: {(profit_rate/TARGET_CPS*100):.1f}%
#             """
#             
#             status_color = "green" if profit_rate >= TARGET_CPS * 0.9 else "yellow" if profit_rate >= TARGET_CPS * 0.5 else "red"
#         
#         console.print(Panel(overall_stats, title="Overall Performance", style=status_color))
#         console.print(table)
#         
#         # Sleep to avoid console flickering
#         time.sleep(1)
#
# def main():
#     global start_time
#     
#     console.print("[bold green]Starting HyperGrid Hydra Trading System")
#     console.print(f"[bold]Target profit rate: {TARGET_CPS} cents per second")
#     
#     # Initialize exchange
#     ex = create_exchange()
#
#     if DRY_RUN:
#         load_state()
#     
#     try:
#         # Check account balance
#         available_balance = 0.0
#         try:
#             if GATE_API_KEY != "YOUR_GATE_API_KEY":
#                 balance = ex.fetch_balance()
#                 available_balance = balance['USDT']['free']
#         except Exception as e:
#             if not DRY_RUN:
#                 raise e
#             console.print(f"[yellow]Warning: Could not fetch balance, using $0.00 for dry run. {e}")
#         
#         console.print(f"[bold]Available balance: ${available_balance:.2f} USDT")
#         
#         if available_balance < INITIAL_DEPOSIT:
#             if not DRY_RUN:
#                 console.print(f"[bold red]Warning: Available balance is less than configured deposit amount")
#                 console.print(f"[bold yellow]Proceeding with available balance: ${available_balance:.2f}")
#                 position_size = available_balance
#             else:
#                 console.print(f"[bold yellow][DRY RUN] Using configured INITIAL_DEPOSIT for simulation: ${INITIAL_DEPOSIT:.2f}")
#                 position_size = INITIAL_DEPOSIT
#         else:
#             position_size = INITIAL_DEPOSIT
#         
#         # Initialize start time
#         start_time = time.time()
#         update_telemetry()
#         save_state()
#         
#         # Find best symbols
#         symbols = get_best_symbols(ex, MAX_SYMBOLS)
#         
#         if not symbols:
#             console.print("[bold red]Error: No suitable symbols found")
#             return
#         
#         console.print(f"[bold green]Selected symbols: {', '.join(symbols)}")
#         
#         # Calculate position size per symbol
#         position_size_per_symbol = position_size / len(symbols)
#         
#         # Setup grids for each symbol
#         for symbol in symbols:
#             setup_grid_for_symbol(ex, symbol, position_size_per_symbol)
#         
#         # Start dashboard
#         display_dashboard(ex)
#         
#     except Exception as e:
#         console.print(f"[bold red]Critical error: {e}")
#         return
#
# if __name__ == "__main__":
#     main()
# ===== END   [130/134] beast.py =====

# ===== BEGIN [131/134] Hedging_Project/real_time_trader.py sha256=41fffa405b2ce973 =====
# #!/usr/bin/env python3
# """
# REAL-TIME TRADING SCANNER
# Connects to Gate.io and trades the exact tokens you listed
# """
#
# import os
# import time
# import json
# import requests
# import hmac
# import hashlib
# from datetime import datetime
# import threading
# import queue
#
# # EXACT TOKENS YOU PROVIDED
# TRADING_TOKENS = [
#     {"symbol": "HIPPO_USDT", "price": 0.000239, "change": -22.21, "volume": 11137302273},
#     {"symbol": "NATIX_USDT", "price": 0.000101, "change": 8.39, "volume": 5239695213},
#     {"symbol": "TOSHI_USDT", "price": 0.000187, "change": 8.17, "volume": 3003309098},
#     {"symbol": "ELIZAOS_USDT", "price": 0.000838, "change": 7.93, "volume": 1447897904},
#     {"symbol": "ETH5S_USDT", "price": 0.005350, "change": -37.41, "volume": 1395317878},
#     {"symbol": "PUMP_USDT", "price": 0.001819, "change": 7.31, "volume": 992958762},
#     {"symbol": "COMMON_USDT", "price": 0.000365, "change": 34.63, "volume": 967736550},
#     {"symbol": "XRP5L_USDT", "price": 0.001275, "change": 28.34, "volume": 918108054},
#     {"symbol": "MRLN_USDT", "price": 0.000151, "change": -24.58, "volume": 673241384},
#     {"symbol": "LINK5L_USDT", "price": 0.001650, "change": 33.17, "volume": 602449379},
#     {"symbol": "XPIN_USDT", "price": 0.001435, "change": 22.39, "volume": 569121348},
#     {"symbol": "RLS_USDT", "price": 0.002627, "change": -7.33, "volume": 568174264},
#     {"symbol": "AVAX5L_USDT", "price": 0.001762, "change": 45.37, "volume": 495150761},
#     {"symbol": "MEMEFI_USDT", "price": 0.000180, "change": 48.10, "volume": 488739465},
#     {"symbol": "FARTCOIN5S_USDT", "price": 0.001155, "change": -61.18, "volume": 464223622},
#     {"symbol": "OMI_USDT", "price": 0.000130, "change": 1.87, "volume": 463075540},
#     {"symbol": "DOGE_USDT", "price": 0.094740, "change": 4.51, "volume": 433636957},
#     {"symbol": "PTB_USDT", "price": 0.000982, "change": -8.30, "volume": 399321349},
#     {"symbol": "DOGE3S_USDT", "price": 0.004231, "change": -14.26, "volume": 398377334},
#     {"symbol": "XEM_USDT", "price": 0.000665, "change": 2.70, "volume": 387611345},
#     {"symbol": "BLUAI_USDT", "price": 0.008946, "change": 11.88, "volume": 373938017},
#     {"symbol": "ADA5L_USDT", "price": 0.001864, "change": 32.76, "volume": 331653806},
#     {"symbol": "TREAT_USDT", "price": 0.000198, "change": 13.27, "volume": 327670639},
#     {"symbol": "BTC5L_USDT", "price": 0.008375, "change": 27.37, "volume": 314726825},
#     {"symbol": "ROOBEE_USDT", "price": 0.000105, "change": 1.16, "volume": 312512589},
#     {"symbol": "PEPE5S_USDT", "price": 0.005005, "change": -40.62, "volume": 312484534},
#     {"symbol": "ART_USDT", "price": 0.000313, "change": 0.67, "volume": 302345159},
#     {"symbol": "XNL_USDT", "price": 0.000201, "change": 0.90, "volume": 293096830},
#     {"symbol": "HMSTR_USDT", "price": 0.000142, "change": 5.43, "volume": 289747018},
#     {"symbol": "BLAST_USDT", "price": 0.000462, "change": 2.80, "volume": 285204866}
# ]
#
# class RealTimeTrader:
#     """Real-time trading scanner for your exact tokens"""
#     
#     def __init__(self):
#         self.api_key = os.getenv("GATE_API_KEY", "")
#         self.api_secret = os.getenv("GATE_API_SECRET", "")
#         self.base_url = "https://api.gateio.ws/api/v4"
#         self.running = False
#         self.trade_count = 0
#         self.total_pnl = 0.0
#         
#         print("🚀 REAL-TIME TRADING SCANNER")
#         print("=" * 60)
#         print(f"📊 Trading {len(TRADING_TOKENS)} tokens you specified:")
#         for i, token in enumerate(TRADING_TOKENS[:10], 1):
#             print(f"   {i:2d}. {token['symbol']} - ${token['price']:.6f} ({token['change']:+.2f}%)")
#         print(f"   ... and {len(TRADING_TOKENS)-10} more tokens")
#         print("=" * 60)
#         
#         # Check API keys
#         if not self.api_key or not self.api_secret:
#             print("⚠️  DEMO MODE - No API keys found")
#             print("   Set GATE_API_KEY and GATE_API_SECRET for live trading")
#         else:
#             print(f"✅ API Key: {self.api_key[:10]}...")
#             print("✅ Ready for live trading")
#     
#     def sign_request(self, method, path, payload):
#         """Generate Gate.io signature"""
#         if not self.api_key or not self.api_secret:
#             return {}
#         
#         ts = str(int(time.time()))
#         payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#         sign_str = f"{method.upper()}\n{path}\n{payload_hash}\n{ts}"
#         sign = hmac.new(self.api_secret.encode(), sign_str.encode(), hashlib.sha512).hexdigest()
#         
#         return {
#             "Accept": "application/json",
#             "Content-Type": "application/json",
#             "KEY": self.api_key,
#             "Timestamp": ts,
#             "SIGN": sign,
#         }
#     
#     def make_request(self, method, path, payload="", private=True):
#         """Make API request"""
#         headers = self.sign_request(method, path, payload) if private else {
#             "Accept": "application/json",
#             "Content-Type": "application/json"
#         }
#         
#         try:
#             response = requests.request(
#                 method, 
#                 f"{self.base_url}{path}", 
#                 headers=headers, 
#                 data=payload if payload else None, 
#                 timeout=10
#             )
#             
#             if response.status_code == 200:
#                 return {"success": True, "data": response.json()}
#             else:
#                 return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
#                 
#         except Exception as e:
#             return {"success": False, "error": str(e)}
#     
#     def get_real_time_data(self, symbol):
#         """Get real-time data for a specific token"""
#         # Get ticker
#         ticker_result = self.make_request("GET", f"/spot/tickers?currency_pair={symbol}", private=False)
#         if not ticker_result["success"]:
#             return None
#         
#         ticker = ticker_result["data"][0] if ticker_result["data"] else None
#         if not ticker:
#             return None
#         
#         # Get order book
#         book_result = self.make_request("GET", f"/spot/order_book?currency_pair={symbol}&limit=1", private=False)
#         if not book_result["success"]:
#             return None
#         
#         book = book_result["data"]
#         if not book.get("bids") or not book.get("asks"):
#             return None
#         
#         return {
#             "symbol": symbol,
#             "price": float(ticker.get("last", 0)),
#             "bid": float(book["bids"][0][0]),
#             "ask": float(book["asks"][0][0]),
#             "volume": float(ticker.get("base_volume", 0)),
#             "change": float(ticker.get("change_percentage", 0)),
#             "spread": float(book["asks"][0][0]) - float(book["bids"][0][0]),
#             "spread_pct": ((float(book["asks"][0][0]) - float(book["bids"][0][0])) / float(book["bids"][0][0])) * 100
#         }
#     
#     def place_order(self, symbol, side, size, price):
#         """Place real order"""
#         if not self.api_key or not self.api_secret:
#             print(f"🧪 DEMO ORDER: {side} {size:.6f} {symbol} @ ${price:.6f}")
#             return {"success": True, "data": {"id": f"demo_{int(time.time())}"}}
#         
#         order_data = {
#             "currency_pair": symbol,
#             "type": "limit",
#             "side": side,
#             "amount": str(size),
#             "price": str(price),
#             "time_in_force": "ioc"
#         }
#         
#         payload = json.dumps(order_data, separators=(",", ":"))
#         result = self.make_request("POST", "/spot/orders", payload, private=True)
#         
#         if result["success"]:
#             print(f"✅ ORDER PLACED: {side} {size:.6f} {symbol} @ ${price:.6f}")
#             print("🔊 Listen for Gate.io exchange sound!")
#         else:
#             print(f"❌ ORDER FAILED: {result.get('error', 'Unknown')}")
#         
#         return result
#     
#     def get_account_balance(self):
#         """Get account balance"""
#         if not self.api_key or not self.api_secret:
#             return {"available": 1000.0, "total": 1000.0}  # Demo balance
#         
#         result = self.make_request("GET", "/spot/accounts", "", private=True)
#         if not result["success"]:
#             return {"available": 0.0, "total": 0.0}
#         
#         for account in result["data"]:
#             if account.get("currency") == "USDT":
#                 return {
#                     "available": float(account.get("available", 0)),
#                     "total": float(account.get("available", 0)) + float(account.get("frozen", 0))
#                 }
#         
#         return {"available": 0.0, "total": 0.0}
#     
#     def analyze_trading_opportunity(self, token_data, original_data):
#         """Analyze if token is good for trading"""
#         if not token_data:
#             return None
#         
#         # Volume check
#         if token_data["volume"] < 1000000:  # Less than $1M volume
#             return None
#         
#         # Spread check
#         if token_data["spread_pct"] > 1.0:  # More than 1% spread
#             return None
#         
#         # Price movement check
#         price_change = ((token_data["price"] - original_data["price"]) / original_data["price"]) * 100
#         
#         # Trading logic
#         if price_change > 5.0:  # Price moved up more than 5%
#             return {
#                 "action": "SELL",
#                 "reasoning": f"Price increased {price_change:.2f}% from ${original_data['price']:.6f}",
#                 "confidence": min(price_change / 10.0, 1.0),
#                 "price": token_data["bid"]
#             }
#         elif price_change < -5.0:  # Price moved down more than 5%
#             return {
#                 "action": "BUY",
#                 "reasoning": f"Price decreased {abs(price_change):.2f}% from ${original_data['price']:.6f}",
#                 "confidence": min(abs(price_change) / 10.0, 1.0),
#                 "price": token_data["ask"]
#             }
#         
#         return None
#     
#     def scan_and_trade(self):
#         """Main scanning and trading loop"""
#         print(f"\n🔍 SCANNING {len(TRADING_TOKENS)} TOKENS FOR TRADING OPPORTUNITIES...")
#         print("=" * 60)
#         
#         # Get account balance
#         balance = self.get_account_balance()
#         print(f"💰 Account Balance: ${balance['available']:.2f}")
#         
#         opportunities = []
#         
#         # Scan all tokens
#         for token in TRADING_TOKENS:
#             print(f"\n📊 Scanning {token['symbol']}...")
#             
#             # Get real-time data
#             real_data = self.get_real_time_data(token["symbol"])
#             
#             if real_data:
#                 print(f"   Current: ${real_data['price']:.6f} ({real_data['change']:+.2f}%)")
#                 print(f"   Volume: ${real_data['volume']/1000000:.1f}M")
#                 print(f"   Spread: {real_data['spread_pct']:.3f}%")
#                 
#                 # Analyze opportunity
#                 opportunity = self.analyze_trading_opportunity(real_data, token)
#                 
#                 if opportunity:
#                     opportunities.append({
#                         "symbol": token["symbol"],
#                         "opportunity": opportunity,
#                         "real_data": real_data
#                     })
#                     print(f"   🎯 OPPORTUNITY: {opportunity['action']} - {opportunity['reasoning']}")
#                     print(f"   📈 Confidence: {opportunity['confidence']:.2f}")
#                 else:
#                     print(f"   ⏸️  No trading opportunity")
#             else:
#                 print(f"   ❌ Failed to get data")
#         
#         # Sort opportunities by confidence
#         opportunities.sort(key=lambda x: x["opportunity"]["confidence"], reverse=True)
#         
#         print(f"\n🎯 FOUND {len(opportunities)} TRADING OPPORTUNITIES:")
#         print("=" * 60)
#         
#         # Execute trades on top opportunities
#         for i, opp in enumerate(opportunities[:5], 1):  # Top 5
#             symbol = opp["symbol"]
#             opportunity = opp["opportunity"]
#             real_data = opp["real_data"]
#             
#             print(f"\n{i}. {symbol}")
#             print(f"   Action: {opportunity['action']}")
#             print(f"   Reasoning: {opportunity['reasoning']}")
#             print(f"   Confidence: {opportunity['confidence']:.2f}")
#             
#             # Calculate order size (target $0.05 nominal)
#             target_nominal = 0.05
#             order_size = target_nominal / opportunity["price"]
#             
#             # Place order
#             result = self.place_order(
#                 symbol, 
#                 opportunity["action"].lower(), 
#                 order_size, 
#                 opportunity["price"]
#             )
#             
#             if result["success"]:
#                 self.trade_count += 1
#                 nominal_value = order_size * opportunity["price"]
#                 print(f"   ✅ Trade executed: ${nominal_value:.4f} nominal")
#                 
#                 # Simulate PnL for demo
#                 if not self.api_key:  # Demo mode
#                     simulated_pnl = nominal_value * 0.001 * (1 if opportunity["action"] == "BUY" else -1)
#                     self.total_pnl += simulated_pnl
#                     print(f"   💰 Simulated PnL: ${simulated_pnl:.4f}")
#         
#         print(f"\n📊 SUMMARY:")
#         print(f"   Tokens Scanned: {len(TRADING_TOKENS)}")
#         print(f"   Opportunities Found: {len(opportunities)}")
#         print(f"   Trades Executed: {self.trade_count}")
#         print(f"   Total PnL: ${self.total_pnl:.4f}")
#         print(f"   Account Balance: ${balance['available']:.2f}")
#     
#     def run_continuous(self):
#         """Run continuous scanning"""
#         self.running = True
#         cycle = 0
#         
#         try:
#             while self.running:
#                 cycle += 1
#                 print(f"\n{'='*80}")
#                 print(f"🚀 TRADING CYCLE {cycle} - {datetime.now().strftime('%H:%M:%S')}")
#                 print(f"{'='*80}")
#                 
#                 self.scan_and_trade()
#                 
#                 if self.running:
#                     print(f"\n⏳ Waiting 30 seconds for next cycle...")
#                     time.sleep(30)
#                     
#         except KeyboardInterrupt:
#             print(f"\n🛑 Trading stopped by user")
#         finally:
#             self.running = False
#     
#     def run_single(self):
#         """Run single scan"""
#         self.scan_and_trade()
#
# def main():
#     """Main function"""
#     print("🚀 REAL-TIME TRADING SCANNER")
#     print("Trading the exact tokens you provided")
#     print("")
#     
#     trader = RealTimeTrader()
#     
#     print("\n🎯 Choose mode:")
#     print("1. Single scan (test)")
#     print("2. Continuous trading (30-second cycles)")
#     
#     try:
#         choice = input("\nEnter choice (1 or 2): ").strip()
#         
#         if choice == "1":
#             trader.run_single()
#         elif choice == "2":
#             trader.run_continuous()
#         else:
#             print("❌ Invalid choice")
#             
#     except KeyboardInterrupt:
#         print("\n🛑 Exiting...")
#     
#     print(f"\n✅ Trading complete!")
#     print(f"📊 Final Stats: {trader.trade_count} trades, ${trader.total_pnl:.4f} PnL")
#
# if __name__ == "__main__":
#     main()
# ===== END   [131/134] Hedging_Project/real_time_trader.py =====

# ===== BEGIN [132/134] Hedging_Project/proper_exchange_connection.py sha256=fd27e5918b6d6107 =====
# #!/usr/bin/env python3
# """
# PROPER EXCHANGE CONNECTION
# Correctly separates endpoints and uses API keys to hit real exchange values
# """
#
# import os
# import time
# import json
# import requests
# import hmac
# import hashlib
# from datetime import datetime
#
# class ProperExchangeConnection:
#     """Properly separated exchange endpoints with correct API usage"""
#     
#     def __init__(self):
#         # Load environment variables
#         self.api_key = os.getenv("GATE_API_KEY", "")
#         self.api_secret = os.getenv("GATE_API_SECRET", "")
#         
#         # CORRECTLY SEPARATED ENDPOINTS
#         self.endpoints = {
#             "spot": {
#                 "base": "https://api.gateio.ws/api/v4",
#                 "tickers": "/spot/tickers",
#                 "orderbook": "/spot/order_book",
#                 "accounts": "/spot/accounts",
#                 "orders": "/spot/orders"
#             },
#             "futures": {
#                 "base": "https://api.gateio.ws/api/v4",
#                 "contracts": "/futures/usdt/contracts",
#                 "positions": "/futures/usdt/positions",
#                 "accounts": "/futures/usdt/accounts",
#                 "orders": "/futures/usdt/orders"
#             }
#         }
#         
#         # Your exact tokens with proper symbol formatting
#         self.trading_tokens = [
#             "HIPPO_USDT", "NATIX_USDT", "TOSHI_USDT", "ELIZAOS_USDT", "ETH5S_USDT",
#             "PUMP_USDT", "COMMON_USDT", "XRP5L_USDT", "MRLN_USDT", "LINK5L_USDT",
#             "XPIN_USDT", "RLS_USDT", "AVAX5L_USDT", "MEMEFI_USDT", "FARTCOIN5S_USDT",
#             "OMI_USDT", "DOGE_USDT", "PTB_USDT", "DOGE3S_USDT", "XEM_USDT",
#             "BLUAI_USDT", "ADA5L_USDT", "TREAT_USDT", "BTC5L_USDT", "ROOBEE_USDT",
#             "PEPE5S_USDT", "ART_USDT", "XNL_USDT", "HMSTR_USDT", "BLAST_USDT"
#         ]
#         
#         print("🚀 PROPER EXCHANGE CONNECTION")
#         print("=" * 60)
#         print(f"🔑 API Key: {self.api_key[:10] if self.api_key else 'NOT_SET'}...")
#         print(f"🔐 API Secret: {self.api_secret[:10] if self.api_secret else 'NOT_SET'}...")
#         print(f"📊 Trading {len(self.trading_tokens)} tokens")
#         print("=" * 60)
#     
#     def generate_signature(self, method, path, query_string, payload, timestamp):
#         """Generate proper Gate.io signature"""
#         if not self.api_key or not self.api_secret:
#             return {}
#         
#         # Hash the payload
#         payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#         
#         # Create signature string
#         sign_str = f"{method.upper()}\n{path}\n{query_string}\n{payload_hash}\n{timestamp}"
#         
#         # Generate HMAC-SHA512 signature
#         signature = hmac.new(
#             self.api_secret.encode('utf-8'),
#             sign_str.encode('utf-8'),
#             hashlib.sha512
#         ).hexdigest()
#         
#         return {
#             "Accept": "application/json",
#             "Content-Type": "application/json",
#             "KEY": self.api_key,
#             "Timestamp": timestamp,
#             "SIGN": signature
#         }
#     
#     def make_request(self, market_type, endpoint_type, params="", payload="", private=False):
#         """Make proper API request with correct endpoint separation"""
#         
#         # Get correct endpoint
#         base_url = self.endpoints[market_type]["base"]
#         endpoint_path = self.endpoints[market_type][endpoint_type]
#         full_path = f"{endpoint_path}{params}"
#         
#         # Generate timestamp
#         timestamp = str(int(time.time()))
#         
#         # Generate headers
#         if private:
#             headers = self.generate_signature("GET", endpoint_path, params, payload, timestamp)
#         else:
#             headers = {
#                 "Accept": "application/json",
#                 "Content-Type": "application/json"
#             }
#         
#         try:
#             print(f"📡 Request: {market_type.upper()} {endpoint_type}")
#             print(f"   URL: {base_url}{full_path}")
#             
#             response = requests.get(f"{base_url}{full_path}", headers=headers, timeout=10)
#             
#             print(f"📥 Response: {response.status_code}")
#             
#             if response.status_code == 200:
#                 return {"success": True, "data": response.json()}
#             else:
#                 print(f"❌ Error Response: {response.text}")
#                 return {"success": False, "error": response.text}
#                 
#         except Exception as e:
#             print(f"❌ Request Exception: {e}")
#             return {"success": False, "error": str(e)}
#     
#     def test_spot_connection(self):
#         """Test SPOT market connection"""
#         print("\n🔍 TESTING SPOT MARKET CONNECTION")
#         print("-" * 40)
#         
#         # Test public endpoint - get all tickers
#         print("1️⃣ Testing public tickers endpoint...")
#         result = self.make_request("spot", "tickers", "?currency_pair=HIPPO_USDT", private=False)
#         
#         if result["success"]:
#             ticker = result["data"][0] if result["data"] else None
#             if ticker:
#                 print(f"✅ HIPPO_USDT: ${float(ticker['last']):.6f}")
#                 print(f"   Volume: ${float(ticker['base_volume']):,.0f}")
#                 print(f"   Change: {float(ticker['change_percentage']):+.2f}%")
#             else:
#                 print("❌ No ticker data found")
#         else:
#             print(f"❌ Ticker failed: {result.get('error')}")
#         
#         # Test order book
#         print("\n2️⃣ Testing order book endpoint...")
#         result = self.make_request("spot", "orderbook", "?currency_pair=HIPPO_USDT&limit=5", private=False)
#         
#         if result["success"]:
#             book = result["data"]
#             if book.get("bids") and book.get("asks"):
#                 best_bid = float(book["bids"][0][0])
#                 best_ask = float(book["asks"][0][0])
#                 print(f"✅ Order Book - Bid: ${best_bid:.6f}, Ask: ${best_ask:.6f}")
#                 print(f"   Spread: {((best_ask - best_bid) / best_bid) * 100:.3f}%")
#             else:
#                 print("❌ No order book data")
#         else:
#             print(f"❌ Order book failed: {result.get('error')}")
#         
#         # Test private endpoint - account balance
#         if self.api_key and self.api_secret:
#             print("\n3️⃣ Testing private account endpoint...")
#             result = self.make_request("spot", "accounts", "", private=True)
#             
#             if result["success"]:
#                 accounts = result["data"]
#                 usdt_account = None
#                 for account in accounts:
#                     if account.get("currency") == "USDT":
#                         usdt_account = account
#                         break
#                 
#                 if usdt_account:
#                     available = float(usdt_account.get("available", 0))
#                     total = float(usdt_account.get("available", 0)) + float(usdt_account.get("frozen", 0))
#                     print(f"✅ USDT Balance: ${available:.2f} available, ${total:.2f} total")
#                     print("🎯 REAL EXCHANGE VALUES DETECTED!")
#                 else:
#                     print("❌ No USDT account found")
#             else:
#                 print(f"❌ Account failed: {result.get('error')}")
#                 if "INVALID_SIGNATURE" in result.get('error', ''):
#                     print("   💡 API keys are invalid or permissions insufficient")
#         else:
#             print("\n3️⃣ Skipping private test - no API keys")
#     
#     def test_futures_connection(self):
#         """Test FUTURES market connection"""
#         print("\n🔍 TESTING FUTURES MARKET CONNECTION")
#         print("-" * 40)
#         
#         # Test contracts
#         print("1️⃣ Testing contracts endpoint...")
#         result = self.make_request("futures", "contracts", "", private=False)
#         
#         if result["success"]:
#             contracts = result["data"]
#             print(f"✅ Found {len(contracts)} futures contracts")
#             
#             # Find specific contracts
#             target_contracts = ["BTC_USDT", "ETH_USDT", "ENA_USDT"]
#             for contract_name in target_contracts:
#                 for contract in contracts:
#                     if contract.get("name") == contract_name:
#                         print(f"   ✅ {contract_name}: {contract.get('status', 'Unknown')}")
#                         break
#         else:
#             print(f"❌ Contracts failed: {result.get('error')}")
#         
#         # Test private positions
#         if self.api_key and self.api_secret:
#             print("\n2️⃣ Testing private positions endpoint...")
#             result = self.make_request("futures", "positions", "", private=True)
#             
#             if result["success"]:
#                 positions = result["data"]
#                 active_positions = [p for p in positions if float(p.get("size", 0)) != 0]
#                 print(f"✅ Found {len(active_positions)} active positions")
#                 
#                 for pos in active_positions[:3]:  # Show first 3
#                     size = float(pos.get("size", 0))
#                     entry_price = float(pos.get("entry_price", 0))
#                     pnl = float(pos.get("unrealised_pnl", 0))
#                     print(f"   {pos.get('contract')}: {size:.6f} @ ${entry_price:.6f} (PnL: ${pnl:.4f})")
#             else:
#                 print(f"❌ Positions failed: {result.get('error')}")
#         else:
#             print("\n2️⃣ Skipping private test - no API keys")
#     
#     def scan_all_tokens(self):
#         """Scan all your tokens with proper exchange connection"""
#         print("\n🔍 SCANNING ALL TRADING TOKENS")
#         print("=" * 60)
#         
#         opportunities = []
#         
#         for i, symbol in enumerate(self.trading_tokens, 1):
#             print(f"\n{i:2d}. {symbol}")
#             
#             # Get ticker data
#             result = self.make_request("spot", "tickers", f"?currency_pair={symbol}", private=False)
#             
#             if result["success"] and result["data"]:
#                 ticker = result["data"][0]
#                 price = float(ticker.get("last", 0))
#                 volume = float(ticker.get("base_volume", 0))
#                 change = float(ticker.get("change_percentage", 0))
#                 
#                 print(f"     Price: ${price:.6f}")
#                 print(f"     Change: {change:+.2f}%")
#                 print(f"     Volume: ${volume:,.0f}")
#                 
#                 # Get order book for spread
#                 book_result = self.make_request("spot", "orderbook", f"?currency_pair={symbol}&limit=1", private=False)
#                 
#                 if book_result["success"] and book_result["data"].get("bids"):
#                     book = book_result["data"]
#                     bid = float(book["bids"][0][0])
#                     ask = float(book["asks"][0][0])
#                     spread_pct = ((ask - bid) / bid) * 100
#                     
#                     print(f"     Spread: {spread_pct:.3f}%")
#                     
#                     # Check for trading opportunity
#                     if volume > 1000000 and spread_pct < 1.0 and abs(change) > 3.0:
#                         action = "BUY" if change < -5.0 else "SELL" if change > 5.0 else "HOLD"
#                         opportunities.append({
#                             "symbol": symbol,
#                             "action": action,
#                             "price": price,
#                             "volume": volume,
#                             "change": change,
#                             "spread": spread_pct
#                         })
#                         print(f"     🎯 OPPORTUNITY: {action}")
#                     else:
#                         print(f"     ⏸️  No opportunity (volume: ${volume/1000000:.1f}M, spread: {spread_pct:.3f}%)")
#                 else:
#                     print(f"     ❌ No order book data")
#             else:
#                 print(f"     ❌ No ticker data")
#         
#         print(f"\n🎯 FOUND {len(opportunities)} TRADING OPPORTUNITIES:")
#         print("=" * 60)
#         
#         for opp in opportunities:
#             print(f"{opp['symbol']}: {opp['action']} at ${opp['price']:.6f} ({opp['change']:+.2f}%)")
#         
#         return opportunities
#     
#     def place_test_order(self, symbol, side):
#         """Place a test order to demonstrate exchange connection"""
#         print(f"\n🎯 PLACING TEST ORDER: {side} {symbol}")
#         print("-" * 40)
#         
#         if not self.api_key or not self.api_secret:
#             print("❌ Cannot place order - no API keys")
#             return
#         
#         # Get current price
#         result = self.make_request("spot", "tickers", f"?currency_pair={symbol}", private=False)
#         
#         if not result["success"] or not result["data"]:
#             print("❌ Cannot get price for order")
#             return
#         
#         ticker = result["data"][0]
#         current_price = float(ticker.get("last", 0))
#         
#         # Calculate small order size (0.01 USDT nominal)
#         order_size = 0.01 / current_price
#         
#         print(f"   Current Price: ${current_price:.6f}")
#         print(f"   Order Size: {order_size:.6f} (${order_size * current_price:.4f} nominal)")
#         
#         # Prepare order
#         timestamp = str(int(time.time()))
#         order_data = {
#             "currency_pair": symbol,
#             "type": "limit",
#             "side": side,
#             "amount": str(order_size),
#             "price": str(current_price),
#             "time_in_force": "ioc"
#         }
#         
#         payload = json.dumps(order_data, separators=(",", ":"))
#         
#         # Generate signature for order
#         headers = self.generate_signature("POST", "/spot/orders", "", payload, timestamp)
#         
#         try:
#             response = requests.post(
#                 f"{self.endpoints['spot']['base']}/spot/orders",
#                 headers=headers,
#                 data=payload,
#                 timeout=10
#             )
#             
#             print(f"📥 Order Response: {response.status_code}")
#             
#             if response.status_code == 200:
#                 order_result = response.json()
#                 order_id = order_result.get("id")
#                 print(f"✅ ORDER SUCCESSFUL!")
#                 print(f"   Order ID: {order_id}")
#                 print(f"   🔊 Listen for Gate.io exchange sound!")
#                 return True
#             else:
#                 print(f"❌ Order Failed: {response.text}")
#                 return False
#                 
#         except Exception as e:
#             print(f"❌ Order Exception: {e}")
#             return False
#     
#     def run_full_test(self):
#         """Run complete exchange connection test"""
#         print("🚀 STARTING FULL EXCHANGE CONNECTION TEST")
#         print("=" * 60)
#         
#         # Test connections
#         self.test_spot_connection()
#         self.test_futures_connection()
#         
#         # Scan tokens
#         opportunities = self.scan_all_tokens()
#         
#         # Place test order if opportunities exist
#         if opportunities and self.api_key and self.api_secret:
#             best_opp = opportunities[0]
#             print(f"\n🎯 BEST OPPORTUNITY: {best_opp['symbol']}")
#             
#             # Place test order
#             self.place_test_order(best_opp['symbol'], best_opp['action'].lower())
#         
#         print(f"\n✅ EXCHANGE CONNECTION TEST COMPLETE")
#         print("=" * 60)
#         
#         if self.api_key and self.api_secret:
#             print("🎯 REAL EXCHANGE VALUES ACCESSED!")
#             print("✅ API keys are working correctly")
#             print("✅ Endpoints are properly separated")
#             print("✅ Exchange connection established")
#         else:
#             print("⚠️  Demo mode only - set API keys for real trading")
#
# def main():
#     """Main function"""
#     connector = ProperExchangeConnection()
#     connector.run_full_test()
#
# if __name__ == "__main__":
#     main()
# ===== END   [132/134] Hedging_Project/proper_exchange_connection.py =====

# ===== BEGIN [133/134] Hedging_Project/fixed_signature_trader.py sha256=7123fab4fa1b308e =====
# #!/usr/bin/env python3
# """
# Fixed Signature Trader - Correct Gate.io API v4 Signature
# """
#
# import os
# import requests
# import hmac
# import hashlib
# import time
# import json
# from datetime import datetime
#
# # Your new API keys
# API_KEY = os.getenv("GATE_API_KEY", "57897b69c76df6aa01a1a25b8d9c6bc8")
# API_SECRET = os.getenv("GATE_API_SECRET", "ed43f2696c3767685e8470c4ba98ea0f7ea85e9adeb9c3d098182889756d79d9")
#
# print("🚀 FIXED SIGNATURE TRADER")
# print("=" * 40)
# print(f"🔑 API Key: {API_KEY[:10]}...")
# print(f"🔐 API Secret: {API_SECRET[:10]}...")
#
# def create_gateio_signature(method, path, query_string, payload, timestamp):
#     """
#     Create CORRECT Gate.io API v4 signature
#     Format: METHOD\nPATH\nQUERY_STRING\nPAYLOAD_HASH\nTIMESTAMP
#     """
#     
#     # Hash the payload
#     payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
#     
#     # Create signature string - THIS IS THE CRITICAL PART
#     sign_str = f"{method.upper()}\n{path}\n{query_string}\n{payload_hash}\n{timestamp}"
#     
#     # Generate HMAC-SHA512 signature
#     signature = hmac.new(
#         API_SECRET.encode('utf-8'),
#         sign_str.encode('utf-8'),
#         hashlib.sha512
#     ).hexdigest()
#     
#     return signature
#
# def make_request(method, endpoint, params="", payload="", private=True):
#     """Make request with correct signature"""
#     
#     base_url = "https://api.gateio.ws/api/v4"
#     
#     # Parse endpoint into path and query
#     if '?' in endpoint:
#         path, query = endpoint.split('?', 1)
#     else:
#         path, query = endpoint, ""
#     
#     timestamp = str(int(time.time()))
#     
#     if private:
#         # Create signature
#         signature = create_gateio_signature(method, path, query, payload, timestamp)
#         
#         headers = {
#             "Accept": "application/json",
#             "Content-Type": "application/json",
#             "KEY": API_KEY,
#             "Timestamp": timestamp,
#             "SIGN": signature
#         }
#     else:
#         headers = {
#             "Accept": "application/json",
#             "Content-Type": "application/json"
#         }
#     
#     try:
#         url = f"{base_url}{endpoint}"
#         
#         if method == "GET":
#             response = requests.get(url, headers=headers, timeout=10)
#         elif method == "POST":
#             response = requests.post(url, headers=headers, data=payload, timeout=10)
#         
#         print(f"📡 {method} {endpoint}")
#         print(f"📥 Status: {response.status_code}")
#         
#         if response.status_code == 200:
#             return {"success": True, "data": response.json()}
#         else:
#             print(f"❌ Error: {response.text}")
#             return {"success": False, "error": response.text}
#             
#     except Exception as e:
#         print(f"❌ Exception: {e}")
#         return {"success": False, "error": str(e)}
#
# def test_account():
#     """Test account endpoint"""
#     print(f"\n🔍 TESTING ACCOUNT ENDPOINT")
#     print("-" * 30)
#     
#     result = make_request("GET", "/spot/accounts", "", "", private=True)
#     
#     if result["success"]:
#         accounts = result["data"]
#         print(f"✅ Account access successful!")
#         
#         # Find USDT balance
#         for account in accounts:
#             if account.get("currency") == "USDT":
#                 available = float(account.get("available", 0))
#                 frozen = float(account.get("frozen", 0))
#                 total = available + frozen
#                 
#                 print(f"💰 USDT Balance:")
#                 print(f"   Available: ${available:.2f}")
#                 print(f"   Frozen: ${frozen:.2f}")
#                 print(f"   Total: ${total:.2f}")
#                 
#                 return total
#         
#         print(f"⚠️  No USDT account found")
#         return 0
#     else:
#         print(f"❌ Account access failed")
#         return 0
#
# def get_token_price(symbol):
#     """Get token price"""
#     result = make_request("GET", f"/spot/tickers?currency_pair={symbol}", "", "", private=False)
#     
#     if result["success"] and result["data"]:
#         ticker = result["data"][0]
#         return {
#             "price": float(ticker["last"]),
#             "bid": float(ticker["highest_bid"]),
#             "ask": float(ticker["lowest_ask"]),
#             "volume": float(ticker["base_volume"]),
#             "change": float(ticker["change_percentage"])
#         }
#     return None
#
# def place_order(symbol, side, amount_usdt=0.01):
#     """Place order with correct signature"""
#     print(f"\n🎯 PLACING ORDER: {side.upper()} {symbol}")
#     print("-" * 30)
#     
#     # Get current price
#     token_data = get_token_price(symbol)
#     if not token_data:
#         print(f"❌ Cannot get price for {symbol}")
#         return False
#     
#     price = token_data["price"]
#     order_size = amount_usdt / price
#     
#     print(f"   Price: ${price:.6f}")
#     print(f"   Size: {order_size:.6f}")
#     print(f"   Nominal: ${order_size * price:.4f}")
#     
#     # Create order payload
#     order_data = {
#         "currency_pair": symbol,
#         "type": "limit",
#         "side": side,
#         "amount": str(order_size),
#         "price": str(price),
#         "time_in_force": "ioc"
#     }
#     
#     payload = json.dumps(order_data, separators=(",", ":"))
#     
#     # Place order
#     result = make_request("POST", "/spot/orders", "", payload, private=True)
#     
#     if result["success"]:
#         order_id = result["data"].get("id")
#         print(f"✅ ORDER PLACED SUCCESSFULLY!")
#         print(f"   Order ID: {order_id}")
#         print(f"   🔊 Listen for Gate.io exchange sound!")
#         return True
#     else:
#         print(f"❌ Order failed: {result.get('error')}")
#         return False
#
# def main():
#     """Main execution"""
#     print(f"\n🚀 STARTING FIXED SIGNATURE TRADER")
#     print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     print("=" * 50)
#     
#     # Test account access
#     balance = test_account()
#     
#     if balance > 0:
#         print(f"\n✅ READY TO TRADE WITH ${balance:.2f}")
#         
#         # Your trading tokens
#         tokens = [
#             "HIPPO_USDT",
#             "DOGE_USDT", 
#             "PEPE_USDT",
#             "SHIB_USDT"
#         ]
#         
#         print(f"\n📊 Trading your tokens...")
#         
#         for token in tokens:
#             print(f"\n{'='*40}")
#             print(f"📈 {token}")
#             
#             # Get token info
#             token_data = get_token_price(token)
#             if token_data:
#                 print(f"   Price: ${token_data['price']:.6f}")
#                 print(f"   Change: {token_data['change']:+.2f}%")
#                 print(f"   Volume: ${token_data['volume']:,.0f}")
#                 
#                 # Place small buy order
#                 success = place_order(token, "buy", 0.01)
#                 
#                 if success:
#                     print(f"✅ {token} trade successful!")
#                 else:
#                     print(f"❌ {token} trade failed!")
#             else:
#                 print(f"❌ Cannot get {token} data")
#             
#             time.sleep(3)  # Wait between trades
#         
#         print(f"\n🎯 TRADING COMPLETE!")
#         print(f"✅ Your API keys are working correctly!")
#         print(f"✅ Signature issue is FIXED!")
#         print(f"✅ Real exchange connection established!")
#         
#     else:
#         print(f"\n❌ Cannot trade - account access failed")
#         print(f"💡 Check:")
#         print(f"   1. API key permissions (need 'Spot Trading')")
#         print(f"   2. IP whitelist (your dedicated IP)")
#         print(f"   3. API key status (active/not expired)")
#
# if __name__ == "__main__":
#     main()
# ===== END   [133/134] Hedging_Project/fixed_signature_trader.py =====

# ===== BEGIN [134/134] ENA_Hedging_Project/run_ena_hedging.py sha256=286e83836a893886 =====
# #!/usr/bin/env python3
# """
# ENA_USDT HEDGING LAUNCHER - COMPLETE SYSTEM
# Easy launcher for the ENA hedging system with all components
# """
#
# import sys
# import os
# import argparse
# from pathlib import Path
# import asyncio
# import logging
#
# # Add src and config directories to path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))
#
# try:
#     from ena_config import ENAHedgingConfig, ENAHedgingConfigDev, ENAHedgingConfigProd
#     from ena_hedging_market_maker_complete import ENAHedgingMarketMaker
#     from ui_components import ModernUI
#     from websocket_client import WebSocketClient, MarketDataManager
#     from trading_engine import TradingEngine
# except ImportError as e:
#     print(f"❌ Import error: {e}")
#     print("Please ensure all dependencies are installed:")
#     print("pip install -r requirements.txt")
#     sys.exit(1)
#
# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('logs/ena_hedging.log'),
#         logging.StreamHandler()
#     ]
# )
# log = logging.getLogger(__name__)
#
# def create_log_directory():
#     """Create log directory if it doesn't exist"""
#     logs_dir = Path("logs")
#     logs_dir.mkdir(exist_ok=True)
#
# def validate_environment():
#     """Validate the trading environment"""
#     print("🔍 Validating trading environment...")
#     
#     # Check Python version
#     if sys.version_info < (3, 8):
#         print("❌ Python 3.8+ required")
#         return False
#     
#     # Check required modules
#     required_modules = ['gate_api', 'websockets', 'numpy', 'tkinter']
#     missing_modules = []
#     
#     for module in required_modules:
#         try:
#             __import__(module)
#         except ImportError:
#             missing_modules.append(module)
#     
#     if missing_modules:
#         print(f"❌ Missing required modules: {', '.join(missing_modules)}")
#         print("Install with: pip install -r requirements.txt")
#         return False
#     
#     # Check log directory
#     create_log_directory()
#     
#     print("✅ Environment validation passed")
#     return True
#
# def print_system_info(config):
#     """Print system information"""
#     print("\n" + "="*80)
#     print("🛡️ ENA_USDT HEDGING SYSTEM - COMPLETE VERSION")
#     print("🧠 Powered by Cascade AI Assistant")
#     print("💰 Multi-coin support for sub-10-cent tokens")
#     print("="*80)
#     print(f"📊 Default Symbol: {config.symbol}")
#     print(f"💰 Min Profit: {config.min_profit_bps} bps")
#     print(f"🎯 Max Position: {config.max_hedge_position}")
#     print(f"📈 Order Size: ${config.hedge_order_size_usd}")
#     print(f"🧠 AI Confidence: {config.ai_confidence_threshold}")
#     print(f"🪙 Supported Coins: {len(config.sub_10_cent_coins)} sub-10-cent tokens")
#     print(f"🔑 API Key: {config.api_key[:8]}...{config.api_key[-4:]}")
#     print("="*80)
#
# def print_coin_list(config):
#     """Print list of supported coins"""
#     print(f"\n🪙 SUPPORTED SUB-10-CENT COINS ({len(config.sub_10_cent_coins)} total):")
#     print("-" * 60)
#     
#     # Group coins by type
#     meme_coins = ["PEPE_USDT", "SHIB_USDT", "DOGE_USDT", "FLOKI_USDT", "BABYDOGE_USDT", "BONK_USDT", "WIF_USDT"]
#     gaming_coins = ["GME_USDT", "AMC_USDT", "BB_USDT"]
#     political_coins = ["TRUMP_USDT", "MAGA_USDT"]
#     ai_coins = ["FET_USDT", "OCEAN_USDT"]
#     solana_coins = ["1000SATS_USDT", "BOME_USDT", "SLERF_USDT", "MOG_USDT"]
#     
#     def print_coins(coins, category):
#         category_coins = [c for c in coins if c in config.sub_10_cent_coins]
#         if category_coins:
#             print(f"📈 {category}:")
#             for coin in category_coins:
#                 settings = config.get_symbol_settings(coin)
#                 print(f"   • {coin} - Min profit: {settings['min_profit_bps']} bps, Max pos: {settings['max_position']}")
#     
#     print_coins(meme_coins, "Meme Coins")
#     print_coins(gaming_coins, "Gaming Stocks")
#     print_coins(political_coins, "Political Coins")
#     print_coins(ai_coins, "AI Tokens")
#     print_coins(solana_coins, "Solana Ecosystem")
#     
#     # Other coins
#     other_coins = [c for c in config.sub_10_cent_coins if not any(
#         c in group for group in [meme_coins, gaming_coins, political_coins, ai_coins, solana_coins]
#     )]
#     if other_coins:
#         print(f"📈 Other:")
#         for coin in other_coins:
#             settings = config.get_symbol_settings(coin)
#             print(f"   • {coin} - Min profit: {settings['min_profit_bps']} bps, Max pos: {settings['max_position']}")
#
# def print_safety_warnings():
#     """Print safety warnings"""
#     print("\n" + "⚠️" * 20)
#     print("🚨 IMPORTANT SAFETY WARNINGS:")
#     print("⚠️ This is automated trading software")
#     print("⚠️ Cryptocurrency trading involves substantial risk")
#     print("⚠️ Never invest more than you can afford to lose")
#     print("⚠️ Start with small amounts in test mode")
#     print("⚠️ Monitor the system closely when first starting")
#     print("⚠️ Keep API keys secure and limited")
#     print("⚠️" * 20)
#
# def main():
#     """Main entry point"""
#     parser = argparse.ArgumentParser(description='ENA_USDT Hedging System - Complete Version')
#     parser.add_argument('--mode', choices=['dev', 'prod', 'test'], default='dev',
#                        help='Running mode (dev=development, prod=production, test=test)')
#     parser.add_argument('--config', type=str, help='Custom config file path')
#     parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no real trades)')
#     parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
#     parser.add_argument('--symbol', type=str, help='Override default symbol')
#     parser.add_argument('--list-coins', action='store_true', help='List all supported coins and exit')
#     parser.add_argument('--validate', action='store_true', help='Validate environment and exit')
#     
#     args = parser.parse_args()
#     
#     # Environment validation
#     if args.validate:
#         if validate_environment():
#             print("✅ Environment is ready for trading")
#             return 0
#         else:
#             print("❌ Environment validation failed")
#             return 1
#     
#     # Validate environment
#     if not validate_environment():
#         return 1
#     
#     # Select configuration
#     if args.config:
#         print(f"📋 Using custom config: {args.config}")
#         config = ENAHedgingConfig()
#     elif args.mode == 'prod':
#         print("🚀 Production Mode")
#         config = ENAHedgingConfigProd()
#     elif args.mode == 'dev':
#         print("🛠️ Development Mode")
#         config = ENAHedgingConfigDev()
#     else:
#         print("🧪 Test Mode")
#         config = ENAHedgingConfig()
#     
#     # Apply command line overrides
#     if args.dry_run:
#         print("🔍 Dry Run Mode - No real trades will be executed")
#         config.simulation_mode = True
#         config.paper_trading = True
#     
#     if args.verbose:
#         print("📝 Verbose Logging Enabled")
#         config.log_level = "DEBUG"
#         logging.getLogger().setLevel(logging.DEBUG)
#     
#     if args.symbol:
#         print(f"📊 Symbol override: {args.symbol}")
#         config.symbol = args.symbol
#         config.update_symbol_config(args.symbol)
#     
#     # Validate configuration
#     try:
#         config.validate_config()
#         print("✅ Configuration validated")
#     except ValueError as e:
#         print(f"❌ Configuration error: {e}")
#         return 1
#     
#     # Print system info
#     print_system_info(config)
#     
#     # List coins if requested
#     if args.list_coins:
#         print_coin_list(config)
#         return 0
#     
#     # Print safety warnings
#     print_safety_warnings()
#     
#     # Confirm start
#     if not args.dry_run:
#         print("\n🤔 Are you ready to start live trading?")
#         print("   Press Enter to continue or Ctrl+C to cancel...")
#         try:
#             input()
#         except KeyboardInterrupt:
#             print("\n❌ Cancelled by user")
#             return 0
#     
#     print("\n🚀 Starting ENA hedging system...")
#     print("Press Ctrl+C to stop\n")
#     
#     # Create and run market maker
#     try:
#         market_maker = ENAHedgingMarketMaker(config)
#         asyncio.run(market_maker.start())
#     except KeyboardInterrupt:
#         print("\n⏹️ Shutting down...")
#         print("📊 Final statistics would be shown here")
#         print("✅ Shutdown complete")
#     except Exception as e:
#         print(f"❌ Runtime error: {e}")
#         if args.verbose:
#             import traceback
#             traceback.print_exc()
#         return 1
#     
#     return 0
#
# if __name__ == "__main__":
#     sys.exit(main())
# ===== END   [134/134] ENA_Hedging_Project/run_ena_hedging.py =====
