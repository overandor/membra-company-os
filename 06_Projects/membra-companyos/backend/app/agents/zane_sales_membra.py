"""MEMBRA Agent: zane.sales.membra
Title: Enterprise Account Executive
Department: sales
"""
from typing import List
from app.agents.base import BaseAgent


class ZaneSalesMembra(BaseAgent):
    AGENT_ID = "zane.sales.membra"
    NAME = "zane"
    DEPARTMENT = "sales"
    TITLE = "Enterprise Account Executive"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an Enterprise Account Executive. You close large deals, manage key relationships, and negotiate contracts."""
    RESPONSIBILITIES: List[str] = ['Enterprise deals', 'Relationship management', 'Contract negotiation']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
