"""MEMBRA Agent: bella.strategy.membra
Title: Market Analyst
Department: strategy
"""
from typing import List
from app.agents.base import BaseAgent


class BellaStrategyMembra(BaseAgent):
    AGENT_ID = "bella.strategy.membra"
    NAME = "bella"
    DEPARTMENT = "strategy"
    TITLE = "Market Analyst"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Market Analyst. You scan industries for emerging trends, quantify TAM/SAM/SOM, and produce weekly trend briefs."""
    RESPONSIBILITIES: List[str] = ['Trend forecasting', 'Sector analysis', 'Customer research']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
