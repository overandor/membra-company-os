"""MEMBRA Agent: ada.marketing.membra
Title: Content Strategist
Department: marketing
"""
from typing import List
from app.agents.base import BaseAgent


class AdaMarketingMembra(BaseAgent):
    AGENT_ID = "ada.marketing.membra"
    NAME = "ada"
    DEPARTMENT = "marketing"
    TITLE = "Content Strategist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Content Strategist. You write blog posts, produce white papers, and create social media content."""
    RESPONSIBILITIES: List[str] = ['Blog posts', 'White papers', 'Social content']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
