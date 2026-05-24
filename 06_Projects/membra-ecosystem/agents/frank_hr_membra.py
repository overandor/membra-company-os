"""MEMBRA Agent: frank.hr.membra
Title: Technical Recruiter
Department: hr

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class FrankHrMembra(BaseAgent):
    AGENT_ID = "frank.hr.membra"
    NAME = "frank"
    DEPARTMENT = "hr"
    TITLE = "Technical Recruiter"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Technical Recruiter. Sourcing Interview loops Offer negotiation. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Sourcing', 'Interview loops', 'Offer negotiation']
    SKILLS: List[str] = ['technical_sourcing', 'interview_loop_design', 'offer_negotiation', 'candidate_experience', 'diversity_sourcing']

    # ─── Job-Specific Skills ───

    async def source_candidates(self, role: str, channels: list) -> dict:
        result = await self.think(f"Develop sourcing strategy for '{role}' using channels: {channels}. Include boolean strings, outreach templates, and diversity focus.")
        return {"sourcing_strategy": result}

    async def design_interview_loop(self, role: str, competencies: list) -> dict:
        result = await self.think(f"Design interview loop for '{role}' assessing competencies: {competencies}. Include questions, rubrics, and panel assignments.")
        return {"interview_loop": result}

    async def negotiate_offer(self, candidate: str, expectations: dict, budget: dict) -> dict:
        result = await self.think(f"Develop offer negotiation strategy for {candidate}. Expectations: {expectations}. Budget: {budget}. Include creative comp options.")
        return {"negotiation_strategy": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
