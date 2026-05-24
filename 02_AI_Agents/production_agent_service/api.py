#!/usr/bin/env python3
"""
Production Agent Service API
FastAPI backend with scan, appraise, and payment endpoints.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from scanner import scan_workspace
from appraiser import appraise_project, report_to_dict

# Optional Stripe integration
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

app = FastAPI(title="Production Agent Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with Redis/DB for production)
SCANS: Dict[str, Dict[str, Any]] = {}
APPRAISALS: Dict[str, Dict[str, Any]] = {}
PAYMENTS: Dict[str, Dict[str, Any]] = {}

PRICING = {
    "basic": {"price_usd": 0, "label": "Basic Scan", "features": ["Project inventory", "Basic readiness score", "Security secrets check"]},
    "pro": {"price_usd": 2900, "label": "Pro Appraisal", "features": ["Full appraisal report", "Monetization scoring", "Action plan", "Priority support"]},
    "enterprise": {"price_usd": 9900, "label": "Enterprise Suite", "features": ["Everything in Pro", "Custom CI/CD setup", "Deployment packaging", "Dedicated agent"]},
}

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DASHBOARD_DIR = Path(__file__).parent / "dashboard"

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    root_path: str = "/Users/alep/Downloads"
    max_depth: int = 6

class AppraiseRequest(BaseModel):
    project_path: str
    project_type: str = "unknown"

class PaymentIntentRequest(BaseModel):
    tier: str
    email: str

class PaymentConfirmRequest(BaseModel):
    payment_intent_id: str

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_state():
    global SCANS, APPRAISALS
    scan_file = DATA_DIR / "scans.json"
    appr_file = DATA_DIR / "appraisals.json"
    if scan_file.is_file():
        SCANS = json.loads(scan_file.read_text())
    if appr_file.is_file():
        APPRAISALS = json.loads(appr_file.read_text())


def _save_state():
    (DATA_DIR / "scans.json").write_text(json.dumps(SCANS, indent=2, default=str))
    (DATA_DIR / "appraisals.json").write_text(json.dumps(APPRAISALS, indent=2, default=str))


_load_state()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"service": "Production Agent Service", "version": "2.0.0", "status": "online"}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/scan")
def create_scan(req: ScanRequest):
    scan_id = str(uuid.uuid4())[:8]
    root = Path(req.root_path).expanduser().resolve()
    if not root.is_dir():
        raise HTTPException(status_code=400, detail="Invalid root path")

    result = scan_workspace(root, max_depth=req.max_depth)
    data = {
        "scan_id": scan_id,
        "root_path": str(root),
        "scanned_at": result.scanned_at,
        "total_projects": len(result.projects),
        "total_files": result.total_files,
        "total_size_mb": round(result.total_size / (1024 * 1024), 2),
        "projects": [
            {
                "name": p.name,
                "root": p.root,
                "type": p.project_type,
                "files": p.total_files,
                "size_mb": round(p.total_size / (1024 * 1024), 2),
                "languages": p.languages,
            }
            for p in result.projects
        ],
    }
    SCANS[scan_id] = data
    _save_state()
    return data


@app.get("/api/scans")
def list_scans():
    return {"scans": list(SCANS.values())}


@app.get("/api/scan/{scan_id}")
def get_scan(scan_id: str):
    if scan_id not in SCANS:
        raise HTTPException(status_code=404, detail="Scan not found")
    return SCANS[scan_id]


@app.post("/api/appraise")
def create_appraisal(req: AppraiseRequest):
    appr_id = str(uuid.uuid4())[:8]
    root = Path(req.project_path).expanduser().resolve()
    if not root.is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path")

    report = appraise_project(root, project_type=req.project_type)
    data = report_to_dict(report)
    data["appraisal_id"] = appr_id
    APPRAISALS[appr_id] = data
    _save_state()
    return data


@app.get("/api/appraisals")
def list_appraisals(project_name: Optional[str] = Query(None)):
    results = list(APPRAISALS.values())
    if project_name:
        results = [r for r in results if project_name.lower() in r["project_name"].lower()]
    return {"appraisals": results}


@app.get("/api/appraisal/{appraisal_id}")
def get_appraisal(appraisal_id: str):
    if appraisal_id not in APPRAISALS:
        raise HTTPException(status_code=404, detail="Appraisal not found")
    return APPRAISALS[appraisal_id]


@app.get("/api/pricing")
def get_pricing():
    return PRICING


@app.post("/api/payment/intent")
def create_payment_intent(req: PaymentIntentRequest):
    tier = PRICING.get(req.tier)
    if not tier:
        raise HTTPException(status_code=400, detail="Invalid tier")

    pi_id = f"pi_{uuid.uuid4().hex[:16]}"
    PAYMENTS[pi_id] = {
        "payment_intent_id": pi_id,
        "tier": req.tier,
        "amount_usd": tier["price_usd"],
        "email": req.email,
        "status": "requires_payment_method",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # If Stripe is configured, use real Stripe; otherwise return mock intent
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if STRIPE_AVAILABLE and stripe_key and not stripe_key.startswith("sk_test_dummy"):
        stripe.api_key = stripe_key
        try:
            intent = stripe.PaymentIntent.create(
                amount=tier["price_usd"],
                currency="usd",
                receipt_email=req.email,
                metadata={"tier": req.tier},
            )
            PAYMENTS[pi_id]["stripe_payment_intent_id"] = intent.id
            PAYMENTS[pi_id]["client_secret"] = intent.client_secret
            PAYMENTS[pi_id]["status"] = intent.status
        except Exception as e:
            PAYMENTS[pi_id]["error"] = str(e)
    else:
        PAYMENTS[pi_id]["client_secret"] = f"{pi_id}_secret_mock"
    _save_state()
    return PAYMENTS[pi_id]


@app.post("/api/payment/confirm")
def confirm_payment(req: PaymentConfirmRequest):
    # Find by intent ID
    for pi_id, data in PAYMENTS.items():
        if data.get("stripe_payment_intent_id") == req.payment_intent_id or pi_id == req.payment_intent_id:
            data["status"] = "succeeded"
            data["confirmed_at"] = datetime.now(timezone.utc).isoformat()
            _save_state()
            return data
    raise HTTPException(status_code=404, detail="Payment intent not found")


@app.get("/api/payments")
def list_payments():
    return {"payments": list(PAYMENTS.values())}


@app.post("/api/batch-appraise")
def batch_appraise(req: ScanRequest):
    """Scan and appraise every project found in the workspace."""
    root = Path(req.root_path).expanduser().resolve()
    if not root.is_dir():
        raise HTTPException(status_code=400, detail="Invalid root path")

    result = scan_workspace(root, max_depth=req.max_depth)
    reports = []
    for proj in result.projects:
        try:
            report = appraise_project(Path(proj.root), project_type=proj.project_type)
            data = report_to_dict(report)
            data["appraisal_id"] = str(uuid.uuid4())[:8]
            APPRAISALS[data["appraisal_id"]] = data
            reports.append(data)
        except Exception as e:
            reports.append({"project_name": proj.name, "error": str(e)})

    _save_state()
    return {
        "scanned_at": result.scanned_at,
        "total_projects": len(result.projects),
        "appraised": len([r for r in reports if "error" not in r]),
        "failed": len([r for r in reports if "error" in r]),
        "reports": reports,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

if DASHBOARD_DIR.is_dir():
    app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")


@app.get("/ui", response_class=HTMLResponse)
def serve_dashboard():
    index = DASHBOARD_DIR / "index.html"
    if index.is_file():
        return HTMLResponse(content=index.read_text(), status_code=200)
    # Fallback inline dashboard
    return HTMLResponse(content=_INLINE_DASHBOARD, status_code=200)


# ---------------------------------------------------------------------------
# Inline dashboard HTML (used if dashboard/ directory is missing)
# ---------------------------------------------------------------------------

_INLINE_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Production Agent Service</title>
<style>
:root{--bg:#0b0f19;--card:#111827;--accent:#10b981;--accent2:#3b82f6;--text:#e5e7eb;--muted:#9ca3af;--danger:#ef4444;--warn:#f59e0b;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;line-height:1.5}
.container{max-width:1200px;margin:0 auto;padding:24px}
header{display:flex;align-items:center;justify-content:space-between;margin-bottom:32px}
h1{font-size:1.6rem}
.badge{background:var(--accent);color:#000;font-size:.75rem;font-weight:700;padding:4px 10px;border-radius:999px}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:var(--card);border:1px solid #1f2937;border-radius:12px;padding:20px}
.card h2{font-size:1.1rem;margin-bottom:12px}
.metric{font-size:2rem;font-weight:700;color:var(--accent)}
.btn{background:var(--accent2);color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer;font-size:.9rem}
.btn:hover{opacity:.9}
.btn.secondary{background:#374151}
table{width:100%;border-collapse:collapse;margin-top:12px;font-size:.85rem}
th,td{padding:10px 8px;text-align:left;border-bottom:1px solid #1f2937}
th{color:var(--muted);font-weight:600}
.grade-A{color:var(--accent);font-weight:700}
.grade-B{color:#34d399;font-weight:700}
.grade-C{color:var(--warn);font-weight:700}
.grade-D{color:var(--danger);font-weight:700}
.grade-F{color:#7f1d1d;font-weight:700}
pre{background:#0b0f19;border:1px solid #1f2937;border-radius:8px;padding:12px;overflow:auto;max-height:400px;font-size:.8rem}
.tabs{display:flex;gap:8px;margin-bottom:16px}
.tab{padding:8px 14px;border-radius:8px;background:#1f2937;color:var(--muted);cursor:pointer;border:none}
.tab.active{background:var(--accent2);color:#fff}
.section{display:none}
.section.active{display:block}
input,select{background:#0b0f19;border:1px solid #374151;color:var(--text);padding:10px 12px;border-radius:8px;width:100%;margin-bottom:10px}
.pricing-card{border:1px solid #1f2937;border-radius:12px;padding:20px;text-align:center}
.price{font-size:2rem;font-weight:700;color:var(--accent)}
.features{text-align:left;margin:12px 0;padding-left:18px;color:var(--muted)}
.features li{margin-bottom:6px}
</style>
</head>
<body>
<div class="container">
<header><h1>Production Agent Service</h1><span class="badge">ONLINE</span></header>
<div class="tabs">
<button class="tab active" onclick="showTab('dashboard')">Dashboard</button>
<button class="tab" onclick="showTab('scan')">Scan</button>
<button class="tab" onclick="showTab('appraisals')">Appraisals</button>
<button class="tab" onclick="showTab('pricing')">Pricing</button>
</div>

<div id="dashboard" class="section active">
<div class="grid">
<div class="card"><h2>Total Scans</h2><div class="metric" id="totalScans">0</div></div>
<div class="card"><h2>Total Appraisals</h2><div class="metric" id="totalAppraisals">0</div></div>
<div class="card"><h2>Avg Score</h2><div class="metric" id="avgScore">-</div></div>
<div class="card"><h2>Total Est. Value</h2><div class="metric" id="totalValue">$0</div></div>
</div>
<div class="card" style="margin-top:16px"><h2>Latest Appraisals</h2><table><thead><tr><th>Project</th><th>Type</th><th>Score</th><th>Grade</th><th>Value</th></tr></thead><tbody id="latestBody"></tbody></table></div>
</div>

<div id="scan" class="section">
<div class="card">
<h2>Scan Workspace</h2>
<input type="text" id="scanPath" value="/Users/alep/Downloads" placeholder="Root path">
<button class="btn" onclick="runScan()">Scan Now</button>
<button class="btn secondary" onclick="batchAppraise()">Scan + Appraise All</button>
<pre id="scanResult">Ready to scan.</pre>
</div>
</div>

<div id="appraisals" class="section">
<div class="card">
<h2>All Appraisals</h2>
<table><thead><tr><th>Project</th><th>Type</th><th>Score</th><th>Grade</th><th>Value</th><th>Secrets</th></tr></thead><tbody id="apprBody"></tbody></table>
</div>
</div>

<div id="pricing" class="section">
<div class="grid">
<div class="pricing-card"><h3>Basic</h3><div class="price">Free</div><ul class="features"><li>Project inventory</li><li>Basic readiness score</li><li>Security secrets check</li></ul><button class="btn secondary" onclick="alert('Basic is free — just scan!')">Start Free</button></div>
<div class="pricing-card"><h3>Pro</h3><div class="price">$29</div><ul class="features"><li>Full appraisal report</li><li>Monetization scoring</li><li>Action plan</li><li>Priority support</li></ul><button class="btn" onclick="createPayment('pro')">Buy Pro</button></div>
<div class="pricing-card"><h3>Enterprise</h3><div class="price">$99</div><ul class="features"><li>Everything in Pro</li><li>Custom CI/CD setup</li><li>Deployment packaging</li><li>Dedicated agent</li></ul><button class="btn" onclick="createPayment('enterprise')">Buy Enterprise</button></div>
</div>
<div class="card" style="margin-top:16px"><h2>Payment Status</h2><pre id="paymentResult">No payments yet.</pre></div>
</div>

</div>
<script>
const API = location.origin + '/api';
async function fetchJSON(url,opts){try{const r=await fetch(url,opts);return await r.json()}catch(e){return {error:e.message}}}
function showTab(id){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));event.target.classList.add('active');document.getElementById(id).classList.add('active');if(id==='appraisals')loadAppraisals();if(id==='dashboard')loadDashboard();}
async function loadDashboard(){const a=(await fetchJSON(API+'/appraisals')).appraisals||[];document.getElementById('totalAppraisals').textContent=a.length;const s=(await fetchJSON(API+'/scans')).scans||[];document.getElementById('totalScans').textContent=s.length;const scores=a.filter(x=>x.overall_score).map(x=>x.overall_score);document.getElementById('avgScore').textContent=scores.length?(scores.reduce((a,b)=>a+b,0)/scores.length).toFixed(1):'-';const tv=a.reduce((sum,x)=>sum+(x.estimated_value_usd||0),0);document.getElementById('totalValue').textContent='$'+tv.toLocaleString();const tb=document.getElementById('latestBody');tb.innerHTML='';a.slice(0,10).forEach(r=>{const g='grade-'+r.readiness_grade;tb.innerHTML+=`<tr><td>${r.project_name}</td><td>${r.project_type}</td><td>${r.overall_score}</td><td class="${g}">${r.readiness_grade}</td><td>$${(r.estimated_value_usd||0).toLocaleString()}</td></tr>`;});}
async function runScan(){const path=document.getElementById('scanPath').value;document.getElementById('scanResult').textContent='Scanning...';const res=await fetchJSON(API+'/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({root_path:path})});document.getElementById('scanResult').textContent=JSON.stringify(res,null,2);loadDashboard();}
async function batchAppraise(){const path=document.getElementById('scanPath').value;document.getElementById('scanResult').textContent='Scanning and appraising all projects...';const res=await fetchJSON(API+'/batch-appraise',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({root_path:path})});document.getElementById('scanResult').textContent=JSON.stringify(res,null,2);loadDashboard();}
async function loadAppraisals(){const a=(await fetchJSON(API+'/appraisals')).appraisals||[];const tb=document.getElementById('apprBody');tb.innerHTML='';a.forEach(r=>{const g='grade-'+r.readiness_grade;const sc=(r.secrets||[]).length;tb.innerHTML+=`<tr><td>${r.project_name}</td><td>${r.project_type}</td><td>${r.overall_score}</td><td class="${g}">${r.readiness_grade}</td><td>$${(r.estimated_value_usd||0).toLocaleString()}</td><td>${sc?'<span style=color:var(--danger)>Yes ('+sc+')</span>':'No'}</td></tr>`;});}
async function createPayment(tier){const email=prompt('Enter email:');if(!email)return;const res=await fetchJSON(API+'/payment/intent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tier,email})});document.getElementById('paymentResult').textContent=JSON.stringify(res,null,2);}
loadDashboard();
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
