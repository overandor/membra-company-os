"""MEMBRA Agent: hank.finance.membra
Title: Treasury Manager
Department: finance

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class HankFinanceMembra(BaseAgent):
    AGENT_ID = "hank.finance.membra"
    NAME = "hank"
    DEPARTMENT = "finance"
    TITLE = "Treasury Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Treasury Manager. Cash management FX risk Investment policy. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Cash management', 'FX risk', 'Investment policy']
    SKILLS: List[str] = ['cash_management', 'fx_hedging', 'investment_policy', 'liquidity_planning', 'bank_relationship_management']

    # ─── Job-Specific Skills ───

    async def forecast_cash(self, inflows: str, outflows: str, horizon: str) -> dict:
        result = await self.think(f"Forecast cash flow with inflows: {inflows}, outflows: {outflows}, horizon: {horizon}. Identify peaks and troughs.")
        return {"cash_forecast": result}

    async def hedge_fx(self, exposures: list, risk_tolerance: float) -> dict:
        result = await self.think(f"Design FX hedging for exposures: {exposures}. Risk tolerance: {risk_tolerance}. Include instruments and costs.")
        return {"hedging_strategy": result}

    async def create_investment_policy(self, liquidity_needs: str, risk_profile: str) -> dict:
        result = await self.think(f"Create an investment policy for liquidity needs: {liquidity_needs} with risk profile: {risk_profile}. Include approved instruments.")
        return {"investment_policy": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
