# Acceptance Criteria Checklist: Usage Limits & Paywall

**Feature:** Usage Limits & Paywall Implementation  
**Date:** 2026-04-04  
**Status:** Implementation Complete, Tests Written

---

## How to Use This Checklist

For each test case:
1. **Manual Verification:** Follow the steps to verify functionality
2. **Automated Test:** Run the corresponding test
3. **Mark Status:** ✅ PASS, ❌ FAIL, ⚠️ BLOCKED
4. **Evidence:** Note observations or test output

---

## Test Case 1: Existing Premium User

### Acceptance Criteria
- Shows 0/3 full assessments (not 0/0)
- Can start full assessment
- Quota increments to 1/3
- Can see all scores immediately

### Manual Verification Steps
1. Login as premium user (admin@adamchins.com)
2. Navigate to dashboard
3. Check usage display shows "0/3 Full Assessments"
4. Click "Start Full Assessment"
5. Select industry and role
6. Verify assessment starts successfully
7. Check dashboard shows "1/3 Full Assessments"
8. Complete KBA section
9. Verify scores displayed immediately (no "Upgrade" message)
10. Complete PPA and PSV sections
11. Verify all scores visible in final results

### Automated Tests
```bash
pytest tests/test_usage_limits.py::test_premium_user_under_limit -v
pytest tests/test_usage_limits.py::test_premium_user_can_start_full_assessment -v
pytest tests/test_usage_limits.py::test_premium_user_increment_usage -v
```

### Implementation Evidence
- **File:** `apps/api/app/services/usage_service.py`
- **Lines:** 52-57 (limit syncing), 70-72 (premium check)
- **Migration:** `migrations/fix_premium_usage_limits.sql`

### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS
- [ ] Database migration applied

### Notes
_Record any observations or issues here_

---

## Test Case 2: Free User - First Premium Attempt

### Acceptance Criteria
- Selects industry + role + full mode
- Can start assessment
- Quota shows 1/1 (used their trial)
- Can complete all sections
- Cannot see section scores (locked message)
- Cannot see final results (upgrade modal)

### Manual Verification Steps
1. Create new free user account
2. Navigate to assessment page
3. Select "Full Assessment" mode
4. Select an industry (e.g., "Technology")
5. Select a role (e.g., "Software Engineer")
6. Click "Start Assessment"
7. Verify assessment starts successfully
8. Check dashboard shows "1/1 Full Assessments Used"
9. Complete KBA section
10. Verify message: "KBA completed. Upgrade to Premium to view your scores."
11. Verify no scores displayed
12. Complete PPA section
13. Verify message: "Task completed. Upgrade to Premium to view results."
14. Complete PSV section
15. Verify message: "PSV completed. Upgrade to Premium to view your score."
16. Navigate to results page
17. Verify upgrade modal shown instead of scores

### Automated Tests
```bash
pytest tests/test_usage_limits.py::test_free_user_first_premium_attempt_allowed -v
pytest tests/test_usage_limits.py::test_check_limit_free_user_no_usage -v
pytest tests/test_usage_limits.py::test_results_locked_hides_kba_scores -v
```

### Implementation Evidence
- **File:** `apps/api/app/routers/assessment.py`
- **Lines:** 272-276 (premium detection), 294-311 (free user logic)
- **Lines:** 444-449 (KBA locked), 590-595 (PPA locked), 783-788 (PSV locked)

### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS
- [ ] All section scores locked
- [ ] Upgrade modal shown

### Notes
_Record any observations or issues here_

---

## Test Case 3: Free User - Second Premium Attempt

### Acceptance Criteria
- Already used 1 trial (quota 1/1)
- Tries to start another premium assessment
- Gets 402 error with upgrade prompt
- Cannot start assessment

### Manual Verification Steps
1. Use free user from Test Case 2 (already has 1/1 used)
2. Navigate to assessment page
3. Select "Full Assessment" mode
4. Select industry and role
5. Click "Start Assessment"
6. Verify error message: "Free trial used. Upgrade to Premium for 3 full assessments per month."
7. Verify 402 status code in network tab
8. Verify "upgrade_required" flag in response
9. Verify assessment does NOT start
10. Verify dashboard still shows "1/1 Full Assessments Used"

### Automated Tests
```bash
pytest tests/test_usage_limits.py::test_free_user_second_premium_attempt_blocked -v
pytest tests/test_usage_limits.py::test_check_limit_free_user_trial_used -v
```

### Implementation Evidence
- **File:** `apps/api/app/services/usage_service.py`
- **Lines:** 65-68 (free tier limit check)
- **File:** `apps/api/app/routers/assessment.py`
- **Lines:** 299-308 (402 error response)

### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS
- [ ] 402 error returned
- [ ] Upgrade prompt shown

### Notes
_Record any observations or issues here_

---

## Test Case 4: Free User Upgrades After Trial

### Acceptance Criteria
- Free user with 1/1 used
- Completes Stripe checkout
- Webhook updates tier to premium
- Webhook updates limit to 3, keeps used=1
- Dashboard shows 1/3 full assessments
- Can start 2 more full assessments this month

### Manual Verification Steps
1. Use free user with 1/1 used from Test Case 3
2. Click "Upgrade to Premium" button
3. Complete Stripe checkout in test mode
   - Use test card: 4242 4242 4242 4242
   - Any future expiry date
   - Any CVC
4. Verify redirected to dashboard
5. Check dashboard shows "1/3 Full Assessments Used"
6. Verify user tier is now "Premium"
7. Start another full assessment
8. Verify assessment starts successfully
9. Check dashboard shows "2/3 Full Assessments Used"
10. Start another full assessment
11. Verify assessment starts successfully
12. Check dashboard shows "3/3 Full Assessments Used"
13. Try to start 4th assessment
14. Verify 403 error: "Assessment limit reached (3/3)"

### Automated Tests
```bash
pytest tests/test_payments.py::test_webhook_upgrade_preserves_usage -v
pytest tests/test_usage_limits.py::test_upgrade_preserves_usage_count -v
```

### Implementation Evidence
- **File:** `apps/api/app/services/stripe_service.py`
- **Lines:** 121-149 (webhook usage update)
- **Lines:** 133-138 (preserve used count)

### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS
- [ ] Usage count preserved (1/1 → 1/3)
- [ ] Can start 2 more assessments

### Notes
_Record any observations or issues here_

---

## Test Case 5: Fresh Premium User

### Acceptance Criteria
- New user, subscribes immediately
- No prior usage record
- Webhook creates usage: 0/3
- Can start full assessment
- Quota increments to 1/3

### Manual Verification Steps
1. Create new user account
2. Immediately click "Upgrade to Premium" (before taking any assessments)
3. Complete Stripe checkout in test mode
4. Verify redirected to dashboard
5. Check dashboard shows "0/3 Full Assessments Used"
6. Start full assessment
7. Verify assessment starts successfully
8. Check dashboard shows "1/3 Full Assessments Used"
9. Complete assessment
10. Verify all scores visible immediately

### Automated Tests
```bash
pytest tests/test_payments.py::test_webhook_fresh_premium_user -v
pytest tests/test_usage_limits.py::test_fresh_premium_user_gets_full_quota -v
```

### Implementation Evidence
- **File:** `apps/api/app/services/stripe_service.py`
- **Lines:** 139-149 (create new usage record)

### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS
- [ ] Usage created as 0/3
- [ ] All scores visible

### Notes
_Record any observations or issues here_

---

## Test Case 6: Monthly Reset

### Acceptance Criteria
- Premium user with 3/3 used in April
- May 1st arrives
- Next assessment start creates new usage record
- Shows 0/3 for May (fresh quota)

### Manual Verification Steps
1. Use premium user with 3/3 used in current month
2. Verify dashboard shows "3/3 Full Assessments Used"
3. Try to start assessment
4. Verify 403 error: "Assessment limit reached"
5. **Simulate month change:**
   - Option A: Wait until next month (1st of month)
   - Option B: Manually update `period_start` in database to next month
6. Start full assessment
7. Verify assessment starts successfully
8. Check dashboard shows "1/3 Full Assessments Used" (new month)
9. Verify old usage record still exists in database (for history)

### Automated Tests
```bash
pytest tests/test_usage_limits.py::test_monthly_reset_creates_new_usage_record -v
```

### Implementation Evidence
- **File:** `apps/api/app/services/usage_service.py`
- **Lines:** 18-23 (get_current_period)
- **Lines:** 32-38 (query by period_start)

### Database Verification
```sql
-- Check usage records for user
SELECT period_start, period_end, full_assessments_used, full_assessments_limit
FROM user_usage
WHERE user_id = '<user_id>'
ORDER BY period_start DESC;

-- Should show multiple records, one per month
```

### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS
- [ ] New record created for new month
- [ ] Old records preserved

### Notes
_Record any observations or issues here_

---

## Test Case 7: Assessment Expiry

### Acceptance Criteria
- Premium user starts full assessment (1/3)
- Assessment expires (time limit)
- Quota stays 1/3 (no refund)
- User can start another (2/3)

### Manual Verification Steps
1. Use premium user with 0/3 used
2. Start full assessment
3. Check dashboard shows "1/3 Full Assessments Used"
4. Wait for assessment to expire (or manually expire in database)
   - Quick mode: 30 minutes
   - Full mode: 2 hours
5. Try to submit answers
6. Verify error: "Assessment has expired"
7. Check dashboard still shows "1/3 Full Assessments Used" (no refund)
8. Start another full assessment
9. Verify assessment starts successfully
10. Check dashboard shows "2/3 Full Assessments Used"

### Automated Tests
```bash
pytest tests/test_usage_limits.py::test_assessment_expiry_no_refund -v
```

### Implementation Evidence
- **File:** `apps/api/app/routers/assessment.py`
- **Lines:** 292, 310 (increment on start, not completion)
- **Note:** No refund logic implemented (intentional)

### Database Verification
```sql
-- Check expired assessment
SELECT id, status, started_at, expires_at, user_id
FROM assessments
WHERE status = 'expired'
AND user_id = '<user_id>';

-- Check usage not refunded
SELECT full_assessments_used, full_assessments_limit
FROM user_usage
WHERE user_id = '<user_id>'
AND period_start = CURRENT_DATE - INTERVAL '1 day' * EXTRACT(DAY FROM CURRENT_DATE) + INTERVAL '1 day';
```

### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS
- [ ] Quota not refunded
- [ ] Can start another assessment

### Notes
_This is intentional behavior (standard SaaS practice)_

---

## Test Case 8: Industry/Role Paywall

### Acceptance Criteria
- Free user selects industry (no role, quick mode)
- Can complete assessment
- Cannot see section scores
- Cannot see final results
- Gets upgrade modal

### Manual Verification Steps

#### Scenario A: Industry Only
1. Create new free user
2. Select "Quick Assessment" mode
3. Select industry (e.g., "Healthcare")
4. Do NOT select role
5. Start assessment
6. Verify assessment starts successfully
7. Complete KBA section
8. Verify message: "KBA completed. Upgrade to Premium to view your scores."
9. View results
10. Verify upgrade modal shown

#### Scenario B: Role Only
1. Use same free user
2. Select "Quick Assessment" mode
3. Do NOT select industry
4. Select role (e.g., "Manager")
5. Start assessment
6. Verify assessment starts successfully
7. Complete sections
8. Verify scores locked

#### Scenario C: Both Industry and Role
1. Use same free user (should be blocked - already used trial)
2. Create new free user
3. Select "Quick Assessment" mode
4. Select both industry and role
5. Start assessment
6. Verify assessment starts successfully
7. Complete sections
8. Verify scores locked

### Automated Tests
```bash
pytest tests/test_usage_limits.py::test_industry_selection_triggers_paywall -v
pytest tests/test_usage_limits.py::test_role_selection_triggers_paywall -v
pytest tests/test_usage_limits.py::test_results_locked_hides_kba_scores -v
```

### Implementation Evidence
- **File:** `apps/api/app/routers/assessment.py`
- **Lines:** 272-276 (premium features detection)
- **Lines:** 444-449 (KBA locked)
- **Lines:** 590-595 (PPA locked)
- **Lines:** 783-788 (PSV locked)

### Status
- [ ] Manual verification PASS (Scenario A)
- [ ] Manual verification PASS (Scenario B)
- [ ] Manual verification PASS (Scenario C)
- [ ] Automated tests PASS
- [ ] All scores locked
- [ ] Upgrade modal shown

### Notes
_Record any observations or issues here_

---

## Additional Verification

### Enterprise User Unlimited Access

#### Steps
1. Create enterprise user (or upgrade existing user to enterprise)
2. Start 10+ full assessments
3. Verify all start successfully
4. Verify no limit errors
5. Verify all scores visible

#### Test
```bash
pytest tests/test_usage_limits.py::test_enterprise_user_no_limits -v
pytest tests/test_usage_limits.py::test_check_limit_enterprise_user_unlimited -v
```

#### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS

---

### Anonymous User Flow

#### Steps
1. Open application without logging in
2. Start assessment with industry/role
3. Verify assessment starts
4. Complete sections
5. Verify all scores locked
6. Verify upgrade prompt shown

#### Test
```bash
pytest tests/test_usage_limits.py::test_anonymous_user_premium_features_locked -v
```

#### Status
- [ ] Manual verification PASS
- [ ] Automated tests PASS

---

## Database Migration Verification

### Before Migration
```sql
SELECT u.email, u.subscription_tier, uu.full_assessments_limit
FROM users u
LEFT JOIN user_usage uu ON u.id = uu.user_id
WHERE u.subscription_tier = 'premium'
AND uu.full_assessments_limit = 0;
```

Expected: Some premium users with limit=0

### Run Migration
```bash
psql -h <host> -U <user> -d <database> -f migrations/fix_premium_usage_limits.sql
```

### After Migration
```sql
SELECT u.email, u.subscription_tier, uu.full_assessments_limit
FROM users u
LEFT JOIN user_usage uu ON u.id = uu.user_id
WHERE u.subscription_tier = 'premium'
AND uu.full_assessments_limit = 0;
```

Expected: No results (all premium users have limit=3)

### Status
- [ ] Migration executed successfully
- [ ] All premium users have limit=3
- [ ] No data loss

---

## Final Checklist

### Code Quality
- [ ] All 8 test cases verified manually
- [ ] All automated tests pass
- [ ] Code follows existing patterns
- [ ] Error handling implemented
- [ ] Security considerations addressed
- [ ] Performance acceptable

### Documentation
- [ ] QUALITY_REPORT.md reviewed
- [ ] TEST_EXECUTION_GUIDE.md followed
- [ ] BACKEND_IMPLEMENTATION_SUMMARY.md accurate
- [ ] All acceptance criteria documented

### Deployment
- [ ] Database migration applied
- [ ] Tests pass in staging
- [ ] Manual verification in staging
- [ ] Monitoring configured
- [ ] Rollback plan prepared

### Production Readiness
- [ ] All tests pass
- [ ] Coverage > 80%
- [ ] No regressions
- [ ] Performance tested
- [ ] Security reviewed

---

## Sign-off

### Developer
- Name: _________________
- Date: _________________
- Signature: _________________

### QA Engineer
- Name: _________________
- Date: _________________
- Signature: _________________

### Product Owner
- Name: _________________
- Date: _________________
- Signature: _________________

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-04
