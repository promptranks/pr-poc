"""Unit tests for Sprint 1: Assessment Session + KBA Engine.

Tests:
- test_start_assessment_quick: Quick mode returns 10 questions (2 per pillar)
- test_start_assessment_full: Full mode returns 20 questions (4 per pillar)
- test_questions_exclude_answers: Response does not include correct_answer or explanation
- test_kba_scoring: Correct score calculation
- test_kba_pillar_balance: 2 questions per pillar in quick mode
- test_timer_expiry: Expired session returns 400 error
- test_kba_double_submit: Cannot submit KBA twice
- test_invalid_mode: Invalid mode returns 400
"""

import uuid
from datetime import datetime, timedelta, timezone
from collections import Counter

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.services.kba_engine import score_kba, check_timer_expired, select_questions


# ============================================================
# Service-level tests (unit tests on kba_engine functions)
# ============================================================


@pytest.mark.asyncio
async def test_select_questions_quick(db_session, seeded_db):
    """Quick mode selects 10 questions: 2 per pillar (1 easy + 1 medium)."""
    questions = await select_questions(db_session, "quick")
    assert len(questions) == 10

    pillar_counts = Counter(q.pillar for q in questions)
    for pillar in ["P", "E", "C", "M", "A"]:
        assert pillar_counts[pillar] == 2, f"Pillar {pillar} has {pillar_counts[pillar]}, expected 2"


@pytest.mark.asyncio
async def test_select_questions_full(db_session, seeded_db):
    """Full mode selects 20 questions: 4 per pillar."""
    questions = await select_questions(db_session, "full")
    assert len(questions) == 20

    pillar_counts = Counter(q.pillar for q in questions)
    for pillar in ["P", "E", "C", "M", "A"]:
        assert pillar_counts[pillar] == 4, f"Pillar {pillar} has {pillar_counts[pillar]}, expected 4"


@pytest.mark.asyncio
async def test_select_questions_quick_difficulty(db_session, seeded_db):
    """Quick mode: each pillar has 1 easy (diff=1) + 1 medium (diff=2)."""
    questions = await select_questions(db_session, "quick")
    for pillar in ["P", "E", "C", "M", "A"]:
        pillar_qs = [q for q in questions if q.pillar == pillar]
        difficulties = sorted([q.difficulty for q in pillar_qs])
        assert difficulties == [1, 2], f"Pillar {pillar}: expected [1,2], got {difficulties}"


def test_score_kba_perfect():
    """All correct answers yield 100% score."""

    class MockQ:
        def __init__(self, qid, pillar, correct):
            self.id = qid
            self.pillar = pillar
            self.correct_answer = correct

    questions_by_id = {
        "q1": MockQ("q1", "P", 0),
        "q2": MockQ("q2", "P", 1),
        "q3": MockQ("q3", "E", 2),
        "q4": MockQ("q4", "E", 3),
    }

    answers = [
        {"question_id": "q1", "selected": 0},
        {"question_id": "q2", "selected": 1},
        {"question_id": "q3", "selected": 2},
        {"question_id": "q4", "selected": 3},
    ]

    result = score_kba(answers, questions_by_id)
    assert result["total_score"] == 100.0
    assert result["total_correct"] == 4
    assert result["total_questions"] == 4
    assert result["pillar_scores"]["P"]["score"] == 100.0
    assert result["pillar_scores"]["E"]["score"] == 100.0


def test_score_kba_partial():
    """Partial correct answers yield proportional score."""

    class MockQ:
        def __init__(self, qid, pillar, correct):
            self.id = qid
            self.pillar = pillar
            self.correct_answer = correct

    questions_by_id = {
        "q1": MockQ("q1", "P", 0),
        "q2": MockQ("q2", "P", 1),
        "q3": MockQ("q3", "E", 2),
        "q4": MockQ("q4", "E", 3),
    }

    answers = [
        {"question_id": "q1", "selected": 0},  # correct
        {"question_id": "q2", "selected": 0},  # wrong
        {"question_id": "q3", "selected": 2},  # correct
        {"question_id": "q4", "selected": 0},  # wrong
    ]

    result = score_kba(answers, questions_by_id)
    assert result["total_score"] == 50.0
    assert result["total_correct"] == 2
    assert result["pillar_scores"]["P"]["score"] == 50.0
    assert result["pillar_scores"]["P"]["correct"] == 1
    assert result["pillar_scores"]["E"]["score"] == 50.0
    assert result["pillar_scores"]["E"]["correct"] == 1


def test_score_kba_zero():
    """All wrong answers yield 0% score."""

    class MockQ:
        def __init__(self, qid, pillar, correct):
            self.id = qid
            self.pillar = pillar
            self.correct_answer = correct

    questions_by_id = {
        "q1": MockQ("q1", "P", 0),
        "q2": MockQ("q2", "E", 1),
    }

    answers = [
        {"question_id": "q1", "selected": 3},
        {"question_id": "q2", "selected": 3},
    ]

    result = score_kba(answers, questions_by_id)
    assert result["total_score"] == 0.0
    assert result["total_correct"] == 0


def test_check_timer_not_expired():
    """Assessment with future expires_at is not expired."""

    class MockAssessment:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    assert check_timer_expired(MockAssessment()) is False


def test_check_timer_expired():
    """Assessment with past expires_at is expired."""

    class MockAssessment:
        expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    assert check_timer_expired(MockAssessment()) is True


def test_check_timer_naive_datetime():
    """Timer check handles naive datetimes (from SQLite)."""

    class MockAssessment:
        expires_at = datetime.utcnow() - timedelta(minutes=1)

    assert check_timer_expired(MockAssessment()) is True


# ============================================================
# API-level tests (integration tests via HTTP client)
# ============================================================


@pytest.mark.asyncio
async def test_start_assessment_quick(seeded_client):
    """POST /assessments/start with mode=quick returns 10 questions."""
    res = await seeded_client.post("/assessments/start", json={"mode": "quick"})
    assert res.status_code == 200

    data = res.json()
    assert "assessment_id" in data
    assert data["mode"] == "quick"
    assert "expires_at" in data
    assert len(data["questions"]) == 10


@pytest.mark.asyncio
async def test_start_assessment_full(seeded_client):
    """POST /assessments/start with mode=full returns 20 questions."""
    res = await seeded_client.post("/assessments/start", json={"mode": "full"})
    assert res.status_code == 200

    data = res.json()
    assert len(data["questions"]) == 20


@pytest.mark.asyncio
async def test_questions_exclude_answers(seeded_client):
    """Questions response does NOT include correct_answer or explanation."""
    res = await seeded_client.post("/assessments/start", json={"mode": "quick"})
    data = res.json()

    for q in data["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q
        assert "correct" not in q
        # Should have: id, text, options, pillar
        assert "id" in q
        assert "text" in q
        assert "options" in q
        assert "pillar" in q


@pytest.mark.asyncio
async def test_kba_pillar_balance(seeded_client):
    """Quick mode returns exactly 2 questions per pillar."""
    res = await seeded_client.post("/assessments/start", json={"mode": "quick"})
    data = res.json()

    pillar_counts = Counter(q["pillar"] for q in data["questions"])
    for pillar in ["P", "E", "C", "M", "A"]:
        assert pillar_counts[pillar] == 2, f"Pillar {pillar}: {pillar_counts[pillar]}, expected 2"


@pytest.mark.asyncio
async def test_kba_submit_scoring(seeded_client):
    """Submit KBA answers and get correct score."""
    # Start assessment
    start_res = await seeded_client.post("/assessments/start", json={"mode": "quick"})
    start_data = start_res.json()
    assessment_id = start_data["assessment_id"]
    questions = start_data["questions"]

    # Answer all with option 0 (which is correct in seeded data)
    answers = [{"question_id": q["id"], "selected": 0} for q in questions]

    res = await seeded_client.post(
        f"/assessments/{assessment_id}/kba/submit",
        json={"answers": answers},
    )
    assert res.status_code == 200

    data = res.json()
    assert data["kba_score"] == 100.0
    assert data["total_correct"] == 10
    assert data["total_questions"] == 10
    assert "pillar_scores" in data
    for pillar in ["P", "E", "C", "M", "A"]:
        assert pillar in data["pillar_scores"]
        assert data["pillar_scores"][pillar]["score"] == 100.0


@pytest.mark.asyncio
async def test_kba_submit_partial(seeded_client):
    """Submit KBA with some wrong answers gives partial score."""
    start_res = await seeded_client.post("/assessments/start", json={"mode": "quick"})
    start_data = start_res.json()
    assessment_id = start_data["assessment_id"]
    questions = start_data["questions"]

    # First 5 correct (option 0), last 5 wrong (option 1)
    answers = []
    for i, q in enumerate(questions):
        answers.append({"question_id": q["id"], "selected": 0 if i < 5 else 1})

    res = await seeded_client.post(
        f"/assessments/{assessment_id}/kba/submit",
        json={"answers": answers},
    )
    assert res.status_code == 200

    data = res.json()
    assert data["kba_score"] == 50.0
    assert data["total_correct"] == 5


@pytest.mark.asyncio
async def test_kba_double_submit(seeded_client):
    """Cannot submit KBA twice for the same assessment."""
    start_res = await seeded_client.post("/assessments/start", json={"mode": "quick"})
    start_data = start_res.json()
    assessment_id = start_data["assessment_id"]
    questions = start_data["questions"]

    answers = [{"question_id": q["id"], "selected": 0} for q in questions]

    # First submit
    res1 = await seeded_client.post(
        f"/assessments/{assessment_id}/kba/submit",
        json={"answers": answers},
    )
    assert res1.status_code == 200

    # Second submit
    res2 = await seeded_client.post(
        f"/assessments/{assessment_id}/kba/submit",
        json={"answers": answers},
    )
    assert res2.status_code == 400
    assert "already submitted" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_timer_expiry(seeded_client, engine):
    """Expired assessment returns 400 on KBA submit."""
    # Start assessment first
    start_res = await seeded_client.post("/assessments/start", json={"mode": "quick"})
    start_data = start_res.json()
    assessment_id = start_data["assessment_id"]
    questions = start_data["questions"]

    # Manually expire the assessment in DB
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(
            select(Assessment).where(Assessment.id == uuid.UUID(assessment_id))
        )
        assessment = result.scalar_one()
        assessment.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        await session.commit()

    # Try to submit
    answers = [{"question_id": q["id"], "selected": 0} for q in questions]
    res = await seeded_client.post(
        f"/assessments/{assessment_id}/kba/submit",
        json={"answers": answers},
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_mode(seeded_client):
    """Invalid mode returns 400."""
    res = await seeded_client.post("/assessments/start", json={"mode": "invalid"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_assessment_not_found(seeded_client):
    """Submit to non-existent assessment returns 404."""
    fake_id = str(uuid.uuid4())
    res = await seeded_client.post(
        f"/assessments/{fake_id}/kba/submit",
        json={"answers": []},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_start_with_industry_role(seeded_client):
    """Start assessment with optional industry and role."""
    res = await seeded_client.post("/assessments/start", json={
        "mode": "quick",
        "industry": "Technology",
        "role": "Software Engineer",
    })
    assert res.status_code == 200
    assert len(res.json()["questions"]) == 10
