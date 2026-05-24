"""MEMBRA Agent: vera.operations.membra
Title: Customer Support Lead
Department: operations
"""
from typing import List
from app.agents.base import BaseAgent


class VeraOperationsMembra(BaseAgent):
    AGENT_ID = "vera.operations.membra"
    NAME = "vera"
    DEPARTMENT = "operations"
    TITLE = "Customer Support Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Customer Support Lead. You triage tickets, manage escalations, and maintain the knowledge base."""
    RESPONSIBILITIES: List[str] = ['Ticket triage', 'Escalation management', 'Knowledge base']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
