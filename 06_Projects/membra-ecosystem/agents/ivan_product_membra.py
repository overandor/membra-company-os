"""MEMBRA Agent: ivan.product.membra
Title: Technical Product Manager
Department: product

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class IvanProductMembra(BaseAgent):
    AGENT_ID = "ivan.product.membra"
    NAME = "ivan"
    DEPARTMENT = "product"
    TITLE = "Technical Product Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Technical Product Manager. PRD writing API design review Release planning. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['PRD writing', 'API design review', 'Release planning']
    SKILLS: List[str] = ['prd_writing', 'api_design_review', 'release_planning', 'technical_specification', 'dependency_mapping']

    # ─── Job-Specific Skills ───

    async def write_prd(self, feature_name: str, requirements: list) -> dict:
        result = await self.think(f"Write a detailed PRD for feature '{feature_name}' with requirements: {requirements}. Include acceptance criteria, metrics, and dependencies.")
        return {"feature": feature_name, "prd": result}

    async def review_api(self, api_spec: str) -> dict:
        result = await self.think(f"Review this API design: {api_spec}. Check for consistency, completeness, and developer experience.")
        return {"review": result}

    async def plan_release(self, features: list, deadline: str) -> dict:
        result = await self.think(f"Plan a release containing {features} by {deadline}. Map dependencies, risks, and rollback plan.")
        return {"release_plan": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
