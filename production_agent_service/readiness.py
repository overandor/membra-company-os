#!/usr/bin/env python3
"""
Production Readiness Evaluator
Scores a project on CI/CD, tests, docs, secrets, typing, linting, docker, etc.
"""

import fnmatch
import json
import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


SECRET_PATTERNS = [
    r"api[_\-]?key\s*[=:]\s*['\"\w]+",
    r"private[_\-]?key\s*[=:]\s*['\"\w]+",
    r"secret\s*[=:]\s*['\"\w]+",
    r"password\s*[=:]\s*['\"\w]+",
    r"token\s*[=:]\s*['\"\w]+",
    r"credentials\s*[=:]\s*['\"\w]+",
    r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    r"AKIA[0-9A-Z]{16}",
    r"ghp_[A-Za-z0-9_]{36}",
    r"glpat-[A-Za-z0-9_\-]{20,}",
    r"sk-[a-zA-Z0-9]{20,}",
    r"xox[baprs]-[a-zA-Z0-9]+",
]

COMPILED_SECRET_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SECRET_PATTERNS]


@dataclass
class ReadinessScore:
    project_name: str
    project_root: str
    overall_score: int = 0
    ci_cd: int = 0
    tests: int = 0
    docs: int = 0
    typing: int = 0
    linting: int = 0
    docker: int = 0
    secrets: int = 100
    dependencies: int = 0
    structure: int = 0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


def _has_file(root: Path, *candidates: str) -> bool:
    for c in candidates:
        if (root / c).exists():
            return True
    return False


def _has_dir(root: Path, *candidates: str) -> bool:
    for c in candidates:
        if (root / c).is_dir():
            return True
    return False


def _read_text_limited(path: Path, limit: int = 50000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""


def scan_secrets(root: Path) -> tuple:
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "target")]
        for f in filenames:
            if f.startswith("."):
                continue
            fp = Path(dirpath) / f
            if fp.stat().st_size > 5_000_000:
                continue
            ext = fp.suffix.lower()
            if ext not in (".py", ".ts", ".tsx", ".js", ".jsx", ".sh", ".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt", ".env", ".rs", ".go", ".sol", ""):
                continue
            text = _read_text_limited(fp)
            for pat in COMPILED_SECRET_PATTERNS:
                for m in pat.finditer(text):
                    hits.append(f"{fp.relative_to(root)}: {m.group(0)[:60]}...")
                    if len(hits) >= 50:
                        return hits, 0
    return hits, 100 if not hits else max(0, 100 - len(hits) * 5)


def evaluate_ci_cd(root: Path) -> tuple:
    score = 0
    notes = []
    has_github = _has_dir(root, ".github/workflows")
    has_gitlab = _has_file(root, ".gitlab-ci.yml")
    has_jenkins = _has_file(root, "Jenkinsfile")
    has_circle = _has_file(root, ".circleci/config.yml")
    has_travis = _has_file(root, ".travis.yml")
    has_azure = _has_file(root, "azure-pipelines.yml")

    if has_github:
        score += 40
        notes.append("GitHub Actions detected")
        # Check for common workflows
        wf_dir = root / ".github/workflows"
        if wf_dir.is_dir():
            wfs = list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))
            if wfs:
                score += 10
                notes.append(f"{len(wfs)} workflow files")
            has_test = any("test" in w.name.lower() for w in wfs)
            has_build = any("build" in w.name.lower() for w in wfs)
            has_lint = any(l in w.name.lower() for w in wfs for l in ("lint", "format", "typecheck"))
            if has_test:
                score += 10
            if has_build:
                score += 10
            if has_lint:
                score += 10
    elif has_gitlab:
        score += 35
        notes.append("GitLab CI detected")
    elif has_jenkins:
        score += 30
        notes.append("Jenkins detected")
    elif has_circle or has_travis or has_azure:
        score += 25
        notes.append("Third-party CI detected")
    else:
        notes.append("No CI/CD detected")

    return min(score, 100), notes


def evaluate_tests(root: Path, project_type: str) -> tuple:
    score = 0
    notes = []
    has_test_dir = _has_dir(root, "tests", "test", "__tests__", "spec", "specs")
    has_test_files = any(
        fnmatch.fnmatch(f, "*test*") or fnmatch.fnmatch(f, "*spec*")
        for _, _, files in os.walk(root)
        for f in files
        if f.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".sol"))
    )
    if has_test_dir:
        score += 30
        notes.append("Test directory present")
    if has_test_files:
        score += 30
        notes.append("Test files found")

    # Coverage config
    if _has_file(root, ".coveragerc", "codecov.yml", "sonar-project.properties"):
        score += 10
        notes.append("Coverage config present")

    # Python specific
    if "python" in project_type:
        if _has_file(root, "pytest.ini", "setup.cfg", "pyproject.toml"):
            cfg = _read_text_limited(root / "pyproject.toml") if (root / "pyproject.toml").exists() else ""
            if "pytest" in cfg.lower() or "test" in cfg.lower():
                score += 20
                notes.append("Python test configuration present")

    # JS/TS specific
    if "nodejs" in project_type:
        pkg = root / "package.json"
        if pkg.exists():
            data = json.loads(_read_text_limited(pkg))
            scripts = data.get("scripts", {})
            if any("test" in k for k in scripts):
                score += 20
                notes.append("Test script in package.json")
            if any("coverage" in k for k in scripts):
                score += 10

    return min(score, 100), notes


def evaluate_docs(root: Path) -> tuple:
    score = 0
    notes = []
    has_readme = _has_file(root, "README.md", "README.rst", "README", "readme.md")
    has_changelog = _has_file(root, "CHANGELOG.md", "CHANGELOG", "CHANGES.md", "HISTORY.md")
    has_contributing = _has_file(root, "CONTRIBUTING.md", "CONTRIBUTING")
    has_license = _has_file(root, "LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")

    if has_readme:
        score += 40
        readme = root / "README.md"
        if readme.exists():
            text = _read_text_limited(readme)
            if len(text) > 500:
                score += 10
            if "install" in text.lower() or "usage" in text.lower():
                score += 10
            if "api" in text.lower() or "endpoint" in text.lower():
                score += 10
        notes.append("README present")
    else:
        notes.append("No README found")

    if has_changelog:
        score += 10
        notes.append("Changelog present")
    if has_contributing:
        score += 10
        notes.append("Contributing guide present")
    if has_license:
        score += 10
        notes.append("License present")

    return min(score, 100), notes


def evaluate_typing(root: Path, project_type: str) -> tuple:
    score = 0
    notes = []
    if "python" in project_type:
        if _has_file(root, "pyproject.toml", "setup.cfg", "mypy.ini"):
            cfg = ""
            for f in ("pyproject.toml", "setup.cfg", "mypy.ini"):
                p = root / f
                if p.exists():
                    cfg = _read_text_limited(p)
                    break
            if "mypy" in cfg.lower():
                score += 40
                notes.append("mypy configured")
            if "type" in cfg.lower():
                score += 20
        # Check for type hints in .py files
        py_files = list(root.rglob("*.py"))
        if py_files:
            typed = 0
            for p in py_files[:50]:
                text = _read_text_limited(p, 5000)
                if "-> " in text or "def " in text and ":" in text.split("def ", 1)[-1][:50]:
                    typed += 1
            if typed > len(py_files[:50]) * 0.3:
                score += 30
                notes.append("Type hints present in Python files")
    elif "nodejs" in project_type or "typescript" in project_type:
        if _has_file(root, "tsconfig.json"):
            score += 50
            notes.append("TypeScript configured")
        if _has_file(root, "*.d.ts"):
            score += 20

    return min(score, 100), notes


def evaluate_linting(root: Path, project_type: str) -> tuple:
    score = 0
    notes = []
    if "python" in project_type:
        for tool in ("ruff", "flake8", "pylint", "black", "isort"):
            cfg_files = [f"{tool}.cfg", f".{tool}rc", "pyproject.toml", "setup.cfg"]
            for cf in cfg_files:
                p = root / cf
                if p.exists() and tool in _read_text_limited(p).lower():
                    score += 25
                    notes.append(f"{tool} configured")
                    break
    elif "nodejs" in project_type or "typescript" in project_type:
        pkg = root / "package.json"
        if pkg.exists():
            data = json.loads(_read_text_limited(pkg))
            dev_deps = data.get("devDependencies", {})
            for tool in ("eslint", "prettier", "biome", "standard"):
                if tool in dev_deps:
                    score += 25
                    notes.append(f"{tool} in devDependencies")

    if _has_file(root, ".pre-commit-config.yaml"):
        score += 20
        notes.append("pre-commit configured")

    return min(score, 100), notes


def evaluate_docker(root: Path) -> tuple:
    score = 0
    notes = []
    if _has_file(root, "Dockerfile"):
        score += 50
        notes.append("Dockerfile present")
    if _has_file(root, "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        score += 30
        notes.append("Docker Compose present")
    if _has_file(root, ".dockerignore"):
        score += 20
        notes.append(".dockerignore present")
    return min(score, 100), notes


def evaluate_dependencies(root: Path, project_type: str) -> tuple:
    score = 0
    notes = []
    if "python" in project_type:
        if _has_file(root, "requirements.txt", "Pipfile", "poetry.lock", "pyproject.toml"):
            score += 40
            notes.append("Python dependency file present")
        if _has_file(root, "requirements-dev.txt"):
            score += 20
            notes.append("Dev dependencies separated")
    elif "nodejs" in project_type:
        if _has_file(root, "package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
            score += 40
            notes.append("Lockfile present")
        if _has_file(root, "package.json"):
            score += 20
            notes.append("package.json present")
    elif "rust" in project_type:
        if _has_file(root, "Cargo.lock"):
            score += 40
            notes.append("Cargo.lock present")
        if _has_file(root, "Cargo.toml"):
            score += 20
            notes.append("Cargo.toml present")
    elif "go" in project_type:
        if _has_file(root, "go.sum"):
            score += 40
            notes.append("go.sum present")
        if _has_file(root, "go.mod"):
            score += 20
            notes.append("go.mod present")

    # Check for known vulnerable patterns
    if _has_file(root, "requirements.txt"):
        req = _read_text_limited(root / "requirements.txt")
        if "==" in req:
            score += 10
            notes.append("Pinned versions in requirements.txt")

    return min(score, 100), notes


def evaluate_structure(root: Path) -> tuple:
    score = 0
    notes = []
    dirs = [d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")]
    files = [f.name for f in root.iterdir() if f.is_file()]

    if any(d in dirs for d in ("src", "lib", "app", "source")):
        score += 20
        notes.append("Source directory present")
    if any(d in dirs for d in ("tests", "test", "__tests__", "spec")):
        score += 20
        notes.append("Test directory present")
    if any(d in dirs for d in ("docs", "documentation", "doc")):
        score += 10
        notes.append("Docs directory present")
    if "config" in dirs or "configs" in dirs:
        score += 10
        notes.append("Config directory present")
    if ".gitignore" in files:
        score += 10
        notes.append(".gitignore present")
    if "Makefile" in files or "justfile" in files:
        score += 10
        notes.append("Build automation present")

    return min(score, 100), notes


def evaluate_project(root: Path, name: str, project_type: str) -> ReadinessScore:
    score = ReadinessScore(project_name=name, project_root=str(root))

    score.ci_cd, ci_notes = evaluate_ci_cd(root)
    score.tests, test_notes = evaluate_tests(root, project_type)
    score.docs, doc_notes = evaluate_docs(root)
    score.typing, type_notes = evaluate_typing(root, project_type)
    score.linting, lint_notes = evaluate_linting(root, project_type)
    score.docker, docker_notes = evaluate_docker(root)
    secrets_hits, score.secrets = scan_secrets(root)
    score.dependencies, dep_notes = evaluate_dependencies(root, project_type)
    score.structure, struct_notes = evaluate_structure(root)

    all_notes = ci_notes + test_notes + doc_notes + type_notes + lint_notes + docker_notes + dep_notes + struct_notes
    score.issues = secrets_hits[:10]
    score.recommendations = []

    if score.ci_cd < 40:
        score.recommendations.append("Add CI/CD (GitHub Actions recommended)")
    if score.tests < 40:
        score.recommendations.append("Add tests (pytest, jest, cargo test, etc.)")
    if score.docs < 40:
        score.recommendations.append("Add README with install/usage instructions")
    if score.secrets < 100:
        score.recommendations.append("Remove secrets from repository — use env vars / vault")
    if score.typing < 40:
        score.recommendations.append("Add type checking (mypy, TypeScript, etc.)")
    if score.linting < 40:
        score.recommendations.append("Add linting (ruff/eslint/prettier)")
    if score.docker < 40:
        score.recommendations.append("Add Dockerfile for reproducible deployments")

    weights = {
        "ci_cd": 0.15,
        "tests": 0.15,
        "docs": 0.10,
        "typing": 0.10,
        "linting": 0.10,
        "docker": 0.10,
        "secrets": 0.15,
        "dependencies": 0.05,
        "structure": 0.10,
    }
    score.overall_score = round(
        score.ci_cd * weights["ci_cd"] +
        score.tests * weights["tests"] +
        score.docs * weights["docs"] +
        score.typing * weights["typing"] +
        score.linting * weights["linting"] +
        score.docker * weights["docker"] +
        score.secrets * weights["secrets"] +
        score.dependencies * weights["dependencies"] +
        score.structure * weights["structure"]
    )

    return score


if __name__ == "__main__":
    import sys
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    r = evaluate_project(p, p.name, "unknown")
    print(json.dumps(asdict(r), indent=2))
