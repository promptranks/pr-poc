# Feature Documentation: Usage Limits and Paywall

**Feature:** usage-limits-paywall  
**Status:** Completed  
**Date:** 2026-04-04

## Overview

This feature implements comprehensive usage tracking and paywall enforcement for the PromptRank assessment platform. It fixes critical bugs in premium user limits, adds free user trial restrictions, and enforces paywall for premium features (industry/role selection, full assessments).

## What Was Built

### Phase 1: Fix Premium User Limits
**Problem:** Premium users showed 0/0 assessments instead of 0/3.

**Solution:**
- Database migration to fix existing premium users
- Updated `UsageService.get_or_create_usage()` to always sync limits with current tier
- Updated Stripe webhook to preserve usage count when users upgrade

**Files Modified:**
- `apps/api/app/services/usage_service.py`
- `apps/api/app/services/stripe_service.py`
- `apps/api/migrations/fix_premium_usage_limits.sql` (new)

### Phase 2: Free User Premium Limit
**Problem:** Free users could take unlimited premium assessments (results locked but no limit).

**Solution:**
- Free users get 1 trial attempt for premium features
- 2nd attempt blocked with 402 error + upgrade prompt
- Usage count preserved when upgrading (1/1 → 1/3)

**Files Modified:**
- `apps/api/app/services/usage_service.py` - Added free tier handling
- `apps/api/app/routers/assessment.py` - Added free user limit check
- `apps/web/src/pages/Landing.tsx` - Handle 402 error with upgrade modal

### Phase 3: Industry/Role Paywall
**Problem:** Only full mode triggered paywall, not industry/role selection.

**Solution:**
- Set `results_locked=true` when free users select industry OR role
- Section endpoints check `results_locked` before returning scores
- Frontend shows completion message instead of scores when locked

**Files Modified:**
- `apps/api/app/routers/assessment.py` - Updated assessment start logic, section endpoints
- `apps/web/src/pages/KBA.tsx` - Handle locked scores
- `apps/web/src/pages/PPA.tsx` - Handle locked outputs
- `apps/web/src/pages/PSV.tsx` - Handle locked scores

### Phase 4: Webhook Handlers
**Problem:** Missing webhook handlers for payment failures and subscription updates.

**Solution:**
- Added `invoice.payment_failed` handler (logs failed payments)
- Added `invoice.payment_succeeded` handler (logs renewals)
- Added `customer.subscription.updated` handler (logs changes)

**Files Modified:**
- `apps/api/app/services/stripe_service.py` - New webhook handlers
- `apps/api/app/routers/payments.py` - Webhook routing

### Security Fix: Assessment Ownership Verification
**Problem:** CRITICAL - Any user could access other users' assessments by knowing the UUID.

**Solution:**
- Added `_verify_assessment_ownership()` helper function
- All assessment endpoints now verify ownership
- Anonymous assessments remain accessible
- User-owned assessments require authentication and ownership match

**Files Modified:**
- `apps/api/app/routers/assessment.py` - Added ownership checks to all endpoints

## How It Works

### Usage Tracking Flow

1. **Assessment Start:**
   - Check if premium features used (full mode, industry_id, role_id)
   - For premium users: check limit (0-3), increment usage
   - For free users: check trial limit (0-1), increment usage, lock results
   - For enterprise: no limit

2. **Section Submission:**
   - Check `results_locked` flag
   - If locked: return completion message (no scores)
   - If unlocked: return scores normally

3. **Results Display:**
   - Check `results_locked` flag
   - If locked: show paywall modal
   - If unlocked: show full results

4. **Monthly Reset:**
   - Automatic on first assessment of new month
   - Creates new usage record with fresh quota
   - Old records preserved for history

5. **Upgrade Flow:**
   - User completes Stripe checkout
   - Webhook updates tier to premium
   - Webhook updates usage limit to 3, preserves used count
   - User sees updated quota immediately

### Tier Limits

| Tier | Full Assessments/Month | Industry/Role Selection | Results Visibility |
|------|------------------------|-------------------------|-------------------|
| Free | 1 trial | Yes (results locked) | Locked |
| Premium | 3 | Yes | Full access |
| Enterprise | Unlimited | Yes | Full access |

## Configuration

### Environment Variables

No new environment variables required. Uses existing:
- `STRIPE_SECRET_KEY` - Stripe API key
- `STRIPE_WEBHOOK_SECRET` - Webhook signature verification

### Database Migration

Run the SQL migration to fix existing premium users:

```bash
psql $DATABASE_URL -f apps/api/migrations/fix_premium_usage_limits.sql
```

This updates `user_usage.full_assessments_limit` from 0 to 3 for current premium users.

## API Changes

### New Error Responses

**402 Payment Required** (Free trial exhausted):
```json
{
  "detail": {
    "message": "Free trial used. Upgrade to Premium for 3 full assessments per month.",
    "used": 1,
    "limit": 1,
    "upgrade_required": true
  }
}
```

**Locked Section Score Response:**
```json
{
  "message": "Section completed. Upgrade to view scores.",
  "results_locked": true
}
```

### Modified Endpoints

All assessment endpoints now require ownership verification:
- `POST /assessments/{id}/kba/submit`
- `GET /assessments/{id}/ppa/tasks`
- `POST /assessments/{id}/ppa/execute`
- `POST /assessments/{id}/ppa/submit-best`
- `GET /assessments/{id}/psv/sample`
- `POST /assessments/{id}/psv/submit`
- `GET /assessments/{id}/results`

Anonymous assessments (user_id=null) remain accessible without auth.

## Testing

### Manual Testing Checklist

See `.feature-flow/usage-limits-paywall/validation/ACCEPTANCE_CRITERIA_CHECKLIST.md` for detailed manual testing procedures.

### Automated Tests

Run the test suite:
```bash
cd apps/api
pytest tests/test_usage_limits.py -v
```

27 tests covering all 8 acceptance criteria from the PRD.

## Monitoring

### Key Metrics to Monitor

1. **Usage Tracking:**
   - Free users hitting trial limit (402 errors)
   - Premium users hitting monthly limit (403 errors)
   - Upgrade conversions after hitting limits

2. **Webhook Processing:**
   - `checkout.session.completed` success rate
   - `invoice.payment_failed` frequency
   - Webhook processing latency

3. **Security:**
   - 401/403 errors on assessment endpoints
   - Unauthorized access attempts

### Logging

All key events are logged:
- Usage limit checks: `UsageService.check_limit()`
- Usage increments: `UsageService.increment_usage()`
- Webhook processing: `StripeService.handle_*()` methods
- Ownership verification failures: `_verify_assessment_ownership()`

## Rollback Plan

### If Issues Arise

1. **Revert to main branch:**
   ```bash
   git checkout main
   git branch -D feature/usage-limits-paywall
   ```

2. **Database rollback (if needed):**
   ```sql
   -- Revert premium user limits to 0 (not recommended, this is the bug)
   UPDATE user_usage SET full_assessments_limit = 0 
   WHERE user_id IN (SELECT id FROM users WHERE subscription_tier = 'premium');
   ```

3. **No data loss:** All changes are backward compatible. Usage records remain intact.

## Known Limitations

1. **No Quota Refunds:** If assessment expires or is voided, quota is not refunded (standard SaaS practice)

2. **Race Conditions:** Concurrent requests may bypass usage limits (low probability, requires database-level locking to fix)

3. **Calendar Month Reset:** Usage resets on 1st of month, not billing cycle date (simpler but less accurate)

## Future Enhancements

1. **Billing Cycle Reset:** Reset usage on subscription anniversary date
2. **Quota Refunds:** Refund quota for expired/voided assessments
3. **Usage Analytics:** Dashboard showing usage trends over time
4. **Grace Period:** Allow 1-2 days grace period after payment failure
5. **Rate Limiting:** Add rate limiting to prevent abuse

## Support

For issues or questions:
- Review security audit: `.feature-flow/usage-limits-paywall/validation/SECURITY_AUDIT.md`
- Review test execution guide: `.feature-flow/usage-limits-paywall/validation/TEST_EXECUTION_GUIDE.md`
- Check implementation summaries: `BACKEND_IMPLEMENTATION_SUMMARY.md`, `FRONTEND_IMPLEMENTATION_SUMMARY.md`
