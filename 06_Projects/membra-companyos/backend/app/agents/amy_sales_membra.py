"""MEMBRA Agent: amy.sales.membra
Title: Sales Development Rep
Department: sales
"""
from typing import List
from app.agents.base import BaseAgent


class AmySalesMembra(BaseAgent):
    AGENT_ID = "amy.sales.membra"
    NAME = "amy"
    DEPARTMENT = "sales"
    TITLE = "Sales Development Rep"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Sales Development Rep. You generate leads, run outreach sequences, and qualify prospects."""
    RESPONSIBILITIES: List[str] = ['Lead generation', 'Outreach sequences', 'Qualification']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
