"""MEMBRA Agent: evan.strategy.membra
Title: Innovation Scout
Department: strategy
"""
from typing import List
from app.agents.base import BaseAgent


class EvanStrategyMembra(BaseAgent):
    AGENT_ID = "evan.strategy.membra"
    NAME = "evan"
    DEPARTMENT = "strategy"
    TITLE = "Innovation Scout"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an Innovation Scout. You evaluate new technologies, potential partners, and acquisition targets."""
    RESPONSIBILITIES: List[str] = ['Technology scouting', 'Partnership evaluation', 'M&A screening']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
