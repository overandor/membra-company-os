import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_agents(client):
    response = await client.get("/agents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 30
    assert data[0]["id"]
    assert data[0]["name"]


@pytest.mark.asyncio
async def test_get_agent(client):
    response = await client.get("/agents/web_research")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "web_research"
    assert "Web Research" in data["name"]


@pytest.mark.asyncio
async def test_get_agent_not_found(client):
    response = await client.get("/agents/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_agent_appraisal(client):
    response = await client.get("/agents/web_research/appraisal")
    assert response.status_code == 200
    data = response.json()
    assert "valuation" in data


@pytest.mark.asyncio
async def test_portfolio_appraisal(client):
    response = await client.get("/agents/portfolio/appraisal")
    assert response.status_code == 200
    data = response.json()
    assert "total_valuation" in data
    assert "average_valuation" in data
