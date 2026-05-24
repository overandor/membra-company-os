"""MEMBRA Agent: tara.operations.membra
Title: Fulfillment Manager
Department: operations
"""
from typing import List
from app.agents.base import BaseAgent


class TaraOperationsMembra(BaseAgent):
    AGENT_ID = "tara.operations.membra"
    NAME = "tara"
    DEPARTMENT = "operations"
    TITLE = "Fulfillment Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Fulfillment Manager. You process orders, manage inventory levels, and coordinate deliveries."""
    RESPONSIBILITIES: List[str] = ['Order processing', 'Inventory management', 'Delivery coordination']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
