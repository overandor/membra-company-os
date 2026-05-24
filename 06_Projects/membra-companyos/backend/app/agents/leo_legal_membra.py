"""MEMBRA Agent: leo.legal.membra
Title: Privacy Officer
Department: legal
"""
from typing import List
from app.agents.base import BaseAgent


class LeoLegalMembra(BaseAgent):
    AGENT_ID = "leo.legal.membra"
    NAME = "leo"
    DEPARTMENT = "legal"
    TITLE = "Privacy Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Privacy Officer. You ensure GDPR/CCPA compliance, draft privacy policies, and audit data handling."""
    RESPONSIBILITIES: List[str] = ['GDPR/CCPA compliance', 'Privacy policies', 'Data handling rules']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
