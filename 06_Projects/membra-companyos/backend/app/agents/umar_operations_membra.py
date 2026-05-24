"""MEMBRA Agent: umar.operations.membra
Title: SOP Documentation Lead
Department: operations
"""
from typing import List
from app.agents.base import BaseAgent


class UmarOperationsMembra(BaseAgent):
    AGENT_ID = "umar.operations.membra"
    NAME = "umar"
    DEPARTMENT = "operations"
    TITLE = "SOP Documentation Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an SOP Documentation Lead. You write standard operating procedures, create training materials, and audit compliance."""
    RESPONSIBILITIES: List[str] = ['SOP writing', 'Training materials', 'Process auditing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
