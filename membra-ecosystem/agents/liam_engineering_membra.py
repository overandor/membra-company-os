"""MEMBRA Agent: liam.engineering.membra
Title: Senior Backend Engineer
Department: engineering

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class LiamEngineeringMembra(BaseAgent):
    AGENT_ID = "liam.engineering.membra"
    NAME = "liam"
    DEPARTMENT = "engineering"
    TITLE = "Senior Backend Engineer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Senior Backend Engineer. API development Database design Service architecture. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['API development', 'Database design', 'Service architecture']
    SKILLS: List[str] = ['api_development', 'database_design', 'microservices', 'performance_tuning', 'async_programming']

    # ─── Job-Specific Skills ───

    async def design_api(self, resource: str, operations: list) -> dict:
        result = await self.think(f"Design a REST API for resource '{resource}' supporting operations: {operations}. Include endpoints, methods, and response schemas.")
        return {"api_design": result}

    async def design_database(self, entities: list, relationships: dict) -> dict:
        result = await self.think(f"Design a database schema for entities: {entities}. Relationships: {relationships}. Include indexes and constraints.")
        return {"schema": result}

    async def review_code(self, code: str, language: str) -> dict:
        prompt = f"Review this {language} code for quality, security, and performance. Suggest improvements:\n{code}"
        result = await self.think(prompt)
        return {"review": result}

    async def optimize_query(self, query: str, db_type: str) -> dict:
        prompt = f"Optimize this {db_type} query. Suggest indexes, rewrites, and explain plan improvements:\n{query}"
        result = await self.think(prompt)
        return {"optimization": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
