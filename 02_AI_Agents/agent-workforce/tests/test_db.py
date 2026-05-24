import pytest
from sqlalchemy import select
from app.db.models import AgentRun, User, BillingEvent


@pytest.mark.asyncio
async def test_create_agent_run(db_session):
    run = AgentRun(
        agent_id="web_research",
        agent_name="Web Research Agent",
        query="test query",
        status="success",
        tokens_used=150,
        cost=0.15,
    )
    db_session.add(run)
    await db_session.commit()

    stmt = select(AgentRun).where(AgentRun.agent_id == "web_research")
    result = await db_session.execute(stmt)
    db_run = result.scalar_one()
    assert db_run.agent_name == "Web Research Agent"
    assert db_run.status == "success"
    assert db_run.tokens_used == 150


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(
        email="test@example.com",
        name="Test User",
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()

    stmt = select(User).where(User.email == "test@example.com")
    result = await db_session.execute(stmt)
    db_user = result.scalar_one()
    assert db_user.name == "Test User"
    assert db_user.role == "admin"
    assert db_user.is_active is True


@pytest.mark.asyncio
async def test_create_billing_event(db_session):
    event = BillingEvent(
        agent_id="web_research",
        amount=150.0,
        currency="usd",
        event_type="usage",
        status="completed",
    )
    db_session.add(event)
    await db_session.commit()

    stmt = select(BillingEvent).where(BillingEvent.agent_id == "web_research")
    result = await db_session.execute(stmt)
    db_event = result.scalar_one()
    assert db_event.amount == 150.0
    assert db_event.status == "completed"
