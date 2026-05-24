"""Tests for MEMBRA Agent Network Protocol OS."""
import pytest
from agents.registry import AgentRegistry


@pytest.mark.asyncio
async def test_registry_loads_60_agents():
    reg = AgentRegistry()
    count = await reg.load_all()
    assert count == 60


def test_dot_notation_ids():
    reg = AgentRegistry()
    import asyncio
    asyncio.get_event_loop().run_until_complete(reg.load_all())

    for agent_id in reg._agents:
        parts = agent_id.split(".")
        assert len(parts) == 3
        assert parts[2] == "membra"

    assert "alex.strategy.membra" in reg._agents
    assert "kai.engineering.membra" in reg._agents
    assert "zack.marketing.membra" in reg._agents
    assert "eve.hr.membra" in reg._agents


def test_job_descriptions():
    reg = AgentRegistry()
    import asyncio
    asyncio.get_event_loop().run_until_complete(reg.load_all())

    alex = reg.get("alex.strategy.membra")
    assert "Chief Strategy Officer" in alex.job_description
    assert "Long-term vision" in alex.job_description

    kai = reg.get("kai.engineering.membra")
    assert "Chief Technology Officer" in kai.job_description


def test_departments():
    reg = AgentRegistry()
    import asyncio
    asyncio.get_event_loop().run_until_complete(reg.load_all())

    depts = reg.departments()
    assert len(depts) == 12
    dept_map = {d["id"]: d for d in depts}
    assert dept_map["strategy"]["count"] == 5
    assert dept_map["engineering"]["count"] == 8
    assert dept_map["marketing"]["count"] == 5


def test_stats():
    reg = AgentRegistry()
    import asyncio
    asyncio.get_event_loop().run_until_complete(reg.load_all())

    stats = reg.stats()
    assert stats["total"] == 60
    assert stats["idle"] == 60
    assert stats["departments"] == 12


@pytest.mark.asyncio
async def test_think_without_ollama():
    """Agents should handle missing Ollama gracefully."""
    reg = AgentRegistry(ollama_host="http://localhost:99999", mode="local")
    await reg.load_all()
    alex = reg.get("alex.strategy.membra")
    result = await alex.think("What is the market outlook?")
    assert "ERROR" in result or len(result) > 0
    assert alex.status == "error"


@pytest.mark.asyncio
async def test_agent_has_skill_methods():
    reg = AgentRegistry()
    await reg.load_all()
    
    # Alex should have strategy methods
    alex = reg.get("alex.strategy.membra")
    assert hasattr(alex, "analyze_market")
    assert hasattr(alex, "forecast_trends")
    assert hasattr(alex, "recommend_strategy")
    assert hasattr(alex, "competitor_intelligence")
    
    # Kai should have engineering methods
    kai = reg.get("kai.engineering.membra")
    assert hasattr(kai, "design_architecture")
    assert hasattr(kai, "select_tech_stack")
    assert hasattr(kai, "review_system_design")
    assert hasattr(kai, "define_engineering_standards")
    
    # Zack should have marketing methods
    zack = reg.get("zack.marketing.membra")
    assert hasattr(zack, "define_brand")
    assert hasattr(zack, "plan_campaign")
    assert hasattr(zack, "allocate_budget")
