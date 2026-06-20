"""
appraiser_bridge.py — use continuous_file_appraiser output as a valuation source.

The `continuous_file_appraiser` (06_Projects/continuous_file_appraiser) writes an
`appraisal_ledger.json` assigning each file a dollar value
(hourly_rate * estimated_hours * complexity). This bridge sums that ledger into a
bottom-up valuation that can override or cross-check the pipeline's 5 methods —
grounding the appraisal in per-file LLM assessment rather than aggregate proxies.
"""
from __future__ import annotations
import json


def load_appraisal_total(ledger_path: str) -> dict:
    with open(ledger_path) as fh:
        data = json.load(fh)
    # tolerate a few shapes: {files:[{value/dollar_value}]} | {path: {value}} | [ {value} ]
    rows = []
    if isinstance(data, dict) and "files" in data:
        rows = data["files"]
    elif isinstance(data, dict):
        rows = list(data.values())
    elif isinstance(data, list):
        rows = data
    total, n = 0.0, 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        v = r.get("dollar_value", r.get("value", r.get("usd", 0))) or 0
        try:
            total += float(v); n += 1
        except (TypeError, ValueError):
            pass
    return {"appraised_total_usd": round(total), "n_files": n, "source": ledger_path}


def as_valuation_method(ledger_path: str, haircut: float = 0.5) -> dict:
    """Return a valuation-method entry (conservative haircut) for blending into underwrite."""
    a = load_appraisal_total(ledger_path)
    return {"method": "file_appraiser_bottom_up",
            "gross_usd": a["appraised_total_usd"],
            "net_usd": round(a["appraised_total_usd"] * haircut),
            "n_files": a["n_files"]}
