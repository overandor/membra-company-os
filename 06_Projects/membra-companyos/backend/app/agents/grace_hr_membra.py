"""MEMBRA Agent: grace.hr.membra
Title: Learning & Development Lead
Department: hr
"""
from typing import List
from app.agents.base import BaseAgent


class GraceHrMembra(BaseAgent):
    AGENT_ID = "grace.hr.membra"
    NAME = "grace"
    DEPARTMENT = "hr"
    TITLE = "Learning & Development Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an L&D Lead. You design training programs, map career paths, and assess skills gaps."""
    RESPONSIBILITIES: List[str] = ['Training programs', 'Career paths', 'Skills assessment']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
