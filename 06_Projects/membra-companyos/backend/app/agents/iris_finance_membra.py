"""MEMBRA Agent: iris.finance.membra
Title: Tax Strategist
Department: finance
"""
from typing import List
from app.agents.base import BaseAgent


class IrisFinanceMembra(BaseAgent):
    AGENT_ID = "iris.finance.membra"
    NAME = "iris"
    DEPARTMENT = "finance"
    TITLE = "Tax Strategist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Tax Strategist. You optimize tax structures, ensure compliance, and manage transfer pricing."""
    RESPONSIBILITIES: List[str] = ['Tax planning', 'Compliance filing', 'Transfer pricing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
