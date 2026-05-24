"""MEMBRA CompanyOS — LLM Concierge service.
Uses Groq/OpenAI when keys exist. Falls back to deterministic response when no provider.
Never fakes records. Never promises income. Always maps to concrete MEMBRA actions.
"""
import os
from typing import Optional, Dict, Any, List
import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.orchestration import OrchestrationService

settings = get_settings()
logger = get_logger(__name__)


class LLMConciergeService:
    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = OrchestrationService(db)

    async def chat(self, message: str, user_wallet: Optional[str] = None,
                   user_id: Optional[str] = None, company_id: Optional[str] = None,
                   chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        # Try LLM if configured
        llm_response = None
        if settings.GROQ_API_KEY:
            llm_response = await self._call_groq(message, chat_history)
        elif settings.OPENAI_API_KEY:
            llm_response = await self._call_openai(message, chat_history)

        if llm_response:
            # Parse LLM response for MEMBRA actions
            actions = self._extract_actions(llm_response)
            if actions.get("orchestrate"):
                result = self.orchestrator.orchestrate(message, user_wallet, user_id, company_id)
                return {
                    "reply": llm_response,
                    "actions_taken": ["orchestration"],
                    "orchestration_result": result,
                    "provider": settings.DEFAULT_LLM_PROVIDER,
                    "disclaimer": "AI structured your intent. Human confirmation required for real-world execution.",
                }
            return {
                "reply": llm_response,
                "actions_taken": actions.get("actions", []),
                "provider": settings.DEFAULT_LLM_PROVIDER,
                "disclaimer": "AI recommendation only. No guaranteed outcomes.",
            }

        # Deterministic fallback
        return self._deterministic_response(message, user_wallet, user_id, company_id)

    async def _call_groq(self, message: str, history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        try:
            system_prompt = self._system_prompt()
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": message})

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": settings.DEFAULT_LLM_MODEL,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 1024,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("groq_error", error=str(e))
            return None

    async def _call_openai(self, message: str, history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        try:
            system_prompt = self._system_prompt()
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": message})

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o",
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 1024,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("openai_error", error=str(e))
            return None

    def _system_prompt(self) -> str:
        return """You are the MEMBRA Concierge, an AI operating within a company-building orchestration system.
Your role is to understand human intent and map it to concrete MEMBRA actions.

RULES:
1. NEVER promise income, profit, or guaranteed returns.
2. NEVER create fake payment records or pretend money moved.
3. ALWAYS recommend human confirmation for real-world execution.
4. ALWAYS explain what MEMBRA will do (structure tasks, assign agents, create jobs, request governance approval).
5. If the user mentions physical assets (window, car, apartment, tool, wearable), explain how WorldBridge registers them.
6. If the user mentions work, tasks, or help, explain how JobOS creates bounties and work orders.
7. If the user mentions tracking or KPIs, explain how CompanyOS records metrics.
8. Be concise but thorough. Use structured bullet points.

AVAILABLE ACTIONS:
- orchestrate: Convert intent into tasks, jobs, and governance gates
- register_asset: Add a real-world asset to WorldBridge
- create_listing: Make an asset visible on the marketplace
- create_job: Post work to the local economy
- request_approval: Send a governance gate for human review
- record_kpi: Log a company metric

RESPOND IN THIS FORMAT:
1. Acknowledge the intent
2. Identify assets/capabilities mentioned
3. Propose MEMBRA actions
4. List required confirmations
5. Add disclaimer: "This is an AI recommendation. Real-world execution requires proof and human confirmation."
"""

    def _extract_actions(self, llm_text: str) -> Dict[str, Any]:
        actions = []
        text = llm_text.lower()
        if any(w in text for w in ["orchestrate", "task", "workflow", "objective", "break down"]):
            actions.append("orchestrate")
        if any(w in text for w in ["asset", "register", "window", "car", "apartment", "tool", "wearable"]):
            actions.append("register_asset")
        if any(w in text for w in ["listing", "marketplace", "sell", "rent", "ad"]):
            actions.append("create_listing")
        if any(w in text for w in ["job", "bounty", "work order", "hire", "assign"]):
            actions.append("create_job")
        if any(w in text for w in ["approve", "confirm", "governance", "consent"]):
            actions.append("request_approval")
        if any(w in text for w in ["kpi", "metric", "track", "measure"]):
            actions.append("record_kpi")
        return {"actions": actions, "orchestrate": "orchestrate" in actions}

    def _deterministic_response(self, message: str, user_wallet: Optional[str],
                                user_id: Optional[str], company_id: Optional[str]) -> Dict[str, Any]:
        msg = message.lower()
        result = None

        if any(w in msg for w in ["window", "car", "apartment", "tool", "wearable", "vehicle", "drill"]):
            result = self.orchestrator.orchestrate(message, user_wallet, user_id, company_id)
            reply = (
                f"MEMBRA detected physical assets in your message.\n\n"
                f"**Actions Taken:**\n"
                f"- Created {len(result['objectives'])} objectives\n"
                f"- Created {len(result['tasks'])} tasks\n"
                f"- Created {len(result['jobs'])} jobs\n"
                f"- Created {len(result['gates'])} governance gates\n\n"
                f"**Next Steps:**\n"
                f"1. Submit proof of ownership for your assets\n"
                f"2. Approve marketplace listings via governance gates\n"
                f"3. Monitor task board for assignments\n\n"
                f"**Proof Hash:** `{result['proof_hash']}`\n\n"
                f"_Disclaimer: This is an AI recommendation. Real-world execution requires proof and human confirmation._"
            )
        elif any(w in msg for w in ["task", "job", "work", "help", "bounty"]):
            result = self.orchestrator.orchestrate(message, user_wallet, user_id, company_id)
            reply = (
                f"MEMBRA structured your work request.\n\n"
                f"**Actions Taken:**\n"
                f"- Created {len(result['objectives'])} objectives\n"
                f"- Created {len(result['tasks'])} tasks\n"
                f"- Created {len(result['jobs'])} jobs\n\n"
                f"**Next Steps:**\n"
                f"1. Review job postings in the dashboard\n"
                f"2. Assign workers or agents\n"
                f"3. Set up payout eligibility when work completes\n\n"
                f"**Proof Hash:** `{result['proof_hash']}`\n\n"
                f"_Disclaimer: This is an AI recommendation. Real-world execution requires proof and human confirmation._"
            )
        else:
            reply = (
                f"MEMBRA Concierge (deterministic mode — no LLM key configured).\n\n"
                f"**I understand:** {message[:200]}\n\n"
                f"**I can help you:**\n"
                f"- Register physical assets (window, car, tool, apartment, wearable)\n"
                f"- Create marketplace listings and ad inventory\n"
                f"- Post jobs and bounties to the local economy\n"
                f"- Track KPIs and company metrics\n"
                f"- Set up governance approvals and consent flows\n\n"
                f"**To proceed:** Describe what you have and what you want to turn it into.\n\n"
                f"_Disclaimer: AI recommendation only. No guaranteed outcomes. Real-world execution requires proof and human confirmation._"
            )

        return {
            "reply": reply,
            "actions_taken": ["deterministic_fallback"],
            "orchestration_result": result,
            "provider": "deterministic",
            "disclaimer": "No LLM provider configured. Using rule-based intent matching. Set GROQ_API_KEY or OPENAI_API_KEY for richer responses.",
        }
