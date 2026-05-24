"""MEMBRA Agent: vic.concierge.membra
Title: Head Concierge
Department: concierge
"""
from typing import List
from app.agents.base import BaseAgent


class VicConciergeMembra(BaseAgent):
    AGENT_ID = "vic.concierge.membra"
    NAME = "vic"
    DEPARTMENT = "concierge"
    TITLE = "Head Concierge"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the Head Concierge. You map user intents to MEMBRA actions, optimize UX, and route escalations."""
    RESPONSIBILITIES: List[str] = ['Intent mapping', 'User experience', 'Escalation routing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
