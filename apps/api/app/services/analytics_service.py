from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String
from typing import List, Dict, Any
from uuid import UUID

from app.models.assessment import Assessment
from app.models.user import User


class AnalyticsService:
    @staticmethod
    async def get_score_trend(user_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(Assessment)
            .where(
                Assessment.user_id == user_id,
                cast(Assessment.status, String) == "completed",
                Assessment.final_score.isnot(None)
            )
            .order_by(Assessment.completed_at)
        )
        assessments = result.scalars().all()

        return [
            {
                "date": a.completed_at.isoformat() if a.completed_at else None,
                "score": a.final_score,
                "mode": a.mode.value
            }
            for a in assessments
        ]

    @staticmethod
    async def get_pillar_comparison(user_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        result = await db.execute(
            select(Assessment)
            .where(
                Assessment.user_id == user_id,
                cast(Assessment.status, String) == "completed",
                Assessment.final_score.isnot(None)
            )
            .order_by(Assessment.completed_at.desc())
        )
        assessments = result.scalars().all()

        if not assessments:
            return {"latest": {}, "average": {}}

        latest = assessments[0]
        latest_pillars = latest.pillar_scores or {}

        avg_pillars = {}
        for pillar in ["P", "E", "C", "A", "M"]:
            scores = []
            for a in assessments:
                if a.pillar_scores and pillar in a.pillar_scores:
                    score_value = a.pillar_scores[pillar]
                    # Handle both dict format {"score": 85} and direct number format
                    if isinstance(score_value, dict) and "score" in score_value:
                        scores.append(score_value["score"])
                    elif isinstance(score_value, (int, float)):
                        scores.append(score_value)
            avg_pillars[pillar] = sum(scores) / len(scores) if scores else 0

        return {"latest": latest_pillars, "average": avg_pillars}

    @staticmethod
    async def get_skill_gaps(user_id: UUID, db: AsyncSession) -> List[str]:
        result = await db.execute(
            select(Assessment)
            .where(
                Assessment.user_id == user_id,
                cast(Assessment.status, String) == "completed",
                Assessment.final_score.isnot(None)
            )
            .order_by(Assessment.completed_at.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        if not latest or not latest.pillar_scores:
            return []

        pillar_scores = latest.pillar_scores
        sorted_pillars = sorted(pillar_scores.items(), key=lambda x: x[1])
        return [p[0] for p in sorted_pillars[:2]]

    @staticmethod
    async def get_recommendations(user_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        from app.models.learning_resource import LearningResource

        weak_pillars = await AnalyticsService.get_skill_gaps(user_id, db)

        if not weak_pillars:
            return []

        result = await db.execute(
            select(LearningResource)
            .where(LearningResource.pillar.in_(weak_pillars))
            .order_by(LearningResource.min_level)
            .limit(6)
        )

        resources = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "title": r.title,
                "url": r.url,
                "pillar": r.pillar,
                "resource_type": r.resource_type
            }
            for r in resources
        ]
