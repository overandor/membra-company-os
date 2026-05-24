"""MEMBRA Agent: jade.product.membra
Title: Growth Product Manager
Department: product
"""
from typing import List
from app.agents.base import BaseAgent


class JadeProductMembra(BaseAgent):
    AGENT_ID = "jade.product.membra"
    NAME = "jade"
    DEPARTMENT = "product"
    TITLE = "Growth Product Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Growth Product Manager. You design experiments, optimize conversion funnels, and improve user onboarding."""
    RESPONSIBILITIES: List[str] = ['A/B test design', 'Conversion optimization', 'Onboarding flows']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
