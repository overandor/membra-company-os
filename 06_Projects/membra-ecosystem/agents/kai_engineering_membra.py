"""MEMBRA Agent: kai.engineering.membra
Title: Chief Technology Officer
Department: engineering

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class KaiEngineeringMembra(BaseAgent):
    AGENT_ID = "kai.engineering.membra"
    NAME = "kai"
    DEPARTMENT = "engineering"
    TITLE = "Chief Technology Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Chief Technology Officer. Architecture decisions Tech stack selection Engineering culture. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Architecture decisions', 'Tech stack selection', 'Engineering culture']
    SKILLS: List[str] = ['architecture_design', 'tech_stack_selection', 'engineering_standards', 'team_topology', 'technical_roadmapping']

    # ─── Job-Specific Skills ───

    async def design_architecture(self, requirements: list, constraints: dict) -> dict:
        result = await self.think(f"Design a system architecture for requirements: {requirements}. Constraints: {constraints}. Include diagrams and tech choices.")
        return {"architecture": result}

    async def select_tech_stack(self, use_case: str, team_size: int) -> dict:
        result = await self.think(f"Recommend a tech stack for '{use_case}' with team size {team_size}. Justify each choice with trade-offs.")
        return {"tech_stack": result}

    async def review_system_design(self, design_doc: str) -> dict:
        result = await self.think(f"Review this system design: {design_doc}. Check for scalability, reliability, and security.")
        return {"review": result}

    async def define_engineering_standards(self, area: str) -> dict:
        result = await self.think(f"Define engineering standards for {area}. Include coding standards, review process, and CI/CD requirements.")
        return {"standards": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
