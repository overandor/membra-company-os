"""MEMBRA Agent: gus.product.membra
Title: UX Research Lead
Department: product

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class GusProductMembra(BaseAgent):
    AGENT_ID = "gus.product.membra"
    NAME = "gus"
    DEPARTMENT = "product"
    TITLE = "UX Research Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the UX Research Lead. User interviews Journey mapping Usability testing. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['User interviews', 'Journey mapping', 'Usability testing']
    SKILLS: List[str] = ['user_interviews', 'journey_mapping', 'usability_testing', 'heuristic_evaluation', 'survey_design']

    # ─── Job-Specific Skills ───

    async def design_interview(self, target_users: str, research_question: str) -> dict:
        result = await self.think(f"Design a user interview protocol for {target_users} to answer: {research_question}")
        return {"protocol": result}

    async def map_journey(self, persona: str, scenario: str) -> dict:
        result = await self.think(f"Map the customer journey for {persona} during {scenario}. Identify pain points and delights.")
        return {"persona": persona, "journey_map": result}

    async def run_usability_test(self, prototype_description: str, tasks: list) -> dict:
        result = await self.think(f"Design a usability test for this prototype: {prototype_description}. Tasks: {tasks}")
        return {"test_plan": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
