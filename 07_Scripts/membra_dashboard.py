#!/usr/bin/env python3
"""
MEMBRA DASHBOARD SERVER
Serves neo-neomorphic glass membrane UI dashboard + landing page.
Production-grade Flask server with API endpoints.

Usage:
    python3 membra_dashboard.py --port 4242
"""

import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

STATE_PATH = "/Users/alep/Downloads/membra_state.json"
APPRAISAL_PATH = "/Users/alep/Downloads/file_level_appraisal.json"
UI = Path("/Users/alep/Downloads/membra_ui")

def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"wallet_created": False, "token_deployed": False, "token_minted": False,
            "pool_created": False, "total_deposits_sol": 0.0, "swaps_executed": 0}

def load_appraisal():
    if os.path.exists(APPRAISAL_PATH):
        with open(APPRAISAL_PATH) as f:
            return json.load(f)
    return {"totals": {"mid": 9_248_000, "files": 1123, "loc": 427_227}}

@app.route("/")
def landing():
    return send_from_directory(UI, "landing.html")

@app.route("/dashboard")
def dashboard():
    return send_from_directory(UI, "dashboard.html")

@app.route("/ui/<path:name>")
def ui_files(name):
    return send_from_directory(str(UI), name)

@app.route("/api/state")
def api_state():
    state = load_state()
    appraisal = load_appraisal()
    return jsonify({
        "app": "MEMBRA",
        "status": "LIVE_UI_READY",
        "mchat_status": "MANIFESTED_NOT_MINTED",
        "mint_address": state.get("mint_address", "NOT_CREATED"),
        "official_money_usd": "0.00_until_external_settlement",
        "execution_requires_user_signature": True,
        "funding_source_required": True,
        "appraisal": appraisal.get("totals", {}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token_symbol": "MEMBRA",
        "token_supply": 9_251_500,
        "network": state.get("network", "devnet"),
        **state,
    })

@app.route("/api/appraisal")
def api_appraisal():
    return jsonify(load_appraisal())

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    msg = data.get("message", "")
    return jsonify({
        "response": f"MEMBRA: Processing '{msg}' via LLM...\n\n[Connect to membra_agent.py for live execution]",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/corpus")
def api_corpus():
    """Get corpus indexing stats."""
    try:
        from membra_corpus_engine import CorpusIndexer
        indexer = CorpusIndexer()
        stats = indexer.get_stats()
        indexer.close()
        return jsonify({
            "status": "indexed",
            "files_indexed": stats["files_indexed"],
            "chunks": stats["chunks"],
            "embeddings": stats["embeddings"],
            "categories": stats["categories"],
            "corpus_dir": str(Path("/Users/alep/Downloads/membra_corpus")),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "not_indexed",
            "error": str(e),
            "message": "Run: python3 membra_corpus_engine.py pipeline",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

@app.route("/api/treasury")
def api_treasury():
    """Get treasury and liquidity status."""
    state = load_state()
    deposits = state.get("total_deposits_sol", 0.0)
    funding_status = "REAL_LIQUIDITY_AVAILABLE" if deposits > 0 else "KNOWLEDGE_SEED_ONLY"
    return jsonify({
        "sol_balance": 0.0,  # Would query chain in production
        "deposits_received_sol": deposits,
        "funding_status": funding_status,
        "can_create_pool": deposits > 0,
        "pool_created": state.get("pool_created", False),
        "rule": "Proof != Money. Only real SOL/USDC = liquid.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/liquidity")
def api_liquidity():
    """Get liquidity pool status."""
    state = load_state()
    deposits = state.get("total_deposits_sol", 0.0)
    return jsonify({
        "pool_tvl_usd": 0.0,
        "swap_depth_usd": 0.0,
        "deposits_sol": deposits,
        "pool_created": state.get("pool_created", False),
        "can_create": deposits > 0,
        "status": "REAL_LIQUIDITY" if deposits > 0 else "KNOWLEDGE_SEED_ONLY",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/health")
def health():
    return jsonify({"status": "live", "timestamp": datetime.now(timezone.utc).isoformat()})

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4242)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    UI.mkdir(parents=True, exist_ok=True)

    print("""
╔══════════════════════════════════════════════════╗
║  MEMBRA DASHBOARD — Neo-Glass Membrane UI        ║
╚══════════════════════════════════════════════════╝
    """)
    print(f"  Landing:   http://localhost:{args.port}")
    print(f"  Dashboard: http://localhost:{args.port}/dashboard")
    print(f"  API:       http://localhost:{args.port}/api/state")
    print()

    app.run(host=args.host, port=args.port, debug=False)

if __name__ == "__main__":
    main()
