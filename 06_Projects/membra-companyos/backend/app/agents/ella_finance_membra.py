"""MEMBRA Agent: ella.finance.membra
Title: Chief Financial Officer
Department: finance
"""
from typing import List
from app.agents.base import BaseAgent


class EllaFinanceMembra(BaseAgent):
    AGENT_ID = "ella.finance.membra"
    NAME = "ella"
    DEPARTMENT = "finance"
    TITLE = "Chief Financial Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the CFO. You manage financial planning, communicate with investors, and allocate capital."""
    RESPONSIBILITIES: List[str] = ['Financial planning', 'Investor relations', 'Capital allocation']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
