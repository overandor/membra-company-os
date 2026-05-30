"""
CollateralOps dynamic project scanner.
Discovers ALL software projects and collateral folders.
No static copies — reads live from source directories.
"""
import json
import os
from pathlib import Path
from typing import Optional


DEFAULT_SCAN_ROOT = Path.home() / "Downloads"


def discover_projects(scan_root: Path = DEFAULT_SCAN_ROOT) -> list:
    """Find all software projects under scan_root."""
    projects = []
    if not scan_root.exists():
        return projects
    for entry in sorted(scan_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        has_collateral = (entry / "collateral").is_dir()
        # Check for source files (quick heuristic)
        has_src = False
        for pat in ["*.py", "*.ts", "*.js", "*.rs", "*.sol", "*.go"]:
            if list(entry.glob(pat)):
                has_src = True
                break
            src_dir = entry / "src"
            if src_dir.exists() and list(src_dir.glob(pat)):
                has_src = True
                break
        # Also check common project markers
        has_markers = any(
            (entry / f).exists()
            for f in ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml",
                       "README.md", "readme.md", ".git"]
        )
        if has_collateral or has_markers:
            projects.append({
                "name": entry.name,
                "path": str(entry),
                "has_collateral": has_collateral,
            })
    return projects


def scan_collateral(repo_path: str) -> list:
    """Scan a repo's collateral/ folder for .filelife.json files."""
    coll_dir = Path(repo_path) / "collateral"
    if not coll_dir.exists():
        return []
    records = []
    for fp in sorted(coll_dir.glob("*.filelife.json")):
        try:
            with open(fp) as f:
                rec = json.load(f)
            records.append(rec)
        except (json.JSONDecodeError, IOError):
            continue
    return records


def full_scan(scan_root: Path = DEFAULT_SCAN_ROOT) -> tuple:
    """Scan all projects and their collateral. Returns (projects, all_collateral)."""
    projects = discover_projects(scan_root)
    all_collateral = {}
    for proj in projects:
        records = scan_collateral(proj["path"])
        proj["collateral_count"] = len(records)
        if records:
            all_collateral[proj["name"]] = records
    return projects, all_collateral
