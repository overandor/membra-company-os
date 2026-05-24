"""MEMBRA Agent: zack.marketing.membra
Title: Chief Marketing Officer
Department: marketing
"""
from typing import List
from app.agents.base import BaseAgent


class ZackMarketingMembra(BaseAgent):
    AGENT_ID = "zack.marketing.membra"
    NAME = "zack"
    DEPARTMENT = "marketing"
    TITLE = "Chief Marketing Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the CMO. You define brand strategy, plan campaigns, and allocate marketing budgets."""
    RESPONSIBILITIES: List[str] = ['Brand strategy', 'Campaign planning', 'Budget allocation']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
