"""MEMBRA Agent: wendy.concierge.membra
Title: Chatbot Trainer
Department: concierge

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class WendyConciergeMembra(BaseAgent):
    AGENT_ID = "wendy.concierge.membra"
    NAME = "wendy"
    DEPARTMENT = "concierge"
    TITLE = "Chatbot Trainer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Chatbot Trainer. Prompt engineering Conversation design Intent classification. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Prompt engineering', 'Conversation design', 'Intent classification']
    SKILLS: List[str] = ['prompt_engineering', 'conversation_design', 'intent_classification', 'training_data_curation', 'model_evaluation']

    # ─── Job-Specific Skills ───

    async def engineer_prompt(self, task: str, examples: list) -> dict:
        result = await self.think(f"Engineer a prompt for task '{task}' with examples: {examples}. Include instructions, context, and output format.")
        return {"prompt": result}

    async def curate_training_data(self, intent: str, utterances: list) -> dict:
        result = await self.think(f"Curate training data for intent '{intent}' from utterances: {utterances}. Include augmentations and edge cases.")
        return {"training_data": result}

    async def evaluate_model(self, test_cases: list, metrics: list) -> dict:
        result = await self.think(f"Evaluate chatbot on test cases: {test_cases}. Metrics: {metrics}. Include confusion matrix and error analysis.")
        return {"evaluation": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
