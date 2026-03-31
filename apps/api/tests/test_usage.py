import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select

from app.models.user import User
from app.models.assessment import Assessment, AssessmentMode
from app.models.user_usage import UserUsage
from app.services.usage_service import UsageService


@pytest.mark.asyncio
async def test_get_tier_limit():
    assert UsageService.get_tier_limit("free") == 0
    assert UsageService.get_tier_limit("premium") == 3
    assert UsageService.get_tier_limit("enterprise") == 999


@pytest.mark.asyncio
async def test_get_current_period():
    period_start, period_end = UsageService.get_current_period()
    assert period_start.day == 1
    assert period_start.month == date.today().month
    assert period_end.month == date.today().month


@pytest.mark.asyncio
async def test_free_user_full_assessment_locked(db_session, test_user):
    test_user.subscription_tier = "free"
    db_session.add(test_user)
    await db_session.commit()

    assessment = Assessment(
        user_id=test_user.id,
        mode=AssessmentMode.full,
        results_locked=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db_session.add(assessment)
    await db_session.commit()

    assert assessment.results_locked is True


@pytest.mark.asyncio
async def test_premium_user_under_limit(db_session, test_user):
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)

    assert can_start is True
    assert used == 0
    assert limit == 3


@pytest.mark.asyncio
async def test_premium_user_increment_usage(db_session, test_user):
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    await UsageService.increment_usage(str(test_user.id), "premium", db_session)

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)
    assert used == 1
    assert limit == 3


@pytest.mark.asyncio
async def test_premium_user_at_limit(db_session, test_user):
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    # Use all 3 assessments
    for _ in range(3):
        await UsageService.increment_usage(str(test_user.id), "premium", db_session)

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)
    assert can_start is False
    assert used == 3
    assert limit == 3


@pytest.mark.asyncio
async def test_enterprise_user_unlimited(db_session, test_user):
    test_user.subscription_tier = "enterprise"
    db_session.add(test_user)
    await db_session.commit()

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "enterprise", db_session)

    assert can_start is True
    assert limit == 999
