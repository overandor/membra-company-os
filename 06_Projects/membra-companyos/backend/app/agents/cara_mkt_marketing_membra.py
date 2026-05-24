"""MEMBRA Agent: cara_mkt.marketing.membra
Title: Community Manager
Department: marketing
"""
from typing import List
from app.agents.base import BaseAgent


class CaramktMarketingMembra(BaseAgent):
    AGENT_ID = "cara_mkt.marketing.membra"
    NAME = "cara"
    DEPARTMENT = "marketing"
    TITLE = "Community Manager"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Community Manager. You manage online communities, plan events, and run ambassador programs."""
    RESPONSIBILITIES: List[str] = ['Discord/Slack management', 'Event planning', 'Ambassador program']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
