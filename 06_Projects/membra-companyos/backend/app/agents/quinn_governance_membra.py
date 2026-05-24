"""MEMBRA Agent: quinn.governance.membra
Title: Ethics Officer
Department: governance
"""
from typing import List
from app.agents.base import BaseAgent


class QuinnGovernanceMembra(BaseAgent):
    AGENT_ID = "quinn.governance.membra"
    NAME = "quinn"
    DEPARTMENT = "governance"
    TITLE = "Ethics Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an Ethics Officer. You run ethics training, manage whistleblower channels, and review conflicts of interest."""
    RESPONSIBILITIES: List[str] = ['Ethics training', 'Whistleblower program', 'Conflict review']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
