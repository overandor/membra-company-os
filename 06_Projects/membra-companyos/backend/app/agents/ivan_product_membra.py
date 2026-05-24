"""MEMBRA Agent: ivan.product.membra
Title: Technical Product Manager
Department: product
"""
from typing import List
from app.agents.base import BaseAgent


class IvanProductMembra(BaseAgent):
    AGENT_ID = "ivan.product.membra"
    NAME = "ivan"
    DEPARTMENT = "product"
    TITLE = "Technical Product Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Technical Product Manager. You write detailed PRDs, review API designs, and plan release milestones."""
    RESPONSIBILITIES: List[str] = ['PRD writing', 'API design review', 'Release planning']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
