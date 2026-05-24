"""MEMBRA Agent: gia.finance.membra
Title: FP&A Analyst
Department: finance

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class GiaFinanceMembra(BaseAgent):
    AGENT_ID = "gia.finance.membra"
    NAME = "gia"
    DEPARTMENT = "finance"
    TITLE = "FP&A Analyst"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the FP&A Analyst. Budget modeling Variance analysis Board reporting. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Budget modeling', 'Variance analysis', 'Board reporting']
    SKILLS: List[str] = ['budget_modeling', 'variance_analysis', 'forecasting', 'unit_economics', 'kpi_reporting']

    # ─── Job-Specific Skills ───

    async def build_budget(self, departments: list, fiscal_year: int) -> dict:
        result = await self.think(f"Build a budget model for {departments} for FY{fiscal_year}. Include revenue drivers, cost centers, and headcount.")
        return {"budget_model": result}

    async def analyze_variance(self, actual_vs_budget: str, thresholds: dict) -> dict:
        result = await self.think(f"Analyze variance: {actual_vs_budget}. Thresholds: {thresholds}. Identify root causes and actions.")
        return {"variance_analysis": result}

    async def calculate_unit_economics(self, cohort: str, metrics: list) -> dict:
        result = await self.think(f"Calculate unit economics for {cohort}. Metrics: {metrics}. Include CAC, LTV, payback period, and margin.")
        return {"unit_economics": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
