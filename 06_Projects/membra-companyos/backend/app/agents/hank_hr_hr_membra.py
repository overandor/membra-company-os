"""MEMBRA Agent: hank_hr.hr.membra
Title: Culture & Engagement Specialist
Department: hr
"""
from typing import List
from app.agents.base import BaseAgent


class HankhrHrMembra(BaseAgent):
    AGENT_ID = "hank_hr.hr.membra"
    NAME = "hank"
    DEPARTMENT = "hr"
    TITLE = "Culture & Engagement Specialist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Culture & Engagement Specialist. You run surveys, design engagement initiatives, and lead diversity programs."""
    RESPONSIBILITIES: List[str] = ['Employee surveys', 'Engagement initiatives', 'Diversity programs']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
