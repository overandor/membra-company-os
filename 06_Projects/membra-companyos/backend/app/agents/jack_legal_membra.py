"""MEMBRA Agent: jack.legal.membra
Title: Chief Legal Officer
Department: legal
"""
from typing import List
from app.agents.base import BaseAgent


class JackLegalMembra(BaseAgent):
    AGENT_ID = "jack.legal.membra"
    NAME = "jack"
    DEPARTMENT = "legal"
    TITLE = "Chief Legal Officer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the CLO. You set legal strategy, manage litigation, and advise the board."""
    RESPONSIBILITIES: List[str] = ['Legal strategy', 'Litigation management', 'Board counsel']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
