"""MEMBRA Agent: olive.governance.membra
Title: Policy Writer
Department: governance

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class OliveGovernanceMembra(BaseAgent):
    AGENT_ID = "olive.governance.membra"
    NAME = "olive"
    DEPARTMENT = "governance"
    TITLE = "Policy Writer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Policy Writer. Policy drafting Version control Compliance mapping. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Policy drafting', 'Version control', 'Compliance mapping']
    SKILLS: List[str] = ['policy_drafting', 'version_control', 'compliance_framework_mapping', 'policy_training', 'gap_analysis']

    # ─── Job-Specific Skills ───

    async def draft_policy(self, topic: str, scope: str, owner: str) -> dict:
        result = await self.think(f"Draft a policy on '{topic}' with scope: {scope}, owner: {owner}. Include purpose, definitions, requirements, and exceptions.")
        return {"policy_draft": result}

    async def map_compliance(self, policy: str, frameworks: list) -> dict:
        result = await self.think(f"Map policy '{policy}' to compliance frameworks: {frameworks}. Create a control matrix and gap list.")
        return {"compliance_map": result}

    async def train_policy(self, policy_name: str, audience: str) -> dict:
        result = await self.think(f"Create training materials for policy '{policy_name}' targeting {audience}. Include scenarios and assessment.")
        return {"training": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
