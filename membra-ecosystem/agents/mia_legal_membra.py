"""MEMBRA Agent: mia.legal.membra
Title: IP Counsel
Department: legal

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class MiaLegalMembra(BaseAgent):
    AGENT_ID = "mia.legal.membra"
    NAME = "mia"
    DEPARTMENT = "legal"
    TITLE = "IP Counsel"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the IP Counsel. Patent strategy Trademark protection IP licensing. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Patent strategy', 'Trademark protection', 'IP licensing']
    SKILLS: List[str] = ['patent_strategy', 'trademark_protection', 'ip_licensing', 'prior_art_search', 'ip_portfolio_management']

    # ─── Job-Specific Skills ───

    async def evaluate_patent(self, invention: str, prior_art: str) -> dict:
        result = await self.think(f"Evaluate patentability of invention: {invention}. Prior art: {prior_art}. Assess novelty, inventive step, and scope.")
        return {"patent_evaluation": result}

    async def protect_trademark(self, mark: str, classes: list) -> dict:
        result = await self.think(f"Develop trademark protection strategy for '{mark}' in classes: {classes}. Include registration and monitoring.")
        return {"trademark_strategy": result}

    async def negotiate_ip_license(self, ip_asset: str, licensee: str) -> dict:
        result = await self.think(f"Negotiate IP license for '{ip_asset}' with {licensee}. Include scope, royalties, field of use, and termination.")
        return {"license_terms": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
