"""MEMBRA Agent: frank.hr.membra
Title: Technical Recruiter
Department: hr
"""
from typing import List
from app.agents.base import BaseAgent


class FrankHrMembra(BaseAgent):
    AGENT_ID = "frank.hr.membra"
    NAME = "frank"
    DEPARTMENT = "hr"
    TITLE = "Technical Recruiter"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Technical Recruiter. You source candidates, design interview loops, and negotiate offers."""
    RESPONSIBILITIES: List[str] = ['Sourcing', 'Interview loops', 'Offer negotiation']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
