"""KBA Engine: question selection, scoring, and timer enforcement."""

import random
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentStatus
from app.models.question import Question

PILLARS = ["P", "E", "C", "M", "A"]


async def select_questions(db: AsyncSession, mode: str) -> list[Question]:
    """Select questions for an assessment.

    Quick: 10 questions (2 per pillar: 1 easy + 1 medium)
    Full: 20 questions (4 per pillar, mixed difficulty)
    """
    result = await db.execute(select(Question).where(Question.is_active == True))  # noqa: E712
    all_questions = result.scalars().all()

    selected: list[Question] = []

    for pillar in PILLARS:
        pillar_qs = [q for q in all_questions if q.pillar == pillar]

        if mode == "quick":
            easy = [q for q in pillar_qs if q.difficulty == 1]
            medium = [q for q in pillar_qs if q.difficulty == 2]
            if easy:
                selected += random.sample(easy, min(1, len(easy)))
            if medium:
                selected += random.sample(medium, min(1, len(medium)))
        elif mode == "full":
            selected += random.sample(pillar_qs, min(4, len(pillar_qs)))

    random.shuffle(selected)
    return selected


def score_kba(
    answers: list[dict],
    questions_by_id: dict[str, Question],
) -> dict:
    """Score KBA answers and return total + per-pillar breakdown.

    Args:
        answers: List of {question_id: str, selected: int}
        questions_by_id: Mapping of question UUID string to Question object

    Returns:
        {
            "total_score": float,
            "total_correct": int,
            "total_questions": int,
            "pillar_scores": {"P": {"score": 100.0, "correct": 2, "total": 2}, ...}
        }
    """
    pillar_results: dict[str, dict] = {
        p: {"correct": 0, "total": 0} for p in PILLARS
    }

    total_correct = 0
    total_questions = len(answers)

    for answer in answers:
        qid = str(answer["question_id"])
        selected = answer["selected"]

        question = questions_by_id.get(qid)
        if question is None:
            continue

        pillar = question.pillar
        pillar_results[pillar]["total"] += 1

        if selected == question.correct_answer:
            total_correct += 1
            pillar_results[pillar]["correct"] += 1

    total_score = (total_correct / total_questions * 100) if total_questions > 0 else 0.0

    pillar_scores = {}
    for pillar, data in pillar_results.items():
        if data["total"] > 0:
            score = data["correct"] / data["total"] * 100
        else:
            score = 0.0
        pillar_scores[pillar] = {
            "score": round(score, 1),
            "correct": data["correct"],
            "total": data["total"],
        }

    return {
        "total_score": round(total_score, 1),
        "total_correct": total_correct,
        "total_questions": total_questions,
        "pillar_scores": pillar_scores,
    }


def check_timer_expired(assessment: Assessment) -> bool:
    """Check if the assessment timer has expired.

    Returns True if expired.
    """
    now = datetime.now(timezone.utc)
    expires_at = assessment.expires_at
    # Handle naive datetimes (from SQLite in tests)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return now > expires_at


async def expire_assessment(db: AsyncSession, assessment: Assessment) -> None:
    """Mark an assessment as expired."""
    assessment.status = AssessmentStatus.expired
    await db.commit()
