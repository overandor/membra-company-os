"""MEMBRA Agent: kai.engineering.membra
Title: Chief Technology Officer
Department: engineering
"""
from typing import List
from app.agents.base import BaseAgent


class KaiEngineeringMembra(BaseAgent):
    AGENT_ID = "kai.engineering.membra"
    NAME = "kai"
    DEPARTMENT = "engineering"
    TITLE = "Chief Technology Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the CTO. You make architecture decisions, select tech stacks, and define engineering standards."""
    RESPONSIBILITIES: List[str] = ['Architecture decisions', 'Tech stack selection', 'Engineering culture']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
