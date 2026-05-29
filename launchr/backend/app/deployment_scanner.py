"""Public deployment detection for known platforms."""
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DeploymentInfo:
    url: str
    platform: str  # vercel, netlify, fly, heroku, render, github_pages
    status: str  # "live", "unknown", "error"
    detected_framework: Optional[str] = None
    response_time_ms: Optional[float] = None
    has_ssl: bool = False
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class DeploymentScanner:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    async def probe(self, url: str) -> DeploymentInfo:
        try:
            import time
            start = time.time()
            resp = await self.client.get(url, headers={"User-Agent": "LaunchR-Probe/1.0"})
            elapsed = (time.time() - start) * 1000

            platform = self._detect_platform(resp.headers, url)
            framework = self._detect_framework(resp.headers, resp.text[:5000])

            return DeploymentInfo(
                url=url,
                platform=platform,
                status="live" if resp.status_code < 400 else "error",
                detected_framework=framework,
                response_time_ms=round(elapsed, 2),
                has_ssl=url.startswith("https"),
                headers=dict(resp.headers),
            )
        except Exception:
            return DeploymentInfo(url=url, platform="unknown", status="error")

    def _detect_platform(self, headers: httpx.Headers, url: str) -> str:
        h = {k.lower(): v for k, v in headers.items()}
        server = h.get("server", "").lower()
        powered = h.get("x-powered-by", "").lower()

        if "vercel" in server or "vercel" in powered:
            return "vercel"
        if "netlify" in server or "netlify" in powered:
            return "netlify"
        if "fly.io" in server or "fly" in server:
            return "fly"
        if "heroku" in server or "heroku" in powered:
            return "heroku"
        if "render" in server:
            return "render"
        if "cloudflare" in server:
            return "cloudflare"
        if "github.io" in url:
            return "github_pages"
        if "readthedocs" in url:
            return "readthedocs"
        return "unknown"

    def _detect_framework(self, headers: httpx.Headers, text: str) -> Optional[str]:
        h = {k.lower(): v for k, v in headers.items()}
        ct = h.get("content-type", "").lower()

        if "next" in text[:2000] or "__NEXT_DATA__" in text:
            return "Next.js"
        if "nuxt" in text[:2000]:
            return "Nuxt.js"
        if "react" in text[:2000]:
            return "React"
        if "vue" in text[:2000]:
            return "Vue"
        if "django" in text[:2000]:
            return "Django"
        if "flask" in text[:2000]:
            return "Flask"
        if "fastapi" in text[:2000]:
            return "FastAPI"
        if "astro" in text[:2000]:
            return "Astro"
        if "svelte" in text[:2000]:
            return "Svelte"
        if ct.startswith("application/json"):
            return "API"
        return None

    async def probe_common_deployments(self, username: str, repo_name: str) -> List[DeploymentInfo]:
        """Probe common deployment URLs for a repo."""
        urls = [
            f"https://{username}.github.io/{repo_name}",
            f"https://{repo_name}.vercel.app",
            f"https://{repo_name}.netlify.app",
            f"https://{repo_name}.fly.dev",
            f"https://{repo_name}.herokuapp.com",
            f"https://{repo_name}.onrender.com",
        ]
        results = []
        for url in urls:
            info = await self.probe(url)
            if info.status == "live":
                results.append(info)
        return results

    async def close(self):
        await self.client.aclose()
