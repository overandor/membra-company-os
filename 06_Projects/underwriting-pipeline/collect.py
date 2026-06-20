"""
collect.py — live metric collectors that auto-populate the underwriting input.

Two backends (no more hand-written JSON):
  * local_git_metrics(path)  — scans a real git checkout (commits, SLOC, tests,
    deployable units, authors, tenure) into the underwriting metrics schema.
  * github_repo_metrics(repo) — coarse per-repo metrics from GitHub repo
    metadata (size/language/dates) for portfolio mode where repos aren't cloned.
"""
from __future__ import annotations
import datetime, os, subprocess

CODE_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".cpp", ".hpp",
            ".c", ".h", ".sol", ".swift", ".sh")
VENDOR = ("node_modules/", "/target/", "/.venv/", "site-packages", "/dist/", "/build/")
TODAY = datetime.date(2026, 6, 20)


def _sh(args: list[str], cwd: str) -> str:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return ""


def local_git_metrics(path: str, login: str = "local", followers: int = 0,
                      public_repos: int = 1, primary_authors: int | None = None) -> dict:
    files = [f for f in _sh(["git", "ls-files"], path).splitlines()
             if not any(v in f for v in VENDOR)]
    code_files = [f for f in files if f.endswith(CODE_EXT)]
    sloc, tests = 0, 0
    for f in code_files:
        fp = os.path.join(path, f)
        try:
            with open(fp, "r", errors="ignore") as fh:
                lines = fh.readlines()
        except Exception:
            continue
        sloc += len(lines)
        if f.endswith(".py"):
            tests += sum(1 for ln in lines if ln.lstrip().startswith("def test_"))
    deployable = sum(1 for f in files if os.path.basename(f).lower() == "dockerfile"
                     or os.path.basename(f) == "package.json")
    defs = 0
    for f in code_files:
        if f.endswith(".py"):
            try:
                with open(os.path.join(path, f), errors="ignore") as fh:
                    defs += sum(1 for ln in fh if ln.lstrip().startswith(("def ", "class ")))
            except Exception:
                pass
    dates = _sh(["git", "log", "--all", "--format=%ad", "--date=short"], path).split()
    created = min(dates) if dates else TODAY.isoformat()
    if primary_authors is None:
        primary_authors = max(1, len([l for l in _sh(
            ["git", "shortlog", "-sne", "--all"], path).splitlines() if l.strip()]))
    return {
        "subject": {"login": login, "name": login, "entity": None,
                    "account_created": created, "as_of": TODAY.isoformat()},
        "portfolio": {"public_repos": public_repos, "followers": followers,
                      "following": 0, "total_size_gb": 0, "primary_authors": primary_authors},
        "code": {"portfolio_sloc": sloc, "dedup_factor": 0.60, "implemented_defs": max(defs, 1),
                 "test_functions": tests, "test_files": 0, "deployable_units": deployable,
                 "platforms": 0, "experiments": 0, "ci_workflows": 0,
                 "compiling_ratio": 1.0},
        "commercial": {"recurring_revenue_usd": 0, "users": 0,
                       "ip_assigned_entity": False, "secrets_remediated": True},
    }


def github_repo_metrics(repo: dict, login: str = "overandor", followers: int = 4,
                        account_created: str = "2025-03-13") -> dict:
    """Coarse metrics from GitHub repo metadata (size_kb, language, dates)."""
    size_kb = repo.get("size", 0)
    sloc = int(size_kb * 12)  # rough lines/KB; coarse by design (no clone)
    created = (repo.get("created_at") or account_created)[:10]
    has_app = (repo.get("language") in ("Python", "TypeScript", "JavaScript", "Rust", "Go", "Swift"))
    return {
        "subject": {"login": login, "name": repo.get("name", "repo"), "entity": None,
                    "account_created": created, "as_of": TODAY.isoformat()},
        "portfolio": {"public_repos": 1, "followers": followers, "following": 0,
                      "total_size_gb": size_kb / 1_048_576, "primary_authors": 1},
        "code": {"portfolio_sloc": max(sloc, 200), "dedup_factor": 0.6,
                 "implemented_defs": max(int(sloc / 30), 1), "test_functions": 0,
                 "test_files": 0, "deployable_units": 1 if has_app else 0,
                 "platforms": 0, "experiments": 1, "ci_workflows": 0, "compiling_ratio": 1.0},
        "commercial": {"recurring_revenue_usd": 0, "users": 0,
                       "ip_assigned_entity": False, "secrets_remediated": True},
        "_repo": {"name": repo.get("name"), "language": repo.get("language"), "size_kb": size_kb},
    }
