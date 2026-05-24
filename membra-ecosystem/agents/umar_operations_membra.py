"""MEMBRA Agent: umar.operations.membra
Title: SOP Documentation Lead
Department: operations

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class UmarOperationsMembra(BaseAgent):
    AGENT_ID = "umar.operations.membra"
    NAME = "umar"
    DEPARTMENT = "operations"
    TITLE = "SOP Documentation Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the SOP Documentation Lead. SOP writing Training materials Process auditing. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['SOP writing', 'Training materials', 'Process auditing']
    SKILLS: List[str] = ['sop_writing', 'training_material_creation', 'process_auditing', 'documentation_standards', 'knowledge_base_management']

    # ─── Job-Specific Skills ───

    async def write_sop(self, process: str, audience: str) -> dict:
        result = await self.think(f"Write a detailed SOP for '{process}' targeting {audience}. Include purpose, scope, procedure, and exceptions.")
        return {"sop": result}

    async def create_training(self, topic: str, format: str) -> dict:
        result = await self.think(f"Create {format} training materials for '{topic}'. Include learning objectives, modules, and assessments.")
        return {"training_materials": result}

    async def audit_process(self, process_name: str, standard: str) -> dict:
        result = await self.think(f"Audit process '{process_name}' against standard '{standard}'. Identify gaps and non-conformances.")
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
