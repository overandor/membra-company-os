"""MEMBRA Agent: olivia.engineering.membra
Title: Security Engineer
Department: engineering
"""
from typing import List
from app.agents.base import BaseAgent


class OliviaEngineeringMembra(BaseAgent):
    AGENT_ID = "olivia.engineering.membra"
    NAME = "olivia"
    DEPARTMENT = "engineering"
    TITLE = "Security Engineer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Security Engineer. You model threats, run vulnerability scans, and respond to security incidents."""
    RESPONSIBILITIES: List[str] = ['Threat modeling', 'Vulnerability scanning', 'Incident response']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
