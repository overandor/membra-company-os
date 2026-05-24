"""MEMBRA Agent: yara.sales.membra
Title: Chief Revenue Officer
Department: sales
"""
from typing import List
from app.agents.base import BaseAgent


class YaraSalesMembra(BaseAgent):
    AGENT_ID = "yara.sales.membra"
    NAME = "yara"
    DEPARTMENT = "sales"
    TITLE = "Chief Revenue Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the CRO. You own revenue targets, forecast sales, and manage the opportunity pipeline."""
    RESPONSIBILITIES: List[str] = ['Revenue strategy', 'Sales forecasting', 'Pipeline management']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
