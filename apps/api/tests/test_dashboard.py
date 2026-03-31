import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.services.auth_service import create_access_token


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient):
    response = await client.get("/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_returns_user_data(client: AsyncClient, db_session: AsyncSession):
    user = User(email="test@example.com", name="Test User", subscription_tier="free", password_hash="hashed")
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(user.id, user.email)

    response = await client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == user.email
    assert "usage" in data
    assert "recent_assessments" in data


@pytest.mark.asyncio
async def test_assessment_history_pagination(client: AsyncClient, db_session: AsyncSession):
    user = User(email="test2@example.com", name="Test User 2", subscription_tier="free", password_hash="hashed")
    db_session.add(user)
    await db_session.commit()

    for i in range(15):
        assessment = Assessment(
            user_id=user.id,
            mode=AssessmentMode.quick,
            status=AssessmentStatus.completed,
            final_score=80.0 + i,
            level=3,
            completed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        db_session.add(assessment)
    await db_session.commit()

    token = create_access_token(user.id, user.email)

    response = await client.get("/dashboard/assessments/history?page=1&limit=10",
                                headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["assessments"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_assessment_history_filter_by_mode(client: AsyncClient, db_session: AsyncSession):
    user = User(email="test3@example.com", name="Test User 3", subscription_tier="free", password_hash="hashed")
    db_session.add(user)
    await db_session.commit()

    quick = Assessment(
        user_id=user.id,
        mode=AssessmentMode.quick,
        status=AssessmentStatus.completed,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    full = Assessment(
        user_id=user.id,
        mode=AssessmentMode.full,
        status=AssessmentStatus.completed,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db_session.add_all([quick, full])
    await db_session.commit()

    token = create_access_token(user.id, user.email)

    response = await client.get("/dashboard/assessments/history?mode=quick",
                                headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert all(a["mode"] == "quick" for a in data["assessments"])

