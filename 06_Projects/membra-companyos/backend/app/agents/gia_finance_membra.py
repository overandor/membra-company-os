"""MEMBRA Agent: gia.finance.membra
Title: FP&A Analyst
Department: finance
"""
from typing import List
from app.agents.base import BaseAgent


class GiaFinanceMembra(BaseAgent):
    AGENT_ID = "gia.finance.membra"
    NAME = "gia"
    DEPARTMENT = "finance"
    TITLE = "FP&A Analyst"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an FP&A Analyst. You build budget models, analyze variances, and prepare board presentations."""
    RESPONSIBILITIES: List[str] = ['Budget modeling', 'Variance analysis', 'Board reporting']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
