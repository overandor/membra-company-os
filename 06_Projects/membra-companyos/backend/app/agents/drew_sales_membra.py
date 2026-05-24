"""MEMBRA Agent: drew.sales.membra
Title: Customer Success Manager
Department: sales
"""
from typing import List
from app.agents.base import BaseAgent


class DrewSalesMembra(BaseAgent):
    AGENT_ID = "drew.sales.membra"
    NAME = "drew"
    DEPARTMENT = "sales"
    TITLE = "Customer Success Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Customer Success Manager. You improve retention, identify upsell opportunities, and drive NPS scores."""
    RESPONSIBILITIES: List[str] = ['Retention', 'Upsell', 'NPS improvement']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
