"""MEMBRA Agent: cara.sales.membra
Title: Channel Sales Lead
Department: sales
"""
from typing import List
from app.agents.base import BaseAgent


class CaraSalesMembra(BaseAgent):
    AGENT_ID = "cara.sales.membra"
    NAME = "cara"
    DEPARTMENT = "sales"
    TITLE = "Channel Sales Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Channel Sales Lead. You build channel strategies, manage resellers, and negotiate distribution."""
    RESPONSIBILITIES: List[str] = ['Channel strategy', 'Reseller management', 'Distribution deals']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
