#!/usr/bin/env python3
"""
Auto-install LLM integration into every project in the workspace.
Detects project type and drops the appropriate adapter.
"""

import json
import os
import shutil
from pathlib import Path
from typing import List

OLLAMA_HUB = Path(__file__).parent.resolve()
ADAPTERS_DIR = OLLAMA_HUB / "adapters"

ADAPTER_MAP = {
    "python": {
        "file": "python_adapter.py",
        "dest_name": "llm.py",
        "marker": ("requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "*.py"),
    },
    "nodejs": {
        "file": "javascript_adapter.js",
        "dest_name": "llm.js",
        "marker": ("package.json", "*.js", "*.ts", "*.tsx"),
    },
    "rust": {
        "file": "rust_adapter.rs",
        "dest_name": "llm.rs",
        "marker": ("Cargo.toml", "*.rs"),
    },
    "go": {
        "file": "go_adapter.go",
        "dest_name": "llm.go",
        "marker": ("go.mod", "*.go"),
    },
    "shell": {
        "file": "shell_adapter.sh",
        "dest_name": "llm.sh",
        "marker": ("*.sh", "Makefile", "*.bash"),
    },
}


def detect_project_types(project_root: Path) -> List[str]:
    types = []
    files = set(f.name for f in project_root.iterdir() if f.is_file())
    all_files = list(project_root.rglob("*"))

    for ptype, info in ADAPTER_MAP.items():
        for marker in info["marker"]:
            if marker.startswith("*."):
                ext = marker[1:]  # e.g. .py
                if any(f.name.endswith(ext) for f in all_files[:200]):
                    types.append(ptype)
                    break
            else:
                if marker in files:
                    types.append(ptype)
                    break
    return types


def install_adapter(project_root: Path, project_type: str, dry_run: bool = False) -> bool:
    info = ADAPTER_MAP.get(project_type)
    if not info:
        return False

    src = ADAPTERS_DIR / info["file"]
    if not src.exists():
        print(f"  SKIP: adapter source missing {src}")
        return False

    dest = project_root / info["dest_name"]
    if dest.exists():
        print(f"  SKIP: {dest.name} already exists")
        return False

    if dry_run:
        print(f"  Would install {info['file']} -> {dest}")
        return True

    shutil.copy2(src, dest)
    print(f"  INSTALLED: {dest}")
    return True


def install_for_project(project_root: Path, dry_run: bool = False) -> dict:
    result = {"path": str(project_root), "types": [], "installed": [], "skipped": []}
    if not project_root.exists():
        result["skipped"].append("DIR_MISSING")
        return result
    types = detect_project_types(project_root)
    result["types"] = types

    for ptype in types:
        info = ADAPTER_MAP.get(ptype)
        dest = project_root / info["dest_name"]
        if dest.exists():
            result["skipped"].append(info["dest_name"])
            continue
        if install_adapter(project_root, ptype, dry_run):
            result["installed"].append(info["dest_name"])

    return result


def scan_and_install(root: Path, dry_run: bool = False) -> List[dict]:
    """Use scanner.py's project detection for accurate results."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "production_agent_service"))
    from scanner import scan_workspace

    print("  Discovering projects via scanner...")
    scan_result = scan_workspace(root, max_depth=6)
    results = []

    for proj in scan_result.projects:
        p = Path(proj.root)
        print(f"\nProject: {p.name} ({p})")
        result = install_for_project(p, dry_run)
        results.append(result)

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Install LLM adapters into all projects")
    parser.add_argument("--root", default="/Users/alep/Downloads", help="Workspace root")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    print(f"Scanning: {root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("-" * 60)

    results = scan_and_install(root, dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    print(f"Projects processed: {len(results)}")
    total_installed = sum(len(r["installed"]) for r in results)
    total_skipped = sum(len(r["skipped"]) for r in results)
    print(f"Adapters installed: {total_installed}")
    print(f"Already existed (skipped): {total_skipped}")
    print(f"{'=' * 60}")

    # Save manifest
    manifest = {
        "installed_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat().replace("+00:00", "Z"),
        "root": str(root),
        "dry_run": args.dry_run,
        "results": results,
    }
    manifest_path = OLLAMA_HUB / "install_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
