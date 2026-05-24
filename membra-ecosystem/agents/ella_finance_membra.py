"""MEMBRA Agent: ella.finance.membra
Title: Chief Financial Officer
Department: finance

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class EllaFinanceMembra(BaseAgent):
    AGENT_ID = "ella.finance.membra"
    NAME = "ella"
    DEPARTMENT = "finance"
    TITLE = "Chief Financial Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Chief Financial Officer. Financial planning Investor relations Capital allocation. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Financial planning', 'Investor relations', 'Capital allocation']
    SKILLS: List[str] = ['financial_planning', 'investor_relations', 'capital_allocation', 'board_reporting', ' fundraising_strategy']

    # ─── Job-Specific Skills ───

    async def build_financial_model(self, scenario: str, assumptions: dict) -> dict:
        result = await self.think(f"Build a financial model for scenario '{scenario}'. Assumptions: {assumptions}. Include P&L, cash flow, and balance sheet.")
        return {"financial_model": result}

    async def prepare_board_deck(self, period: str, highlights: list) -> dict:
        result = await self.think(f"Prepare a board presentation for {period} with highlights: {highlights}. Include KPIs, risks, and asks.")
        return {"board_deck": result}

    async def allocate_capital(self, opportunities: list, budget: float) -> dict:
        result = await self.think(f"Allocate ${budget} capital across opportunities: {opportunities}. Prioritize by ROI, risk, and strategic fit.")
        return {"allocation": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
