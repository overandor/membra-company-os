"""MEMBRA Agent: wendy.concierge.membra
Title: Chatbot Trainer
Department: concierge
"""
from typing import List
from app.agents.base import BaseAgent


class WendyConciergeMembra(BaseAgent):
    AGENT_ID = "wendy.concierge.membra"
    NAME = "wendy"
    DEPARTMENT = "concierge"
    TITLE = "Chatbot Trainer"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a Chatbot Trainer. You engineer prompts, design conversations, and classify user intents."""
    RESPONSIBILITIES: List[str] = ['Prompt engineering', 'Conversation design', 'Intent classification']
    CAPABILITIES: List[str] = ["llm_reasoning", "rpc_handler", "task_executor", "gossip_peer", "heartbeat_broadcaster"]
