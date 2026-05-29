"""Package registry scanner for npm, PyPI, and Cargo/crates.io."""
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class RegistryPackageInfo:
    name: str
    registry: str  # npm, pypi, cargo
    version: str
    downloads: int = 0
    dependents: int = 0
    license: Optional[str] = None
    description: str = ""
    repository_url: Optional[str] = None
    homepage: Optional[str] = None
    author: Optional[str] = None
    keywords: List[str] = None
    last_published: Optional[str] = None
    maintainers: int = 0

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RegistryScanner:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)

    async def scan_npm(self, package_name: str) -> Optional[RegistryPackageInfo]:
        try:
            resp = await self.client.get(f"https://registry.npmjs.org/{package_name}")
            if resp.status_code != 200:
                return None
            data = resp.json()
            latest = data.get("dist-tags", {}).get("latest", "")
            version_data = data.get("versions", {}).get(latest, {})
            downloads = 0
            try:
                dl_resp = await self.client.get(
                    f"https://api.npmjs.org/downloads/point/last-year/{package_name}"
                )
                if dl_resp.status_code == 200:
                    downloads = dl_resp.json().get("downloads", 0)
            except Exception:
                pass
            return PackageInfo(
                name=package_name,
                registry="npm",
                version=latest,
                downloads=downloads,
                license=version_data.get("license"),
                description=data.get("description", ""),
                repository_url=version_data.get("repository", {}).get("url") if isinstance(version_data.get("repository"), dict) else None,
                homepage=data.get("homepage"),
                author=version_data.get("author", {}).get("name") if isinstance(version_data.get("author"), dict) else None,
                keywords=data.get("keywords", []),
                last_published=data.get("time", {}).get(latest),
                maintainers=len(data.get("maintainers", [])),
            )
        except Exception:
            return None

    async def scan_pypi(self, package_name: str) -> Optional[RegistryPackageInfo]:
        try:
            resp = await self.client.get(f"https://pypi.org/pypi/{package_name}/json")
            if resp.status_code != 200:
                return None
            data = resp.json()
            info = data.get("info", {})
            return RegistryPackageInfo(
                name=package_name,
                registry="pypi",
                version=info.get("version", ""),
                downloads=0,  # PyPI doesn't expose downloads easily
                license=info.get("license"),
                description=info.get("summary", ""),
                repository_url=info.get("project_urls", {}).get("Source") if isinstance(info.get("project_urls"), dict) else None,
                homepage=info.get("home_page"),
                author=info.get("author"),
                keywords=[k.strip() for k in info.get("keywords", "").split(",") if k.strip()],
                last_published=None,
                maintainers=len(info.get("maintainers", [])),
            )
        except Exception:
            return None

    async def scan_cargo(self, crate_name: str) -> Optional[RegistryPackageInfo]:
        try:
            resp = await self.client.get(f"https://crates.io/api/v1/crates/{crate_name}")
            if resp.status_code != 200:
                return None
            data = resp.json()
            crate = data.get("crate", {})
            return RegistryPackageInfo(
                name=crate_name,
                registry="cargo",
                version=crate.get("newest_version", ""),
                downloads=crate.get("downloads", 0),
                license=None,
                description=crate.get("description", ""),
                repository_url=crate.get("repository"),
                homepage=crate.get("homepage"),
                author=None,
                keywords=[k.get("id") for k in data.get("categories", [])],
                last_published=crate.get("updated_at"),
                maintainers=0,
            )
        except Exception:
            return None

    async def close(self):
        await self.client.aclose()
