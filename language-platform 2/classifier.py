"""
Asset classifier for CollateralOps.
Classifies discovered repos/folders into asset types,
detects features, and assigns proof levels.
"""
import os
import re
from pathlib import Path
from collections import Counter


ASSET_TYPES = [
    "production_system", "working_prototype", "research_prototype",
    "internal_tool", "api_service", "frontend_product", "backend_service",
    "trading_engine", "smart_contract", "huggingface_space", "dataset",
    "prompt_system", "agent_workflow", "documentation_package",
    "proof_ledger", "collateral_package", "outreach_system",
    "fork_template", "scaffold", "duplicate", "junk",
]

PROOF_LEVELS = {
    0: "Claimed",
    1: "Discovered",
    2: "Hashed",
    3: "Clean",
    4: "Build-Checked",
    5: "Use-Checked",
    6: "Market-Checked",
    7: "Financeable",
}


def classify_repo(repo_path: str, repo_name: str, collateral_records: list) -> dict:
    """Classify a repository into an asset type and compute signals."""
    p = Path(repo_path)
    if not p.exists():
        return _empty_classification(repo_name, repo_path)

    signals = _detect_signals(p)
    asset_type = _infer_type(repo_name, signals, collateral_records)
    proof_level = _compute_proof_level(signals, collateral_records)
    risk_flags = _detect_risks(signals, collateral_records)
    quality_scores = _compute_quality(signals, collateral_records)

    return {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "asset_type": asset_type,
        "proof_level": proof_level,
        "proof_level_name": PROOF_LEVELS.get(proof_level, "Unknown"),
        "signals": signals,
        "risk_flags": risk_flags,
        "quality": quality_scores,
        "collateral_files": len(collateral_records),
        "workstreams": _extract_workstreams(collateral_records),
    }


def _empty_classification(name, path):
    return {
        "repo_name": name, "repo_path": path, "asset_type": "junk",
        "proof_level": 0, "proof_level_name": "Claimed",
        "signals": {}, "risk_flags": ["path_not_found"],
        "quality": {}, "collateral_files": 0, "workstreams": [],
    }


def _detect_signals(p: Path) -> dict:
    """Detect all observable signals from the repo directory."""
    sigs = {}

    # Source code — fast count using os.walk with depth limit
    import os as _os
    MAX_DEPTH = 6
    MAX_FILES = 2000
    counts = {"py": 0, "ts": 0, "js": 0, "rs": 0, "sol": 0, "go": 0}
    all_src = []
    base_depth = str(p).count(_os.sep)
    try:
        for root, dirs, files in _os.walk(str(p)):
            depth = root.count(_os.sep) - base_depth
            if depth > MAX_DEPTH:
                dirs.clear()
                continue
            # Skip heavy dirs
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__", "venv", ".next", "dist", "build")]
            for fn in files:
                ext = fn.rsplit(".", 1)[-1] if "." in fn else ""
                if ext in counts:
                    counts[ext] += 1
                    if len(all_src) < MAX_FILES:
                        all_src.append(Path(root) / fn)
            if sum(counts.values()) >= MAX_FILES:
                break
    except (PermissionError, OSError):
        pass
    py = [f for f in all_src if f.suffix == ".py"]
    ts = [f for f in all_src if f.suffix == ".ts"]
    js = [f for f in all_src if f.suffix == ".js"]
    rs = [f for f in all_src if f.suffix == ".rs"]
    sol = [f for f in all_src if f.suffix == ".sol"]
    go = [f for f in all_src if f.suffix == ".go"]
    sigs["py_files"] = len(py)
    sigs["ts_files"] = len(ts)
    sigs["js_files"] = len(js)
    sigs["rs_files"] = len(rs)
    sigs["sol_files"] = len(sol)
    sigs["go_files"] = len(go)
    sigs["total_src"] = sum([len(py), len(ts), len(js), len(rs), len(sol), len(go)])

    # Primary language
    lang_counts = {"python": len(py), "typescript": len(ts), "javascript": len(js),
                   "rust": len(rs), "solidity": len(sol), "go": len(go)}
    sigs["primary_language"] = max(lang_counts, key=lang_counts.get) if any(lang_counts.values()) else "none"

    # Infrastructure
    sigs["has_git"] = (p / ".git").exists()
    sigs["has_readme"] = (p / "README.md").exists() or (p / "readme.md").exists()
    sigs["has_license"] = (p / "LICENSE").exists() or (p / "LICENSE.md").exists() or (p / "LICENCE").exists()
    sigs["has_dockerfile"] = (p / "Dockerfile").exists()
    sigs["has_docker_compose"] = (p / "docker-compose.yml").exists() or (p / "docker-compose.yaml").exists()
    sigs["has_ci"] = (p / ".github" / "workflows").exists() or (p / ".gitlab-ci.yml").exists()
    sigs["has_vercel"] = (p / "vercel.json").exists()
    sigs["has_package_json"] = (p / "package.json").exists()
    sigs["has_requirements"] = (p / "requirements.txt").exists()
    sigs["has_pyproject"] = (p / "pyproject.toml").exists()
    sigs["has_cargo"] = (p / "Cargo.toml").exists()
    sigs["has_tsconfig"] = (p / "tsconfig.json").exists() or (p / "tsconfig.base.json").exists()

    # Risk signals
    sigs["has_env_file"] = (p / ".env").exists() or (p / ".env.local").exists()
    sigs["has_gitignore"] = (p / ".gitignore").exists()
    sigs["has_collateral"] = (p / "collateral").is_dir()

    # Test signals
    test_files = [f for f in (py + ts + js)[:2000] if "test" in f.name.lower() or "spec" in f.name.lower()]
    sigs["test_files"] = len(test_files)
    sigs["has_tests"] = len(test_files) > 0

    # Deployment signals
    sigs["has_procfile"] = (p / "Procfile").exists()
    sigs["has_render"] = (p / "render.yaml").exists()

    # Collateral
    coll_dir = p / "collateral"
    if coll_dir.exists():
        sigs["collateral_count"] = len(list(coll_dir.glob("*.filelife.json")))
    else:
        sigs["collateral_count"] = 0

    # Size — reuse os.walk data, don't rescan
    total_size = 0
    file_count = 0
    try:
        for root, dirs, files in _os.walk(str(p)):
            depth = root.count(_os.sep) - base_depth
            if depth > MAX_DEPTH:
                dirs.clear()
                continue
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__", "venv", ".next", "dist", "build")]
            for fn in files:
                try:
                    total_size += (Path(root) / fn).stat().st_size
                except OSError:
                    pass
                file_count += 1
                if file_count >= 5000:
                    break
            if file_count >= 5000:
                break
    except (PermissionError, OSError):
        pass
    sigs["total_size_bytes"] = total_size
    sigs["total_files"] = file_count

    return sigs


def _infer_type(name: str, sigs: dict, records: list) -> str:
    """Infer asset type from signals."""
    nl = name.lower()
    src = sigs.get("total_src", 0)
    has_coll = sigs.get("has_collateral", False)
    coll_count = sigs.get("collateral_count", 0)

    # No source and no collateral = junk
    if src == 0 and coll_count == 0:
        return "junk"

    # Only collateral, no source = collateral package
    if src == 0 and coll_count > 0:
        return "collateral_package"

    # Trading keywords
    if any(k in nl for k in ["trade", "arb", "bot", "algo", "profit", "hedge", "swap"]):
        return "trading_engine"

    # Smart contract keywords
    if sigs.get("sol_files", 0) > 0 or any(k in nl for k in ["contract", "solana", "membra-"]):
        return "smart_contract"

    # Agent/AI keywords
    if any(k in nl for k in ["agent", "llm", "ai", "inference", "model"]):
        return "agent_workflow"

    # API/service
    if any(k in nl for k in ["api", "service", "server", "worker"]):
        return "api_service"

    # Frontend
    if sigs.get("has_tsconfig") and sigs.get("has_package_json"):
        if any(k in nl for k in ["dashboard", "app", "ui", "frontend", "web"]):
            return "frontend_product"

    # Has deployment = working prototype or production
    if sigs.get("has_dockerfile") or sigs.get("has_vercel") or sigs.get("has_procfile"):
        if sigs.get("has_tests") and sigs.get("has_ci"):
            return "production_system"
        return "working_prototype"

    # Has some source but minimal
    if src < 5:
        return "scaffold"

    # Research/protocol
    if any(k in nl for k in ["research", "proof", "protocol", "zk"]):
        return "research_prototype"

    # Default
    if src >= 10 and sigs.get("has_readme"):
        return "internal_tool"

    return "working_prototype"


def _compute_proof_level(sigs: dict, records: list) -> int:
    """Compute proof level (0-7)."""
    level = 1  # Discovered (we found it)

    # Level 2: Hashed (collateral with hashes exists)
    if records and any(r.get("raw_file_hash") for r in records):
        level = 2

    # Level 3: Clean (has license, gitignore, no env exposure)
    if level >= 2:
        clean_checks = [
            sigs.get("has_license", False),
            sigs.get("has_gitignore", False),
            not sigs.get("has_env_file", True),
        ]
        if sum(clean_checks) >= 2:
            level = 3

    # Level 4: Build-Checked
    if level >= 3:
        build_checks = [
            sigs.get("has_dockerfile", False) or sigs.get("has_vercel", False),
            sigs.get("has_tests", False),
            sigs.get("has_readme", False),
        ]
        if sum(build_checks) >= 2:
            level = 4

    # Level 5: Use-Checked (deployment evidence)
    if level >= 4 and (sigs.get("has_vercel") or sigs.get("has_procfile")):
        level = 5

    return level


def _detect_risks(sigs: dict, records: list) -> list:
    """Detect risk flags."""
    risks = []
    if sigs.get("has_env_file"):
        risks.append("env_file_detected")
    if not sigs.get("has_license"):
        risks.append("no_license")
    if not sigs.get("has_readme"):
        risks.append("no_readme")
    if not sigs.get("has_gitignore"):
        risks.append("no_gitignore")
    if not sigs.get("has_tests"):
        risks.append("no_tests")
    if not sigs.get("has_git"):
        risks.append("no_version_control")
    if sigs.get("total_src", 0) == 0 and sigs.get("collateral_count", 0) == 0:
        risks.append("no_source_code")
    return risks


def _compute_quality(sigs: dict, records: list) -> dict:
    """Compute quality sub-scores (0-100)."""
    # Engineering substance
    src = sigs.get("total_src", 0)
    eng = min(100, src * 3)
    if sigs.get("has_tests"): eng = min(100, eng + 15)
    if sigs.get("has_ci"): eng = min(100, eng + 10)

    # Documentation
    doc = 0
    if sigs.get("has_readme"): doc += 40
    if sigs.get("has_license"): doc += 25
    if sigs.get("has_gitignore"): doc += 10
    if sigs.get("has_dockerfile"): doc += 15
    if sigs.get("has_ci"): doc += 10

    # Security cleanliness
    sec = 80
    if sigs.get("has_env_file"): sec -= 30
    if not sigs.get("has_gitignore"): sec -= 20
    if sigs.get("has_license"): sec += 10
    sec = max(0, min(100, sec))

    # Deployment readiness
    dep = 0
    if sigs.get("has_dockerfile"): dep += 30
    if sigs.get("has_vercel"): dep += 25
    if sigs.get("has_procfile"): dep += 20
    if sigs.get("has_ci"): dep += 15
    if sigs.get("has_package_json") or sigs.get("has_requirements"): dep += 10

    # Collateral completeness
    coll = 0
    if records:
        ws = set(r.get("workstream", "") for r in records)
        coll = min(100, len(ws) * 13)
        if all(r.get("raw_file_hash") for r in records): coll = min(100, coll + 10)
        if all(r.get("solana_tx_short") for r in records): coll = min(100, coll + 10)

    return {
        "engineering": min(100, eng),
        "documentation": min(100, doc),
        "security": sec,
        "deployment": min(100, dep),
        "collateral": coll,
    }


def _extract_workstreams(records: list) -> list:
    ws = Counter()
    for r in records:
        w = r.get("workstream", "Unknown")
        ws[w] += 1
    return [{"workstream": k, "files": v} for k, v in ws.most_common()]
