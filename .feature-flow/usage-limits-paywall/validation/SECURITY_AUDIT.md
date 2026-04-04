# Security Audit Report: Usage Limits & Paywall Feature

**Date:** 2026-04-04  
**Auditor:** Security Analysis Agent  
**Overall Risk Rating:** 🔴 **HIGH RISK**

## Executive Summary

The usage-limits-paywall feature implementation contains **1 critical vulnerability** and **multiple high-severity issues** that must be addressed before production deployment. While the authentication system and results locking mechanisms are properly implemented, the lack of assessment ownership verification creates a broken access control vulnerability that undermines the entire paywall system.

## Critical Vulnerabilities

### 🔴 CRITICAL: Broken Access Control - No Assessment Ownership Verification

**Severity:** Critical  
**CVSS Score:** 8.1 (High)  
**CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)

**Description:**  
All assessment endpoints (`submit_kba`, `execute_ppa`, `submit_best_attempt`, `get_psv_sample`, `submit_psv`, `get_results`) do not verify that the requesting user owns the assessment. Any user who knows an assessment UUID can access, modify, or view results for that assessment, regardless of ownership.

**Affected Files:**
- `/Volumes/DEV/ScopeLabs.Work/OpenSource/prk-poc/apps/api/app/routers/assessment.py` (lines 390-899)

**Attack Scenario:**
1. Free user starts assessment, gets assessment_id `abc-123`
2. Free user's results are locked (results_locked=true)
3. Attacker guesses or intercepts assessment_id `abc-123`
4. Attacker calls `/assessments/abc-123/results` without authentication
5. Attacker receives full results despite results_locked flag

**Impact:**
- Unauthorized access to assessment data
- Bypass of paywall restrictions
- Privacy violation (users can access other users' assessments)
- Business logic bypass (free users can view locked results)

**Proof of Concept:**
```bash
# User A creates assessment
curl -X POST /assessments/start -H "Authorization: Bearer <user_a_token>"
# Returns: {"assessment_id": "550e8400-e29b-41d4-a716-446655440000"}

# User B (or anonymous) accesses User A's assessment
curl /assessments/550e8400-e29b-41d4-a716-446655440000/results
# Returns: Full results without authorization check
```

**Recommended Fix:**
```python
# Add ownership verification helper
async def _verify_assessment_ownership(
    assessment: Assessment,
    current_user: User | None
) -> None:
    """Verify user owns assessment or raise 403."""
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

# Apply to all assessment endpoints
@router.post("/{assessment_id}/kba/submit")
async def submit_kba(
    assessment_id: str,
    body: SubmitKBARequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),  # ADD THIS
):
    assessment = await _load_assessment(db, assessment_id)
    await _verify_assessment_ownership(assessment, current_user)  # ADD THIS
    # ... rest of logic
```

---

## High Severity Issues

### 🟠 HIGH: Race Condition in Usage Limit Enforcement

**Severity:** High  
**CVSS Score:** 6.5 (Medium)  
**CWE:** CWE-362 (Concurrent Execution using Shared Resource with Improper Synchronization)

**Description:**  
The usage limit check and increment are not atomic. Two concurrent requests can both pass the limit check before either increments the counter, allowing users to exceed their limits.

**Affected Files:**
- `apps/api/app/services/usage_service.py` (lines 62-79)
- `apps/api/app/routers/assessment.py` (lines 284-292, 296-311)

**Attack Scenario:**
```python
# Free user with 0/1 usage sends 2 concurrent requests
# Request 1: check_limit() returns (True, 0, 1) ✓
# Request 2: check_limit() returns (True, 0, 1) ✓
# Request 1: increment_usage() → 1/1
# Request 2: increment_usage() → 2/1 (EXCEEDED LIMIT)
```

**Impact:**
- Free users can take multiple premium assessments
- Premium users can exceed 3/month limit
- Revenue loss from bypassed paywall

**Recommended Fix:**
```python
# Option 1: Database-level constraint
# Add unique constraint on (user_id, period_start) and use optimistic locking

# Option 2: Atomic increment with SELECT FOR UPDATE
@staticmethod
async def check_and_increment_usage(
    user_id: str, tier: str, db: AsyncSession
) -> Tuple[bool, int, int]:
    """Atomically check and increment usage. Returns (success, used, limit)."""
    period_start, period_end = UsageService.get_current_period()
    limit = UsageService.get_tier_limit(tier)
    user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    
    # Lock the row for update
    result = await db.execute(
        select(UserUsage)
        .where(
            UserUsage.user_id == user_uuid,
            UserUsage.period_start == period_start
        )
        .with_for_update()
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
    
    # Check limit
    effective_limit = 1 if tier == "free" else usage.full_assessments_limit
    if usage.full_assessments_used >= effective_limit:
        await db.rollback()  # Release lock
        return False, usage.full_assessments_used, effective_limit
    
    # Increment atomically
    usage.full_assessments_used += 1
    usage.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return True, usage.full_assessments_used, effective_limit
```

### 🟠 HIGH: No Webhook Replay Attack Prevention

**Severity:** High  
**CVSS Score:** 6.5 (Medium)  
**CWE:** CWE-294 (Authentication Bypass by Capture-Replay)

**Description:**  
Stripe webhook events are not tracked for idempotency. An attacker who captures a valid webhook payload could replay it to trigger duplicate subscription upgrades or downgrades.

**Affected Files:**
- `apps/api/app/routers/payments.py` (lines 136-175)
- `apps/api/app/services/stripe_service.py` (lines 94-233)

**Attack Scenario:**
1. Attacker intercepts `checkout.session.completed` webhook
2. Attacker replays webhook multiple times
3. System processes upgrade multiple times (though current implementation is mostly idempotent)
4. Potential for duplicate email notifications or analytics events

**Impact:**
- Duplicate processing of subscription events
- Potential for inconsistent state
- Spam notifications to users

**Recommended Fix:**
```python
# Create webhook event tracking table
class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stripe_event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    processed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# In webhook handler
@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # ... signature verification ...
    
    event_id = event.get("id")
    
    # Check if already processed
    result = await db.execute(
        select(ProcessedWebhookEvent).where(
            ProcessedWebhookEvent.stripe_event_id == event_id
        )
    )
    if result.scalar_one_or_none() is not None:
        logger.info(f"Webhook {event_id} already processed, skipping")
        return {"status": "already_processed"}
    
    # Process event...
    
    # Mark as processed
    db.add(ProcessedWebhookEvent(
        stripe_event_id=event_id,
        event_type=event["type"]
    ))
    await db.commit()
    
    return {"status": "success"}
```

### 🟠 HIGH: Usage Increment Before Assessment Creation

**Severity:** High  
**CVSS Score:** 5.3 (Medium)  
**CWE:** CWE-754 (Improper Check for Unusual or Exceptional Conditions)

**Description:**  
Usage is incremented before the assessment is created. If assessment creation fails (database error, validation error, etc.), the user loses a usage credit without receiving an assessment.

**Affected Files:**
- `apps/api/app/routers/assessment.py` (lines 292, 310, 318-368)

**Attack Scenario:**
1. Premium user with 2/3 usage starts assessment
2. Usage incremented to 3/3
3. Database error occurs during assessment creation
4. User now has 3/3 usage but no assessment was created
5. User cannot start any more assessments

**Impact:**
- Users lose usage credits without receiving service
- Poor user experience
- Potential refund requests

**Recommended Fix:**
```python
# Move usage increment AFTER successful assessment creation
@router.post("/start", response_model=StartAssessmentResponse)
async def start_assessment(
    body: StartAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    # ... validation and limit checks ...
    
    # Check limit but DON'T increment yet
    if premium_features_used and current_user:
        tier = current_user.subscription_tier
        if tier in ("free", "premium"):
            can_start, used, limit = await UsageService.check_limit(
                str(current_user.id), tier, db
            )
            if not can_start:
                raise HTTPException(...)
    
    # Create assessment
    assessment = Assessment(...)
    db.add(assessment)
    
    # Update pending assessment if exists
    if pending:
        pending.status = "in_progress"
        pending.assessment_id = assessment.id
    
    # Commit assessment first
    await db.commit()
    await db.refresh(assessment)
    
    # NOW increment usage after successful creation
    if premium_features_used and current_user and tier in ("free", "premium"):
        await UsageService.increment_usage(str(current_user.id), tier, db)
    
    # Return response...
```

---

## Medium Severity Issues

### 🟡 MEDIUM: No Rate Limiting

**Severity:** Medium  
**CVSS Score:** 5.3 (Medium)  
**CWE:** CWE-770 (Allocation of Resources Without Limits or Throttling)

**Description:**  
No rate limiting is implemented on any endpoints. Attackers can perform brute force attacks, API abuse, or denial of service attacks.

**Affected Endpoints:**
- All assessment endpoints
- All payment endpoints
- All authentication endpoints

**Recommended Fix:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to sensitive endpoints
@router.post("/start")
@limiter.limit("10/minute")  # 10 assessments per minute max
async def start_assessment(...):
    ...

@router.post("/webhook")
@limiter.limit("100/minute")  # Stripe webhooks
async def stripe_webhook(...):
    ...
```

### 🟡 MEDIUM: No Stripe Webhook IP Whitelisting

**Severity:** Medium  
**CVSS Score:** 4.3 (Medium)  
**CWE:** CWE-346 (Origin Validation Error)

**Description:**  
Webhook endpoint accepts requests from any IP address. While signature verification is implemented, IP whitelisting provides defense in depth.

**Recommended Fix:**
```python
STRIPE_WEBHOOK_IPS = [
    "3.18.12.63", "3.130.192.231", "13.235.14.237",
    "13.235.122.149", "18.211.135.69", "35.154.171.200",
    "52.15.183.38", "54.187.174.169", "54.187.205.235",
    "54.187.216.72",
]

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host
    
    # Allow localhost for development
    if client_ip not in STRIPE_WEBHOOK_IPS and client_ip != "127.0.0.1":
        logger.warning(f"Webhook from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # ... rest of webhook logic ...
```

### 🟡 MEDIUM: No Foreign Key Validation

**Severity:** Medium  
**CVSS Score:** 4.3 (Medium)  
**CWE:** CWE-20 (Improper Input Validation)

**Description:**  
When `industry_id` or `role_id` are provided, there's no validation that these UUIDs actually exist in the database before creating the assessment.

**Affected Files:**
- `apps/api/app/routers/assessment.py` (lines 333-344)

**Recommended Fix:**
```python
# Validate industry_id exists
if body.industry_id:
    try:
        industry_uuid = uuid.UUID(body.industry_id)
        result = await db.execute(
            select(Industry).where(Industry.id == industry_uuid)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=400, detail="Invalid industry_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid industry_id format")

# Validate role_id exists
if body.role_id:
    try:
        role_uuid = uuid.UUID(body.role_id)
        result = await db.execute(
            select(Role).where(Role.id == role_uuid)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=400, detail="Invalid role_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role_id format")
```

---

## Security Checklist Results

### 1. Authentication & Authorization

| Check | Status | Notes |
|-------|--------|-------|
| All new endpoints require proper authentication | ❌ FAIL | Assessment endpoints allow anonymous access (intentional but risky) |
| User can only access their own usage data | ✅ PASS | Usage queries filtered by user_id |
| Tier validation happens server-side | ✅ PASS | Tier checked in backend, not client-side |
| results_locked flag is enforced server-side | ✅ PASS | Enforced in submit_kba, execute_ppa, submit_psv |
| **Assessment ownership verification** | ❌ **CRITICAL FAIL** | **No ownership checks on any assessment endpoints** |

### 2. Input Validation

| Check | Status | Notes |
|-------|--------|-------|
| All user inputs validated | ⚠️ PARTIAL | Mode, user_level validated; industry_id/role_id not validated |
| UUID validation for user_id | ✅ PASS | UUID parsing with try/except |
| Stripe webhook signature verified | ✅ PASS | Using stripe.Webhook.construct_event() |
| No SQL injection vulnerabilities | ✅ PASS | Using SQLAlchemy ORM with parameterized queries |

### 3. Data Protection

| Check | Status | Notes |
|-------|--------|-------|
| No sensitive data in error messages | ✅ PASS | Error messages are safe |
| No PII in logs | ✅ PASS | Only user emails logged (acceptable) |
| Usage data filtered by user_id | ✅ PASS | All usage queries include user_id filter |
| Stripe customer data properly protected | ✅ PASS | Queries filtered by user_id |

### 4. Business Logic Security

| Check | Status | Notes |
|-------|--------|-------|
| Free users cannot bypass 1 trial limit | ❌ FAIL | Race condition allows bypass |
| Premium users cannot exceed 3/month limit | ❌ FAIL | Race condition allows bypass |
| results_locked cannot be bypassed client-side | ✅ PASS | Server-side enforcement |
| Usage increment is atomic | ❌ FAIL | No locking, race condition possible |

### 5. OWASP Top 10

| Check | Status | Notes |
|-------|--------|-------|
| No injection vulnerabilities | ✅ PASS | Using ORM, no raw SQL |
| No broken authentication | ✅ PASS | JWT properly implemented |
| No sensitive data exposure | ⚠️ PARTIAL | Questions/PSV protected, but no ownership checks |
| No broken access control | ❌ **CRITICAL FAIL** | **No assessment ownership verification** |
| No security misconfiguration | ⚠️ PARTIAL | No rate limiting, no IP whitelisting |

### 6. Rate Limiting & Abuse Prevention

| Check | Status | Notes |
|-------|--------|-------|
| Rate limiting exists for assessment start | ❌ FAIL | No rate limiting implemented |
| Concurrent request handling is safe | ❌ FAIL | Race conditions in usage tracking |
| Webhook replay attacks are prevented | ❌ FAIL | No event deduplication |

---

## Additional Security Observations

### ✅ Security Strengths

1. **JWT Authentication**: Properly implemented with token validation
2. **Password Security**: Using passlib for hashing (referenced in security patterns)
3. **Results Locking**: Server-side enforcement prevents score leakage
4. **Webhook Signature Verification**: Stripe signatures properly validated
5. **UUID Primary Keys**: Non-sequential IDs prevent enumeration
6. **Input Validation**: Mode, user_level, and UUID formats validated
7. **Error Message Safety**: No information leakage in error messages
8. **Database Constraints**: Foreign keys with CASCADE deletes
9. **Question Protection**: correct_answer not exposed to clients
10. **PSV Protection**: ground_truth_level not exposed before submission

### ⚠️ Security Concerns

1. **Anonymous Assessment Access**: Allows anyone to access assessments without authentication
2. **No Audit Logging**: No comprehensive security event tracking
3. **No Request Signing**: Client requests not cryptographically signed
4. **No CORS Configuration**: Not visible in audited files
5. **No Content-Type Validation**: Not enforced in middleware
6. **No Session Management**: Stateless JWT (acceptable but limits revocation)

---

## Recommended Immediate Actions

### Priority 1 (Critical - Fix Before Production)

1. **Implement Assessment Ownership Verification**
   - Add `_verify_assessment_ownership()` helper function
   - Apply to all assessment endpoints
   - Add `current_user` parameter to all assessment endpoints
   - Test with multiple users to verify isolation

2. **Fix Race Condition in Usage Tracking**
   - Implement `SELECT FOR UPDATE` locking
   - Combine check and increment into atomic operation
   - Add database-level unique constraint on (user_id, period_start)
   - Test with concurrent requests

3. **Implement Webhook Event Deduplication**
   - Create `processed_webhook_events` table
   - Check event_id before processing
   - Add cleanup job for old events (>30 days)

### Priority 2 (High - Fix Within 1 Week)

4. **Move Usage Increment After Assessment Creation**
   - Reorder operations in `start_assessment`
   - Add transaction rollback on failure
   - Test error scenarios

5. **Add Rate Limiting**
   - Install slowapi or similar library
   - Apply limits to all public endpoints
   - Configure appropriate limits per endpoint

6. **Add Stripe Webhook IP Whitelisting**
   - Configure Stripe IP whitelist
   - Add environment variable for dev/prod IPs
   - Log unauthorized attempts

### Priority 3 (Medium - Fix Within 2 Weeks)

7. **Add Foreign Key Validation**
   - Validate industry_id exists before creating assessment
   - Validate role_id exists before creating assessment
   - Return clear error messages

8. **Add Audit Logging**
   - Log security events (failed auth, limit exceeded, etc.)
   - Log webhook processing
   - Add monitoring alerts

9. **Add Security Headers**
   - Configure CORS properly
   - Add Content-Type validation middleware
   - Add security headers (X-Frame-Options, etc.)

---

## Testing Recommendations

### Security Test Cases

1. **Test Assessment Ownership**
   ```bash
   # User A creates assessment
   assessment_id=$(curl -X POST /assessments/start -H "Authorization: Bearer $USER_A_TOKEN" | jq -r .assessment_id)
   
   # User B tries to access User A's assessment (should fail with 403)
   curl /assessments/$assessment_id/results -H "Authorization: Bearer $USER_B_TOKEN"
   # Expected: 403 Forbidden
   ```

2. **Test Race Condition**
   ```bash
   # Free user sends 10 concurrent requests
   for i in {1..10}; do
     curl -X POST /assessments/start -H "Authorization: Bearer $FREE_USER_TOKEN" &
   done
   wait
   
   # Check usage (should be 1/1, not 10/1)
   curl /dashboard/usage -H "Authorization: Bearer $FREE_USER_TOKEN"
   ```

3. **Test Webhook Replay**
   ```bash
   # Capture webhook payload
   # Replay same payload 5 times
   # Verify only processed once
   ```

4. **Test Usage Increment Failure**
   ```bash
   # Mock database error during assessment creation
   # Verify usage not incremented
   ```

---

## Compliance Considerations

### GDPR
- ✅ User data properly isolated (with ownership fix)
- ✅ Cascade deletes implemented
- ⚠️ No audit trail for data access
- ⚠️ No data retention policy visible

### PCI DSS (if handling payments)
- ✅ Using Stripe (PCI compliant payment processor)
- ✅ No card data stored locally
- ⚠️ No rate limiting on payment endpoints
- ⚠️ No IP whitelisting for webhooks

### SOC 2
- ⚠️ No comprehensive audit logging
- ⚠️ No security monitoring
- ⚠️ No incident response procedures visible

---

## Conclusion

The usage-limits-paywall feature implementation demonstrates good security practices in authentication, data protection, and webhook signature verification. However, the **critical lack of assessment ownership verification** creates a broken access control vulnerability that must be fixed before production deployment.

The race condition in usage tracking and lack of webhook replay prevention are also high-priority issues that could lead to business logic bypasses and revenue loss.

**Recommendation:** Do not deploy to production until Priority 1 issues are resolved and tested.

---

## Appendix: Security Testing Commands

### Test Authentication
```bash
# Test without token (should fail)
curl /assessments/start

# Test with invalid token (should fail)
curl /assessments/start -H "Authorization: Bearer invalid_token"

# Test with valid token (should succeed)
curl /assessments/start -H "Authorization: Bearer $VALID_TOKEN"
```

### Test Authorization
```bash
# Create assessment as User A
ASSESSMENT_ID=$(curl -X POST /assessments/start \
  -H "Authorization: Bearer $USER_A_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"full","industry_id":"'$INDUSTRY_ID'"}' \
  | jq -r .assessment_id)

# Try to access as User B (should fail after fix)
curl /assessments/$ASSESSMENT_ID/results \
  -H "Authorization: Bearer $USER_B_TOKEN"
```

### Test Usage Limits
```bash
# Free user first attempt (should succeed)
curl -X POST /assessments/start \
  -H "Authorization: Bearer $FREE_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"full"}'

# Free user second attempt (should fail with 402)
curl -X POST /assessments/start \
  -H "Authorization: Bearer $FREE_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"full"}'
```

### Test Results Locking
```bash
# Free user completes KBA (should return locked message)
curl -X POST /assessments/$ASSESSMENT_ID/kba/submit \
  -H "Content-Type: application/json" \
  -d '{"answers":[...]}'
# Expected: {"message": "KBA completed. Upgrade to Premium to view your scores.", "results_locked": true}
```

---

**Report Generated:** 2026-04-04  
**Next Review:** After Priority 1 fixes are implemented
