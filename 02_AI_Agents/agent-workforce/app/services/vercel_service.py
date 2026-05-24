import httpx
from typing import Dict, Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import VercelDeployRequest, VercelDeployResponse

logger = get_logger("vercel_service")

class VercelService:
    BASE = "https://api.vercel.com"
    def __init__(self):
        self.token = settings.vercel_token
        self.team_id = settings.vercel_team_id
        self.client = httpx.AsyncClient(timeout=60.0)

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def _params(self):
        return {"teamId": self.team_id} if self.team_id else {}

    async def create_project(self, name: str, framework: str = "nextjs", env_vars: Optional[Dict[str, str]] = None) -> dict:
        if not self.token:
            return {"status": "skipped", "reason": "vercel_not_configured"}
        try:
            payload = {"name": name, "framework": framework}
            if env_vars:
                payload["env"] = [{"key": k, "value": v, "type": "plain"} for k, v in env_vars.items()]
            resp = await self.client.post(
                f"{self.BASE}/v11/projects",
                headers=self._headers(),
                params=self._params(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("vercel_project_created", name=name, project_id=data.get("id"))
            return {"status": "created", "project_id": data.get("id"), "name": name}
        except Exception as e:
            logger.error("vercel_project_failed", name=name, error=str(e))
            return {"status": "error", "error": str(e)}

    async def deploy_repo(self, req: VercelDeployRequest) -> VercelDeployResponse:
        if not self.token:
            return VercelDeployResponse(project_id="", deployment_url="", status="skipped")
        try:
            # Ensure project exists
            project = await self.create_project(req.project_name, req.framework or "nextjs", req.env_vars)
            project_id = project.get("project_id", req.project_name)
            payload = {
                "name": req.project_name,
                "gitSource": {
                    "type": "github",
                    "repo": req.repo_url.replace("https://github.com/", "").replace(".git", ""),
                    "ref": "main",
                },
            }
            if req.env_vars:
                payload["env"] = [{"key": k, "value": v, "type": "plain"} for k, v in req.env_vars.items()]
            resp = await self.client.post(
                f"{self.BASE}/v13/deployments",
                headers=self._headers(),
                params=self._params(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            url = data.get("url", f"https://{req.project_name}.vercel.app")
            logger.info("vercel_deployment_created", project=req.project_name, url=url)
            return VercelDeployResponse(project_id=project_id, deployment_url=url, status="success")
        except Exception as e:
            logger.error("vercel_deploy_failed", project=req.project_name, error=str(e))
            return VercelDeployResponse(project_id="", deployment_url="", status=f"error: {e}")

    async def list_deployments(self, project_id: str) -> list:
        if not self.token:
            return []
        try:
            resp = await self.client.get(
                f"{self.BASE}/v6/deployments",
                headers=self._headers(),
                params={**self._params(), "projectId": project_id},
            )
            resp.raise_for_status()
            return resp.json().get("deployments", [])
        except Exception as e:
            logger.error("list_deployments_failed", project_id=project_id, error=str(e))
            return []

vercel_service = VercelService()
