"""MEMBRA Agent: rex.proof.membra
Title: Lead Auditor
Department: proof
"""
from typing import List
from app.agents.base import BaseAgent


class RexProofMembra(BaseAgent):
    AGENT_ID = "rex.proof.membra"
    NAME = "rex"
    DEPARTMENT = "proof"
    TITLE = "Lead Auditor"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Lead Auditor. You plan audits, review evidence, and write detailed audit reports."""
    RESPONSIBILITIES: List[str] = ['Audit planning', 'Evidence review', 'Report writing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
