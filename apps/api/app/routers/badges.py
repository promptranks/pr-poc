"""Badges router: public badge verification endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.badge import Badge

router = APIRouter(prefix="/badges", tags=["badges"])


class BadgeVerifyResponse(BaseModel):
    badge_id: str
    mode: str
    level: int
    level_name: str
    final_score: float
    pillar_scores: dict[str, Any]
    badge_svg: str
    issued_at: str
    valid: bool


@router.get("/verify/{badge_id}", response_model=BadgeVerifyResponse)
async def verify_badge(
    badge_id: str,
    db: AsyncSession = Depends(get_db),
) -> BadgeVerifyResponse:
    """Public badge verification endpoint. No auth required."""
    try:
        bid = uuid.UUID(badge_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid badge ID")

    result = await db.execute(select(Badge).where(Badge.id == bid))
    badge = result.scalar_one_or_none()

    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")

    issued_at_str = badge.issued_at.isoformat() if badge.issued_at else ""

    return BadgeVerifyResponse(
        badge_id=str(badge.id),
        mode=badge.mode,
        level=badge.level,
        level_name=badge.level_name,
        final_score=badge.final_score,
        pillar_scores=badge.pillar_scores or {},
        badge_svg=badge.badge_svg or "",
        issued_at=issued_at_str,
        valid=True,
    )
