"""MEMBRA Agent: jade.product.membra
Title: Growth Product Manager
Department: product

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class JadeProductMembra(BaseAgent):
    AGENT_ID = "jade.product.membra"
    NAME = "jade"
    DEPARTMENT = "product"
    TITLE = "Growth Product Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Growth Product Manager. A/B test design Conversion optimization Onboarding flows. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['A/B test design', 'Conversion optimization', 'Onboarding flows']
    SKILLS: List[str] = ['ab_test_design', 'conversion_rate_optimization', 'onboarding_flow_design', 'funnel_analysis', 'growth_hacking']

    # ─── Job-Specific Skills ───

    async def design_ab_test(self, hypothesis: str, metrics: list) -> dict:
        result = await self.think(f"Design an A/B test for hypothesis: '{hypothesis}'. Success metrics: {metrics}. Include sample size and duration.")
        return {"test_design": result}

    async def optimize_funnel(self, funnel_steps: list, current_conversion: float) -> dict:
        result = await self.think(f"Optimize funnel with steps {funnel_steps}. Current conversion: {current_conversion}%. Identify drop-off points and fixes.")
        return {"optimization": result}

    async def design_onboarding(self, user_type: str, product_features: list) -> dict:
        result = await self.think(f"Design an onboarding flow for {user_type} users. Key features to highlight: {product_features}")
        return {"onboarding_flow": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
