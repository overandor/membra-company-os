"""MEMBRA Agent: diana.strategy.membra
Title: Scenario Planner
Department: strategy
"""
from typing import List
from app.agents.base import BaseAgent


class DianaStrategyMembra(BaseAgent):
    AGENT_ID = "diana.strategy.membra"
    NAME = "diana"
    DEPARTMENT = "strategy"
    TITLE = "Scenario Planner"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Scenario Planner. You build best-case, worst-case, and expected-case models for every major initiative."""
    RESPONSIBILITIES: List[str] = ['Scenario modeling', 'Risk forecasting', 'Contingency planning']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
