"""MEMBRA Agent: tom.proof.membra
Title: Compliance Auditor
Department: proof
"""
from typing import List
from app.agents.base import BaseAgent


class TomProofMembra(BaseAgent):
    AGENT_ID = "tom.proof.membra"
    NAME = "tom"
    DEPARTMENT = "proof"
    TITLE = "Compliance Auditor"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Compliance Auditor. You run SOC2 audits, review ISO27001 controls, and test compliance."""
    RESPONSIBILITIES: List[str] = ['SOC2 audit', 'ISO27001 review', 'Control testing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
