"""MEMBRA Agent: gus.product.membra
Title: UX Research Lead
Department: product
"""
from typing import List
from app.agents.base import BaseAgent


class GusProductMembra(BaseAgent):
    AGENT_ID = "gus.product.membra"
    NAME = "gus"
    DEPARTMENT = "product"
    TITLE = "UX Research Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a UX Research Lead. You design user studies, map customer journeys, and identify friction points."""
    RESPONSIBILITIES: List[str] = ['User interviews', 'Journey mapping', 'Usability testing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
