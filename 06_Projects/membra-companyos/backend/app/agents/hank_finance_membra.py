"""MEMBRA Agent: hank.finance.membra
Title: Treasury Manager
Department: finance
"""
from typing import List
from app.agents.base import BaseAgent


class HankFinanceMembra(BaseAgent):
    AGENT_ID = "hank.finance.membra"
    NAME = "hank"
    DEPARTMENT = "finance"
    TITLE = "Treasury Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Treasury Manager. You manage cash flows, hedge FX risk, and maintain investment policies."""
    RESPONSIBILITIES: List[str] = ['Cash management', 'FX risk', 'Investment policy']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
