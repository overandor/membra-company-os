"""MEMBRA Agent: iris.finance.membra
Title: Tax Strategist
Department: finance

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class IrisFinanceMembra(BaseAgent):
    AGENT_ID = "iris.finance.membra"
    NAME = "iris"
    DEPARTMENT = "finance"
    TITLE = "Tax Strategist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Tax Strategist. Tax planning Compliance filing Transfer pricing. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Tax planning', 'Compliance filing', 'Transfer pricing']
    SKILLS: List[str] = ['tax_planning', 'compliance_filing', 'transfer_pricing', 'tax_optimization', 'international_tax']

    # ─── Job-Specific Skills ───

    async def optimize_tax_structure(self, entities: list, jurisdictions: list) -> dict:
        result = await self.think(f"Optimize tax structure for entities: {entities} in jurisdictions: {jurisdictions}. Include withholding and treaty benefits.")
        return {"tax_optimization": result}

    async def prepare_compliance(self, jurisdiction: str, filing_type: str) -> dict:
        result = await self.think(f"Prepare {filing_type} compliance filing for {jurisdiction}. Include deadlines, supporting docs, and calculations.")
        return {"compliance_filing": result}

    async def design_transfer_pricing(self, transactions: list, method: str) -> dict:
        result = await self.think(f"Design transfer pricing documentation for transactions: {transactions} using method '{method}'. Include comparables.")
        return {"transfer_pricing": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
