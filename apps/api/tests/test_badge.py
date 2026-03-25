"""Unit tests for Sprint 4: Badge claim + verify.

Tests:
- Claim: register + claim creates badge with SVG
- Claim: login + claim works for existing user
- Claim: duplicate claim returns 409
- Claim: non-completed assessment returns 400
- Verify: public endpoint returns badge data
- Verify: invalid badge ID returns 404
- Badge SVG: contains level, score, radar, date, mode label
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.services.badge_service import generate_badge_svg


# ============================================================
# Badge SVG generation tests
# ============================================================


def test_badge_svg_contains_level():
    """Badge SVG includes level text."""
    svg = generate_badge_svg(
        level=3,
        level_name="Proficient",
        final_score=75.5,
        pillar_scores={"P": {"combined": 80}, "E": {"combined": 70}, "C": {"combined": 75}, "A": {"combined": 72}, "M": {"combined": 78}},
        issued_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        mode="quick",
        badge_id="test-id",
    )
    assert "L3" in svg
    assert "Proficient" in svg


def test_badge_svg_contains_score():
    """Badge SVG includes final score."""
    svg = generate_badge_svg(
        level=4,
        level_name="Expert",
        final_score=88.3,
        pillar_scores={"P": {"combined": 90}, "E": {"combined": 85}, "C": {"combined": 88}, "A": {"combined": 87}, "M": {"combined": 92}},
        issued_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        mode="full",
        badge_id="test-id",
    )
    assert "88" in svg
    assert "FINAL SCORE" in svg


def test_badge_svg_contains_date():
    """Badge SVG includes issue date."""
    svg = generate_badge_svg(
        level=2,
        level_name="Practitioner",
        final_score=55.0,
        pillar_scores={"P": {"combined": 60}, "E": {"combined": 50}, "C": {"combined": 55}, "A": {"combined": 52}, "M": {"combined": 58}},
        issued_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        mode="quick",
        badge_id="test-id",
    )
    assert "2026-03-25" in svg


def test_badge_svg_contains_mode_label_estimated():
    """Quick mode badge shows 'Estimated'."""
    svg = generate_badge_svg(
        level=1,
        level_name="Novice",
        final_score=30.0,
        pillar_scores={"P": {"combined": 30}, "E": {"combined": 25}, "C": {"combined": 35}, "A": {"combined": 28}, "M": {"combined": 32}},
        issued_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        mode="quick",
        badge_id="test-id",
    )
    assert "Estimated" in svg


def test_badge_svg_contains_mode_label_certified():
    """Full mode badge shows 'Certified'."""
    svg = generate_badge_svg(
        level=5,
        level_name="Master",
        final_score=97.0,
        pillar_scores={"P": {"combined": 98}, "E": {"combined": 96}, "C": {"combined": 97}, "A": {"combined": 95}, "M": {"combined": 99}},
        issued_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        mode="full",
        badge_id="test-id",
    )
    assert "Certified" in svg


def test_badge_svg_contains_radar_points():
    """Badge SVG contains radar chart polygon."""
    svg = generate_badge_svg(
        level=3,
        level_name="Proficient",
        final_score=75.0,
        pillar_scores={"P": {"combined": 80}, "E": {"combined": 70}, "C": {"combined": 75}, "A": {"combined": 72}, "M": {"combined": 78}},
        issued_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        mode="quick",
        badge_id="test-id",
    )
    assert "<polygon" in svg
    assert "fill=\"rgba(0,255,65,0.2)\"" in svg


def test_badge_svg_contains_verification_url():
    """Badge SVG contains verification URL."""
    svg = generate_badge_svg(
        level=3,
        level_name="Proficient",
        final_score=75.0,
        pillar_scores={"P": {"combined": 80}, "E": {"combined": 70}, "C": {"combined": 75}, "A": {"combined": 72}, "M": {"combined": 78}},
        issued_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        mode="quick",
        badge_id="abc-123",
    )
    assert "/badges/verify/abc-123" in svg


# ============================================================
# Helpers
# ============================================================


async def _create_completed_assessment(db_session: AsyncSession) -> Assessment:
    """Create a completed assessment for testing."""
    assessment = Assessment(
        id=uuid.uuid4(),
        mode=AssessmentMode.quick,
        status=AssessmentStatus.completed,
        kba_score=80.0,
        ppa_score=70.0,
        final_score=74.0,
        level=3,
        pillar_scores={"P": {"kba": 80, "ppa": 70, "combined": 75}, "E": {"kba": 75, "ppa": 65, "combined": 70}, "C": {"kba": 85, "ppa": 75, "combined": 80}, "A": {"kba": 78, "ppa": 68, "combined": 73}, "M": {"kba": 82, "ppa": 72, "combined": 77}},
        started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        completed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db_session.add(assessment)
    await db_session.commit()
    await db_session.refresh(assessment)
    return assessment


# ============================================================
# Integration tests: Claim endpoint
# ============================================================


@pytest.mark.asyncio
async def test_claim_register_creates_badge(client, db_session):
    """Register + claim creates badge and returns SVG."""
    assessment = await _create_completed_assessment(db_session)

    resp = await client.post(f"/assessments/{assessment.id}/claim", json={
        "email": "claimuser@test.com",
        "password": "password123",
        "name": "Claim User",
        "is_login": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "badge_id" in data
    assert "badge_svg" in data
    assert "<svg" in data["badge_svg"]
    assert "token" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_claim_login_existing_user(client, db_session):
    """Existing user can login and claim."""
    # Register first
    await client.post("/auth/register", json={
        "email": "existing@test.com",
        "name": "Existing User",
        "password": "password123",
    })

    assessment = await _create_completed_assessment(db_session)

    resp = await client.post(f"/assessments/{assessment.id}/claim", json={
        "email": "existing@test.com",
        "password": "password123",
        "is_login": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "badge_id" in data
    assert "<svg" in data["badge_svg"]


@pytest.mark.asyncio
async def test_claim_duplicate_returns_409(client, db_session):
    """Can't claim the same assessment twice."""
    assessment = await _create_completed_assessment(db_session)

    # First claim
    resp1 = await client.post(f"/assessments/{assessment.id}/claim", json={
        "email": "dup_claim@test.com",
        "password": "password123",
        "name": "Dup User",
        "is_login": False,
    })
    assert resp1.status_code == 200

    # Second claim
    resp2 = await client.post(f"/assessments/{assessment.id}/claim", json={
        "email": "dup_claim@test.com",
        "password": "password123",
        "is_login": True,
    })
    assert resp2.status_code == 409
    assert "already claimed" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_claim_non_completed_assessment(client, db_session):
    """Can't claim an in-progress assessment."""
    assessment = Assessment(
        id=uuid.uuid4(),
        mode=AssessmentMode.quick,
        status=AssessmentStatus.in_progress,
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db_session.add(assessment)
    await db_session.commit()

    resp = await client.post(f"/assessments/{assessment.id}/claim", json={
        "email": "nope@test.com",
        "password": "password123",
        "name": "Nope",
        "is_login": False,
    })
    assert resp.status_code == 400
    assert "not completed" in resp.json()["detail"]


# ============================================================
# Integration tests: Verify endpoint
# ============================================================


@pytest.mark.asyncio
async def test_verify_returns_badge_data(client, db_session):
    """Verify endpoint returns badge details."""
    assessment = await _create_completed_assessment(db_session)

    # Claim first
    claim_resp = await client.post(f"/assessments/{assessment.id}/claim", json={
        "email": "verify_test@test.com",
        "password": "password123",
        "name": "Verify User",
        "is_login": False,
    })
    badge_id = claim_resp.json()["badge_id"]

    # Verify
    resp = await client.get(f"/badges/verify/{badge_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["badge_id"] == badge_id
    assert data["valid"] is True
    assert data["level"] == 3
    assert data["level_name"] == "Proficient"
    assert data["final_score"] == 74.0
    assert "<svg" in data["badge_svg"]


@pytest.mark.asyncio
async def test_verify_invalid_badge_404(client):
    """Verify endpoint returns 404 for unknown badge."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/badges/verify/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_verify_bad_uuid_400(client):
    """Verify endpoint returns 400 for invalid UUID."""
    resp = await client.get("/badges/verify/not-a-uuid")
    assert resp.status_code == 400
