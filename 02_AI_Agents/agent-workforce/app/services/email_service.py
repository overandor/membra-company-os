import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import EmailRequest

logger = get_logger("email_service")

class EmailService:
    def __init__(self):
        self.sendgrid_key = settings.sendgrid_api_key
        self.from_email = settings.email_from
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send(self, req: EmailRequest) -> dict:
        if not self.sendgrid_key:
            logger.warning("sendgrid_not_configured")
            return {"status": "skipped", "reason": "sendgrid_not_configured"}
        try:
            payload = {
                "personalizations": [{"to": [{"email": req.to}]}],
                "from": {"email": self.from_email},
                "subject": req.subject,
                "content": [],
            }
            if req.html:
                payload["content"].append({"type": "text/html", "value": req.html})
            else:
                payload["content"].append({"type": "text/plain", "value": req.body})
            headers = {"Authorization": f"Bearer {self.sendgrid_key}", "Content-Type": "application/json"}
            resp = await self.client.post("https://api.sendgrid.com/v3/mail/send", headers=headers, json=payload)
            resp.raise_for_status()
            logger.info("email_sent", to=req.to, subject=req.subject, agent_id=req.agent_id)
            return {"status": "sent", "to": req.to, "subject": req.subject}
        except Exception as e:
            logger.error("email_send_failed", to=req.to, error=str(e))
            return {"status": "error", "error": str(e)}

    async def send_agent_result(self, to: str, agent_id: str, result_summary: str, detail_url: Optional[str] = None):
        html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
        <h2>Agent Workforce - Task Complete</h2>
        <p><strong>Agent:</strong> {agent_id}</p>
        <p><strong>Result:</strong></p>
        <pre style="background:#f4f4f4;padding:10px;border-radius:5px;overflow:auto">{result_summary}</pre>
        {f'<p><a href="{detail_url}" style="background:#007bff;color:#fff;padding:10px 15px;text-decoration:none;border-radius:5px">View Details</a></p>' if detail_url else ''}
        <hr/><p style="font-size:12px;color:#666">Powered by AgentWorkforce</p>
        </body></html>
        """
        return await self.send(EmailRequest(to=to, subject=f"Agent {agent_id} Task Complete", body=result_summary, html=html, agent_id=agent_id))

email_service = EmailService()
