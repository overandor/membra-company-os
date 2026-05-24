"""MEMBRA Agent: finn.finance.membra
Title: Senior Accountant
Department: finance
"""
from typing import List
from app.agents.base import BaseAgent


class FinnFinanceMembra(BaseAgent):
    AGENT_ID = "finn.finance.membra"
    NAME = "finn"
    DEPARTMENT = "finance"
    TITLE = "Senior Accountant"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Senior Accountant. You maintain books, execute month-end close, and prepare for audits."""
    RESPONSIBILITIES: List[str] = ['Bookkeeping', 'Month-end close', 'Audit prep']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
