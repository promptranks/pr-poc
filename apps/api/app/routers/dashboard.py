from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.assessment import Assessment, AssessmentStatus
from app.models.badge import Badge
from app.services.usage_service import UsageService
from app.services.analytics_service import AnalyticsService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tier = current_user.subscription_tier
    _, used, limit = await UsageService.check_limit(str(current_user.id), tier, db)

    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == current_user.id)
        .order_by(Assessment.completed_at.desc())
        .limit(5)
    )
    recent_assessments = result.scalars().all()

    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "avatar_url": current_user.avatar_url,
            "subscription_tier": tier
        },
        "usage": {
            "full_assessments_used": used,
            "full_assessments_limit": limit,
            "tier": tier
        },
        "recent_assessments": [
            {
                "id": str(a.id),
                "mode": a.mode.value,
                "final_score": a.final_score,
                "level": a.level,
                "status": a.status.value,
                "results_locked": a.results_locked,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None
            }
            for a in recent_assessments
        ]
    }


@router.get("/assessments/history")
async def get_assessment_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    mode: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit

    query = select(Assessment).where(Assessment.user_id == current_user.id)

    if mode and mode in ["quick", "full"]:
        query = query.where(Assessment.mode == mode)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    query = query.order_by(Assessment.completed_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    assessments = result.scalars().all()

    return {
        "assessments": [
            {
                "id": str(a.id),
                "mode": a.mode.value,
                "final_score": a.final_score,
                "level": a.level,
                "status": a.status.value,
                "results_locked": a.results_locked,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "started_at": a.started_at.isoformat()
            }
            for a in assessments
        ],
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/assessments/{assessment_id}/details")
async def get_assessment_details(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    assessment_uuid = UUID(assessment_id)
    result = await db.execute(
        select(Assessment).where(
            Assessment.id == assessment_uuid,
            Assessment.user_id == current_user.id
        )
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    pillar_scores = assessment.pillar_scores or {}

    recommendations = await AnalyticsService.get_recommendations(current_user.id, db)

    return {
        "assessment": {
            "id": str(assessment.id),
            "mode": assessment.mode.value,
            "final_score": assessment.final_score,
            "level": assessment.level,
            "status": assessment.status.value,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None
        },
        "pillar_scores": pillar_scores,
        "recommendations": recommendations
    }


@router.get("/unclaimed-badges")
async def get_unclaimed_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of completed assessments that haven't had their badges claimed yet."""
    # Find completed assessments for this user where badge_claimed = False
    result = await db.execute(
        select(Assessment)
        .where(
            Assessment.user_id == current_user.id,
            Assessment.status == "completed",
            Assessment.badge_claimed == False
        )
        .order_by(Assessment.completed_at.desc())
    )
    unclaimed_assessments = result.scalars().all()

    badges_data = []
    for assessment in unclaimed_assessments:
        # Check if badge exists for this assessment
        badge_result = await db.execute(
            select(Badge).where(Badge.assessment_id == assessment.id)
        )
        badge = badge_result.scalar_one_or_none()

        badges_data.append({
            "assessment_id": str(assessment.id),
            "badge_id": str(badge.id) if badge else None,
            "industry": assessment.industry,
            "role": assessment.role,
            "mode": assessment.mode.value,
            "score": assessment.final_score,
            "level": assessment.level,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        })

    return {"unclaimed_badges": badges_data}

