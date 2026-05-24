"""MEMBRA Agent: grace.hr.membra
Title: Learning & Development Lead
Department: hr

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class GraceHrMembra(BaseAgent):
    AGENT_ID = "grace.hr.membra"
    NAME = "grace"
    DEPARTMENT = "hr"
    TITLE = "Learning & Development Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Learning & Development Lead. Training programs Career paths Skills assessment. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Training programs', 'Career paths', 'Skills assessment']
    SKILLS: List[str] = ['training_program_design', 'career_path_mapping', 'skills_assessment', 'competency_framework', 'learning_platform_management']

    # ─── Job-Specific Skills ───

    async def design_training(self, skill_gap: str, audience: str, format: str) -> dict:
        result = await self.think(f"Design {format} training program for {audience} to close skill gap: {skill_gap}. Include modules, assessments, and metrics.")
        return {"training_program": result}

    async def map_career_path(self, role: str, levels: int) -> dict:
        result = await self.think(f"Map career path for '{role}' across {levels} levels. Include competencies, milestones, and transition criteria.")
        return {"career_path": result}

    async def assess_skills(self, team: str, required_skills: list) -> dict:
        result = await self.think(f"Assess skills for team {team} against required skills: {required_skills}. Identify gaps and development priorities.")
        return {"skills_assessment": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
