#!/usr/bin/env python3
"""
Mac Compute Node — Web Dashboard
Real-time monitoring of compute resources, tasks, L2 rollup, and earnings.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine import ComputeEngine
from l2.rollup import RollupEngine
from l2.solana_bridge import SolanaBridge
from marketplace.compute_market import ComputeMarket
import yaml


app = FastAPI(title="Mac Compute Node", version="1.0.0")

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

# Global state
engine: ComputeEngine = None
rollup: RollupEngine = None
bridge: SolanaBridge = None
market: ComputeMarket = None


@app.on_event("startup")
async def startup():
    global engine, rollup, bridge, market
    engine = ComputeEngine(CONFIG_PATH)
    rollup = RollupEngine(CONFIG["l2"])
    bridge = SolanaBridge(CONFIG["l2"])
    market = ComputeMarket(CONFIG["marketplace"])
    # Register this node
    market.register_node(engine.node_id, engine.get_resources().__dict__)
    # Start background
    asyncio.create_task(engine.start())
    asyncio.create_task(rollup.start())


@app.on_event("shutdown")
async def shutdown():
    if engine:
        await engine.stop()
    if rollup:
        await rollup.stop()


@app.get("/")
async def root():
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/api/status")
async def api_status():
    return {
        "node": engine.get_status() if engine else {},
        "rollup": rollup.get_status() if rollup else {},
        "bridge": bridge.get_status() if bridge else {},
        "market": market.get_market_stats() if market else {},
    }


@app.get("/api/earnings")
async def api_earnings():
    if engine and market:
        return market.get_node_earnings(engine.node_id)
    return {}


@app.get("/api/containers")
async def api_containers():
    if engine and engine.containers:
        return engine.containers.get_stats()
    return {}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            if engine and rollup and bridge and market:
                payload = {
                    "timestamp": time.time(),
                    "node": engine.get_status(),
                    "rollup": rollup.get_status(),
                    "bridge": bridge.get_status(),
                    "market": market.get_market_stats(),
                    "earnings": market.get_node_earnings(engine.node_id),
                }
                await ws.send_json(payload)
            await asyncio.sleep(2)
    except Exception:
        await ws.close()


DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Mac Compute Node</title>
<style>
  :root { --bg:#0f0f0f; --panel:#1a1a1a; --accent:#00ff88; --text:#e0e0e0; --muted:#888; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,sans-serif; }
  header { background:var(--panel); padding:20px 30px; border-bottom:1px solid #333; display:flex; justify-content:space-between; align-items:center; }
  header h1 { font-size:24px; color:var(--accent); }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:20px; padding:30px; }
  .card { background:var(--panel); border-radius:12px; padding:20px; border:1px solid #2a2a2a; }
  .card h2 { font-size:16px; color:var(--accent); margin-bottom:15px; text-transform:uppercase; letter-spacing:1px; }
  .metric { display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #2a2a2a; }
  .metric:last-child { border:none; }
  .metric .label { color:var(--muted); }
  .metric .value { font-family:monospace; color:var(--text); }
  .value.good { color:var(--accent); }
  .value.warn { color:#ffaa00; }
  .value.bad { color:#ff4444; }
  .progress-bar { height:6px; background:#333; border-radius:3px; margin-top:4px; overflow:hidden; }
  .progress-fill { height:100%; background:var(--accent); border-radius:3px; transition:width 0.5s; }
  .tps-display { font-size:48px; font-weight:700; color:var(--accent); text-align:center; margin:20px 0; }
  #log { font-family:monospace; font-size:12px; color:var(--muted); max-height:200px; overflow:auto; padding:10px; background:#0a0a0a; border-radius:6px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:12px; background:#2a2a2a; }
  .badge.active { background:#004d2a; color:var(--accent); }
</style>
</head>
<body>
<header>
  <h1>⚡ Mac Compute Node</h1>
  <div id="connection-status" class="badge">Connecting...</div>
</header>
<div class="grid">
  <div class="card">
    <h2>Resources</h2>
    <div id="resources"></div>
  </div>
  <div class="card">
    <h2>Tasks</h2>
    <div id="tasks"></div>
  </div>
  <div class="card">
    <h2>L2 Rollup</h2>
    <div class="tps-display" id="tps">0</div>
    <div id="rollup"></div>
  </div>
  <div class="card">
    <h2>Earnings</h2>
    <div id="earnings"></div>
  </div>
  <div class="card">
    <h2>Marketplace</h2>
    <div id="market"></div>
  </div>
  <div class="card">
    <h2>Bridge</h2>
    <div id="bridge"></div>
  </div>
  <div class="card" style="grid-column:1/-1;">
    <h2>Live Log</h2>
    <div id="log"></div>
  </div>
</div>
<script>
const ws = new WebSocket('ws://' + location.host + '/ws');
ws.onopen = () => { document.getElementById('connection-status').textContent = '● LIVE'; document.getElementById('connection-status').classList.add('active'); };
ws.onclose = () => { document.getElementById('connection-status').textContent = '● DISCONNECTED'; document.getElementById('connection-status').classList.remove('active'); };

function bar(pct, label) {
  const cls = pct > 90 ? 'bad' : pct > 70 ? 'warn' : 'good';
  return `<div><div class="metric"><span class="label">${label}</span><span class="value ${cls}">${pct.toFixed(1)}%</span></div><div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div></div>`;
}

ws.onmessage = (e) => {
  const d = JSON.parse(e.data);
  const node = d.node;
  const rollup = d.rollup;
  const market = d.market;
  const bridge = d.bridge;
  const earnings = d.earnings;

  if (node && node.resources) {
    const r = node.resources;
    document.getElementById('resources').innerHTML =
      bar(r.cpu_percent, 'CPU') +
      bar(r.memory_percent, 'Memory') +
      bar(r.disk_percent, 'Disk') +
      `<div class="metric"><span class="label">Cores</span><span class="value">${r.cpu_cores}</span></div>` +
      `<div class="metric"><span class="label">GPU</span><span class="value">${r.gpu_available ? 'Yes' : 'No'}</span></div>`;
  }

  if (node && node.tasks) {
    const t = node.tasks;
    document.getElementById('tasks').innerHTML =
      `<div class="metric"><span class="label">Total</span><span class="value">${t.total}</span></div>` +
      `<div class="metric"><span class="label">Completed</span><span class="value good">${t.completed}</span></div>` +
      `<div class="metric"><span class="label">Failed</span><span class="value bad">${t.failed}</span></div>` +
      `<div class="metric"><span class="label">Active</span><span class="value warn">${t.active}</span></div>`;
  }

  if (rollup) {
    document.getElementById('tps').textContent = rollup.current_tps.toLocaleString();
    document.getElementById('rollup').innerHTML =
      `<div class="metric"><span class="label">Block Height</span><span class="value">${rollup.block_height.toLocaleString()}</span></div>` +
      `<div class="metric"><span class="label">Processed</span><span class="value">${rollup.total_processed.toLocaleString()}</span></div>` +
      `<div class="metric"><span class="label">Target TPS</span><span class="value">${rollup.target_tps.toLocaleString()}</span></div>` +
      `<div class="metric"><span class="label">Mempool</span><span class="value">${rollup.mempool_size.toLocaleString()}</span></div>` +
      `<div class="metric"><span class="label">Latency</span><span class="value">${rollup.avg_latency_ms} ms</span></div>`;
  }

  if (earnings) {
    document.getElementById('earnings').innerHTML =
      `<div class="metric"><span class="label">Total</span><span class="value good">${earnings.total} ${earnings.currency}</span></div>` +
      `<div class="metric"><span class="label">Tasks</span><span class="value">${earnings.tasks_count}</span></div>`;
  }

  if (market) {
    document.getElementById('market').innerHTML =
      `<div class="metric"><span class="label">Active Nodes</span><span class="value">${market.active_nodes}</span></div>` +
      `<div class="metric"><span class="label">Avg Price/hr</span><span class="value">$${market.avg_price_per_hour}</span></div>` +
      `<div class="metric"><span class="label">Total Earnings</span><span class="value">${market.total_earnings} ${market.currency}</span></div>`;
  }

  if (bridge) {
    document.getElementById('bridge').innerHTML =
      `<div class="metric"><span class="label">Network</span><span class="value">${bridge.network}</span></div>` +
      `<div class="metric"><span class="label">Wallet</span><span class="value">${bridge.wallet ? bridge.wallet.slice(0,8)+'...' : 'N/A'}</span></div>` +
      `<div class="metric"><span class="label">Balance</span><span class="value">${bridge.balance_sol.toFixed(4)} SOL</span></div>`;
  }

  const log = document.getElementById('log');
  log.innerHTML = `Connected @ ${new Date().toLocaleTimeString()} | Node: ${node.node_id} | Uptime: ${Math.floor(node.uptime/60)}m<br>` + log.innerHTML;
};
</script>
</body>
</html>
"""


def run_dashboard():
    cfg = CONFIG["dashboard"]
    uvicorn.run(
        "dashboard.app:app",
        host=cfg.get("host", "0.0.0.0"),
        port=cfg.get("port", 7777),
        reload=False,
    )


if __name__ == "__main__":
    run_dashboard()
