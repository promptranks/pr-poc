# Implementation Plan: Usage Limits and Paywall

## Overview

**Total Phases:** 4
**Estimated Effort:** 3-5 days
**Priority Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4

## Phase 1: Fix Premium User Limits

**Priority:** P0 (Critical Bug Fix)
**Effort:** 4 hours
**Risk:** Low

### Task 1.1: Database Migration - Fix Existing Records

**File:** SQL Migration Script
**Action:** Create and execute migration

```sql
-- Fix existing premium users with incorrect limits
UPDATE user_usage 
SET full_assessments_limit = 3,
    updated_at = NOW()
WHERE user_id IN (
    SELECT id FROM users WHERE subscription_tier = 'premium'
) 
AND full_assessments_limit != 3
AND period_start >= DATE_TRUNC('month', CURRENT_DATE)::DATE;

-- Verify results
SELECT u.email, u.subscription_tier, uu.full_assessments_used, uu.full_assessments_limit
FROM user_usage uu
JOIN users u ON u.id = uu.user_id
WHERE u.subscription_tier = 'premium'
AND uu.period_start >= DATE_TRUNC('month', CURRENT_DATE)::DATE;
```

**Test Cases:**
- Verify premium users show X/3 instead of X/0
- Verify free users still show X/0
- Verify enterprise users unaffected

### Task 1.2: Update UsageService - Always Sync Limit

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/usage_service.py`
**Lines:** 26-52 (get_or_create_usage method)

**Changes:**
```python
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
    else:
        # NEW: Always sync limit with current tier
        if usage.full_assessments_limit != limit:
            usage.full_assessments_limit = limit
            usage.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(usage)

    return usage
```

**Test Cases:**
- User with old limit=0, tier=premium → limit updated to 3
- User with correct limit → no update
- Fresh user → creates with correct limit

### Task 1.3: Update Stripe Webhook - Sync Usage on Upgrade

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/stripe_service.py`
**Lines:** 94-125 (handle_checkout_completed method)

**Changes:**
```python
@staticmethod
async def handle_checkout_completed(session_data: dict, db: AsyncSession):
    import logging
    logger = logging.getLogger(__name__)

    user_id = UUID(session_data["metadata"]["user_id"])
    subscription_id = session_data["subscription"]

    logger.info(f"Webhook: checkout.session.completed for user {user_id}")

    result = await db.execute(select(User).where(User.id == user_id))
    user = await _resolve(result.scalar_one())

    logger.info(f"Webhook: Updating user {user.email} to premium")

    user.subscription_tier = "premium"
    user.updated_at = datetime.now(timezone.utc)

    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.user_id == user_id)
    )
    stripe_customer = await _resolve(result.scalar_one())
    stripe_customer.stripe_subscription_id = subscription_id

    if hasattr(stripe_customer, "updated_at"):
        stripe_customer.updated_at = datetime.now(timezone.utc)

    # NEW: Update current month's usage limit
    from app.services.usage_service import UsageService
    period_start, period_end = UsageService.get_current_period()
    
    result = await db.execute(
        select(UserUsage).where(
            UserUsage.user_id == user_id,
            UserUsage.period_start == period_start
        )
    )
    usage = await _resolve(result.scalar_one_or_none())
    
    if usage:
        # User has existing usage record (was free, took assessments)
        # Update limit to premium (3), keep existing used count
        usage.full_assessments_limit = 3
        usage.updated_at = datetime.now(timezone.utc)
        logger.info(f"Webhook: Updated usage limit to 3, used={usage.full_assessments_used}")
    else:
        # No usage record yet, create new one
        usage = UserUsage(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            full_assessments_used=0,
            full_assessments_limit=3
        )
        db.add(usage)
        logger.info(f"Webhook: Created new usage record 0/3")

    await db.commit()
    logger.info(f"Webhook: Successfully updated user {user.email} to premium")

    EmailService.send_upgrade_email(user.email, user.name)
```

**Additional Import Required:**
```python
from app.models.user_usage import UserUsage
```

**Test Cases:**
- Free user with 1/0 usage → upgrade → shows 1/3
- Free user with 0/0 usage → upgrade → shows 0/3
- Fresh user upgrade → creates 0/3
- Webhook called twice (idempotent) → no errors

---

## Phase 2: Free User Premium Limit

**Priority:** P0 (Critical Feature)
**Effort:** 6 hours
**Risk:** Medium

### Task 2.1: Update UsageService - Handle Free Tier

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/usage_service.py`
**Lines:** 54-58 (check_limit method)

**Changes:**
```python
@staticmethod
async def check_limit(user_id: str, tier: str, db: AsyncSession) -> Tuple[bool, int, int]:
    usage = await UsageService.get_or_create_usage(user_id, tier, db)
    
    if tier == "free":
        # Free users get 1 trial attempt
        can_access = usage.full_assessments_used < 1
        return can_access, usage.full_assessments_used, 1
    else:
        # Premium/enterprise use normal limits
        can_access = usage.full_assessments_used < usage.full_assessments_limit
        return can_access, usage.full_assessments_used, usage.full_assessments_limit
```

**Test Cases:**
- Free user with 0 used → can_access=True, shows 0/1
- Free user with 1 used → can_access=False, shows 1/1
- Premium user with 2/3 → can_access=True, shows 2/3

### Task 2.2: Update Assessment Start - Check Free User Limit

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py`
**Lines:** 268-286 (start_assessment endpoint)

**Changes:**
```python
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
```

**Test Cases:**
- Free user, 0 used, starts premium → allowed, 1/1, results_locked=true
- Free user, 1 used, starts premium → 402 error with upgrade_required
- Premium user, 2/3 used, starts → allowed, 3/3, results_locked=false
- Anonymous user, starts premium → allowed, results_locked=true

### Task 2.3: Frontend - Handle 402 Error

**File:** Frontend assessment start handler
**Action:** Add error handling for 402 status

```typescript
try {
  const response = await api.post('/assessments/start', assessmentData);
  // Handle success
} catch (error) {
  if (error.response?.status === 402) {
    const detail = error.response.data.detail;
    if (detail.upgrade_required) {
      // Show upgrade modal
      showUpgradeModal({
        message: detail.message,
        used: detail.used,
        limit: detail.limit
      });
    }
  } else if (error.response?.status === 403) {
    // Premium user hit limit
    showLimitReachedModal(error.response.data.detail);
  }
}
```

**Test Cases:**
- Free user hits 402 → upgrade modal shown
- Premium user hits 403 → limit reached modal shown
- Network error → generic error shown

---

## Phase 3: Industry/Role Paywall

**Priority:** P1 (Core Feature)
**Effort:** 8 hours
**Risk:** Medium

### Task 3.1: Update Assessment Start - Industry/Role Check

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py`
**Lines:** 268-286

**Note:** Already covered in Task 2.2 (premium_features_used logic)

### Task 3.2: Update KBA Submit - Check Results Lock

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py`
**Lines:** 361-421 (submit_kba endpoint)

**Changes:**
```python
async def submit_kba(
    assessment_id: str,
    body: SubmitKBARequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit KBA answers. Returns score + per-pillar breakdown."""
    # ... existing validation code ...

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

    # NEW: Check if results are locked
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
```

**Test Cases:**
- Free user, results_locked=true → returns locked message
- Premium user, results_locked=false → returns scores
- Anonymous user, results_locked=true → returns locked message

### Task 3.3: Update PPA Execute - Check Results Lock

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py`
**Lines:** 496-600 (execute_ppa endpoint)

**Changes:**
```python
async def execute_ppa(
    assessment_id: str,
    body: PPAExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute a user prompt against a PPA task."""
    assessment = await _load_assessment(db, assessment_id)

    # ... existing validation and execution code ...

    # NEW: Check if results are locked before returning output
    if assessment.results_locked:
        return {
            "message": "Task completed. Upgrade to Premium to view results.",
            "results_locked": True
        }

    # Return normal response with LLM output
    return {
        "task_id": body.task_id,
        "output": llm_output,
        "attempt_number": current_attempts + 1,
        "max_attempts": max_att,
        "results_locked": False
    }
```

**Test Cases:**
- Free user executes task → returns locked message
- Premium user executes task → returns LLM output

### Task 3.4: Update PSV Submit - Check Results Lock

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py`
**Lines:** 696-750 (submit_psv endpoint)

**Changes:**
```python
async def submit_psv(
    assessment_id: str,
    body: PSVSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit PSV evaluation."""
    assessment = await _load_assessment(db, assessment_id)
    
    # ... existing validation and scoring code ...

    assessment.psv_score = psv_score
    assessment.psv_submission = {
        "sample_id": str(sample.id),
        "sample_external_id": sample.external_id,
        "ground_truth_level": sample.ground_truth_level,
        "user_level": body.user_level,
        "delta": delta,
        "score": psv_score,
    }
    await db.commit()

    # NEW: Check if results are locked
    if assessment.results_locked:
        return {
            "message": "PSV completed. Upgrade to Premium to view your score.",
            "results_locked": True
        }

    return {
        "psv_score": psv_score,
        "ground_truth_level": sample.ground_truth_level,
        "user_level": body.user_level,
        "delta": delta,
        "results_locked": False
    }
```

**Test Cases:**
- Free user submits PSV → returns locked message
- Premium user submits PSV → returns score

### Task 3.5: Frontend - Handle Locked Section Scores

**File:** Frontend Assessment component
**Action:** Check results_locked in section responses

```typescript
// After KBA submission
const kbaResponse = await api.post(`/assessments/${id}/kba/submit`, answers);

if (kbaResponse.data.results_locked) {
  // Show locked message
  showSectionComplete("KBA completed. Upgrade to view scores.");
} else {
  // Show scores
  displayKBAScores(kbaResponse.data);
}
```

**Test Cases:**
- Free user completes KBA → sees locked message
- Premium user completes KBA → sees scores
- UI handles both response formats

### Task 3.6: Frontend - Show Paywall Modal on Results

**File:** Frontend Results component
**Action:** Check results_locked flag

```typescript
if (assessment.results_locked) {
  return <UpgradeModal 
    message="Upgrade to Premium to view your assessment results"
    features={["View detailed scores", "3 assessments per month", "Industry & role insights"]}
  />;
}

return <ResultsDisplay assessment={assessment} />;
```

**Test Cases:**
- Free user views results → sees upgrade modal
- Premium user views results → sees scores

---

## Phase 4: Webhook Handlers

**Priority:** P2 (Production Readiness)
**Effort:** 4 hours
**Risk:** Low

### Task 4.1: Add Payment Failed Handler

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/stripe_service.py`
**Action:** Add new method

```python
@staticmethod
async def handle_payment_failed(invoice: dict, db: AsyncSession):
    """Handle failed payment - log and notify user."""
    import logging
    logger = logging.getLogger(__name__)
    
    customer_id = invoice.get("customer")
    attempt_count = invoice.get("attempt_count", 0)
    
    # Find user by stripe_customer_id
    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.stripe_customer_id == customer_id)
    )
    stripe_customer = await _resolve(result.scalar_one_or_none())
    
    if not stripe_customer:
        logger.warning(f"Payment failed for unknown customer {customer_id}")
        return
    
    result = await db.execute(select(User).where(User.id == stripe_customer.user_id))
    user = await _resolve(result.scalar_one())
    
    logger.warning(f"Payment failed for user {user.email}, attempt {attempt_count}")
    
    # Send notification email (optional)
    # EmailService.send_payment_failed_email(user.email, user.name, attempt_count)
    
    # Stripe will retry automatically
    # After final retry fails, customer.subscription.deleted will fire
```

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/payments.py`
**Lines:** 157-165 (webhook handler)

**Changes:**
```python
if event["type"] == "checkout.session.completed":
    logger.info("Webhook: Processing checkout.session.completed")
    await StripeService.handle_checkout_completed(event["data"]["object"], db)
elif event["type"] == "customer.subscription.deleted":
    logger.info("Webhook: Processing customer.subscription.deleted")
    await StripeService.handle_subscription_deleted(event["data"]["object"], db)
elif event["type"] == "invoice.payment_failed":
    logger.info("Webhook: Processing invoice.payment_failed")
    await StripeService.handle_payment_failed(event["data"]["object"], db)
else:
    logger.info(f"Webhook: Unhandled event type: {event['type']}")
```

**Test Cases:**
- Payment fails → logged, user notified
- Multiple retries → each logged
- Final failure → subscription.deleted fires

### Task 4.2: Add Optional Webhook Handlers

**File:** `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/services/stripe_service.py`
**Action:** Add placeholder methods

```python
@staticmethod
async def handle_invoice_paid(invoice: dict, db: AsyncSession):
    """Log successful monthly renewal."""
    import logging
    logger = logging.getLogger(__name__)
    
    customer_id = invoice.get("customer")
    amount_paid = invoice.get("amount_paid", 0) / 100  # Convert cents to dollars
    
    logger.info(f"Invoice paid: customer={customer_id}, amount=${amount_paid}")
    
    # Optional: Log to analytics, send receipt email

@staticmethod
async def handle_subscription_updated(subscription: dict, db: AsyncSession):
    """Handle subscription changes (plan change, pause, etc.)."""
    import logging
    logger = logging.getLogger(__name__)
    
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    
    logger.info(f"Subscription updated: customer={customer_id}, status={status}")
    
    # Optional: Handle status changes (paused, past_due, etc.)
```

**Test Cases:**
- Invoice paid → logged
- Subscription updated → logged
- No errors thrown

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_usage_service.py`
```python
async def test_check_limit_free_tier():
    # Free user with 0 used
    can_access, used, limit = await UsageService.check_limit(user_id, "free", db)
    assert can_access == True
    assert used == 0
    assert limit == 1

async def test_check_limit_free_tier_exhausted():
    # Free user with 1 used
    can_access, used, limit = await UsageService.check_limit(user_id, "free", db)
    assert can_access == False
    assert used == 1
    assert limit == 1

async def test_get_or_create_usage_syncs_limit():
    # Create usage with wrong limit
    # Call get_or_create_usage with correct tier
    # Verify limit updated
```

### Integration Tests

**File:** `tests/test_assessment_flow.py`
```python
async def test_free_user_premium_trial():
    # Free user starts premium assessment
    response = await client.post("/assessments/start", json={
        "mode": "full",
        "industry_id": industry_id
    })
    assert response.status_code == 200
    assert response.json()["results_locked"] == True
    
    # Try to start second premium assessment
    response = await client.post("/assessments/start", json={
        "mode": "full"
    })
    assert response.status_code == 402
    assert response.json()["detail"]["upgrade_required"] == True

async def test_upgrade_preserves_usage():
    # Free user takes 1 assessment
    # Simulate webhook (upgrade to premium)
    # Check usage shows 1/3
```

### E2E Tests

**Scenarios:**
1. Complete free user journey: signup → trial → blocked → upgrade → premium access
2. Premium user journey: signup → upgrade → 3 assessments → limit reached
3. Paywall journey: free user → select industry → complete → no scores → upgrade modal

---

## Deployment Plan

### Pre-Deployment
1. Run unit tests
2. Run integration tests
3. Test on staging environment
4. Verify database migration on staging

### Deployment Steps
1. **Phase 1:** Deploy database migration + code changes
2. **Phase 2:** Deploy after 24h monitoring of Phase 1
3. **Phase 3:** Deploy after 24h monitoring of Phase 2
4. **Phase 4:** Deploy after 48h monitoring of Phase 3

### Post-Deployment
1. Monitor webhook success rate
2. Monitor 402 error rate
3. Monitor conversion rate
4. Check premium user limits are correct

### Rollback Triggers
- Premium users report incorrect limits
- Free users blocked incorrectly
- Webhook failures >5%
- Frontend errors with locked responses

---

## Success Criteria

### Phase 1
- ✅ All premium users show X/3 limits (not X/0)
- ✅ New premium users get correct limits immediately
- ✅ Upgrades preserve usage count

### Phase 2
- ✅ Free users can take 1 premium trial
- ✅ Free users blocked on 2nd attempt with clear message
- ✅ Upgrade flow works: 1/1 → upgrade → 1/3

### Phase 3
- ✅ Industry/role selection triggers paywall
- ✅ Section scores hidden for locked assessments
- ✅ Upgrade modal shown on results page
- ✅ No score leakage for free users

### Phase 4
- ✅ Payment failures logged and handled
- ✅ Webhook success rate >95%
- ✅ No production errors from new handlers
