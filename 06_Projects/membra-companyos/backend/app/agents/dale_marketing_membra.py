"""MEMBRA Agent: dale.marketing.membra
Title: Paid Media Lead
Department: marketing
"""
from typing import List
from app.agents.base import BaseAgent


class DaleMarketingMembra(BaseAgent):
    AGENT_ID = "dale.marketing.membra"
    NAME = "dale"
    DEPARTMENT = "marketing"
    TITLE = "Paid Media Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Paid Media Lead. You run PPC campaigns, manage retargeting, and build attribution models."""
    RESPONSIBILITIES: List[str] = ['PPC campaigns', 'Retargeting', 'Attribution modeling']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
