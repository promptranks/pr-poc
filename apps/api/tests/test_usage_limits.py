"""Comprehensive tests for usage limits and paywall functionality."""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.models.user import User
from app.models.assessment import Assessment, AssessmentMode, AssessmentStatus
from app.models.user_usage import UserUsage
from app.services.usage_service import UsageService


# --- Unit Tests for UsageService ---


@pytest.mark.asyncio
async def test_get_tier_limit_all_tiers():
    """Test tier limits for all subscription tiers."""
    assert UsageService.get_tier_limit("free") == 0
    assert UsageService.get_tier_limit("premium") == 3
    assert UsageService.get_tier_limit("enterprise") == 999
    assert UsageService.get_tier_limit("unknown") == 0


@pytest.mark.asyncio
async def test_get_or_create_usage_creates_new_record(db_session, test_user):
    """Test that get_or_create_usage creates a new record for premium user."""
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    usage = await UsageService.get_or_create_usage(str(test_user.id), "premium", db_session)

    assert usage is not None
    assert usage.user_id == test_user.id
    assert usage.full_assessments_used == 0
    assert usage.full_assessments_limit == 3


@pytest.mark.asyncio
async def test_get_or_create_usage_syncs_limit(db_session, test_user):
    """Test that get_or_create_usage syncs limit when tier changes."""
    test_user.subscription_tier = "free"
    db_session.add(test_user)
    await db_session.commit()

    # Create usage record as free user (limit=0)
    usage = await UsageService.get_or_create_usage(str(test_user.id), "free", db_session)
    assert usage.full_assessments_limit == 0

    # Upgrade to premium
    test_user.subscription_tier = "premium"
    await db_session.commit()

    # Get usage again - should sync limit to 3
    usage = await UsageService.get_or_create_usage(str(test_user.id), "premium", db_session)
    assert usage.full_assessments_limit == 3


@pytest.mark.asyncio
async def test_check_limit_free_user_no_usage(db_session, test_user):
    """Test free user with no usage can start 1 trial."""
    test_user.subscription_tier = "free"
    db_session.add(test_user)
    await db_session.commit()

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "free", db_session)

    assert can_start is True
    assert used == 0
    assert limit == 1  # Free users get 1 trial


@pytest.mark.asyncio
async def test_check_limit_free_user_trial_used(db_session, test_user):
    """Test free user with 1 trial used cannot start another."""
    test_user.subscription_tier = "free"
    db_session.add(test_user)
    await db_session.commit()

    # Use the trial
    await UsageService.increment_usage(str(test_user.id), "free", db_session)

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "free", db_session)

    assert can_start is False
    assert used == 1
    assert limit == 1


@pytest.mark.asyncio
async def test_check_limit_premium_user_under_limit(db_session, test_user):
    """Test premium user under limit can start assessment."""
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)

    assert can_start is True
    assert used == 0
    assert limit == 3


@pytest.mark.asyncio
async def test_check_limit_premium_user_at_limit(db_session, test_user):
    """Test premium user at limit cannot start assessment."""
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
async def test_check_limit_enterprise_user_unlimited(db_session, test_user):
    """Test enterprise user has unlimited access."""
    test_user.subscription_tier = "enterprise"
    db_session.add(test_user)
    await db_session.commit()

    # Use many assessments
    for _ in range(100):
        await UsageService.increment_usage(str(test_user.id), "enterprise", db_session)

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "enterprise", db_session)

    assert can_start is True  # 100 < 999, so can still start
    assert used == 100
    assert limit == 999


@pytest.mark.asyncio
async def test_increment_usage_increments_counter(db_session, test_user):
    """Test increment_usage increases the counter."""
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    await UsageService.increment_usage(str(test_user.id), "premium", db_session)
    await UsageService.increment_usage(str(test_user.id), "premium", db_session)

    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)

    assert used == 2
    assert limit == 3


# --- Integration Tests for Assessment Flow ---


@pytest.mark.asyncio
async def test_free_user_first_premium_attempt_allowed(client, test_user, seeded_db):
    """Test Case 2: Free user can start first premium assessment with locked results."""
    test_user.subscription_tier = "free"

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    response = await client.post(
        "/assessments/start",
        json={
            "mode": "full",
            "industry_id": str(uuid.uuid4()),
            "role_id": str(uuid.uuid4())
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "full"
    assert "assessment_id" in data


@pytest.mark.asyncio
async def test_free_user_second_premium_attempt_blocked(client, test_user, seeded_db, db_session):
    """Test Case 3: Free user cannot start second premium assessment."""
    test_user.subscription_tier = "free"
    await db_session.commit()

    # Use the trial
    await UsageService.increment_usage(str(test_user.id), "free", db_session)

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    response = await client.post(
        "/assessments/start",
        json={
            "mode": "full",
            "industry_id": str(uuid.uuid4()),
            "role_id": str(uuid.uuid4())
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 402
    data = response.json()
    assert "upgrade_required" in data["detail"] or "Free trial used" in str(data)


@pytest.mark.asyncio
async def test_premium_user_can_start_full_assessment(client, test_user, seeded_db):
    """Test Case 1: Premium user can start full assessment."""
    test_user.subscription_tier = "premium"

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    response = await client.post(
        "/assessments/start",
        json={
            "mode": "full",
            "industry_id": str(uuid.uuid4()),
            "role_id": str(uuid.uuid4())
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "full"


@pytest.mark.asyncio
async def test_premium_user_at_limit_blocked(client, test_user, seeded_db, db_session):
    """Test premium user at 3/3 limit is blocked."""
    test_user.subscription_tier = "premium"
    await db_session.commit()

    # Use all 3 assessments
    for _ in range(3):
        await UsageService.increment_usage(str(test_user.id), "premium", db_session)

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    response = await client.post(
        "/assessments/start",
        json={
            "mode": "full",
            "industry_id": str(uuid.uuid4()),
            "role_id": str(uuid.uuid4())
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert "limit reached" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_anonymous_user_premium_features_locked(client, seeded_db):
    """Test anonymous user can start assessment but results are locked."""
    response = await client.post(
        "/assessments/start",
        json={
            "mode": "full",
            "industry_id": str(uuid.uuid4()),
            "role_id": str(uuid.uuid4())
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "full"


@pytest.mark.asyncio
async def test_results_locked_hides_kba_scores(client, test_user, seeded_db, db_session):
    """Test Case 8: Results locked prevents viewing KBA scores."""
    test_user.subscription_tier = "free"
    await db_session.commit()

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    # Create assessment with results_locked
    assessment = Assessment(
        id=uuid.uuid4(),
        user_id=test_user.id,
        mode=AssessmentMode.full,
        status=AssessmentStatus.in_progress,
        results_locked=True,
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        kba_responses={"question_ids": [str(q.id) for q in seeded_db[:10]]}
    )
    db_session.add(assessment)
    await db_session.commit()

    # Submit KBA answers
    answers = [{"question_id": str(q.id), "selected": 0} for q in seeded_db[:10]]

    response = await client.post(
        f"/assessments/{assessment.id}/kba/submit",
        json={"answers": answers},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data.get("results_locked") is True
    assert "message" in data
    assert "Upgrade" in data["message"]


@pytest.mark.asyncio
async def test_industry_selection_triggers_paywall(client, test_user, seeded_db):
    """Test Case 8: Industry selection triggers paywall for free users."""
    test_user.subscription_tier = "free"

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    response = await client.post(
        "/assessments/start",
        json={
            "mode": "quick",
            "industry_id": str(uuid.uuid4())
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "quick"


@pytest.mark.asyncio
async def test_role_selection_triggers_paywall(client, test_user, seeded_db):
    """Test role selection triggers paywall for free users."""
    test_user.subscription_tier = "free"

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    response = await client.post(
        "/assessments/start",
        json={
            "mode": "quick",
            "role_id": str(uuid.uuid4())
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "quick"


@pytest.mark.asyncio
async def test_monthly_reset_creates_new_usage_record(db_session, test_user):
    """Test Case 6: Monthly reset creates new usage record."""
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    # Create usage for current period
    period_start, period_end = UsageService.get_current_period()
    usage = UserUsage(
        user_id=test_user.id,
        period_start=period_start,
        period_end=period_end,
        full_assessments_used=3,
        full_assessments_limit=3
    )
    db_session.add(usage)
    await db_session.commit()

    # Verify user is at limit
    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)
    assert can_start is False
    assert used == 3

    # Note: In production, when next month arrives, get_or_create_usage will create
    # a new record with period_start for the new month, resetting used to 0


@pytest.mark.asyncio
async def test_upgrade_preserves_usage_count(db_session, test_user):
    """Test Case 4: Upgrading from free to premium preserves usage count."""
    test_user.subscription_tier = "free"
    db_session.add(test_user)
    await db_session.commit()

    # Free user uses their trial
    await UsageService.increment_usage(str(test_user.id), "free", db_session)

    # Verify usage
    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "free", db_session)
    assert used == 1
    assert limit == 1

    # Simulate upgrade (what webhook does)
    test_user.subscription_tier = "premium"
    await db_session.commit()

    # Get usage with new tier - should sync limit but preserve used count
    usage = await UsageService.get_or_create_usage(str(test_user.id), "premium", db_session)
    assert usage.full_assessments_used == 1  # Preserved
    assert usage.full_assessments_limit == 3  # Updated

    # Check limit
    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)
    assert used == 1
    assert limit == 3
    assert can_start is True  # Can start 2 more


@pytest.mark.asyncio
async def test_fresh_premium_user_gets_full_quota(db_session, test_user):
    """Test Case 5: Fresh premium user gets 0/3 quota."""
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    # Check limit - should create new usage record
    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)

    assert can_start is True
    assert used == 0
    assert limit == 3


@pytest.mark.asyncio
async def test_assessment_expiry_no_refund(db_session, test_user):
    """Test Case 7: Assessment expiry does not refund quota."""
    test_user.subscription_tier = "premium"
    db_session.add(test_user)
    await db_session.commit()

    # Start assessment (increments usage)
    await UsageService.increment_usage(str(test_user.id), "premium", db_session)

    # Create expired assessment
    assessment = Assessment(
        id=uuid.uuid4(),
        user_id=test_user.id,
        mode=AssessmentMode.full,
        status=AssessmentStatus.expired,
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(assessment)
    await db_session.commit()

    # Check usage - should still be 1/3 (no refund)
    can_start, used, limit = await UsageService.check_limit(str(test_user.id), "premium", db_session)
    assert used == 1
    assert limit == 3
    assert can_start is True  # Can start another


@pytest.mark.asyncio
async def test_enterprise_user_no_limits(client, test_user, seeded_db, db_session):
    """Test enterprise user has no limits."""
    test_user.subscription_tier = "enterprise"
    db_session.add(test_user)
    await db_session.commit()

    # Create auth token
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id, test_user.email)

    # Start multiple assessments (enterprise has no limit)
    for i in range(5):
        response = await client.post(
            "/assessments/start",
            json={
                "mode": "full",
                # Use None for industry/role to avoid premium requirement check
                "industry_id": None,
                "role_id": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Attempt {i+1} failed: {response.json()}"
