"""Assessment router: start, KBA submit, PPA execute, PSV submit, results."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.models.question import Question
from app.services.kba_engine import (
    check_timer_expired,
    expire_assessment,
    score_kba,
    select_questions,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


# --- Request/Response schemas ---


class StartAssessmentRequest(BaseModel):
    mode: str  # "quick" or "full"
    industry: str | None = None
    role: str | None = None


class QuestionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    text: str
    options: list[str]
    pillar: str


class StartAssessmentResponse(BaseModel):
    assessment_id: str
    mode: str
    expires_at: str
    questions: list[QuestionOut]


class KBAAnswer(BaseModel):
    question_id: str
    selected: int


class SubmitKBARequest(BaseModel):
    answers: list[KBAAnswer]


class PillarScoreOut(BaseModel):
    score: float
    correct: int
    total: int


class SubmitKBAResponse(BaseModel):
    kba_score: float
    total_correct: int
    total_questions: int
    pillar_scores: dict[str, PillarScoreOut]


# --- Endpoints ---


@router.post("/start", response_model=StartAssessmentResponse)
async def start_assessment(
    body: StartAssessmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start a new assessment (quick or full). No auth required."""
    if body.mode not in ("quick", "full"):
        raise HTTPException(status_code=400, detail="mode must be 'quick' or 'full'")

    # Select questions
    questions = await select_questions(db, body.mode)
    if not questions:
        raise HTTPException(status_code=500, detail="No questions available. Run the seed script first.")

    # Calculate expiry
    if body.mode == "quick":
        time_limit = settings.quick_assessment_time_limit
    else:
        time_limit = settings.full_kba_time_limit

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=time_limit)

    # Create assessment
    assessment = Assessment(
        id=uuid.uuid4(),
        mode=AssessmentMode(body.mode),
        status=AssessmentStatus.in_progress,
        industry=body.industry,
        role=body.role,
        started_at=now,
        expires_at=expires_at,
        kba_responses={"question_ids": [str(q.id) for q in questions]},
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    # Return questions WITHOUT correct_answer or explanation
    questions_out = [
        QuestionOut(
            id=str(q.id),
            text=q.question_text,
            options=q.options,
            pillar=q.pillar,
        )
        for q in questions
    ]

    return StartAssessmentResponse(
        assessment_id=str(assessment.id),
        mode=body.mode,
        expires_at=expires_at.isoformat(),
        questions=questions_out,
    )


@router.post("/{assessment_id}/kba/submit", response_model=SubmitKBAResponse)
async def submit_kba(
    assessment_id: str,
    body: SubmitKBARequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit KBA answers. Returns score + per-pillar breakdown."""
    # Load assessment
    try:
        aid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assessment ID")

    result = await db.execute(select(Assessment).where(Assessment.id == aid))
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.status == AssessmentStatus.expired:
        raise HTTPException(status_code=400, detail="Assessment has expired")

    if assessment.status == AssessmentStatus.voided:
        raise HTTPException(status_code=400, detail="Assessment has been voided")

    if assessment.kba_score is not None:
        raise HTTPException(status_code=400, detail="KBA already submitted for this assessment")

    # Check timer
    if check_timer_expired(assessment):
        await expire_assessment(db, assessment)
        raise HTTPException(status_code=400, detail="Assessment has expired")

    # Load the questions that were assigned to this assessment
    question_ids_str = assessment.kba_responses.get("question_ids", []) if assessment.kba_responses else []
    question_ids = [uuid.UUID(qid) for qid in question_ids_str]

    result = await db.execute(select(Question).where(Question.id.in_(question_ids)))
    questions = result.scalars().all()
    questions_by_id = {str(q.id): q for q in questions}

    # Score
    answers_dicts = [{"question_id": a.question_id, "selected": a.selected} for a in body.answers]
    kba_result = score_kba(answers_dicts, questions_by_id)

    # Update assessment
    assessment.kba_score = kba_result["total_score"]
    assessment.kba_responses = {
        "question_ids": question_ids_str,
        "answers": [a.model_dump() for a in body.answers],
    }
    assessment.pillar_scores = kba_result["pillar_scores"]
    await db.commit()

    return SubmitKBAResponse(
        kba_score=kba_result["total_score"],
        total_correct=kba_result["total_correct"],
        total_questions=kba_result["total_questions"],
        pillar_scores={
            p: PillarScoreOut(**data) for p, data in kba_result["pillar_scores"].items()
        },
    )


@router.post("/{assessment_id}/ppa/execute")
async def execute_ppa(assessment_id: str):
    """Execute a prompt in PPA sandbox."""
    return {"message": "not implemented"}


@router.post("/{assessment_id}/psv/submit")
async def submit_psv(assessment_id: str):
    """Submit PSV portfolio entry."""
    return {"message": "not implemented"}


@router.get("/{assessment_id}/results")
async def get_results(assessment_id: str):
    """Get assessment results and badge."""
    return {"message": "not implemented"}
