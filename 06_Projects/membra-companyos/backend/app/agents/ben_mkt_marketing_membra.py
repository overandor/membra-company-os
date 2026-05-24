"""MEMBRA Agent: ben_mkt.marketing.membra
Title: SEO Specialist
Department: marketing
"""
from typing import List
from app.agents.base import BaseAgent


class BenmktMarketingMembra(BaseAgent):
    AGENT_ID = "ben_mkt.marketing.membra"
    NAME = "ben"
    DEPARTMENT = "marketing"
    TITLE = "SEO Specialist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are an SEO Specialist. You research keywords, optimize technical SEO, and build backlink strategies."""
    RESPONSIBILITIES: List[str] = ['Keyword research', 'Technical SEO', 'Backlink strategy']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
