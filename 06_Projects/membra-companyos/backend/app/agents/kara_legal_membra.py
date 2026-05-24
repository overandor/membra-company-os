"""MEMBRA Agent: kara.legal.membra
Title: Contract Specialist
Department: legal
"""
from typing import List
from app.agents.base import BaseAgent


class KaraLegalMembra(BaseAgent):
    AGENT_ID = "kara.legal.membra"
    NAME = "kara"
    DEPARTMENT = "legal"
    TITLE = "Contract Specialist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Contract Specialist. You draft agreements, maintain templates, and review vendor contracts."""
    RESPONSIBILITIES: List[str] = ['Contract drafting', 'Template management', 'Vendor agreements']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
