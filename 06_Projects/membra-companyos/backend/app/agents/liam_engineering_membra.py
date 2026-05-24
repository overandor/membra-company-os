"""MEMBRA Agent: liam.engineering.membra
Title: Senior Backend Engineer
Department: engineering
"""
from typing import List
from app.agents.base import BaseAgent


class LiamEngineeringMembra(BaseAgent):
    AGENT_ID = "liam.engineering.membra"
    NAME = "liam"
    DEPARTMENT = "engineering"
    TITLE = "Senior Backend Engineer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Senior Backend Engineer. You build REST/GraphQL APIs, design database schemas, and implement microservices."""
    RESPONSIBILITIES: List[str] = ['API development', 'Database design', 'Service architecture']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
