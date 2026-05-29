import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="MEMBRA Language Platform",
    description="Unified API for language-protocol, language-surfaces, and language-runtime collateral",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEMS = ["language-protocol", "language-surfaces", "language-runtime"]
DATA_DIR = Path(__file__).parent / "data"

_index: list[dict] = []


def load_index():
    global _index
    if _index:
        return _index
    for system in SYSTEMS:
        system_dir = DATA_DIR / system
        if not system_dir.exists():
            continue
        for fp in sorted(system_dir.glob("*.filelife.json")):
            with open(fp) as f:
                rec = json.load(f)
            rec["_system"] = system
            _index.append(rec)
    return _index


@app.on_event("startup")
async def startup():
    load_index()


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    idx = load_index()
    return {"status": "ok", "total_records": len(idx), "systems": SYSTEMS}


# ── Systems overview ────────────────────────────────────────────────────────

@app.get("/api/systems")
def list_systems():
    idx = load_index()
    out = []
    for s in SYSTEMS:
        items = [r for r in idx if r["_system"] == s]
        workstreams = sorted({r.get("workstream", "unknown") for r in items})
        out.append({
            "system": s,
            "total_files": len(items),
            "workstreams": workstreams,
        })
    return {"systems": out}


# ── Collateral list / filter ────────────────────────────────────────────────

@app.get("/api/collateral")
def list_collateral(
    system: Optional[str] = Query(None, description="Filter by system name"),
    workstream: Optional[str] = Query(None, description="Filter by workstream"),
    extension: Optional[str] = Query(None, description="Filter by file extension (.pdf, .csv, .zip)"),
    lifecycle_stage: Optional[int] = Query(None, description="Filter by lifecycle stage"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    idx = load_index()
    results = idx
    if system:
        results = [r for r in results if r["_system"] == system]
    if workstream:
        wl = workstream.lower()
        results = [r for r in results if wl in r.get("workstream", "").lower()]
    if extension:
        ext = extension if extension.startswith(".") else f".{extension}"
        results = [r for r in results if r.get("extension") == ext]
    if lifecycle_stage is not None:
        results = [r for r in results if r.get("lifecycle_stage") == lifecycle_stage]
    total = len(results)
    page = results[offset : offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "items": page}


# ── Single item by SKU ──────────────────────────────────────────────────────

@app.get("/api/collateral/sku/{sku}")
def get_by_sku(sku: str):
    idx = load_index()
    for r in idx:
        if r.get("sku") == sku:
            return r
    raise HTTPException(404, detail="SKU not found")


# ── Single system's collateral ──────────────────────────────────────────────

@app.get("/api/collateral/{system}")
def list_system_collateral(
    system: str,
    workstream: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if system not in SYSTEMS:
        raise HTTPException(404, detail=f"Unknown system: {system}")
    idx = load_index()
    results = [r for r in idx if r["_system"] == system]
    if workstream:
        wl = workstream.lower()
        results = [r for r in results if wl in r.get("workstream", "").lower()]
    total = len(results)
    page = results[offset : offset + limit]
    return {"system": system, "total": total, "offset": offset, "limit": limit, "items": page}


# ── Single file metadata ───────────────────────────────────────────────────

@app.get("/api/collateral/{system}/{filename}")
def get_file_metadata(system: str, filename: str):
    if system not in SYSTEMS:
        raise HTTPException(404, detail=f"Unknown system: {system}")
    idx = load_index()
    for r in idx:
        if r["_system"] == system and r.get("filename_hint") == filename:
            return r
    raise HTTPException(404, detail=f"File not found in {system}")


# ── Search ──────────────────────────────────────────────────────────────────

@app.get("/api/search")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=500),
):
    idx = load_index()
    ql = q.lower()
    hits = []
    for r in idx:
        searchable = " ".join([
            r.get("filename_hint", ""),
            r.get("workstream", ""),
            r.get("sub_workstream", ""),
            r.get("system_name", ""),
            r.get("sku", ""),
            r.get("row_id", ""),
        ]).lower()
        if ql in searchable:
            hits.append(r)
    return {"query": q, "total": len(hits), "items": hits[:limit]}


# ── Workstreams ─────────────────────────────────────────────────────────────

@app.get("/api/workstreams")
def list_workstreams():
    idx = load_index()
    ws_map: dict[str, dict] = {}
    for r in idx:
        ws = r.get("workstream", "unknown")
        if ws not in ws_map:
            ws_map[ws] = {"workstream": ws, "sub_workstreams": set(), "file_count": 0, "systems": set()}
        ws_map[ws]["sub_workstreams"].add(r.get("sub_workstream", ""))
        ws_map[ws]["file_count"] += 1
        ws_map[ws]["systems"].add(r["_system"])
    out = []
    for ws in sorted(ws_map):
        entry = ws_map[ws]
        out.append({
            "workstream": entry["workstream"],
            "sub_workstreams": sorted(entry["sub_workstreams"]),
            "file_count": entry["file_count"],
            "systems": sorted(entry["systems"]),
        })
    return {"workstreams": out}


# ── Stats ───────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def stats():
    idx = load_index()
    by_system: dict[str, int] = {}
    by_ext: dict[str, int] = {}
    by_stage: dict[int, int] = {}
    by_workstream: dict[str, int] = {}
    total_bytes = 0
    for r in idx:
        s = r["_system"]
        by_system[s] = by_system.get(s, 0) + 1
        ext = r.get("extension", "unknown")
        by_ext[ext] = by_ext.get(ext, 0) + 1
        stage = r.get("lifecycle_stage", -1)
        by_stage[stage] = by_stage.get(stage, 0) + 1
        ws = r.get("workstream", "unknown")
        by_workstream[ws] = by_workstream.get(ws, 0) + 1
        total_bytes += r.get("file_size_bytes", 0)
    return {
        "total_files": len(idx),
        "total_bytes": total_bytes,
        "by_system": by_system,
        "by_extension": by_ext,
        "by_lifecycle_stage": {str(k): v for k, v in sorted(by_stage.items())},
        "by_workstream": by_workstream,
    }


# ── Dashboard ───────────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MEMBRA Language Platform</title>
<style>
  :root { --bg: #0d0d0d; --card: #1a1a1a; --accent: #ff6b00; --text: #e0e0e0; --dim: #888; --border: #333; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'SF Mono', 'Fira Code', monospace; background: var(--bg); color: var(--text); min-height: 100vh; padding: 2rem; }
  h1 { color: var(--accent); font-size: 1.6rem; margin-bottom: 0.5rem; }
  .subtitle { color: var(--dim); margin-bottom: 2rem; font-size: 0.85rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.2rem; margin-bottom: 2rem; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem;
          box-shadow: 6px 6px 16px #080808, -4px -4px 12px #222; }
  .card h2 { color: var(--accent); font-size: 1rem; margin-bottom: 1rem; }
  .stat { font-size: 2rem; font-weight: bold; color: #fff; }
  .stat-label { color: var(--dim); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; }
  .bar-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
  .bar-label { width: 120px; font-size: 0.75rem; color: var(--dim); text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bar { height: 18px; background: var(--accent); border-radius: 4px; min-width: 4px; transition: width 0.6s ease; }
  .bar-val { font-size: 0.75rem; color: var(--text); min-width: 30px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  th { text-align: left; color: var(--accent); padding: 0.5rem; border-bottom: 1px solid var(--border); }
  td { padding: 0.5rem; border-bottom: 1px solid #222; color: var(--text); }
  tr:hover td { background: #222; }
  .endpoint { background: #222; border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; }
  .endpoint code { color: var(--accent); font-size: 0.85rem; }
  .endpoint .method { background: var(--accent); color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }
  .endpoint .desc { color: var(--dim); font-size: 0.75rem; }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  #search { width: 100%; padding: 0.75rem 1rem; background: #222; border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-family: inherit; font-size: 0.9rem; margin-bottom: 1rem; }
  #search:focus { outline: none; border-color: var(--accent); }
  #results { max-height: 400px; overflow-y: auto; }
  .pill { display: inline-block; background: #333; color: var(--accent); padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; margin-right: 4px; }
</style>
</head>
<body>
<h1>MEMBRA Language Platform</h1>
<p class="subtitle">Unified collateral API &mdash; language-protocol &bull; language-surfaces &bull; language-runtime</p>

<div class="grid">
  <div class="card">
    <h2>Overview</h2>
    <div id="overview">Loading...</div>
  </div>
  <div class="card">
    <h2>By System</h2>
    <div id="by-system"></div>
  </div>
  <div class="card">
    <h2>By Extension</h2>
    <div id="by-ext"></div>
  </div>
  <div class="card">
    <h2>By Workstream</h2>
    <div id="by-ws"></div>
  </div>
</div>

<div class="card" style="margin-bottom:2rem">
  <h2>Search Collateral</h2>
  <input id="search" type="text" placeholder="Search by filename, workstream, SKU...">
  <div id="results"></div>
</div>

<div class="card" style="margin-bottom:2rem">
  <h2>API Endpoints</h2>
  <div class="endpoint"><div><span class="method">GET</span> <code>/health</code></div><span class="desc">Health check + record count</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/systems</code></div><span class="desc">List all systems with workstreams</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/collateral</code></div><span class="desc">List/filter all collateral (system, workstream, extension, stage)</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/collateral/sku/{sku}</code></div><span class="desc">Lookup by SKU</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/collateral/{system}</code></div><span class="desc">Collateral for a single system</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/collateral/{system}/{filename}</code></div><span class="desc">Single file metadata</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/search?q=...</code></div><span class="desc">Full-text search</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/workstreams</code></div><span class="desc">All workstreams with counts</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/api/stats</code></div><span class="desc">Aggregate statistics</span></div>
  <div class="endpoint"><div><span class="method">GET</span> <code>/docs</code></div><span class="desc">Interactive OpenAPI docs (Swagger)</span></div>
</div>

<script>
const BASE = '';
function makeBar(label, val, max) {
  const pct = max > 0 ? (val / max * 100) : 0;
  return `<div class="bar-row"><span class="bar-label" title="${label}">${label}</span><div class="bar" style="width:${pct}%"></div><span class="bar-val">${val}</span></div>`;
}
async function init() {
  const stats = await (await fetch(BASE + '/api/stats')).json();
  document.getElementById('overview').innerHTML = `
    <div class="stat">${stats.total_files}</div><div class="stat-label">Total Files</div>
    <div style="margin-top:1rem"><span class="stat">${(stats.total_bytes/1024).toFixed(1)}</span> <span class="stat-label">KB total</span></div>
    <div style="margin-top:1rem"><span class="stat">${Object.keys(stats.by_workstream).length}</span> <span class="stat-label">Workstreams</span></div>`;
  const sysMax = Math.max(...Object.values(stats.by_system));
  document.getElementById('by-system').innerHTML = Object.entries(stats.by_system).map(([k,v]) => makeBar(k.replace('language-',''),v,sysMax)).join('');
  const extMax = Math.max(...Object.values(stats.by_extension));
  document.getElementById('by-ext').innerHTML = Object.entries(stats.by_extension).sort((a,b)=>b[1]-a[1]).map(([k,v]) => makeBar(k,v,extMax)).join('');
  const wsMax = Math.max(...Object.values(stats.by_workstream));
  document.getElementById('by-ws').innerHTML = Object.entries(stats.by_workstream).sort((a,b)=>b[1]-a[1]).map(([k,v]) => makeBar(k,v,wsMax)).join('');
}
let debounce;
document.getElementById('search').addEventListener('input', e => {
  clearTimeout(debounce);
  debounce = setTimeout(async () => {
    const q = e.target.value.trim();
    if (!q) { document.getElementById('results').innerHTML = ''; return; }
    const data = await (await fetch(BASE + '/api/search?q=' + encodeURIComponent(q))).json();
    if (!data.items.length) { document.getElementById('results').innerHTML = '<p style="color:#888">No results</p>'; return; }
    document.getElementById('results').innerHTML = '<table><tr><th>File</th><th>System</th><th>Workstream</th><th>Ext</th></tr>' +
      data.items.slice(0,30).map(r => `<tr><td>${r.filename_hint}</td><td><span class="pill">${r._system.replace('language-','')}</span></td><td>${r.workstream||''}</td><td>${r.extension}</td></tr>`).join('') + '</table>';
  }, 300);
});
init();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
