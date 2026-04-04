# Impact Assessment: Usage Limits and Paywall

## Executive Summary

**Risk Level:** Medium
**Breaking Changes:** None (backward compatible)
**Affected Users:** All users (free, premium, existing, new)
**Database Changes:** Data updates only (no schema changes)
**API Changes:** Response format additions (backward compatible)

## Risk Analysis by Phase

### Phase 1: Fix Premium User Limits (Risk: LOW)

**Impact:**
- Affects existing premium users with incorrect limits (0/0 → 0/3)
- Database update + code change to prevent recurrence

**Risks:**
1. **Data Migration Risk**: SQL update could fail or affect wrong records
   - Mitigation: Test query on staging, use WHERE clause with tier check
   - Rollback: Revert limit back to 0 (but this is the bug we're fixing)

2. **Concurrent Usage Risk**: User starts assessment during migration
   - Mitigation: Migration is fast (single UPDATE), low collision probability
   - Impact: Worst case, one assessment uses old limit (0), next one uses new (3)

3. **Logic Change Risk**: Always syncing limit could cause unexpected behavior
   - Mitigation: Only updates if limit differs from tier limit
   - Testing: Verify with free→premium, premium→free, fresh users

**Breaking Changes:** None
- Existing API responses unchanged
- Only fixes incorrect data

**Affected Components:**
- `UsageService.get_or_create_usage()` - adds limit sync logic
- `StripeService.handle_checkout_completed()` - updates usage limit on upgrade
- Database: `user_usage` table

### Phase 2: Free User Premium Limit (Risk: MEDIUM)

**Impact:**
- Changes behavior for free users attempting premium features
- Previously: Unlimited premium attempts (results locked)
- After: 1 trial attempt, then 402 error blocking 2nd attempt

**Risks:**
1. **User Experience Risk**: Free users blocked after 1 trial
   - Mitigation: Clear error message with upgrade CTA
   - Impact: Intentional - drives conversion

2. **Usage Tracking Risk**: Free users now consume quota
   - Mitigation: Reuse existing full_assessments_used counter
   - Edge case: Free user with existing usage record (rare)

3. **Upgrade Flow Risk**: Usage count must persist after upgrade
   - Mitigation: Webhook preserves used count, only updates limit
   - Testing: Critical path - free user with 1/1 → upgrade → shows 1/3

4. **Anonymous User Risk**: No user_id, can't track usage
   - Current: results_locked = true, no quota tracking
   - After: Same behavior (no change for anonymous)

**Breaking Changes:** Partial
- Free users now get 402 error after 1 premium attempt
- Frontend must handle 402 with upgrade_required flag
- Existing free users with 0 attempts: No impact
- Existing free users with 1+ attempts: Blocked immediately

**Affected Components:**
- `assessment.py:start_assessment()` - adds free tier limit check
- `UsageService.check_limit()` - returns (can_access, used, 1) for free tier
- Frontend: Must handle 402 error with upgrade modal

**Migration Concerns:**
- Existing free users who already took premium assessments will be blocked
- Solution: Acceptable - they used their trial, should upgrade
- Alternative: One-time grace period (not recommended)

### Phase 3: Industry/Role Paywall (Risk: MEDIUM)

**Impact:**
- Changes when results_locked is set
- Previously: Only full mode locks results
- After: Industry OR role selection also locks results

**Risks:**
1. **Scope Creep Risk**: Industry/role selection is broader than expected
   - Current: UI allows selection but doesn't enforce paywall
   - After: Selecting industry/role triggers paywall
   - Impact: More free users hit paywall (intentional)

2. **Section Score Leak Risk**: Scores returned before checking results_locked
   - Current: Section endpoints return scores immediately
   - After: Must check results_locked before returning
   - Testing: Critical - verify no score leakage

3. **Frontend Compatibility Risk**: Frontend expects scores, gets locked message
   - Mitigation: Return consistent response format with results_locked flag
   - Breaking: Frontend must handle locked responses

4. **Partial Completion Risk**: User completes KBA, then hits paywall at PPA
   - Current: results_locked set at start, consistent throughout
   - After: Same behavior (locked at start, stays locked)

**Breaking Changes:** Yes (API response format)
- Section score endpoints now return different response when locked
- Before: `{"kba_score": 85, "pillar_scores": {...}}`
- After: `{"message": "...", "results_locked": true}` (when locked)
- Frontend must handle both response types

**Affected Components:**
- `assessment.py:start_assessment()` - checks industry/role for results_locked
- `assessment.py:submit_kba()` - checks results_locked before returning scores
- `assessment.py:execute_ppa()` - checks results_locked before returning output
- `assessment.py:submit_psv()` - checks results_locked before returning scores
- Frontend: Assessment.tsx, Results.tsx

**Edge Cases:**
1. User selects industry but not role → results_locked = true
2. User selects role but not industry → results_locked = true
3. User selects neither, quick mode → results_locked = false
4. Premium user selects industry/role → results_locked = false (can see scores)

### Phase 4: Webhook Handlers (Risk: LOW)

**Impact:**
- Adds missing webhook handlers for production readiness
- No behavior change for existing flows

**Risks:**
1. **Payment Failure Risk**: invoice.payment_failed not handled
   - Current: Stripe retries automatically, eventually cancels subscription
   - After: Log failure, send notification, let Stripe handle retry
   - Impact: Better visibility, no behavior change

2. **Subscription Update Risk**: customer.subscription.updated not handled
   - Current: Plan changes not tracked
   - After: Log updates, handle status changes
   - Impact: Better tracking, no immediate behavior change

3. **Webhook Ordering Risk**: Events arrive out of order
   - Mitigation: Each handler is idempotent
   - Example: subscription.updated before checkout.completed
   - Solution: Handlers check current state, don't assume order

**Breaking Changes:** None
- Adds new handlers, doesn't modify existing ones
- Existing webhooks continue to work

**Affected Components:**
- `payments.py:stripe_webhook()` - adds new event type handlers
- `StripeService` - adds new handler methods

## Edge Cases and Scenarios

### Scenario 1: Free User Upgrade Mid-Assessment
**Flow:**
1. Free user starts premium assessment (1/1 used, results_locked=true)
2. Completes KBA (no scores shown)
3. Upgrades to premium during assessment
4. Continues to PPA

**Expected Behavior:**
- Assessment remains locked (results_locked set at start)
- User must start new assessment to see scores
- New assessment shows 1/3 used (previous attempt counts)

**Risk:** User expects to see scores immediately after upgrade
**Mitigation:** Clear messaging - "Start a new assessment to see your scores"

### Scenario 2: Premium User Downgrade
**Flow:**
1. Premium user with 2/3 used
2. Cancels subscription (downgrade to free)
3. Tries to start new premium assessment

**Expected Behavior:**
- User now has free tier
- Usage record shows 2/3 (old limit)
- get_or_create_usage() syncs limit to 0 (free tier)
- check_limit() for free tier allows 1 trial
- User already used 2, so 2 >= 1 → blocked

**Risk:** Downgraded user can't use free trial (already consumed)
**Mitigation:** Acceptable - they used premium features, should re-upgrade

### Scenario 3: Month Boundary During Assessment
**Flow:**
1. User starts assessment on April 30, 11:59 PM (3/3 used)
2. Assessment expires at 12:30 AM on May 1
3. User tries to start new assessment on May 1

**Expected Behavior:**
- May 1 assessment uses new period (2026-05-01)
- get_or_create_usage() creates new record (0/3)
- User can start assessment

**Risk:** None - period_start is date-based, clean boundary
**Testing:** Verify period calculation at month boundaries

### Scenario 4: Concurrent Assessment Starts
**Flow:**
1. Premium user with 2/3 used
2. Opens two browser tabs
3. Clicks "Start Assessment" in both tabs simultaneously

**Expected Behavior:**
- Tab 1: check_limit() → 2/3, can_start=true, increment to 3/3
- Tab 2: check_limit() → 3/3, can_start=false, 403 error
- OR both succeed if race condition (3/3 and 4/3)

**Risk:** User could exceed limit due to race condition
**Mitigation:** Database transaction isolation (SQLAlchemy default)
**Impact:** Low - rare scenario, max 1 extra assessment

### Scenario 5: Webhook Failure During Upgrade
**Flow:**
1. User completes Stripe checkout
2. Stripe sends webhook
3. Webhook handler crashes (database error, timeout)
4. User redirected to dashboard

**Expected Behavior:**
- Stripe retries webhook (up to 3 days)
- User sees old tier until webhook succeeds
- Manual sync endpoint available (/payments/sync-subscription)

**Risk:** User paid but doesn't see premium access
**Mitigation:** 
- Webhook retry mechanism (Stripe built-in)
- Manual sync endpoint for support
- Monitor webhook failures

### Scenario 6: Anonymous User Premium Attempt
**Flow:**
1. Anonymous user (not logged in)
2. Selects industry + role + full mode
3. Starts assessment

**Expected Behavior:**
- No user_id, can't track usage
- results_locked = true
- Can complete assessment but can't see scores
- No quota consumed (no user record)

**Risk:** Anonymous users could take unlimited premium assessments
**Mitigation:** Acceptable - they can't see results, encourages signup
**Alternative:** Require login before assessment (not in scope)

### Scenario 7: Expired Assessment Quota Refund
**Flow:**
1. Premium user starts assessment (1/3 used)
2. Assessment expires (time limit)
3. User wants to try again

**Expected Behavior (Current):**
- Quota stays 1/3 (no refund)
- User can start another (2/3)

**Expected Behavior (Optional Enhancement):**
- Refund quota when assessment expires
- User still shows 0/3

**Risk:** Refund logic could be exploited (start/abandon repeatedly)
**Recommendation:** Keep current behavior (no refund) for MVP

## Database Impact

### Schema Changes
**None** - All required fields already exist:
- `user_usage.full_assessments_limit` (exists)
- `user_usage.full_assessments_used` (exists)
- `assessments.results_locked` (exists)

### Data Migration Required

**Migration 1: Fix Premium User Limits**
```sql
-- Update existing premium users with wrong limits
UPDATE user_usage 
SET full_assessments_limit = 3,
    updated_at = NOW()
WHERE user_id IN (
    SELECT id FROM users WHERE subscription_tier = 'premium'
) 
AND full_assessments_limit != 3
AND period_start >= '2026-04-01';  -- Current month only
```

**Estimated Impact:** 
- Rows affected: ~10-100 (depends on premium user count)
- Execution time: <1 second
- Rollback: Not needed (fixing bug)

**Migration 2: Free User Usage Tracking (Optional)**
```sql
-- Create usage records for free users who don't have one
-- This ensures consistent behavior when they hit the limit
-- Not strictly required (get_or_create_usage handles it)
INSERT INTO user_usage (id, user_id, period_start, period_end, full_assessments_used, full_assessments_limit, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    u.id,
    DATE_TRUNC('month', CURRENT_DATE)::DATE,
    (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day')::DATE,
    0,
    0,
    NOW(),
    NOW()
FROM users u
WHERE u.subscription_tier = 'free'
AND NOT EXISTS (
    SELECT 1 FROM user_usage uu 
    WHERE uu.user_id = u.id 
    AND uu.period_start = DATE_TRUNC('month', CURRENT_DATE)::DATE
);
```

**Estimated Impact:**
- Rows affected: ~1000-10000 (depends on free user count)
- Execution time: 1-5 seconds
- Optional: Code handles missing records

### Performance Impact

**Query Load:**
- `get_or_create_usage()` called on every assessment start
- Current: 1 SELECT + 0-1 INSERT
- After: 1 SELECT + 0-1 INSERT + 0-1 UPDATE (if limit sync needed)
- Impact: Negligible (single row operations)

**Index Requirements:**
- Existing: `user_usage(user_id, period_start)` - likely indexed
- Verify: Check if composite index exists
- Add if missing: `CREATE INDEX idx_user_usage_lookup ON user_usage(user_id, period_start);`

## API Contract Changes

### Backward Compatible Changes

**1. Assessment Start Response (No Change)**
```json
{
  "assessment_id": "uuid",
  "mode": "full",
  "results_locked": true,  // Existing field
  "expires_at": "2026-04-04T12:00:00Z"
}
```

**2. Usage Endpoint Response (No Change)**
```json
{
  "full_assessments_used": 1,
  "full_assessments_limit": 3,  // Now correct for premium
  "period_start": "2026-04-01",
  "period_end": "2026-04-30"
}
```

### Breaking Changes

**1. Assessment Start Error (New 402 for Free Users)**
```json
// Before: Free users could start unlimited premium assessments
// After: Free users blocked after 1 trial
{
  "status_code": 402,
  "detail": {
    "message": "Free trial used. Upgrade to Premium for 3 full assessments per month.",
    "used": 1,
    "upgrade_required": true
  }
}
```

**Frontend Impact:** Must handle 402 error and show upgrade modal

**2. Section Score Responses (Conditional Format)**
```json
// When results_locked = false (premium user)
{
  "kba_score": 85,
  "total_correct": 17,
  "total_questions": 20,
  "pillar_scores": {
    "P": {"score": 90, "correct": 9, "total": 10},
    "E": {"score": 80, "correct": 8, "total": 10}
  }
}

// When results_locked = true (free user)
{
  "message": "Assessment completed. Upgrade to view results.",
  "results_locked": true
}
```

**Frontend Impact:** Must check for results_locked flag and handle both formats

## Rollback Strategy

### Phase 1 Rollback
**If:** Premium users report incorrect limits after fix
**Action:**
1. Revert code changes to `get_or_create_usage()`
2. Revert webhook handler changes
3. Keep database updates (they fix the bug)

**Risk:** Low - changes are additive and fix existing bug

### Phase 2 Rollback
**If:** Free users blocked incorrectly or conversion drops unexpectedly
**Action:**
1. Revert assessment start logic (remove free tier limit check)
2. Free users can again take unlimited premium attempts (results locked)
3. Keep usage tracking (no harm)

**Risk:** Medium - requires code deployment

### Phase 3 Rollback
**If:** Section score endpoints break frontend or leak scores
**Action:**
1. Revert section endpoint changes (remove results_locked check)
2. Scores returned immediately (old behavior)
3. Keep industry/role paywall logic at assessment start

**Risk:** Medium - partial rollback possible (keep start logic, revert endpoints)

### Phase 4 Rollback
**If:** New webhook handlers cause errors
**Action:**
1. Remove new event handlers from webhook router
2. Keep existing handlers (checkout.completed, subscription.deleted)

**Risk:** Low - new handlers are independent

## Testing Requirements

### Critical Path Tests
1. Free user → 1 premium trial → blocked on 2nd attempt → upgrade → 1/3 used
2. Premium user → 0/3 → start assessment → 1/3 → complete → see scores
3. Free user → select industry → complete assessment → no scores → upgrade modal
4. Webhook → checkout.completed → user tier updated → usage limit updated

### Regression Tests
1. Existing premium users still see correct limits
2. Anonymous users can still take assessments (results locked)
3. Quick assessments without industry/role work for free users
4. Monthly reset still works (May 1st creates new usage record)

### Edge Case Tests
1. Concurrent assessment starts (race condition)
2. Month boundary during assessment
3. Upgrade mid-assessment (results stay locked)
4. Downgrade with existing usage (blocked from free trial)

## Monitoring and Alerts

### Metrics to Track
1. **Free user conversion rate**: % who upgrade after hitting limit
2. **Premium usage distribution**: How many users hit 3/3 limit
3. **Webhook success rate**: % of webhooks processed successfully
4. **402 error rate**: Free users hitting premium limit

### Alerts to Configure
1. **Webhook failures**: Alert if >5% webhooks fail
2. **Usage limit errors**: Alert if premium users get 403 unexpectedly
3. **Database sync issues**: Alert if usage limits don't match tiers

## Conclusion

**Overall Risk:** Medium
- Most changes are backward compatible
- Breaking changes limited to free user behavior (intentional)
- Database changes are data-only (no schema changes)
- Rollback strategy available for each phase

**Recommendation:** Proceed with phased rollout
- Phase 1: Low risk, fixes critical bug
- Phase 2: Medium risk, test thoroughly with free users
- Phase 3: Medium risk, verify no score leakage
- Phase 4: Low risk, production readiness only
