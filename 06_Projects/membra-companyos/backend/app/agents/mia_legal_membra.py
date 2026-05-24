"""MEMBRA Agent: mia.legal.membra
Title: IP Counsel
Department: legal
"""
from typing import List
from app.agents.base import BaseAgent


class MiaLegalMembra(BaseAgent):
    AGENT_ID = "mia.legal.membra"
    NAME = "mia"
    DEPARTMENT = "legal"
    TITLE = "IP Counsel"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an IP Counsel. You manage patent portfolios, protect trademarks, and negotiate IP licenses."""
    RESPONSIBILITIES: List[str] = ['Patent strategy', 'Trademark protection', 'IP licensing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
