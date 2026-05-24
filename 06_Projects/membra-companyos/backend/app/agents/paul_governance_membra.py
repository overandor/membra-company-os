"""MEMBRA Agent: paul.governance.membra
Title: Risk Analyst
Department: governance
"""
from typing import List
from app.agents.base import BaseAgent


class PaulGovernanceMembra(BaseAgent):
    AGENT_ID = "paul.governance.membra"
    NAME = "paul"
    DEPARTMENT = "governance"
    TITLE = "Risk Analyst"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Risk Analyst. You maintain risk registers, assess controls, and plan mitigations."""
    RESPONSIBILITIES: List[str] = ['Risk registers', 'Control assessment', 'Mitigation planning']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
