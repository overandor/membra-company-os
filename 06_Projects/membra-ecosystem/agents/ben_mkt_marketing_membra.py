"""MEMBRA Agent: ben_mkt.marketing.membra
Title: SEO Specialist
Department: marketing

This agent implements real job-specific skills matching their title and responsibilities.
Each method executes the actual task using LLM reasoning via Ollama.
"""
from typing import List
from agents.base import BaseAgent


class BenmktMarketingMembra(BaseAgent):
    AGENT_ID = "ben_mkt.marketing.membra"
    NAME = "ben"
    DEPARTMENT = "marketing"
    TITLE = "SEO Specialist"
    MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are the SEO Specialist. Keyword research Technical SEO Backlink strategy. Always provide actionable, detailed output backed by reasoning."""
    RESPONSIBILITIES: List[str] = ['Keyword research', 'Technical SEO', 'Backlink strategy']
    SKILLS: List[str] = ['keyword_research', 'technical_seo_audit', 'backlink_strategy', 'content_optimization', 'rank_tracking']

    # ─── Job-Specific Skills ───

    async def research_keywords(self, seed_terms: list, competitors: list) -> dict:
        result = await self.think(f"Research keywords from seeds: {seed_terms} vs competitors: {competitors}. Include volume, difficulty, and intent classification.")
        return {"keyword_research": result}

    async def audit_technical_seo(self, site_url: str, crawl_data: str) -> dict:
        result = await self.think(f"Conduct technical SEO audit for {site_url}. Crawl data: {crawl_data}. Check indexing, speed, mobile, schema, and redirects.")
        return {"technical_audit": result}

    async def build_backlink_strategy(self, domain: str, industry: str) -> dict:
        result = await self.think(f"Build a backlink strategy for {domain} in {industry}. Include outreach targets, content assets, and anchor text distribution.")
        return {"backlink_strategy": result}


    async def execute_task(self, task_type: str, params: dict) -> dict:
        """Route job-specific tasks to the appropriate skill method."""
        method_map = {
            # Map task types to methods - subclasses override as needed
        }
        # Default: use think() for any unmatched task
        prompt = f"Execute {task_type} with params: {params}"
        result = await self.think(prompt)
        return {"task": task_type, "result": result, "agent": self.agent_id}
