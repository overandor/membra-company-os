"""
CollateralOps — Software Collateral Execution Network
Turns developer work into a balance sheet.

Runs in two modes:
  LOCAL: scans ~/Downloads live (python app.py)
  VERCEL: reads from pre-built data/index.json (deployed)
"""
import json
import os
import time
from pathlib import Path
from typing import Optional

import csv
import io

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

app = FastAPI(
    title="CollateralOps",
    description="Software Collateral Execution Network — turns developer work into a balance sheet",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PAGES = Path(__file__).parent / "pages"
INDEX_PATH = Path(__file__).parent / "data" / "index.json"
IS_VERCEL = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

# State
_projects: list = []
_classifications: dict = {}
_appraisals: dict = {}
_collateral: dict = {}
_lender_summaries: dict = {}
_buyer_summaries: dict = {}
_last_scan: float = 0


def _load_from_index():
    """Load pre-built index for Vercel deployment."""
    global _projects, _classifications, _appraisals, _collateral, _lender_summaries, _buyer_summaries, _last_scan
    if not INDEX_PATH.exists():
        return False
    with open(INDEX_PATH) as f:
        idx = json.load(f)
    _projects = []
    for entry in idx.get("projects", []):
        name = entry["name"]
        cls = entry.get("classification", {})
        apr = entry.get("appraisal", {})
        # Rebuild signals from summary for compatibility
        if "signals_summary" in cls and "signals" not in cls:
            cls["signals"] = cls["signals_summary"]
        _projects.append({"name": name, "has_collateral": bool(entry.get("collateral_records"))})
        _classifications[name] = cls
        _appraisals[name] = apr
        _collateral[name] = entry.get("collateral_records", [])
        _lender_summaries[name] = entry.get("lender_summary", {})
        _buyer_summaries[name] = entry.get("buyer_summary", {})
    _last_scan = idx.get("generated_at", time.time())
    return True


def _scan_live():
    """Scan local folders live."""
    global _projects, _classifications, _appraisals, _collateral, _lender_summaries, _buyer_summaries, _last_scan
    from scanner import discover_projects, scan_collateral
    from classifier import classify_repo
    try:
        from appraiser_v2 import appraise_v2 as appraise
    except ImportError:
        from appraiser import appraise
    from packet import generate_packet, generate_lender_summary, generate_buyer_summary

    scan_root = Path(os.environ.get("SCAN_ROOT", str(Path.home() / "Downloads")))
    _projects = discover_projects(scan_root)
    _classifications = {}
    _appraisals = {}
    _collateral = {}
    _lender_summaries = {}
    _buyer_summaries = {}

    for proj in _projects:
        name = proj["name"]
        records = scan_collateral(proj["path"])
        cls = classify_repo(proj["path"], name, records)
        apr = appraise(cls)
        pkt = generate_packet(cls, apr, records)
        _classifications[name] = cls
        _appraisals[name] = apr
        _collateral[name] = records
        _lender_summaries[name] = generate_lender_summary(pkt)
        _buyer_summaries[name] = generate_buyer_summary(pkt)
    _last_scan = time.time()


# Load data immediately
if INDEX_PATH.exists():
    _load_from_index()


@app.on_event("startup")
async def startup():
    if not _projects and not IS_VERCEL:
        _scan_live()


# ── Health ──────────────────────────────────────────────────────────

@app.get("/health")
def health():
    total_rc = sum(a.get("replacement_cost_usd", 0) for a in _appraisals.values())
    total_csv = sum(a.get("collateral_support_value_usd", 0) for a in _appraisals.values())
    total_market = sum(a.get("market_comparable_value_usd", 0) for a in _appraisals.values())
    financeable = sum(1 for a in _appraisals.values() if a.get("financeability_score", 0) >= 40)
    avg_fs = sum(a.get("financeability_score", 0) for a in _appraisals.values()) / max(1, len(_appraisals))
    return {
        "status": "ok",
        "product": "CollateralOps v2.0",
        "mode": "index" if INDEX_PATH.exists() else "live_scan",
        "total_projects": len(_projects),
        "total_replacement_value_usd": round(total_rc, 2),
        "total_collateral_support_usd": round(total_csv, 2),
        "total_market_comparable_usd": round(total_market, 2),
        "financeable_assets": financeable,
        "avg_financeability": round(avg_fs, 1),
        "last_scan": _last_scan,
    }


# ── Passport API Endpoints ────────────────────────────────────────────

@app.get("/api/stats")
def stats():
    """General stats for passport page."""
    total_files = sum(cls.get("collateral_files", 0) for cls in _classifications.values())
    total_src = sum(cls.get("signals", {}).get("total_src", 0) for cls in _classifications.values())
    total_rc = sum(a.get("replacement_cost_usd", 0) for a in _appraisals.values())
    
    return {
        "total_projects": len(_projects),
        "total_files": total_files,
        "total_src": total_src,
        "total_replacement_value_usd": round(total_rc, 2),
        "generated_at": _last_scan
    }


@app.get("/api/systems")
def systems():
    """Systems breakdown for passport page."""
    from collections import Counter
    types = Counter(cls.get("asset_type", "unknown") for cls in _classifications.values())
    
    systems_data = []
    for asset_type, count in types.most_common():
        systems_data.append({
            "system": {"name": asset_type},
            "count": count,
            "label": "Assets"
        })
    
    return {"systems": systems_data}


@app.get("/api/workstreams")
def workstreams():
    """Workstream breakdown for passport page."""
    from collections import Counter
    all_recs = [r for recs in _collateral.values() for r in recs]
    by_ws = Counter(r.get("workstream", "unknown") for r in all_recs)
    
    workstreams_data = []
    for ws, count in by_ws.most_common(10):
        workstreams_data.append({
            "workstream": ws,
            "count": count
        })
    
    return {"workstreams": workstreams_data}


# ── Balance Sheet ──────────────────────────────────────────────────

@app.get("/api/balance-sheet")
def balance_sheet():
    assets = []
    for proj in _projects:
        name = proj["name"]
        cls = _classifications.get(name, {})
        apr = _appraisals.get(name, {})
        sigs = cls.get("signals", cls.get("signals_summary", {}))
        assets.append({
            "name": name,
            "asset_type": cls.get("asset_type", "unknown"),
            "proof_level": cls.get("proof_level", 0),
            "proof_level_name": cls.get("proof_level_name", "Unknown"),
            "capital_readiness": apr.get("capital_readiness", "Unknown"),
            "replacement_cost_usd": apr.get("replacement_cost_usd", 0),
            "as_is_sale_value_usd": apr.get("as_is_sale_value_usd", 0),
            "productized_value_usd": apr.get("productized_value_usd", 0),
            "liquidation_value_usd": apr.get("liquidation_value_usd", 0),
            "collateral_support_value_usd": apr.get("collateral_support_value_usd", 0),
            "market_comparable_value_usd": apr.get("market_comparable_value_usd", 0),
            "network_effect_value_usd": apr.get("network_effect_value_usd", 0),
            "complexity_adjusted_value_usd": apr.get("complexity_adjusted_value_usd", 0),
            "financeability_score": apr.get("financeability_score", 0),
            "confidence_score": apr.get("confidence_score", 0),
            "subscores": apr.get("subscores", {}),
            "risk_matrix": apr.get("risk_matrix", {}),
            "risk_flags": cls.get("risk_flags", []),
            "collateral_files": cls.get("collateral_files", 0),
            "primary_language": sigs.get("primary_language", "none"),
            "total_src": sigs.get("total_src", 0),
        })
    assets.sort(key=lambda a: -a["replacement_cost_usd"])

    total_rc = sum(a["replacement_cost_usd"] for a in assets)
    total_as_is = sum(a["as_is_sale_value_usd"] for a in assets)
    total_liq = sum(a["liquidation_value_usd"] for a in assets)
    total_csv = sum(a["collateral_support_value_usd"] for a in assets)
    total_prod = sum(a.get("productized_value_usd", 0) for a in assets)
    total_market = sum(a.get("market_comparable_value_usd", 0) for a in assets)
    avg_fs = sum(a["financeability_score"] for a in assets) / max(1, len(assets))
    sale_cands = sum(1 for a in assets if a["financeability_score"] >= 40 and a["asset_type"] not in ("junk", "scaffold", "duplicate"))
    needs_cleanup = sum(1 for a in assets if a["risk_flags"])
    junk = sum(1 for a in assets if a["asset_type"] in ("junk", "scaffold", "duplicate"))

    actionable = [a for a in assets if 20 < a["financeability_score"] < 70 and a["asset_type"] not in ("junk", "scaffold")]
    top3 = sorted(actionable, key=lambda a: -a["replacement_cost_usd"])[:3]
    unlock = f"Add tests, deployment proof, and license to: {', '.join(a['name'] for a in top3)}" if top3 else "Review and classify all projects"

    return {
        "summary": {
            "total_strategic_value_usd": round(total_rc, 2),
            "buyer_today_value_usd": round(total_as_is, 2),
            "liquidation_value_usd": round(total_liq, 2),
            "collateral_support_value_usd": round(total_csv, 2),
            "productized_value_usd": round(total_prod, 2),
            "market_comparable_value_usd": round(total_market, 2),
            "financeability_score_avg": round(avg_fs),
            "total_projects": len(assets),
            "sale_candidates": sale_cands,
            "needs_cleanup": needs_cleanup,
            "junk_scaffold": junk,
            "next_value_unlock": unlock,
        },
        "assets": assets,
    }


# ── Individual Asset ───────────────────────────────────────────────

@app.get("/api/asset/{name}")
def asset_detail(name: str):
    if name not in _classifications:
        raise HTTPException(404, f"Asset not found: {name}")
    return {"classification": _classifications[name], "appraisal": _appraisals[name]}


@app.get("/api/asset/{name}/lender")
def lender_view(name: str):
    if name not in _lender_summaries:
        raise HTTPException(404)
    return _lender_summaries[name]


@app.get("/api/asset/{name}/buyer")
def buyer_view(name: str):
    if name not in _buyer_summaries:
        raise HTTPException(404)
    return _buyer_summaries[name]


# ── Collateral Records ─────────────────────────────────────────────

@app.get("/api/collateral")
def list_collateral(
    repo: Optional[str] = Query(None),
    workstream: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    records = []
    for name, recs in _collateral.items():
        for r in recs:
            r["_repo"] = name
            records.append(r)
    if repo:
        records = [r for r in records if r.get("_repo") == repo]
    if workstream:
        wl = workstream.lower()
        records = [r for r in records if wl in r.get("workstream", "").lower()]
    total = len(records)
    return {"total": total, "offset": offset, "limit": limit, "items": records[offset:offset + limit]}


@app.get("/api/collateral/stats")
def collateral_stats():
    from collections import Counter
    all_recs = [r for recs in _collateral.values() for r in recs]
    by_ws = Counter(r.get("workstream", "?") for r in all_recs)
    by_ext = Counter(r.get("extension", "?") for r in all_recs)
    by_repo = {name: len(recs) for name, recs in _collateral.items() if recs}
    return {
        "total_files": len(all_recs),
        "total_repos_with_collateral": len(by_repo),
        "by_workstream": dict(by_ws.most_common()),
        "by_extension": dict(by_ext.most_common()),
        "by_repo": dict(sorted(by_repo.items(), key=lambda x: -x[1])),
    }


@app.get("/api/collateral/{repo_name}")
def repo_collateral(repo_name: str, limit: int = Query(200)):
    records = _collateral.get(repo_name, [])
    if not records:
        raise HTTPException(404, f"No collateral for: {repo_name}")
    return {"repo": repo_name, "total": len(records), "items": records[:limit]}


@app.get("/api/collateral/{repo_name}/{sku}")
def collateral_by_sku(repo_name: str, sku: str):
    records = _collateral.get(repo_name, [])
    for r in records:
        if r.get("sku") == sku:
            return r
    raise HTTPException(404, "SKU not found")


# ── Search ─────────────────────────────────────────────────────────

@app.get("/api/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(50)):
    ql = q.lower()
    hits = []
    for name, cls in _classifications.items():
        apr = _appraisals.get(name, {})
        sigs = cls.get("signals", cls.get("signals_summary", {}))
        searchable = f"{name} {cls.get('asset_type', '')} {sigs.get('primary_language', '')}"
        if ql in searchable.lower():
            hits.append({
                "name": name, "asset_type": cls.get("asset_type"),
                "financeability": apr.get("financeability_score", 0),
                "replacement_cost": apr.get("replacement_cost_usd", 0),
            })
    return {"query": q, "total": len(hits), "items": hits[:limit]}


# ── Portfolio Views ────────────────────────────────────────────────

@app.get("/api/portfolio/by-type")
def by_type():
    from collections import Counter
    types = Counter(cls.get("asset_type", "?") for cls in _classifications.values())
    return {"by_type": dict(types.most_common())}


@app.get("/api/portfolio/risk-blocked")
def risk_blocked():
    blocked = []
    for name, cls in _classifications.items():
        risks = cls.get("risk_flags", [])
        critical = [r for r in risks if r in ("env_file_detected", "no_license", "no_version_control")]
        if critical:
            apr = _appraisals.get(name, {})
            blocked.append({
                "name": name,
                "critical_risks": critical,
                "financeability": apr.get("financeability_score", 0),
                "replacement_cost_usd": apr.get("replacement_cost_usd", 0),
                "collateral_support_value_usd": apr.get("collateral_support_value_usd", 0),
                "asset_type": cls.get("asset_type", "unknown"),
                "all_risks": risks
            })
    blocked.sort(key=lambda b: -b["replacement_cost_usd"])
    return {"total": len(blocked), "items": blocked}


@app.get("/api/portfolio/improvement-queue")
def improvement_queue():
    queue = []
    for name, apr in _appraisals.items():
        fs = apr.get("financeability_score", 0)
        at = _classifications.get(name, {}).get("asset_type", "")
        if fs < 80 and at not in ("junk", "scaffold", "duplicate"):
            actions = apr.get("next_actions", [])
            cls = _classifications.get(name, {})
            queue.append({
                "name": name,
                "current_financeability": fs,
                "replacement_cost_usd": apr.get("replacement_cost_usd", 0),
                "collateral_support_value_usd": apr.get("collateral_support_value_usd", 0),
                "top_action": actions[0] if actions else None,
                "all_actions": actions,
                "asset_type": at,
                "proof_level": cls.get("proof_level", 0),
                "capital_readiness": apr.get("capital_readiness", "Unknown"),
                "estimated_days": sum(a.get("effort", "0").replace("h","").replace("d","").split() for a in actions[:3] if a.get("effort")) if actions else 0
            })
    queue.sort(key=lambda q: (-q["replacement_cost_usd"], q["current_financeability"]))
    return {"total": len(queue), "items": queue}


# ── Agent Work Accounting ──────────────────────────────────────────────

@app.get("/api/agent/accounting")
def agent_accounting():
    """Returns agent work accounting data for the Agent Accounting tab."""
    total_work = 0
    assets_processed = len(_projects)
    total_files = sum(cls.get("collateral_files", 0) for cls in _classifications.values())
    total_value_processed = sum(apr.get("replacement_cost_usd", 0) for apr in _appraisals.values())
    
    # Estimate work items based on collateral records
    work_items = []
    for name, recs in _collateral.items():
        for r in recs:
            work_items.append({
                "asset": name,
                "workstream": r.get("workstream", "unknown"),
                "file": r.get("file_path", ""),
                "sku": r.get("sku", ""),
                "status": "processed",
                "value_contribution": r.get("value_estimate", 0)
            })
    
    return {
        "summary": {
            "total_work_items": len(work_items),
            "assets_processed": assets_processed,
            "total_files_processed": total_files,
            "total_value_processed_usd": round(total_value_processed, 2),
            "agent_efficiency": round(len(work_items) / max(1, assets_processed), 2)
        },
        "work_items": work_items[:100]  # Limit to 100 items for performance
    }


# ── Capital Readiness Pipeline ─────────────────────────────────────────

@app.get("/api/capital-readiness")
def capital_readiness_pipeline():
    """Returns capital readiness pipeline data."""
    pipeline = {
        "ready_for_collateral": [],
        "near_ready": [],
        "needs_work": [],
        "not_ready": []
    }
    
    for name, apr in _appraisals.items():
        fs = apr.get("financeability_score", 0)
        cls = _classifications.get(name, {})
        at = cls.get("asset_type", "")
        if at in ("junk", "scaffold", "duplicate"):
            continue
            
        readiness = {
            "name": name,
            "financeability_score": fs,
            "capital_readiness": apr.get("capital_readiness", "Unknown"),
            "replacement_cost_usd": apr.get("replacement_cost_usd", 0),
            "collateral_support_value_usd": apr.get("collateral_support_value_usd", 0),
            "proof_level": cls.get("proof_level", 0),
            "asset_type": at
        }
        
        if fs >= 70:
            pipeline["ready_for_collateral"].append(readiness)
        elif fs >= 50:
            pipeline["near_ready"].append(readiness)
        elif fs >= 30:
            pipeline["needs_work"].append(readiness)
        else:
            pipeline["not_ready"].append(readiness)
    
    # Sort each bucket by value
    for key in pipeline:
        pipeline[key].sort(key=lambda x: -x["replacement_cost_usd"])
    
    return {
        "summary": {
            "ready_for_collateral": len(pipeline["ready_for_collateral"]),
            "near_ready": len(pipeline["near_ready"]),
            "needs_work": len(pipeline["needs_work"]),
            "not_ready": len(pipeline["not_ready"]),
            "total": sum(len(v) for v in pipeline.values())
        },
        "pipeline": pipeline
    }


# ── Evidence Chain Data ────────────────────────────────────────────────

@app.get("/api/evidence-chain/{name}")
def evidence_chain(name: str):
    """Returns evidence chain data for an asset."""
    if name not in _classifications:
        raise HTTPException(404, f"Asset not found: {name}")
    
    cls = _classifications[name]
    proof_level = cls.get("proof_level", 0)
    
    # Build evidence chain steps based on proof level
    steps = [
        {"step": "discovered", "label": "Discovered", "status": "done" if proof_level >= 0 else "pending"},
        {"step": "hashed", "label": "Hashed", "status": "done" if proof_level >= 1 else "pending"},
        {"step": "git_metadata", "label": "Git Metadata", "status": "done" if proof_level >= 3 else "pending"},
        {"step": "security_scan", "label": "Security Scan", "status": "done" if proof_level >= 3 else "pending"},
        {"step": "documented", "label": "Documented", "status": "done" if proof_level >= 4 else "pending"},
        {"step": "test_verified", "label": "Test Verified", "status": "done" if proof_level >= 5 else "pending"},
        {"step": "build_verified", "label": "Build Verified", "status": "done" if proof_level >= 6 else "pending"}
    ]
    
    return {
        "asset": name,
        "proof_level": proof_level,
        "proof_level_name": cls.get("proof_level_name", "Unknown"),
        "evidence_steps": steps,
        "collateral_files": cls.get("collateral_files", 0),
        "risk_flags": cls.get("risk_flags", [])
    }


# ── Packet Readiness Data ───────────────────────────────────────────────

@app.get("/api/packet-readiness/{name}")
def packet_readiness(name: str):
    """Returns collateral packet readiness data for an asset."""
    if name not in _classifications:
        raise HTTPException(404, f"Asset not found: {name}")
    
    cls = _classifications[name]
    apr = _appraisals[name]
    proof_level = cls.get("proof_level", 0)
    
    # Define packet sections and their readiness based on proof level
    sections = [
        {"name": "Executive Summary", "state": "complete" if proof_level >= 1 else "missing"},
        {"name": "Asset Identity", "state": "complete" if proof_level >= 1 else "missing"},
        {"name": "Ownership Statement", "state": "started" if proof_level >= 2 else "missing"},
        {"name": "Technical Inventory", "state": "complete" if proof_level >= 2 else "started"},
        {"name": "File Hash Manifest", "state": "complete" if proof_level >= 2 else "missing"},
        {"name": "Git/Commit Evidence", "state": "complete" if proof_level >= 3 else "started"},
        {"name": "Build and Test Evidence", "state": "complete" if proof_level >= 5 else "started"},
        {"name": "Security and Secret Scan", "state": "complete" if len(cls.get("risk_flags", [])) == 0 else "blocked"},
        {"name": "License and Fork Risk", "state": "complete" if len(cls.get("risk_flags", [])) == 0 else "blocked"},
        {"name": "Documentation Review", "state": "complete" if proof_level >= 4 else "started"},
        {"name": "Market Use Case", "state": "complete" if apr.get("as_is_sale_value_usd", 0) > 0 else "started"},
        {"name": "Valuation Methodology", "state": "complete" if proof_level >= 5 else "missing"},
        {"name": "Collateral Support Estimate", "state": "complete" if proof_level >= 5 else "missing"},
        {"name": "Liquidation Route", "state": "complete" if apr.get("liquidation_value_usd", 0) > 0 else "started"}
    ]
    
    # Calculate overall readiness percentage
    completed = sum(1 for s in sections if s["state"] == "complete")
    readiness_pct = round((completed / len(sections)) * 100)
    
    return {
        "asset": name,
        "overall_readiness_pct": readiness_pct,
        "proof_level": proof_level,
        "sections": sections,
        "total_sections": len(sections),
        "completed_sections": completed,
        "blocked_sections": sum(1 for s in sections if s["state"] == "blocked"),
        "missing_sections": sum(1 for s in sections if s["state"] == "missing")
    }


# ── Buyer Universe Data ─────────────────────────────────────────────────

@app.get("/api/buyer-universe")
def buyer_universe():
    """Returns buyer universe data for institutional buyers."""
    buyers = [
        {
            "id": "buyer_001",
            "name": "Strategic Tech Acquisitions",
            "type": "Strategic",
            "focus_areas": ["developer_tools", "infrastructure", "platforms"],
            "min_financeability": 50,
            "min_collateral_value": 100000,
            "active": True
        },
        {
            "id": "buyer_002",
            "name": "Institutional Software Fund",
            "type": "Financial",
            "focus_areas": ["enterprise_software", "saas", "platforms"],
            "min_financeability": 60,
            "min_collateral_value": 500000,
            "active": True
        },
        {
            "id": "buyer_003",
            "name": "Open Source Collective",
            "type": "Community",
            "focus_areas": ["open_source", "developer_tools", "libraries"],
            "min_financeability": 40,
            "min_collateral_value": 50000,
            "active": True
        },
        {
            "id": "buyer_004",
            "name": "Private Equity Ventures",
            "type": "Financial",
            "focus_areas": ["enterprise", "infrastructure", "platforms"],
            "min_financeability": 70,
            "min_collateral_value": 1000000,
            "active": True
        }
    ]
    
    # Match assets to buyers
    matches = []
    for name, apr in _appraisals.items():
        cls = _classifications.get(name, {})
        fs = apr.get("financeability_score", 0)
        csv = apr.get("collateral_support_value_usd", 0)
        at = cls.get("asset_type", "")
        
        if at in ("junk", "scaffold", "duplicate"):
            continue
            
        for buyer in buyers:
            if not buyer["active"]:
                continue
            if fs >= buyer["min_financeability"] and csv >= buyer["min_collateral_value"]:
                matches.append({
                    "asset": name,
                    "buyer": buyer["name"],
                    "buyer_id": buyer["id"],
                    "match_score": min(100, (fs + (csv / buyer["min_collateral_value"]) * 10) / 2),
                    "collateral_value_usd": csv
                })
    
    matches.sort(key=lambda m: -m["match_score"])
    
    return {
        "buyers": buyers,
        "matches": matches[:50],  # Limit to top 50 matches
        "total_matches": len(matches)
    }


# ── Liquidation Route Data ───────────────────────────────────────────────

@app.get("/api/liquidation-route/{name}")
def liquidation_route(name: str):
    """Returns liquidation route data for an asset."""
    if name not in _classifications:
        raise HTTPException(404, f"Asset not found: {name}")
    
    cls = _classifications[name]
    apr = _appraisals[name]
    
    # Determine liquidation route based on asset type and financeability
    at = cls.get("asset_type", "")
    fs = apr.get("financeability_score", 0)
    liq_val = apr.get("liquidation_value_usd", 0)
    
    routes = []
    
    if at in ("mvp", "prototype", "poc"):
        routes.append({
            "route": "Direct Sale to Developer",
            "priority": "high",
            "estimated_recovery_pct": 60,
            "timeframe_days": 30,
            "description": "Sell directly to individual developer or small team"
        })
    
    if at in ("library", "sdk", "api", "tool"):
        routes.append({
            "route": "Open Source Release",
            "priority": "medium",
            "estimated_recovery_pct": 40,
            "timeframe_days": 60,
            "description": "Release as open source to build community value"
        })
    
    if fs >= 50:
        routes.append({
            "route": "Strategic Buyer Acquisition",
            "priority": "high",
            "estimated_recovery_pct": 70,
            "timeframe_days": 90,
            "description": "Sell to strategic buyer in related space"
        })
    
    if fs >= 70:
        routes.append({
            "route": "Secondary Market Auction",
            "priority": "medium",
            "estimated_recovery_pct": 80,
            "timeframe_days": 120,
            "description": "List on secondary market for institutional buyers"
        })
    
    routes.append({
        "route": "Asset Liquidation Auction",
        "priority": "low",
        "estimated_recovery_pct": 30,
        "timeframe_days": 180,
        "description": "Bulk liquidation of code and assets"
    })
    
    routes.sort(key=lambda r: -r["estimated_recovery_pct"])
    
    return {
        "asset": name,
        "asset_type": at,
        "financeability_score": fs,
        "liquidation_value_usd": liq_val,
        "recommended_routes": routes[:3],
        "all_routes": routes
    }


# ── Catacomb Prioritization ───────────────────────────────────────────

@app.get("/api/catacomb/prioritization")
def catacomb_prioritization():
    """Catacomb-style prioritization: ranks assets by revival potential."""
    
    prioritized = []
    
    for name, cls in _classifications.items():
        apr = _appraisals.get(name, {})
        sigs = cls.get("signals", cls.get("signals_summary", {}))
        
        at = cls.get("asset_type", "")
        fs = apr.get("financeability_score", 0)
        rc = apr.get("replacement_cost_usd", 0)
        csv = apr.get("collateral_support_value_usd", 0)
        pl = cls.get("proof_level", 0)
        src = sigs.get("total_src", 0)
        
        # Skip junk/scaffold/duplicate
        if at in ("junk", "scaffold", "duplicate"):
            continue
        
        # Calculate revival potential score (Catacomb algorithm)
        # Higher replacement cost = higher potential value
        # Higher financeability = easier to realize value
        # Higher proof level = better foundation
        # More source code = more substance
        
        value_score = min(100, (rc / 100000) * 10) if rc > 0 else 0  # Scale by $100k
        financeability_score = fs
        proof_score = (pl / 7) * 100
        substance_score = min(100, (src / 1000) * 20) if src > 0 else 0
        
        # Weighted revival potential (Catacomb thesis)
        revival_potential = (
            value_score * 0.4 +           # 40% - raw value
            financeability_score * 0.3 +     # 30% - ease of realization
            proof_score * 0.2 +             # 20% - foundation
            substance_score * 0.1           # 10% - substance
        )
        
        # Calculate collateral conversion gap
        conversion_gap_pct = ((rc - csv) / rc * 100) if rc > 0 else 0
        
        # Estimate effort to reach financeable (FS >= 70)
        actions = apr.get("next_actions", [])
        critical_actions = [a for a in actions if a.get("priority") == "critical"]
        high_actions = [a for a in actions if a.get("priority") == "high"]
        estimated_effort_weeks = len(critical_actions) * 2 + len(high_actions) * 1
        
        # Catacomb tier classification
        if revival_potential >= 70 and rc > 1000000:
            tier = "Tier 1 - Core Asset"
        elif revival_potential >= 50 and rc > 500000:
            tier = "Tier 2 - High Potential"
        elif revival_potential >= 30:
            tier = "Tier 3 - Medium Potential"
        elif revival_potential >= 15:
            tier = "Tier 4 - Low Potential"
        else:
            tier = "Archive Candidate"
        
        prioritized.append({
            "name": name,
            "asset_type": at,
            "replacement_cost_usd": rc,
            "collateral_support_usd": csv,
            "financeability_score": fs,
            "proof_level": pl,
            "total_src": src,
            "revival_potential_score": round(revival_potential, 1),
            "conversion_gap_pct": round(conversion_gap_pct, 1),
            "tier": tier,
            "estimated_effort_weeks": estimated_effort_weeks,
            "critical_actions": len(critical_actions),
            "high_actions": len(high_actions),
            "total_actions": len(actions),
            "roi_estimate": round((csv * (100 / max(1, 100 - conversion_gap_pct))) / max(1, estimated_effort_weeks)) if estimated_effort_weeks > 0 else 0
        })
    
    # Sort by revival potential descending
    prioritized.sort(key=lambda x: -x["revival_potential_score"])
    
    return {
        "total_assets": len(prioritized),
        "tiers": {
            "tier_1": len([p for p in prioritized if "Tier 1" in p["tier"]]),
            "tier_2": len([p for p in prioritized if "Tier 2" in p["tier"]]),
            "tier_3": len([p for p in prioritized if "Tier 3" in p["tier"]]),
            "tier_4": len([p for p in prioritized if "Tier 4" in p["tier"]]),
            "archive": len([p for p in prioritized if "Archive" in p["tier"]])
        },
        "prioritized_assets": prioritized
    }


# ── Rescan (local mode only) ──────────────────────────────────────

@app.post("/api/rescan")
def rescan():
    if IS_VERCEL:
        return {"status": "index_mode", "note": "Rescan not available in deployed mode. Rebuild index locally and redeploy."}
    _scan_live()
    return {"status": "rescanned", "total_projects": len(_projects)}


# ── Pages ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def landing():
    return (PAGES / "landing.html").read_text()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return (PAGES / "dashboard.html").read_text()

@app.get("/asset/{name}", response_class=HTMLResponse)
def asset_page(name: str):
    return (PAGES / "asset.html").read_text()

@app.get("/lender", response_class=HTMLResponse)
def lender_page():
    return (PAGES / "lender.html").read_text()

@app.get("/explorer", response_class=HTMLResponse)
def explorer():
    return (PAGES / "explorer.html").read_text()

@app.get("/prioritization", response_class=HTMLResponse)
def prioritization_page():
    return (PAGES / "prioritization.html").read_text()

@app.get("/compare", response_class=HTMLResponse)
def compare_page():
    return (PAGES / "compare.html").read_text()


@app.get("/api/compare")
def compare_api(a: str, b: str):
    """Side-by-side comparison of two assets."""
    if a not in _classifications or b not in _classifications:
        raise HTTPException(404, "Asset not found")
    return {
        "asset_a": {"name": a, "classification": _classifications[a], "appraisal": _appraisals[a]},
        "asset_b": {"name": b, "classification": _classifications[b], "appraisal": _appraisals[b]},
    }


@app.get("/api/export/balance-sheet")
def export_balance_sheet(format: str = Query("json", enum=["json", "csv"])):
    """Export the full balance sheet as JSON or CSV."""
    if format == "json":
        data = balance_sheet()
        return Response(
            content=json.dumps(data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="collateralops-balance-sheet.json"'}
        )
    # CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "name", "asset_type", "proof_level", "primary_language", "total_src",
        "financeability_score", "confidence_score", "replacement_cost_usd",
        "as_is_sale_value_usd", "productized_value_usd", "liquidation_value_usd",
        "collateral_support_value_usd", "market_comparable_value_usd",
        "network_effect_value_usd", "complexity_adjusted_value_usd",
        "recommended_ltv_min", "recommended_ltv_max", "capital_readiness",
        "risk_count", "deduction_count", "action_count"
    ])
    data = balance_sheet()
    for a in data.get("assets", []):
        apr = a.get("appraisal", {})
        ltv = apr.get("recommended_ltv", {})
        writer.writerow([
            a.get("name"), a.get("asset_type"), a.get("proof_level"),
            a.get("primary_language"), a.get("total_src"),
            apr.get("financeability_score"), apr.get("confidence_score"),
            apr.get("replacement_cost_usd"), apr.get("as_is_sale_value_usd"),
            apr.get("productized_value_usd"), apr.get("liquidation_value_usd"),
            apr.get("collateral_support_value_usd"), apr.get("market_comparable_value_usd"),
            apr.get("network_effect_value_usd"), apr.get("complexity_adjusted_value_usd"),
            ltv.get("min_pct"), ltv.get("max_pct"), apr.get("capital_readiness"),
            len(apr.get("risk_matrix", {})), len(apr.get("deductions", [])),
            len(apr.get("next_actions", []))
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="collateralops-balance-sheet.csv"'}
    )


@app.get("/api/timeline/{name}")
def timeline(name: str):
    """Generate synthetic appraisal timeline for an asset."""
    if name not in _classifications:
        raise HTTPException(404, "Asset not found")
    apr = _appraisals.get(name, {})
    cls = _classifications.get(name, {})
    signals = cls.get("signals", {})
    commits = signals.get("commit_count", 10)
    has_tests = signals.get("has_tests", False)
    has_ci = signals.get("has_ci", False)

    # Generate 4-6 historical points based on commit maturity
    points = max(4, min(6, commits // 3))
    timeline = []
    base_fs = apr.get("financeability_score", 50)
    base_conf = apr.get("confidence_score", 50)
    base_rc = apr.get("replacement_cost_usd", 50000)
    base_pv = apr.get("productized_value_usd", 30000)

    for i in range(points):
        progress = (i + 1) / points
        # Simulate growth curve: starts lower, grows to current
        fs = int(base_fs * (0.3 + 0.7 * progress * progress))
        conf = int(base_conf * (0.4 + 0.6 * progress))
        rc = int(base_rc * (0.2 + 0.8 * progress))
        pv = int(base_pv * (0.1 + 0.9 * progress))
        # Add milestones
        milestones = []
        if i == 0:
            milestones.append("Initial commit")
        if has_tests and i == points - 2:
            milestones.append("Test suite added")
        if has_ci and i == points - 1:
            milestones.append("CI/CD integrated")
        if i == points - 1:
            milestones.append("Current appraisal")
        timeline.append({
            "period": f"Q{i + 1}",
            "financeability_score": fs,
            "confidence_score": conf,
            "replacement_cost_usd": rc,
            "productized_value_usd": pv,
            "milestones": milestones,
        })
    return {"name": name, "timeline": timeline, "generated_at": time.time()}


@app.get("/api/export/asset/{name}")
def export_asset(name: str, format: str = Query("json", enum=["json", "csv"])):
    """Export a single asset appraisal as JSON or CSV."""
    if name not in _classifications:
        raise HTTPException(404, "Asset not found")
    cls = _classifications[name]
    apr = _appraisals[name]
    if format == "json":
        return Response(
            content=json.dumps({"name": name, "classification": cls, "appraisal": apr}, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="collateralops-{name}.json"'}
        )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["field", "value"])
    writer.writerow(["name", name])
    writer.writerow(["asset_type", cls.get("asset_type")])
    writer.writerow(["proof_level", cls.get("proof_level")])
    writer.writerow(["financeability_score", apr.get("financeability_score")])
    writer.writerow(["confidence_score", apr.get("confidence_score")])
    writer.writerow(["replacement_cost_usd", apr.get("replacement_cost_usd")])
    writer.writerow(["as_is_sale_value_usd", apr.get("as_is_sale_value_usd")])
    writer.writerow(["productized_value_usd", apr.get("productized_value_usd")])
    writer.writerow(["liquidation_value_usd", apr.get("liquidation_value_usd")])
    writer.writerow(["collateral_support_value_usd", apr.get("collateral_support_value_usd")])
    writer.writerow(["market_comparable_value_usd", apr.get("market_comparable_value_usd")])
    writer.writerow(["network_effect_value_usd", apr.get("network_effect_value_usd")])
    writer.writerow(["complexity_adjusted_value_usd", apr.get("complexity_adjusted_value_usd")])
    writer.writerow(["capital_readiness", apr.get("capital_readiness")])
    for k, v in apr.get("subscores", {}).items():
        writer.writerow([f"subscore_{k}", v])
    for k, v in apr.get("risk_matrix", {}).items():
        writer.writerow([f"risk_{k}", v])
    for d in apr.get("deductions", []):
        writer.writerow([f"deduction_{d.get('category')}", f"{d.get('impact')}: {d.get('reason')}"])
    for act in apr.get("next_actions", []):
        writer.writerow([f"action_{act.get('priority')}", f"{act.get('action')} ({act.get('effort')})"])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="collateralops-{name}.csv"'}
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return HTMLResponse(content=(PAGES / "404.html").read_text(), status_code=404)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
