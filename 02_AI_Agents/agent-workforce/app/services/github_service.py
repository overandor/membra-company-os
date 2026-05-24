import base64
import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import GitHubRepoRequest, GitHubRepoResponse

logger = get_logger("github_service")

class GitHubService:
    BASE = "https://api.github.com"
    def __init__(self):
        self.token = settings.github_token
        self.org = settings.github_org
        self.client = httpx.AsyncClient(timeout=60.0)

    def _headers(self):
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def create_repo(self, req: GitHubRepoRequest) -> GitHubRepoResponse:
        if not self.token:
            return GitHubRepoResponse(repo_url="", clone_url="", created=False)
        try:
            path = f"/orgs/{self.org}/repos" if self.org else "/user/repos"
            payload = {
                "name": req.name,
                "description": req.description or f"Auto-created repo for {req.name}",
                "private": req.private,
                "auto_init": True,
            }
            resp = await self.client.post(f"{self.BASE}{path}", headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            repo_url = data["html_url"]
            clone_url = data["clone_url"]
            if req.readme_content:
                await self._update_readme(req.name, req.readme_content)
            logger.info("repo_created", name=req.name, url=repo_url)
            return GitHubRepoResponse(repo_url=repo_url, clone_url=clone_url, created=True)
        except Exception as e:
            logger.error("repo_creation_failed", name=req.name, error=str(e))
            return GitHubRepoResponse(repo_url="", clone_url="", created=False)

    async def _update_readme(self, repo_name: str, content: str):
        try:
            path = f"{self.BASE}/repos/{self.org or 'user'}/{repo_name}/contents/README.md"
            if self.org:
                path = f"{self.BASE}/repos/{self.org}/{repo_name}/contents/README.md"
            payload = {
                "message": "docs: update README via AgentWorkforce",
                "content": base64.b64encode(content.encode()).decode(),
            }
            resp = await self.client.put(path, headers=self._headers(), json=payload)
            resp.raise_for_status()
        except Exception as e:
            logger.error("readme_update_failed", repo=repo_name, error=str(e))

    async def create_file(self, repo_name: str, path: str, content: str, message: str = "Auto commit via AgentWorkforce"):
        if not self.token:
            return {"status": "skipped"}
        try:
            full_repo = f"{self.org}/{repo_name}" if self.org else repo_name
            url = f"{self.BASE}/repos/{full_repo}/contents/{path}"
            payload = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
            }
            resp = await self.client.put(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            return {"status": "created", "path": path}
        except Exception as e:
            # Try update if exists
            logger.warning("file_create_failed_trying_update", path=path, error=str(e))
            return await self.update_file(repo_name, path, content, message)

    async def update_file(self, repo_name: str, path: str, content: str, message: str):
        try:
            full_repo = f"{self.org}/{repo_name}" if self.org else repo_name
            url = f"{self.BASE}/repos/{full_repo}/contents/{path}"
            # Get SHA first
            r = await self.client.get(url, headers=self._headers())
            if r.status_code != 200:
                return {"status": "error", "detail": r.text}
            sha = r.json()["sha"]
            payload = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "sha": sha,
            }
            resp = await self.client.put(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            return {"status": "updated", "path": path}
        except Exception as e:
            logger.error("file_update_failed", path=path, error=str(e))
            return {"status": "error", "error": str(e)}

    async def create_repo_and_push(self, repo_name: str, files: dict, private: bool = True, description: str = "") -> GitHubRepoResponse:
        repo = await self.create_repo(GitHubRepoRequest(name=repo_name, private=private, description=description))
        if not repo.created:
            return repo
        for path, content in files.items():
            await self.create_file(repo_name, path, content)
        return repo

github_service = GitHubService()
