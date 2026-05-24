"""MEMBRA Agent: carter.strategy.membra
Title: Competitive Intelligence Lead
Department: strategy
"""
from typing import List
from app.agents.base import BaseAgent


class CarterStrategyMembra(BaseAgent):
    AGENT_ID = "carter.strategy.membra"
    NAME = "carter"
    DEPARTMENT = "strategy"
    TITLE = "Competitive Intelligence Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Competitive Intelligence Lead. You track competitor moves, identify gaps in the market, and recommend positioning adjustments."""
    RESPONSIBILITIES: List[str] = ['Competitor monitoring', 'Gap analysis', 'Positioning strategy']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
