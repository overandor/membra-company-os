"""
Build a deployable collateral index from all local repos.
Run before deploying to Vercel:
  python3 build_index.py
Outputs data/index.json with all collateral records + classifications + appraisals.
"""
import json
import sys
import time
from pathlib import Path

from scanner import discover_projects, scan_collateral
from classifier import classify_repo
from appraiser import appraise
from packet import generate_packet, generate_lender_summary, generate_buyer_summary

SCAN_ROOT = Path.home() / "Downloads"
OUT = Path(__file__).parent / "data" / "index.json"


def build():
    print(f"Scanning {SCAN_ROOT}...")
    projects = discover_projects(SCAN_ROOT)
    print(f"Found {len(projects)} projects")

    index = {
        "generated_at": time.time(),
        "scan_root": str(SCAN_ROOT),
        "projects": [],
    }

    for i, proj in enumerate(projects):
        name = proj["name"]
        print(f"  [{i+1}/{len(projects)}] {name}...", end=" ", flush=True)

        records = scan_collateral(proj["path"])
        cls = classify_repo(proj["path"], name, records)
        apr = appraise(cls)
        pkt = generate_packet(cls, apr, records)

        # Strip heavy signals from classification for smaller index
        cls_light = {k: v for k, v in cls.items() if k != "signals"}
        cls_light["signals_summary"] = {
            "total_src": cls.get("signals", {}).get("total_src", 0),
            "primary_language": cls.get("signals", {}).get("primary_language", "none"),
            "has_git": cls.get("signals", {}).get("has_git", False),
            "has_readme": cls.get("signals", {}).get("has_readme", False),
            "has_license": cls.get("signals", {}).get("has_license", False),
            "has_tests": cls.get("signals", {}).get("has_tests", False),
            "has_dockerfile": cls.get("signals", {}).get("has_dockerfile", False),
            "has_ci": cls.get("signals", {}).get("has_ci", False),
            "has_vercel": cls.get("signals", {}).get("has_vercel", False),
            "has_env_file": cls.get("signals", {}).get("has_env_file", False),
            "total_files": cls.get("signals", {}).get("total_files", 0),
            "total_size_bytes": cls.get("signals", {}).get("total_size_bytes", 0),
            "test_files": cls.get("signals", {}).get("test_files", 0),
            "collateral_count": cls.get("signals", {}).get("collateral_count", 0),
        }

        entry = {
            "name": name,
            "classification": cls_light,
            "appraisal": apr,
            "collateral_records": records,
            "lender_summary": generate_lender_summary(pkt),
            "buyer_summary": generate_buyer_summary(pkt),
        }
        index["projects"].append(entry)

        at = cls.get("asset_type", "?")
        fs = apr.get("financeability_score", 0)
        rc = apr.get("replacement_cost_usd", 0)
        print(f"type={at} fs={fs} rc=${rc:.0f} coll={len(records)}")

    # Summary
    total_rc = sum(p["appraisal"]["replacement_cost_usd"] for p in index["projects"])
    total_csv = sum(p["appraisal"]["collateral_support_value_usd"] for p in index["projects"])
    financeable = sum(1 for p in index["projects"] if p["appraisal"]["financeability_score"] >= 40)

    index["summary"] = {
        "total_projects": len(index["projects"]),
        "total_replacement_cost_usd": round(total_rc, 2),
        "total_collateral_support_usd": round(total_csv, 2),
        "financeable_assets": financeable,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(index, f, indent=2, default=str)

    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"\nIndex written to {OUT} ({size_mb:.1f} MB)")
    print(f"Total projects: {len(index['projects'])}")
    print(f"Total replacement cost: ${total_rc:,.0f}")
    print(f"Total collateral support: ${total_csv:,.0f}")
    print(f"Financeable assets: {financeable}")


if __name__ == "__main__":
    build()
