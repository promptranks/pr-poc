# Analysis: Usage Limits and Paywall Implementation

**Date:** 2026-04-03
**Status:** Current State Analysis + Implementation Plan

---

## Issue 1: Premium User Shows 0/0 Full Assessments

### Current State

**Database:**
```sql
-- User: admin@adamchins.com
subscription_tier: premium

-- user_usage table:
period_start: 2026-04-01
period_end: 2026-04-30
full_assessments_used: 0
full_assessments_limit: 0  ❌ WRONG - should be 3
```

**Code Analysis:**

1. **UsageService.get_tier_limit()** (apps/api/app/services/usage_service.py:13-15)
   ```python
   def get_tier_limit(tier: str) -> int:
       limits = {"free": 0, "premium": 3, "enterprise": 999}
       return limits.get(tier, 0)
   ```
   ✅ Correctly returns 3 for premium

2. **UsageService.get_or_create_usage()** (apps/api/app/services/usage_service.py:26-52)
   - Creates new usage record with `full_assessments_limit = limit`
   - ✅ Logic is correct

3. **Problem:** Old usage records were created BEFORE user upgraded to premium
   - When user was `free`, limit was set to 0
   - When user upgraded to `premium`, existing usage records were NOT updated

### Root Cause
The usage records are created when the user first accesses the system each month. If created while user was `free`, the limit is set to 0. When user upgrades to `premium`, the existing usage record is NOT updated.

### Solution for Issue 1

**Update existing usage records when tier changes (Recommended)**

- When user upgrades via Stripe webhook, update current month's usage record
- Set `full_assessments_limit` to match new tier

**Implementation Plan:**
1. Update `StripeService.handle_checkout_completed()` to update usage limit
2. Add helper method to update current period usage limit
3. Update existing records in database for current premium users

---

## Issue 2: Paywall Logic for Industry/Role Selection

### Current Business Logic (Your Requirements)

**Premium Features:**
- Industry & Role selection (for both Quick and Full assessments)
- Full assessment mode

**Free User Behavior:**
- ✅ Can select industry/role (UI shows but doesn't block)
- ✅ Can take Quick assessment (no restrictions)
- ✅ Can take Full assessment (no restrictions)
- ❌ **CANNOT see scores** if they used premium features

**Paywall Trigger:**
- Free user selects industry OR role → results_locked = true
- Free user selects Full mode → results_locked = true
- During assessment: hide section scores (KBA, PPA, PSV) if results_locked = true
- At final results: show paywall modal instead of scores

### Current Implementation

**Assessment Start** (apps/api/app/routers/assessment.py:268-286)
```python
results_locked = False
if body.mode == "full":
    if current_user:
        tier = current_user.subscription_tier
        if tier == "premium":
            # Check limit, increment usage
            can_start, used, limit = await UsageService.check_limit(...)
            if not can_start:
                raise HTTPException(403, "Limit reached")
            await UsageService.increment_usage(...)
        elif tier == "free":
            results_locked = True  ✅ Correct
        # enterprise: no limit
    else:
        results_locked = True  ✅ Correct
```

**Current Logic:**
- ✅ Full mode for free users → results_locked = true
- ❌ Industry/role selection does NOT set results_locked = true
- ❌ Section scores (KBA, PPA, PSV) are ALWAYS returned, regardless of results_locked

**Section Score Endpoints:**
1. `POST /assessments/{id}/kba/submit` → Returns `kba_score` and `pillar_scores`
2. `POST /assessments/{id}/ppa/execute` → Returns task scores
3. `POST /assessments/{id}/psv/submit` → Returns `psv_score`

**Problem:** These endpoints return scores immediately, no check for `results_locked`

### Solution for Issue 2

**Backend Changes:**

1. **Update assessment start logic** (assessment.py:268-286)
   ```python
   results_locked = False
   
   # Check if premium features are used
   premium_features_used = (
       body.mode == "full" or 
       body.industry is not None or 
       body.role is not None
   )
   
   if premium_features_used:
       if current_user:
           tier = current_user.subscription_tier
           if tier == "premium":
               if body.mode == "full":
                   # Check limit and increment
                   can_start, used, limit = await UsageService.check_limit(...)
                   if not can_start:
                       raise HTTPException(403, "Limit reached")
                   await UsageService.increment_usage(...)
           elif tier == "free":
               results_locked = True
       else:
           results_locked = True
   ```

2. **Update section score endpoints** to check `results_locked`:
   - `submit_kba()` - Check before returning scores
   - `execute_ppa()` - Check before returning scores
   - `submit_psv()` - Check before returning scores
   
   ```python
   # In each endpoint, after scoring:
   if assessment.results_locked:
       return {
           "message": "Assessment completed. Upgrade to view results.",
           "results_locked": True
       }
   else:
       return {
           "score": ...,
           "pillar_scores": ...,
           "results_locked": False
       }
   ```

3. **Update final results endpoint** (already has results_locked check)
   - ✅ Already returns `results_locked` flag
   - Frontend should show paywall modal when true

**Frontend Changes:**

1. **Assessment.tsx** - Handle locked section scores
   - When section score response has `results_locked: true`, show message instead of score
   - "✓ Section completed. Upgrade to Premium to view your scores."

2. **Results.tsx** - Show paywall modal
   - Check `results_locked` flag
   - If true, show upgrade modal instead of scores
   - Already partially implemented

---

## Issue 3: Monthly Usage Reset

### Current State
- ✅ Usage records are created per month (period_start, period_end)
- ❌ No automatic reset mechanism
- ❌ Old records are not cleaned up

### Business Requirement
> "If user subscribed on 1st day of month, reset on 1st of each month"

**Problem:** This is NOT how subscription billing works!

**Correct Approach:**
- Stripe subscriptions have a billing cycle (e.g., subscribed on March 15 → renews on April 15)
- Usage should reset on the billing cycle date, NOT calendar month

**However**, for simplicity, the PRD uses calendar month reset (1st of each month).

### Solution for Issue 3

**Option B: Billing Cycle Reset (More accurate)**
- Track subscription start date
- Reset usage on anniversary date each month
- More complex but fair to users

**Current Implementation Analysis:**
```python
# UsageService.get_or_create_usage() line 32-38
result = await db.execute(
    select(UserUsage).where(
        UserUsage.user_id == user_uuid,
        UserUsage.period_start == period_start  # ✅ Queries by current period
    )
)
```

✅ **Already works correctly!** When a new month starts:
- `get_current_period()` returns new period_start (e.g., 2026-05-01)
- Query finds no record for new period
- Creates new record with `full_assessments_used = 0`
- Old records remain in DB for history

**No changes needed for reset logic!**

---

## Issue 4: Quota Increment Timing and Free User Premium Attempts

### Current Quota Increment Behavior

**When is quota incremented?**
```python
# apps/api/app/routers/assessment.py:280
# Incremented IMMEDIATELY when assessment starts
if tier == "premium":
    can_start, used, limit = await UsageService.check_limit(...)
    if not can_start:
        raise HTTPException(403, "Limit reached")
    await UsageService.increment_usage(...)  # ← Increments on START, not completion
```

**Edge Cases:**
1. User starts assessment but doesn't finish (network issue, browser closed)
2. Assessment expires (time limit exceeded)
3. Assessment voided (anti-cheat violations)

**Current Behavior:** Quota is consumed even if assessment not completed.

**Analysis:**
- ✅ **Increment on START** = Standard SaaS practice, prevents abuse
  - Prevents users from starting many assessments and cherry-picking
  - Prevents gaming the system by abandoning "bad" attempts
  - Industry standard (AWS, Stripe, etc. charge on API call, not success)
  
- ❌ **Increment on COMPLETION** = Fairer but exploitable
  - Users could start unlimited assessments and abandon if they don't like questions
  - More complex to implement (need to track pending vs completed)
  - Edge case: What if user completes but network fails before saving?

**Recommendation:** Keep increment on START (current behavior is correct).

### Critical Gap: Free User Premium Attempts

**Current Free User Behavior:**
```python
# apps/api/app/routers/assessment.py:281-282
elif tier == "free":
    results_locked = True  # ← Allows UNLIMITED premium attempts!
```

**Problem:** Free users can start unlimited premium assessments (industry/role/full), just can't see scores.

**Required Business Logic:**
1. Free users get **1 trial** of premium features
2. After 1 premium attempt, **block** them from starting another → force upgrade
3. When they upgrade, their pre-payment attempts **count** against 3/month limit
4. Example: Free user took 1 full assessment → upgrades → shows 1/3 used

**Why This Matters:**
- Prevents abuse: Free users taking unlimited premium assessments
- Creates urgency: "You've used your 1 free trial, upgrade to continue"
- Fair accounting: Pre-payment attempts count after upgrade

### Solution for Issue 4

**Part A: Track Premium Attempts for Free Users**

1. **Reuse existing `user_usage` table**
   - Free users already have usage records (with limit=0)
   - Use `full_assessments_used` to track premium attempts
   - When free user starts premium assessment, increment their usage

2. **Update assessment start logic** (assessment.py:268-286)
   ```python
   results_locked = False
   
   # Check if premium features are used
   premium_features_used = (
       body.mode == "full" or 
       body.industry is not None or 
       body.role is not None
   )
   
   if premium_features_used:
       if current_user:
           tier = current_user.subscription_tier
           if tier == "premium":
               # Check limit and increment
               can_start, used, limit = await UsageService.check_limit(...)
               if not can_start:
                   raise HTTPException(403, f"Assessment limit reached ({used}/{limit})")
               await UsageService.increment_usage(...)
           elif tier == "free":
               # NEW: Check free user premium attempts
               can_start, used, limit = await UsageService.check_limit(...)
               # Free users get 1 trial (limit=0 but we allow 1)
               if used >= 1:
                   raise HTTPException(
                       402,
                       detail={
                           "message": "Free trial used. Upgrade to Premium for 3 full assessments per month.",
                           "used": used,
                           "upgrade_required": True
                       }
                   )
               # Allow this attempt but lock results
               await UsageService.increment_usage(...)
               results_locked = True
           # enterprise: no limit
       else:
           # Anonymous users: allow 1 attempt, lock results
           results_locked = True
   ```

3. **Update UsageService to handle free tier tracking**
   
   ```python
   # apps/api/app/services/usage_service.py
   
   @staticmethod
   async def check_limit(user_id: str, tier: str, db: AsyncSession) -> Tuple[bool, int, int]:
       usage = await UsageService.get_or_create_usage(user_id, tier, db)
       
       if tier == "free":
           # Free users get 1 trial attempt
           can_access = usage.full_assessments_used < 1
           return can_access, usage.full_assessments_used, 1  # Show as X/1
       else:
           # Premium/enterprise use normal limits
           can_access = usage.full_assessments_used < usage.full_assessments_limit
           return can_access, usage.full_assessments_used, usage.full_assessments_limit
   ```

**Part B: Preserve Usage Count on Upgrade**

1. **Update Stripe webhook handler** (stripe_service.py:85-127)
   ```python
   async def handle_checkout_completed(session: dict, db: AsyncSession):
       # ... existing code to update user.subscription_tier = "premium" ...
       
       # NEW: Update current month's usage record
       period_start, period_end = UsageService.get_current_period()
       user_uuid = user.id
       
       result = await db.execute(
           select(UserUsage).where(
               UserUsage.user_id == user_uuid,
               UserUsage.period_start == period_start
           )
       )
       usage = result.scalar_one_or_none()
       
       if usage:
           # User already has usage record (was free, took some assessments)
           # Update limit to premium (3), keep existing used count
           usage.full_assessments_limit = 3
           # usage.full_assessments_used stays the same (e.g., 1)
       else:
           # No usage record yet, create new one
           usage = UserUsage(
               user_id=user_uuid,
               period_start=period_start,
               period_end=period_end,
               full_assessments_used=0,
               full_assessments_limit=3
           )
           db.add(usage)
       
       await db.commit()
   ```

2. **Update get_or_create_usage to always sync limit** (Option B from Issue 1)
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
           # NEW: Always update limit to match current tier
           if usage.full_assessments_limit != limit:
               usage.full_assessments_limit = limit
               await db.commit()
               await db.refresh(usage)
       
       return usage
   ```

**Part C: Handle Expired/Voided Assessments (Optional Enhancement)**

**Current:** Quota consumed even if assessment expires/voided.

**Enhancement (Optional):**
```python
# Add method to refund quota
@staticmethod
async def refund_usage(user_id: str, tier: str, db: AsyncSession) -> None:
    usage = await UsageService.get_or_create_usage(user_id, tier, db)
    if usage.full_assessments_used > 0:
        usage.full_assessments_used -= 1
        usage.updated_at = datetime.now(timezone.utc)
        await db.commit()

# Call when assessment expires/voided
# In assessment.py, when marking as expired/voided:
if assessment.user_id and assessment.mode == "full":
    tier = user.subscription_tier
    if tier in ("free", "premium"):  # Don't refund enterprise
        await UsageService.refund_usage(str(assessment.user_id), tier, db)
```

**Recommendation:** Skip refund logic for MVP. Standard SaaS practice is no refunds for started sessions.

---

## Issue 5: Stripe Webhook Lifecycle (Production Readiness)

### Current Webhook Handlers

```python
# apps/api/app/routers/payments.py:136-166
if event["type"] == "checkout.session.completed":
    await StripeService.handle_checkout_completed(...)
elif event["type"] == "customer.subscription.deleted":
    await StripeService.handle_subscription_deleted(...)
```

### Missing Webhook Handlers

**Critical for Production:**

1. **`invoice.payment_succeeded`** - Monthly renewal success
   - Stripe charges customer automatically each month
   - Backend should log successful renewal
   - Optional: Send receipt email, update analytics

2. **`invoice.payment_failed`** - Payment declined
   - Credit card expired, insufficient funds, etc.
   - Should notify user, retry, or downgrade to free
   - Critical: Don't let users stay premium if payment fails

3. **`customer.subscription.updated`** - Subscription modified
   - User changes plan (monthly → annual)
   - User pauses subscription
   - Proration, plan upgrades/downgrades

### Implementation Plan

```python
# apps/api/app/routers/payments.py - Add handlers

elif event["type"] == "invoice.payment_succeeded":
    invoice = event["data"]["object"]
    await StripeService.handle_invoice_paid(invoice, db)

elif event["type"] == "invoice.payment_failed":
    invoice = event["data"]["object"]
    await StripeService.handle_payment_failed(invoice, db)

elif event["type"] == "customer.subscription.updated":
    subscription = event["data"]["object"]
    await StripeService.handle_subscription_updated(subscription, db)
```

```python
# apps/api/app/services/stripe_service.py - Add methods

@staticmethod
async def handle_invoice_paid(invoice: dict, db: AsyncSession):
    """Log successful monthly renewal."""
    customer_id = invoice.get("customer")
    # Find user by stripe_customer_id
    # Log renewal in database (optional)
    # Send receipt email (optional)
    # Update analytics (optional)
    pass

@staticmethod
async def handle_payment_failed(invoice: dict, db: AsyncSession):
    """Handle failed payment - notify user, retry, or downgrade."""
    customer_id = invoice.get("customer")
    # Find user by stripe_customer_id
    # Send "payment failed" email
    # Stripe will retry automatically (configurable)
    # After final retry fails, subscription will be canceled
    # customer.subscription.deleted event will fire
    pass

@staticmethod
async def handle_subscription_updated(subscription: dict, db: AsyncSession):
    """Handle subscription changes (plan change, pause, etc.)."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    # Update user tier based on new subscription status
    # Handle paused, past_due, canceled, etc.
    pass
```

### Recommendation

**For MVP/Current State:**
- ✅ Keep current handlers (checkout.session.completed, customer.subscription.deleted)
- ✅ Calendar month usage reset works correctly
- ⚠️ Add `invoice.payment_failed` handler (critical for production)

**For Production:**
- Add all 5 webhook handlers
- Add email notifications for payment events
- Add admin dashboard to monitor subscription health

---

## Summary of Required Changes

### 🔴 Critical (Must Fix Now)

1. **Fix usage limit for existing premium users**
   - SQL: Update `full_assessments_limit` in user_usage table for current premium users
   - Code: Update `get_or_create_usage()` to always sync limit with current tier

2. **Implement free user premium attempt limit**
   - Track premium attempts for free users (reuse full_assessments_used)
   - Limit free users to 1 premium trial
   - Block 2nd attempt with upgrade prompt
   - Preserve usage count when user upgrades

3. **Implement paywall for industry/role selection**
   - Update assessment start to set `results_locked` when industry/role selected
   - Update section score endpoints to check `results_locked`
   - Update frontend to handle locked scores

4. **Update Stripe webhook to preserve usage on upgrade**
   - When user upgrades, update current month's usage limit to 3
   - Keep existing `full_assessments_used` count (don't reset to 0)

### 🟡 Important (Should Fix for Production)

5. **Add invoice.payment_failed webhook handler**
   - Handle declined payments
   - Notify users, allow Stripe retry logic
   - Prevent premium access after final failure

6. **Frontend paywall modal**
   - Show upgrade CTA when results_locked = true
   - Hide scores during assessment if locked
   - Show "1 free trial used" message for free users

### 🟢 Nice to Have (Optional)

7. **Quota refund for expired/voided assessments**
   - Refund quota if assessment expires or voided
   - More user-friendly but not standard SaaS practice
8. **Additional webhook handlers**
   - invoice.payment_succeeded (renewal logging)
   - customer.subscription.updated (plan changes)

---

## Implementation Order

### Phase 1: Fix Critical Usage Issues (Priority 1)

**Step 1.1: Fix existing premium users (Database + Code)**
```sql
-- Fix current premium users with wrong limits
UPDATE user_usage 
SET full_assessments_limit = 3 
WHERE user_id IN (
    SELECT id FROM users WHERE subscription_tier = 'premium'
) AND full_assessments_limit != 3;
```

**Step 1.2: Update UsageService.get_or_create_usage()**
- Always sync `full_assessments_limit` with current tier
- Fixes issue where old records have wrong limits

**Step 1.3: Update StripeService.handle_checkout_completed()**
- Update current month's usage record when user upgrades
- Set limit to 3, preserve existing used count

### Phase 2: Implement Free User Premium Limit (Priority 1)

**Step 2.1: Update assessment start logic**
- Check if premium features used (industry/role/full)
- For free users: check usage, allow 1 trial, block 2nd attempt
- Increment usage for free users on premium attempts

**Step 2.2: Update UsageService.check_limit()**
- Handle free tier: return (can_access, used, 1) for free users
- Show "X/1" for free users, "X/3" for premium

**Step 2.3: Update frontend error handling**
- Handle 402 error with upgrade_required flag
- Show upgrade modal with "Free trial used" message

### Phase 3: Implement Industry/Role Paywall (Priority 1)

**Step 3.1: Update assessment start logic**
- Set `results_locked = true` when industry OR role selected by free user
- Already done for full mode, extend to industry/role

**Step 3.2: Update section score endpoints**
- Check `assessment.results_locked` before returning scores
- Return `{"message": "...", "results_locked": true}` instead of scores
- Apply to: submit_kba(), execute_ppa(), submit_psv()

**Step 3.3: Update frontend Assessment.tsx**
- Handle locked section scores
- Show "✓ Section completed. Upgrade to view scores." message

**Step 3.4: Update frontend Results.tsx**
- Check `results_locked` flag
- Show upgrade modal instead of scores

### Phase 4: Production Webhook Handlers (Priority 2)

**Step 4.1: Add invoice.payment_failed handler**
- Log failed payments
- Send notification email
- Let Stripe handle retry logic

**Step 4.2: Add other webhook handlers (optional)**
- invoice.payment_succeeded
- customer.subscription.updated

### Phase 5: Polish (Priority 3)

**Step 5.1: Quota refund (optional)**
- Add refund_usage() method
- Call when assessment expires/voided

**Step 5.2: Usage cleanup (optional)**
- Cron job to delete old records

---

## Testing Checklist

### Test Case 1: Existing Premium User
- ✅ Shows 0/3 full assessments (not 0/0)
- ✅ Can start full assessment
- ✅ Quota increments to 1/3
- ✅ Can see all scores immediately

### Test Case 2: Free User - First Premium Attempt
- ✅ Selects industry + role + full mode
- ✅ Can start assessment
- ✅ Quota shows 1/1 (used their trial)
- ✅ Can complete all sections
- ✅ Cannot see section scores (locked message)
- ✅ Cannot see final results (upgrade modal)

### Test Case 3: Free User - Second Premium Attempt
- ✅ Already used 1 trial (quota 1/1)
- ✅ Tries to start another premium assessment
- ✅ Gets 402 error with upgrade prompt
- ✅ Cannot start assessment

### Test Case 4: Free User Upgrades After Trial
- ✅ Free user with 1/1 used
- ✅ Completes Stripe checkout
- ✅ Webhook updates tier to premium
- ✅ Webhook updates limit to 3, keeps used=1
- ✅ Dashboard shows 1/3 full assessments
- ✅ Can start 2 more full assessments this month

### Test Case 5: Fresh Premium User
- ✅ New user, subscribes immediately
- ✅ No prior usage record
- ✅ Webhook creates usage: 0/3
- ✅ Can start full assessment
- ✅ Quota increments to 1/3

### Test Case 6: Monthly Reset
- ✅ Premium user with 3/3 used in April
- ✅ May 1st arrives
- ✅ Next assessment start creates new usage record
- ✅ Shows 0/3 for May (fresh quota)

### Test Case 7: Assessment Expiry (Current Behavior)
- ✅ Premium user starts full assessment (1/3)
- ✅ Assessment expires (time limit)
- ✅ Quota stays 1/3 (no refund)
- ✅ User can start another (2/3)

### Test Case 8: Industry/Role Paywall
- ✅ Free user selects industry (no role, quick mode)
- ✅ Can complete assessment
- ✅ Cannot see section scores
- ✅ Cannot see final results
- ✅ Gets upgrade modal

