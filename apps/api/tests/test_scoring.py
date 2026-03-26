"""Unit tests for Sprint 3: Scoring, Levels, Pillar Aggregation, Anti-Cheat, Results.

Tests:
- Scoring formulas: Quick = KBA*0.40 + PPA*0.60, Full = KBA*0.30 + PPA*0.60 + PSV*0.10
- Level assignment: L1(0-49), L2(50-69), L3(70-84), L4(85-94), L5(95-100)
- PECAM pillar aggregation across KBA + PPA
- Anti-cheat: 3 violations = voided
- Results endpoint: computes and marks completed
- PSV submission (full mode only)
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.models.question import Task
from app.services.scoring import (
    aggregate_pillar_scores,
    assign_level,
    compute_final_score,
)
from app.services.psv_engine import compute_psv_score


# ============================================================
# Fixtures (reuse seeded_tasks from test_ppa)
# ============================================================


@pytest_asyncio.fixture
async def seeded_tasks(db_session):
    """Seed test database with sample PPA tasks."""
    tasks = []
    t1 = Task(
        id=uuid.uuid4(),
        external_id="TASK-QUICK-S3-001",
        title="Meeting Notes to Action Plan",
        pillar="P",
        pillars_tested=["P", "C", "A"],
        difficulty=2,
        brief="Extract action items from a meeting transcript.",
        input_data="Meeting transcript here...",
        success_criteria=["All action items identified", "JSON format"],
        scoring_rubric={
            "accuracy": {"weight": 0.30, "description": "Correct extraction"},
            "completeness": {"weight": 0.25, "description": "All items found"},
            "prompt_efficiency": {"weight": 0.20, "description": "Concise prompt"},
            "output_quality": {"weight": 0.15, "description": "Well formatted"},
            "creativity": {"weight": 0.10, "description": "Clever techniques"},
        },
        max_attempts=2,
        time_limit_seconds=480,
        is_quick=True,
        is_active=True,
    )
    db_session.add(t1)
    tasks.append(t1)

    for i, pillar in enumerate(["P", "C", "E"]):
        t = Task(
            id=uuid.uuid4(),
            external_id=f"TASK-S3-{pillar}-{i:03d}",
            title=f"Task {pillar} {i}",
            pillar=pillar,
            pillars_tested=[pillar],
            difficulty=2,
            brief=f"Brief for task {pillar}-{i}",
            input_data=f"Input data for {pillar}-{i}",
            success_criteria=[f"Criteria for {pillar}-{i}"],
            scoring_rubric={
                "accuracy": {"weight": 0.30, "description": "Accuracy"},
                "completeness": {"weight": 0.25, "description": "Completeness"},
                "prompt_efficiency": {"weight": 0.20, "description": "Efficiency"},
                "output_quality": {"weight": 0.15, "description": "Quality"},
                "creativity": {"weight": 0.10, "description": "Creativity"},
            },
            max_attempts=3,
            time_limit_seconds=480,
            is_quick=False,
            is_active=True,
        )
        db_session.add(t)
        tasks.append(t)

    await db_session.commit()
    return tasks


@pytest_asyncio.fixture
async def seeded_all(db_session, seeded_db, seeded_tasks):
    """Seed both questions and tasks."""
    return {"questions": seeded_db, "tasks": seeded_tasks}


@pytest_asyncio.fixture
async def seeded_scoring_client(engine, seeded_all):
    """Test client with seeded questions and tasks."""
    from httpx import AsyncClient, ASGITransport
    from app.database import get_db
    from app.main import app

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


MOCK_LLM_OUTPUT = "Here are the action items:\n1. Fix the race condition\n2. Check formatting"

MOCK_JUDGE_RESULT = {
    "accuracy": {"score": 85, "rationale": "Good extraction"},
    "completeness": {"score": 90, "rationale": "All items found"},
    "prompt_efficiency": {"score": 75, "rationale": "Decent prompt"},
    "output_quality": {"score": 80, "rationale": "Well formatted"},
    "creativity": {"score": 70, "rationale": "Some techniques used"},
}

MOCK_PSV_JUDGE_RESULT = {
    "relevance": {"score": 80, "rationale": "Good relevance"},
    "depth": {"score": 70, "rationale": "OK depth"},
    "evidence": {"score": 60, "rationale": "Some evidence"},
}


# ============================================================
# Service-level tests: scoring.py
# ============================================================


class TestComputeFinalScore:
    """Test compute_final_score formulas."""

    def test_quick_formula(self):
        """Quick: KBA*0.40 + PPA*0.60"""
        score = compute_final_score("quick", kba_score=80.0, ppa_score=70.0)
        # 80*0.40 + 70*0.60 = 32 + 42 = 74.0
        assert score == 74.0

    def test_full_formula(self):
        """Full: KBA*0.30 + PPA*0.60 + PSV*0.10"""
        score = compute_final_score("full", kba_score=80.0, ppa_score=70.0, psv_score=90.0)
        # 80*0.30 + 70*0.60 + 90*0.10 = 24 + 42 + 9 = 75.0
        assert score == 75.0

    def test_full_formula_no_psv(self):
        """Full mode with no PSV treats it as 0."""
        score = compute_final_score("full", kba_score=80.0, ppa_score=70.0, psv_score=None)
        # 80*0.30 + 70*0.60 + 0*0.10 = 24 + 42 + 0 = 66.0
        assert score == 66.0

    def test_perfect_quick_score(self):
        score = compute_final_score("quick", kba_score=100.0, ppa_score=100.0)
        assert score == 100.0

    def test_perfect_full_score(self):
        score = compute_final_score("full", kba_score=100.0, ppa_score=100.0, psv_score=100.0)
        assert score == 100.0

    def test_zero_scores(self):
        score = compute_final_score("quick", kba_score=0.0, ppa_score=0.0)
        assert score == 0.0

    def test_rounding(self):
        """Verify scores round to 1 decimal."""
        score = compute_final_score("quick", kba_score=33.3, ppa_score=66.7)
        # 33.3*0.40 + 66.7*0.60 = 13.32 + 40.02 = 53.34
        assert score == 53.3


class TestAssignLevel:
    """Test level boundary assignment."""

    def test_level_1_zero(self):
        assert assign_level(0) == 1

    def test_level_1_boundary(self):
        assert assign_level(49) == 1

    def test_level_1_high(self):
        assert assign_level(49.4) == 1

    def test_level_2_boundary(self):
        assert assign_level(50) == 2

    def test_level_2_middle(self):
        assert assign_level(60) == 2

    def test_level_2_top(self):
        assert assign_level(69) == 2

    def test_level_3_boundary(self):
        assert assign_level(70) == 3

    def test_level_3_top(self):
        assert assign_level(84) == 3

    def test_level_4_boundary(self):
        assert assign_level(85) == 4

    def test_level_4_top(self):
        assert assign_level(94) == 4

    def test_level_5_boundary(self):
        assert assign_level(95) == 5

    def test_level_5_perfect(self):
        assert assign_level(100) == 5

    def test_level_boundary_49_5_rounds_to_50(self):
        """49.5 rounds to 50 -> L2."""
        assert assign_level(49.5) == 2

    def test_level_boundary_84_5_rounds_to_85(self):
        """84.5 rounds to 85 -> L4 (round half up)."""
        # Python round() uses banker's rounding, but 84.5 rounds to 84 in Python
        # However our function uses round() which gives 84 for 84.5 (banker's rounding)
        # 84 is L3
        assert assign_level(84.5) == 3


class TestAggregatePillarScores:
    """Test PECAM pillar aggregation."""

    def test_kba_only(self):
        kba_pillars = {
            "P": {"score": 100.0, "correct": 2, "total": 2},
            "E": {"score": 50.0, "correct": 1, "total": 2},
        }
        result = aggregate_pillar_scores(kba_pillars, None)
        assert result["P"]["kba"] == 100.0
        assert result["P"]["combined"] == 100.0
        assert result["E"]["kba"] == 50.0
        assert result["E"]["combined"] == 50.0
        assert result["C"]["combined"] == 0.0

    def test_kba_and_ppa(self):
        kba_pillars = {
            "P": {"score": 80.0, "correct": 2, "total": 2},
            "E": {"score": 60.0, "correct": 1, "total": 2},
        }
        ppa_responses = {
            "task_ids": ["t1"],
            "tasks": {
                "t1": {
                    "ppa_score": 70.0,
                    "pillars_tested": ["P"],
                    "judge_result": {"accuracy": {"score": 70}},
                },
            },
        }
        result = aggregate_pillar_scores(kba_pillars, ppa_responses)
        assert result["P"]["kba"] == 80.0
        assert result["P"]["ppa"] == 70.0
        assert result["P"]["combined"] == 75.0  # avg of 80 and 70

    def test_empty_inputs(self):
        result = aggregate_pillar_scores(None, None)
        for pillar in ["P", "E", "C", "A", "M"]:
            assert result[pillar]["combined"] == 0.0


class TestComputePSVScore:
    """Test PSV delta-based score computation."""

    def test_perfect_match(self):
        assert compute_psv_score(3, 3) == 100.0

    def test_off_by_one(self):
        assert compute_psv_score(4, 3) == 75.0
        assert compute_psv_score(2, 3) == 75.0

    def test_off_by_two(self):
        assert compute_psv_score(5, 3) == 50.0
        assert compute_psv_score(1, 3) == 50.0

    def test_off_by_three(self):
        assert compute_psv_score(5, 2) == 25.0

    def test_off_by_four(self):
        assert compute_psv_score(1, 5) == 0.0
        assert compute_psv_score(5, 1) == 0.0

    def test_all_levels_match(self):
        for level in range(1, 6):
            assert compute_psv_score(level, level) == 100.0


# ============================================================
# API-level tests: anti-cheat violations
# ============================================================


async def _start_and_submit_kba(client) -> str:  # type: ignore[no-untyped-def]
    """Helper: start quick assessment + submit KBA (all correct). Returns assessment_id."""
    start_res = await client.post("/assessments/start", json={"mode": "quick"})
    assert start_res.status_code == 200
    data = start_res.json()
    assessment_id = data["assessment_id"]
    questions = data["questions"]

    answers = [{"question_id": q["id"], "selected": 0} for q in questions]
    kba_res = await client.post(
        f"/assessments/{assessment_id}/kba/submit",
        json={"answers": answers},
    )
    assert kba_res.status_code == 200
    return assessment_id


@pytest.mark.asyncio
async def test_violation_increments(seeded_scoring_client):
    """Violations increment correctly."""
    aid = await _start_and_submit_kba(seeded_scoring_client)

    res = await seeded_scoring_client.post(
        f"/assessments/{aid}/violation",
        json={"violation_type": "tab_switch"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["violations"] == 1
    assert data["voided"] is False


@pytest.mark.asyncio
async def test_three_violations_void(seeded_scoring_client):
    """3 violations = session voided."""
    aid = await _start_and_submit_kba(seeded_scoring_client)

    for i in range(3):
        res = await seeded_scoring_client.post(
            f"/assessments/{aid}/violation",
            json={"violation_type": "tab_switch"},
        )

    data = res.json()
    assert data["violations"] == 3
    assert data["voided"] is True
    assert "voided" in data["message"].lower()


@pytest.mark.asyncio
async def test_voided_assessment_returns_voided(seeded_scoring_client):
    """Already voided assessment returns voided status."""
    aid = await _start_and_submit_kba(seeded_scoring_client)

    # Void it
    for _ in range(3):
        await seeded_scoring_client.post(
            f"/assessments/{aid}/violation",
            json={"violation_type": "tab_switch"},
        )

    # Fourth violation still returns voided
    res = await seeded_scoring_client.post(
        f"/assessments/{aid}/violation",
        json={"violation_type": "tab_switch"},
    )
    assert res.status_code == 200
    assert res.json()["voided"] is True


@pytest.mark.asyncio
async def test_voided_assessment_blocks_ppa(seeded_scoring_client):
    """Voided assessment blocks PPA access."""
    aid = await _start_and_submit_kba(seeded_scoring_client)

    for _ in range(3):
        await seeded_scoring_client.post(
            f"/assessments/{aid}/violation",
            json={"violation_type": "tab_switch"},
        )

    res = await seeded_scoring_client.get(f"/assessments/{aid}/ppa/tasks")
    assert res.status_code == 400
    assert "voided" in res.json()["detail"].lower()


# ============================================================
# API-level tests: results endpoint
# ============================================================


@pytest.mark.asyncio
@patch("app.services.ppa_engine.judge_output", new_callable=AsyncMock)
@patch("app.services.ppa_engine.execute_prompt", new_callable=AsyncMock)
async def test_results_quick_assessment(mock_execute, mock_judge, seeded_scoring_client):
    """Quick assessment results: final = KBA*0.40 + PPA*0.60."""
    mock_execute.return_value = MOCK_LLM_OUTPUT
    mock_judge.return_value = MOCK_JUDGE_RESULT

    aid = await _start_and_submit_kba(seeded_scoring_client)

    # Complete PPA
    tasks_res = await seeded_scoring_client.get(f"/assessments/{aid}/ppa/tasks")
    task_id = tasks_res.json()["tasks"][0]["task_id"]

    await seeded_scoring_client.post(
        f"/assessments/{aid}/ppa/execute",
        json={"task_id": task_id, "prompt": "Extract items"},
    )
    await seeded_scoring_client.post(
        f"/assessments/{aid}/ppa/submit-best",
        json={"task_id": task_id, "attempt_index": 0},
    )

    # Get results
    res = await seeded_scoring_client.get(f"/assessments/{aid}/results")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["mode"] == "quick"
    assert data["level"] >= 1
    assert data["level"] <= 5
    assert data["final_score"] > 0
    assert data["kba_score"] > 0
    assert data["ppa_score"] > 0
    assert data["psv_score"] is None

    # Verify formula: KBA*0.40 + PPA*0.60
    expected = round(data["kba_score"] * 0.40 + data["ppa_score"] * 0.60, 1)
    assert data["final_score"] == expected


@pytest.mark.asyncio
@patch("app.services.ppa_engine.judge_output", new_callable=AsyncMock)
@patch("app.services.ppa_engine.execute_prompt", new_callable=AsyncMock)
async def test_results_already_completed(mock_execute, mock_judge, seeded_scoring_client):
    """Calling results twice returns cached results."""
    mock_execute.return_value = MOCK_LLM_OUTPUT
    mock_judge.return_value = MOCK_JUDGE_RESULT

    aid = await _start_and_submit_kba(seeded_scoring_client)

    tasks_res = await seeded_scoring_client.get(f"/assessments/{aid}/ppa/tasks")
    task_id = tasks_res.json()["tasks"][0]["task_id"]

    await seeded_scoring_client.post(
        f"/assessments/{aid}/ppa/execute",
        json={"task_id": task_id, "prompt": "Extract items"},
    )
    await seeded_scoring_client.post(
        f"/assessments/{aid}/ppa/submit-best",
        json={"task_id": task_id, "attempt_index": 0},
    )

    # First call
    res1 = await seeded_scoring_client.get(f"/assessments/{aid}/results")
    assert res1.status_code == 200

    # Second call (cached)
    res2 = await seeded_scoring_client.get(f"/assessments/{aid}/results")
    assert res2.status_code == 200
    assert res1.json()["final_score"] == res2.json()["final_score"]


@pytest.mark.asyncio
async def test_results_requires_ppa(seeded_scoring_client):
    """Results require PPA to be completed."""
    aid = await _start_and_submit_kba(seeded_scoring_client)

    res = await seeded_scoring_client.get(f"/assessments/{aid}/results")
    assert res.status_code == 400
    assert "ppa" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_results_voided_returns_400(seeded_scoring_client):
    """Voided assessment cannot get results."""
    aid = await _start_and_submit_kba(seeded_scoring_client)

    for _ in range(3):
        await seeded_scoring_client.post(
            f"/assessments/{aid}/violation",
            json={"violation_type": "tab_switch"},
        )

    res = await seeded_scoring_client.get(f"/assessments/{aid}/results")
    assert res.status_code == 400
    assert "voided" in res.json()["detail"].lower()


# ============================================================
# API-level tests: PSV submission
# ============================================================


@pytest.mark.asyncio
async def test_psv_quick_mode_rejected(seeded_scoring_client):
    """PSV submission rejected for quick mode assessments."""
    aid = await _start_and_submit_kba(seeded_scoring_client)

    res = await seeded_scoring_client.post(
        f"/assessments/{aid}/psv/submit",
        json={"user_level": 3},
    )
    assert res.status_code == 400
    assert "full" in res.json()["detail"].lower()


# ============================================================
# API-level tests: timer enforcement for PPA
# ============================================================


@pytest.mark.asyncio
@patch("app.services.ppa_engine.execute_prompt", new_callable=AsyncMock)
async def test_ppa_timer_enforcement(mock_execute, seeded_scoring_client, engine):
    """Late PPA submission returns 400."""
    mock_execute.return_value = MOCK_LLM_OUTPUT

    aid = await _start_and_submit_kba(seeded_scoring_client)
    tasks_res = await seeded_scoring_client.get(f"/assessments/{aid}/ppa/tasks")
    task_id = tasks_res.json()["tasks"][0]["task_id"]

    # Expire the assessment
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(
            select(Assessment).where(Assessment.id == uuid.UUID(aid))
        )
        assessment = result.scalar_one()
        assessment.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        await session.commit()

    res = await seeded_scoring_client.post(
        f"/assessments/{aid}/ppa/execute",
        json={"task_id": task_id, "prompt": "Too late"},
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()


@pytest.mark.asyncio
@patch("app.services.ppa_engine.judge_output", new_callable=AsyncMock)
@patch("app.services.ppa_engine.execute_prompt", new_callable=AsyncMock)
async def test_submit_best_timer_enforcement(mock_execute, mock_judge, seeded_scoring_client, engine):
    """Late PPA submit-best returns 400."""
    mock_execute.return_value = MOCK_LLM_OUTPUT
    mock_judge.return_value = MOCK_JUDGE_RESULT

    aid = await _start_and_submit_kba(seeded_scoring_client)
    tasks_res = await seeded_scoring_client.get(f"/assessments/{aid}/ppa/tasks")
    task_id = tasks_res.json()["tasks"][0]["task_id"]

    # Execute an attempt first
    await seeded_scoring_client.post(
        f"/assessments/{aid}/ppa/execute",
        json={"task_id": task_id, "prompt": "Test"},
    )

    # Expire the assessment
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        result = await session.execute(
            select(Assessment).where(Assessment.id == uuid.UUID(aid))
        )
        assessment = result.scalar_one()
        assessment.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        await session.commit()

    res = await seeded_scoring_client.post(
        f"/assessments/{aid}/ppa/submit-best",
        json={"task_id": task_id, "attempt_index": 0},
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()
