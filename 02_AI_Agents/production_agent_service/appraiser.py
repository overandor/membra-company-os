#!/usr/bin/env python3
"""
Production Readiness Appraiser
Deterministic, rule-based scoring engine for codebase valuation.
No LLM required — fast, repeatable, auditable.
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


SEVERITY_WEIGHTS = {
    "critical": 0,
    "high": 15,
    "medium": 30,
    "low": 45,
}

SECRET_PATTERNS = [
    (r"api[_\-]?key\s*[=:]\s*['\"\w\-]{16,}", "high", "Hardcoded API key"),
    (r"secret\s*[=:]\s*['\"\w\-]{8,}", "high", "Hardcoded secret"),
    (r"password\s*[=:]\s*['\"][^'\"]{4,}['\"]", "critical", "Hardcoded password"),
    (r"token\s*[=:]\s*['\"\w\-]{20,}", "high", "Hardcoded token"),
    (r"private[_\-]?key\s*[=:]\s*['\"\w\-/+=]{20,}", "critical", "Hardcoded private key"),
    (r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "critical", "Embedded private key PEM"),
    (r"AKIA[0-9A-Z]{16}", "critical", "AWS Access Key ID"),
    (r"ghp_[A-Za-z0-9_]{36}", "critical", "GitHub PAT"),
    (r"sk-[a-zA-Z0-9]{20,}", "high", "OpenAI/Stripe secret key pattern"),
]


@dataclass
class CheckResult:
    name: str
    passed: bool
    score: int  # 0-100
    weight: float
    details: List[str] = field(default_factory=list)


@dataclass
class AppraisalReport:
    project_name: str
    project_path: str
    project_type: str
    appraised_at: str
    overall_score: int
    monetization_score: int
    readiness_grade: str
    checks: List[CheckResult]
    secrets: List[Dict[str, Any]]
    recommendations: List[str]
    estimated_value_usd: int
    action_plan: List[str]


def _scan_for_secrets(root: Path, max_files: int = 500) -> List[Dict]:
    found = []
    compiled = [(re.compile(p, re.IGNORECASE), sev, desc) for p, sev, desc in SECRET_PATTERNS]
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {
            ".git", "node_modules", "__pycache__", ".venv", "venv", "target", "dist", "build"
        }]
        for f in filenames:
            if count >= max_files:
                break
            if not f.endswith((".py", ".js", ".ts", ".tsx", ".rs", ".go", ".sol", ".yaml", ".yml", ".json", ".env", ".toml", ".sh", ".md")):
                continue
            fp = Path(dirpath) / f
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
                count += 1
                for pattern, severity, description in compiled:
                    for m in pattern.finditer(text):
                        snippet = text[max(0, m.start()-20):m.end()+20].replace("\n", " ")
                        found.append({
                            "file": str(fp.relative_to(root)),
                            "severity": severity,
                            "description": description,
                            "snippet": snippet[:100],
                        })
            except Exception:
                continue
    # Deduplicate by file+description
    seen = set()
    unique = []
    for s in found:
        key = (s["file"], s["description"])
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def _has_file(root: Path, name: str) -> bool:
    return (root / name).is_file()


def _has_dir(root: Path, name: str) -> bool:
    return (root / name).is_dir()


def _read_first_lines(path: Path, n: int = 30) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return "".join(f.readline() for _ in range(n))
    except Exception:
        return ""


def _git_status(root: Path) -> Dict[str, Any]:
    result = {"has_git": False, "has_remote": False, "uncommitted": False, "branch": "", "commits_behind": 0}
    git_dir = root / ".git"
    if not git_dir.exists():
        return result
    result["has_git"] = True
    try:
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, timeout=5)
        if branch.returncode == 0:
            result["branch"] = branch.stdout.strip()
        remote = subprocess.run(["git", "remote", "-v"], cwd=root, capture_output=True, text=True, timeout=5)
        result["has_remote"] = len(remote.stdout.strip()) > 0
        status = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=5)
        result["uncommitted"] = len(status.stdout.strip()) > 0
        rev = subprocess.run(["git", "rev-list", "--count", "--left-only", "@{u}...HEAD"], cwd=root, capture_output=True, text=True, timeout=5)
        if rev.returncode == 0:
            try:
                result["commits_behind"] = int(rev.stdout.strip())
            except ValueError:
                pass
    except Exception:
        pass
    return result


def _check_ci(root: Path) -> Dict[str, Any]:
    ci = {"has_ci": False, "ci_platform": "", "test_job": False, "build_job": False, "lint_job": False}
    gh = root / ".github" / "workflows"
    if gh.is_dir():
        ci["has_ci"] = True
        ci["ci_platform"] = "github_actions"
        for wf in gh.glob("*.yml"):
            text = wf.read_text(encoding="utf-8", errors="ignore").lower()
            if "test" in text:
                ci["test_job"] = True
            if "build" in text or "compile" in text:
                ci["build_job"] = True
            if "lint" in text or "typecheck" in text or "mypy" in text or "eslint" in text:
                ci["lint_job"] = True
    gl = root / ".gitlab-ci.yml"
    if gl.is_file():
        ci["has_ci"] = True
        ci["ci_platform"] = "gitlab_ci"
        text = gl.read_text(encoding="utf-8", errors="ignore").lower()
        ci["test_job"] = "test" in text
        ci["build_job"] = "build" in text
        ci["lint_job"] = "lint" in text
    return ci


def _check_tests(root: Path, project_type: str) -> Dict[str, Any]:
    result = {"has_tests": False, "test_count": 0, "coverage": False}
    test_dirs = ["tests", "test", "__tests__", "spec", "specs"]
    for td in test_dirs:
        p = root / td
        if p.is_dir():
            result["has_tests"] = True
            result["test_count"] += len(list(p.rglob("*")))
    # Coverage config
    result["coverage"] = any(_has_file(root, f) for f in [".coveragerc", "codecov.yml", "coverage.json"])
    if project_type == "nodejs" and (root / "package.json").is_file():
        pkg = json.loads((root / "package.json").read_text())
        scripts = pkg.get("scripts", {})
        if any("test" in k for k in scripts):
            result["has_tests"] = True
    return result


def _check_docs(root: Path) -> Dict[str, Any]:
    result = {"has_readme": False, "readme_length": 0, "has_changelog": False, "has_license": False, "has_contributing": False}
    for name in ["README.md", "README", "readme.md", "Readme.md"]:
        p = root / name
        if p.is_file():
            result["has_readme"] = True
            result["readme_length"] = len(p.read_text())
            break
    result["has_changelog"] = any(_has_file(root, f) for f in ["CHANGELOG.md", "CHANGELOG", "HISTORY.md"])
    result["has_license"] = any(_has_file(root, f) for f in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"])
    result["has_contributing"] = any(_has_file(root, f) for f in ["CONTRIBUTING.md", "CONTRIBUTING"])
    return result


def _check_dependencies(root: Path, project_type: str) -> Dict[str, Any]:
    result = {"has_lockfile": False, "has_requirements": False, "outdated_risk": "unknown"}
    lockfiles = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock", "go.sum", "Pipfile.lock"]
    if any(_has_file(root, f) for f in lockfiles):
        result["has_lockfile"] = True
    if project_type == "python":
        result["has_requirements"] = any(_has_file(root, f) for f in ["requirements.txt", "Pipfile", "pyproject.toml"])
    if project_type == "nodejs":
        result["has_requirements"] = _has_file(root, "package.json")
    return result


def appraise_project(project_root: Path, project_type: str = "unknown") -> AppraisalReport:
    root = Path(project_root).expanduser().resolve()
    name = root.name

    secrets = _scan_for_secrets(root)
    git_info = _git_status(root)
    ci_info = _check_ci(root)
    test_info = _check_tests(root, project_type)
    doc_info = _check_docs(root)
    dep_info = _check_dependencies(root, project_type)

    checks: List[CheckResult] = []

    # 1. Secrets & Security (weight 25)
    secret_score = 100
    if secrets:
        worst = max((SEVERITY_WEIGHTS.get(s["severity"], 0) for s in secrets), default=100)
        secret_score = worst
    checks.append(CheckResult("security_secrets", secret_score == 100, secret_score, 25.0,
                              details=[f"{s['severity']}: {s['description']} in {s['file']}" for s in secrets[:5]]))

    # 2. Version Control (weight 10)
    vc_score = 0
    if git_info["has_git"]:
        vc_score += 40
    if git_info["has_remote"]:
        vc_score += 30
    if not git_info["uncommitted"]:
        vc_score += 30
    checks.append(CheckResult("version_control", git_info["has_git"], vc_score, 10.0,
                              details=[f"git={git_info['has_git']}, remote={git_info['has_remote']}, clean={not git_info['uncommitted']}"]))

    # 3. CI/CD (weight 15)
    ci_score = 0
    if ci_info["has_ci"]:
        ci_score += 40
    if ci_info["test_job"]:
        ci_score += 30
    if ci_info["build_job"]:
        ci_score += 20
    if ci_info["lint_job"]:
        ci_score += 10
    checks.append(CheckResult("ci_cd", ci_info["has_ci"], ci_score, 15.0,
                              details=[f"platform={ci_info['ci_platform']}, test={ci_info['test_job']}, build={ci_info['build_job']}, lint={ci_info['lint_job']}"]))

    # 4. Testing (weight 15)
    test_score = 0
    if test_info["has_tests"]:
        test_score += 60
        if test_info["test_count"] > 5:
            test_score += 20
        if test_info["coverage"]:
            test_score += 20
    checks.append(CheckResult("testing", test_info["has_tests"], test_score, 15.0,
                              details=[f"tests={test_info['has_tests']}, count≈{test_info['test_count']}, coverage={test_info['coverage']}"]))

    # 5. Documentation (weight 10)
    doc_score = 0
    if doc_info["has_readme"]:
        doc_score += 40
        if doc_info["readme_length"] > 500:
            doc_score += 20
        if doc_info["readme_length"] > 1500:
            doc_score += 10
    if doc_info["has_changelog"]:
        doc_score += 10
    if doc_info["has_license"]:
        doc_score += 10
    if doc_info["has_contributing"]:
        doc_score += 10
    checks.append(CheckResult("documentation", doc_info["has_readme"], doc_score, 10.0,
                              details=[f"readme={doc_info['has_readme']}({doc_info['readme_length']} chars), changelog={doc_info['has_changelog']}, license={doc_info['has_license']}, contributing={doc_info['has_contributing']}"]))

    # 6. Dependency Management (weight 10)
    dep_score = 0
    if dep_info["has_requirements"]:
        dep_score += 50
    if dep_info["has_lockfile"]:
        dep_score += 50
    checks.append(CheckResult("dependencies", dep_info["has_requirements"], dep_score, 10.0,
                              details=[f"requirements={dep_info['has_requirements']}, lockfile={dep_info['has_lockfile']}"]))

    # 7. Deployment Artifacts (weight 10)
    deploy_score = 0
    if _has_file(root, "Dockerfile") or _has_file(root, "docker-compose.yml") or _has_file(root, "docker-compose.yaml"):
        deploy_score += 50
    if _has_file(root, "netlify.toml") or _has_file(root, "vercel.json") or _has_file(root, "render.yaml") or _has_file(root, "fly.toml"):
        deploy_score += 30
    if _has_file(root, "Dockerfile") and ci_info["build_job"]:
        deploy_score += 20
    checks.append(CheckResult("deployment", deploy_score > 0, deploy_score, 10.0,
                              details=[f"docker={_has_file(root, 'Dockerfile')}, deploy_config={deploy_score > 0}"]))

    # 8. Code Quality Signals (weight 5)
    quality_score = 100
    quality_issues = []
    # Check for common anti-patterns in first few files
    if (root / "package.json").is_file():
        pkg_text = _read_first_lines(root / "package.json")
        if "eslint" not in pkg_text.lower() and project_type == "nodejs":
            quality_score -= 20
            quality_issues.append("No ESLint configured")
    if (root / "pyproject.toml").is_file():
        pyproj = _read_first_lines(root / "pyproject.toml")
        if "ruff" not in pyproj and "black" not in pyproj and "flake8" not in pyproj:
            quality_score -= 20
            quality_issues.append("No Python linter configured")
    checks.append(CheckResult("code_quality", quality_score == 100, quality_score, 5.0, details=quality_issues))

    # Compute weighted overall score
    total_weight = sum(c.weight for c in checks)
    weighted_sum = sum(c.score * c.weight for c in checks)
    overall = round(weighted_sum / total_weight) if total_weight > 0 else 0

    # Monetization score = overall * readiness modifier
    readiness = "A" if overall >= 90 else "B" if overall >= 75 else "C" if overall >= 60 else "D" if overall >= 45 else "F"
    monetization = round(overall * (1.2 if readiness == "A" else 1.0 if readiness == "B" else 0.8 if readiness == "C" else 0.5 if readiness == "D" else 0.2))
    monetization = min(100, monetization)

    # Estimated value: simplistic model based on project type + score
    base_values = {"rust": 80000, "solana": 120000, "python": 40000, "nodejs": 50000, "go": 70000, "cpp": 60000, "jvm": 75000}
    base = 10000
    for pt, val in base_values.items():
        if pt in project_type:
            base = val
            break
    estimated_value = round(base * (monetization / 100))

    # Recommendations
    recommendations = []
    if secrets:
        recommendations.append("URGENT: Remove hardcoded secrets and use environment variables or a vault.")
    if not git_info["has_git"]:
        recommendations.append("Initialize git repository for version control.")
    if not git_info["has_remote"]:
        recommendations.append("Push to a remote repository (GitHub/GitLab) for backup and collaboration.")
    if git_info["uncommitted"]:
        recommendations.append("Commit or stash uncommitted changes.")
    if not ci_info["has_ci"]:
        recommendations.append("Add CI/CD pipeline (GitHub Actions/GitLab CI) for automated testing and deployment.")
    if not ci_info["test_job"]:
        recommendations.append("Add automated test jobs to CI pipeline.")
    if not ci_info["lint_job"]:
        recommendations.append("Add lint/typecheck jobs to CI pipeline.")
    if not test_info["has_tests"]:
        recommendations.append("Add unit/integration tests.")
    if not doc_info["has_readme"]:
        recommendations.append("Write a comprehensive README with setup instructions.")
    if not doc_info["has_license"]:
        recommendations.append("Add a LICENSE file.")
    if not dep_info["has_lockfile"]:
        recommendations.append("Add a lockfile for reproducible builds.")
    if not _has_file(root, "Dockerfile"):
        recommendations.append("Add Dockerfile or docker-compose for containerized deployment.")

    action_plan = []
    if secrets:
        action_plan.append("1. Remove secrets and rotate exposed credentials")
    if not git_info["has_remote"]:
        action_plan.append("2. Push repository to GitHub/GitLab")
    if not ci_info["has_ci"]:
        action_plan.append("3. Add CI/CD workflow")
    if not test_info["has_tests"]:
        action_plan.append("4. Write core unit tests")
    if not doc_info["has_readme"]:
        action_plan.append("5. Write README and LICENSE")
    if not _has_file(root, "Dockerfile"):
        action_plan.append("6. Add Dockerfile")

    return AppraisalReport(
        project_name=name,
        project_path=str(root),
        project_type=project_type,
        appraised_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        overall_score=overall,
        monetization_score=monetization,
        readiness_grade=readiness,
        checks=checks,
        secrets=secrets,
        recommendations=recommendations,
        estimated_value_usd=estimated_value,
        action_plan=action_plan,
    )


def report_to_dict(report: AppraisalReport) -> Dict[str, Any]:
    return {
        "project_name": report.project_name,
        "project_path": report.project_path,
        "project_type": report.project_type,
        "appraised_at": report.appraised_at,
        "overall_score": report.overall_score,
        "monetization_score": report.monetization_score,
        "readiness_grade": report.readiness_grade,
        "estimated_value_usd": report.estimated_value_usd,
        "checks": [asdict(c) for c in report.checks],
        "secrets": report.secrets,
        "recommendations": report.recommendations,
        "action_plan": report.action_plan,
    }


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/Users/alep/Downloads/production_agent_service")
    r = appraise_project(target, "python")
    print(json.dumps(report_to_dict(r), indent=2, default=str))
