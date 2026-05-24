"""MEMBRA Agent: finn.finance.membra
Title: Senior Accountant
Department: finance

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class FinnFinanceMembra(BaseAgent):
    AGENT_ID = "finn.finance.membra"
    NAME = "finn"
    DEPARTMENT = "finance"
    TITLE = "Senior Accountant"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Senior Accountant. Bookkeeping Month-end close Audit prep. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Bookkeeping', 'Month-end close', 'Audit prep']
    SKILLS: List[str] = ['bookkeeping', 'month_end_close', 'audit_preparation', 'gaap_compliance', 'reconciliation']

    # ─── Job-Specific Skills ───

    async def close_month(self, transactions: str, accounts: list) -> dict:
        result = await self.think(f"Plan month-end close for accounts: {accounts}. Transactions: {transactions}. Include checklist and deadlines.")
        return {"close_plan": result}

    async def prepare_audit(self, focus_areas: list, prior_findings: str) -> dict:
        result = await self.think(f"Prepare for audit focusing on: {focus_areas}. Prior findings: {prior_findings}. Include documentation and controls.")
        return {"audit_prep": result}

    async def reconcile_accounts(self, account_pairs: list) -> dict:
        result = await self.think(f"Design reconciliation procedures for: {account_pairs}. Include tolerance thresholds and investigation steps.")
        return {"reconciliation": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
