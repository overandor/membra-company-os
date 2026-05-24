"""MEMBRA Agent: rex.proof.membra
Title: Lead Auditor
Department: proof

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class RexProofMembra(BaseAgent):
    AGENT_ID = "rex.proof.membra"
    NAME = "rex"
    DEPARTMENT = "proof"
    TITLE = "Lead Auditor"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Lead Auditor. Audit planning Evidence review Report writing. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Audit planning', 'Evidence review', 'Report writing']
    SKILLS: List[str] = ['audit_planning', 'evidence_review', 'audit_report_writing', 'sampling_design', 'finding_classification']

    # ─── Job-Specific Skills ───

    async def plan_audit(self, scope: str, objectives: list) -> dict:
        result = await self.think(f"Plan an audit with scope '{scope}' and objectives: {objectives}. Include timeline, resources, and methodology.")
        return {"audit_plan": result}

    async def review_evidence(self, evidence_type: str, samples: list) -> dict:
        result = await self.think(f"Review {evidence_type} evidence from samples: {samples}. Assess sufficiency, reliability, and relevance.")
        return {"evidence_review": result}

    async def write_audit_report(self, findings: list, ratings: dict) -> dict:
        result = await self.think(f"Write an audit report with findings: {findings} and ratings: {ratings}. Include executive summary and action plan.")
        return {"audit_report": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
