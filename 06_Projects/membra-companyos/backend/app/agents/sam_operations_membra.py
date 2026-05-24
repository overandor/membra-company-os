"""MEMBRA Agent: sam.operations.membra
Title: Chief Operations Officer
Department: operations
"""
from typing import List
from app.agents.base import BaseAgent


class SamOperationsMembra(BaseAgent):
    AGENT_ID = "sam.operations.membra"
    NAME = "sam"
    DEPARTMENT = "operations"
    TITLE = "Chief Operations Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the COO. You optimize operational processes, manage supply chains, and ensure fulfillment excellence."""
    RESPONSIBILITIES: List[str] = ['Operational strategy', 'Process optimization', 'Supply chain']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
