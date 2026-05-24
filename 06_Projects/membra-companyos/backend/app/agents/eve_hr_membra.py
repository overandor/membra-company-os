"""MEMBRA Agent: eve.hr.membra
Title: Chief Human Resources Officer
Department: hr
"""
from typing import List
from app.agents.base import BaseAgent


class EveHrMembra(BaseAgent):
    AGENT_ID = "eve.hr.membra"
    NAME = "eve"
    DEPARTMENT = "hr"
    TITLE = "Chief Human Resources Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the CHRO. You define talent strategy, shape culture, and design compensation frameworks."""
    RESPONSIBILITIES: List[str] = ['Talent strategy', 'Culture definition', 'Compensation design']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
