"""
CollateralOps — GitHub integration for repo metadata enrichment (T10).
Fetches stars, forks, contributors, issues, and language stats from GitHub API.
"""
import os
from typing import Optional, Dict, Any

import httpx

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


def _extract_owner_repo(repo_url: str) -> Optional[tuple]:
    """Extract (owner, repo) from https://github.com/owner/repo or owner/repo."""
    repo_url = repo_url.rstrip("/")
    if repo_url.startswith("https://github.com/"):
        parts = repo_url.replace("https://github.com/", "").split("/")
    elif repo_url.startswith("github.com/"):
        parts = repo_url.replace("github.com/", "").split("/")
    else:
        parts = repo_url.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None


async def fetch_repo_metadata(repo_url: str) -> Dict[str, Any]:
    """Fetch GitHub metadata for a repo. Returns empty dict on failure."""
    pair = _extract_owner_repo(repo_url)
    if not pair:
        return {}
    owner, repo = pair
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        try:
            r = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if r.status_code != 200:
                return {"error": f"GitHub API {r.status_code}", "url": repo_url}
            data = r.json()
            return {
                "url": repo_url,
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "watchers": data.get("watchers_count", 0),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "pushed_at": data.get("pushed_at"),
                "size_kb": data.get("size", 0),
                "language": data.get("language"),
                "license": data.get("license", {}).get("spdx_id") if data.get("license") else None,
                "topics": data.get("topics", []),
                "network_count": data.get("network_count", 0),
                "subscribers_count": data.get("subscribers_count", 0),
            }
        except Exception as e:
            return {"error": str(e), "url": repo_url}


async def fetch_contributors(repo_url: str) -> list:
    """Fetch top contributors for IP ownership verification."""
    pair = _extract_owner_repo(repo_url)
    if not pair:
        return []
    owner, repo = pair
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        try:
            r = await client.get(f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=10")
            if r.status_code != 200:
                return []
            return [{"login": c.get("login"), "contributions": c.get("contributions", 0)} for c in r.json()]
        except Exception:
            return []


async def fetch_languages(repo_url: str) -> Dict[str, int]:
    """Fetch language breakdown."""
    pair = _extract_owner_repo(repo_url)
    if not pair:
        return {}
    owner, repo = pair
    async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
        try:
            r = await client.get(f"https://api.github.com/repos/{owner}/{repo}/languages")
            if r.status_code != 200:
                return {}
            return r.json()
        except Exception:
            return {}
