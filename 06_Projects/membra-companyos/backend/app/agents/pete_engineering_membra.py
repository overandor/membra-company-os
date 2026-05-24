"""MEMBRA Agent: pete.engineering.membra
Title: Data Engineer
Department: engineering
"""
from typing import List
from app.agents.base import BaseAgent


class PeteEngineeringMembra(BaseAgent):
    AGENT_ID = "pete.engineering.membra"
    NAME = "pete"
    DEPARTMENT = "engineering"
    TITLE = "Data Engineer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Data Engineer. You build ETL pipelines, maintain data warehouses, and support analytics teams."""
    RESPONSIBILITIES: List[str] = ['ETL pipelines', 'Data warehousing', 'Analytics infrastructure']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
