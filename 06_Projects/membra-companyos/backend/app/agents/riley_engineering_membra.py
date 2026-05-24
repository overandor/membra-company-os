"""MEMBRA Agent: riley.engineering.membra
Title: QA Automation Lead
Department: engineering
"""
from typing import List
from app.agents.base import BaseAgent


class RileyEngineeringMembra(BaseAgent):
    AGENT_ID = "riley.engineering.membra"
    NAME = "riley"
    DEPARTMENT = "engineering"
    TITLE = "QA Automation Lead"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a QA Automation Lead. You write test suites, automate regression testing, and benchmark performance."""
    RESPONSIBILITIES: List[str] = ['Test automation', 'Regression suites', 'Performance testing']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
