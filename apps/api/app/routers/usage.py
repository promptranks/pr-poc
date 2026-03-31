from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.usage_service import UsageService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/check")
async def check_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tier = current_user.subscription_tier
    can_start, used, limit = await UsageService.check_limit(str(current_user.id), tier, db)

    return {
        "can_start_full": can_start,
        "full_assessments_used": used,
        "full_assessments_limit": limit,
        "tier": tier
    }
