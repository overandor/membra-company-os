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

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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
            blocked.append({"name": name, "critical_risks": critical, "financeability": _appraisals.get(name, {}).get("financeability_score", 0)})
    return {"total": len(blocked), "items": blocked}


@app.get("/api/portfolio/improvement-queue")
def improvement_queue():
    queue = []
    for name, apr in _appraisals.items():
        fs = apr.get("financeability_score", 0)
        at = _classifications.get(name, {}).get("asset_type", "")
        if fs < 80 and at not in ("junk", "scaffold", "duplicate"):
            actions = apr.get("next_actions", [])
            queue.append({"name": name, "current_financeability": fs, "replacement_cost": apr.get("replacement_cost_usd", 0), "top_action": actions[0] if actions else None})
    queue.sort(key=lambda q: (-q["replacement_cost"], q["current_financeability"]))
    return {"total": len(queue), "items": queue}


# ── Rescan (local mode only) ──────────────────────────────────────

@app.post("/api/rescan")
def rescan():
    if IS_VERCEL:
        return {"status": "index_mode", "note": "Rescan not available in deployed mode. Rebuild index locally and redeploy."}
    _scan_live()
    return {"status": "rescanned", "total_projects": len(_projects)}


# ── Pages ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
