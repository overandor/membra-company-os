"""GitHub API scanner for public repo data."""
import hashlib
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx

from app.models import RepoSummary

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
BASE_URL = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "LaunchR-Scanner/1.0",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# In-memory cache for scan results (survives across requests)
_scan_cache: Dict[str, List[RepoSummary]] = {}


class GitHubRateLimitError(Exception):
    pass


class GitHubScanner:
    def __init__(self):
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True)
        self.rate_limited = False
        self.rate_limit_reason = ""

    async def _get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"
        resp = await self.client.get(url, params=params)
        if resp.status_code in (403, 429):
            raise GitHubRateLimitError(
                "GitHub API rate limit exceeded. "
                "Set GITHUB_TOKEN env var on the backend to authenticate. "
                "Get a token at https://github.com/settings/tokens"
            )
        resp.raise_for_status()
        return resp.json()

    def get_cached(self, username: str) -> Optional[List[RepoSummary]]:
        return _scan_cache.get(username)

    def set_cached(self, username: str, repos: List[RepoSummary]):
        _scan_cache[username] = repos

    def clear_cache(self):
        _scan_cache.clear()

    async def get_user_repos(self, username: str, per_page: int = 100) -> List[Dict[str, Any]]:
        repos = []
        page = 1
        while True:
            data = await self._get(f"/users/{username}/repos", {"per_page": per_page, "page": page, "sort": "updated"})
            if not data:
                break
            repos.extend(data)
            if len(data) < per_page:
                break
            page += 1
            if page > 5:  # cap at 500 repos
                break
        return repos

    async def get_repo_languages(self, full_name: str) -> Dict[str, int]:
        try:
            return await self._get(f"/repos/{full_name}/languages")
        except Exception:
            return {}

    async def get_repo_commits(self, full_name: str, since: Optional[str] = None, per_page: int = 100) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        if since:
            params["since"] = since
        try:
            return await self._get(f"/repos/{full_name}/commits", params)
        except Exception:
            return []

    async def get_repo_contributors(self, full_name: str) -> List[Dict[str, Any]]:
        try:
            return await self._get(f"/repos/{full_name}/contributors", {"per_page": 100})
        except Exception:
            return []

    async def get_repo_releases(self, full_name: str) -> List[Dict[str, Any]]:
        try:
            return await self._get(f"/repos/{full_name}/releases", {"per_page": 100})
        except Exception:
            return []

    async def get_repo_content(self, full_name: str, path: str = "") -> List[Dict[str, Any]]:
        try:
            return await self._get(f"/repos/{full_name}/contents/{path}")
        except Exception:
            return []

    async def get_readme(self, full_name: str) -> Optional[str]:
        try:
            data = await self._get(f"/repos/{full_name}/readme")
            import base64
            return base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
        except Exception:
            return None

    def _has_file(self, contents: List[Dict], name_substr: str) -> bool:
        return any(name_substr.lower() in c.get("name", "").lower() for c in contents)

    def _hash_snapshot(self, repo_data: Dict, readme: Optional[str], languages: Dict) -> str:
        payload = f"{repo_data.get('full_name')}:{repo_data.get('pushed_at')}:{repo_data.get('stargazers_count')}:{repo_data.get('size')}:{sorted(languages.keys())}"
        if readme:
            payload += f":{readme[:500]}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    async def scan_repo(self, username: str, repo_data: Dict[str, Any]) -> RepoSummary:
        full_name = repo_data["full_name"]
        languages = await self.get_repo_languages(full_name)
        since = (datetime.utcnow() - timedelta(days=90)).isoformat()
        commits = await self.get_repo_commits(full_name, since=since)
        contributors = await self.get_repo_contributors(full_name)
        releases = await self.get_repo_releases(full_name)
        contents = await self.get_repo_content(full_name)
        readme = await self.get_readme(full_name)

        license_name = None
        if repo_data.get("license"):
            license_name = repo_data["license"].get("spdx_id") or repo_data["license"].get("name")

        return RepoSummary(
            name=repo_data["name"],
            full_name=full_name,
            description=repo_data.get("description") or "",
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            open_issues=repo_data.get("open_issues_count", 0),
            language=repo_data.get("language"),
            languages=languages,
            created_at=repo_data.get("created_at", ""),
            updated_at=repo_data.get("updated_at", ""),
            pushed_at=repo_data.get("pushed_at"),
            size_kb=repo_data.get("size", 0),
            license=license_name,
            has_readme=readme is not None and len(readme) > 50,
            has_tests=self._has_file(contents, "test") or self._has_file(contents, "spec"),
            has_actions=self._has_file(contents, ".github"),
            has_security=self._has_file(contents, "security") or self._has_file(contents, "SECURITY"),
            topics=repo_data.get("topics", []),
            default_branch=repo_data.get("default_branch", "main"),
            commits_90d=len(commits),
            contributors=len(contributors),
            releases=len(releases),
        )

    @staticmethod
    def _generate_demo_repos(username: str) -> List[RepoSummary]:
        """Generate realistic demo repos when GitHub API is rate limited."""
        import random
        random.seed(hash(username) % 2**32)
        languages = ["Python", "TypeScript", "Rust", "Go", "JavaScript"]
        repo_names = [
            f"{username}-core", f"{username}-api", f"{username}-cli",
            f"{username}-web", f"{username}-ml", f"{username}-utils",
            f"{username}-agent", f"{username}-chain", f"{username}-data",
        ]
        results = []
        for i, name in enumerate(repo_names[:random.randint(3, 7)]):
            lang = languages[i % len(languages)]
            stars = random.randint(5, 500)
            results.append(RepoSummary(
                name=name,
                full_name=f"{username}/{name}",
                description=f"Auto-generated demo: {name} project built with {lang}",
                stars=stars,
                forks=random.randint(0, stars // 4),
                open_issues=random.randint(0, 20),
                language=lang,
                languages={lang: random.randint(60, 95), "Other": random.randint(5, 40)},
                created_at="2023-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
                pushed_at="2024-01-01T00:00:00Z",
                size_kb=random.randint(100, 50000),
                license="MIT",
                has_readme=True,
                has_tests=random.random() > 0.3,
                has_actions=random.random() > 0.5,
                has_security=random.random() > 0.7,
                topics=[lang.lower(), "demo"],
                default_branch="main",
                commits_90d=random.randint(5, 100),
                contributors=random.randint(1, 8),
                releases=random.randint(0, 10),
            ))
        return results

    async def scan_user(self, username: str) -> List[RepoSummary]:
        try:
            repos_data = await self.get_user_repos(username)
        except GitHubRateLimitError:
            self.rate_limited = True
            self.rate_limit_reason = "GitHub API rate limit exceeded"
            cached = self.get_cached(username)
            return cached if cached else self._generate_demo_repos(username)

        results = []
        for rd in repos_data:
            if rd.get("fork"):
                continue  # skip forks for appraisal
            try:
                summary = await self.scan_repo(username, rd)
                results.append(summary)
            except GitHubRateLimitError:
                self.rate_limited = True
                self.rate_limit_reason = "GitHub API rate limit exceeded during repo detail scan"
                break
            except Exception:
                continue

        if not self.rate_limited:
            self.set_cached(username, results)
        return results

    async def close(self):
        await self.client.aclose()
