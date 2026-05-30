"""
CollateralOps — LLM agent for asset improvement recommendations (T23).
Uses Groq or Ollama to generate prioritized improvement tasks.
"""
import json
import os
from typing import Dict, List

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def _build_prompt(asset: Dict) -> str:
    """Build a structured prompt for improvement recommendations."""
    return f"""You are a software collateral appraisal agent. Analyze this software asset and suggest the top 5 improvements that would most increase its financeability score (collateral value for lenders).

Asset: {asset.get('name', 'Unknown')}
Type: {asset.get('type', 'repo')}
Status: {asset.get('status', 'active')}
Lines of code: {asset.get('lines_of_code', 0)}
Tech stack: {', '.join(asset.get('tech_stack', []))}
Current financeability score: {asset.get('financeability_score', 0)}/100
Risk score: {asset.get('risk_score', 0)}/100
Strategic value: ${asset.get('strategic_value', 0):,.0f}

Existing risks: {json.dumps([{'category': r.get('category'), 'severity': r.get('severity'), 'reason': r.get('reason')} for r in asset.get('risks', [])])}

Return ONLY a JSON array of objects with these exact keys:
- title: concise action title
- category: one of [documentation, testing, security, legal, coverage, build, commercial]
- impact_estimate: numeric points 1-15
- effort_estimate: one of [small, medium, large]
- rationale: one sentence explaining why this increases collateral value

Order by impact_estimate descending. Be specific and actionable."""


async def query_groq(prompt: str) -> List[Dict]:
    """Call Groq API for recommendations."""
    if not GROQ_API_KEY:
        return []
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1500,
            },
        )
        if r.status_code != 200:
            return []
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)


async def query_ollama(prompt: str, model: str = "llama3") -> List[Dict]:
    """Call local Ollama API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            if r.status_code != 200:
                return []
            content = r.json().get("response", "")
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return []


async def generate_improvements(asset: Dict, prefer_local: bool = False) -> List[Dict]:
    """Generate improvement recommendations for an asset."""
    prompt = _build_prompt(asset)
    if prefer_local or not GROQ_API_KEY:
        return await query_ollama(prompt)
    return await query_groq(prompt)
