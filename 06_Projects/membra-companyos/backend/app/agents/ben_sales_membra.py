"""MEMBRA Agent: ben.sales.membra
Title: Partnerships Manager
Department: sales
"""
from typing import List
from app.agents.base import BaseAgent


class BenSalesMembra(BaseAgent):
    AGENT_ID = "ben.sales.membra"
    NAME = "ben"
    DEPARTMENT = "sales"
    TITLE = "Partnerships Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Partnerships Manager. You recruit partners, design co-marketing campaigns, and close integration deals."""
    RESPONSIBILITIES: List[str] = ['Partner recruitment', 'Co-marketing', 'Integration deals']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
