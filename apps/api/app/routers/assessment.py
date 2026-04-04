"""Assessment router: start, KBA submit, PPA execute, PSV submit, results, violations."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.config import settings
from app.database import get_db
from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.models.badge import Badge
from app.models.question import Question, Task
from app.models.user import User
from app.models.pending_assessment import PendingAssessment
from app.services.kba_engine import (
    check_timer_expired,
    expire_assessment,
    score_kba,
    select_questions,
)
from app.services.ppa_engine import (
    compute_ppa_score,
    execute_task_prompt,
    get_attempt_count,
    get_max_attempts,
    get_task_brief,
    judge_task_output,
    select_tasks,
    store_attempt,
)
from app.models.psv_sample import PsvSample
from app.services.psv_engine import select_psv_sample, compute_psv_score
from app.services.auth_service import (
    create_access_token,
    create_user,
    get_user_by_email,
    verify_password,
)
from app.services.badge_service import create_badge
from app.services.scoring import aggregate_pillar_scores, assign_level, compute_final_score
from app.services.redis_client import get_redis
from app.services.leaderboard_service import update_score, LEVEL_NAMES
from app.services.usage_service import UsageService
from app.middleware.auth import get_current_user_optional, get_current_user

router = APIRouter(prefix="/assessments", tags=["assessments"])


# --- Helper functions ---


def _check_premium_required(industry: str | None, role: str | None, mode: str) -> bool:
    """Check if industry/role combination requires premium subscription."""
    # Premium required for specific industries
    premium_industries = ["healthcare", "finance", "legal", "enterprise"]
    if industry and industry.lower() in premium_industries:
        return True
    # Full mode always requires premium for certain roles
    premium_roles = ["architect", "director", "vp", "cto", "ciso"]
    if mode == "full" and role and role.lower() in premium_roles:
        return True
    return False


# --- Request/Response schemas ---


class StartAssessmentRequest(BaseModel):
    mode: str  # "quick" or "full"
    industry: str | None = None
    role: str | None = None
    industry_id: str | None = None
    role_id: str | None = None
    session_id: str | None = None  # For resuming pending assessments


class PendingAssessmentRequest(BaseModel):
    industry: str
    role: str
    mode: str  # "quick" or "full"
    session_id: str
    user_id: str | None = None


class PendingAssessmentResponse(BaseModel):
    id: str
    industry: str
    role: str
    mode: str
    status: str
    assessment_id: str | None = None


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


class PPAExecuteRequest(BaseModel):
    task_id: str
    prompt: str


class PPAExecuteResponse(BaseModel):
    task_id: str
    attempt_number: int
    output: str
    attempts_used: int
    max_attempts: int


class PPASubmitBestRequest(BaseModel):
    task_id: str
    attempt_index: int  # 0-based index of the best attempt


class DimensionScore(BaseModel):
    score: int
    rationale: str


class PPASubmitBestResponse(BaseModel):
    task_id: str
    ppa_score: float
    dimensions: dict[str, DimensionScore]


class PPATasksResponse(BaseModel):
    tasks: list[dict[str, Any]]


class PSVSampleResponse(BaseModel):
    sample_id: str
    title: str
    pillar: str
    difficulty: int
    task_context: str
    prompt_text: str
    output_text: str
    # NOTE: ground_truth_level is NOT exposed


class PSVSubmitRequest(BaseModel):
    user_level: int  # 1-5 PECAM level rating


class PSVSubmitResponse(BaseModel):
    psv_score: float
    user_level: int
    ground_truth_level: int
    delta: int


class ViolationRequest(BaseModel):
    violation_type: str  # "tab_switch", "copy_paste", etc.


class ViolationResponse(BaseModel):
    violations: int
    voided: bool
    message: str


class ResultsResponse(BaseModel):
    assessment_id: str
    mode: str
    status: str
    results_locked: bool
    final_score: float
    level: int
    kba_score: float
    ppa_score: float
    psv_score: float | None
    pillar_scores: dict[str, dict[str, float]]
    completed_at: str


class ClaimRequest(BaseModel):
    email: str | None = None
    password: str | None = None
    name: str = ""
    is_login: bool = False  # True = login existing user, False = register new


class ClaimResponse(BaseModel):
    badge_id: str
    badge_svg: str
    verification_url: str
    token: str
    user_id: str


# --- Endpoints ---


@router.post("/start", response_model=StartAssessmentResponse)
async def start_assessment(
    body: StartAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Start a new assessment (quick or full). Checks for pending assessment and premium requirements."""
    if body.mode not in ("quick", "full"):
        raise HTTPException(status_code=400, detail="mode must be 'quick' or 'full'")

    # Check for pending assessment to resume
    pending = None
    if body.session_id:
        result = await db.execute(
            select(PendingAssessment).where(PendingAssessment.session_id == body.session_id)
        )
        pending = result.scalar_one_or_none()

    # Use pending assessment data if available
    if pending:
        body.industry = pending.industry
        body.role = pending.role
        body.mode = pending.mode

    # Premium gating - single decision point
    requires_premium = _check_premium_required(body.industry, body.role, body.mode)
    if requires_premium:
        user_tier = current_user.subscription_tier if current_user else "free"
        if user_tier not in ("premium", "enterprise"):
            raise HTTPException(
                status_code=402,
                detail="Premium subscription required for this industry/role combination"
            )

    # Check usage limits for premium features
    results_locked = False

    # Determine if premium features are used
    premium_features_used = (
        body.mode == "full" or
        body.industry_id is not None or
        body.role_id is not None
    )

    if premium_features_used:
        if current_user:
            tier = current_user.subscription_tier

            if tier == "premium":
                # Premium users: check limit and increment
                can_start, used, limit = await UsageService.check_limit(
                    str(current_user.id), tier, db
                )
                if not can_start:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Assessment limit reached ({used}/{limit}). Upgrade to Enterprise for unlimited access."
                    )
                await UsageService.increment_usage(str(current_user.id), tier, db)

            elif tier == "free":
                # Free users: check 1 trial limit
                can_start, used, limit = await UsageService.check_limit(
                    str(current_user.id), tier, db
                )
                if not can_start:
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "message": "Free trial used. Upgrade to Premium for 3 full assessments per month.",
                            "used": used,
                            "limit": limit,
                            "upgrade_required": True
                        }
                    )
                # Allow this attempt but lock results
                await UsageService.increment_usage(str(current_user.id), tier, db)
                results_locked = True

            # enterprise: no limit, results_locked stays False
        else:
            # Anonymous user: allow but lock results
            results_locked = True

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
    industry_uuid = None
    role_uuid = None
    if body.industry_id:
        try:
            industry_uuid = uuid.UUID(body.industry_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid industry_id")
    if body.role_id:
        try:
            role_uuid = uuid.UUID(body.role_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role_id")

    assessment = Assessment(
        id=uuid.uuid4(),
        user_id=current_user.id if current_user else None,
        mode=AssessmentMode(body.mode),
        status=AssessmentStatus.in_progress,
        industry=body.industry,
        role=body.role,
        industry_id=industry_uuid,
        role_id=role_uuid,
        started_at=now,
        expires_at=expires_at,
        results_locked=results_locked,
        kba_responses={"question_ids": [str(q.id) for q in questions]},
    )
    db.add(assessment)

    # Update pending assessment if exists
    if pending:
        pending.status = "in_progress"
        pending.assessment_id = assessment.id
        pending.updated_at = now

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
    current_user: User | None = Depends(get_current_user_optional),
):
    """Submit KBA answers. Returns score + per-pillar breakdown."""
    # Load assessment and verify ownership
    assessment = await _load_assessment(db, assessment_id)
    await _verify_assessment_ownership(assessment, current_user)

    if assessment.status == "expired":
        raise HTTPException(status_code=400, detail="Assessment has expired")

    if assessment.status == "voided":
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

    # Check if results are locked
    if assessment.results_locked:
        return {
            "message": "KBA completed. Upgrade to Premium to view your scores.",
            "results_locked": True
        }

    return SubmitKBAResponse(
        kba_score=kba_result["total_score"],
        total_correct=kba_result["total_correct"],
        total_questions=kba_result["total_questions"],
        pillar_scores={
            p: PillarScoreOut(**data) for p, data in kba_result["pillar_scores"].items()
        },
    )


# --- Helper to load + validate assessment ---


async def _load_assessment(db: AsyncSession, assessment_id: str) -> Assessment:
    """Load assessment by ID or raise 404."""
    try:
        aid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assessment ID")

    result = await db.execute(select(Assessment).where(Assessment.id == aid))
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return assessment


async def _verify_assessment_ownership(
    assessment: Assessment,
    current_user: User | None
) -> None:
    """Verify user owns assessment or raise 403.

    Anonymous assessments (user_id=None) can be accessed without auth.
    User-owned assessments require authentication and ownership verification.
    """
    # Allow anonymous assessments to be accessed without auth
    if assessment.user_id is None:
        return

    # Require authentication for user-owned assessments
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to access this assessment"
        )

    # Verify ownership
    if assessment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this assessment"
        )


async def _load_assessment(db: AsyncSession, assessment_id: str) -> Assessment:
    """Load an in-progress, non-expired assessment or raise HTTPException."""
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
    if assessment.status == "completed":
        raise HTTPException(status_code=400, detail="Assessment already completed")
    if check_timer_expired(assessment):
        await expire_assessment(db, assessment)
        raise HTTPException(status_code=400, detail="Assessment has expired")

    return assessment


# --- PPA Endpoints ---


@router.get("/{assessment_id}/ppa/tasks", response_model=PPATasksResponse)
async def get_ppa_tasks(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get PPA tasks for the assessment. Selects tasks on first call, returns cached on subsequent calls."""
    assessment = await _load_assessment(db, assessment_id)
    await _verify_assessment_ownership(assessment, current_user)

    # Check KBA is done
    if assessment.kba_score is None:
        raise HTTPException(status_code=400, detail="KBA must be completed before PPA")

    # Check if tasks already assigned
    ppa: dict = assessment.ppa_responses or {}
    task_ids_str = ppa.get("task_ids", [])

    if not task_ids_str:
        # Select tasks
        tasks = await select_tasks(db, assessment.mode.value)
        if not tasks:
            raise HTTPException(status_code=500, detail="No PPA tasks available. Run the seed script.")

        task_ids_str = [str(t.id) for t in tasks]
        assessment.ppa_responses = {
            "task_ids": task_ids_str,
            "tasks": {},
        }
        flag_modified(assessment, "ppa_responses")
        await db.commit()
    else:
        # Load tasks from DB
        task_ids = [uuid.UUID(tid) for tid in task_ids_str]
        result = await db.execute(select(Task).where(Task.id.in_(task_ids)))
        tasks = list(result.scalars().all())

    # Return briefs (without scoring rubric)
    briefs = [get_task_brief(t) for t in tasks]
    return PPATasksResponse(tasks=briefs)


@router.post("/{assessment_id}/ppa/execute", response_model=PPAExecuteResponse)
async def execute_ppa(
    assessment_id: str,
    body: PPAExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Execute a user prompt against a PPA task. Returns LLM output (not judge scores)."""
    assessment = await _load_assessment(db, assessment_id)
    await _verify_assessment_ownership(assessment, current_user)

    if assessment.kba_score is None:
        raise HTTPException(status_code=400, detail="KBA must be completed before PPA")

    # Validate task is assigned to this assessment
    ppa: dict = assessment.ppa_responses or {}
    task_ids_str = ppa.get("task_ids", [])
    if body.task_id not in task_ids_str:
        raise HTTPException(status_code=400, detail="Task not assigned to this assessment")

    # Load task from DB
    try:
        task_uuid = uuid.UUID(body.task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    result = await db.execute(select(Task).where(Task.id == task_uuid))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check max attempts
    max_att = get_max_attempts(task, assessment.mode.value)
    current_attempts = get_attempt_count(ppa, body.task_id)

    if current_attempts >= max_att:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum attempts ({max_att}) reached for this task",
        )

    # Execute prompt via LLM
    try:
        output = await execute_task_prompt(body.prompt, task)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM execution failed: {str(e)}")

    # Store attempt
    attempt_number = current_attempts + 1
    updated_ppa = store_attempt(
        ppa_responses=ppa,
        task_id=body.task_id,
        prompt=body.prompt,
        output=output,
        attempt_number=attempt_number,
    )
    assessment.ppa_responses = updated_ppa
    flag_modified(assessment, "ppa_responses")
    await db.commit()

    # Check if results are locked before returning output
    if assessment.results_locked:
        return {
            "message": "Task completed. Upgrade to Premium to view results.",
            "results_locked": True
        }

    return PPAExecuteResponse(
        task_id=body.task_id,
        attempt_number=attempt_number,
        output=output,
        attempts_used=attempt_number,
        max_attempts=max_att,
    )


@router.post("/{assessment_id}/ppa/submit-best", response_model=PPASubmitBestResponse)
async def submit_best_attempt(
    assessment_id: str,
    body: PPASubmitBestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit best attempt for judging. Returns 5-dimension scores."""
    assessment = await _load_assessment(db, assessment_id)

    ppa: dict = assessment.ppa_responses or {}
    task_ids_str = ppa.get("task_ids", [])
    if body.task_id not in task_ids_str:
        raise HTTPException(status_code=400, detail="Task not assigned to this assessment")

    # Get task data
    task_data = ppa.get("tasks", {}).get(body.task_id)
    if not task_data or not task_data.get("attempts"):
        raise HTTPException(status_code=400, detail="No attempts found for this task")

    attempts = task_data["attempts"]
    if body.attempt_index < 0 or body.attempt_index >= len(attempts):
        raise HTTPException(status_code=400, detail="Invalid attempt index")

    # Check not already judged
    if task_data.get("judge_result") is not None:
        raise HTTPException(status_code=400, detail="This task has already been judged")

    # Load task from DB
    try:
        task_uuid = uuid.UUID(body.task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    result = await db.execute(select(Task).where(Task.id == task_uuid))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the selected attempt
    best_attempt = attempts[body.attempt_index]

    # Judge the output
    try:
        judge_result = await judge_task_output(
            task=task,
            user_prompt=best_attempt["prompt"],
            llm_output=best_attempt["output"],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM judging failed: {str(e)}")

    # Compute weighted score
    ppa_score = compute_ppa_score(judge_result, task.scoring_rubric)

    # Store judge result
    task_data["selected_best"] = body.attempt_index
    task_data["judge_result"] = judge_result
    task_data["ppa_score"] = ppa_score
    ppa["tasks"][body.task_id] = task_data

    # Check if all tasks are judged — compute overall PPA score
    all_judged = all(
        ppa.get("tasks", {}).get(tid, {}).get("judge_result") is not None
        for tid in task_ids_str
    )
    if all_judged:
        # Average PPA scores across all tasks
        task_scores = [
            ppa["tasks"][tid]["ppa_score"]
            for tid in task_ids_str
            if "ppa_score" in ppa["tasks"].get(tid, {})
        ]
        if task_scores:
            assessment.ppa_score = round(sum(task_scores) / len(task_scores), 1)

    assessment.ppa_responses = ppa
    flag_modified(assessment, "ppa_responses")
    await db.commit()

    return PPASubmitBestResponse(
        task_id=body.task_id,
        ppa_score=ppa_score,
        dimensions={
            dim: DimensionScore(
                score=data["score"],
                rationale=data.get("rationale", ""),
            )
            for dim, data in judge_result.items()
        },
    )


@router.get("/{assessment_id}/psv/sample", response_model=PSVSampleResponse)
async def get_psv_sample(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get a PSV sample for evaluation (full mode only)."""
    assessment = await _load_assessment(db, assessment_id)
    await _verify_assessment_ownership(assessment, current_user)
    if assessment.mode != AssessmentMode.full:
        raise HTTPException(400, "PSV is only available in full assessment mode")
    if assessment.kba_score is None:
        raise HTTPException(400, "KBA must be completed before PSV")
    if assessment.ppa_score is None:
        raise HTTPException(400, "PPA must be completed before PSV")
    if assessment.psv_score is not None:
        raise HTTPException(400, "PSV already submitted")

    # Check if sample already assigned
    if assessment.psv_submission and assessment.psv_submission.get("sample_id"):
        sample_id = assessment.psv_submission["sample_id"]
        result = await db.execute(select(PsvSample).where(PsvSample.id == uuid.UUID(sample_id)))
        sample = result.scalar_one_or_none()
    else:
        sample = await select_psv_sample(db)
        if not sample:
            raise HTTPException(404, "No PSV samples available")
        # Store the assigned sample so same one is returned on re-fetch
        assessment.psv_submission = {"sample_id": str(sample.id)}
        flag_modified(assessment, "psv_submission")
        await db.commit()

    if not sample:
        raise HTTPException(404, "PSV sample not found")

    return PSVSampleResponse(
        sample_id=str(sample.id),
        title=sample.title,
        pillar=sample.pillar,
        difficulty=sample.difficulty,
        task_context=sample.task_context,
        prompt_text=sample.prompt_text,
        output_text=sample.output_text,
    )


@router.post("/{assessment_id}/psv/submit", response_model=PSVSubmitResponse)
async def submit_psv(
    assessment_id: str,
    body: PSVSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Submit PSV evaluation (full mode only). Compares user's level against ground truth."""
    assessment = await _load_assessment(db, assessment_id)
    await _verify_assessment_ownership(assessment, current_user)
    if assessment.mode != AssessmentMode.full:
        raise HTTPException(400, "PSV is only available in full assessment mode")
    if assessment.kba_score is None:
        raise HTTPException(400, "KBA must be completed before PSV")
    if assessment.ppa_score is None:
        raise HTTPException(400, "PPA must be completed before PSV")
    if assessment.psv_score is not None:
        raise HTTPException(400, "PSV already submitted")
    if body.user_level < 1 or body.user_level > 5:
        raise HTTPException(400, "user_level must be between 1 and 5")

    # Get assigned sample
    if not assessment.psv_submission or not assessment.psv_submission.get("sample_id"):
        raise HTTPException(400, "Must fetch PSV sample first via GET /psv/sample")

    sample_id = assessment.psv_submission["sample_id"]
    result = await db.execute(select(PsvSample).where(PsvSample.id == uuid.UUID(sample_id)))
    sample = result.scalar_one_or_none()
    if not sample:
        raise HTTPException(404, "PSV sample not found")

    psv_score = compute_psv_score(body.user_level, sample.ground_truth_level)
    delta = abs(body.user_level - sample.ground_truth_level)

    assessment.psv_score = psv_score
    assessment.psv_submission = {
        "sample_id": str(sample.id),
        "sample_external_id": sample.external_id,
        "ground_truth_level": sample.ground_truth_level,
        "user_level": body.user_level,
        "delta": delta,
        "score": psv_score,
    }
    flag_modified(assessment, "psv_submission")
    await db.commit()

    # Check if results are locked
    if assessment.results_locked:
        return {
            "message": "PSV completed. Upgrade to Premium to view your score.",
            "results_locked": True
        }

    return PSVSubmitResponse(
        psv_score=psv_score,
        user_level=body.user_level,
        ground_truth_level=sample.ground_truth_level,
        delta=delta,
    )


# --- Anti-cheat ---


@router.post("/{assessment_id}/violation", response_model=ViolationResponse)
async def report_violation(
    assessment_id: str,
    body: ViolationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Report an anti-cheat violation. 3 violations = session voided."""
    try:
        aid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assessment ID")

    result = await db.execute(select(Assessment).where(Assessment.id == aid))
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status == AssessmentStatus.voided:
        return ViolationResponse(
            violations=assessment.violations or 0,
            voided=True,
            message="Assessment already voided",
        )
    if assessment.status in (AssessmentStatus.completed, AssessmentStatus.expired):
        raise HTTPException(status_code=400, detail="Assessment is no longer active")

    # Increment violations
    current_violations = (assessment.violations or 0) + 1
    assessment.violations = current_violations

    # Append to violation log
    log: list[dict[str, str]] = list(assessment.violation_log or [])
    log.append({
        "type": body.violation_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    assessment.violation_log = log
    flag_modified(assessment, "violation_log")

    voided = current_violations >= 3
    if voided:
        assessment.status = AssessmentStatus.voided

    await db.commit()

    return ViolationResponse(
        violations=current_violations,
        voided=voided,
        message="Assessment voided due to excessive violations" if voided else f"Warning {current_violations}/3",
    )


# --- Results ---


@router.get("/{assessment_id}/results", response_model=ResultsResponse)
async def get_results(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get assessment results. Computes final score and marks as completed on first call."""
    try:
        aid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assessment ID")

    result = await db.execute(select(Assessment).where(Assessment.id == aid))
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Verify ownership
    await _verify_assessment_ownership(assessment, current_user)

    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status == AssessmentStatus.voided:
        raise HTTPException(status_code=400, detail="Assessment has been voided")
    if assessment.status == AssessmentStatus.expired:
        raise HTTPException(status_code=400, detail="Assessment has expired")

    # If already completed, return cached results
    if assessment.status == AssessmentStatus.completed and assessment.final_score is not None:
        return _build_results_response(assessment)

    # Validate required scores exist
    if assessment.kba_score is None:
        raise HTTPException(status_code=400, detail="KBA not completed")
    if assessment.ppa_score is None:
        raise HTTPException(status_code=400, detail="PPA not completed")

    # For full mode, PSV is required
    mode_str = assessment.mode.value if isinstance(assessment.mode, AssessmentMode) else str(assessment.mode)
    if mode_str == "full" and assessment.psv_score is None:
        raise HTTPException(status_code=400, detail="PSV not completed (required for full mode)")

    # Compute final score
    final = compute_final_score(
        mode=mode_str,
        kba_score=assessment.kba_score,
        ppa_score=assessment.ppa_score,
        psv_score=assessment.psv_score,
    )

    # Assign level
    level = assign_level(final)

    # Aggregate pillar scores
    pillar_agg = aggregate_pillar_scores(
        kba_pillar_scores=assessment.pillar_scores,
        ppa_responses=assessment.ppa_responses,
    )

    # Update assessment
    now = datetime.now(timezone.utc)
    assessment.final_score = final
    assessment.level = level
    assessment.pillar_scores = pillar_agg
    assessment.status = AssessmentStatus.completed
    assessment.completed_at = now
    flag_modified(assessment, "pillar_scores")
    await db.commit()

    # Update leaderboard for full-mode assessments with a linked user
    if mode_str == "full" and assessment.user_id is not None:
        try:
            redis = await get_redis()
            user_result = await db.execute(
                select(User).where(User.id == assessment.user_id)
            )
            user_obj = user_result.scalar_one_or_none()
            user_name = user_obj.name if user_obj else ""

            badge_result = await db.execute(
                select(Badge).where(Badge.assessment_id == assessment.id)
            )
            badge_obj = badge_result.scalar_one_or_none()
            badge_id = str(badge_obj.id) if badge_obj else None

            await update_score(
                redis=redis,
                user_id=str(assessment.user_id),
                score=final,
                user_name=user_name,
                level=level,
                level_name=LEVEL_NAMES.get(level, "Novice"),
                pillar_scores=pillar_agg,
                badge_id=badge_id,
                achieved_at=now.isoformat(),
                industry_id=str(assessment.industry_id) if assessment.industry_id else None,
                role_id=str(assessment.role_id) if assessment.role_id else None,
            )
        except Exception:
            pass  # Leaderboard failure must not break assessment results

    return _build_results_response(assessment)


@router.post("/{assessment_id}/claim", response_model=ClaimResponse)
async def claim_assessment(
    assessment_id: str,
    body: ClaimRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ClaimResponse:
    """Claim a completed assessment: register or login, link to user, generate badge."""
    # Load assessment
    try:
        aid = uuid.UUID(assessment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assessment ID")

    result = await db.execute(select(Assessment).where(Assessment.id == aid))
    assessment = result.scalar_one_or_none()

    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status != "completed":
        raise HTTPException(status_code=400, detail="Assessment is not completed")

    # Check if already claimed (badge exists for this assessment)
    existing_badge = await db.execute(select(Badge).where(Badge.assessment_id == aid))
    if existing_badge.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Assessment already claimed")

    # Determine user: either authenticated user or authenticate via body
    user = None
    if current_user:
        # Simplified flow: authenticated user claiming badge
        user = current_user
    elif body.email and body.password:
        # Old flow: authenticate or register user via email/password
        if body.is_login:
            user = await get_user_by_email(db, body.email)
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            if not verify_password(body.password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            # Register new user
            existing = await get_user_by_email(db, body.email)
            if existing is not None:
                raise HTTPException(status_code=409, detail="Email already registered. Use is_login=true to login.")
            if len(body.password) < 8:
                raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
            name = body.name if body.name else body.email.split("@")[0]
            user = await create_user(db, body.email, name, body.password)
    else:
        raise HTTPException(status_code=401, detail="Authentication required: provide token or email/password")

    # Link assessment to user
    assessment.user_id = user.id

    # Mark badge as claimed
    assessment.badge_claimed = True
    assessment.badge_claimed_at = datetime.now(timezone.utc)

    await db.commit()

    # Generate badge
    badge = await create_badge(db, user, assessment)

    # Backfill leaderboard entry for auth-last full assessments claimed after results were computed
    mode_str = assessment.mode.value if isinstance(assessment.mode, AssessmentMode) else str(assessment.mode)
    if (
        mode_str == "full"
        and assessment.status == AssessmentStatus.completed
        and assessment.final_score is not None
    ):
        try:
            redis = await get_redis()
            level = assessment.level or 1
            achieved_at = (
                assessment.completed_at.isoformat()
                if assessment.completed_at
                else datetime.now(timezone.utc).isoformat()
            )
            await update_score(
                redis=redis,
                user_id=str(user.id),
                score=assessment.final_score,
                user_name=user.name or "",
                level=level,
                level_name=LEVEL_NAMES.get(level, "Novice"),
                pillar_scores=assessment.pillar_scores or {},
                badge_id=str(badge.id),
                achieved_at=achieved_at,
                industry_id=str(assessment.industry_id) if assessment.industry_id else None,
                role_id=str(assessment.role_id) if assessment.role_id else None,
            )
        except Exception:
            pass  # Leaderboard failure must not break badge claim

    # Create token
    token = create_access_token(user.id, user.email)

    return ClaimResponse(
        badge_id=str(badge.id),
        badge_svg=badge.badge_svg or "",
        verification_url=badge.verification_url or "",
        token=token,
        user_id=str(user.id),
    )


def _build_results_response(assessment: Assessment) -> ResultsResponse:
    """Build ResultsResponse from a completed assessment."""
    mode_str = assessment.mode.value if isinstance(assessment.mode, AssessmentMode) else str(assessment.mode)
    status_str = assessment.status.value if isinstance(assessment.status, AssessmentStatus) else str(assessment.status)
    completed_at_str = assessment.completed_at.isoformat() if assessment.completed_at else datetime.now(timezone.utc).isoformat()

    return ResultsResponse(
        assessment_id=str(assessment.id),
        mode=mode_str,
        status=status_str,
        results_locked=assessment.results_locked or False,
        final_score=assessment.final_score or 0.0,
        level=assessment.level or 1,
        kba_score=assessment.kba_score or 0.0,
        ppa_score=assessment.ppa_score or 0.0,
        psv_score=assessment.psv_score,
        pillar_scores=assessment.pillar_scores or {},
        completed_at=completed_at_str,
    )


# --- Pending Assessment Endpoints ---


@router.post("/pending", response_model=PendingAssessmentResponse)
async def create_pending_assessment(
    body: PendingAssessmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create or update a pending assessment for state persistence."""
    if body.mode not in ("quick", "full"):
        raise HTTPException(status_code=400, detail="mode must be 'quick' or 'full'")

    # Check if pending assessment already exists for this session
    result = await db.execute(
        select(PendingAssessment).where(PendingAssessment.session_id == body.session_id)
    )
    existing = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if existing:
        # Update existing
        existing.industry = body.industry
        existing.role = body.role
        existing.mode = body.mode
        existing.updated_at = now
        existing.expires_at = now + timedelta(hours=24)
        if body.user_id:
            try:
                existing.user_id = uuid.UUID(body.user_id)
            except ValueError:
                pass
        await db.commit()
        await db.refresh(existing)
        return PendingAssessmentResponse(
            id=str(existing.id),
            industry=existing.industry,
            role=existing.role,
            mode=existing.mode,
            status=existing.status,
            assessment_id=str(existing.assessment_id) if existing.assessment_id else None,
        )
    else:
        # Create new
        user_uuid = None
        if body.user_id:
            try:
                user_uuid = uuid.UUID(body.user_id)
            except ValueError:
                pass

        pending = PendingAssessment(
            session_id=body.session_id,
            user_id=user_uuid,
            industry=body.industry,
            role=body.role,
            mode=body.mode,
            status="pending",
        )
        db.add(pending)
        await db.commit()
        await db.refresh(pending)

        return PendingAssessmentResponse(
            id=str(pending.id),
            industry=pending.industry,
            role=pending.role,
            mode=pending.mode,
            status=pending.status,
            assessment_id=None,
        )


@router.get("/pending/{session_id}", response_model=PendingAssessmentResponse)
async def get_pending_assessment(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get pending assessment by session ID."""
    result = await db.execute(
        select(PendingAssessment).where(PendingAssessment.session_id == session_id)
    )
    pending = result.scalar_one_or_none()

    if not pending:
        raise HTTPException(status_code=404, detail="No pending assessment found")

    return PendingAssessmentResponse(
        id=str(pending.id),
        industry=pending.industry,
        role=pending.role,
        mode=pending.mode,
        status=pending.status,
        assessment_id=str(pending.assessment_id) if pending.assessment_id else None,
    )


@router.delete("/pending/{pending_id}")
async def delete_pending_assessment(
    pending_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete/abandon a pending assessment."""
    try:
        pid = uuid.UUID(pending_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pending assessment ID")

    result = await db.execute(
        select(PendingAssessment).where(PendingAssessment.id == pid)
    )
    pending = result.scalar_one_or_none()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending assessment not found")

    await db.delete(pending)
    await db.commit()

    return {"success": True}

