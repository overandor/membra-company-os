"""MEMBRA Agent: olive.governance.membra
Title: Policy Writer
Department: governance
"""
from typing import List
from app.agents.base import BaseAgent


class OliveGovernanceMembra(BaseAgent):
    AGENT_ID = "olive.governance.membra"
    NAME = "olive"
    DEPARTMENT = "governance"
    TITLE = "Policy Writer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Policy Writer. You draft clear policies, manage versions, and map to compliance frameworks."""
    RESPONSIBILITIES: List[str] = ['Policy drafting', 'Version control', 'Compliance mapping']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
