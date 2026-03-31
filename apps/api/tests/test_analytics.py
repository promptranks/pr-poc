import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.services.analytics_service import AnalyticsService
from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.models.user import User


@pytest.mark.asyncio
async def test_score_trend_calculation(db_session):
    user = User(id=uuid4(), email="test@example.com", name="Test User", password_hash="hashed")
    db_session.add(user)

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    assessments = [
        Assessment(
            id=uuid4(), user_id=user.id, mode=AssessmentMode.full,
            status=AssessmentStatus.completed, final_score=75.0,
            completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            expires_at=expires
        ),
        Assessment(
            id=uuid4(), user_id=user.id, mode=AssessmentMode.full,
            status=AssessmentStatus.completed, final_score=82.0,
            completed_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            expires_at=expires
        ),
        Assessment(
            id=uuid4(), user_id=user.id, mode=AssessmentMode.full,
            status=AssessmentStatus.completed, final_score=88.0,
            completed_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            expires_at=expires
        )
    ]

    for a in assessments:
        db_session.add(a)
    await db_session.commit()

    trend = await AnalyticsService.get_score_trend(user.id, db_session)

    assert len(trend) == 3
    assert trend[0]["score"] == 75.0
    assert trend[1]["score"] == 82.0
    assert trend[2]["score"] == 88.0


@pytest.mark.asyncio
async def test_pillar_comparison(db_session):
    user = User(id=uuid4(), email="test@example.com", name="Test User", password_hash="hashed")
    db_session.add(user)

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    assessments = [
        Assessment(
            id=uuid4(), user_id=user.id, mode=AssessmentMode.full,
            status=AssessmentStatus.completed, final_score=80.0,
            pillar_scores={"P": 85.0, "E": 75.0, "C": 80.0, "A": 78.0, "M": 82.0},
            completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            expires_at=expires
        ),
        Assessment(
            id=uuid4(), user_id=user.id, mode=AssessmentMode.full,
            status=AssessmentStatus.completed, final_score=85.0,
            pillar_scores={"P": 90.0, "E": 80.0, "C": 85.0, "A": 83.0, "M": 87.0},
            completed_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            expires_at=expires
        )
    ]

    for a in assessments:
        db_session.add(a)
    await db_session.commit()

    comparison = await AnalyticsService.get_pillar_comparison(user.id, db_session)

    assert "latest" in comparison
    assert "average" in comparison
    assert comparison["latest"]["P"] == 90.0
    assert comparison["average"]["P"] == 87.5


@pytest.mark.asyncio
async def test_skill_gap_identification(db_session):
    user = User(id=uuid4(), email="test@example.com", name="Test User", password_hash="hashed")
    db_session.add(user)

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    assessment = Assessment(
        id=uuid4(), user_id=user.id, mode=AssessmentMode.full,
        status=AssessmentStatus.completed, final_score=80.0,
        pillar_scores={"P": 90.0, "E": 70.0, "C": 85.0, "A": 65.0, "M": 88.0},
        completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        expires_at=expires
    )
    db_session.add(assessment)
    await db_session.commit()

    gaps = await AnalyticsService.get_skill_gaps(user.id, db_session)

    assert len(gaps) == 2
    assert "A" in gaps
    assert "E" in gaps


@pytest.mark.asyncio
async def test_recommendations_filtered_by_pillar(db_session):
    from sqlalchemy import text

    user = User(id=uuid4(), email="test@example.com", name="Test User", password_hash="hashed")
    db_session.add(user)

    expires = datetime.now(timezone.utc) + timedelta(days=7)
    assessment = Assessment(
        id=uuid4(), user_id=user.id, mode=AssessmentMode.full,
        status=AssessmentStatus.completed, final_score=80.0,
        pillar_scores={"P": 90.0, "E": 70.0, "C": 85.0, "A": 65.0, "M": 88.0},
        completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        expires_at=expires
    )
    db_session.add(assessment)

    await db_session.execute(
        text("""
            INSERT INTO learning_resources (id, title, url, pillar, min_level, max_level, resource_type)
            VALUES (:id, :title, :url, :pillar, :min_level, :max_level, :resource_type)
        """),
        {"id": str(uuid4()), "title": "Efficiency Guide", "url": "http://example.com",
         "pillar": "E", "min_level": 1, "max_level": 5, "resource_type": "article"}
    )
    await db_session.commit()

    recommendations = await AnalyticsService.get_recommendations(user.id, db_session)

    assert len(recommendations) > 0
    assert any(r["pillar"] in ["E", "A"] for r in recommendations)
