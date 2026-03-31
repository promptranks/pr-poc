from datetime import date, datetime, timezone
from calendar import monthrange
from typing import Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user_usage import UserUsage


class UsageService:
    @staticmethod
    def get_tier_limit(tier: str) -> int:
        limits = {"free": 0, "premium": 3, "enterprise": 999}
        return limits.get(tier, 0)

    @staticmethod
    def get_current_period() -> Tuple[date, date]:
        today = date.today()
        period_start = date(today.year, today.month, 1)
        last_day = monthrange(today.year, today.month)[1]
        period_end = date(today.year, today.month, last_day)
        return period_start, period_end

    @staticmethod
    async def get_or_create_usage(user_id: str, tier: str, db: AsyncSession) -> UserUsage:
        period_start, period_end = UsageService.get_current_period()
        limit = UsageService.get_tier_limit(tier)

        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        result = await db.execute(
            select(UserUsage).where(
                UserUsage.user_id == user_uuid,
                UserUsage.period_start == period_start
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            usage = UserUsage(
                user_id=user_uuid,
                period_start=period_start,
                period_end=period_end,
                full_assessments_used=0,
                full_assessments_limit=limit
            )
            db.add(usage)
            await db.commit()
            await db.refresh(usage)

        return usage

    @staticmethod
    async def check_limit(user_id: str, tier: str, db: AsyncSession) -> Tuple[bool, int, int]:
        usage = await UsageService.get_or_create_usage(user_id, tier, db)
        can_access = usage.full_assessments_used < usage.full_assessments_limit
        return can_access, usage.full_assessments_used, usage.full_assessments_limit

    @staticmethod
    async def increment_usage(user_id: str, tier: str, db: AsyncSession) -> None:
        usage = await UsageService.get_or_create_usage(user_id, tier, db)
        usage.full_assessments_used += 1
        usage.updated_at = datetime.now(timezone.utc)
        await db.commit()
