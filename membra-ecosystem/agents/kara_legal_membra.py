"""MEMBRA Agent: kara.legal.membra
Title: Contract Specialist
Department: legal

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class KaraLegalMembra(BaseAgent):
    AGENT_ID = "kara.legal.membra"
    NAME = "kara"
    DEPARTMENT = "legal"
    TITLE = "Contract Specialist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Contract Specialist. Contract drafting Template management Vendor agreements. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Contract drafting', 'Template management', 'Vendor agreements']
    SKILLS: List[str] = ['contract_drafting', 'template_management', 'vendor_agreement_negotiation', 'clause_library', 'risk_clause_identification']

    # ─── Job-Specific Skills ───

    async def draft_contract(self, agreement_type: str, parties: list, key_terms: dict) -> dict:
        result = await self.think(f"Draft a {agreement_type} between {parties} with key terms: {key_terms}. Include standard clauses and protections.")
        return {"contract_draft": result}

    async def review_vendor_agreement(self, agreement: str, red_flags: list) -> dict:
        result = await self.think(f"Review this vendor agreement: {agreement}. Watch for red flags: {red_flags}. Suggest revisions.")
        return {"review": result}

    async def create_template(self, contract_type: str, variables: list) -> dict:
        result = await self.think(f"Create a contract template for {contract_type} with variables: {variables}. Include fallback positions.")
        return {"template": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
