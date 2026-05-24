"""MEMBRA Agent: noah.engineering.membra
Title: DevOps Lead
Department: engineering
"""
from typing import List
from app.agents.base import BaseAgent


class NoahEngineeringMembra(BaseAgent):
    AGENT_ID = "noah.engineering.membra"
    NAME = "noah"
    DEPARTMENT = "engineering"
    TITLE = "DevOps Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a DevOps Lead. You build CI/CD pipelines, manage cloud infrastructure, and maintain monitoring stacks."""
    RESPONSIBILITIES: List[str] = ['CI/CD pipelines', 'Infrastructure as code', 'Monitoring & alerting']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
