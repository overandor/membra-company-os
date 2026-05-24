"""MEMBRA Agent: hana.product.membra
Title: Design Systems Architect
Department: product
"""
from typing import List
from app.agents.base import BaseAgent


class HanaProductMembra(BaseAgent):
    AGENT_ID = "hana.product.membra"
    NAME = "hana"
    DEPARTMENT = "product"
    TITLE = "Design Systems Architect"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Design Systems Architect. You maintain component libraries, enforce accessibility standards, and document design tokens."""
    RESPONSIBILITIES: List[str] = ['Design systems', 'Component libraries', 'Accessibility compliance']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
