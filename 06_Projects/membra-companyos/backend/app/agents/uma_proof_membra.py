"""MEMBRA Agent: uma.proof.membra
Title: Digital Forensics Lead
Department: proof
"""
from typing import List
from app.agents.base import BaseAgent


class UmaProofMembra(BaseAgent):
    AGENT_ID = "uma.proof.membra"
    NAME = "uma"
    DEPARTMENT = "proof"
    TITLE = "Digital Forensics Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Digital Forensics Lead. You reconstruct incidents, analyze logs, and preserve digital evidence."""
    RESPONSIBILITIES: List[str] = ['Incident reconstruction', 'Log analysis', 'Evidence preservation']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
